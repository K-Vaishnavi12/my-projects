"""
Unified `generate_answer(system_name, question)` interface for the three
systems compared in Phase 3.

Why a registry?
---------------
Each of the three systems shares 90% of its plumbing — the only differences
are (a) whether to apply the LoRA adapter and (b) whether to wrap the LLM
in a RetrievalQA chain. A small registry keeps RAGAS evaluation code
trivially symmetric (`for sys in systems: evaluate(sys, ...)`) and lets us
add new systems (e.g. `rag_finetuned_mmr`) without touching the eval loop.

Models / chains are loaded **lazily** — the first call to `generate_answer(name)`
materialises the heavy artifacts and caches them. Call `GeneratorRegistry.unload()`
between systems to free GPU memory if you're tight on VRAM.

Public API
----------
    SYSTEM_NAMES                       : ('base', 'rag_base', 'rag_finetuned')
    GeneratorRegistry(cfg)             : singleton-style cache
    generate_answer(system, question)  : convenience top-level function
"""

from __future__ import annotations

import gc
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow `python -m evaluation.generators`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configs.config import FineTuneConfig, get_default_config

logger = logging.getLogger("amazonqa.eval.generators")


# ---------------------------------------------------------------------------
# Registry of supported systems
# ---------------------------------------------------------------------------
SYSTEM_NAMES: Tuple[str, ...] = ("base", "rag_base", "rag_finetuned")


class GeneratorRegistry:
    """
    Lazy, single-process cache for the three eval systems.

    Holds at most ONE LLM in GPU memory at a time by default — this is
    intentional on T4-class hardware where two 7B models won't fit.
    Set `keep_all_in_memory=True` if you have a beefy GPU and want to avoid
    the reload cost between systems.
    """

    def __init__(
        self,
        cfg: Optional[FineTuneConfig] = None,
        *,
        keep_all_in_memory: bool = False,
    ):
        self.cfg = cfg or get_default_config()
        self.keep_all_in_memory = keep_all_in_memory
        # Cache: system_name -> dict with keys {"llm", "chain"} (chain only for RAG systems)
        self._cache: Dict[str, Dict[str, Any]] = {}
        # Shared retriever — built once, reused by both RAG systems.
        self._retriever = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def unload(self, system_name: Optional[str] = None) -> None:
        """
        Drop a system (or everything) from memory. Pairs with `gc.collect()`
        + `torch.cuda.empty_cache()` to reclaim VRAM between systems.
        """
        if system_name is None:
            self._cache.clear()
        else:
            self._cache.pop(system_name, None)

        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------
    def _ensure_retriever(self):
        """Build the shared FAISS retriever once; reuse for rag_base + rag_finetuned."""
        if self._retriever is not None:
            return self._retriever

        # Lazy-import RAG plumbing so this module is importable without GPU.
        from src.rag_pipeline import (
            build_retriever,
            chunk_documents,
            build_vector_store,
            load_documents,
            load_vector_store,
        )

        index_path = self.cfg.paths.vector_store_dir / "index.faiss"
        if index_path.exists():
            logger.info("Loading existing FAISS index from %s", index_path.parent)
            vs = load_vector_store(self.cfg)
        else:
            logger.info("No FAISS index found — building one from corpus")
            docs = load_documents(self.cfg)
            chunks = chunk_documents(docs, self.cfg)
            vs = build_vector_store(chunks, self.cfg)

        self._retriever = build_retriever(vs, self.cfg)
        return self._retriever

    def _load_system(self, system_name: str) -> Dict[str, Any]:
        """Materialise one system on first use."""
        if system_name not in SYSTEM_NAMES:
            raise ValueError(
                f"Unknown system '{system_name}'. Must be one of {SYSTEM_NAMES}."
            )

        # If we don't keep everything resident, evict any existing cache first.
        if not self.keep_all_in_memory and self._cache:
            evicted = list(self._cache.keys())
            logger.info(
                "Evicting %s from memory to make room for '%s'",
                evicted,
                system_name,
            )
            self.unload()

        # Lazy imports keep the module importable in CI / on CPU.
        from src.llm_loader import load_llm
        from src.rag_pipeline import build_rag_chain

        if system_name == "base":
            llm = load_llm(
                self.cfg,
                mode="base",
                max_new_tokens=self.cfg.eval.eval_max_new_tokens,
                temperature=self.cfg.eval.eval_temperature,
            )
            entry = {"llm": llm, "chain": None}

        elif system_name == "rag_base":
            llm = load_llm(
                self.cfg,
                mode="base",
                max_new_tokens=self.cfg.eval.eval_max_new_tokens,
                temperature=self.cfg.eval.eval_temperature,
            )
            retriever = self._ensure_retriever()
            chain = build_rag_chain(llm, retriever, self.cfg)
            entry = {"llm": llm, "chain": chain}

        elif system_name == "rag_finetuned":
            llm = load_llm(
                self.cfg,
                mode="finetuned",
                max_new_tokens=self.cfg.eval.eval_max_new_tokens,
                temperature=self.cfg.eval.eval_temperature,
            )
            retriever = self._ensure_retriever()
            chain = build_rag_chain(llm, retriever, self.cfg)
            entry = {"llm": llm, "chain": chain}

        self._cache[system_name] = entry
        return entry

    # ------------------------------------------------------------------
    # Public: single-question generation
    # ------------------------------------------------------------------
    def generate(
        self,
        system_name: str,
        question: str,
        *,
        return_contexts: bool = True,
    ) -> Dict[str, Any]:
        """
        Run one question through one system.

        Returns:
            {
                "system":   str,
                "question": str,
                "answer":   str,
                "contexts": List[str]   — retrieved chunks (RAG only) or [] for base
            }
        """
        entry = self._cache.get(system_name) or self._load_system(system_name)

        if system_name == "base":
            # Single-shot generation against the bare instruction-tuned LLM.
            # We use the SFT prompt template so the model sees the same
            # "Amazon shopping assistant" framing it saw during training.
            prompt = self.cfg.prompt_template.format(
                question=question, answer=""
            ).rstrip("</s>").rstrip()
            answer = entry["llm"].invoke(prompt)
            contexts: List[str] = []

        else:  # rag_base or rag_finetuned
            chain = entry["chain"]
            result = chain.invoke({"query": question})
            answer = (result.get("result") or result.get("answer") or "").strip()
            sources = result.get("source_documents") or []
            contexts = [doc.page_content for doc in sources] if return_contexts else []

        return {
            "system": system_name,
            "question": question,
            "answer": answer.strip() if isinstance(answer, str) else str(answer),
            "contexts": contexts,
        }


# ---------------------------------------------------------------------------
# Module-level convenience wrapper (mirrors the API the user asked for)
# ---------------------------------------------------------------------------
_DEFAULT_REGISTRY: Optional[GeneratorRegistry] = None


def _get_default_registry(
    cfg: Optional[FineTuneConfig] = None,
) -> GeneratorRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = GeneratorRegistry(cfg)
    return _DEFAULT_REGISTRY


def generate_answer(
    system_name: str,
    question: str,
    *,
    cfg: Optional[FineTuneConfig] = None,
) -> Dict[str, Any]:
    """
    One-call convenience function matching the spec interface.

    Example:
        >>> from evaluation.generators import generate_answer
        >>> out = generate_answer("rag_finetuned", "Does the Echo Dot work with Spotify?")
        >>> print(out["answer"])
        >>> print(out["contexts"])  # 5 retrieved chunks
    """
    return _get_default_registry(cfg).generate(system_name, question)


__all__ = [
    "SYSTEM_NAMES",
    "GeneratorRegistry",
    "generate_answer",
]
