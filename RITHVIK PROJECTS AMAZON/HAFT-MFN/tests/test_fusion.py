"""Tests for AFN, pairwise attention, trimodal gating, global fusion."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import torch
from models import (AdaptiveFeatureNormalization, PairwiseCrossModalAttention,
                    TrimodalGatedFusion, GlobalMultimodalFusion)


MODS = ["text", "image", "audio", "video"]


def _feats(d=64, T=5, B=2):
    return {m: torch.randn(B, T, d) for m in MODS}


def test_afn():
    afn = AdaptiveFeatureNormalization(MODS, [64]*4, d_model=64)
    out = afn(_feats())
    for m in MODS:
        assert out[m].shape == (2, 5, 64)


def test_pairwise():
    pairs = [("text","image"), ("text","audio"), ("text","video"),
             ("image","audio"), ("image","video"), ("audio","video")]
    pw = PairwiseCrossModalAttention(pairs, d_model=64, n_heads=4, ffn=128)
    out = pw(_feats())
    assert len(out["pair_repr"]) == 6
    for k, v in out["pair_repr"].items():
        assert v.shape == (2, 64)


def test_trimodal():
    pairs = [("text","image"), ("text","audio"), ("text","video"),
             ("image","audio"), ("image","video"), ("audio","video")]
    groups = [("text","image","audio"), ("text","image","video"),
              ("text","audio","video"), ("image","audio","video")]
    pw = PairwiseCrossModalAttention(pairs, d_model=64, n_heads=4, ffn=128)
    tri = TrimodalGatedFusion(MODS, groups, pairs, d_model=64)
    feats = _feats()
    pair_out = pw(feats)
    out = tri(feats, pair_out["pair_repr"])
    assert len(out["trimodal_repr"]) == 4
    for v in out["trimodal_repr"].values():
        assert v.shape == (2, 64)


def test_global():
    g = GlobalMultimodalFusion(d_model=64, n_heads=4, ffn=128, n_layers=1)
    feats = _feats()
    pair_repr = {"a__b": torch.randn(2, 64), "c__d": torch.randn(2, 64)}
    tri_repr = {"x_y_z": torch.randn(2, 64)}
    out = g(feats, pair_repr, tri_repr)
    assert out["global_cls"].shape == (2, 64)


if __name__ == "__main__":
    test_afn(); test_pairwise(); test_trimodal(); test_global()
    print("fusion tests ok")
