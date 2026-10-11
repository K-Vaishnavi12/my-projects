"""Attention & gating visualization utilities."""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch


def _ensure(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def plot_attention_map(weights: torch.Tensor, title="Cross-Modal Attention",
                       save_path="figures/attention.png"):
    _ensure(save_path)
    w = weights.detach().cpu().numpy()
    if w.ndim == 3:
        w = w[0]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(w, cmap="viridis", aspect="auto")
    ax.set_title(title); plt.colorbar(im, ax=ax)
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path


def plot_gating_weights(gates: dict, save_path="figures/gating.png"):
    _ensure(save_path)
    names = list(gates.keys())
    values = [float(g.mean().detach().cpu()) for g in gates.values()]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(names, values, color="#55a868")
    ax.set_ylim(0, 1); ax.set_title("Learnable Modality Gating (mean sigmoid)")
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path


def analyze_missing_modality(model, batch, drop_modality: str):
    """Compute output distance when a modality is zeroed vs original."""
    model.eval()
    with torch.no_grad():
        out_full = model(batch)
        b2 = {k: v.clone() if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
        key = {"text": "input_ids", "image": "image", "audio": "audio", "video": "video"}[drop_modality]
        if key in b2 and isinstance(b2[key], torch.Tensor):
            b2[key] = torch.zeros_like(b2[key])
        out_drop = model(b2)
        delta = (out_full["global_cls"] - out_drop["global_cls"]).norm(dim=-1).mean().item()
    return delta
