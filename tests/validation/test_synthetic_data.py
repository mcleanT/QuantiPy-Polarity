"""Tests for validation/synthetic_data.py."""

import pandas as pd
from scipy.stats import pearsonr

from quantipy_polarity.validation.synthetic_data import (
    generate_validation_parquets,
    write_validation_parquets,
)


def test_schema_qp():
    qp_df, _ = generate_validation_parquets()
    assert set(
        ["fov_id", "cell_id", "centroid_y", "centroid_x", "qp_magnitude", "qp_axis_deg"]
    ).issubset(qp_df.columns)
    assert len(qp_df) == 100  # 50 cells × 2 FOVs
    assert set(qp_df["fov_id"].unique()) == {"fov_A", "fov_B"}


def test_schema_py():
    _, py_df = generate_validation_parquets()
    assert set(
        ["fov_id", "cell_id", "centroid_y", "centroid_x", "py_magnitude", "py_axis_deg"]
    ).issubset(py_df.columns)
    assert len(py_df) == 100


def test_seed_stability():
    qp1, py1 = generate_validation_parquets(seed=42)
    qp2, py2 = generate_validation_parquets(seed=42)
    pd.testing.assert_frame_equal(qp1, qp2)
    pd.testing.assert_frame_equal(py1, py2)


def test_different_seeds_differ():
    _, py1 = generate_validation_parquets(seed=42)
    _, py2 = generate_validation_parquets(seed=99)
    assert not py1["py_magnitude"].equals(py2["py_magnitude"])


def test_r2_property():
    """Merged synthetic data must have R² > 0.85 magnitude (by construction)."""
    qp_df, py_df = generate_validation_parquets()
    merged = qp_df.merge(
        py_df[["fov_id", "cell_id", "py_magnitude", "py_axis_deg"]],
        on=["fov_id", "cell_id"],
    )
    r, _ = pearsonr(merged["qp_magnitude"], merged["py_magnitude"])
    assert r**2 > 0.85, f"R² = {r**2:.4f} unexpectedly low"


def test_magnitude_range():
    qp_df, py_df = generate_validation_parquets()
    assert qp_df["qp_magnitude"].between(0.0, 1.0).all()
    assert py_df["py_magnitude"].between(0.0, 1.0).all()


def test_angle_range():
    qp_df, py_df = generate_validation_parquets()
    assert qp_df["qp_axis_deg"].between(0.0, 180.0).all()
    assert py_df["py_axis_deg"].between(0.0, 180.0).all()


def test_write_and_load(tmp_path):
    write_validation_parquets(tmp_path)
    qp = pd.read_parquet(tmp_path / "qp_results.parquet")
    py = pd.read_parquet(tmp_path / "python_results.parquet")
    assert len(qp) == 100
    assert len(py) == 100
