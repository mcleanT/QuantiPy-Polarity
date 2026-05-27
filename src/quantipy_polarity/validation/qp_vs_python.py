"""QP-vs-Python comparison: axial angle metrics and figure.

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

Angle methodology
-----------------
Polarity axes are AXIAL — defined modulo 180°, not 360°. A naive Pearson R²
on raw angle values is the wrong metric because cells near the ±90° boundary
alias: a cell at +89° and one at -89° are 2° apart physically but look 178°
apart in raw angle space. Two corrections are applied:

1. **Axial Δθ** (axial_angle_diff_deg): computes |((a - b + 90) % 180) − 90|,
   which is symmetric and lives in [0°, 90°].

2. **Stokes-space R²**: map angles to the Stokes S₁ = cos(2θ) and S₂ = sin(2θ)
   components (the standard representation for axial/orientation data), then
   compute Pearson R² on each component separately.

3. **Magnitude filter**: cells with near-zero polarity magnitude have physically
   meaningless axis angles. Only cells with both qp_magnitude > MAGNITUDE_THRESHOLD
   AND py_magnitude > MAGNITUDE_THRESHOLD are included in the angle metrics.

Reference: Mardia & Jupp, "Directional Statistics" (Wiley, 2000).
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

#: Cells with magnitude below this threshold have physically meaningless angles.
#: Both qp_magnitude AND py_magnitude must exceed this for a cell to enter the
#: axial angle metrics.
MAGNITUDE_THRESHOLD = 0.05

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
_BLUE_LIGHT = "#A8C4EB"   # lighter blue for "all cells" histogram bars


@dataclasses.dataclass(frozen=True)
class ValidationResult:
    """Metrics from a QP-vs-Python paired comparison.

    Magnitude fields
    ----------------
    r2_magnitude, slope_magnitude, intercept_magnitude : float
        OLS regression of py_magnitude ~ qp_magnitude on all cells.

    Angle fields (axial, magnitude-filtered)
    -----------------------------------------
    n_angle_filtered : int
        Number of cells with both qp_magnitude > MAGNITUDE_THRESHOLD and
        py_magnitude > MAGNITUDE_THRESHOLD (used for all angle metrics).
    median_axial_delta_deg : float
        Median of |((qp_angle − py_angle + 90) % 180) − 90| in degrees.
        Range [0°, 90°].
    mean_cos_2delta : float
        Mean of cos(2 * axial_Δθ), where axial_Δθ is in radians.
        Range [−1, 1]; values near 1 indicate excellent agreement.
    stokes_r2_s1 : float
        Pearson R² of cos(2·qp_angle) vs cos(2·py_angle) on filtered cells.
    stokes_r2_s2 : float
        Pearson R² of sin(2·qp_angle) vs sin(2·py_angle) on filtered cells.

    Legacy count fields
    -------------------
    n_matched : int
        Total number of matched cells (all cells, before magnitude filter).
    n_unmatched_qp, n_unmatched_py : int
        Always 0 for combined-format inputs; non-zero only for legacy two-file path.
    """

    r2_magnitude: float
    slope_magnitude: float
    intercept_magnitude: float
    n_matched: int
    n_angle_filtered: int
    median_axial_delta_deg: float
    mean_cos_2delta: float
    stokes_r2_s1: float
    stokes_r2_s2: float
    n_unmatched_qp: int = 0  # always 0 for combined-format inputs
    n_unmatched_py: int = 0  # always 0 for combined-format inputs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Return (r², slope, intercept) from OLS linear regression."""
    result = linregress(x, y)
    return float(result.rvalue**2), float(result.slope), float(result.intercept)


def axial_angle_diff_deg(a_deg: np.ndarray, b_deg: np.ndarray) -> np.ndarray:
    """Axial angular difference in degrees, symmetric and in [0°, 90°].

    Handles the mod-180° wraparound correctly so that e.g. +89° and -89°
    give Δθ = 2° instead of 178°.
    """
    diff = np.abs(((a_deg - b_deg) + 90) % 180 - 90)
    return diff


