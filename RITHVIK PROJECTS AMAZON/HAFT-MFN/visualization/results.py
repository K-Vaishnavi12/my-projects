"""Plot training curves, comparison bars, ablation graph, efficiency graph."""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _ensure(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def plot_curves(history, save_path="figures/curves.png"):
    _ensure(save_path)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    if history.get("train_loss"):
        ax[0].plot(history["train_loss"], label="train")
    if history.get("val_loss"):
        ax[0].plot(history["val_loss"], label="val")
    ax[0].set_title("Loss"); ax[0].set_xlabel("epoch"); ax[0].legend()
    if history.get("val_acc"):
        ax[1].plot(history["val_acc"], label="val_acc", color="green")
    ax[1].set_title("Validation Accuracy"); ax[1].set_xlabel("epoch"); ax[1].legend()
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path


def plot_dataset_comparison(rows, metric_idx=1, title="Dataset Comparison",
                            save_path="figures/dataset_comparison.png"):
    _ensure(save_path)
    labels = [r[0] for r in rows]
    values = [r[metric_idx] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values, color="#4c72b0")
    ax.set_title(title); ax.set_ylabel("Value")
    plt.xticks(rotation=30, ha="right"); plt.tight_layout()
    plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path


def plot_ablation(rows, save_path="figures/ablation.png"):
    _ensure(save_path)
    labels = [r[0] for r in rows]
    acc = [r[1] for r in rows]
    f1 = [r[2] for r in rows]
    x = np.arange(len(labels))
    w = 0.4
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - w/2, acc, w, label="Acc-2")
    ax.bar(x + w/2, f1, w, label="F1")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.legend(); ax.set_title("Ablation Study (paper reference values)")
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path


def plot_efficiency(rows, save_path="figures/efficiency.png"):
    _ensure(save_path)
    labels = [r[0] for r in rows]
    flops = [r[1] for r in rows]
    params = [r[2] for r in rows]
    inf = [r[3] for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(labels)); w = 0.25
    ax.bar(x - w, flops, w, label="FLOPs (G)")
    ax.bar(x,     params, w, label="Params (M)")
    ax.bar(x + w, inf,    w, label="Inference (ms)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.legend(); ax.set_title("Computational Efficiency (paper reference)")
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path


def plot_confusion_matrix(cm, labels, save_path="figures/confusion.png"):
    _ensure(save_path)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45); ax.set_yticklabels(labels)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
    ax.set_title("Confusion Matrix"); plt.colorbar(im, ax=ax)
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close(fig)
    return save_path
