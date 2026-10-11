"""Adaptive Feature Normalization (AFN).

Projects heterogeneous modality representations into a unified d_model space
while preserving modality-specific characteristics via learnable affine
parameters and a residual gate.
"""
from __future__ import annotations
import torch
import torch.nn as nn


class AdaptiveFeatureNormalization(nn.Module):
    def __init__(self, modalities, in_dims, d_model: int = 768):
        super().__init__()
        assert len(modalities) == len(in_dims)
        self.modalities = list(modalities)
        self.d_model = d_model
        self.norms = nn.ModuleDict()
        self.projs = nn.ModuleDict()
        self.gamma = nn.ParameterDict()
        self.beta = nn.ParameterDict()
        self.gate = nn.ParameterDict()
        for m, d in zip(modalities, in_dims):
            self.norms[m] = nn.LayerNorm(d)
            self.projs[m] = nn.Linear(d, d_model)
            self.gamma[m] = nn.Parameter(torch.ones(d_model))
            self.beta[m] = nn.Parameter(torch.zeros(d_model))
            self.gate[m] = nn.Parameter(torch.zeros(d_model))  # sigmoid(0)=0.5

    def forward(self, features: dict):
        """features: {modality: (B, T, D_m) or (B, D_m)} -> {modality: (B, T?, d_model)}"""
        out = {}
        for m, x in features.items():
            if m not in self.projs:
                raise KeyError(f"AFN not configured for modality '{m}'")
            xn = self.norms[m](x)
            xp = self.projs[m](xn)
            xp = xp * self.gamma[m] + self.beta[m]
            g = torch.sigmoid(self.gate[m])
            # residual gate blends normalized-projected with a plain projection to
            # preserve modality-specific characteristics
            out[m] = g * xp + (1 - g) * torch.nn.functional.gelu(xp)
        return out
