"""Measure actual FLOPs, parameters, and inference time of HAFT-MFN."""
from __future__ import annotations
import argparse, os, sys, time, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import torch
from models import HAFT_MFN
from datasets import make_mock_sample
from evaluation.comparisons import REFERENCE_EFFICIENCY, format_table


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def approximate_flops(model, sample_batch):
    """Rough FLOP estimate: 2 * params * seq (very approximate).

    We do NOT claim this equals paper-reported FLOPs. It reports the actual
    parameter-based estimate for the built model.
    """
    return 2 * count_parameters(model)


def measure_inference_time(model, sample_batch, n_iter=20, warmup=5, device="cpu"):
    model.eval().to(device)
    with torch.no_grad():
        for _ in range(warmup):
            _ = model(sample_batch)
        t0 = time.time()
        for _ in range(n_iter):
            _ = model(sample_batch)
        dt = (time.time() - t0) / n_iter
    return dt * 1000  # ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    args = ap.parse_args()
    with open(args.config) as f: cfg = yaml.safe_load(f)
    for m in cfg["encoders"].values():
        if "use_pretrained" in m: m["use_pretrained"] = False  # fast build

    model = HAFT_MFN(cfg)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    s = make_mock_sample(cfg)
    batch = {k: v.unsqueeze(0).to(device) for k, v in s.items()}

    params = count_parameters(model) / 1e6
    flops = approximate_flops(model, batch) / 1e9
    inf_ms = measure_inference_time(model, batch, device=device)

    print(f"Actual measurements (this build, batch=1, device={device}):")
    print(f"  Parameters (M)   : {params:.2f}")
    print(f"  Approx FLOPs (G) : {flops:.2f}")
    print(f"  Inference time (ms/sample): {inf_ms:.2f}")

    print("\n" + format_table(
        "Reference Efficiency (from paper)",
        ["Method", "FLOPs(G)", "Params(M)", "Inference(ms)", "Acc-2(%)"],
        REFERENCE_EFFICIENCY))
    print("\nNOTE: The reference values above are paper-reported, NOT reproduced by this run.")


if __name__ == "__main__":
    main()
