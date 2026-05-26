"""QP-vs-Python comparison: cell matching, linear regression, and figure.

Public API:
    run_validation(qp_path, py_path, output_dir, *, tolerance_px=5.0) -> ValidationResult

Matching algorithm:
    Per-FOV nearest-neighbour on (centroid_y, centroid_x). Cells with no match
    within `tolerance_px` Euclidean distance are excluded and logged. Matched cells
    only appear once (mutual exclusion enforced by greedy assignment).

Figure layout (2 panels):
    Left:  scatter qp_magnitude (x) vs py_magnitude (y) + y=x line + R²/slope label
    Right: scatter qp_axis_deg (x) vs py_axis_deg (y) + y=x line + R²/slope label
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
from scipy.stats import linregress

log = logging.getLogger(__name__)

_NATURE_RC: dict = {
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "font.family": "Arial",
    "axes.linewidth": 0.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "font.size": 7,
    "axes.titlesize": 8,
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
}

# Lab palette (CB-safe)
_BLUE = "#5B8FD6"
_ORANGE = "#E28E2C"


@dataclasses.dataclass(frozen=True)
class ValidationResult:
    """Metrics from a QP-vs-Python paired comparison."""
    r2_magnitude: float
    slope_magnitude: float
    intercept_magnitude: float
    r2_angle: float
    slope_angle: float
    intercept_angle: float
    n_matched: int
    n_unmatched_qp: int
    n_unmatched_py: int


def _match_cells(
    qp_df: pd.DataFrame,
    py_df: pd.DataFrame,
    tolerance_px: float = 5.0,
) -> pd.DataFrame:
    """Nearest-neighbour match cells per FOV.

    Returns a DataFrame with columns:
        fov_id, cell_id_qp, cell_id_py,
        qp_magnitude, qp_axis_deg, py_magnitude, py_axis_deg
    """
    rows: list[dict] = []
    for fov_id in qp_df["fov_id"].unique():
        qp_fov = qp_df[qp_df["fov_id"] == fov_id].reset_index(drop=True)
        py_fov = py_df[py_df["fov_id"] == fov_id].reset_index(drop=True)
        if py_fov.empty:
            log.warning("fov %s: no Python cells, skipping", fov_id)
            continue
        qp_pts = qp_fov[["centroid_y", "centroid_x"]].to_numpy()
        py_pts = py_fov[["centroid_y", "centroid_x"]].to_numpy()
        tree = KDTree(py_pts)
        dists, idxs = tree.query(qp_pts, workers=-1)
        used_py: set[int] = set()
        for qp_i, (dist, py_i) in enumerate(zip(dists, idxs)):
            if dist > tolerance_px or py_i in used_py:
                continue
            used_py.add(int(py_i))
            rows.append({
                "fov_id": fov_id,
                "cell_id_qp": int(qp_fov.at[qp_i, "cell_id"]),
                "cell_id_py": int(py_fov.at[int(py_i), "cell_id"]),
                "qp_magnitude": float(qp_fov.at[qp_i, "qp_magnitude"]),
                "qp_axis_deg": float(qp_fov.at[qp_i, "qp_axis_deg"]),
                "py_magnitude": float(py_fov.at[int(py_i), "py_magnitude"]),
                "py_axis_deg": float(py_fov.at[int(py_i), "py_axis_deg"]),
            })
    return pd.DataFrame(rows)


def _r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Return (r², slope, intercept) from OLS linear regression."""
    result = linregress(x, y)
    return float(result.rvalue ** 2), float(result.slope), float(result.intercept)


