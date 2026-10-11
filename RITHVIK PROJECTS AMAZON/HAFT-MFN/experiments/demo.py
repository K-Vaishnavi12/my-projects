"""End-to-end demo: build HAFT-MFN, run a mock batch, print outputs and metrics.

Usage:
    python -m experiments.demo
"""
from __future__ import annotations
import os, sys, yaml, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import torch
from models import HAFT_MFN
from datasets import make_mock_sample, collate_fn, MockMultimodalDataset
from losses import MultiTaskLoss
from evaluation import evaluate_model
from evaluation.comparisons import (REFERENCE_CMU_MOSEI, REFERENCE_MELD,
                                    REFERENCE_VGGSOUND, REFERENCE_IEMOCAP,
                                    REFERENCE_ABLATION, REFERENCE_EFFICIENCY,
                                    format_table)
from visualization import render_architecture


def main():
    with open(os.path.join(ROOT, "configs", "config.yaml")) as f:
        cfg = yaml.safe_load(f)
    # small demo config, no downloads
    cfg["model"]["d_model"] = 128; cfg["model"]["n_heads"] = 4
    cfg["model"]["ffn_dim"] = 256; cfg["model"]["n_global_layers"] = 1
    cfg["encoders"]["text"]["max_length"] = 12
    cfg["encoders"]["image"]["image_size"] = 96
    cfg["encoders"]["audio"]["sample_rate"] = 8000
    cfg["encoders"]["video"]["n_frames"] = 4
    cfg["encoders"]["video"]["frame_size"] = 64
    for m in cfg["encoders"].values():
        if "use_pretrained" in m: m["use_pretrained"] = False
    cfg["task"]["num_classes"] = 7
    cfg["data"]["mode"] = "demo"; cfg["data"]["dataset"] = "cmu_mosei"

    print("Building HAFT-MFN ...")
    model = HAFT_MFN(cfg)
    n_params = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"  Built. Parameters: {n_params:.2f}M")

    # forward
    batch = collate_fn([make_mock_sample(cfg, num_classes=7, seed=i+1) for i in range(4)])
    out = model(batch)
    print("\nForward outputs:")
    print("  logits:", tuple(out["logits"].shape))
    print("  regression:", tuple(out["regression"].shape))
    print("  contrastive_proj keys:", list(out["contrastive_proj"].keys()))
    print("  attn_maps count:", len(out["attn_maps"]))
    print("  trimodal_gates keys:", list(out["trimodal_gates"].keys()))

    # loss + backward
    crit = MultiTaskLoss(cfg["task"]["loss_weights"])
    losses = crit(out, {"labels": batch["labels"].long(),
                        "regression": batch["regression"].float()})
    losses["total"].backward()
    print("\nLosses:", {k: float(v) for k, v in losses.items() if hasattr(v, "item")})

    # evaluation on tiny demo set
    ds = MockMultimodalDataset(cfg, n_samples=8, num_classes=7)
    metrics = evaluate_model(model, ds, task="sentiment", num_classes=7)
    print("\nActual demo metrics (mock data — NOT benchmark results):")
    print(json.dumps(metrics, indent=2))

    # architecture figure
    fig_path = render_architecture(save_path=os.path.join(ROOT, "figures", "architecture.png"))
    print(f"\nSaved architecture figure -> {fig_path}")

    # print reference tables
    print("\n" + format_table("Table 1: CMU-MOSEI (paper reference)",
        ["Method","Acc-2","Acc-7","F1","MAE","Corr"], REFERENCE_CMU_MOSEI))
    print("\n" + format_table("Table 2: MELD (paper reference)",
        ["Method","Accuracy","W-F1","Precision","Recall"], REFERENCE_MELD))
    print("\n" + format_table("Table 3: VGGSound (paper reference)",
        ["Method","Top-1","Top-5","mAP"], REFERENCE_VGGSOUND))
    print("\n" + format_table("Table 4: IEMOCAP (paper reference)",
        ["Method","W-F1","Accuracy","Valence MAE","Arousal MAE"], REFERENCE_IEMOCAP))
    print("\n" + format_table("Table 5: Ablation (paper reference)",
        ["Configuration","Acc-2","F1","MAE"], REFERENCE_ABLATION))
    print("\n" + format_table("Table 6: Efficiency (paper reference)",
        ["Method","FLOPs(G)","Params(M)","Inference(ms)","Acc-2"], REFERENCE_EFFICIENCY))

    print("\nNOTE: All tables above are paper-reported values, NOT reproduced by this demo run.")


if __name__ == "__main__":
    main()
