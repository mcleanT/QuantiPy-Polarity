"""Half-disk rose plot for axial polarity directions.

Convention (lifted from plot_rose_pair_halfdisk.py in the research repo):
    angles plotted as ((axis_deg % 180) + 180) % 180  — all in [0, 180).
    0° / 180° = polarity PARALLEL to image horizontal.
    90° = polarity PERPENDICULAR to image horizontal (typical migration direction).

Each cell appears once on the upper semicircle.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quantipy_polarity.viz._style import apply_nature_style, save_figure, PALETTE


def _axial_mod180(angles_deg: np.ndarray) -> np.ndarray:
    a = np.asarray(angles_deg, dtype=float)
    return ((a % 180.0) + 180.0) % 180.0


def plot_rose(
    angles_deg: np.ndarray,
    *,
    n_bins: int = 24,
    half_disk: bool = True,
    title: str | None = None,
    color: str | None = None,
    figsize: tuple[float, float] = (2.5, 2.5),
    ax: plt.Axes | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot a single half-disk (or full) rose histogram of axial angles.

    Parameters
    ----------
    angles_deg : 1-D array of polarity axis angles in degrees.
    n_bins : number of histogram bins (default 24 → 7.5° per bin for half-disk).
    half_disk : if True plot [0, 180); if False plot [0, 360).
    title : optional axis title.
    color : bar colour; defaults to PALETTE['phase1'].
    figsize : figure size in inches.
    ax : existing polar Axes to draw into; if None a new figure is created.

    Returns
    -------
    (fig, ax) tuple.
    """
    apply_nature_style()
    if ax is None:
        fig, ax = plt.subplots(
            subplot_kw={"projection": "polar"},
            figsize=figsize,
            constrained_layout=True,
        )
    else:
        fig = ax.get_figure()

    if color is None:
        color = PALETTE["phase1"]

    a = _axial_mod180(angles_deg[np.isfinite(angles_deg)])
    if half_disk:
        span = np.pi  # 0 to π
        bins = np.linspace(0, span, n_bins + 1)
        counts, _ = np.histogram(np.deg2rad(a), bins=bins)
        theta = (bins[:-1] + bins[1:]) / 2.0
        width = span / n_bins
        ax.set_thetamin(0)
        ax.set_thetamax(180)
    else:
        span = 2 * np.pi
        bins = np.linspace(0, span, n_bins + 1)
        counts, _ = np.histogram(np.deg2rad(a) % span, bins=bins)
        theta = (bins[:-1] + bins[1:]) / 2.0
        width = span / n_bins

    ax.bar(
        theta,
        counts,
        width=width,
        color=color,
        alpha=0.8,
        edgecolor="white",
        linewidth=0.3,
        align="center",
    )
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.tick_params(labelsize=5)
    ax.set_rlabel_position(90)
    ax.yaxis.set_tick_params(labelsize=4)
    ax.spines["polar"].set_linewidth(0.4)

    if title:
        ax.set_title(title, fontsize=7, fontweight="bold", pad=4)

    return fig, ax


def plot_rose_grouped(
    df: pd.DataFrame,
    *,
    condition_col: str = "condition",
    angle_col: str = "axis_deg",
    n_bins: int = 24,
    half_disk: bool = True,
    figsize_per_panel: tuple[float, float] = (2.5, 2.5),
) -> plt.Figure:
    """Plot one rose per condition group in a row of subplots.

    Parameters
    ----------
    df : DataFrame with at least `angle_col` and optionally `condition_col`.
    condition_col : column used to split groups; if absent or all-None,
        treats entire df as one group.
    angle_col : column containing polarity angles in degrees.
    n_bins, half_disk : forwarded to plot_rose.
    figsize_per_panel : size of each individual panel.

    Returns
    -------
    matplotlib Figure.
    """
    apply_nature_style()
    conditions = (
        sorted(df[condition_col].dropna().unique())
        if condition_col in df.columns and df[condition_col].notna().any()
        else ["all"]
    )
    n = len(conditions)
    fig, axes = plt.subplots(
        1,
        n,
        subplot_kw={"projection": "polar"},
        figsize=(figsize_per_panel[0] * n, figsize_per_panel[1]),
        constrained_layout=True,
    )
    if n == 1:
        axes = [axes]

    palette_vals = list(PALETTE.values())
    for i, (cond, ax) in enumerate(zip(conditions, axes)):
        if cond == "all":
            angles = df[angle_col].to_numpy(dtype=float)
        else:
            angles = df[df[condition_col] == cond][angle_col].to_numpy(dtype=float)
        color = palette_vals[i % len(palette_vals)]
        plot_rose(
            angles,
            n_bins=n_bins,
            half_disk=half_disk,
            title=str(cond),
            color=color,
            ax=ax,
        )

    return fig


def save_rose(
    angles_deg: np.ndarray,
    stem: Path,
    **kwargs: object,
) -> list[Path]:
    """Plot single-group rose and save; return written paths."""
    fig, _ax = plot_rose(angles_deg, **kwargs)
    paths = save_figure(fig, stem)
    plt.close(fig)
    return paths
