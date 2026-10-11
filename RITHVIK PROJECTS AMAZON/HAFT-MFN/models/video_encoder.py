"""Video encoder: TimeSformer (approx.) + 3D-CNN with temporal attention."""
from __future__ import annotations
import torch
import torch.nn as nn


class _TimeSformerLite(nn.Module):
    """Divided space-time attention approximation (works without timm)."""
    def __init__(self, image_size=112, patch=16, dim=384, depth=2, heads=6):
        super().__init__()
        self.patch = patch
        self.proj = nn.Conv2d(3, dim, patch, patch)
        n = (image_size // patch) ** 2
        self.pos_space = nn.Parameter(torch.randn(1, n, dim) * 0.02)
        self.pos_time = nn.Parameter(torch.randn(1, 64, dim) * 0.02)
        s_layer = nn.TransformerEncoderLayer(dim, heads, 1536, 0.1, "gelu", batch_first=True)
        self.spatial = nn.TransformerEncoder(s_layer, depth)
        t_layer = nn.TransformerEncoderLayer(dim, heads, 1536, 0.1, "gelu", batch_first=True)
        self.temporal = nn.TransformerEncoder(t_layer, depth)
        self.dim = dim

    def forward(self, x):
        # x: (B, F, 3, H, W)
        B, F, C, H, W = x.shape
        xf = x.reshape(B * F, C, H, W)
        tokens = self.proj(xf).flatten(2).transpose(1, 2)  # (B*F, N, D)
        tokens = tokens + self.pos_space[:, : tokens.size(1)]
        tokens = self.spatial(tokens)  # (B*F, N, D)
        # Pool spatial -> per-frame token
        frame_tokens = tokens.mean(dim=1).reshape(B, F, self.dim)
        frame_tokens = frame_tokens + self.pos_time[:, :F]
        return self.temporal(frame_tokens)  # (B, F, D)


class VideoEncoder(nn.Module):
    def __init__(self, d_model: int = 768, n_frames: int = 8, frame_size: int = 112,
                 use_pretrained: bool = True) -> None:
        super().__init__()
        self.n_frames = n_frames
        self.frame_size = frame_size

        # TimeSformer-like branch
        self.timesformer = _TimeSformerLite(image_size=frame_size, dim=384)
        ts_dim = 384

        # 3D-CNN branch (r3d_18)
        self.r3d = None
        r3d_dim = 512
        if use_pretrained:
            try:
                import torchvision.models.video as vmodels
                weights = None
                if hasattr(vmodels, "R3D_18_Weights"):
                    try:
                        weights = vmodels.R3D_18_Weights.DEFAULT
                    except Exception:
                        weights = None
                m = vmodels.r3d_18(weights=weights) if weights is not None else vmodels.r3d_18(weights=None)
                self.r3d = nn.Sequential(*list(m.children())[:-2])  # remove avgpool/fc
            except Exception:
                self.r3d = None
        if self.r3d is None:
            self.r3d = nn.Sequential(
                nn.Conv3d(3, 64, (3, 7, 7), (1, 2, 2), (1, 3, 3)), nn.ReLU(inplace=True),
                nn.Conv3d(64, 128, 3, (1, 2, 2), 1), nn.ReLU(inplace=True),
                nn.Conv3d(128, 256, 3, (1, 2, 2), 1), nn.ReLU(inplace=True),
                nn.Conv3d(256, r3d_dim, 3, (1, 2, 2), 1), nn.ReLU(inplace=True),
            )

        self.ts_proj = nn.Linear(ts_dim, d_model)
        self.r3d_proj = nn.Linear(r3d_dim, d_model)

        # temporal attention
        self.tattn = nn.MultiheadAttention(d_model, num_heads=8, dropout=0.1, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(nn.Linear(d_model, 2048), nn.GELU(), nn.Linear(2048, d_model))

    def forward(self, video: torch.Tensor):
        """video: (B, F, 3, H, W)"""
        B, F, C, H, W = video.shape
        ts_tokens = self.timesformer(video)  # (B, F, ts_dim)
        ts_tokens = self.ts_proj(ts_tokens)

        # r3d expects (B, C, T, H, W)
        v3d = video.transpose(1, 2)
        r3d_feat = self.r3d(v3d)  # (B, C', T', H', W')
        r3d_feat = r3d_feat.mean(dim=[3, 4]).transpose(1, 2)  # (B, T', C')
        r3d_feat = self.r3d_proj(r3d_feat)
        # align temporal lengths
        if r3d_feat.size(1) != ts_tokens.size(1):
            r3d_feat = torch.nn.functional.interpolate(
                r3d_feat.transpose(1, 2), size=ts_tokens.size(1),
                mode="linear", align_corners=False,
            ).transpose(1, 2)

        tokens = ts_tokens + r3d_feat  # combine
        attn_out, _ = self.tattn(tokens, tokens, tokens, need_weights=False)
        h = self.norm(tokens + attn_out)
        h = self.norm(h + self.ffn(h))
        return {"seq": h, "cls": h[:, 0], "mean": h.mean(dim=1)}
