"""CMU-MOSEI dataset wrapper.

Supports 3 modes:
  - mock: synthetic tensors (fast unit-test)
  - demo: small synthetic subset (a few real-shaped samples)
  - full: expects preprocessed .pt files in {root}/cmu_mosei/{split}/

Real CMU-MOSEI processing is dataset-license restricted. Users must download
CMU-MOSEI from http://multicomp.cs.cmu.edu/resources/cmu-mosei-dataset/ and
preprocess to the .pt format documented in datasets/common.py.
"""
from .common import MockMultimodalDataset, PreprocessedFolderDataset
import os


def get_cmu_mosei(cfg, split="train"):
    mode = cfg["data"]["mode"]
    if mode == "mock":
        return MockMultimodalDataset(cfg, n_samples=32, num_classes=7)
    if mode == "demo":
        return MockMultimodalDataset(cfg, n_samples=cfg["data"]["demo_samples"], num_classes=7)
    if mode == "full":
        path = os.path.join(cfg["data"]["root"], "cmu_mosei", split)
        return PreprocessedFolderDataset(path)
    raise ValueError(f"Unknown data.mode: {mode}")
