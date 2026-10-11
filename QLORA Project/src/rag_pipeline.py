"""
RAG pipeline for the AmazonQA-RAG project.

Builds, persists, and queries a FAISS vector index over an Amazon
product/support corpus, then wires it into a LangChain `RetrievalQA`
chain on top of the (optionally fine-tuned) LLM from Phase 1.

Public API
----------
    build_corpus_from_hf(cfg)         → quickly bootstrap a corpus from the
                                        same Amazon-QA dataset we trained on
    load_documents(cfg)               → load CSV / JSONL / TXT into LangChain Documents
    chunk_documents(docs, cfg)        → RecursiveCharacterTextSplitter
    build_vector_store(chunks, cfg)   → embeds + writes FAISS index to disk
    load_vector_store(cfg)            → reads FAISS index from disk
    build_retriever(vs, cfg)          → returns a top-k retriever
    build_rag_chain(llm, retriever, cfg) → returns a LangChain RetrievalQA
    answer(chain, question)           → returns {answer, source_documents}

The notebook `02_build_rag.ipynb` calls these in order; Phases 3 and 4
re-use the same functions.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow `python -m src.rag_pipeline`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from datasets import load_dataset

# LangChain imports — try modern paths first, fall back for older installs.
try:
    from langchain_community.document_loaders import (
        TextLoader,
        DirectoryLoader,
    )
    from langchain_community.vectorstores import FAISS
except ImportError:  # pragma: no cover
    from langchain.document_loaders import (  # type: ignore
        TextLoader,
        DirectoryLoader,
    )
    from langchain.vectorstores import FAISS  # type: ignore

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:  # pragma: no cover
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
    except ImportError:
        from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from configs.config import FineTuneConfig, get_default_config

logger = logging.getLogger("amazonqa.rag")


# ===========================================================================
# 1. Corpus bootstrap (lets users skip "find me an Amazon dataset" friction)
# ===========================================================================
def build_corpus_from_hf(
    cfg: FineTuneConfig,
    output_format: str = "csv",
    overwrite: bool = False,
) -> Path:
    """
    Create a local Amazon QA corpus by re-using the HF dataset from Phase 1.

    This gives users an instant working corpus without hunting for files.
    For a "real" deployment you'd replace this with your own product
    catalog, help-center articles, or seller-Q&A export.

    Args:
        cfg: Project config.
        output_format: "csv" or "jsonl".
        overwrite: If False and the corpus exists, skip regeneration.

    Returns:
        Path to the written corpus file.
    """
    suffix = ".csv" if output_format == "csv" else ".jsonl"
    out_path = cfg.paths.raw_data_dir / f"amazon_corpus{suffix}"

    if out_path.exists() and not overwrite:
        logger.info("Corpus already exists at %s (use overwrite=True to regenerate)", out_path)
        return out_path

    logger.info("Bootstrapping corpus from HF dataset: %s", cfg.dataset.hf_dataset_id)
    raw = load_dataset(cfg.dataset.hf_dataset_id, split=cfg.dataset.hf_dataset_split)

    sample_size = cfg.rag.corpus_sample_size or len(raw)
    sample_size = min(sample_size, len(raw))
    raw = raw.shuffle(seed=cfg.dataset.seed).select(range(sample_size))

    # Flatten into the schema RAG expects
    rows = []
    for ex in raw:
        question = (ex.get("query") or ex.get("question") or "").strip()
        answers = ex.get("pos") or ex.get("answers") or []
        answer = (answers[0] if isinstance(answers, list) and answers else "").strip()
        if len(question) > 5 and len(answer) > 5:
            rows.append({"question": question, "answer": answer})

    cfg.paths.raw_data_dir.mkdir(parents=True, exist_ok=True)

    if output_format == "csv":
        import csv
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["question", "answer"])
            writer.writeheader()
            writer.writerows(rows)
    else:
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    logger.info("Wrote %d rows to %s", len(rows), out_path)
    return out_path


# ===========================================================================
# 2. Document loading (format-agnostic)
# ===========================================================================
def _detect_format(path: Path) -> str:
    """Infer corpus format from file extension."""
    ext = path.suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext in (".json", ".jsonl"):
        return "jsonl"
    if ext == ".txt":
        return "txt"
    if path.is_dir():
        return "txt"  # DirectoryLoader for a folder of .txts
    raise ValueError(f"Cannot auto-detect format for {path}")


def load_documents(cfg: FineTuneConfig) -> List[Document]:
    """
    Load the source corpus into a list of LangChain `Document` objects.

    Resolution order for the corpus path:
        1. `cfg.rag.corpus_path` if set
        2. `<raw_data_dir>/amazon_corpus.csv` if it exists
        3. Auto-bootstrap from HF dataset (calls `build_corpus_from_hf`)

    Args:
        cfg: Project config.

    Returns:
        List of `Document`s with `page_content` and `metadata={"source": ...}`.
    """
    # 1. Resolve the corpus path
    if cfg.rag.corpus_path:
        corpus_path = Path(cfg.rag.corpus_path)
    elif (cfg.paths.raw_data_dir / "amazon_corpus.csv").exists():
        corpus_path = cfg.paths.raw_data_dir / "amazon_corpus.csv"
    else:
        logger.info("No corpus found — bootstrapping from HF dataset...")
        corpus_path = build_corpus_from_hf(cfg, output_format="csv")

    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus path does not exist: {corpus_path}")

    fmt = cfg.rag.corpus_format if cfg.rag.corpus_format != "auto" else _detect_format(corpus_path)
    logger.info("Loading corpus: %s (format=%s)", corpus_path, fmt)

    # 2. Load with the right loader
    if fmt == "csv":
        # CSVLoader concatenates all columns by default — we want to control
        # the joining so chunks contain both question and answer context.
        import csv as _csv
        docs: List[Document] = []
        with corpus_path.open("r", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for i, row in enumerate(reader):
                content_parts = []
                for col in cfg.rag.corpus_text_columns:
                    if col in row and row[col]:
                        content_parts.append(f"{col.title()}: {row[col]}")
                content = "\n".join(content_parts)
                if content.strip():
                    docs.append(
                        Document(
                            page_content=content,
                            metadata={"source": str(corpus_path), "row": i},
                        )
                    )
    elif fmt == "jsonl":
        docs = []
        with corpus_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                obj = json.loads(line)
                content_parts = [
                    f"{col.title()}: {obj[col]}"
                    for col in cfg.rag.corpus_text_columns
                    if col in obj and obj[col]
                ]
                content = "\n".join(content_parts)
                if content.strip():
                    docs.append(
                        Document(
                            page_content=content,
                            metadata={"source": str(corpus_path), "row": i},
                        )
                    )
    elif fmt == "txt":
        if corpus_path.is_dir():
            loader = DirectoryLoader(
                str(corpus_path), glob="**/*.txt", loader_cls=TextLoader
            )
        else:
            loader = TextLoader(str(corpus_path), encoding="utf-8")
        docs = loader.load()
    else:
        raise ValueError(f"Unsupported corpus_format: {fmt}")

    logger.info("Loaded %d documents", len(docs))
    return docs


# ===========================================================================
# 3. Chunking
# ===========================================================================
def chunk_documents(
    docs: List[Document], cfg: FineTuneConfig
) -> List[Document]:
    """
    Split documents into overlapping chunks using RecursiveCharacterTextSplitter.

    The recursive splitter is the right default for mixed-structure text: it
    tries to split on paragraph breaks first, then sentences, then words —
    preserving semantic boundaries far better than naive fixed-length splits.

    Args:
        docs: Output of `load_documents()`.
        cfg: Project config (uses cfg.rag.chunk_size and chunk_overlap).

    Returns:
        List of chunked Documents, each ≤ chunk_size characters.
    """
    logger.info(
        "Chunking: size=%d, overlap=%d", cfg.rag.chunk_size, cfg.rag.chunk_overlap
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.rag.chunk_size,
        chunk_overlap=cfg.rag.chunk_overlap,
        separators=cfg.rag.chunk_separators,
        length_function=len,
    )
    chunks = splitter.split_documents(docs)
    logger.info("Produced %d chunks from %d documents", len(chunks), len(docs))
    return chunks


# ===========================================================================
# 4. Embeddings + FAISS vector store
# ===========================================================================
def _get_embeddings(cfg: FineTuneConfig) -> HuggingFaceEmbeddings:
    """Instantiate the sentence-transformers embedding model."""
    device = cfg.rag.embedding_device
    if device == "cuda" and not torch.cuda.is_available():
        logger.warning("CUDA requested for embeddings but unavailable — using CPU.")
        device = "cpu"

    logger.info(
        "Loading embedding model: %s (device=%s)",
        cfg.rag.embedding_model_id,
        device,
    )
    return HuggingFaceEmbeddings(
        model_name=cfg.rag.embedding_model_id,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": cfg.rag.embedding_normalize},
    )


def build_vector_store(
    chunks: List[Document], cfg: FineTuneConfig, persist: bool = True
) -> FAISS:
    """
    Embed the chunks and build a FAISS index.

    Args:
        chunks: Output of `chunk_documents()`.
        cfg: Project config.
        persist: If True, save the index to `cfg.paths.vector_store_dir`.

    Returns:
        A `FAISS` vector store ready for retrieval.
    """
    embeddings = _get_embeddings(cfg)

    logger.info("Embedding %d chunks and building FAISS index...", len(chunks))
    vs = FAISS.from_documents(chunks, embeddings)

    if persist:
        cfg.paths.vector_store_dir.mkdir(parents=True, exist_ok=True)
        vs.save_local(str(cfg.paths.vector_store_dir))
        logger.info("FAISS index persisted to %s", cfg.paths.vector_store_dir)

    return vs


def load_vector_store(cfg: FineTuneConfig) -> FAISS:
    """
    Reload a previously-built FAISS index from disk.

    Raises:
        FileNotFoundError: If no index exists at `cfg.paths.vector_store_dir`.
    """
    index_dir = cfg.paths.vector_store_dir
    if not (index_dir / "index.faiss").exists():
        raise FileNotFoundError(
            f"No FAISS index at {index_dir}. "
            "Build one first by running build_vector_store()."
        )

    embeddings = _get_embeddings(cfg)
    logger.info("Loading FAISS index from %s", index_dir)
    # allow_dangerous_deserialization=True needed for newer langchain versions
    # since FAISS uses pickle; safe because we wrote it ourselves.
    return FAISS.load_local(
        str(index_dir), embeddings, allow_dangerous_deserialization=True
    )


# ===========================================================================
# 5. Retriever
# ===========================================================================
def build_retriever(vector_store: FAISS, cfg: FineTuneConfig):
    """
    Wrap a FAISS vector store in a LangChain retriever.

    Supports plain similarity search (default) and MMR (Maximal Marginal
    Relevance) for diversity-aware retrieval — useful when many chunks
    near the query are near-duplicates of each other.
    """
    if cfg.rag.search_type == "mmr":
        logger.info(
            "Building MMR retriever (k=%d, fetch_k=%d, lambda=%.2f)",
            cfg.rag.top_k,
            cfg.rag.mmr_fetch_k,
            cfg.rag.mmr_lambda,
        )
        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": cfg.rag.top_k,
                "fetch_k": cfg.rag.mmr_fetch_k,
                "lambda_mult": cfg.rag.mmr_lambda,
            },
        )

    logger.info("Building similarity retriever (k=%d)", cfg.rag.top_k)
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": cfg.rag.top_k},
    )


# ===========================================================================
# 6. RAG chain
# ===========================================================================
def build_rag_chain(llm, retriever, cfg: FineTuneConfig) -> RetrievalQA:
    """
    Wire the LLM + retriever + RAG prompt template into a LangChain RetrievalQA.

    Args:
        llm: A LangChain-compatible LLM (use `src.llm_loader.load_llm`).
        retriever: A LangChain retriever (use `build_retriever`).
        cfg: Project config (uses cfg.rag.rag_prompt_template).

    Returns:
        A `RetrievalQA` chain. Call `.invoke({"query": "..."})` to query.
    """
    prompt = PromptTemplate(
        template=cfg.rag.rag_prompt_template,
        input_variables=["context", "question"],
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",            # "stuff" = concat all chunks into prompt
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,  # critical for Streamlit display + RAGAS
    )
    logger.info("RAG chain ready (chain_type='stuff', return_sources=True)")
    return chain


# ===========================================================================
# 7. Inference helper
# ===========================================================================
def answer(chain: RetrievalQA, question: str) -> Dict[str, Any]:
    """
    Run a single RAG query end-to-end.

    Returns:
        {
            "question": str,
            "answer":   str,            # cleaned model output
            "sources":  List[Document]  # the top-k retrieved chunks
        }
    """
    result = chain.invoke({"query": question})
    # Different LangChain versions return slightly different shapes — normalize.
    raw_answer = result.get("result") or result.get("answer") or ""
    sources = result.get("source_documents") or []

    return {
        "question": question,
        "answer": raw_answer.strip(),
        "sources": sources,
    }


# ===========================================================================
# 8. End-to-end convenience builder
# ===========================================================================
def build_full_pipeline(
    cfg: Optional[FineTuneConfig] = None,
    *,
    llm_mode: str = "auto",
    rebuild_index: bool = False,
):
    """
    One-call helper: load corpus, build/load index, load LLM, return RAG chain.

    Returns the chain plus a few intermediate objects so callers can inspect
    the index or swap the LLM later.
    """
    cfg = cfg or get_default_config()

    # Vector store: build if missing, else load
    if rebuild_index or not (cfg.paths.vector_store_dir / "index.faiss").exists():
        docs = load_documents(cfg)
        chunks = chunk_documents(docs, cfg)
        vs = build_vector_store(chunks, cfg)
    else:
        vs = load_vector_store(cfg)

    retriever = build_retriever(vs, cfg)

    # LLM (imported lazily to keep this module importable without GPU)
    from src.llm_loader import load_llm
    llm = load_llm(cfg, mode=llm_mode)

    chain = build_rag_chain(llm, retriever, cfg)
    return {
        "chain": chain,
        "retriever": retriever,
        "vector_store": vs,
        "llm": llm,
    }


__all__ = [
    "build_corpus_from_hf",
    "load_documents",
    "chunk_documents",
    "build_vector_store",
    "load_vector_store",
    "build_retriever",
    "build_rag_chain",
    "answer",
    "build_full_pipeline",
]
