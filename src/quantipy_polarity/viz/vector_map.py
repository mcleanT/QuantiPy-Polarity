"""Per-FOV polarity vector map.

Renders cell outlines on the membrane channel image with an axial arrow
per cell coloured by polarity magnitude.

Lifted from:
- pipeline/plot_fov_polarity_panel.py: cell-outline + axis-line drawing
- pipeline/debug_polarity.py:draw_axial_line(): angle/length convention
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from skimage.segmentation import find_boundaries

from quantipy_polarity.viz._style import apply_nature_style, save_figure, PALETTE


def _draw_axial_line(
    ax: plt.Axes,
    cx: float,
    cy: float,
    angle_deg: float,
    length: float,
    color: object,
    lw: float = 0.8,
) -> None:
    """Draw an axial line through (cx, cy) on ax.

    Angle 0° = horizontal (+x). Image y-axis points down so -sin converts
    screen-down pixel coords to math-frame-up angle convention.
    """
    th = np.radians(angle_deg)
    dx = np.cos(th) * length / 2.0
    dy = -np.sin(th) * length / 2.0
    ax.plot(
        [cx - dx, cx + dx],
        [cy - dy, cy + dy],
        "-",
        color=color,
        lw=lw,
        solid_capstyle="round",
    )


def plot_vector_map(
    membrane: np.ndarray,
    labels: np.ndarray,
    fov_df: pd.DataFrame,
    *,
    pixel_size_um: float = 1.0,
    vector_scale: float = 1.0,
    cmap: str = "viridis",
    figsize: tuple[float, float] = (4.0, 4.0),
    title: str | None = None,
) -> plt.Figure:
    """Generate a per-FOV polarity vector map figure.

    Parameters
    ----------
    membrane : (H, W) float or uint16 membrane channel image.
    labels : (H, W) uint16 label mask.
    fov_df : DataFrame with columns cell_id, centroid_y, centroid_x,
             axis_deg, magnitude (single FOV).
    pixel_size_um : microns per pixel (used to scale arrow length).
    vector_scale : multiplicative scale applied to arrow length.
    cmap : matplotlib colourmap for magnitude colouring.
    figsize : figure size in inches.
    title : optional axis title.

    Returns
    -------
    matplotlib Figure (caller closes it after saving).
    """
    apply_nature_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize, constrained_layout=True)

    mem = membrane.astype(float)
    vmin, vmax = np.percentile(mem[mem > 0], [2, 98]) if mem.max() > 0 else (0, 1)
    ax.imshow(mem, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")

    # Cell outlines
    outline = find_boundaries(labels, mode="outer")
    ax.contour(
        outline, levels=[0.5], colors=[PALETTE["composite"]], linewidths=0.4, alpha=0.6
    )

    # Arrows coloured by magnitude
    if len(fov_df) > 0:
        mags = fov_df["magnitude"].to_numpy(dtype=float)
        norm = mcolors.Normalize(vmin=0, vmax=max(mags.max(), 1e-9))
        cmap_obj = plt.get_cmap(cmap)
        for _, row in fov_df.iterrows():
            cy = float(row["centroid_y"])
            cx = float(row["centroid_x"])
            ang = float(row["axis_deg"])
            mag = float(row["magnitude"])
            # Arrow length: magnitude * scale * ~10 px reference
            length = mag * vector_scale * 10.0
            color = cmap_obj(norm(mag))
            _draw_axial_line(ax, cx, cy, ang, length, color=color, lw=1.0)

        sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
        cbar.set_label("Polarity magnitude", fontsize=6)
        cbar.ax.tick_params(labelsize=5)

    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=8, fontweight="bold")

    return fig


def save_vector_map(
    membrane: np.ndarray,
    labels: np.ndarray,
    fov_df: pd.DataFrame,
    stem: Path,
    **kwargs: object,
) -> list[Path]:
    """Convenience wrapper: plot and save, return written paths."""
    fig = plot_vector_map(membrane, labels, fov_df, **kwargs)
    paths = save_figure(fig, stem)
    plt.close(fig)
    return paths
