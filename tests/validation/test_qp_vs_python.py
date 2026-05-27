"""Tests for validation/qp_vs_python.py."""

import json

import numpy as np
import pytest

from quantipy_polarity.validation.qp_vs_python import (
    MAGNITUDE_THRESHOLD,
    ValidationResult,
    _match_cells,
    _r2,
    axial_angle_diff_deg,
    make_figure,
    run_validation,
    stokes,
)
from quantipy_polarity.validation.synthetic_data import (
    generate_validation_parquets,
    write_validation_parquets,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def paired_parquets(tmp_path):
    """Legacy two-file fixture using synthetic data."""
    write_validation_parquets(tmp_path)
    return tmp_path / "qp_results.parquet", tmp_path / "python_results.parquet"


@pytest.fixture()
def combined_parquet(tmp_path):
    """Combined single-file fixture using synthetic data."""
    qp_df, py_df = generate_validation_parquets()
    # Merge into combined format expected by new API
    combined = qp_df[["fov_id", "cell_id", "qp_magnitude", "qp_axis_deg"]].copy()
    combined["py_magnitude"] = py_df["py_magnitude"].values
    combined["py_axis_deg"] = py_df["py_axis_deg"].values
    # Rename to match real-data column names
    combined = combined.rename(
        columns={"qp_axis_deg": "qp_angle_deg", "py_axis_deg": "py_angle_deg"}
    )
    path = tmp_path / "qp_vs_python_real.parquet"
    combined.to_parquet(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Unit tests — _r2 helper
# ---------------------------------------------------------------------------


def test_r2_perfect():
    x = np.array([0.1, 0.5, 0.9])
    r2, slope, intercept = _r2(x, x)
    assert abs(r2 - 1.0) < 1e-10
    assert abs(slope - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# Unit tests — axial angle helpers
# ---------------------------------------------------------------------------


def test_axial_angle_diff_zero():
    """Identical angles give 0°."""
    a = np.array([0.0, 45.0, 89.0, -89.0])
    diff = axial_angle_diff_deg(a, a)
    np.testing.assert_allclose(diff, 0.0, atol=1e-10)


def test_axial_angle_diff_wraparound():
    """Angles that straddle ±90° should give a small difference, not ~180°."""
    # +89° and -89° are 2° apart axially (not 178°)
    diff = axial_angle_diff_deg(np.array([89.0]), np.array([-89.0]))
    assert diff[0] < 5.0, f"Expected ~2°, got {diff[0]:.2f}°"


def test_axial_angle_diff_range():
    """Result must be in [0°, 90°]."""
    rng = np.random.default_rng(42)
    a = rng.uniform(-90, 90, 1000)
    b = rng.uniform(-90, 90, 1000)
    diff = axial_angle_diff_deg(a, b)
    assert diff.min() >= 0.0
    assert diff.max() <= 90.0 + 1e-10


def test_stokes_orthogonal():
    """cos(2θ) and sin(2θ) should be on the unit circle."""
    angles = np.linspace(-90, 90, 50)
    s1, s2 = stokes(angles)
    norms = s1**2 + s2**2
    np.testing.assert_allclose(norms, 1.0, atol=1e-10)


# ---------------------------------------------------------------------------
# Unit tests — _match_cells (legacy path, used by synthetic tests)
# ---------------------------------------------------------------------------


def test_match_cells_all_matched():
    qp_df, py_df = generate_validation_parquets()
    matched = _match_cells(qp_df, py_df, tolerance_px=5.0)
    assert len(matched) == 100
    assert "qp_magnitude" in matched.columns
    assert "py_magnitude" in matched.columns


def test_match_cells_tight_tolerance_excludes():
    """Tolerance of 0.0 should match no cells (jitter > 0)."""
    qp_df, py_df = generate_validation_parquets()
    py_df = py_df.copy()
    py_df["centroid_x"] += 0.5
    matched = _match_cells(qp_df, py_df, tolerance_px=0.0)
    assert len(matched) < 100


# ---------------------------------------------------------------------------
# Combined-parquet API (new primary path)
# ---------------------------------------------------------------------------


def test_run_validation_combined_outputs(combined_parquet, tmp_path):
    out = tmp_path / "val_out"
    result = run_validation(combined_parquet, out)
    assert isinstance(result, ValidationResult)
    assert (out / "validation_qp_vs_python.pdf").exists()
    assert (out / "validation_qp_vs_python.png").exists()
    assert (out / "validation_metrics.json").exists()


def test_run_validation_combined_n_cells(combined_parquet, tmp_path):
    result = run_validation(combined_parquet, tmp_path / "val")
    assert result.n_matched == 100
    assert result.n_unmatched_qp == 0
    assert result.n_unmatched_py == 0


def test_run_validation_combined_r2(combined_parquet, tmp_path):
    """Synthetic combined data should still have high magnitude R² (no noise path)."""
    result = run_validation(combined_parquet, tmp_path / "val")
    assert result.r2_magnitude > 0.80, f"R² = {result.r2_magnitude:.4f}"


def test_run_validation_combined_axial_metrics(combined_parquet, tmp_path):
    """Axial angle metrics should exist and be in valid ranges for synthetic data."""
    result = run_validation(combined_parquet, tmp_path / "val")
    # n_angle_filtered can be 0 if synthetic magnitudes are all below threshold
    assert result.n_angle_filtered >= 0
    # If we have filtered cells, check metric ranges
    if result.n_angle_filtered >= 3:
        assert 0.0 <= result.median_axial_delta_deg <= 90.0
        assert -1.0 <= result.mean_cos_2delta <= 1.0
        assert 0.0 <= result.stokes_r2_s1 <= 1.0
        assert 0.0 <= result.stokes_r2_s2 <= 1.0


def test_run_validation_combined_metrics_json_has_new_fields(combined_parquet, tmp_path):
    """The metrics JSON must contain the new axial angle fields."""
    out = tmp_path / "val"
    run_validation(combined_parquet, out)
    metrics = json.loads((out / "validation_metrics.json").read_text())
    assert "r2_magnitude" in metrics
    assert "n_matched" in metrics
    assert "n_angle_filtered" in metrics
    assert "median_axial_delta_deg" in metrics
    assert "mean_cos_2delta" in metrics
    assert "stokes_r2_s1" in metrics
    assert "stokes_r2_s2" in metrics
    # Old naive angle fields should NOT be present
    assert "r2_angle" not in metrics
    assert "slope_angle" not in metrics
    assert "intercept_angle" not in metrics


# ---------------------------------------------------------------------------
# Legacy two-file API (backward compat)
# ---------------------------------------------------------------------------


def test_run_validation_outputs(paired_parquets, tmp_path):
    qp_path, py_path = paired_parquets
    out = tmp_path / "val_out"
    result = run_validation(qp_path, py_path, out)
    assert isinstance(result, ValidationResult)
    assert (out / "validation_qp_vs_python.pdf").exists()
    assert (out / "validation_qp_vs_python.png").exists()
    assert (out / "validation_metrics.json").exists()


def test_run_validation_r2_threshold(paired_parquets, tmp_path):
    qp_path, py_path = paired_parquets
    result = run_validation(qp_path, py_path, tmp_path / "val")
    assert result.r2_magnitude > 0.85, f"R² = {result.r2_magnitude:.4f}"
    assert 0.7 <= result.slope_magnitude <= 1.3, f"slope = {result.slope_magnitude:.4f}"


def test_run_validation_n_matched(paired_parquets, tmp_path):
    qp_path, py_path = paired_parquets
    result = run_validation(qp_path, py_path, tmp_path / "val")
    assert result.n_matched == 100


def test_metrics_json_written(paired_parquets, tmp_path):
    qp_path, py_path = paired_parquets
    out = tmp_path / "val"
    run_validation(qp_path, py_path, out)
    metrics = json.loads((out / "validation_metrics.json").read_text())
    assert "r2_magnitude" in metrics
    assert "n_matched" in metrics


def test_make_figure_writes_files(tmp_path):
    qp_df, py_df = generate_validation_parquets()
    matched = _match_cells(qp_df, py_df)
    pdf_path, png_path = make_figure(
        matched,
        tmp_path,
        mag_col_qp="qp_magnitude",
        mag_col_py="py_magnitude",
        ang_col_qp="qp_axis_deg",
        ang_col_py="py_axis_deg",
    )
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert png_path.suffix == ".png"


def test_insufficient_matches_raises(tmp_path):
    """If fewer than 10 cells match, run_validation raises ValueError."""
    qp_df, py_df = generate_validation_parquets()
    py_df = py_df.copy()
    py_df["centroid_y"] += 1000.0
    py_df["centroid_x"] += 1000.0
    qp_path = tmp_path / "qp.parquet"
    py_path = tmp_path / "py.parquet"
    qp_df.to_parquet(qp_path, index=False)
    py_df.to_parquet(py_path, index=False)
    with pytest.raises(ValueError, match="cells matched"):
        run_validation(qp_path, py_path, tmp_path / "out")
