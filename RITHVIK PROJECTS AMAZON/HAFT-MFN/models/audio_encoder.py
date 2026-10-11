"""Audio encoder: Wav2Vec 2.0 + MFCC (with fallbacks)."""
from __future__ import annotations
import torch
import torch.nn as nn


class _TinyWav(nn.Module):
    """Fallback conv encoder for raw audio when Wav2Vec is unavailable."""
    def __init__(self, out_dim: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 64, 10, 5, 3), nn.GELU(),
            nn.Conv1d(64, 128, 8, 4, 2), nn.GELU(),
            nn.Conv1d(128, 256, 4, 2, 1), nn.GELU(),
            nn.Conv1d(256, out_dim, 4, 2, 1), nn.GELU(),
        )

    def forward(self, x):  # x: (B, T)
        if x.dim() == 2:
            x = x.unsqueeze(1)
        return self.net(x).transpose(1, 2)  # (B, T', out_dim)


class AudioEncoder(nn.Module):
    def __init__(
        self,
        d_model: int = 768,
        wav2vec_name: str = "facebook/wav2vec2-base",
        n_mfcc: int = 40,
        sample_rate: int = 16000,
        use_pretrained: bool = True,
    ) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.wav2vec = None
        wav_dim = 512
        if use_pretrained:
            try:
                from transformers import Wav2Vec2Model
                self.wav2vec = Wav2Vec2Model.from_pretrained(wav2vec_name)
                wav_dim = self.wav2vec.config.hidden_size
            except Exception:
                self.wav2vec = None
        if self.wav2vec is None:
            self.wav_fallback = _TinyWav(wav_dim)

        # MFCC
        self.mfcc = None
        try:
            import torchaudio.transforms as T
            self.mfcc = T.MFCC(
                sample_rate=sample_rate, n_mfcc=n_mfcc,
                melkwargs={"n_fft": 400, "hop_length": 160, "n_mels": 64},
            )
        except Exception:
            self.mfcc = None

        self.mfcc_proj = nn.Linear(n_mfcc, wav_dim)
        self.fuse = nn.Linear(wav_dim * 2, d_model)
        self.norm = nn.LayerNorm(d_model)

    def _mfcc(self, waveform):
        if self.mfcc is not None:
            m = self.mfcc(waveform)  # (B, n_mfcc, T')
            return m.transpose(1, 2)  # (B, T', n_mfcc)
        # naive fallback: STFT magnitude summarized
        B, T = waveform.shape
        n_frames = max(1, T // 160)
        w = waveform[:, : n_frames * 160].reshape(B, n_frames, 160)
        feat = torch.stack([w.mean(-1), w.std(-1), w.abs().max(-1).values], dim=-1)
        feat = feat.repeat(1, 1, (self.n_mfcc + 2) // 3)[:, :, : self.n_mfcc]
        return feat

    def _align(self, a, b):
        """Align temporal length of two (B,T,D) tensors via interpolation on a."""
        if a.size(1) == b.size(1):
            return a
        a2 = a.transpose(1, 2)  # (B,D,T)
        a2 = torch.nn.functional.interpolate(a2, size=b.size(1), mode="linear", align_corners=False)
        return a2.transpose(1, 2)

    def forward(self, waveform: torch.Tensor):
        """waveform: (B, T) at sample_rate."""
        if self.wav2vec is not None:
            out = self.wav2vec(waveform)
            wav_feat = out.last_hidden_state  # (B, T', H)
        else:
            wav_feat = self.wav_fallback(waveform)

        mfcc_feat = self._mfcc(waveform)  # (B, T'', n_mfcc)
        mfcc_feat = self.mfcc_proj(mfcc_feat)
        mfcc_feat = self._align(mfcc_feat, wav_feat)

        feat = torch.cat([wav_feat, mfcc_feat], dim=-1)
        feat = self.norm(self.fuse(feat))
        return {"seq": feat, "cls": feat[:, 0], "mean": feat.mean(dim=1)}
