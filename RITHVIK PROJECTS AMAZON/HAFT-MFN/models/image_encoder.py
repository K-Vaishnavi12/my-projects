"""Image encoder: ResNet-50 + ViT-B/16 with spatial attention fusion."""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


class _TinyConv(nn.Module):
    def __init__(self, out_dim: int = 2048):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 64, 7, 2, 3), nn.ReLU(inplace=True), nn.MaxPool2d(3, 2, 1),
            nn.Conv2d(64, 256, 3, 2, 1), nn.ReLU(inplace=True),
            nn.Conv2d(256, 512, 3, 2, 1), nn.ReLU(inplace=True),
            nn.Conv2d(512, out_dim, 3, 2, 1), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)  # (B, out_dim, H', W')


class _TinyViT(nn.Module):
    def __init__(self, image_size=224, patch=16, dim=768):
        super().__init__()
        self.patch = patch
        self.proj = nn.Conv2d(3, dim, patch, patch)
        n = (image_size // patch) ** 2
        self.pos = nn.Parameter(torch.randn(1, n, dim) * 0.02)
        layer = nn.TransformerEncoderLayer(dim, 8, 2048, 0.1, "gelu", batch_first=True)
        self.enc = nn.TransformerEncoder(layer, 2)

    def forward(self, x):
        t = self.proj(x).flatten(2).transpose(1, 2)  # (B,N,D)
        return self.enc(t + self.pos)


class ImageEncoder(nn.Module):
    def __init__(
        self,
        d_model: int = 768,
        resnet_name: str = "resnet50",
        vit_name: str = "vit_b_16",
        use_pretrained: bool = True,
        image_size: int = 224,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.image_size = image_size
        cnn_dim = 2048
        vit_dim = 768
        # ResNet
        self.resnet = None
        if use_pretrained:
            try:
                import torchvision.models as tvm
                weights = None
                if hasattr(tvm, "ResNet50_Weights"):
                    try:
                        weights = tvm.ResNet50_Weights.DEFAULT
                    except Exception:
                        weights = None
                m = getattr(tvm, resnet_name)(weights=weights) if weights is not None else getattr(tvm, resnet_name)(weights=None)
                # drop avgpool and fc -> keep conv features
                self.resnet = nn.Sequential(*list(m.children())[:-2])
                cnn_dim = 2048
            except Exception:
                self.resnet = None
        if self.resnet is None:
            self.resnet = _TinyConv(cnn_dim)

        # ViT
        self.vit = None
        if use_pretrained:
            try:
                import torchvision.models as tvm
                weights = None
                if hasattr(tvm, "ViT_B_16_Weights"):
                    try:
                        weights = tvm.ViT_B_16_Weights.DEFAULT
                    except Exception:
                        weights = None
                vm = tvm.vit_b_16(weights=weights) if weights is not None else tvm.vit_b_16(weights=None)
                self.vit_model = vm
                vit_dim = vm.hidden_dim
                self._use_tv_vit = True
            except Exception:
                self._use_tv_vit = False
        else:
            self._use_tv_vit = False
        if not self._use_tv_vit:
            self.vit = _TinyViT(image_size=image_size, dim=vit_dim)

        # spatial attention projections over concatenated tokens
        self.cnn_proj = nn.Linear(cnn_dim, d_model)
        self.vit_proj = nn.Linear(vit_dim, d_model)
        self.attn = nn.MultiheadAttention(d_model, num_heads=8, dropout=0.1, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(nn.Linear(d_model, 2048), nn.GELU(), nn.Linear(2048, d_model))

    def _vit_tokens(self, x):
        if self._use_tv_vit:
            m = self.vit_model
            # Reproduce torchvision ViT patch embed + encoder to obtain tokens
            x = m._process_input(x)
            n = x.shape[0]
            cls = m.class_token.expand(n, -1, -1)
            x = torch.cat([cls, x], dim=1)
            x = m.encoder(x)
            return x  # (B, 1+N, D)
        return self.vit(x)

    def forward(self, images: torch.Tensor):
        """images: (B, 3, H, W). Returns dict seq/cls/mean."""
        c = self.resnet(images)  # (B,C,H',W')
        B, C, H, W = c.shape
        c_tokens = c.flatten(2).transpose(1, 2)  # (B, H'W', C)
        c_tokens = self.cnn_proj(c_tokens)

        v_tokens = self._vit_tokens(images)
        v_tokens = self.vit_proj(v_tokens)

        tokens = torch.cat([c_tokens, v_tokens], dim=1)
        attn_out, _ = self.attn(tokens, tokens, tokens, need_weights=False)
        h = self.norm(tokens + attn_out)
        h = self.norm(h + self.ffn(h))
        return {"seq": h, "cls": h[:, 0], "mean": h.mean(dim=1)}
