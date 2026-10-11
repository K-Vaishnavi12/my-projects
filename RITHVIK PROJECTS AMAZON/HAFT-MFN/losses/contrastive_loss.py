"""Cross-modal InfoNCE-style contrastive loss over modality pairs."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from itertools import combinations


class ContrastiveLoss(nn.Module):
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.T = temperature

    def _pair_loss(self, za: torch.Tensor, zb: torch.Tensor):
        # both are (B, D) already L2-normalized
        logits = za @ zb.t() / self.T  # (B,B)
        targets = torch.arange(za.size(0), device=za.device)
        return 0.5 * (F.cross_entropy(logits, targets) + F.cross_entropy(logits.t(), targets))

    def forward(self, projections: dict):
        keys = list(projections.keys())
        if len(keys) < 2:
            return torch.tensor(0.0, device=next(iter(projections.values())).device)
        losses = []
        for a, b in combinations(keys, 2):
            losses.append(self._pair_loss(projections[a], projections[b]))
        return torch.stack(losses).mean()
