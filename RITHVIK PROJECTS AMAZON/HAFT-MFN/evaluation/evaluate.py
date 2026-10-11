"""End-to-end evaluation utility."""
from __future__ import annotations
import numpy as np
import torch
from torch.utils.data import DataLoader

from datasets import collate_fn
from .metrics import compute_task_metrics


@torch.no_grad()
def evaluate_model(model, dataset, task: str, device="cpu", batch_size=8, num_classes=None):
    model.eval().to(device)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
    all_logits, all_preds, all_targets = [], [], []
    all_reg_pred, all_reg_tgt = [], []
    for batch in loader:
        b = {k: (v.to(device) if isinstance(v, torch.Tensor) else v) for k, v in batch.items()}
        out = model(b)
        logits = out["logits"].detach().cpu().numpy()
        preds = logits.argmax(axis=-1)
        all_logits.append(logits); all_preds.append(preds)
        all_targets.append(batch["labels"].cpu().numpy())
        if out.get("regression") is not None and "regression" in batch:
            all_reg_pred.append(out["regression"].detach().cpu().numpy())
            all_reg_tgt.append(batch["regression"].cpu().numpy())

    logits = np.concatenate(all_logits, axis=0)
    preds = np.concatenate(all_preds, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    reg_pred = np.concatenate(all_reg_pred, axis=0) if all_reg_pred else None
    reg_tgt = np.concatenate(all_reg_tgt, axis=0) if all_reg_tgt else None
    return compute_task_metrics(task, logits, preds, targets, reg_pred, reg_tgt, num_classes=num_classes)
