"""
LLM loader — produces LangChain-compatible LLM wrappers around our models.

Three loading modes are supported, all behind one stable interface:

    load_llm(cfg, mode="base")        → base instruction-tuned model only
    load_llm(cfg, mode="finetuned")   → base + our QLoRA adapter
    load_llm(cfg, mode="auto")        → finetuned if adapter exists, else base

This single module is the seam between Phase 1 (raw PyTorch + PEFT) and
Phases 2-4 (LangChain pipelines + Streamlit). Keeping it isolated means
the rest of the project never imports peft/transformers directly.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Literal, Optional, Tuple

# Allow imports when invoked as `python -m src.llm_loader` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline,
)

# LangChain has reshuffled this import path twice in the last year.
# We try the newest location first, then fall back gracefully.
try:
    from langchain_huggingface import HuggingFacePipeline
except ImportError:  # pragma: no cover - older langchain
    try:
        from langchain_community.llms import HuggingFacePipeline  # type: ignore
    except ImportError:
        from langchain.llms import HuggingFacePipeline  # type: ignore

from configs.config import FineTuneConfig, get_default_config

logger = logging.getLogger("amazonqa.llm_loader")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _build_bnb_config(cfg: FineTuneConfig) -> Optional[BitsAndBytesConfig]:
    """Return a BitsAndBytes 4-bit config, or None if CUDA isn't available."""
    if not torch.cuda.is_available():
        logger.warning(
            "CUDA unavailable — loading in full precision on CPU. This will "
            "be slow and is only intended for code-path testing."
        )
        return None

    return BitsAndBytesConfig(
        load_in_4bit=cfg.model.load_in_4bit,
        bnb_4bit_quant_type=cfg.model.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=getattr(torch, cfg.model.bnb_4bit_compute_dtype),
        bnb_4bit_use_double_quant=cfg.model.bnb_4bit_use_double_quant,
    )


def _load_tokenizer(cfg: FineTuneConfig) -> AutoTokenizer:
    """Load and configure the tokenizer for inference (left-padding for generate)."""
    tokenizer_id = cfg.model.tokenizer_id or cfg.model.base_model_id
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_id, trust_remote_code=cfg.model.trust_remote_code
    )
    # Generation uses left-padding so newly generated tokens append correctly.
    # (Training used right-padding — different requirement.)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def _adapter_exists(cfg: FineTuneConfig) -> bool:
    """Check whether the LoRA adapter from Phase 1 is on disk."""
    adapter_cfg = cfg.paths.adapter_dir / "adapter_config.json"
    return adapter_cfg.exists()


# ---------------------------------------------------------------------------
# Public API — raw PyTorch model + tokenizer
# ---------------------------------------------------------------------------
def load_raw_model(
    cfg: FineTuneConfig,
    mode: Literal["base", "finetuned", "auto"] = "auto",
) -> Tuple[torch.nn.Module, AutoTokenizer]:
    """
    Load the base LLM (and optionally apply the QLoRA adapter).

    This returns raw transformers objects — use `load_llm()` for the
    LangChain-wrapped version.

    Args:
        cfg: Project config.
        mode: 'base' → just the base model; 'finetuned' → base + adapter
              (raises if adapter missing); 'auto' → finetuned if available
              else base with a warning.

    Returns:
        (model, tokenizer) ready for inference.
    """
    # Resolve auto-mode
    if mode == "auto":
        mode = "finetuned" if _adapter_exists(cfg) else "base"
        logger.info("Auto-selected mode: %s", mode)

    bnb_config = _build_bnb_config(cfg)
    logger.info("Loading base model: %s", cfg.model.base_model_id)

    try:
        model = AutoModelForCausalLM.from_pretrained(
            cfg.model.base_model_id,
            quantization_config=bnb_config,
            device_map=cfg.model.device_map if torch.cuda.is_available() else "cpu",
            trust_remote_code=cfg.model.trust_remote_code,
        )
    except torch.cuda.OutOfMemoryError as exc:
        raise RuntimeError(
            "OOM while loading the base model. Try the Phi-2 fallback config "
            "(get_phi2_fallback_config()) or restart your Colab runtime."
        ) from exc

    model.config.use_cache = True       # re-enable KV cache for fast inference

    # ------------------------------------------------------------------
    # Apply LoRA adapter if requested
    # ------------------------------------------------------------------
    if mode == "finetuned":
        if not _adapter_exists(cfg):
            raise FileNotFoundError(
                f"No LoRA adapter found at {cfg.paths.adapter_dir}. "
                "Run Phase 1 (notebooks/01_qlora_finetune.ipynb) first, "
                "or pass mode='base' to use the unfine-tuned model."
            )
        logger.info("Applying LoRA adapter from %s", cfg.paths.adapter_dir)
        model = PeftModel.from_pretrained(model, str(cfg.paths.adapter_dir))
        # Merging adapter into base weights would be faster at inference
        # but blocks future re-loading. We keep them separate.

    model.eval()
    tokenizer = _load_tokenizer(cfg)
    return model, tokenizer


# ---------------------------------------------------------------------------
# Public API — LangChain-wrapped LLM (this is what RAG / eval / app use)
# ---------------------------------------------------------------------------
def load_llm(
    cfg: Optional[FineTuneConfig] = None,
    mode: Literal["base", "finetuned", "auto"] = "auto",
    *,
    max_new_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> HuggingFacePipeline:
    """
    Return a LangChain-compatible LLM ready to plug into any chain.

    Args:
        cfg: Project config. Defaults to `get_default_config()`.
        mode: see `load_raw_model`.
        max_new_tokens: override `cfg.rag.max_new_tokens`.
        temperature: override `cfg.rag.temperature`.

    Returns:
        A `HuggingFacePipeline` LLM. Call `.invoke(prompt)` to generate.
    """
    cfg = cfg or get_default_config()

    model, tokenizer = load_raw_model(cfg, mode=mode)

    gen_pipe = pipeline(
        task="text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens or cfg.rag.max_new_tokens,
        temperature=temperature if temperature is not None else cfg.rag.temperature,
        top_p=cfg.rag.top_p,
        repetition_penalty=cfg.rag.repetition_penalty,
        do_sample=True,
        return_full_text=False,    # critical — return ONLY the completion
        pad_token_id=tokenizer.pad_token_id,
    )

    llm = HuggingFacePipeline(pipeline=gen_pipe)
    logger.info(
        "LLM ready (mode=%s, max_new_tokens=%d, temperature=%.2f)",
        mode,
        gen_pipe.model.config.max_position_embeddings if hasattr(gen_pipe.model.config, 'max_position_embeddings') else -1,
        gen_pipe._forward_params.get("temperature", -1) if hasattr(gen_pipe, '_forward_params') else -1,
    )
    return llm


__all__ = ["load_raw_model", "load_llm"]
