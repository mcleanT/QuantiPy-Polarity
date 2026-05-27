"""QP-vs-Python comparison: linear regression and figure.

Public API (primary):
    run_validation(combined_path, output_dir) -> ValidationResult

    `combined_path` is a parquet with pre-paired cells and columns:
        qp_magnitude, py_magnitude, qp_angle_deg, py_angle_deg
    (plus optional metadata columns: clone, fov, cell_identity)

    Cells are already matched — no centroid KDTree needed.

Legacy two-file API (deprecated, kept for backward compatibility):
    run_validation(qp_path, py_path, output_dir, *, tolerance_px=5.0)

    Pass a second positional argument (py_path) to trigger the old
    KDTree-matching code path on separate qp_results.parquet /
    python_results.parquet files. This path is only used by the
    synthetic-data tests; real validation always uses combined_path.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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
    n_unmatched_qp: int = 0   # always 0 for combined-format inputs
    n_unmatched_py: int = 0   # always 0 for combined-format inputs


def _r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Return (r², slope, intercept) from OLS linear regression."""
    result = linregress(x, y)
    return float(result.rvalue**2), float(result.slope), float(result.intercept)


def make_figure(
    matched: pd.DataFrame,
    output_dir: Path,
    *,
    mag_col_qp: str = "qp_magnitude",
    mag_col_py: str = "py_magnitude",
    ang_col_qp: str = "qp_angle_deg",
    ang_col_py: str = "py_angle_deg",
) -> tuple[Path, Path]:
    """Generate 2-panel validation scatter figure.

    Returns (pdf_path, png_path).
    """
    with plt.rc_context(_NATURE_RC):
        fig, axes = plt.subplots(1, 2, figsize=(7, 3.5), constrained_layout=True)

        for ax, (xcol, ycol, xlabel, ylabel, title, ref_lo, ref_hi) in zip(
            axes,
            [
                (
                    mag_col_qp,
                    mag_col_py,
                    "QP magnitude",
                    "Python magnitude",
                    "A  Magnitude correlation",
                    0.0,
                    1.0,
                ),
                (
                    ang_col_qp,
                    ang_col_py,
                    "QP axis (°)",
                    "Python axis (°)",
                    "B  Axis angle correlation",
                    -180.0,
                    180.0,
                ),
            ],
        ):
            x = matched[xcol].to_numpy()
            y = matched[ycol].to_numpy()
            r2, slope, intercept = _r2(x, y)
            ax.scatter(x, y, s=2, alpha=0.3, color=_BLUE, linewidths=0, rasterized=True)
            # identity line
            ax.plot(
                [ref_lo, ref_hi],
                [ref_lo, ref_hi],
                "k--",
                lw=0.8,
                label="y = x",
                zorder=5,
            )
            # best-fit line
            x_line = np.array([ref_lo, ref_hi])
            ax.plot(
                x_line,
                slope * x_line + intercept,
                color=_ORANGE,
                lw=0.8,
                label=f"fit (slope {slope:.2f})",
                zorder=6,
            )
            ax.set_xlim(ref_lo, ref_hi)
            ax.set_ylim(ref_lo, ref_hi)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.text(
                0.05,
                0.92,
                f"R² = {r2:.3f}\nslope = {slope:.3f}",
                transform=ax.transAxes,
                fontsize=6,
                va="top",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8),
            )
            ax.legend(fontsize=6)

        n = len(matched)
        fig.suptitle(
            f"QP vs Python polarity  (n = {n:,} cells)",
            fontsize=8,
            fontweight="bold",
        )

        pdf_path = output_dir / "validation_qp_vs_python.pdf"
        png_path = output_dir / "validation_qp_vs_python.png"
        fig.savefig(pdf_path, format="pdf")
        fig.savefig(png_path, dpi=600)
        plt.close(fig)

    return pdf_path, png_path


# ---------------------------------------------------------------------------
# Legacy KDTree-matching path (two-file format)
# ---------------------------------------------------------------------------

