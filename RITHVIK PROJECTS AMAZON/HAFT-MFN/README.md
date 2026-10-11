# HAFT-MFN

Hey — this is my implementation of **HAFT-MFN** (Hierarchical Attention Fusion Transformer with Multimodal Feature Normalization), the model from the paper *"Deep Learning Architectures for Multimodal Data Processing with Enhanced Feature Representation and Fusion."*

In plain English: the model takes in **text, images, audio, and video** all at once, figures out how they relate to each other, and then makes a prediction (sentiment, emotion, or action, depending on what you're doing). Think of it as teaching a network to "watch and listen" the way a person would when trying to understand a scene.

---

## What's inside

Here's a quick tour so you know what you're looking at:

1. What the project actually does
2. What every folder and file is for
3. How data flows through the model (with a little diagram)
4. The config file, explained
5. The three data modes (and why they exist)
6. Installing everything
7. Every command you can run
8. What the output means
9. A quick honesty note about numbers
10. How to add your own stuff

---

## 1. What it actually does

You give it up to four inputs per sample — a sentence, a picture, an audio clip, and a short video — and it gives you back:

- A **classification prediction** (which sentiment, which emotion, which action).
- A **regression prediction** for continuous emotional dimensions like valence and arousal.
- Some **contrastive projections** used behind the scenes to line up the modalities in a shared space.
- **Attention maps and gate values** so you can peek inside and see which modality the model is paying attention to.

The repo also handles all the boring-but-important stuff:

- Training loop with mixed precision on GPU, automatic fallback to CPU, gradient accumulation, checkpoints, resume, cosine LR schedule with warmup.
- Evaluation with the right metrics for each task family (sentiment / emotion / action).
- A full ablation study across 10 configurations so you can prove each piece is pulling its weight.
- Efficiency numbers (parameters, rough FLOPs, inference time).
- Some visualization helpers for the architecture, ablation results, attention, and modality gates.

---

## 2. What every folder is for

```
HAFT-MFN/
├── README.md                     ← you are here
├── requirements.txt              ← pip dependencies
├── environment.yml               ← optional conda env
├── .gitignore
│
├── configs/
│   └── config.yaml               ← one file to rule them all — model, data, training knobs
│
├── models/                       ← the neural network itself
│   ├── text_encoder.py                  RoBERTa-base (with an offline fallback so tests run without downloads)
│   ├── image_encoder.py                 ResNet-50 + ViT-B/16, glued together with spatial attention
│   ├── audio_encoder.py                 Wav2Vec 2.0 + classic MFCC features
│   ├── video_encoder.py                 A TimeSformer-style branch + a 3D-CNN (r3d_18)
│   ├── adaptive_feature_normalization.py Puts all four modalities on the same scale without erasing their identity
│   ├── pairwise_cross_attention.py      Level 1 — every pair of modalities talks to each other
│   ├── trimodal_gated_fusion.py         Level 2 — three-at-a-time fusion with learnable gates
│   ├── global_multimodal_fusion.py      Level 3 — one big self-attention pass over everything
│   ├── multitask_head.py                Classification + regression + contrastive heads
│   └── haft_mfn.py                      Puts it all together, plus ablation switches
│
├── datasets/                     ← where the data comes from
│   ├── common.py                        Mock and preprocessed-folder datasets + the collate function
│   ├── cmu_mosei.py                     CMU-MOSEI loader
│   ├── meld.py                          MELD loader (7 emotion classes)
│   ├── vggsound.py                      VGGSound loader (309 classes)
│   ├── iemocap.py                       IEMOCAP loader
│   └── __init__.py                      get_dataset(cfg, split) — picks the right one for you
│
├── losses/                       ← the objectives
│   ├── classification_loss.py           Cross-entropy
│   ├── regression_loss.py               MSE
│   ├── contrastive_loss.py              Symmetric InfoNCE between modality projections
│   └── multitask_loss.py                Weighted sum of the three above
│
├── training/                     ← the training loop
│   ├── trainer.py                       Trainer class — fit, validate, save/load checkpoints
│   ├── optimizer.py                     AdamW with two separate learning rates
│   └── scheduler.py                     Cosine annealing + warmup
│
├── evaluation/
│   ├── metrics.py                       accuracy, Acc-2/Acc-7, weighted/macro F1, MAE, Pearson, Top-k, mAP
│   ├── evaluate.py                      One-shot evaluate_model(...) helper
│   └── comparisons.py                   The six paper-reference tables, stored verbatim
│
├── experiments/                  ← the things you actually run
│   ├── train.py                         Kick off training
│   ├── evaluate.py                      Evaluate a checkpoint
│   ├── ablation.py                      Run all 10 ablation variants
│   ├── efficiency.py                    Measure params / FLOPs / inference time
│   └── demo.py                          A friendly end-to-end demo
│
├── visualization/
│   ├── architecture.py                  Draws the block diagram
│   ├── results.py                       Curves, bar charts, confusion matrices
│   └── attention.py                     Attention maps + gating plots + missing-modality analysis
│
├── tests/                        ← quick sanity checks (CPU, no downloads)
│   ├── test_encoders.py
│   ├── test_fusion.py
│   ├── test_model.py
│   └── test_training_step.py
│
├── docs/
│   └── viva.md                          Q&A explaining every design choice in plain language
│
├── notebooks/
│   └── demo.ipynb                       Jupyter version of the demo
│
├── checkpoints/                  ← training checkpoints land here
├── results/                      ← runtime outputs
└── figures/                      ← generated PNGs
```

---

## 3. How data flows through the model

Here's the mental model. For a batch of samples containing text, image, audio and video, this is what happens:

```
text  ─► TextEncoder  ─►
image ─► ImageEncoder ─►      each modality turns into a
audio ─► AudioEncoder ─►      sequence of vectors of size d_model
video ─► VideoEncoder ─►
                    │
                    ▼
       Adaptive Feature Normalization
       (equalizes scale, keeps the "flavor" of each modality)
                    │
                    ▼
     Level 1 — every pair of modalities cross-attends
              (text↔image, text↔audio, ... 6 pairs)
                    │
                    ▼
     Level 2 — trimodal groups with learnable gates
              (which modality matters right now?)
                    │
                    ▼
     Level 3 — one big self-attention over
              modality + pair + trimodal tokens
                    │
                    ▼
             Prediction heads
             ├── classification (cross-entropy)
             ├── regression     (MSE for valence/arousal)
             └── contrastive    (aligning modalities)
```

If you want to turn any of these off for an ablation, just call `model.configure_ablation(use_afn=False, ...)`. The ablation script does this automatically for all 10 variants.

---

## 4. The config file

Everything lives in `configs/config.yaml`. The interesting knobs are:

- **model** — embedding size (768), attention heads (8), FFN size (2048), dropout, activation, number of global-fusion layers, contrastive temperature.
- **encoders** — pretrained model names, max text length, image size, audio sample rate, video frames and frame size, and whether to actually download pretrained weights (turn this off if you're offline).
- **fusion** — the six modality pairs and four trimodal groups.
- **task** — how many classes, regression dimensions, and the three loss weights.
- **training** — epochs (50 by default), batch size (32), gradient accumulation, two learning rates (one for pretrained, one for new layers), weight decay, warmup, cosine schedule, mixed precision, seed, checkpoint directory.
- **data** — which dataset and which mode (mock / demo / full).

---

## 5. The three data modes

- **mock** — everything is random tensors with the right shapes. Runs in seconds. Use this to check that nothing is broken.
- **demo** — a handful of synthetic samples. Slightly more realistic. Nice for interactive tinkering.
- **full** — reads real preprocessed samples from `data/{dataset}/{split}/*.pt`. Each `.pt` file should be a dict with these keys:
  - `input_ids` — LongTensor `[max_len]`
  - `attention_mask` — LongTensor `[max_len]`
  - `image` — FloatTensor `[3, H, W]`
  - `audio` — FloatTensor `[T]` (at the configured sample rate)
  - `video` — FloatTensor `[F, 3, H, W]`
  - `labels` — Long scalar
  - `regression` — FloatTensor `[2]` (valence, arousal)

You'll need to grab CMU-MOSEI / MELD / VGGSound / IEMOCAP from their official sources yourself — each has its own license.

---

## 6. Installing

Open PowerShell and:

```powershell
cd "C:\Users\kvais\OneDrive\Desktop\RITHVIK PROJECTS AMAZON\HAFT-MFN"
pip install -r requirements.txt
```

That's it. It runs on CPU out of the box. If a GPU is around, mixed precision kicks in automatically.

---

## 7. Every command you can run

All from the project root.

**Sanity checks (fast, no downloads):**
```powershell
python tests\test_encoders.py
python tests\test_fusion.py
python tests\test_model.py
python tests\test_training_step.py
```

**Full demo — best place to start:**
```powershell
python experiments\demo.py
```
This builds the model, runs one forward + backward pass, evaluates on mock data, and prints all six paper-reference tables at the end.

**Just print the reference tables:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python -c "from evaluation.comparisons import ALL_TABLES, format_table_markdown; [print(format_table_markdown(t, h, r), '\n') for (t,h,r) in ALL_TABLES.values()]"
```

**Train (mock, 1 epoch, quick):**
```powershell
python -m experiments.train --config configs\config.yaml --dataset mock --mode mock --epochs 1
```

**Train on a real dataset (after you've preprocessed it):**
```powershell
python -m experiments.train --config configs\config.yaml --dataset cmu_mosei --mode full
```

**Resume from a checkpoint:**
```powershell
python -m experiments.train --config configs\config.yaml --resume checkpoints\last.pt
```

**Evaluate a checkpoint:**
```powershell
python -m experiments.evaluate --config configs\config.yaml --dataset mock --mode mock --checkpoint checkpoints\best.pt
```

**Run the full ablation study:**
```powershell
python experiments\ablation.py --mode mock
```

**Measure efficiency:**
```powershell
python experiments\efficiency.py
```

**Draw the architecture diagram:**
```powershell
python -c "from visualization import render_architecture; print(render_architecture())"
```

**Open the notebook:**
```powershell
jupyter notebook notebooks\demo.ipynb
```

---

## 8. What the output means

| If you run this... | You're checking that... |
|---|---|
| `test_encoders.py` | Each modality encoder produces the right output shapes. |
| `test_fusion.py` | AFN and all three fusion levels behave correctly. |
| `test_model.py` | The full model runs end-to-end, and every ablation variant still works. |
| `test_training_step.py` | Forward → loss → backward → optimizer step → checkpoint save/load all succeed. |
| `experiments\demo.py` | Everything works together, and you see the six reference tables. |
| `experiments\train.py` | Training loop runs, checkpoints get written. |
| `experiments\evaluate.py` | Metrics for a given dataset + checkpoint. |
| `experiments\ablation.py` | Each ablation variant runs; you'll see reference vs actual side by side. |
| `experiments\efficiency.py` | Parameter count, FLOPs estimate, and inference time. |

---

## 9. A quick honesty note about numbers

There are two kinds of numbers floating around:

- **Reference numbers** — the ones from the paper. They live in `evaluation/comparisons.py` and get printed as Tables 1 through 6, exactly as reported. Don't mistake them for something this code produced.
- **Actual numbers** — whatever your run of this code spits out. In mock or demo mode these are just proof-of-life values; they aren't benchmarks. To actually reproduce the paper's headline results you'd need the real datasets and something close to the paper's hardware (4× A100 40 GB).

The scripts label both clearly, and never overwrite a reference table with a measured value.

---

## 10. Extending it

- **New dataset?** Copy `datasets\meld.py`, tweak it, and register it in `datasets\__init__.py`.
- **New modality?** Add it to `MODALITIES` in `models\haft_mfn.py`, write an encoder, plug its dim into `AdaptiveFeatureNormalization`, and update the pairs/groups in `configs\config.yaml`.
- **New ablation?** Add a flag to `HAFT_MFN.configure_ablation`, branch on it in `forward()`, and add the case to `ABLATION_CONFIGS` in `experiments\ablation.py`.
- **New loss?** Drop a module in `losses\`, give it a weight in the config, and add it to `losses\multitask_loss.py`.

If you're preparing for a viva or an oral defense, have a look at `docs\viva.md` — it walks through every design choice in question-and-answer format.
