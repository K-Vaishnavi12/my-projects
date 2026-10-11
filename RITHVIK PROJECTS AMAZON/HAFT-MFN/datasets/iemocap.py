from .common import MockMultimodalDataset, PreprocessedFolderDataset
import os


def get_iemocap(cfg, split="train"):
    mode = cfg["data"]["mode"]
    if mode == "mock":
        return MockMultimodalDataset(cfg, n_samples=32, num_classes=6)
    if mode == "demo":
        return MockMultimodalDataset(cfg, n_samples=cfg["data"]["demo_samples"], num_classes=6)
    if mode == "full":
        return PreprocessedFolderDataset(os.path.join(cfg["data"]["root"], "iemocap", split))
    raise ValueError(f"Unknown data.mode: {mode}")
