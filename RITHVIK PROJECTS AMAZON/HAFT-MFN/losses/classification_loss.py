import torch
import torch.nn as nn


class ClassificationLoss(nn.Module):
    def __init__(self, label_smoothing: float = 0.0, weight=None):
        super().__init__()
        self.ce = nn.CrossEntropyLoss(label_smoothing=label_smoothing, weight=weight)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor):
        return self.ce(logits, targets)
