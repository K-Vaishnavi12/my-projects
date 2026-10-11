"""End-to-end model test: forward pass + ablation configs."""
import os, sys, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import torch
from models import HAFT_MFN
from datasets import make_mock_sample, collate_fn


def _cfg():
    with open(os.path.join(ROOT, "configs", "config.yaml")) as f:
        cfg = yaml.safe_load(f)
    # small, fast, no downloads
    cfg["model"]["d_model"] = 96
    cfg["model"]["n_heads"] = 4
    cfg["model"]["ffn_dim"] = 128
    cfg["model"]["n_global_layers"] = 1
    cfg["encoders"]["text"]["max_length"] = 8
    cfg["encoders"]["image"]["image_size"] = 64
    cfg["encoders"]["audio"]["sample_rate"] = 4000
    cfg["encoders"]["video"]["n_frames"] = 2
    cfg["encoders"]["video"]["frame_size"] = 48
    for m in cfg["encoders"].values():
        if "use_pretrained" in m: m["use_pretrained"] = False
    cfg["task"]["num_classes"] = 4
    return cfg


def _batch(cfg, B=2):
    samples = [make_mock_sample(cfg, seed=i+1) for i in range(B)]
    return collate_fn(samples)


def test_forward():
    cfg = _cfg()
    model = HAFT_MFN(cfg)
    b = _batch(cfg)
    out = model(b)
    assert out["logits"].shape == (2, 4)
    assert out["regression"].shape == (2, 2)
    assert set(out["contrastive_proj"].keys()) == {"text","image","audio","video"}


def test_ablations():
    cfg = _cfg()
    for kwargs in [
        {"use_afn": False},
        {"use_hierarchical": False},
        {"use_gating": False},
        {"use_contrastive_head": False},
        {"use_multitask": False},
        {"modality_mask": ["text"]},
        {"modality_mask": ["video"]},
        {"fusion_mode": "early"},
        {"fusion_mode": "late"},
    ]:
        model = HAFT_MFN(cfg)
        model.configure_ablation(**kwargs)
        b = _batch(cfg)
        out = model(b)
        assert out["logits"].shape[0] == 2


if __name__ == "__main__":
    test_forward(); print("forward ok")
    test_ablations(); print("ablations ok")
