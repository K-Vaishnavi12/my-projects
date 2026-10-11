"""Trainer for HAFT-MFN with mixed precision, checkpoints, resume, CPU fallback."""
from __future__ import annotations
import os
import time
import random
import numpy as np
import torch
from torch.utils.data import DataLoader

from datasets import get_dataset, collate_fn
from losses import MultiTaskLoss
from .optimizer import build_optimizer
from .scheduler import build_scheduler


def set_seed(seed: int):
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _move(batch, device):
    return {k: (v.to(device) if isinstance(v, torch.Tensor) else v) for k, v in batch.items()}


class Trainer:
    def __init__(self, model, cfg, train_dataset=None, val_dataset=None, device=None):
        self.model = model
        self.cfg = cfg
        set_seed(cfg["training"]["seed"])
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self.train_ds = train_dataset if train_dataset is not None else get_dataset(cfg, "train")
        self.val_ds = val_dataset if val_dataset is not None else get_dataset(cfg, "val")

        self.train_loader = DataLoader(
            self.train_ds, batch_size=cfg["training"]["batch_size"], shuffle=True,
            num_workers=cfg["training"]["num_workers"], collate_fn=collate_fn,
        )
        self.val_loader = DataLoader(
            self.val_ds, batch_size=cfg["training"]["batch_size"], shuffle=False,
            num_workers=cfg["training"]["num_workers"], collate_fn=collate_fn,
        )

        self.criterion = MultiTaskLoss(
            weights=cfg["task"]["loss_weights"],
            temperature=cfg["model"]["contrastive_temperature"],
        )
        self.optimizer = build_optimizer(model, cfg)
        self.scheduler = build_scheduler(self.optimizer, cfg,
                                         steps_per_epoch=max(1, len(self.train_loader)))

        self.use_amp = cfg["training"]["mixed_precision"] and self.device == "cuda"
        self.scaler = torch.cuda.amp.GradScaler(enabled=self.use_amp)

        self.grad_accum = cfg["training"]["grad_accum"]
        self.log_every = cfg["training"]["log_every"]
        self.ckpt_dir = cfg["training"]["checkpoint_dir"]
        os.makedirs(self.ckpt_dir, exist_ok=True)

        self.epoch = 0
        self.global_step = 0
        self.history = {"train_loss": [], "val_loss": [], "val_acc": []}

    def _step_batch(self, batch, train: bool):
        batch = _move(batch, self.device)
        with torch.cuda.amp.autocast(enabled=self.use_amp):
            outputs = self.model(batch)
            targets = {}
            if "labels" in batch:
                targets["labels"] = batch["labels"].long()
            if "regression" in batch:
                targets["regression"] = batch["regression"].float()
            losses = self.criterion(outputs, targets)
        return outputs, losses

    def train_one_epoch(self):
        self.model.train()
        total = 0.0; n = 0
        self.optimizer.zero_grad(set_to_none=True)
        for i, batch in enumerate(self.train_loader):
            outputs, losses = self._step_batch(batch, train=True)
            loss = losses["total"] / self.grad_accum
            self.scaler.scale(loss).backward()
            if (i + 1) % self.grad_accum == 0:
                self.scaler.step(self.optimizer)
                self.scaler.update()
                self.optimizer.zero_grad(set_to_none=True)
                self.scheduler.step()
                self.global_step += 1
            total += float(losses["total"].detach().cpu()); n += 1
            if (i + 1) % self.log_every == 0:
                print(f"  step {i+1}/{len(self.train_loader)} loss={total/n:.4f}")
        avg = total / max(1, n)
        self.history["train_loss"].append(avg)
        return avg

    @torch.no_grad()
    def validate(self):
        self.model.eval()
        total = 0.0; n = 0; correct = 0; count = 0
        for batch in self.val_loader:
            outputs, losses = self._step_batch(batch, train=False)
            total += float(losses["total"].cpu()); n += 1
            if outputs.get("logits") is not None and "labels" in batch:
                preds = outputs["logits"].argmax(dim=-1).cpu()
                correct += int((preds == batch["labels"].long()).sum())
                count += preds.numel()
        avg = total / max(1, n)
        acc = correct / max(1, count)
        self.history["val_loss"].append(avg)
        self.history["val_acc"].append(acc)
        return avg, acc

    def save_checkpoint(self, path):
        torch.save({
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict(),
            "epoch": self.epoch,
            "global_step": self.global_step,
            "history": self.history,
            "cfg": self.cfg,
        }, path)

    def load_checkpoint(self, path):
        d = torch.load(path, map_location=self.device)
        self.model.load_state_dict(d["model"])
        self.optimizer.load_state_dict(d["optimizer"])
        self.scheduler.load_state_dict(d["scheduler"])
        self.epoch = d["epoch"]; self.global_step = d["global_step"]
        self.history = d.get("history", self.history)

    def fit(self, epochs: int | None = None):
        epochs = epochs or self.cfg["training"]["epochs"]
        best = float("inf")
        for e in range(self.epoch, epochs):
            self.epoch = e
            t0 = time.time()
            tr = self.train_one_epoch()
            va, acc = self.validate()
            dt = time.time() - t0
            print(f"[Epoch {e+1}/{epochs}] train={tr:.4f} val={va:.4f} val_acc={acc:.4f} ({dt:.1f}s)")
            if va < best:
                best = va
                self.save_checkpoint(os.path.join(self.ckpt_dir, "best.pt"))
            self.save_checkpoint(os.path.join(self.ckpt_dir, "last.pt"))
        return self.history
