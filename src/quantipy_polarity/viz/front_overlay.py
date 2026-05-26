"""Per-FOV migration-front overlay figure.

Renders membrane channel image with:
- Cell outlines (thin, semi-transparent)
- Front ribbon (dilated front_mask pixels, coloured phase2/orange)
- Per-cell migration direction arrows (green arrows toward front)

Lifted from pipeline/debug_polarity.py display conventions:
- Yellow → phase2 orange (lab palette)
- Green arrows for migration direction
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.segmentation import find_boundaries

from quantipy_polarity.viz._style import apply_nature_style, PALETTE


def plot_front_overlay(
    membrane: np.ndarray,
    labels: np.ndarray,
    front_mask: np.ndarray,
    fov_df: pd.DataFrame | None = None,
    *,
    vx: np.ndarray | None = None,
    vy: np.ndarray | None = None,
    pixel_size_um: float = 1.0,
    arrow_scale: float = 15.0,
    figsize: tuple[float, float] = (4.0, 4.0),
    title: str | None = None,
) -> plt.Figure:
    """Render a migration-front overlay figure.

    Parameters
    ----------
    membrane : (H, W) uint16 or float membrane image.
    labels : (H, W) uint16 label mask.
    front_mask : (H, W) bool front-pixel mask from detect_front.
    fov_df : optional DataFrame with cell_id, centroid_y, centroid_x columns
             for placing arrow origins.
    vx, vy : (H, W) displacement fields. If provided AND fov_df is provided,
             arrows drawn at cell centroids pointing along mean (vx, vy).
    pixel_size_um : microns per pixel (unused in px-space drawing; for label).
    arrow_scale : arrow length scaling factor.
    figsize : figure size in inches.
    title : optional title.

    Returns
    -------
    matplotlib Figure.
    """
    apply_nature_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize, constrained_layout=True)

    mem = membrane.astype(float)
    vmin, vmax = np.percentile(mem[mem > 0], [2, 98]) if mem.max() > 0 else (0, 1)
    ax.imshow(mem, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")

    # Cell outlines
    outline = find_boundaries(labels, mode="outer")
    ax.contour(outline, levels=[0.5], colors=[PALETTE["composite"]],
               linewidths=0.3, alpha=0.5)

    # Front ribbon: dilate front_mask by 2 px for visibility
    if front_mask.any():
        ribbon = ndi.binary_dilation(front_mask, iterations=2)
        rgba = np.zeros((*membrane.shape, 4), dtype=float)
        # Orange front colour
        r, g, b = tuple(
            int(PALETTE["phase2"][i: i + 2], 16) / 255.0
            for i in (1, 3, 5)
        )
        rgba[ribbon, 0] = r
        rgba[ribbon, 1] = g
        rgba[ribbon, 2] = b
        rgba[ribbon, 3] = 0.7
        ax.imshow(rgba, interpolation="nearest")

    # Per-cell migration arrows
    if fov_df is not None and vx is not None and vy is not None and len(fov_df) > 0:
        for _, row in fov_df.iterrows():
            cid = int(row["cell_id"])
            cy = float(row["centroid_y"])
            cx = float(row["centroid_x"])
            cell_mask = labels == cid
            if not cell_mask.any():
                continue
            mean_vx = float(vx[cell_mask].mean())
            mean_vy = float(vy[cell_mask].mean())
            length = float(np.hypot(mean_vx, mean_vy))
            if length < 1e-6:
                continue
            scale = arrow_scale / max(length, 1.0)
            ax.annotate(
                "",
                xy=(cx + mean_vx * scale, cy + mean_vy * scale),
                xytext=(cx, cy),
                arrowprops=dict(
                    arrowstyle="->",
                    color=PALETTE["phase3"],  # green
                    lw=0.6,
                ),
            )

    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=8, fontweight="bold")

    return fig


def save_front_overlay(
    membrane: np.ndarray,
    labels: np.ndarray,
    front_mask: np.ndarray,
    stem: Path,
    **kwargs: object,
) -> Path:
    """Save front overlay as PNG only (QC overlay; raster sufficient).

    Returns path to the written PNG.
    """
    import os, tempfile
    fig = plot_front_overlay(membrane, labels, front_mask, **kwargs)
    out = Path(stem).with_suffix(".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=".overlay_tmp_", suffix=".png")
    os.close(fd)
    try:
        fig.savefig(tmp, dpi=600, bbox_inches="tight")
        os.replace(tmp, out)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    finally:
        plt.close(fig)
    return out
