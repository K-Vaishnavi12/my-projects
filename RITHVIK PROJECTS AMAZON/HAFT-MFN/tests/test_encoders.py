"""Unit tests for the four modality encoders in mock/no-download mode."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import torch
from models import TextEncoder, ImageEncoder, AudioEncoder, VideoEncoder


def test_text_encoder():
    enc = TextEncoder(use_pretrained=False, d_model=128, max_length=16, vocab_size=1000)
    ids = torch.randint(0, 1000, (2, 16))
    am = torch.ones(2, 16, dtype=torch.long)
    out = enc(ids, am)
    assert out["seq"].shape == (2, 16, 128)
    assert out["cls"].shape == (2, 128)
    assert out["mean"].shape == (2, 128)


def test_image_encoder():
    enc = ImageEncoder(d_model=128, use_pretrained=False)
    x = torch.randn(2, 3, 224, 224)
    out = enc(x)
    assert out["seq"].dim() == 3 and out["seq"].shape[-1] == 128
    assert out["cls"].shape == (2, 128)


def test_audio_encoder():
    enc = AudioEncoder(d_model=128, use_pretrained=False, sample_rate=16000)
    x = torch.randn(2, 16000)
    out = enc(x)
    assert out["seq"].shape[-1] == 128
    assert out["mean"].shape == (2, 128)


def test_video_encoder():
    enc = VideoEncoder(d_model=128, n_frames=4, frame_size=64, use_pretrained=False)
    x = torch.randn(2, 4, 3, 64, 64)
    out = enc(x)
    assert out["seq"].shape[-1] == 128


if __name__ == "__main__":
    test_text_encoder(); print("text ok")
    test_image_encoder(); print("image ok")
    test_audio_encoder(); print("audio ok")
    test_video_encoder(); print("video ok")
