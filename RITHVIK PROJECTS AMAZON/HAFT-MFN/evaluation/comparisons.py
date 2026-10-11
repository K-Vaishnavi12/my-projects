"""IMMUTABLE reference tables from the target paper.

These values are the authoritative reference values. They are copied verbatim
from the master specification and MUST NOT be modified, rounded, recomputed,
or replaced by any trained-model output.
"""

# ---------------------------------------------------------------------------
# Table 1 — CMU-MOSEI
# ---------------------------------------------------------------------------
TABLE1_TITLE = "Table 1: Performance comparison on CMU-MOSEI dataset. Best results in bold, second best underlined."
TABLE1_HEADERS = ["Method", "Acc-2 (%)", "Acc-7 (%)", "F1-Score (%)", "MAE \u2193", "Corr \u2191"]
TABLE1_ROWS = [
    ("MulT [9]",        "82.5", "51.8", "82.3", "0.580", "0.703"),
    ("MMTSA [2]",       "83.1", "52.4", "82.9", "0.572", "0.715"),
    ("MBT [15]",        "83.8", "53.2", "83.6", "0.565", "0.721"),
    ("PSACF [4]",       "84.2", "53.9", "84.1", "0.558", "0.728"),
    ("CMDAF [8]",       "84.7", "54.3", "84.5", "0.551", "0.735"),
    ("MPT-HCL [13]",    "85.1", "54.8", "84.9", "0.545", "0.742"),
    ("AVT-CA [11]",     "84.9", "54.5", "84.7", "0.548", "0.738"),
    ("TMBL [17]",       "85.3", "55.1", "85.2", "0.542", "0.745"),
    ("HAFT-MFN (Ours)", "89.5", "58.9", "89.1", "0.498", "0.781"),
    ("Improvement",     "+4.2", "+3.8", "+3.9", "-0.044", "+0.036"),
]

# ---------------------------------------------------------------------------
# Table 2 — MELD
# ---------------------------------------------------------------------------
TABLE2_TITLE = "Table 2: Performance comparison on MELD dataset for emotion recognition."
TABLE2_HEADERS = ["Method", "Accuracy (%)", "W-F1 (%)", "Precision (%)", "Recall (%)"]
TABLE2_ROWS = [
    ("EMSAN [7]",       "92.28", "91.85", "91.92", "91.78"),
    ("MMTSA [2]",       "90.45", "89.92", "90.18", "89.85"),
    ("PSACF [4]",       "91.73", "91.28", "91.45", "91.21"),
    ("CMDAF [8]",       "92.15", "91.72", "91.88", "91.65"),
    ("MPT-HCL [13]",    "93.02", "92.51", "92.68", "92.45"),
    ("AVT-CA [11]",     "92.87", "92.35", "92.52", "92.28"),
    ("HAFT-MFN (Ours)", "96.82", "96.31", "96.45", "96.18"),
    ("Improvement",     "+3.8",  "+3.8",  "+3.77", "+3.73"),
]

# ---------------------------------------------------------------------------
# Table 3 — VGG Sound
# ---------------------------------------------------------------------------
TABLE3_TITLE = "Table 3: Performance comparison on VGG Sound dataset for audio-visual classification."
TABLE3_HEADERS = ["Method", "Top-1 Acc (%)", "Top-5 Acc (%)", "mAP (%)"]
TABLE3_ROWS = [
    ("MBT [15]",           "51.2", "78.5", "48.7"),
    ("AVT [6]",            "61.2", "84.3", "58.9"),
    ("Sparse Fusion [19]", "59.8", "83.1", "57.2"),
    ("MT-CMVAD [12]",      "62.5", "85.2", "60.1"),
    ("AVT-CA [11]",        "63.1", "85.8", "60.8"),
    ("HAFT-MFN (Ours)",    "68.2", "89.7", "65.9"),
    ("Improvement",        "+5.1", "+3.9", "+5.1"),
]

# ---------------------------------------------------------------------------
# Table 4 — IEMOCAP
# ---------------------------------------------------------------------------
TABLE4_TITLE = "Table 4: Performance comparison on IEMOCAP dataset."
TABLE4_HEADERS = ["Method", "W-F1 (%)", "Accuracy (%)", "Valence MAE \u2193", "Arousal MAE \u2193"]
TABLE4_ROWS = [
    ("MulT [9]",        "68.45", "69.12", "0.142", "0.138"),
    ("PSACF [4]",       "70.28", "71.05", "0.135", "0.131"),
    ("MPT-HCL [13]",    "72.51", "73.28", "0.128", "0.125"),
    ("AAT-CGF [20]",    "71.89", "72.65", "0.131", "0.127"),
    ("HAFT-MFN (Ours)", "76.83", "77.52", "0.115", "0.112"),
    ("Improvement",     "+4.32", "+4.24", "-0.013", "-0.013"),
]

