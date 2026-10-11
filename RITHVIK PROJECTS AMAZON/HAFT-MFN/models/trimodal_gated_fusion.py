"""Level 2: Trimodal fusion with learnable gating."""
from __future__ import annotations
import torch
import torch.nn as nn


class TrimodalGatedFusion(nn.Module):
    def __init__(self, modalities, groups, pairs, d_model=768, dropout=0.1):
        super().__init__()
        self.modalities = list(modalities)
        self.groups = [tuple(g) for g in groups]
        self.pairs = [tuple(p) for p in pairs]

        # per-modality gates (learnable, per-dim)
        self.mod_gates = nn.ParameterDict({m: nn.Parameter(torch.zeros(d_model)) for m in modalities})
        # per-pair learnable scalar weights
        self.pair_weights = nn.ParameterDict()
        for a, b in self.pairs:
            self.pair_weights[f"{a}__{b}"] = nn.Parameter(torch.tensor(0.0))

        # per-group projection layer
        self.projs = nn.ModuleDict()
        for g in self.groups:
            key = "_".join(g)
            self.projs[key] = nn.Sequential(
                nn.Linear(d_model, d_model), nn.GELU(), nn.Dropout(dropout), nn.LayerNorm(d_model),
            )

    def _pooled(self, x):
        if x.dim() == 3:
            return x.mean(dim=1)
        return x

    def forward(self, mod_feats: dict, pair_repr: dict):
        """Returns dict:
        - trimodal_repr: {group_key: (B, d_model)}
        - trimodal_gates: {mod: sigmoid(gate)} (for viz)
        """
        pooled = {m: self._pooled(v) for m, v in mod_feats.items()}
        gates = {m: torch.sigmoid(self.mod_gates[m]) for m in self.modalities}

        out = {}
        for g in self.groups:
            key = "_".join(g)
            # gated sum of modalities
            base = sum(gates[m] * pooled[m] for m in g)
            # add pairwise interactions within group
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    a, b = g[i], g[j]
                    pkey = f"{a}__{b}" if f"{a}__{b}" in pair_repr else f"{b}__{a}"
                    if pkey in pair_repr:
                        w = torch.sigmoid(self.pair_weights[pkey]) if pkey in self.pair_weights else torch.tensor(0.5, device=base.device)
                        base = base + w * pair_repr[pkey]
            out[key] = self.projs[key](base)

        return {"trimodal_repr": out, "trimodal_gates": gates}
