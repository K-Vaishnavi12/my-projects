"""Configuration package."""
from configs.config import (  # noqa: F401
    FineTuneConfig,
    PathConfig,
    DatasetConfig,
    ModelConfig,
    LoRAConfig,
    TrainingConfig,
    RAGConfig,
    EvalConfig,
    get_default_config,
    get_phi2_fallback_config,
    RAG_PROMPT_TEMPLATE_MISTRAL,
    RAG_PROMPT_TEMPLATE_PHI2,
)
