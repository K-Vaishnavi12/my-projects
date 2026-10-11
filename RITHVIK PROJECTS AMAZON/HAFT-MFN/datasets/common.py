"""Common dataset utilities with mock/demo/full modes.

Mock/demo produce synthetic tensors matching model input signatures so the
full pipeline (forward, loss, backward) can be tested without external data.

FULL mode reads a directory of preprocessed samples in a simple format
`{sample_id}.pt` containing a dict with keys: input_ids, attention_mask, image,
audio, video, label, regression (if applicable).
This lets you plug in any real dataset once you preprocess it externally.
"""
from __future__ import annotations
import os
import torch
from torch.utils.data import Dataset


def make_mock_sample(cfg, num_classes=None, reg_dim=None, seed=None):
    g = torch.Generator()
    if seed is not None:
        g.manual_seed(int(seed))
    e = cfg["encoders"]
    max_len = e["text"]["max_length"]
    img_size = e["image"]["image_size"]
    sr = e["audio"]["sample_rate"]
    n_frames = e["video"]["n_frames"]
    frame_size = e["video"]["frame_size"]
    nc = num_classes if num_classes is not None else cfg["task"]["num_classes"]
    rd = reg_dim if reg_dim is not None else cfg["task"]["regression_dim"]

    return {
        "input_ids": torch.randint(0, 30000, (max_len,), generator=g),
        "attention_mask": torch.ones(max_len, dtype=torch.long),
        "image": torch.randn(3, img_size, img_size, generator=g),
        "audio": torch.randn(sr, generator=g),  # 1 second
        "video": torch.randn(n_frames, 3, frame_size, frame_size, generator=g),
        "labels": torch.randint(0, nc, (1,), generator=g).squeeze(),
        "regression": torch.randn(rd, generator=g),
    }


class MockMultimodalDataset(Dataset):
    def __init__(self, cfg, n_samples: int = 32, num_classes=None, reg_dim=None):
        self.cfg = cfg
        self.n = n_samples
        self.num_classes = num_classes
        self.reg_dim = reg_dim

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        return make_mock_sample(self.cfg, self.num_classes, self.reg_dim, seed=idx + 1)


class PreprocessedFolderDataset(Dataset):
    """Full mode: expects `{root}/*.pt` sample dicts."""
    def __init__(self, root: str):
        self.root = root
        self.files = sorted([f for f in os.listdir(root) if f.endswith(".pt")])
        if not self.files:
            raise FileNotFoundError(f"No .pt samples in {root}")

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        return torch.load(os.path.join(self.root, self.files[idx]))


def collate_fn(batch):
    keys = batch[0].keys()
    out = {}
    for k in keys:
        vals = [b[k] for b in batch]
        if isinstance(vals[0], torch.Tensor):
            out[k] = torch.stack(vals, dim=0)
        else:
            out[k] = vals
    return out
