"""Per-cell distance-to-front and migration alignment.

Lifted from:
- recompute_migration_v3.py: per-cell angle/distance pattern
- compute_48h_local_migration.py:align_wt(): magnitude-weighted alignment
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantipy_polarity.contracts import FrontResult


def _axial_diff_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Unsigned axial difference in [0, 90] degrees.

    Both inputs are axial angles (mod 180). Returns the minimum angular
    distance between them treating each angle as a headless line.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = np.mod(a - b, 180.0)
    return np.where(d > 90.0, 180.0 - d, d)


def compute_per_cell_migration(
    per_cell_df: pd.DataFrame,
    labels: np.ndarray,
    vx: np.ndarray,
    vy: np.ndarray,
    front_result: FrontResult,
) -> pd.DataFrame:
    """Add mig_dir_deg, dist_to_front_um, mig_alignment to per_cell_df rows.

    Operates on a single-FOV slice of per_cell_df (all rows must share the
    same fov_id matching front_result.fov_id).

    Parameters
    ----------
    per_cell_df : DataFrame with columns cell_id, axis_deg, magnitude.
        Must be a single-FOV slice (fov_id column must equal front_result.fov_id).
    labels : (H, W) label mask matching the FOV.
    vx, vy : (H, W) float32 displacement fields from _compute_migration_field_v6.
    front_result : FrontResult for this FOV (provides pixel_size_um).

    Returns
    -------
    Copy of per_cell_df with three columns updated:
        mig_dir_deg : angle toward front (degrees, [0, 360))
        dist_to_front_um : Euclidean distance to front (microns)
        mig_alignment : magnitude-weighted cos(2Δθ) alignment in [-1, +1]
            where Δθ = axial difference between polarity and migration direction.
    """
    df = per_cell_df.copy()
    px = front_result.pixel_size_um

    mig_dir = np.full(len(df), np.nan, dtype=float)
    dist_um = np.full(len(df), np.nan, dtype=float)

    n_front = front_result.n_front_px

    for i, row in df.iterrows():
        cid = int(row["cell_id"])
        mask = labels == cid
        if not mask.any() or n_front == 0:
            continue
        mean_vx = float(vx[mask].mean())
        mean_vy = float(vy[mask].mean())
        dist_px = float(np.hypot(mean_vx, mean_vy))
        dist_um[df.index.get_loc(i)] = dist_px * px
        # angle: +x = 0°, +y_image-up = +90° (image y-axis flipped)
        mig_dir[df.index.get_loc(i)] = float(
            np.degrees(np.arctan2(-mean_vy, mean_vx)) % 360.0
        )

    df["mig_dir_deg"] = mig_dir
    df["dist_to_front_um"] = dist_um

    # Alignment: magnitude-weighted cos(2Δθ) where Δθ is axial diff
    valid = (
        np.isfinite(mig_dir)
        & np.isfinite(df["axis_deg"].to_numpy())
        & np.isfinite(df["magnitude"].to_numpy())
    )
    if valid.sum() > 0:
        pol_deg = df["axis_deg"].to_numpy()[valid]
        mig_deg = mig_dir[valid]
        mags = df["magnitude"].to_numpy()[valid]
        # Axial: treat polarity as mod-180, migration as mod-360 → diff mod 180
        rel = _axial_diff_deg(pol_deg, mig_deg % 180.0)
        rel_rad = np.deg2rad(rel)
        # align_wt = sum(|p| * cos(2*rel)) / sum(|p|) lifted from align_wt()
        alignment = float(np.sum(mags * np.cos(2 * rel_rad)) / np.sum(mags))
    else:
        alignment = float("nan")

    df["mig_alignment"] = alignment  # scalar broadcast — same value per FOV
    return df


def compute_all_fovs(
    per_cell_df: pd.DataFrame,
    labels_by_fov: dict[str, np.ndarray],
    fields_by_fov: dict[str, tuple[np.ndarray, np.ndarray]],
    results_by_fov: dict[str, FrontResult],
) -> pd.DataFrame:
    """Run compute_per_cell_migration for each FOV and concatenate.

    Parameters
    ----------
    per_cell_df : full experiment-wide per_cell DataFrame.
    labels_by_fov : mapping fov_id -> (H, W) label mask.
    fields_by_fov : mapping fov_id -> (vx, vy) displacement arrays.
    results_by_fov : mapping fov_id -> FrontResult.

    Returns
    -------
    Full per_cell DataFrame with migration columns populated where possible.
    """
    chunks = []
    for fov_id, grp in per_cell_df.groupby("fov_id"):
        fov_id = str(fov_id)
        if fov_id not in results_by_fov:
            chunks.append(grp)
            continue
        vx, vy = fields_by_fov[fov_id]
        labels = labels_by_fov[fov_id]
        result = results_by_fov[fov_id]
        chunks.append(compute_per_cell_migration(grp, labels, vx, vy, result))
    if not chunks:
        return per_cell_df.copy()
    return pd.concat(chunks, ignore_index=True)
