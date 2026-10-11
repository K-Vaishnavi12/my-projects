"""Level 3: Global multimodal fusion with multi-head self-attention."""
from __future__ import annotations
import torch
import torch.nn as nn


class GlobalMultimodalFusion(nn.Module):
    def __init__(self, d_model=768, n_heads=8, ffn=2048, dropout=0.1, n_layers=2):
        super().__init__()
        self.cls = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
        layer = nn.TransformerEncoderLayer(
            d_model, n_heads, ffn, dropout, "gelu", batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, mod_feats: dict, pair_repr: dict, trimodal_repr: dict):
        """Concatenate pooled modality reps, pairwise reprs, trimodal reprs as tokens."""
        tokens = []
        for m, v in mod_feats.items():
            tokens.append(v.mean(dim=1) if v.dim() == 3 else v)
        for _, v in pair_repr.items():
            tokens.append(v)
        for _, v in trimodal_repr.items():
            tokens.append(v)
        seq = torch.stack(tokens, dim=1)  # (B, N, d)
        B = seq.size(0)
        cls = self.cls.expand(B, -1, -1)
        seq = torch.cat([cls, seq], dim=1)
        h = self.encoder(seq)
        h = self.norm(h)
        return {"global_seq": h, "global_cls": h[:, 0]}
