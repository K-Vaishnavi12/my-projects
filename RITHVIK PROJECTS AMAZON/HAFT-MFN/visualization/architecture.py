"""Text-based architecture diagram + a matplotlib block diagram."""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def render_architecture(save_path="figures/architecture.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")

    def box(x, y, w, h, text, color="#dbe9ff"):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                      linewidth=1.5, edgecolor="#333", facecolor=color)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, wrap=True)

    # Modality encoders
    box(0.2, 6.3, 2.4, 1.0, "RoBERTa\n(text)", "#ffe9d6")
    box(2.9, 6.3, 2.4, 1.0, "ResNet-50 + ViT\n(image)", "#d6ffe1")
    box(5.6, 6.3, 2.4, 1.0, "Wav2Vec 2.0 + MFCC\n(audio)", "#f2d6ff")
    box(8.3, 6.3, 2.4, 1.0, "TimeSformer + 3D-CNN\n(video)", "#ffe6f0")

    # AFN
    box(1.5, 5.0, 9.0, 0.7, "Adaptive Feature Normalization (AFN)", "#fff2b3")

    # L1
    box(0.5, 3.8, 10.5, 0.8,
        "Level 1: Pairwise Cross-Modal Attention (6 pairs, bidirectional)", "#c8e0ff")
    # L2
    box(1.0, 2.7, 10.0, 0.8,
        "Level 2: Trimodal Fusion with Learnable Gating (4 groups)", "#bee7c8")
    # L3
    box(1.5, 1.6, 9.0, 0.8,
        "Level 3: Global Multimodal Fusion (Multi-Head Self-Attention)", "#f7c5c5")
    # Heads
    box(0.5, 0.3, 3.3, 0.9, "Classification Head\n(CE)", "#eaeaea")
    box(4.3, 0.3, 3.3, 0.9, "Regression Head\n(MSE)", "#eaeaea")
    box(8.1, 0.3, 3.3, 0.9, "Contrastive Head\n(InfoNCE)", "#eaeaea")

    ax.text(6, 7.7, "HAFT-MFN — Hierarchical Attention Fusion Transformer\nwith Multimodal Feature Normalization",
            ha="center", fontsize=13, weight="bold")

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return save_path


if __name__ == "__main__":
    print(render_architecture())
