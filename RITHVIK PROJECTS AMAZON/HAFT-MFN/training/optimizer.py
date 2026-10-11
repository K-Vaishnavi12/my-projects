"""Optimizer builder with separate LR groups for pretrained vs new parameters."""
import torch


def _is_pretrained_param(name: str) -> bool:
    return any(k in name for k in [
        "text_enc.backbone", "image_enc.resnet", "image_enc.vit_model",
        "audio_enc.wav2vec", "video_enc.r3d",
    ])


def build_optimizer(model, cfg):
    lr_pre = cfg["training"]["lr_pretrained"]
    lr_new = cfg["training"]["lr_new"]
    wd = cfg["training"]["weight_decay"]

    pre_params, new_params = [], []
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        (pre_params if _is_pretrained_param(n) else new_params).append(p)

    param_groups = []
    if pre_params:
        param_groups.append({"params": pre_params, "lr": lr_pre})
    if new_params:
        param_groups.append({"params": new_params, "lr": lr_new})

    return torch.optim.AdamW(param_groups, weight_decay=wd)
