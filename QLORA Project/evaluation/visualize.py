"""
Visualisation helpers for Phase 3 RAGAS evaluation.

Two charts are produced:

    plot_ragas_comparison(summary)  -> grouped bar chart (one bar per system,
                                       grouped by metric; saved as
                                       results/ragas_comparison.png)

    plot_ragas_radar(summary)       -> radar / spider chart (one polygon per
                                       system; saved as
                                       results/ragas_radar.png)

Both functions accept the summary DataFrame produced by
`evaluation.ragas_eval.run_full_evaluation` (rows = systems,
columns = `{metric}_mean`).

Style choices
-------------
- Publication-ready: 300 dpi, tight layout, sans-serif font.
- Colour palette is read from `cfg.eval.system_colors` so it stays in sync
  with whatever the user chooses in the config (no hard-coded colours here).
- Pure matplotlib (no seaborn dep) — keeps the install footprint small.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

# Allow `python -m evaluation.visualize`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from configs.config import FineTuneConfig, get_default_config

logger = logging.getLogger("amazonqa.eval.visualize")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _metric_columns(summary: pd.DataFrame) -> List[str]:
    """Return the ordered list of metric columns present in the summary."""
    return [c for c in summary.columns if c.endswith("_mean")]


def _short_metric_name(col: str) -> str:
    """Strip the trailing `_mean` so axes look clean."""
    return col[:-5] if col.endswith("_mean") else col


def _ensure_results_dir(cfg: FineTuneConfig) -> Path:
    cfg.paths.results_dir.mkdir(parents=True, exist_ok=True)
    return cfg.paths.results_dir


# ---------------------------------------------------------------------------
# 1. Grouped bar chart
# ---------------------------------------------------------------------------
def plot_ragas_comparison(
    summary: pd.DataFrame,
    *,
    cfg: Optional[FineTuneConfig] = None,
    save_path: Optional[Path] = None,
    show: bool = False,
) -> Path:
    """
    Grouped bar chart: x-axis = metrics, bars = systems, y-axis = score.

    Args:
        summary: DataFrame indexed by system name with `{metric}_mean` columns.
        cfg: Project config (controls colours + output path).
        save_path: Override default output location.
        show: Call plt.show() (useful in notebooks).

    Returns:
        Path the figure was written to.
    """
    import matplotlib.pyplot as plt

    cfg = cfg or get_default_config()

    metric_cols = _metric_columns(summary)
    if not metric_cols:
        raise ValueError(
            "Summary DataFrame has no `_mean` columns. "
            "Did you pass the right object from run_full_evaluation()?"
        )

    systems = list(summary.index)
    metrics_short = [_short_metric_name(c) for c in metric_cols]
    n_systems = len(systems)
    n_metrics = len(metric_cols)

    # Bar layout: each metric gets a cluster of n_systems bars.
    bar_width = 0.8 / n_systems
    x_positions = np.arange(n_metrics)

    fig, ax = plt.subplots(figsize=(max(8, 1.5 * n_metrics + 3), 5.5), dpi=120)

    for i, system in enumerate(systems):
        # `i - (n_systems-1)/2` centres the cluster on each metric tick
        offsets = x_positions + (i - (n_systems - 1) / 2) * bar_width
        values = [summary.loc[system, c] for c in metric_cols]
        color = cfg.eval.system_colors.get(system, None)
        label = cfg.eval.system_display_names.get(system, system)
        bars = ax.bar(
            offsets,
            values,
            width=bar_width,
            color=color,
            edgecolor="black",
            linewidth=0.5,
            label=label,
        )
        # Numerical label on top of each bar — handy for screenshots.
        for bar, v in zip(bars, values):
            if pd.notna(v):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.015,
                    f"{v:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([m.replace("_", "\n") for m in metrics_short], fontsize=10)
    ax.set_ylabel("Score (0 - 1, higher is better)", fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_title(
        "RAGAS Evaluation — Three-System Comparison\n(AmazonQA-RAG)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=True, fontsize=9)
    fig.tight_layout()

    out = save_path or (_ensure_results_dir(cfg) / cfg.eval.bar_chart_filename)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    logger.info("Bar chart saved to %s", out)
    if show:
        plt.show()
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# 2. Radar / spider chart
# ---------------------------------------------------------------------------
def plot_ragas_radar(
    summary: pd.DataFrame,
    *,
    cfg: Optional[FineTuneConfig] = None,
    save_path: Optional[Path] = None,
    show: bool = False,
) -> Path:
    """
    Radar chart: one polygon per system, axes = metrics.

    Use sparingly — bar charts are usually clearer for ≤ 6 metrics. The
    radar is most useful when you want to *demonstrate* that one system
    Pareto-dominates the others (its polygon strictly contains the others).
    """
    import matplotlib.pyplot as plt

    cfg = cfg or get_default_config()

    metric_cols = _metric_columns(summary)
    if not metric_cols:
        raise ValueError("Summary DataFrame has no `_mean` columns.")

    systems = list(summary.index)
    metrics_short = [_short_metric_name(c) for c in metric_cols]
    n_metrics = len(metric_cols)

    # Angles for each axis (closing the polygon by repeating the first angle).
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(
        figsize=(7, 7), dpi=120, subplot_kw=dict(polar=True)
    )

    for system in systems:
        values = [summary.loc[system, c] for c in metric_cols]
        values = [float(v) if pd.notna(v) else 0.0 for v in values]
        values += values[:1]  # close polygon

        color = cfg.eval.system_colors.get(system, None)
        label = cfg.eval.system_display_names.get(system, system)
        ax.plot(angles, values, color=color, linewidth=2, label=label)
        ax.fill(angles, values, color=color, alpha=0.18)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics_short, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8, color="grey")
    ax.set_rlabel_position(45)

    ax.set_title(
        "RAGAS Radar — Three-System Comparison\n(AmazonQA-RAG)",
        fontsize=13,
        fontweight="bold",
        pad=18,
    )
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.05), frameon=True, fontsize=9)
    fig.tight_layout()

    out = save_path or (_ensure_results_dir(cfg) / cfg.eval.radar_chart_filename)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    logger.info("Radar chart saved to %s", out)
    if show:
        plt.show()
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# CLI helper — re-render charts from an existing summary CSV
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Re-render Phase 3 charts from an existing ragas_summary.csv."
    )
    parser.add_argument(
        "--summary",
        type=str,
        default=None,
        help="Path to ragas_summary.csv. Defaults to results/ragas_summary.csv.",
    )
    args = parser.parse_args()
    cfg = get_default_config()

    summary_path = Path(
        args.summary or (cfg.paths.results_dir / cfg.eval.summary_filename)
    )
    if not summary_path.exists():
        raise SystemExit(f"Summary CSV not found: {summary_path}")

    df = pd.read_csv(summary_path, index_col=0)
    plot_ragas_comparison(df, cfg=cfg)
    plot_ragas_radar(df, cfg=cfg)


__all__ = ["plot_ragas_comparison", "plot_ragas_radar"]
