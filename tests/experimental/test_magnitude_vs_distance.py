"""Tests for experimental.analyses.magnitude_vs_distance."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantipy_polarity.experimental.analyses.magnitude_vs_distance import (
    run_magnitude_vs_distance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parquet(
    tmp_path: Path,
    n: int = 50,
    include_distance: bool = True,
    magnitude_col: str = "qp_magnitude",
    distance_col: str = "dist_to_front_px",
) -> Path:
    """Write a synthetic per_cell.parquet and return its path."""
    rng = np.random.default_rng(42)
    data: dict = {magnitude_col: rng.uniform(0.1, 1.0, n)}
    if include_distance:
        data[distance_col] = rng.uniform(0.0, 200.0, n)
    df = pd.DataFrame(data)
    path = tmp_path / "per_cell.parquet"
    df.to_parquet(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_with_distance_col_produces_pdf_and_json(tmp_path):
    per_cell_path = _make_parquet(tmp_path)
    run_magnitude_vs_distance(per_cell_path, tmp_path)
    assert (tmp_path / "magnitude_vs_distance.pdf").exists()
    assert (tmp_path / "magnitude_vs_distance_results.json").exists()


def test_returns_slope_and_r_squared(tmp_path):
    per_cell_path = _make_parquet(tmp_path)
    result = run_magnitude_vs_distance(per_cell_path, tmp_path)
    assert isinstance(result["slope"], float)
    assert isinstance(result["r_squared"], float)


def test_missing_distance_col_returns_gracefully(tmp_path):
    """When distance_col is absent, function returns without raising."""
    per_cell_path = _make_parquet(tmp_path, include_distance=False)
    result = run_magnitude_vs_distance(per_cell_path, tmp_path)
    assert result["distance_col_found"] is False
    assert not (tmp_path / "magnitude_vs_distance.pdf").exists()


def test_missing_distance_col_writes_json(tmp_path):
    """JSON results file is still written when distance col is absent."""
    per_cell_path = _make_parquet(tmp_path, include_distance=False)
    run_magnitude_vs_distance(per_cell_path, tmp_path)
    assert (tmp_path / "magnitude_vs_distance_results.json").exists()


def test_missing_per_cell_raises_fnf(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_magnitude_vs_distance(tmp_path / "does_not_exist.parquet", tmp_path)


def test_missing_magnitude_col_raises_value_error(tmp_path):
    per_cell_path = _make_parquet(tmp_path)
    with pytest.raises(ValueError):
        run_magnitude_vs_distance(
            per_cell_path, tmp_path, magnitude_col="no_such_magnitude"
        )


def test_max_cells_subsample(tmp_path):
    """With max_cells=5, a 100-row parquet results in n_cells <= 5."""
    per_cell_path = _make_parquet(tmp_path, n=100)
    result = run_magnitude_vs_distance(per_cell_path, tmp_path, max_cells=5)
    assert result["n_cells"] <= 5


def test_r_squared_range(tmp_path):
    """r_squared is between 0.0 and 1.0 inclusive."""
    per_cell_path = _make_parquet(tmp_path)
    result = run_magnitude_vs_distance(per_cell_path, tmp_path)
    assert 0.0 <= result["r_squared"] <= 1.0
