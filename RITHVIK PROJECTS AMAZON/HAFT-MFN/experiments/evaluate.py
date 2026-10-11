"""Evaluate a trained (or freshly built) HAFT-MFN model."""
from __future__ import annotations
import argparse, os, sys, yaml, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from models import HAFT_MFN
from datasets import get_dataset
from evaluation import evaluate_model


TASK_MAP = {"cmu_mosei": "sentiment", "meld": "emotion",
            "vggsound": "action", "iemocap": "emotion", "mock": "sentiment"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--mode", default=None)
    args = ap.parse_args()

    with open(args.config) as f: cfg = yaml.safe_load(f)
    if args.dataset: cfg["data"]["dataset"] = args.dataset
    if args.mode: cfg["data"]["mode"] = args.mode
    if cfg["data"]["mode"] == "mock":
        for m in cfg["encoders"].values():
            if "use_pretrained" in m: m["use_pretrained"] = False

    model = HAFT_MFN(cfg)
    if args.checkpoint and os.path.exists(args.checkpoint):
        import torch
        d = torch.load(args.checkpoint, map_location="cpu")
        model.load_state_dict(d["model"])

    ds = get_dataset(cfg, "test")
    task = TASK_MAP.get(cfg["data"]["dataset"], "sentiment")
    metrics = evaluate_model(model, ds, task=task, num_classes=cfg["task"]["num_classes"])
    print(json.dumps({"actual_metrics": metrics, "dataset": cfg["data"]["dataset"],
                      "mode": cfg["data"]["mode"]}, indent=2))
    if cfg["data"]["mode"] in ("mock", "demo"):
        print("\nNOTE: Mode is", cfg["data"]["mode"],
              "- these are NOT benchmark results, only pipeline verification metrics.")


if __name__ == "__main__":
    main()
