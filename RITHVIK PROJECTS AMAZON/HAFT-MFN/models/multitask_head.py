"""Multi-task prediction heads: classification, regression, contrastive projections."""
from __future__ import annotations
import torch
import torch.nn as nn


class MultiTaskHead(nn.Module):
    def __init__(self, d_model=768, num_classes=7, regression_dim=2,
                 contrastive_dim=128, modalities=("text", "image", "audio", "video"),
                 dropout=0.1):
        super().__init__()
        self.cls_head = nn.Sequential(
            nn.Linear(d_model, d_model), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(d_model, num_classes),
        )
        self.reg_head = nn.Sequential(
            nn.Linear(d_model, d_model), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(d_model, regression_dim),
        )
        # per-modality projection heads for contrastive alignment
        self.proj = nn.ModuleDict({
            m: nn.Sequential(nn.Linear(d_model, d_model), nn.GELU(),
                             nn.Linear(d_model, contrastive_dim))
            for m in modalities
        })

    def forward(self, global_cls: torch.Tensor, mod_feats: dict):
        logits = self.cls_head(global_cls)
        reg = self.reg_head(global_cls)
        proj = {}
        for m, v in mod_feats.items():
            x = v.mean(dim=1) if v.dim() == 3 else v
            z = self.proj[m](x)
            proj[m] = torch.nn.functional.normalize(z, dim=-1)
        return {"logits": logits, "regression": reg, "contrastive_proj": proj}
