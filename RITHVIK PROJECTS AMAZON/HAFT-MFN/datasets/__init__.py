from .common import MockMultimodalDataset, PreprocessedFolderDataset, collate_fn, make_mock_sample
from .cmu_mosei import get_cmu_mosei
from .meld import get_meld
from .vggsound import get_vggsound
from .iemocap import get_iemocap


def get_dataset(cfg, split="train"):
    name = cfg["data"]["dataset"]
    if name == "mock":
        return MockMultimodalDataset(cfg, n_samples=32)
    if name == "cmu_mosei":
        return get_cmu_mosei(cfg, split)
    if name == "meld":
        return get_meld(cfg, split)
    if name == "vggsound":
        return get_vggsound(cfg, split)
    if name == "iemocap":
        return get_iemocap(cfg, split)
    raise ValueError(f"Unknown dataset: {name}")


__all__ = [
    "MockMultimodalDataset", "PreprocessedFolderDataset", "collate_fn",
    "make_mock_sample", "get_dataset",
    "get_cmu_mosei", "get_meld", "get_vggsound", "get_iemocap",
]