def _match_cells(
    qp_df: pd.DataFrame,
    py_df: pd.DataFrame,
    tolerance_px: float = 5.0,
) -> pd.DataFrame:
    """Nearest-neighbour match cells per FOV.

    Returns a DataFrame with columns:
        fov_id, cell_id_qp, cell_id_py,
        qp_magnitude, qp_axis_deg, py_magnitude, py_axis_deg

    .. deprecated::
        The combined-parquet API (run_validation with a single path) is preferred.
        This function is kept for tests that use synthetic_data.py fixtures.
    """
    from scipy.spatial import KDTree

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
            rows.append(
                {
                    "fov_id": fov_id,
                    "cell_id_qp": int(qp_fov.at[qp_i, "cell_id"]),
                    "cell_id_py": int(py_fov.at[int(py_i), "cell_id"]),
                    "qp_magnitude": float(qp_fov.at[qp_i, "qp_magnitude"]),
                    "qp_axis_deg": float(qp_fov.at[qp_i, "qp_axis_deg"]),
                    "py_magnitude": float(py_fov.at[int(py_i), "py_magnitude"]),
                    "py_axis_deg": float(py_fov.at[int(py_i), "py_axis_deg"]),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Primary API
# ---------------------------------------------------------------------------

def run_validation(
    combined_path: Path | str,
    output_dir_or_py_path: Path | str,
    output_dir: Optional[Path | str] = None,
    *,
    tolerance_px: float = 5.0,
) -> ValidationResult:
    """Load paired data, compute metrics, write figure + metrics JSON.

    Primary signature (combined parquet):
        run_validation(combined_path, output_dir) -> ValidationResult

        combined_path must be a parquet with columns:
            qp_magnitude, py_magnitude, qp_angle_deg, py_angle_deg

    Legacy signature (two separate files, deprecated):
        run_validation(qp_path, py_path, output_dir, *, tolerance_px=5.0)

        Uses KDTree centroid matching per FOV. Only needed for synthetic-data
        test fixtures; real validation always uses the combined format.

    Returns:
        ValidationResult with R², slope, and cell counts.
    """
    combined_path = Path(combined_path)

    # --- detect which calling convention was used ---
    if output_dir is None:
        # New primary API: run_validation(combined_path, output_dir)
        real_output_dir = Path(output_dir_or_py_path)
        real_output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_parquet(combined_path)
        df = df.dropna(subset=["qp_magnitude", "py_magnitude", "qp_angle_deg", "py_angle_deg"])

        if len(df) < 10:
            raise ValueError(
                f"Only {len(df)} valid cells in combined parquet. "
                "Check that qp_magnitude / py_magnitude / qp_angle_deg / py_angle_deg columns exist."
            )

        r2_mag, slope_mag, intercept_mag = _r2(
            df["qp_magnitude"].to_numpy(),
            df["py_magnitude"].to_numpy(),
        )
        r2_ang, slope_ang, intercept_ang = _r2(
            df["qp_angle_deg"].to_numpy(),
            df["py_angle_deg"].to_numpy(),
        )

        result = ValidationResult(
            r2_magnitude=r2_mag,
            slope_magnitude=slope_mag,
            intercept_magnitude=intercept_mag,
            r2_angle=r2_ang,
            slope_angle=slope_ang,
            intercept_angle=intercept_ang,
            n_matched=len(df),
            n_unmatched_qp=0,
            n_unmatched_py=0,
        )

        make_figure(df, real_output_dir)

    else:
        # Legacy two-file API: run_validation(qp_path, py_path, output_dir, ...)
        py_path = Path(output_dir_or_py_path)
        real_output_dir = Path(output_dir)
        real_output_dir.mkdir(parents=True, exist_ok=True)

        qp_df = pd.read_parquet(combined_path)   # here combined_path is actually qp_path
        py_df = pd.read_parquet(py_path)

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

        make_figure(
            matched,
            real_output_dir,
            mag_col_qp="qp_magnitude",
            mag_col_py="py_magnitude",
            ang_col_qp="qp_axis_deg",
            ang_col_py="py_axis_deg",
        )

    metrics_path = real_output_dir / "validation_metrics.json"
    metrics_path.write_text(
        json.dumps(dataclasses.asdict(result), indent=2), encoding="utf-8"
    )

    log.info(
        "validation complete",
        r2_magnitude=f"{r2_mag:.4f}",
        slope_magnitude=f"{slope_mag:.4f}",
        r2_angle=f"{r2_ang:.4f}",
        n_matched=result.n_matched,
    )

    return result
