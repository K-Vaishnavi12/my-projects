import torch
import torch.nn as nn


class RegressionLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.mse = nn.MSELoss()

    def forward(self, pred: torch.Tensor, targets: torch.Tensor):
        return self.mse(pred, targets)
