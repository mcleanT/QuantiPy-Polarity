"""Deterministic synthetic validation data generator.

Used to (a) create the committed data/validation/ parquets at repo init time,
(b) regenerate them in CI for structural identity checks.

Call `generate_validation_parquets(seed=42)` to get (qp_df, py_df).
Call `write_validation_parquets(out_dir, seed=42)` to write parquets.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


_N_CELLS_PER_FOV = 50
_FOVS = ("fov_A", "fov_B")
_GRID_SPACING = 48.0  # px — 10×10 grid in 512 px image with margin
_MAG_SIGMA = 0.03
_ANG_SIGMA = 2.0  # degrees


def generate_validation_parquets(seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (qp_df, py_df) synthetic validation DataFrames.

    Deterministic at fixed seed. R² between qp_magnitude and py_magnitude ≈ 0.97.
    Angle R² ≈ 0.999 (small noise).
    """
    rng = np.random.default_rng(seed)
    qp_rows: list[dict] = []
    py_rows: list[dict] = []
    for fov_id in _FOVS:
        for i in range(_N_CELLS_PER_FOV):
            row_idx = i // 10
            col_idx = i % 10
            cy = 30.0 + row_idx * _GRID_SPACING + rng.uniform(-3, 3)
            cx = 30.0 + col_idx * _GRID_SPACING + rng.uniform(-3, 3)
            qp_mag = float(rng.uniform(0.1, 0.9))
            qp_ang = float(rng.uniform(0.0, 180.0))
            py_mag = float(np.clip(qp_mag + rng.normal(0.0, _MAG_SIGMA), 0.0, 1.0))
            raw_ang = qp_ang + rng.normal(0.0, _ANG_SIGMA)
            py_ang = float(((raw_ang % 180.0) + 180.0) % 180.0)
            cell_id = i + 1
            base = {
                "fov_id": fov_id,
                "cell_id": cell_id,
                "centroid_y": round(cy, 2),
                "centroid_x": round(cx, 2),
            }
            qp_rows.append({**base, "qp_magnitude": qp_mag, "qp_axis_deg": qp_ang})
            py_rows.append({**base, "py_magnitude": py_mag, "py_axis_deg": py_ang})

    qp_df = pd.DataFrame(qp_rows)
    py_df = pd.DataFrame(py_rows)
    return qp_df, py_df


def write_validation_parquets(out_dir: Path | str, seed: int = 42) -> None:
    """Write qp_results.parquet and python_results.parquet to out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    qp_df, py_df = generate_validation_parquets(seed=seed)
    qp_df.to_parquet(out_dir / "qp_results.parquet", index=False)
    py_df.to_parquet(out_dir / "python_results.parquet", index=False)


if __name__ == "__main__":
    import sys

    dest = sys.argv[1] if len(sys.argv) > 1 else "data/validation"
    write_validation_parquets(dest)
    print(f"Wrote validation parquets to {dest}/")
