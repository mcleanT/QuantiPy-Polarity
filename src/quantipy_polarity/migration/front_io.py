"""Read/write front_um_per_fov.parquet.

Schema (SemVer-stable in v0.1.0):
    fov_id          str
    front_y_um      float64  (nullable — None when no front detected)
    front_angle_deg float64  (nullable)
    n_front_px      int64
    pixel_size_um   float64
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Sequence

import pandas as pd

from quantipy_polarity.contracts import FrontResult

_COLUMNS: tuple[str, ...] = (
    "fov_id",
    "front_y_um",
    "front_angle_deg",
    "n_front_px",
    "pixel_size_um",
)


def write_front_parquet(
    results: Sequence[FrontResult],
    out_path: Path,
) -> Path:
    """Serialise a list of FrontResult objects to Parquet (atomic write).

    Parameters
    ----------
    results : sequence of FrontResult, one per FOV.
    out_path : destination .parquet file path (parent dir must exist).

    Returns
    -------
    Resolved absolute path of the written file.
    """
    out_path = Path(out_path).resolve()
    rows = [
        {
            "fov_id": r.fov_id,
            "front_y_um": r.front_y_um,
            "front_angle_deg": r.front_angle_deg,
            "n_front_px": r.n_front_px,
            "pixel_size_um": r.pixel_size_um,
        }
        for r in results
    ]
    df = pd.DataFrame(rows, columns=list(_COLUMNS))
    df["n_front_px"] = df["n_front_px"].astype("int64")
    df["pixel_size_um"] = df["pixel_size_um"].astype("float64")

    fd, tmp = tempfile.mkstemp(
        dir=out_path.parent, prefix=".front_tmp_", suffix=".parquet"
    )
    os.close(fd)
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, out_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return out_path


def read_front_parquet(path: Path) -> pd.DataFrame:
    """Read front_um_per_fov.parquet into a DataFrame.

    Validates that expected columns are present.

    Parameters
    ----------
    path : path to the .parquet file written by write_front_parquet.

    Returns
    -------
    DataFrame with columns from _COLUMNS.

    Raises
    ------
    ValueError if any required column is missing.
    """
    path = Path(path)
    df = pd.read_parquet(path)
    missing = [c for c in _COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"front parquet at {path} is missing columns: {missing}")
    return df[list(_COLUMNS)]
