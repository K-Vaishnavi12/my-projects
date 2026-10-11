"""Level 1: Bidirectional Pairwise Cross-Modal Attention."""
from __future__ import annotations
import torch
import torch.nn as nn


class _CrossAttnBlock(nn.Module):
    def __init__(self, d_model=768, n_heads=8, ffn=2048, dropout=0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.n1 = nn.LayerNorm(d_model)
        self.n2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ffn), nn.GELU(), nn.Dropout(dropout), nn.Linear(ffn, d_model),
        )

    def forward(self, q, kv):
        a, w = self.attn(q, kv, kv, need_weights=True, average_attn_weights=True)
        x = self.n1(q + a)
        x = self.n2(x + self.ffn(x))
        return x, w


class PairwiseCrossModalAttention(nn.Module):
    """Bidirectional cross-attention for a set of modality pairs.

    Returns per-pair pooled fused representations plus attention maps.
    """

    def __init__(self, pairs, d_model=768, n_heads=8, ffn=2048, dropout=0.1):
        super().__init__()
        self.pairs = [tuple(p) for p in pairs]
        self.blocks_ab = nn.ModuleDict()
        self.blocks_ba = nn.ModuleDict()
        self.combine = nn.ModuleDict()
        for a, b in self.pairs:
            key = f"{a}__{b}"
            self.blocks_ab[key] = _CrossAttnBlock(d_model, n_heads, ffn, dropout)
            self.blocks_ba[key] = _CrossAttnBlock(d_model, n_heads, ffn, dropout)
            self.combine[key] = nn.Linear(d_model * 2, d_model)

    def _as_seq(self, x):
        if x.dim() == 2:
            return x.unsqueeze(1)
        return x

    def forward(self, mod_feats: dict):
        """mod_feats: {modality: (B,T,d_model)}. Returns:
        - pair_repr: {"a__b": (B, d_model)} pooled
        - pair_seq:  {"a__b": (B, T_a+T_b, d_model)} concatenated fused seq
        - attn_maps: {"a__b__ab": w, "a__b__ba": w}
        """
        pair_repr, pair_seq, attn_maps = {}, {}, {}
        for a, b in self.pairs:
            key = f"{a}__{b}"
            xa = self._as_seq(mod_feats[a])
            xb = self._as_seq(mod_feats[b])
            fab, w_ab = self.blocks_ab[key](xa, xb)  # a attends to b
            fba, w_ba = self.blocks_ba[key](xb, xa)  # b attends to a
            pooled = torch.cat([fab.mean(dim=1), fba.mean(dim=1)], dim=-1)
            pair_repr[key] = self.combine[key](pooled)
            pair_seq[key] = torch.cat([fab, fba], dim=1)
            attn_maps[f"{key}__ab"] = w_ab
            attn_maps[f"{key}__ba"] = w_ba
        return {"pair_repr": pair_repr, "pair_seq": pair_seq, "attn_maps": attn_maps}
