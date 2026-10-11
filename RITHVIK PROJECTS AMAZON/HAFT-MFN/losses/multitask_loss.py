"""Weighted multi-task loss combining classification, regression, contrastive."""
import torch
import torch.nn as nn

from .classification_loss import ClassificationLoss
from .regression_loss import RegressionLoss
from .contrastive_loss import ContrastiveLoss


class MultiTaskLoss(nn.Module):
    def __init__(self, weights: dict, temperature: float = 0.07):
        super().__init__()
        self.w = weights
        self.cls = ClassificationLoss()
        self.reg = RegressionLoss()
        self.con = ContrastiveLoss(temperature=temperature)

    def forward(self, outputs: dict, targets: dict):
        losses = {}
        total = 0.0
        if "labels" in targets and outputs.get("logits") is not None:
            l = self.cls(outputs["logits"], targets["labels"])
            losses["classification"] = l
            total = total + self.w.get("classification", 1.0) * l
        if "regression" in targets and outputs.get("regression") is not None:
            l = self.reg(outputs["regression"], targets["regression"])
            losses["regression"] = l
            total = total + self.w.get("regression", 0.0) * l
        if outputs.get("contrastive_proj") is not None:
            l = self.con(outputs["contrastive_proj"])
            losses["contrastive"] = l
            total = total + self.w.get("contrastive", 0.0) * l
        losses["total"] = total if isinstance(total, torch.Tensor) else torch.tensor(float(total))
        return losses
