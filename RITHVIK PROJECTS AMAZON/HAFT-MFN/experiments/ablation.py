"""Ablation study runner.

Runs each ablation configuration for 1 epoch on the currently configured
dataset (mock/demo/full) and reports actual measured metrics. Also prints the
paper's reference ablation values side by side.

DO NOT confuse the two: reference values are quoted from the paper;
actual values are what THIS code produced.
"""
from __future__ import annotations
import argparse, os, sys, yaml, json, copy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from models import HAFT_MFN
from datasets import get_dataset
from evaluation import evaluate_model
from evaluation.comparisons import REFERENCE_ABLATION, format_table
from training import Trainer


ABLATION_CONFIGS = [
    ("Full HAFT-MFN",              {}),
    ("w/o Adaptive Feature Normalization", {"use_afn": False}),
    ("w/o Hierarchical Fusion",    {"use_hierarchical": False}),
    ("w/o Learnable Gating",       {"use_gating": False}),
    ("w/o Contrastive Learning",   {"use_contrastive_head": False}),
    ("w/o Multi-Task Learning",    {"use_multitask": False}),
    ("Text-only",                  {"modality_mask": ["text"]}),
    ("Video-only",                 {"modality_mask": ["video"]}),
    ("Early Fusion",               {"fusion_mode": "early"}),
    ("Late Fusion",                {"fusion_mode": "late"}),
]


def run_one(cfg, ablation):
    model = HAFT_MFN(cfg)
    model.configure_ablation(**ablation)
    # ensure loss weights respect ablation
    if ablation.get("use_contrastive_head") is False:
        cfg["task"]["loss_weights"]["contrastive"] = 0.0
    if ablation.get("use_multitask") is False:
        cfg["task"]["loss_weights"]["regression"] = 0.0

    trainer = Trainer(model, cfg)
    trainer.fit(epochs=1)
    ds = get_dataset(cfg, "test")
    return evaluate_model(model, ds, task="sentiment",
                          num_classes=cfg["task"]["num_classes"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--mode", default="mock")
    args = ap.parse_args()

    with open(args.config) as f: base_cfg = yaml.safe_load(f)
    base_cfg["data"]["mode"] = args.mode
    if args.mode == "mock":
        for m in base_cfg["encoders"].values():
            if "use_pretrained" in m: m["use_pretrained"] = False
    base_cfg["training"]["epochs"] = 1

    actual_rows = []
    for name, ablation in ABLATION_CONFIGS:
        cfg = copy.deepcopy(base_cfg)
        try:
            print(f"\n=== Ablation: {name} ===")
            metrics = run_one(cfg, ablation)
            acc = metrics.get("accuracy", 0.0) * 100
            f1 = metrics.get("f1_weighted", 0.0) * 100
            mae = metrics.get("mae", 0.0)
            actual_rows.append((name, round(acc, 2), round(f1, 2), round(mae, 3)))
        except Exception as e:
            actual_rows.append((name, f"ERR: {e}", "-", "-"))

    print("\n" + format_table(
        "Reference Ablation Values (from paper)",
        ["Configuration", "Acc-2", "F1-Score", "MAE"], REFERENCE_ABLATION))
    print("\n" + format_table(
        f"Actual Ablation Values (this run, mode={args.mode})",
        ["Configuration", "Accuracy", "F1-Score", "MAE"], actual_rows))
    if args.mode in ("mock", "demo"):
        print("\nNOTE: mode is", args.mode,
              "- actual numbers are pipeline verification only, not benchmark results.")


if __name__ == "__main__":
    main()
