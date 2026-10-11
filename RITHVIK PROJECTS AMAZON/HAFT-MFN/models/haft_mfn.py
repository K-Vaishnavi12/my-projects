"""HAFT-MFN: Hierarchical Attention Fusion Transformer with Multimodal Feature Normalization."""
from __future__ import annotations
import torch
import torch.nn as nn

from .text_encoder import TextEncoder
from .image_encoder import ImageEncoder
from .audio_encoder import AudioEncoder
from .video_encoder import VideoEncoder
from .adaptive_feature_normalization import AdaptiveFeatureNormalization
from .pairwise_cross_attention import PairwiseCrossModalAttention
from .trimodal_gated_fusion import TrimodalGatedFusion
from .global_multimodal_fusion import GlobalMultimodalFusion
from .multitask_head import MultiTaskHead


MODALITIES = ("text", "image", "audio", "video")


class HAFT_MFN(nn.Module):
    """Complete HAFT-MFN model.

    Ablation flags:
        use_afn: enable Adaptive Feature Normalization
        use_hierarchical: enable full L1+L2+L3; if False -> only L1 -> pooled avg
        use_gating: enable learnable gating in L2 (else uniform gates)
        use_contrastive_head: enable contrastive projections
        use_multitask: enable regression head
        modality_mask: iterable of modalities to actually use (others zeroed/dropped)
        fusion_mode: 'hierarchical' | 'early' | 'late'
    """

    def __init__(self, config: dict):
        super().__init__()
        m = config["model"]
        e = config["encoders"]
        f = config["fusion"]
        t = config["task"]

        self.d_model = m["d_model"]
        self.modalities = list(MODALITIES)

        # Encoders
        self.text_enc = TextEncoder(
            pretrained_name=e["text"]["pretrained_name"],
            d_model=self.d_model,
            max_length=e["text"]["max_length"],
            freeze=e["text"]["freeze"],
            use_pretrained=e["text"]["use_pretrained"],
        )
        self.image_enc = ImageEncoder(
            d_model=self.d_model,
            resnet_name=e["image"]["resnet"],
            vit_name=e["image"]["vit"],
            use_pretrained=e["image"]["use_pretrained"],
            image_size=e["image"]["image_size"],
        )
        self.audio_enc = AudioEncoder(
            d_model=self.d_model,
            wav2vec_name=e["audio"]["wav2vec_name"],
            n_mfcc=e["audio"]["n_mfcc"],
            sample_rate=e["audio"]["sample_rate"],
            use_pretrained=e["audio"]["use_pretrained"],
        )
        self.video_enc = VideoEncoder(
            d_model=self.d_model,
            n_frames=e["video"]["n_frames"],
            frame_size=e["video"]["frame_size"],
            use_pretrained=e["video"]["use_pretrained"],
        )

        # AFN (inputs already d_model, but AFN performs unified normalization)
        self.afn = AdaptiveFeatureNormalization(
            modalities=self.modalities,
            in_dims=[self.d_model] * len(self.modalities),
            d_model=self.d_model,
        )

        # Level 1
        self.pairwise = PairwiseCrossModalAttention(
            pairs=f["pairs"], d_model=self.d_model, n_heads=m["n_heads"],
            ffn=m["ffn_dim"], dropout=m["dropout"],
        )
        # Level 2
        self.trimodal = TrimodalGatedFusion(
            modalities=self.modalities, groups=f["trimodal_groups"],
            pairs=f["pairs"], d_model=self.d_model, dropout=m["dropout"],
        )
        # Level 3
        self.global_fusion = GlobalMultimodalFusion(
            d_model=self.d_model, n_heads=m["n_heads"], ffn=m["ffn_dim"],
            dropout=m["dropout"], n_layers=m["n_global_layers"],
        )

        # Multi-task head
        self.head = MultiTaskHead(
            d_model=self.d_model, num_classes=t["num_classes"],
            regression_dim=t["regression_dim"], modalities=self.modalities,
            dropout=m["dropout"],
        )

        # ablation flags
        self.use_afn = True
        self.use_hierarchical = True
        self.use_gating = True
        self.use_contrastive_head = True
        self.use_multitask = True
        self.fusion_mode = "hierarchical"
        self.modality_mask = set(self.modalities)

    # ---- ablation setters ----
    def configure_ablation(self, **kwargs):
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise AttributeError(f"Unknown ablation flag: {k}")
            setattr(self, k, v)
        if "modality_mask" in kwargs:
            self.modality_mask = set(kwargs["modality_mask"])

    def _encode(self, batch: dict) -> dict:
        feats = {}
        if "text" in self.modality_mask and "input_ids" in batch:
            t = self.text_enc(batch["input_ids"], batch.get("attention_mask"))
            feats["text"] = t["seq"]
        if "image" in self.modality_mask and "image" in batch:
            i = self.image_enc(batch["image"])
            feats["image"] = i["seq"]
        if "audio" in self.modality_mask and "audio" in batch:
            a = self.audio_enc(batch["audio"])
            feats["audio"] = a["seq"]
        if "video" in self.modality_mask and "video" in batch:
            v = self.video_enc(batch["video"])
            feats["video"] = v["seq"]
        # If no modality present, raise
        if not feats:
            raise ValueError("No modality inputs provided.")
        return feats

    def _zero_pool(self, device, dtype):
        return torch.zeros(1, self.d_model, device=device, dtype=dtype)

    def forward(self, batch: dict):
        feats = self._encode(batch)
        # AFN
        if self.use_afn:
            feats = self.afn(feats)

        # Populate missing modalities with zero placeholders so downstream layers
        # (which are trained with 4 modalities) still function during ablation.
        any_feat = next(iter(feats.values()))
        B = any_feat.size(0)
        for m in self.modalities:
            if m not in feats:
                feats[m] = torch.zeros(B, 1, self.d_model, device=any_feat.device, dtype=any_feat.dtype)

        # Early/Late fusion ablation paths
        if self.fusion_mode == "early":
            # concat pooled and mlp
            pooled = torch.stack([v.mean(dim=1) for v in feats.values()], dim=1).mean(dim=1)
            out = self.head(pooled, feats)
            return {"logits": out["logits"], "regression": out["regression"],
                    "contrastive_proj": out["contrastive_proj"],
                    "attn_maps": {}, "trimodal_gates": {}, "global_cls": pooled}
        if self.fusion_mode == "late":
            pooled = torch.stack([v.mean(dim=1) for v in feats.values()], dim=1).mean(dim=1)
            out = self.head(pooled, feats)
            return {"logits": out["logits"], "regression": out["regression"],
                    "contrastive_proj": out["contrastive_proj"],
                    "attn_maps": {}, "trimodal_gates": {}, "global_cls": pooled}

        # Level 1
        l1 = self.pairwise(feats)
        pair_repr = l1["pair_repr"]

        if not self.use_hierarchical:
            # only L1: pool all pairwise reps
            pooled = torch.stack(list(pair_repr.values()), dim=1).mean(dim=1)
            out = self.head(pooled, feats)
            return {"logits": out["logits"], "regression": out["regression"],
                    "contrastive_proj": out["contrastive_proj"],
                    "attn_maps": l1["attn_maps"], "trimodal_gates": {},
                    "global_cls": pooled}

        # Level 2
        if self.use_gating:
            l2 = self.trimodal(feats, pair_repr)
        else:
            # bypass gates: uniform
            with torch.no_grad():
                for m in self.modalities:
                    self.trimodal.mod_gates[m].data.zero_()  # sigmoid(0)=0.5
            l2 = self.trimodal(feats, pair_repr)
        trimodal_repr = l2["trimodal_repr"]

        # Level 3
        l3 = self.global_fusion(feats, pair_repr, trimodal_repr)
        global_cls = l3["global_cls"]

        out = self.head(global_cls, feats)
        return {
            "logits": out["logits"],
            "regression": out["regression"] if self.use_multitask else None,
            "contrastive_proj": out["contrastive_proj"] if self.use_contrastive_head else None,
            "attn_maps": l1["attn_maps"],
            "trimodal_gates": l2["trimodal_gates"],
            "global_cls": global_cls,
        }