# ---------------------------------------------------------------------------
# Table 5 — Ablation Study on CMU-MOSEI
# ---------------------------------------------------------------------------
TABLE5_TITLE = "Table 5: Ablation study on CMU-MOSEI dataset analyzing component contributions."
TABLE5_HEADERS = ["Configuration", "Acc-2 (%)", "F1-Score (%)", "MAE \u2193"]
TABLE5_ROWS = [
    ("Full HAFT-MFN",                          "89.5", "89.1", "0.498"),
    ("w/o Adaptive Feature Normalization",     "86.2", "85.8", "0.532"),
    ("w/o Hierarchical Fusion (only Level 1)", "85.7", "85.3", "0.541"),
    ("w/o Learnable Gating",                   "87.1", "86.7", "0.518"),
    ("w/o Contrastive Learning",               "87.8", "87.4", "0.509"),
    ("w/o Multi-Task Learning",                "86.9", "86.5", "0.523"),
    ("Single Modality (Text only)",            "78.3", "77.9", "0.625"),
    ("Single Modality (Video only)",           "72.5", "72.1", "0.687"),
    ("Early Fusion (Concatenation)",           "82.4", "82.0", "0.578"),
    ("Late Fusion (Average)",                  "83.8", "83.4", "0.562"),
]

# ---------------------------------------------------------------------------
# Table 6 — Computational Efficiency
# ---------------------------------------------------------------------------
TABLE6_TITLE = "Table 6: Computational efficiency comparison. Lower is better for FLOPs, Parameters, and Inference Time."
TABLE6_HEADERS = ["Method", "FLOPs (G)", "Parameters (M)", "Inference Time (ms)", "Acc-2 (%)"]
TABLE6_ROWS = [
    ("MulT [9]",           "45.2",   "128.5",  "42.3",   "82.5"),
    ("MMTSA [2]",          "38.7",   "115.2",  "35.8",   "83.1"),
    ("MBT [15]",           "32.5",   "98.7",   "28.9",   "83.8"),
    ("PSACF [4]",          "41.8",   "122.3",  "38.5",   "84.2"),
    ("CMDAF [8]",          "43.2",   "125.8",  "40.1",   "84.7"),
    ("MPT-HCL [13]",       "46.5",   "132.4",  "44.2",   "85.1"),
    ("Sparse Fusion [19]", "28.3",   "92.1",   "25.6",   "81.9"),
    ("HAFT-MFN",           "35.8",   "108.3",  "31.2",   "89.5"),
    ("Efficiency Gain",    "-18.3%", "-18.2%", "-29.4%", "+4.4%"),
]


ALL_TABLES = {
    "Table 1": (TABLE1_TITLE, TABLE1_HEADERS, TABLE1_ROWS),
    "Table 2": (TABLE2_TITLE, TABLE2_HEADERS, TABLE2_ROWS),
    "Table 3": (TABLE3_TITLE, TABLE3_HEADERS, TABLE3_ROWS),
    "Table 4": (TABLE4_TITLE, TABLE4_HEADERS, TABLE4_ROWS),
    "Table 5": (TABLE5_TITLE, TABLE5_HEADERS, TABLE5_ROWS),
    "Table 6": (TABLE6_TITLE, TABLE6_HEADERS, TABLE6_ROWS),
}


def format_table_markdown(title, headers, rows):
    lines = [f"### {title}", "",
             "| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


# Aliases retained for backwards compatibility with earlier evaluation code.
REFERENCE_CMU_MOSEI = TABLE1_ROWS
REFERENCE_MELD = TABLE2_ROWS
REFERENCE_VGGSOUND = TABLE3_ROWS
REFERENCE_IEMOCAP = TABLE4_ROWS
REFERENCE_ABLATION = TABLE5_ROWS
REFERENCE_EFFICIENCY = TABLE6_ROWS


def format_table(title, header, rows, highlight_row=None):
    """Backwards-compatible plain markdown table."""
    return format_table_markdown(title, header, [tuple(str(c) for c in r) for r in rows])
