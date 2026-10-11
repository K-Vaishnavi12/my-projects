"""
QLoRA fine-tuning engine for the AmazonQA-RAG project.

This module wraps the full Phase 1 pipeline:
  1. Load + preprocess the Amazon QA dataset
  2. Load the base LLM in 4-bit (BitsAndBytes NF4)
  3. Attach LoRA adapters (PEFT)
  4. Train with SFTTrainer (TRL)
  5. Save adapter weights + run a smoke-test generation

It is imported by `notebooks/01_qlora_finetune.ipynb` and can also be invoked
directly from the CLI:  python -m src.finetune

The notebook contains the narrative; this file contains the logic.
"""

from __future__ import annotations

import gc
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Allow `python -m src.finetune` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from datasets import Dataset, DatasetDict, load_dataset
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer

from configs.config import FineTuneConfig, get_default_config

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("amazonqa.finetune")


# ===========================================================================
# 1. Data loading + preprocessing
# ===========================================================================
def load_and_preprocess_dataset(cfg: FineTuneConfig) -> DatasetDict:
    """
    Load the Amazon QA dataset from HuggingFace and format it for SFT.

    The `embedding-data/Amazon-QA` dataset ships rows of the form:
        {"query": "...", "pos": ["answer 1", "answer 2", ...]}
    We flatten this to (question, answer) pairs and then apply the
    instruction-tuning prompt template defined in the config.

    Args:
        cfg: Project configuration.

    Returns:
        A `DatasetDict` with `train` and `validation` splits, each row
        containing a single `text` column ready for SFTTrainer.

    Raises:
        RuntimeError: If the dataset cannot be downloaded.
    """
    logger.info("Downloading dataset: %s", cfg.dataset.hf_dataset_id)
    try:
        raw = load_dataset(cfg.dataset.hf_dataset_id, split=cfg.dataset.hf_dataset_split)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load dataset '{cfg.dataset.hf_dataset_id}'. "
            f"Check your internet connection and HuggingFace cache. Original error: {exc}"
        ) from exc

    logger.info("Raw dataset loaded: %d rows", len(raw))

    # ------------------------------------------------------------------
    # Sub-sample BEFORE flattening to keep memory low
    # ------------------------------------------------------------------
    sample_size = min(cfg.dataset.train_sample_size, len(raw))
    raw = raw.shuffle(seed=cfg.dataset.seed).select(range(sample_size))

    # ------------------------------------------------------------------
    # Flatten {query, pos:[...]} → list of {question, answer}
    # ------------------------------------------------------------------
    def _flatten(example: Dict) -> Dict:
        question = example.get("query") or example.get("question") or ""
        answers = example.get("pos") or example.get("answers") or []
        # Use the first (highest-quality) answer
        answer = answers[0] if isinstance(answers, list) and answers else ""
        return {"question": question.strip(), "answer": answer.strip()}

    flat = raw.map(_flatten, remove_columns=raw.column_names)
    flat = flat.filter(lambda r: len(r["question"]) > 5 and len(r["answer"]) > 5)

    logger.info("After flatten + filter: %d rows", len(flat))

    # ------------------------------------------------------------------
    # Apply the instruction prompt template
    # ------------------------------------------------------------------
    def _format(example: Dict) -> Dict:
        text = cfg.prompt_template.format(
            question=example["question"], answer=example["answer"]
        )
        return {"text": text}

    formatted = flat.map(_format, remove_columns=flat.column_names)

    # ------------------------------------------------------------------
    # Train / validation split
    # ------------------------------------------------------------------
    splits = formatted.train_test_split(
        test_size=cfg.dataset.val_split_ratio, seed=cfg.dataset.seed
    )
    ds = DatasetDict(train=splits["train"], validation=splits["test"])
    logger.info(
        "Final split → train: %d | validation: %d",
        len(ds["train"]),
        len(ds["validation"]),
    )

    # Persist a copy for reproducibility
    ds.save_to_disk(str(cfg.paths.processed_data_dir / "amazon_qa_sft"))
    return ds


