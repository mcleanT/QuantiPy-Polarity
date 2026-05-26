"""Per-cell aggregation: turn per-FOV polarity results into the experiment-wide parquet.

Two operations:
  - `per_fov_to_parquet`: take the output of compute_cell_polarity for one FOV,
    rename QP-style columns to contracts schema, add fov_id and per-cell geometry,
    project to PER_CELL_COLUMNS, write atomically to disk.
  - `aggregate_experiment`: concatenate per-FOV parquets into one experiment-wide parquet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from quantipy_polarity.contracts import PER_CELL_COLUMNS


# QP-style column names emitted by compute_cell_polarity -> canonical contract names
_RENAME_MAP: dict[str, str] = {
    "Cell Identity": "cell_id",
    "PCA Magnitude": "magnitude",
    "PCA Angle (°)": "axis_deg",
}


def _normalize_polarity_result(result, fov_id: str) -> pd.DataFrame:
    """Turn the compute_cell_polarity DataFrame into a DataFrame with contracts column names.

    Accepts either a DataFrame with QP-style names or a DataFrame already using the
    contracts names (in case a caller has pre-renamed). Also accepts a list of dicts.
    """
    if isinstance(result, pd.DataFrame):
        df = result.copy()
    else:
        df = pd.DataFrame.from_records(list(result))
    df = df.rename(columns=_RENAME_MAP)
    df["fov_id"] = fov_id
    if "axis_deg" in df.columns:
        df["axis_deg"] = df["axis_deg"].astype(float) % 360.0
    return df


def per_fov_to_parquet(
    polarity_result,
    fov_id: str,
    label_mask: np.ndarray,
    out_path: Path,
    *,
    condition: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Write one FOV's per-cell polarity to a parquet matching PER_CELL_COLUMNS schema.

    Computes per-cell centroid + area from the label mask. Migration columns
    (mig_*) are left null in v0.1.0 — populated by Phase 4.
    """
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        raise FileExistsError(f"{out_path} exists; pass overwrite=True to replace")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = _normalize_polarity_result(polarity_result, fov_id)
    if "cell_id" not in df.columns:
        raise ValueError(f"{fov_id}: polarity result missing 'cell_id' column")
    if "magnitude" not in df.columns:
        raise ValueError(f"{fov_id}: polarity result missing 'magnitude' column")

    # Compute centroids + area per cell from label_mask
    cell_ids = df["cell_id"].astype(int).to_numpy()
    centroids_y = []
    centroids_x = []
    areas = []
    for cid in cell_ids:
        coords = np.argwhere(label_mask == cid)
        if coords.size == 0:
            centroids_y.append(np.nan)
            centroids_x.append(np.nan)
            areas.append(0)
            continue
        centroids_y.append(float(coords[:, 0].mean()))
        centroids_x.append(float(coords[:, 1].mean()))
        areas.append(int(coords.shape[0]))
    df["centroid_y"] = centroids_y
    df["centroid_x"] = centroids_x
    df["area_px"] = areas

    if "qc_flags" not in df.columns:
        df["qc_flags"] = 0

    df["condition"] = condition
    df["mig_dir_deg"] = np.nan
    df["mig_alignment"] = np.nan
    df["dist_to_front_um"] = np.nan

    # Project to canonical column order
    df = df[list(PER_CELL_COLUMNS)]
    # Atomic write: temp file + rename
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    df.to_parquet(tmp_path, index=False)
    tmp_path.replace(out_path)
    return out_path


def aggregate_experiment(
    per_fov_parquets: Iterable[Path], out_path: Path, *, overwrite: bool = False
) -> Path:
    """Concatenate per-FOV parquets into one experiment-wide parquet."""
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        raise FileExistsError(f"{out_path} exists; pass overwrite=True to replace")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    frames = [pd.read_parquet(p) for p in per_fov_parquets]
    if not frames:
        raise ValueError("aggregate_experiment: no input parquets provided")
    df = pd.concat(frames, ignore_index=True)
    df = df[list(PER_CELL_COLUMNS)]
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    df.to_parquet(tmp_path, index=False)
    tmp_path.replace(out_path)
    return out_path
