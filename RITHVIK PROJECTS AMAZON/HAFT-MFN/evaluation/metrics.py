"""Evaluation metrics for all supported tasks."""
from __future__ import annotations
import numpy as np
import torch


def _to_np(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)


def accuracy(preds, targets):
    p, t = _to_np(preds), _to_np(targets)
    return float((p == t).mean())


def top_k_accuracy(logits, targets, k=5):
    logits = _to_np(logits); targets = _to_np(targets)
    idx = np.argsort(-logits, axis=-1)[:, :k]
    correct = (idx == targets.reshape(-1, 1)).any(axis=-1)
    return float(correct.mean())


def acc_2(preds, targets):
    """Binary accuracy for sentiment (negative vs non-negative)."""
    p, t = _to_np(preds), _to_np(targets)
    return float(((p > 0) == (t > 0)).mean())


def mae(pred, target):
    return float(np.mean(np.abs(_to_np(pred) - _to_np(target))))


def pearson_corr(pred, target):
    p = _to_np(pred).reshape(-1).astype(np.float64)
    t = _to_np(target).reshape(-1).astype(np.float64)
    if p.std() == 0 or t.std() == 0:
        return 0.0
    return float(np.corrcoef(p, t)[0, 1])


def weighted_f1(preds, targets, num_classes=None):
    from sklearn.metrics import f1_score
    return float(f1_score(_to_np(targets), _to_np(preds), average="weighted", zero_division=0))


def macro_f1(preds, targets):
    from sklearn.metrics import f1_score
    return float(f1_score(_to_np(targets), _to_np(preds), average="macro", zero_division=0))


def precision_recall(preds, targets):
    from sklearn.metrics import precision_score, recall_score
    return (
        float(precision_score(_to_np(targets), _to_np(preds), average="weighted", zero_division=0)),
        float(recall_score(_to_np(targets), _to_np(preds), average="weighted", zero_division=0)),
    )


def mean_average_precision(logits, targets, num_classes):
    """One-vs-rest mAP for multi-class."""
    from sklearn.metrics import average_precision_score
    logits = _to_np(logits); targets = _to_np(targets)
    onehot = np.eye(num_classes)[targets]
    # softmax
    e = np.exp(logits - logits.max(axis=-1, keepdims=True))
    probs = e / e.sum(axis=-1, keepdims=True)
    try:
        return float(average_precision_score(onehot, probs, average="macro"))
    except Exception:
        return 0.0


def compute_task_metrics(task: str, logits, preds, targets, reg_pred=None, reg_target=None, num_classes=None):
    """Return dict of metrics for a task in {'sentiment','emotion','action'}."""
    out = {"accuracy": accuracy(preds, targets)}
    if task == "sentiment":
        out["acc_2"] = acc_2(preds, targets)
        out["acc_7"] = accuracy(preds, targets)
        out["f1_weighted"] = weighted_f1(preds, targets)
        if reg_pred is not None and reg_target is not None:
            out["mae"] = mae(reg_pred, reg_target)
            out["pearson_corr"] = pearson_corr(reg_pred, reg_target)
    elif task == "emotion":
        out["f1_weighted"] = weighted_f1(preds, targets)
        out["f1_macro"] = macro_f1(preds, targets)
        p, r = precision_recall(preds, targets)
        out["precision"] = p; out["recall"] = r
    elif task == "action":
        out["top1"] = accuracy(preds, targets)
        out["top5"] = top_k_accuracy(logits, targets, k=5)
        if num_classes is not None:
            out["mAP"] = mean_average_precision(logits, targets, num_classes)
    return out
