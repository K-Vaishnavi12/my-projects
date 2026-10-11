# HAFT-MFN — Viva Explanation

**Q1. What problem does the project solve?**
It processes and fuses information from **four modalities — text, image, audio, video** — for tasks such as sentiment analysis, emotion recognition, and audio-visual action recognition, achieving higher accuracy and lower computational cost than prior multimodal transformers.

**Q2. What is multimodal learning?**
Learning from more than one data type. Each modality carries complementary information (e.g., words say *"great"*, tone says *sarcastic*); combining them yields more robust predictions.

**Q3. Why four modalities?**
Because human communication and real-world events are inherently multimodal. Each provides different cues: text (semantics), image (visual context), audio (prosody/paralinguistics), video (motion and temporal dynamics).

**Q4. Why RoBERTa?**
RoBERTa is a strong, robustly optimized BERT variant that produces excellent contextualized embeddings and is well suited to sentiment/emotion text.

**Q5. Why ResNet-50 + ViT?**
ResNet-50 captures **local convolutional patterns** (edges, textures). ViT captures **global spatial relationships** via self-attention over patches. Combining them yields both local and global visual features.

**Q6. Why Wav2Vec 2.0 + MFCC?**
Wav2Vec 2.0 gives learned self-supervised speech representations. MFCC provides classical, hand-crafted acoustic features (spectral envelope). Together they cover both learned and traditional audio information.

**Q7. Why TimeSformer + 3D-CNN?**
TimeSformer models spatiotemporal attention across frames. 3D-CNN captures short-range motion dynamics. Their combination handles both long-range temporal reasoning and fine-grained motion.

**Q8. What is AFN?**
Adaptive Feature Normalization projects each modality's features into a **unified embedding space** through per-modality LayerNorm + projection + learnable affine `(γ, β)` + a residual gate. It prevents any single modality from dominating fusion and equalizes distribution scales.

**Q9. What is cross-modal attention?**
Attention where **queries** come from one modality and **keys/values** from another. It lets one modality dynamically attend to relevant parts of another modality.

**Q10. Why hierarchical fusion?**
Because modalities interact at multiple levels: (i) pairwise (Level 1), (ii) trimodal groups (Level 2), (iii) global multimodal (Level 3). Hierarchical fusion models each interaction type explicitly instead of forcing everything through a single attention block.

**Q11. What is learnable gating?**
Sigmoid gates over learnable parameters that dynamically control how much each modality (and each pairwise interaction) contributes to the fused representation, per input.

**Q12. Why contrastive learning?**
Cross-modal InfoNCE encourages representations of the *same sample*'s different modalities to be similar, and different samples' modalities to be dissimilar. This aligns modalities in a shared semantic space.

**Q13. Why multi-task learning?**
Sharing a backbone across classification, regression, and contrastive objectives regularizes learning and improves generalization, especially where labels are scarce.

**Q14. What datasets are used?**
CMU-MOSEI, MELD, VGGSound, IEMOCAP — covering sentiment, emotion, action, and dimensional-emotion tasks.

**Q15. What metrics are used?**
Sentiment: Acc-2/Acc-7, weighted F1, MAE, Pearson. Emotion: accuracy, weighted/macro F1, precision, recall. Action: Top-1, Top-5, mAP. Efficiency: FLOPs, parameters, inference time.

**Q16. What are the ablation experiments?**
Removing AFN, hierarchical fusion, learnable gating, contrastive learning, multi-task learning; using only text or only video; comparing early fusion vs late fusion vs HAFT-MFN.

**Q17. How does HAFT-MFN improve over baselines?**
By combining AFN (fair modality scaling), three-level hierarchical attention (fine-to-coarse interactions), learnable gating (adaptive contribution), and multi-task learning (better representations). The paper reports **+4.2% / +3.8% / +5.1%** on CMU-MOSEI / MELD / VGGSound and **-18.3% FLOPs** vs. prior SOTA.

**Q18. Limitations?**
- Requires all four modalities to fully exploit the architecture.
- Pretrained encoders are large; training cost is significant.
- Reference numbers assume specific hardware (4×A100) and preprocessing.
- Some datasets (CMU-MOSEI etc.) have licensing constraints; end-users must obtain and preprocess them.

**Q19. Future improvements?**
More modalities (depth/thermal/physiological), model compression (KD/pruning/quantization), large-scale self-supervised pretraining, better interpretability (attention rollout, counterfactuals), and domain adaptation.
