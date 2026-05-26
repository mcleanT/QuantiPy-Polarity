"""Population summary figure for across-experiment polarity data.

Four-panel figure:
A. Polarity magnitude distribution (histogram)
B. Aggregate half-disk rose (all cells)
C. Distance-to-front distribution (if dist_to_front_um populated)
D. Per-FOV cell count bar chart
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quantipy_polarity.viz._style import apply_nature_style, save_figure, PALETTE
from quantipy_polarity.viz.rose_plot import plot_rose


def plot_population_summary(
    per_cell: pd.DataFrame,
    *,
    n_rose_bins: int = 24,
    figsize: tuple[float, float] = (7.0, 3.5),
    suptitle: str | None = None,
) -> plt.Figure:
    """Generate a 4-panel population summary figure.

    Parameters
    ----------
    per_cell : experiment-wide per_cell DataFrame. Required columns:
        fov_id, magnitude, axis_deg.
        Optional: dist_to_front_um (panel C is greyed if absent/all-NaN).
    n_rose_bins : bins for the aggregate rose.
    figsize : total figure size.
    suptitle : optional super-title.

    Returns
    -------
    matplotlib Figure.
    """
    apply_nature_style()

    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1])
    ax_mag = fig.add_subplot(gs[0])
    ax_rose = fig.add_subplot(gs[1], projection="polar")
    ax_dist = fig.add_subplot(gs[2])
    ax_count = fig.add_subplot(gs[3])

    # A. Magnitude distribution
    mags = per_cell["magnitude"].dropna().to_numpy(dtype=float)
    if len(mags) > 0:
        ax_mag.hist(
            mags,
            bins=30,
            color=PALETTE["phase1"],
            edgecolor="white",
            linewidth=0.3,
            alpha=0.85,
        )
    ax_mag.set_xlabel("Polarity magnitude", fontsize=7)
    ax_mag.set_ylabel("Cells", fontsize=7)
    ax_mag.set_title("A  Magnitude", fontsize=8, fontweight="bold", loc="left")

    # B. Aggregate rose
    angles = per_cell["axis_deg"].dropna().to_numpy(dtype=float)
    plot_rose(
        angles, n_bins=n_rose_bins, half_disk=True, color=PALETTE["phase1"], ax=ax_rose
    )
    ax_rose.set_title("B  Polarity axes", fontsize=8, fontweight="bold", pad=4)

    # C. Distance to front
    if "dist_to_front_um" in per_cell.columns:
        dists = per_cell["dist_to_front_um"].dropna().to_numpy(dtype=float)
    else:
        dists = np.array([])
    if len(dists) > 0:
        ax_dist.hist(
            dists,
            bins=30,
            color=PALETTE["phase2"],
            edgecolor="white",
            linewidth=0.3,
            alpha=0.85,
        )
        ax_dist.set_xlabel("Dist to front (µm)", fontsize=7)
    else:
        ax_dist.text(
            0.5,
            0.5,
            "No front data",
            ha="center",
            va="center",
            transform=ax_dist.transAxes,
            fontsize=7,
            color="gray",
        )
        ax_dist.set_axis_off()
    ax_dist.set_title("C  Dist to front", fontsize=8, fontweight="bold", loc="left")

    # D. Per-FOV cell count
    counts = per_cell.groupby("fov_id").size().sort_index()
    if len(counts) > 0:
        fov_labels = [str(f) for f in counts.index]
        ax_count.bar(
            range(len(counts)),
            counts.values,
            color=PALETTE["phase3"],
            edgecolor="white",
            linewidth=0.3,
        )
        ax_count.set_xticks(range(len(counts)))
        ax_count.set_xticklabels(fov_labels, rotation=45, ha="right", fontsize=5)
        ax_count.set_ylabel("Cells", fontsize=7)
    ax_count.set_title("D  Cells per FOV", fontsize=8, fontweight="bold", loc="left")

    if suptitle:
        fig.suptitle(suptitle, fontsize=9, fontweight="bold")

    return fig


def save_population_summary(
    per_cell: pd.DataFrame,
    stem: Path,
    **kwargs: object,
) -> list[Path]:
    """Generate and save the population summary; return written paths."""
    fig = plot_population_summary(per_cell, **kwargs)
    paths = save_figure(fig, stem)
    plt.close(fig)
    return paths
