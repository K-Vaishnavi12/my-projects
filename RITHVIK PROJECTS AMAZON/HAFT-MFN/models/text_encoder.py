"""Text encoder: RoBERTa-base (with graceful fallback for offline/mock mode)."""
from __future__ import annotations
import torch
import torch.nn as nn


class TextEncoder(nn.Module):
    """Extract token embeddings, [CLS], mean-pool from RoBERTa.

    If transformers/pretrained weights aren't available (offline/mock mode),
    falls back to a small Embedding + TransformerEncoder producing the same
    interface (token seq, cls, mean).
    """

    def __init__(
        self,
        pretrained_name: str = "roberta-base",
        d_model: int = 768,
        max_length: int = 64,
        freeze: bool = False,
        use_pretrained: bool = True,
        vocab_size: int = 50265,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.max_length = max_length
        self.use_pretrained_ok = False
        self.backbone = None

        if use_pretrained:
            try:  # pragma: no cover - network dependent
                from transformers import RobertaModel, RobertaTokenizer
                self.backbone = RobertaModel.from_pretrained(pretrained_name)
                self.tokenizer = RobertaTokenizer.from_pretrained(pretrained_name)
                hidden = self.backbone.config.hidden_size
                self.proj = nn.Linear(hidden, d_model) if hidden != d_model else nn.Identity()
                self.use_pretrained_ok = True
                if freeze:
                    for p in self.backbone.parameters():
                        p.requires_grad = False
            except Exception:
                self.backbone = None

        if self.backbone is None:
            # fallback: small internal encoder
            self.embed = nn.Embedding(vocab_size, d_model)
            self.pos = nn.Embedding(max_length, d_model)
            layer = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=8, dim_feedforward=2048,
                dropout=0.1, activation="gelu", batch_first=True,
            )
            self.fallback_encoder = nn.TransformerEncoder(layer, num_layers=2)
            self.cls_token = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
            self.proj = nn.Identity()

    @torch.no_grad()
    def tokenize(self, texts):
        if not self.use_pretrained_ok:
            raise RuntimeError("Tokenizer only available when transformers weights loaded.")
        enc = self.tokenizer(
            texts, padding="max_length", truncation=True,
            max_length=self.max_length, return_tensors="pt",
        )
        return enc["input_ids"], enc["attention_mask"]

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None):
        """Returns dict with 'seq' (B,T,d), 'cls' (B,d), 'mean' (B,d)."""
        if self.use_pretrained_ok:
            out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
            hidden = self.proj(out.last_hidden_state)  # (B,T,d)
            cls = hidden[:, 0]
            if attention_mask is None:
                mean = hidden.mean(dim=1)
            else:
                m = attention_mask.unsqueeze(-1).float()
                mean = (hidden * m).sum(1) / m.sum(1).clamp(min=1e-6)
            return {"seq": hidden, "cls": cls, "mean": mean}

        B, T = input_ids.shape
        T = min(T, self.max_length)
        input_ids = input_ids[:, :T]
        pos = torch.arange(T, device=input_ids.device).unsqueeze(0).expand(B, T)
        x = self.embed(input_ids.clamp_min(0)) + self.pos(pos)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1)
        if attention_mask is not None:
            am = attention_mask[:, :T]
            am = torch.cat([torch.ones(B, 1, device=am.device, dtype=am.dtype), am], dim=1)
            key_pad = (am == 0)
        else:
            key_pad = None
        h = self.fallback_encoder(x, src_key_padding_mask=key_pad)
        return {"seq": h[:, 1:], "cls": h[:, 0], "mean": h[:, 1:].mean(dim=1)}
