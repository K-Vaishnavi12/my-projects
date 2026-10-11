"""Training entry-point.

Usage:
    python -m experiments.train --config configs/config.yaml
    python -m experiments.train --config configs/config.yaml --dataset mock --epochs 1
"""
from __future__ import annotations
import argparse
import os
import sys
import yaml

# make repo root importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models import HAFT_MFN
from training import Trainer


def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--mode", default=None, help="mock|demo|full")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--resume", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.dataset: cfg["data"]["dataset"] = args.dataset
    if args.mode: cfg["data"]["mode"] = args.mode
    if args.epochs: cfg["training"]["epochs"] = args.epochs

    # disable pretrained downloads when mode == mock (fast test)
    if cfg["data"]["mode"] == "mock":
        for m in cfg["encoders"].values():
            if "use_pretrained" in m:
                m["use_pretrained"] = False

    model = HAFT_MFN(cfg)
    trainer = Trainer(model, cfg)
    if args.resume:
        trainer.load_checkpoint(args.resume)
    trainer.fit()


if __name__ == "__main__":
    main()
