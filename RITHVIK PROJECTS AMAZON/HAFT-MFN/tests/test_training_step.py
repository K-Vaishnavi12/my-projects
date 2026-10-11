"""One full training step: forward, loss, backward, optimizer.step, ckpt IO."""
import os, sys, yaml, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import torch
from models import HAFT_MFN
from losses import MultiTaskLoss
from datasets import make_mock_sample, collate_fn, MockMultimodalDataset
from training import Trainer


def _cfg():
    with open(os.path.join(ROOT, "configs", "config.yaml")) as f:
        cfg = yaml.safe_load(f)
    cfg["model"]["d_model"] = 96; cfg["model"]["n_heads"] = 4
    cfg["model"]["ffn_dim"] = 128; cfg["model"]["n_global_layers"] = 1
    cfg["encoders"]["text"]["max_length"] = 8
    cfg["encoders"]["image"]["image_size"] = 64
    cfg["encoders"]["audio"]["sample_rate"] = 4000
    cfg["encoders"]["video"]["n_frames"] = 2
    cfg["encoders"]["video"]["frame_size"] = 48
    for m in cfg["encoders"].values():
        if "use_pretrained" in m: m["use_pretrained"] = False
    cfg["task"]["num_classes"] = 4
    cfg["training"]["batch_size"] = 2
    cfg["training"]["grad_accum"] = 1
    cfg["training"]["epochs"] = 1
    cfg["training"]["mixed_precision"] = False
    cfg["training"]["log_every"] = 1
    cfg["training"]["num_workers"] = 0
    cfg["data"]["mode"] = "mock"
    cfg["data"]["dataset"] = "mock"
    return cfg


def test_backward_step():
    cfg = _cfg()
    model = HAFT_MFN(cfg)
    b = collate_fn([make_mock_sample(cfg, num_classes=4, seed=i+1) for i in range(2)])
    crit = MultiTaskLoss(cfg["task"]["loss_weights"])
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    out = model(b)
    losses = crit(out, {"labels": b["labels"].long(), "regression": b["regression"].float()})
    losses["total"].backward()
    opt.step()
    assert losses["total"].item() > 0


def test_trainer_epoch_and_ckpt():
    cfg = _cfg()
    model = HAFT_MFN(cfg)
    ds = MockMultimodalDataset(cfg, n_samples=4, num_classes=4)
    with tempfile.TemporaryDirectory() as tmp:
        cfg["training"]["checkpoint_dir"] = tmp
        trainer = Trainer(model, cfg, train_dataset=ds, val_dataset=ds, device="cpu")
        trainer.fit(epochs=1)
        p = os.path.join(tmp, "last.pt")
        assert os.path.exists(p)
        # reload
        trainer2 = Trainer(HAFT_MFN(cfg), cfg, train_dataset=ds, val_dataset=ds, device="cpu")
        trainer2.load_checkpoint(p)


if __name__ == "__main__":
    test_backward_step(); print("backward ok")
    test_trainer_epoch_and_ckpt(); print("trainer ok")
