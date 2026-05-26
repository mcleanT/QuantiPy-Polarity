"""Tests for migration/distance.py."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantipy_polarity.contracts import FrontResult
from quantipy_polarity.migration.distance import (
    _axial_diff_deg,
    compute_per_cell_migration,
    compute_all_fovs,
)


def _synthetic_df(n: int = 5, fov_id: str = "FOV_01") -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "fov_id": fov_id,
            "cell_id": list(range(1, n + 1)),
            "axis_deg": rng.uniform(0, 180, n).tolist(),
            "magnitude": rng.uniform(0.1, 1.0, n).tolist(),
            "centroid_y": rng.uniform(10, 50, n).tolist(),
            "centroid_x": rng.uniform(10, 50, n).tolist(),
            "area_px": [200] * n,
            "qc_flags": [0] * n,
        }
    )


def _tiny_labels(n: int = 5, size: int = 64) -> np.ndarray:
    labels = np.zeros((size, size), dtype=np.uint16)
    step = size // (n + 1)
    for cid in range(1, n + 1):
        cy, cx = step * cid, step * cid
        labels[cy - 4 : cy + 4, cx - 4 : cx + 4] = cid
    return labels


def test_axial_diff_deg_same_angle_is_zero() -> None:
    a = np.array([45.0, 90.0, 135.0])
    assert np.allclose(_axial_diff_deg(a, a), 0.0)


def test_axial_diff_deg_orthogonal_is_90() -> None:
    assert abs(_axial_diff_deg(np.array([0.0]), np.array([90.0]))[0] - 90.0) < 1e-9


def test_axial_diff_deg_antiparallel_is_zero() -> None:
    # 0° and 180° are the same axial direction
    assert abs(_axial_diff_deg(np.array([0.0]), np.array([180.0]))[0]) < 1e-9


def test_compute_per_cell_migration_adds_columns() -> None:
    size = 64
    labels = _tiny_labels(5, size)
    vx = np.ones((size, size), np.float32) * 5.0
    vy = np.zeros((size, size), np.float32)
    result = FrontResult(
        fov_id="FOV_01",
        front_y_um=20.0,
        front_angle_deg=0.0,
        n_front_px=100,
        front_mask_shape=(size, size),
        pixel_size_um=0.65,
    )
    df = _synthetic_df(5)
    out = compute_per_cell_migration(df, labels, vx, vy, result)
    assert "mig_dir_deg" in out.columns
    assert "dist_to_front_um" in out.columns
    assert "mig_alignment" in out.columns


def test_compute_per_cell_migration_no_front_gives_nans() -> None:
    size = 64
    labels = _tiny_labels(5, size)
    vx = np.zeros((size, size), np.float32)
    vy = np.zeros((size, size), np.float32)
    result = FrontResult(
        fov_id="FOV_01",
        front_y_um=None,
        front_angle_deg=None,
        n_front_px=0,
        front_mask_shape=(size, size),
        pixel_size_um=0.65,
    )
    df = _synthetic_df(5)
    out = compute_per_cell_migration(df, labels, vx, vy, result)
    assert out["dist_to_front_um"].isna().all()


def test_compute_all_fovs_concatenates_correctly() -> None:
    size = 64
    labels = _tiny_labels(5, size)
    vx = np.ones((size, size), np.float32)
    vy = np.zeros((size, size), np.float32)
    r = FrontResult(
        fov_id="FOV_01",
        front_y_um=20.0,
        front_angle_deg=0.0,
        n_front_px=50,
        front_mask_shape=(size, size),
        pixel_size_um=0.65,
    )
    df1 = _synthetic_df(5, "FOV_01")
    df2 = _synthetic_df(3, "FOV_02")
    full = pd.concat([df1, df2], ignore_index=True)
    out = compute_all_fovs(
        full,
        labels_by_fov={"FOV_01": labels},
        fields_by_fov={"FOV_01": (vx, vy)},
        results_by_fov={"FOV_01": r},
    )
    assert len(out) == 8
    # FOV_02 rows have no FrontResult → pass through unchanged
    fov2 = out[out["fov_id"] == "FOV_02"]
    assert fov2["dist_to_front_um"].isna().all()