def make_figure(matched: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    """Generate 2-panel validation scatter figure.

    Returns (pdf_path, png_path).
    """
    with plt.rc_context(_NATURE_RC):
        fig, axes = plt.subplots(1, 2, figsize=(7, 3.5), constrained_layout=True)

        for ax, (xcol, ycol, xlabel, ylabel, title, ref_lo, ref_hi) in zip(
            axes,
            [
                (
                    "qp_magnitude", "py_magnitude",
                    "QP magnitude", "Python magnitude",
                    "A  Magnitude correlation",
                    0.0, 1.0,
                ),
                (
                    "qp_axis_deg", "py_axis_deg",
                    "QP axis (°)", "Python axis (°)",
                    "B  Axis angle correlation",
                    0.0, 180.0,
                ),
            ],
        ):
            x = matched[xcol].to_numpy()
            y = matched[ycol].to_numpy()
            r2, slope, intercept = _r2(x, y)
            ax.scatter(x, y, s=6, alpha=0.6, color=_BLUE, linewidths=0, rasterized=True)
            ax.plot(
                [ref_lo, ref_hi], [ref_lo, ref_hi],
                "k--", lw=0.8, label="y = x", zorder=5,
            )
            ax.set_xlim(ref_lo, ref_hi)
            ax.set_ylim(ref_lo, ref_hi)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.text(
                0.05, 0.92,
                f"R² = {r2:.3f}\nslope = {slope:.3f}",
                transform=ax.transAxes, fontsize=6, va="top",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8),
            )
            ax.legend(fontsize=6)

        fig.suptitle(
            f"QP vs Python polarity (n = {len(matched)} matched cells)",
            fontsize=8, fontweight="bold",
        )

        pdf_path = output_dir / "validation_qp_vs_python.pdf"
        png_path = output_dir / "validation_qp_vs_python.png"
        fig.savefig(pdf_path, format="pdf")
        fig.savefig(png_path, dpi=600)
        plt.close(fig)

    return pdf_path, png_path


def run_validation(
    qp_path: Path | str,
    py_path: Path | str,
    output_dir: Path | str,
    *,
    tolerance_px: float = 5.0,
) -> ValidationResult:
    """Load paired parquets, match, compute metrics, write figure + metrics.

    Args:
        qp_path: Path to qp_results.parquet.
        py_path: Path to python_results.parquet.
        output_dir: Directory for output figure files.
        tolerance_px: Max centroid distance for a valid cell match (pixels).

    Returns:
        ValidationResult with R², slope, and match counts.
    """
    qp_df = pd.read_parquet(qp_path)
    py_df = pd.read_parquet(py_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_qp_total = len(qp_df)
    n_py_total = len(py_df)
    matched = _match_cells(qp_df, py_df, tolerance_px=tolerance_px)
    n_matched = len(matched)

    if n_matched < 10:
        raise ValueError(
            f"Only {n_matched} cells matched (tolerance={tolerance_px} px). "
            "Check that centroid columns align between parquets."
        )

    r2_mag, slope_mag, intercept_mag = _r2(
        matched["qp_magnitude"].to_numpy(),
        matched["py_magnitude"].to_numpy(),
    )
    r2_ang, slope_ang, intercept_ang = _r2(
        matched["qp_axis_deg"].to_numpy(),
        matched["py_axis_deg"].to_numpy(),
    )

    result = ValidationResult(
        r2_magnitude=r2_mag,
        slope_magnitude=slope_mag,
        intercept_magnitude=intercept_mag,
        r2_angle=r2_ang,
        slope_angle=slope_ang,
        intercept_angle=intercept_ang,
        n_matched=n_matched,
        n_unmatched_qp=n_qp_total - n_matched,
        n_unmatched_py=n_py_total - n_matched,
    )

    make_figure(matched, output_dir)

    metrics_path = output_dir / "validation_metrics.json"
    import json
    metrics_path.write_text(
        json.dumps(dataclasses.asdict(result), indent=2), encoding="utf-8"
    )

    log.info(
        "validation complete",
        r2_magnitude=f"{r2_mag:.4f}",
        slope_magnitude=f"{slope_mag:.4f}",
        r2_angle=f"{r2_ang:.4f}",
        n_matched=n_matched,
    )

    return result