def stokes(angle_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert axial angles (degrees) to Stokes S₁, S₂ components.

    S₁ = cos(2θ), S₂ = sin(2θ)  (standard representation for axial data).
    """
    theta = np.deg2rad(2 * angle_deg)
    return np.cos(theta), np.sin(theta)


def _angle_metrics(
    qp_ang: np.ndarray,
    py_ang: np.ndarray,
    qp_mag: np.ndarray,
    py_mag: np.ndarray,
    threshold: float = MAGNITUDE_THRESHOLD,
) -> tuple[int, float, float, float, float]:
    """Compute axial angle metrics on magnitude-filtered cells.

    Returns
    -------
    n_filtered : int
    median_axial_delta_deg : float
    mean_cos_2delta : float
    stokes_r2_s1 : float
    stokes_r2_s2 : float
    """
    mask = (qp_mag > threshold) & (py_mag > threshold)
    n_filtered = int(mask.sum())

    if n_filtered < 3:
        # Not enough cells to compute meaningful metrics
        return n_filtered, float("nan"), float("nan"), float("nan"), float("nan")

    qa = qp_ang[mask]
    pa = py_ang[mask]

    delta_deg = axial_angle_diff_deg(qa, pa)
    median_delta = float(np.median(delta_deg))

    # cos(2 * delta) where delta is in radians — alignment metric in [-1, 1]
    delta_rad = np.deg2rad(delta_deg)
    mean_cos2 = float(np.mean(np.cos(2 * delta_rad)))

    # Stokes-space R²
    qs1, qs2 = stokes(qa)
    ps1, ps2 = stokes(pa)
    r2_s1, _, _ = _r2(qs1, ps1)
    r2_s2, _, _ = _r2(qs2, ps2)

    return n_filtered, median_delta, mean_cos2, r2_s1, r2_s2


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------


def make_figure(
    matched: pd.DataFrame,
    output_dir: Path,
    *,
    mag_col_qp: str = "qp_magnitude",
    mag_col_py: str = "py_magnitude",
    ang_col_qp: str = "qp_angle_deg",
    ang_col_py: str = "py_angle_deg",
) -> tuple[Path, Path]:
    """Generate 2-panel validation figure.

    Panel A — magnitude scatter (QP vs Python), unchanged from v0.1.3.
    Panel B — axial Δθ histogram with all-cells and magnitude-filtered overlays.

    Returns (pdf_path, png_path).
    """
    qp_mag = matched[mag_col_qp].to_numpy()
    py_mag = matched[mag_col_py].to_numpy()
    qp_ang = matched[ang_col_qp].to_numpy()
    py_ang = matched[ang_col_py].to_numpy()

    n_total = len(matched)

    # Magnitude panel stats
    r2_mag, slope_mag, _ = _r2(qp_mag, py_mag)

    # Angle metrics — all cells
    delta_all = axial_angle_diff_deg(qp_ang, py_ang)
    median_all = float(np.median(delta_all))

    # Angle metrics — magnitude-filtered
    mag_mask = (qp_mag > MAGNITUDE_THRESHOLD) & (py_mag > MAGNITUDE_THRESHOLD)
    n_filtered = int(mag_mask.sum())
    delta_filtered = axial_angle_diff_deg(qp_ang[mag_mask], py_ang[mag_mask])
    median_filtered = float(np.median(delta_filtered)) if n_filtered > 0 else float("nan")

    with plt.rc_context(_NATURE_RC):
        fig, axes = plt.subplots(1, 2, figsize=(7, 3.5), constrained_layout=True)

        # ------------------------------------------------------------------
        # Panel A — magnitude scatter
        # ------------------------------------------------------------------
        ax_mag = axes[0]
        ax_mag.scatter(
            qp_mag, py_mag,
            s=2, alpha=0.3, color=_BLUE, linewidths=0, rasterized=True,
        )
        ax_mag.plot([0, 1], [0, 1], "k--", lw=0.8, label="y = x", zorder=5)
        x_line = np.array([0.0, 1.0])
        slope_full, intercept_full = linregress(qp_mag, py_mag)[0:2]
        ax_mag.plot(
            x_line, slope_full * x_line + intercept_full,
            color=_ORANGE, lw=0.8, label=f"fit (slope {slope_full:.2f})", zorder=6,
        )
        ax_mag.set_xlim(0, 1)
        ax_mag.set_ylim(0, 1)
        ax_mag.set_xlabel("QP magnitude")
        ax_mag.set_ylabel("Python magnitude")
        ax_mag.set_title("A  Magnitude correlation")
        ax_mag.text(
            0.05, 0.92,
            f"R² = {r2_mag:.3f}\nslope = {slope_full:.3f}",
            transform=ax_mag.transAxes,
            fontsize=6, va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8),
        )
        ax_mag.legend(fontsize=6)

        # ------------------------------------------------------------------
        # Panel B — axial Δθ histogram
        # ------------------------------------------------------------------
        ax_ang = axes[1]
        bins = np.linspace(0, 90, 37)  # 2.5° bins

        # All cells (light bars)
        ax_ang.hist(
            delta_all, bins=bins,
            color=_BLUE_LIGHT, edgecolor="none", alpha=0.7,
            label=f"All cells (n={n_total:,})",
        )
        # Magnitude-filtered cells (darker bars)
        ax_ang.hist(
            delta_filtered, bins=bins,
            color=_BLUE, edgecolor="none", alpha=0.85,
            label=f"mag > {MAGNITUDE_THRESHOLD} (n={n_filtered:,})",
        )

        # Annotate medians
        y_max = ax_ang.get_ylim()[1]
        ax_ang.axvline(median_all, color=_BLUE_LIGHT, lw=1.2, ls="--")
        ax_ang.axvline(median_filtered, color=_BLUE, lw=1.2, ls="--")

        ax_ang.text(
            median_all + 1.0, 0.92,
            f"median {median_all:.1f}°",
            transform=ax_ang.get_xaxis_transform(),
            fontsize=6, color=_BLUE_LIGHT, va="top",
        )
        ax_ang.text(
            median_filtered + 1.0, 0.82,
            f"median {median_filtered:.1f}°\n(mag-filtered)",
            transform=ax_ang.get_xaxis_transform(),
            fontsize=6, color=_BLUE, va="top",
        )

        ax_ang.set_xlabel("Axial Δθ (°)")
        ax_ang.set_ylabel("Cell count")
        ax_ang.set_xlim(0, 90)
        ax_ang.set_title("B  Axis angle agreement (axial Δθ)")
        ax_ang.legend(fontsize=6, loc="upper right")

        # ------------------------------------------------------------------
        # Supertitle
        # ------------------------------------------------------------------
        fig.suptitle(
            f"QP vs Python polarity  (n = {n_total:,} cells total)",
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
    """Load paired data, compute axial angle metrics, write figure + metrics JSON.

    Primary signature (combined parquet):
        run_validation(combined_path, output_dir) -> ValidationResult

        combined_path must be a parquet with columns:
            qp_magnitude, py_magnitude, qp_angle_deg, py_angle_deg

    Legacy signature (two separate files, deprecated):
        run_validation(qp_path, py_path, output_dir, *, tolerance_px=5.0)

        Uses KDTree centroid matching per FOV. Only needed for synthetic-data
        test fixtures; real validation always uses the combined format.

    Angle metrics
    -------------
    Axis angles are AXIAL (defined mod 180°). Naive Pearson R² on raw angles
    is incorrect because cells near ±90° alias spuriously. The returned
    ValidationResult contains:
      - median_axial_delta_deg : robust axial agreement (lower is better)
      - mean_cos_2delta        : Stokes alignment score near 1 = excellent
      - stokes_r2_s1/s2       : R² on cos(2θ) / sin(2θ) components
    All angle metrics are computed only on cells where both qp_magnitude and
    py_magnitude exceed MAGNITUDE_THRESHOLD (= {threshold}).

    Returns:
        ValidationResult with magnitude R², axial angle metrics, and cell counts.
    """.format(threshold=MAGNITUDE_THRESHOLD)
    combined_path = Path(combined_path)

    # --- detect which calling convention was used ---
    if output_dir is None:
        # New primary API: run_validation(combined_path, output_dir)
        real_output_dir = Path(output_dir_or_py_path)
        real_output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_parquet(combined_path)
        df = df.dropna(
            subset=["qp_magnitude", "py_magnitude", "qp_angle_deg", "py_angle_deg"]
        )

        if len(df) < 10:
            raise ValueError(
                f"Only {len(df)} valid cells in combined parquet. "
                "Check that qp_magnitude / py_magnitude / qp_angle_deg / py_angle_deg columns exist."
            )

        r2_mag, slope_mag, intercept_mag = _r2(
            df["qp_magnitude"].to_numpy(),
            df["py_magnitude"].to_numpy(),
        )

        n_filtered, median_delta, mean_cos2, r2_s1, r2_s2 = _angle_metrics(
            df["qp_angle_deg"].to_numpy(),
            df["py_angle_deg"].to_numpy(),
            df["qp_magnitude"].to_numpy(),
            df["py_magnitude"].to_numpy(),
        )

        result = ValidationResult(
            r2_magnitude=r2_mag,
            slope_magnitude=slope_mag,
            intercept_magnitude=intercept_mag,
            n_matched=len(df),
            n_angle_filtered=n_filtered,
            median_axial_delta_deg=median_delta,
            mean_cos_2delta=mean_cos2,
            stokes_r2_s1=r2_s1,
            stokes_r2_s2=r2_s2,
            n_unmatched_qp=0,
            n_unmatched_py=0,
        )

        make_figure(df, real_output_dir)

    else:
        # Legacy two-file API: run_validation(qp_path, py_path, output_dir, ...)
        py_path = Path(output_dir_or_py_path)
        real_output_dir = Path(output_dir)
        real_output_dir.mkdir(parents=True, exist_ok=True)

        qp_df = pd.read_parquet(combined_path)  # here combined_path is actually qp_path
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

        n_filtered, median_delta, mean_cos2, r2_s1, r2_s2 = _angle_metrics(
            matched["qp_axis_deg"].to_numpy(),
            matched["py_axis_deg"].to_numpy(),
            matched["qp_magnitude"].to_numpy(),
            matched["py_magnitude"].to_numpy(),
        )

        result = ValidationResult(
            r2_magnitude=r2_mag,
            slope_magnitude=slope_mag,
            intercept_magnitude=intercept_mag,
            n_matched=n_matched,
            n_angle_filtered=n_filtered,
            median_axial_delta_deg=median_delta,
            mean_cos_2delta=mean_cos2,
            stokes_r2_s1=r2_s1,
            stokes_r2_s2=r2_s2,
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
        r2_magnitude=f"{result.r2_magnitude:.4f}",
        slope_magnitude=f"{result.slope_magnitude:.4f}",
        n_matched=result.n_matched,
        n_angle_filtered=result.n_angle_filtered,
        median_axial_delta_deg=f"{result.median_axial_delta_deg:.2f}",
        mean_cos_2delta=f"{result.mean_cos_2delta:.4f}",
        stokes_r2_s1=f"{result.stokes_r2_s1:.4f}",
    )

    return result