# ===========================================================================
# 2. Model + tokenizer loading
# ===========================================================================
def load_base_model_and_tokenizer(
    cfg: FineTuneConfig,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the base LLM in 4-bit and its tokenizer.

    Uses the QLoRA recipe: NF4 quantization + double-quant + bf16 compute dtype.
    Gradient checkpointing is enabled by the trainer, so we call
    `prepare_model_for_kbit_training` to wire up the necessary hooks.

    Returns:
        Tuple of (4-bit-quantized model ready for LoRA, tokenizer).
    """
    logger.info("Configuring BitsAndBytes 4-bit quantization (NF4)")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=cfg.model.load_in_4bit,
        bnb_4bit_quant_type=cfg.model.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=getattr(torch, cfg.model.bnb_4bit_compute_dtype),
        bnb_4bit_use_double_quant=cfg.model.bnb_4bit_use_double_quant,
    )

    logger.info("Loading base model: %s", cfg.model.base_model_id)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            cfg.model.base_model_id,
            quantization_config=bnb_config,
            device_map=cfg.model.device_map,
            trust_remote_code=cfg.model.trust_remote_code,
        )
    except torch.cuda.OutOfMemoryError as exc:
        raise RuntimeError(
            "OOM while loading the base model. Options:\n"
            "  1. Use the Phi-2 fallback config (get_phi2_fallback_config())\n"
            "  2. Restart the Colab runtime to free leaked memory\n"
            "  3. Reduce max_seq_length in DatasetConfig"
        ) from exc

    model.config.use_cache = False        # required for gradient checkpointing
    model.config.pretraining_tp = 1       # disable tensor parallelism slicing

    logger.info("Preparing model for k-bit training")
    model = prepare_model_for_kbit_training(model)

    # ------------------------------------------------------------------
    # Tokenizer
    # ------------------------------------------------------------------
    tokenizer_id = cfg.model.tokenizer_id or cfg.model.base_model_id
    logger.info("Loading tokenizer: %s", tokenizer_id)
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_id, trust_remote_code=cfg.model.trust_remote_code
    )
    # Causal LMs train left→right; padding must go on the right during SFT
    # so loss isn't computed on padding tokens that bleed into the answer.
    tokenizer.padding_side = "right"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


# ===========================================================================
# 3. LoRA attachment
# ===========================================================================
def attach_lora_adapters(
    model: AutoModelForCausalLM, cfg: FineTuneConfig
) -> AutoModelForCausalLM:
    """
    Wrap the base model with LoRA adapters using PEFT.

    Only the adapter weights become trainable; the 4-bit base stays frozen,
    which is what makes QLoRA fit on consumer GPUs.

    Returns:
        PEFT-wrapped model with trainable LoRA parameters.
    """
    logger.info(
        "Attaching LoRA: r=%d, alpha=%d, dropout=%.2f, targets=%s",
        cfg.lora.r,
        cfg.lora.lora_alpha,
        cfg.lora.lora_dropout,
        cfg.lora.target_modules,
    )
    lora_config = LoraConfig(
        r=cfg.lora.r,
        lora_alpha=cfg.lora.lora_alpha,
        lora_dropout=cfg.lora.lora_dropout,
        bias=cfg.lora.bias,
        task_type=cfg.lora.task_type,
        target_modules=cfg.lora.target_modules,
    )
    model = get_peft_model(model, lora_config)

    # Report trainable param count — should be ~0.1–1% of total for QLoRA
    trainable, total = 0, 0
    for _, p in model.named_parameters():
        total += p.numel()
        if p.requires_grad:
            trainable += p.numel()
    logger.info(
        "Trainable params: %s / %s  (%.4f%%)",
        f"{trainable:,}",
        f"{total:,}",
        100 * trainable / total,
    )
    return model


# ===========================================================================
# 4. Training
# ===========================================================================
def build_trainer(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    dataset: DatasetDict,
    cfg: FineTuneConfig,
) -> SFTTrainer:
    """Construct a TRL SFTTrainer wired with our hyperparameters."""
    logger.info("Building TrainingArguments")
    training_args = TrainingArguments(
        output_dir=str(cfg.paths.adapter_dir),
        num_train_epochs=cfg.training.num_train_epochs,
        max_steps=cfg.training.max_steps,
        per_device_train_batch_size=cfg.training.per_device_train_batch_size,
        per_device_eval_batch_size=cfg.training.per_device_eval_batch_size,
        gradient_accumulation_steps=cfg.training.gradient_accumulation_steps,
        gradient_checkpointing=cfg.training.gradient_checkpointing,
        optim=cfg.training.optim,
        learning_rate=cfg.training.learning_rate,
        weight_decay=cfg.training.weight_decay,
        lr_scheduler_type=cfg.training.lr_scheduler_type,
        warmup_ratio=cfg.training.warmup_ratio,
        max_grad_norm=cfg.training.max_grad_norm,
        fp16=cfg.training.fp16,
        bf16=cfg.training.bf16,
        logging_steps=cfg.training.logging_steps,
        save_steps=cfg.training.save_steps,
        save_total_limit=cfg.training.save_total_limit,
        eval_strategy=cfg.training.eval_strategy,
        eval_steps=cfg.training.eval_steps,
        report_to=cfg.training.report_to,
        seed=cfg.training.seed,
        group_by_length=cfg.training.group_by_length,
        logging_dir=str(cfg.paths.logs_dir),
    )

    logger.info("Building SFTTrainer")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        dataset_text_field="text",
        max_seq_length=cfg.dataset.max_seq_length,
        args=training_args,
        packing=False,  # packing speeds up training but hurts loss on QA-style data
    )
    return trainer


def train(cfg: Optional[FineTuneConfig] = None) -> Path:
    """
    Run the full Phase 1 pipeline end-to-end.

    Args:
        cfg: Optional override config. Defaults to `get_default_config()`.

    Returns:
        Path to the saved LoRA adapter directory.
    """
    cfg = cfg or get_default_config()
    cfg.paths.ensure_all()

    # 1. Data
    dataset = load_and_preprocess_dataset(cfg)

    # 2. Model + tokenizer
    model, tokenizer = load_base_model_and_tokenizer(cfg)

    # 3. LoRA
    model = attach_lora_adapters(model, cfg)

    # 4. Trainer
    trainer = build_trainer(model, tokenizer, dataset, cfg)

    logger.info("Starting training")
    trainer.train()

    # 5. Save adapter (NOT the full model — only the small LoRA weights)
    logger.info("Saving LoRA adapter to %s", cfg.paths.adapter_dir)
    trainer.model.save_pretrained(str(cfg.paths.adapter_dir))
    tokenizer.save_pretrained(str(cfg.paths.adapter_dir))

    # 6. Free memory before returning
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()

    return cfg.paths.adapter_dir


# ===========================================================================
# 5. Smoke-test inference (used by the notebook for before/after comparison)
# ===========================================================================
def generate_with_model(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 200,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    """
    Run a single forward generation pass and return the decoded completion.

    Used both for the "before fine-tuning" baseline and "after fine-tuning"
    comparison in the notebook.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Strip the echoed prompt
    if text.startswith(prompt):
        text = text[len(prompt):].strip()
    return text


def load_finetuned_model(
    cfg: FineTuneConfig,
) -> Tuple[PeftModel, AutoTokenizer]:
    """
    Reload the base model + apply the saved LoRA adapter for inference.

    This is the canonical way to use the fine-tuned model in downstream
    phases (RAG, evaluation, Streamlit app).
    """
    base, tokenizer = load_base_model_and_tokenizer(cfg)
    logger.info("Loading LoRA adapter from %s", cfg.paths.adapter_dir)
    model = PeftModel.from_pretrained(base, str(cfg.paths.adapter_dir))
    model.eval()
    return model, tokenizer


# ===========================================================================
# CLI entry point
# ===========================================================================
if __name__ == "__main__":
    adapter_path = train()
    print(f"\nDone. Adapter saved to: {adapter_path}")
