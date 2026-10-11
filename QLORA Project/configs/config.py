"""
Central configuration for the AmazonQA-RAG project.

All hyperparameters, paths, and model identifiers live here so that experiments
are reproducible and no magic numbers appear in the pipeline code.

Switching between Mistral-7B and the Phi-2 fallback is a one-line change:
    ModelConfig.base_model_id = "microsoft/phi-2"
    ModelConfig.lora_target_modules = PHI2_LORA_TARGETS
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
# Resolve project root from this file's location so paths work on both
# Windows (local dev) and Linux (Colab) without modification.
#
# `__file__` is undefined when this code is executed inside a Jupyter/Colab
# notebook cell (notebook cells are strings, not files), so we fall back to
# the current working directory in that case.
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path.cwd()

# Colab override: if /content exists we are on Colab, prefer that workspace
# so that Drive mounting / checkpoint persistence works out of the box.
if Path("/content").exists():
    PROJECT_ROOT = Path("/content/AmazonQA-RAG")
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)


@dataclass
class PathConfig:
    """File-system paths used across all phases."""

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_data_dir: Path = PROJECT_ROOT / "data" / "processed"
    eval_data_dir: Path = PROJECT_ROOT / "data" / "eval"

    # Model artifacts
    adapter_dir: Path = PROJECT_ROOT / "artifacts" / "lora_adapter"
    merged_model_dir: Path = PROJECT_ROOT / "artifacts" / "merged_model"
    vector_store_dir: Path = PROJECT_ROOT / "artifacts" / "faiss_index"

    # Results
    results_dir: Path = PROJECT_ROOT / "results"
    logs_dir: Path = PROJECT_ROOT / "logs"

    def ensure_all(self) -> None:
        """Create every directory referenced above if it does not already exist."""
        for attr_name in self.__dataclass_fields__:
            path = getattr(self, attr_name)
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------
@dataclass
class DatasetConfig:
    """
    Dataset selection and preprocessing parameters.

    We default to `embedding-data/Amazon-QA` — a clean, well-formed
    Amazon question/answer corpus (~190k QA pairs). The legacy
    `amazon_qa` script-based dataset is deprecated; this one is direct-load.
    """

    hf_dataset_id: str = "embedding-data/Amazon-QA"
    hf_dataset_split: str = "train"

    # Subsample for free-tier training. Full 190k * 3 epochs would take ~12h on T4.
    # 10k samples * 1 epoch ≈ 45–60 min on T4 with seq_len=512, batch=4, grad_accum=4.
    train_sample_size: int = 10_000
    eval_sample_size: int = 500

    # Train/validation split ratio applied AFTER sub-sampling.
    val_split_ratio: float = 0.05

    # Tokenization
    max_seq_length: int = 512

    # Reproducibility
    seed: int = 42


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# Recommended LoRA target modules per architecture family.
# Determined by inspecting `model.named_modules()` for each base model.
MISTRAL_LORA_TARGETS: List[str] = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
PHI2_LORA_TARGETS: List[str] = ["q_proj", "k_proj", "v_proj", "dense"]
LLAMA_LORA_TARGETS: List[str] = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


@dataclass
class ModelConfig:
    """
    Base model + tokenizer settings.

    PRIMARY: Mistral-7B-Instruct-v0.2 (4-bit, ~5GB VRAM for weights).
    FALLBACK: microsoft/phi-2 (2.7B, ~2GB VRAM in 4-bit) — use if OOM on T4.
    """

    base_model_id: str = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer_id: Optional[str] = None  # defaults to base_model_id when None

    # 4-bit quantization (BitsAndBytes NF4 — the QLoRA paper recipe)
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "bfloat16"  # T4 supports bf16 via autocast
    bnb_4bit_use_double_quant: bool = True

    # Device / memory
    device_map: str = "auto"
    trust_remote_code: bool = True


@dataclass
class LoRAConfig:
    """
    Low-Rank Adaptation hyperparameters.

    rank=16, alpha=32 is the QLoRA paper default and is a sweet spot for
    7B-class models. Larger rank → more capacity but more VRAM + slower.
    """

    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    target_modules: List[str] = field(
        default_factory=lambda: MISTRAL_LORA_TARGETS.copy()
    )


# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------
@dataclass
class TrainingConfig:
    """
    SFTTrainer / TrainingArguments hyperparameters.

    Effective batch size = per_device_train_batch_size * gradient_accumulation_steps
                         = 4 * 4 = 16
    On T4 with Mistral-7B-4bit + LoRA + seq_len=512 this stays under 14GB VRAM.
    """

    # Optimizer
    learning_rate: float = 2e-4
    weight_decay: float = 0.001
    optim: str = "paged_adamw_8bit"   # memory-efficient AdamW for QLoRA
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.03
    max_grad_norm: float = 0.3

    # Batching
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    gradient_checkpointing: bool = True

    # Duration
    num_train_epochs: int = 1
    max_steps: int = -1               # -1 → train for full num_train_epochs

    # Precision (T4 supports fp16 natively; bf16 is emulated)
    fp16: bool = True
    bf16: bool = False

    # Logging / saving
    logging_steps: int = 25
    save_steps: int = 250
    save_total_limit: int = 2
    eval_strategy: str = "steps"
    eval_steps: int = 250
    report_to: str = "none"           # set to "wandb" if you want experiment tracking

    # Misc
    seed: int = 42
    group_by_length: bool = True      # speeds up training by ~20% via length bucketing


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
# Mistral-Instruct uses the [INST] ... [/INST] format. Keeping this in config
# means we never hardcode it in trainer or inference code.
PROMPT_TEMPLATE_MISTRAL: str = (
    "<s>[INST] You are a helpful Amazon shopping assistant. "
    "Answer the customer's question accurately and concisely.\n\n"
    "Question: {question} [/INST] {answer}</s>"
)

PROMPT_TEMPLATE_PHI2: str = (
    "Instruct: You are a helpful Amazon shopping assistant. "
    "Answer the customer's question accurately and concisely.\n"
    "Question: {question}\n"
    "Output: {answer}"
)


# ---------------------------------------------------------------------------
# RAG prompt templates (Phase 2)
# ---------------------------------------------------------------------------
# The RAG prompt MUST do three things well:
#   1. Clearly delimit retrieved context from the question (we use ### markers).
#   2. Instruct the model to ground its answer in the context.
#   3. Tell it what to do when the context is insufficient (avoid hallucination).
# These three lines together are the single biggest lever on RAGAS faithfulness.
RAG_PROMPT_TEMPLATE_MISTRAL: str = (
    "<s>[INST] You are a helpful Amazon shopping assistant. Use ONLY the context "
    "below to answer the customer's question. If the context does not contain "
    "the answer, say \"I don't have enough information to answer that.\" — do "
    "not invent product details, prices, or compatibility claims.\n\n"
    "### Context\n{context}\n\n"
    "### Question\n{question} [/INST]"
)

RAG_PROMPT_TEMPLATE_PHI2: str = (
    "Instruct: You are a helpful Amazon shopping assistant. Use ONLY the context "
    "below to answer the customer's question. If the context does not contain "
    "the answer, say \"I don't have enough information to answer that.\"\n\n"
    "### Context\n{context}\n\n"
    "### Question\n{question}\n"
    "Output:"
)


# ---------------------------------------------------------------------------
# RAG / retrieval configuration
# ---------------------------------------------------------------------------
@dataclass
class RAGConfig:
    """
    Retrieval Augmented Generation hyperparameters.

    Defaults are tuned for Amazon-style short QA: chunk_size=512 captures
    a typical product Q+A turn without wasting context window; top_k=5
    gives the LLM enough evidence to triangulate without blowing the prompt.
    """

    # -- Embedding model --
    # all-MiniLM-L6-v2: 384-dim, ~80 MB, 14k sentences/sec on CPU.
    # Strong recall on short QA, far cheaper than e5-large or bge-large.
    embedding_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cuda"        # auto-falls-back to cpu in code
    embedding_normalize: bool = True      # cosine similarity via inner-product

    # -- Document loading --
    # Where the source corpus lives. Either a CSV with `question,answer` cols,
    # a JSON-Lines file with the same fields, or a directory of .txt files.
    corpus_path: Optional[str] = None     # set by load helper if None
    corpus_format: str = "auto"           # "csv" | "jsonl" | "txt" | "auto"
    corpus_text_columns: List[str] = field(
        default_factory=lambda: ["question", "answer"]
    )
    # Subsample for fast indexing during development. None = use all rows.
    corpus_sample_size: Optional[int] = 5000

    # -- Chunking --
    chunk_size: int = 512                 # characters, not tokens
    chunk_overlap: int = 50
    chunk_separators: List[str] = field(
        default_factory=lambda: ["\n\n", "\n", ". ", " ", ""]
    )

    # -- Retrieval --
    top_k: int = 5
    search_type: str = "similarity"       # "similarity" | "mmr"
    # MMR settings (only used if search_type == "mmr") — encourages diverse
    # results so the LLM isn't shown 5 near-duplicate chunks.
    mmr_fetch_k: int = 20
    mmr_lambda: float = 0.5

    # -- Generation --
    # Lower temperature for RAG: we want the model to stick to the context.
    max_new_tokens: int = 256
    temperature: float = 0.3
    top_p: float = 0.9
    repetition_penalty: float = 1.1

    # -- Vector store --
    # FAISS index type. "Flat" is exact + small-corpus optimal.
    # Switch to "IVFFlat" with nlist=100 for corpora > 100k chunks.
    faiss_index_type: str = "Flat"

    # -- Prompt --
    rag_prompt_template: str = RAG_PROMPT_TEMPLATE_MISTRAL


# ---------------------------------------------------------------------------
# Evaluation configuration (Phase 3)
# ---------------------------------------------------------------------------
# RAGAS uses an LLM-as-judge for `faithfulness` and `answer_relevancy`, and an
# embedding model for `answer_similarity`-style metrics. Defaults below favour
# the OpenAI route (most reliable + matches the RAGAS docs) but the module
# supports a local-only fallback via HuggingFace pipelines (no API key needed)
# — see `evaluation/ragas_eval.py::_build_ragas_judge`.
@dataclass
class EvalConfig:
    """
    Phase 3 (RAGAS) evaluation hyperparameters.

    Three-system comparison: 'base', 'rag_base', 'rag_finetuned'.
    Defaults are tuned so the full eval finishes in ~15-25 min on a T4
    with `n_samples=100`.
    """

    # -- Held-out test set --
    # Sample size for the test set. 100 is the floor for stable RAGAS means;
    # 200 gives tighter confidence intervals at ~2x the cost.
    test_set_size: int = 100
    # Random seed used to pick the held-out slice. MUST differ from the seeds
    # used in DatasetConfig.seed so the eval rows weren't seen during training.
    test_set_seed: int = 2026
    # File the prepared test set is written to (read by the eval script).
    test_set_filename: str = "test_qa.csv"

    # -- Generation (used by all three systems for fair comparison) --
    # Higher max_new_tokens than RAG default so the base LLM doesn't get
    # truncated mid-sentence and tank `answer_relevancy` artificially.
    eval_max_new_tokens: int = 256
    eval_temperature: float = 0.3
    eval_top_p: float = 0.9

    # -- Output paths --
    summary_filename: str = "ragas_summary.csv"
    per_system_filename_template: str = "{system}_ragas_scores.csv"
    bar_chart_filename: str = "ragas_comparison.png"
    radar_chart_filename: str = "ragas_radar.png"

    # -- RAGAS judge LLM --
    # 'openai'   → use OpenAI via OPENAI_API_KEY env var (default, recommended)
    # 'local'    → spin up a local HF pipeline judge (free, slower, weaker)
    # 'auto'     → openai if OPENAI_API_KEY is set, else local
    ragas_judge_backend: str = "auto"
    ragas_openai_model: str = "gpt-4o-mini"      # cheap + accurate enough for RAGAS
    ragas_local_judge_model: str = "google/flan-t5-base"  # CPU-friendly fallback
    ragas_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # -- Metric selection --
    # If you add new metrics later, append them here AND import them in
    # `evaluation/ragas_eval.py::_get_ragas_metrics`.
    metrics: List[str] = field(
        default_factory=lambda: [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]
    )

    # -- Misc --
    # When True, runs each system on a 5-row debug slice instead of the full
    # test set. Useful for `--smoke-test` CLI flag.
    smoke_test_size: int = 5

    # Per-system display names + plot colours (publication-ready palette).
    system_display_names: dict = field(
        default_factory=lambda: {
            "base": "Base LLM",
            "rag_base": "RAG + Base LLM",
            "rag_finetuned": "RAG + Fine-tuned LLM",
        }
    )
    system_colors: dict = field(
        default_factory=lambda: {
            "base": "#9CA3AF",          # neutral grey
            "rag_base": "#60A5FA",      # blue
            "rag_finetuned": "#10B981", # emerald — our hero system
        }
    )


# ---------------------------------------------------------------------------
# Convenience aggregator
# ---------------------------------------------------------------------------
@dataclass
class FineTuneConfig:
    """One-stop bundle passed around between modules."""

    paths: PathConfig = field(default_factory=PathConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    prompt_template: str = PROMPT_TEMPLATE_MISTRAL


def get_default_config() -> FineTuneConfig:
    """Return the default project configuration with directories pre-created."""
    cfg = FineTuneConfig()
    cfg.paths.ensure_all()
    return cfg


def get_phi2_fallback_config() -> FineTuneConfig:
    """
    Return a configuration that swaps in Phi-2 (2.7B) for the base model.

    Use this if Mistral-7B OOMs on your T4 instance — Phi-2 in 4-bit needs
    only ~2GB for weights and trains 2-3x faster.
    """
    cfg = get_default_config()
    cfg.model.base_model_id = "microsoft/phi-2"
    cfg.lora.target_modules = PHI2_LORA_TARGETS.copy()
    cfg.prompt_template = PROMPT_TEMPLATE_PHI2
    cfg.rag.rag_prompt_template = RAG_PROMPT_TEMPLATE_PHI2
    cfg.training.per_device_train_batch_size = 8  # Phi-2 is smaller → bigger batches
    cfg.training.gradient_accumulation_steps = 2
    return cfg
