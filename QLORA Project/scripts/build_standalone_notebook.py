"""
Build the standalone single-file Colab notebook for AmazonQA-RAG.

Inlines configs/config.py + src/finetune.py + src/llm_loader.py + src/rag_pipeline.py
as code cells so a single .ipynb upload tests both Phase 1 and Phase 2 end-to-end.
"""

import json
from pathlib import Path

import nbformat as nbf

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "notebooks" / "00_standalone_test_phase1_and_2.ipynb"

CONFIG_PY = (PROJECT / "configs" / "config.py").read_text(encoding="utf-8")
FINETUNE_PY = (PROJECT / "src" / "finetune.py").read_text(encoding="utf-8")
LLM_LOADER_PY = (PROJECT / "src" / "llm_loader.py").read_text(encoding="utf-8")
RAG_PIPELINE_PY = (PROJECT / "src" / "rag_pipeline.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers — clean source code for inlining
# ---------------------------------------------------------------------------
def strip_for_inline(source: str) -> str:
    """
    Remove sys.path hacks and `from configs.config import ...` lines.
    The inlined notebook defines everything in one global namespace
    so module-style imports/relative paths are unnecessary.
    """
    lines = []
    skip_block = False
    for ln in source.splitlines():
        stripped = ln.strip()
        # Skip sys.path manipulation
        if stripped.startswith("sys.path.insert"):
            continue
        if stripped == "import sys" and "sys.path" in source[source.find(ln):source.find(ln)+200]:
            continue
        # Skip "from configs.config import ..." — all symbols are already global
        if stripped.startswith("from configs.config import") or stripped.startswith(
            "from configs import"
        ):
            continue
        # Skip "from src.xxx import ..." — same reason
        if stripped.startswith("from src."):
            continue
        # Skip "Allow ... `python -m ...`" docstring comments — irrelevant in notebook
        if stripped.startswith("# Allow imports when invoked") or stripped.startswith(
            "# Allow `python -m"
        ):
            continue
        lines.append(ln)
    return "\n".join(lines)


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(text)


def code(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(text)


# ---------------------------------------------------------------------------
# Build notebook
# ---------------------------------------------------------------------------
nb = nbf.v4.new_notebook()
cells = []

# ===== HEADER =====
cells.append(md(
    "# AmazonQA-RAG — Standalone Smoke Test (Phase 1 + Phase 2)\n"
    "\n"
    "> **Purpose:** Verify the full AmazonQA-RAG pipeline runs end-to-end on a Colab T4 in one notebook,\n"
    "> with no external repo or file uploads beyond this `.ipynb`.\n"
    "\n"
    "**What this notebook does (in order):**\n"
    "\n"
    "1. Installs all dependencies in ONE atomic pip transaction (no version drift)\n"
    "2. Restarts the kernel so freshly-installed NumPy 1.x is loaded into memory\n"
    "3. Inlines `configs/config.py`, `src/finetune.py`, `src/llm_loader.py`, `src/rag_pipeline.py` as code cells\n"
    "4. Runs a **fast** Phase 1 fine-tune (500 samples, 50 steps - ~5 min)\n"
    "5. Builds a Phase 2 FAISS index over a 1000-doc corpus\n"
    "6. Compares Base LLM vs RAG+Base vs RAG+Fine-tuned on 3 sample questions\n"
    "\n"
    "**Default model: `microsoft/phi-2` (2.7B)** - fits T4 free-tier comfortably (~2 GB VRAM), no HuggingFace token required, trains 2-3x faster than Mistral-7B. Mistral remains opt-in via the `USE_PHI2` toggle in Step 1.\n"
    "\n"
    "**Total runtime:** ~10 min on a free T4. If every cell passes, the full project will work.\n"
    "\n"
    "**Hardware required:** `Runtime -> Change runtime type -> T4 GPU`\n"
    "\n"
    "---\n"
    "## Smoke-test settings (reduced for speed)\n"
    "\n"
    "| Param | Smoke-test | Production |\n"
    "|---|---|---|\n"
    "| Base model | Phi-2 (2.7B) | Phi-2 or Mistral-7B-Instruct |\n"
    "| Training samples | 500 | 10,000 |\n"
    "| Training steps | 50 | full epoch (~625) |\n"
    "| Corpus size | 1,000 docs | 5,000 docs |\n"
    "| Expected runtime (T4) | ~10 min | ~75 min |\n"
))

# ===== STEP 0 — GPU CHECK =====
cells.append(md("---\n## Step 0 — GPU sanity check"))
cells.append(code(
    "!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv\n"
    "\n"
    "import torch\n"
    "print(f'\\nCUDA available : {torch.cuda.is_available()}')\n"
    "print(f'Device         : {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')\n"
    "print(f'VRAM total     : {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f} GB' if torch.cuda.is_available() else '')\n"
    "\n"
    "assert torch.cuda.is_available(), 'No GPU detected — switch runtime to T4 GPU before continuing'"
))

# ===== STEP 1 — INSTALL DEPS =====
cells.append(md(
    "---\n"
    "## Step 1 — Install dependencies (single atomic transaction)\n"
    "\n"
    "Two-cell pattern:\n"
    "1. **Install everything in ONE pip call** so pip's resolver picks compatible\n"
    "   binaries up-front (avoids the dreaded successive-install version drift).\n"
    "2. **Restart the kernel via the Jupyter API** so freshly-installed NumPy 1.x\n"
    "   replaces the in-memory NumPy 2.x that ships with Colab.\n"
    "\n"
    "After the restart, Colab will reconnect automatically (~10 sec).\n"
    "**Skip both cells in Step 1 on subsequent runs — packages persist on disk.**"
))
cells.append(code(
    "%%capture\n"
    "# ONE atomic install — every constraint resolved together. This is the\n"
    "# version lock-set that worked end-to-end on Colab T4 with the AmazonQA-RAG\n"
    "# project. Conflict warnings about gradio/diffusers/cupy/jax are harmless\n"
    "# (those are Colab's pre-installed extras we don't use).\n"
    "!pip install -q \\\n"
    "    \"numpy==1.26.4\" \\\n"
    "    \"torch==2.4.0\" \\\n"
    "    \"transformers==4.44.2\" \\\n"
    "    \"tokenizers==0.19.1\" \\\n"
    "    \"huggingface_hub==0.25.2\" \\\n"
    "    \"peft==0.13.2\" \\\n"
    "    \"trl==0.11.4\" \\\n"
    "    \"bitsandbytes==0.43.3\" \\\n"
    "    \"accelerate==0.34.2\" \\\n"
    "    \"datasets==2.21.0\" \\\n"
    "    \"sentence-transformers==3.0.1\" \\\n"
    "    \"faiss-cpu==1.8.0.post1\" \\\n"
    "    \"langchain==0.2.16\" \\\n"
    "    \"langchain-community==0.2.16\" \\\n"
    "    \"langchain-huggingface==0.0.3\" \\\n"
    "    \"fsspec==2024.6.1\" \\\n"
    "    \"sentencepiece==0.2.0\""
))

cells.append(md(
    "### Restart the kernel so the freshly-installed NumPy 1.x is loaded\n"
    "\n"
    "Colab will show *\"Kernel is restarting\"* / *\"Your session crashed\"* — **this is intentional and expected**.\n"
    "After the auto-reconnect, **skip the install cell AND this restart cell** and start running cells from the GPU check (Step 0) onward.\n"
    "\n"
    "If the auto-restart doesn't trigger, manually do **Runtime → Restart session** in the Colab top menu — same result."
))
cells.append(code(
    "# Reliable kernel restart — the official Jupyter API.\n"
    "# Same effect as 'Runtime → Restart session' from the Colab menu.\n"
    "import IPython\n"
    "IPython.Application.instance().kernel.do_shutdown(True)"
))

cells.append(md(
    "### Verify the version lock landed\n"
    "\n"
    "Run this cell after the kernel auto-reconnects. You want to see:\n"
    "```\n"
    "numpy           : 1.26.4\n"
    "torch           : 2.4.0\n"
    "transformers    : 4.44.2\n"
    "huggingface_hub : 0.25.2\n"
    "peft            : 0.13.2\n"
    "trl             : 0.11.4\n"
    "```\n"
    "If any version is different, do **Runtime → Disconnect and delete runtime** and start over from Step 0."
))
cells.append(code(
    "import numpy, torch, transformers, huggingface_hub, peft, trl\n"
    "print(f'numpy           : {numpy.__version__}')\n"
    "print(f'torch           : {torch.__version__}')\n"
    "print(f'transformers    : {transformers.__version__}')\n"
    "print(f'huggingface_hub : {huggingface_hub.__version__}')\n"
    "print(f'peft            : {peft.__version__}')\n"
    "print(f'trl             : {trl.__version__}')\n"
    "\n"
    "assert numpy.__version__.startswith('1.'), 'NumPy 1.x not loaded — restart kernel via menu and retry'\n"
    "print('\\nAll versions match the lock-set. Continue to HuggingFace login below.')"
))

cells.append(md(
    "### Authenticate with HuggingFace (only needed if you want Mistral-7B)\n"
    "\n"
    "**Default model is Phi-2** (Microsoft, 2.7B, not gated, fits T4 free-tier easily). If you want to try Mistral-7B instead:\n"
    "\n"
    "1. Accept the license at https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2\n"
    "2. Create a read-token at https://huggingface.co/settings/tokens\n"
    "3. In Colab, click the **key icon** in the left sidebar → **+ Add new secret** → name `HF_TOKEN`, value = your token, toggle **Notebook access** ON\n"
    "4. Set `USE_PHI2 = False` in the cell below\n"
    "\n"
    "**Recommendation: stick with Phi-2 for the smoke test** — Mistral-7B in 4-bit is on the edge of T4 VRAM and frequently OOMs on free-tier."
))
cells.append(code(
    "# DEFAULT: Phi-2. Phi-2 is the safe choice on free-tier Colab.\n"
    "# Set to False ONLY if you have a paid Colab tier OR have confirmed Mistral fits.\n"
    "USE_PHI2 = True\n"
    "\n"
    "if not USE_PHI2:\n"
    "    from huggingface_hub import login\n"
    "    try:\n"
    "        from google.colab import userdata\n"
    "        hf_token = userdata.get('HF_TOKEN')\n"
    "        login(token=hf_token)\n"
    "        print('Logged in to HuggingFace via Colab secret.')\n"
    "    except Exception as e:\n"
    "        print(f'No HF_TOKEN secret found ({e}).')\n"
    "        print('Falling back to Phi-2 — no authentication required.')\n"
    "        USE_PHI2 = True\n"
    "\n"
    "print(f'\\nModel selection: {\"microsoft/phi-2 (default, recommended)\" if USE_PHI2 else \"mistralai/Mistral-7B-Instruct-v0.2\"}')"
))

# ===== STEP 2 — INLINE CONFIG =====
cells.append(md(
    "---\n"
    "## Step 2 — Inline `configs/config.py`\n"
    "\n"
    "All hyperparameters live here as dataclasses. No magic numbers anywhere else.\n"
    "You can edit any value in this cell and re-run downstream cells to experiment."
))
cells.append(code(strip_for_inline(CONFIG_PY)))

cells.append(md(
    "### Load the right config based on the Phi-2 toggle from Step 1"
))
cells.append(code(
    "cfg = get_phi2_fallback_config() if USE_PHI2 else get_default_config()\n"
    "\n"
    "# Smoke-test overrides — DRASTICALLY reduce training time for verification.\n"
    "# Remove or raise these values for a real run.\n"
    "cfg.dataset.train_sample_size = 500\n"
    "cfg.dataset.val_split_ratio = 0.1\n"
    "cfg.training.max_steps = 50          # ~5 min instead of ~60\n"
    "cfg.training.logging_steps = 5\n"
    "cfg.training.save_steps = 50\n"
    "cfg.training.eval_steps = 50\n"
    "cfg.rag.corpus_sample_size = 1000\n"
    "\n"
    "print(f'Base model       : {cfg.model.base_model_id}')\n"
    "print(f'Train samples    : {cfg.dataset.train_sample_size}')\n"
    "print(f'Max train steps  : {cfg.training.max_steps}')\n"
    "print(f'Corpus size      : {cfg.rag.corpus_sample_size}')\n"
    "print(f'Adapter out dir  : {cfg.paths.adapter_dir}')"
))

# ===== STEP 3 — INLINE FINETUNE.PY =====
cells.append(md(
    "---\n"
    "## Step 3 — Inline `src/finetune.py` (Phase 1 engine)\n"
    "\n"
    "Defines: dataset loading + preprocessing, 4-bit base model loading,\n"
    "LoRA attachment, SFTTrainer construction, and inference helpers."
))
cells.append(code(strip_for_inline(FINETUNE_PY)))

# ===== STEP 4 — RUN PHASE 1 =====
cells.append(md(
    "---\n"
    "## Step 4 — Run Phase 1: load data + base model + LoRA + train\n"
    "\n"
    "This is the longest cell — ~5 min with smoke-test settings, ~60 min for full run."
))
cells.append(code(
    "# 4.1 Load and preprocess dataset\n"
    "dataset = load_and_preprocess_dataset(cfg)\n"
    "print(dataset)\n"
    "print('\\nFormatted example:\\n', dataset['train'][0]['text'][:400])"
))
cells.append(code(
    "# 4.2 Load 4-bit base model + tokenizer\n"
    "model, tokenizer = load_base_model_and_tokenizer(cfg)\n"
    "import torch\n"
    "print(f'\\nVRAM after base load: {torch.cuda.memory_allocated()/1024**3:.2f} GB')"
))
cells.append(code(
    "# 4.3 Baseline generation BEFORE fine-tuning — keep for comparison\n"
    "SAMPLE_Q = 'Does the Echo Dot 5th gen work with Apple Music?'\n"
    "baseline_prompt = cfg.prompt_template.format(question=SAMPLE_Q, answer='').rstrip()\n"
    "baseline_answer = generate_with_model(model, tokenizer, baseline_prompt, max_new_tokens=120)\n"
    "print('=== BEFORE fine-tuning ===\\n', baseline_answer)"
))
cells.append(code(
    "# 4.4 Attach LoRA adapters\n"
    "model = attach_lora_adapters(model, cfg)\n"
    "model.print_trainable_parameters()"
))
cells.append(code(
    "# 4.5 Build trainer\n"
    "trainer = build_trainer(model, tokenizer, dataset, cfg)"
))
cells.append(code(
    "# 4.6 Train (this is the long step — ~5 min smoke test, ~60 min full)\n"
    "trainer.train()"
))
cells.append(code(
    "# 4.7 Save adapter to disk\n"
    "trainer.model.save_pretrained(str(cfg.paths.adapter_dir))\n"
    "tokenizer.save_pretrained(str(cfg.paths.adapter_dir))\n"
    "!ls -lh {cfg.paths.adapter_dir}"
))
cells.append(code(
    "# 4.8 Generate AFTER fine-tuning with the SAME prompt → side-by-side\n"
    "ft_answer = generate_with_model(trainer.model, tokenizer, baseline_prompt, max_new_tokens=120)\n"
    "print('=== BEFORE ===\\n', baseline_answer)\n"
    "print('\\n=== AFTER  ===\\n', ft_answer)"
))
cells.append(code(
    "# 4.9 Free GPU before Phase 2\n"
    "import gc, torch\n"
    "del trainer, model\n"
    "gc.collect()\n"
    "torch.cuda.empty_cache()\n"
    "print(f'VRAM after cleanup: {torch.cuda.memory_allocated()/1024**3:.2f} GB')"
))

# ===== STEP 5 — INLINE LLM LOADER =====
cells.append(md(
    "---\n"
    "## Step 5 — Inline `src/llm_loader.py`\n"
    "\n"
    "Wraps the base + adapter into a LangChain-compatible `HuggingFacePipeline`.\n"
    "Used by both the RAG pipeline (Step 7) and the Streamlit app (Phase 4)."
))
cells.append(code(strip_for_inline(LLM_LOADER_PY)))

# ===== STEP 6 — INLINE RAG PIPELINE =====
cells.append(md(
    "---\n"
    "## Step 6 — Inline `src/rag_pipeline.py`\n"
    "\n"
    "Document loading, chunking, FAISS indexing, retrieval, and the `RetrievalQA`\n"
    "chain assembly. The `build_full_pipeline()` helper at the bottom does it all\n"
    "in one call."
))
cells.append(code(strip_for_inline(RAG_PIPELINE_PY)))

# ===== STEP 7 — RUN PHASE 2 =====
cells.append(md(
    "---\n"
    "## Step 7 — Run Phase 2: build the FAISS index\n"
    "\n"
    "Bootstraps a 1k-document corpus from the same Amazon QA dataset, chunks it,\n"
    "embeds with `all-MiniLM-L6-v2`, writes a FAISS flat index."
))
cells.append(code(
    "# 7.1 Bootstrap corpus + load\n"
    "corpus_path = build_corpus_from_hf(cfg, output_format='csv', overwrite=False)\n"
    "print('Corpus path:', corpus_path)\n"
    "\n"
    "docs = load_documents(cfg)\n"
    "print(f'Loaded {len(docs)} documents')\n"
    "print('\\nExample:\\n', docs[0].page_content[:300])"
))
cells.append(code(
    "# 7.2 Chunk\n"
    "chunks = chunk_documents(docs, cfg)\n"
    "print(f'{len(docs)} docs → {len(chunks)} chunks')"
))
cells.append(code(
    "# 7.3 Build FAISS index (writes to artifacts/faiss_index/)\n"
    "vs = build_vector_store(chunks, cfg, persist=True)\n"
    "print(f'\\nFAISS index built: {vs.index.ntotal} vectors, dim={vs.index.d}')"
))
cells.append(code(
    "# 7.4 Retrieval-only sanity check (no LLM)\n"
    "retriever = build_retriever(vs, cfg)\n"
    "hits = retriever.invoke('Is this Bluetooth speaker compatible with iPhone?')\n"
    "print(f'Top-{len(hits)} chunks:\\n')\n"
    "for i, doc in enumerate(hits, 1):\n"
    "    snippet = doc.page_content[:160].replace('\\n', ' ')\n"
    "    print(f'[{i}] {snippet}...')"
))

# ===== STEP 8 — ABLATION =====
cells.append(md(
    "---\n"
    "## Step 8 — Three-way qualitative ablation\n"
    "\n"
    "Same 3 questions through:\n"
    "1. **Base LLM** (no RAG, no fine-tuning)\n"
    "2. **RAG + Base** (retrieval-augmented, but no fine-tuning)\n"
    "3. **RAG + Fine-tuned** (the full system)\n"
    "\n"
    "Phase 3 will replace this eyeball test with RAGAS quantitative scoring."
))
cells.append(code(
    "import gc, torch\n"
    "\n"
    "QUERIES = [\n"
    "    'Is the Echo Dot 5th gen waterproof?',\n"
    "    'Does this USB-C cable support 100W fast charging?',\n"
    "    'How long is the warranty on Kindle Paperwhite?',\n"
    "]\n"
    "results = {q: {} for q in QUERIES}\n"
    "\n"
    "def free_gpu():\n"
    "    gc.collect()\n"
    "    if torch.cuda.is_available():\n"
    "        torch.cuda.empty_cache()"
))
cells.append(code(
    "# 8a — Base LLM only\n"
    "base_llm = load_llm(cfg, mode='base')\n"
    "for q in QUERIES:\n"
    "    prompt = cfg.prompt_template.format(question=q, answer='').rstrip()\n"
    "    out = base_llm.invoke(prompt)\n"
    "    results[q]['base'] = out.strip()[:250]\n"
    "    print(f'\\nQ: {q}\\nA: {results[q][\"base\"]}')\n"
    "del base_llm; free_gpu()"
))
cells.append(code(
    "# 8b — RAG + Base LLM\n"
    "base_llm = load_llm(cfg, mode='base')\n"
    "rag_base = build_rag_chain(base_llm, retriever, cfg)\n"
    "for q in QUERIES:\n"
    "    out = answer(rag_base, q)\n"
    "    results[q]['rag_base'] = out['answer'][:250]\n"
    "    print(f'\\nQ: {q}\\nA: {results[q][\"rag_base\"]}')\n"
    "del base_llm, rag_base; free_gpu()"
))
cells.append(code(
    "# 8c — RAG + Fine-tuned LLM (the full system)\n"
    "ft_llm = load_llm(cfg, mode='finetuned')\n"
    "rag_ft = build_rag_chain(ft_llm, retriever, cfg)\n"
    "for q in QUERIES:\n"
    "    out = answer(rag_ft, q)\n"
    "    results[q]['rag_ft'] = out['answer'][:250]\n"
    "    print(f'\\nQ: {q}\\nA: {results[q][\"rag_ft\"]}')"
))
cells.append(code(
    "# Pretty side-by-side\n"
    "import pandas as pd\n"
    "df = pd.DataFrame(results).T\n"
    "df.columns = ['Base LLM', 'RAG + Base', 'RAG + Fine-tuned']\n"
    "df.index.name = 'Question'\n"
    "df"
))

# ===== STEP 9 — DRIVE BACKUP =====
cells.append(md(
    "---\n"
    "## Step 9 — Persist artifacts to Google Drive (optional)\n"
    "\n"
    "Colab sessions die after ~12h idle. Backing up the LoRA adapter + FAISS\n"
    "index to Drive means later phases can resume from a fresh runtime."
))
cells.append(code(
    "try:\n"
    "    from google.colab import drive\n"
    "    drive.mount('/content/drive')\n"
    "    DEST = '/content/drive/MyDrive/AmazonQA-RAG'\n"
    "    !mkdir -p \"{DEST}/lora_adapter\" \"{DEST}/faiss_index\"\n"
    "    !cp -r {cfg.paths.adapter_dir}/* \"{DEST}/lora_adapter/\"\n"
    "    !cp -r {cfg.paths.vector_store_dir}/* \"{DEST}/faiss_index/\"\n"
    "    print(f'Artifacts backed up to: {DEST}')\n"
    "except Exception as e:\n"
    "    print(f'(Skipping Drive backup: {e})')"
))

# ===== FOOTER =====
cells.append(md(
    "---\n"
    "## Smoke test complete\n"
    "\n"
    "If every cell ran without error and Step 8 produced sensible answers,\n"
    "**both Phase 1 (QLoRA fine-tuning) and Phase 2 (RAG pipeline) are working**.\n"
    "\n"
    "### Going from smoke test → production run\n"
    "\n"
    "Re-run after deleting these smoke-test overrides in the Step 2 config cell:\n"
    "\n"
    "```python\n"
    "cfg.dataset.train_sample_size = 500    # remove → uses 10,000\n"
    "cfg.training.max_steps = 50            # remove → trains 1 full epoch\n"
    "cfg.rag.corpus_sample_size = 1000      # remove → indexes 5,000 docs\n"
    "```\n"
    "\n"
    "### Troubleshooting\n"
    "\n"
    "| Symptom | Fix |\n"
    "|---|---|\n"
    "| `Your session crashed` after running cell 4.2 (model load) | OOM. Set `USE_PHI2 = True` in Step 1 and re-run from Step 1 onward. Mistral-7B is on the edge of T4 free-tier. |\n"
    "| `numpy.dtype size changed, may indicate binary incompatibility` | NumPy 1.x didn't load. Verify with `import numpy; numpy.__version__` — if it shows 2.x, do **Runtime -> Disconnect and delete runtime** and start over from Step 0. |\n"
    "| `cannot import name 'HF_HUB_ENABLE_HF_TRANSFER'` | huggingface_hub version mismatch. Re-run Step 1's atomic install cell — version 0.25.2 is the correct lock. |\n"
    "| `NameError: load_and_preprocess_dataset` after a kernel restart | Memory was wiped. Re-run Step 2 (config), the cfg cell, and Step 3 (finetune) cells in order. Packages persist on disk; function definitions don't. |\n"
    "| `OSError: ... Mistral gated` | Accept license at https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 + add `HF_TOKEN` Colab secret. Or just leave `USE_PHI2 = True`. |\n"
    "| LLM repeats the prompt verbatim | `return_full_text=False` is set inside `load_llm` — verify Step 5's cell ran (look for the `def load_llm` definition in `dir()`). |\n"
    "| `FAISS deserialization` error | `allow_dangerous_deserialization=True` is already set in `load_vector_store` — should not happen. If it does, re-run Step 6 (RAG inline). |\n"
    "\n"
    "### Critical lesson on kernel restarts\n"
    "\n"
    "Whenever Colab restarts the kernel (deliberately via Step 1's restart cell, or after an OOM crash):\n"
    "- **Disk-installed packages are preserved**\n"
    "- **In-memory variables and function definitions are wiped**\n"
    "\n"
    "After ANY restart, you must re-run the inlined module cells (Step 2, Step 3, Step 5, Step 6) before any cell that calls those functions. Skip the install cell and the kill cell.\n"
    "\n"
    "### Next: Phase 3 — RAGAS evaluation\n"
    "\n"
    "Will quantify what Step 8 showed qualitatively, using: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`."
))

# ---------------------------------------------------------------------------
# Assemble notebook
# ---------------------------------------------------------------------------
nb.cells = cells
nb.metadata = {
    "accelerator": "GPU",
    "colab": {"gpuType": "T4", "provenance": []},
    "kernelspec": {"display_name": "Python 3", "name": "python3"},
    "language_info": {"name": "python"},
}

with OUT.open("w", encoding="utf-8") as f:
    nbf.write(nb, f)

# Summary
print(f"Wrote: {OUT}")
print(f"Cells : {len(cells)}  ({sum(1 for c in cells if c.cell_type=='markdown')} md "
      f"+ {sum(1 for c in cells if c.cell_type=='code')} code)")
print(f"Size  : {OUT.stat().st_size/1024:.1f} KB")
