"""Tests for experimental.analyses.polarity_by_condition."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantipy_polarity.experimental.analyses.polarity_by_condition import (
    run_polarity_by_condition,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_per_cell(
    tmp_path: Path, n: int = 30, conditions: list[str] | None = None
) -> tuple[Path, Path]:
    """Write synthetic per_cell.parquet + metadata.csv with *n* rows.

    Returns (per_cell_path, metadata_path).
    """
    rng = np.random.default_rng(0)
    if conditions is None:
        conditions = ["ctrl", "treat"]

    fov_ids = [f"fov{i:02d}" for i in range(n)]
    magnitudes = rng.uniform(0.1, 1.0, size=n)
    df = pd.DataFrame({"fov_id": fov_ids, "magnitude": magnitudes})
    per_cell_path = tmp_path / "per_cell.parquet"
    df.to_parquet(per_cell_path, index=False)

    # Assign conditions round-robin so all groups are represented
    cond_list = [conditions[i % len(conditions)] for i in range(n)]
    meta = pd.DataFrame({"fov_id": fov_ids, "condition": cond_list})
    metadata_path = tmp_path / "metadata.csv"
    meta.to_csv(metadata_path, index=False)

    return per_cell_path, metadata_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_two_group_produces_pdf_and_json(tmp_path):
    per_cell_path, metadata_path = _make_per_cell(tmp_path)
    run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)
    assert (tmp_path / "polarity_by_condition.pdf").exists()
    assert (tmp_path / "polarity_by_condition_results.json").exists()


def test_two_group_returns_p_value(tmp_path):
    per_cell_path, metadata_path = _make_per_cell(tmp_path)
    result = run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)
    assert "p_value" in result
    assert isinstance(result["p_value"], float)


def test_two_group_mann_whitney_test_name(tmp_path):
    per_cell_path, metadata_path = _make_per_cell(tmp_path)
    result = run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)
    assert result["test_used"] == "Mann-Whitney U"


def test_group_n_and_medians_correct(tmp_path):
    n = 30
    per_cell_path, metadata_path = _make_per_cell(tmp_path, n=n)
    result = run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)
    # n_per_group should sum to total merged cells (all fov_ids match)
    assert sum(result["n_per_group"]) == n
    # Medians should be finite floats
    for median in result["medians"]:
        assert isinstance(median, float)
        assert math.isfinite(median)


def test_three_group_no_p_value(tmp_path):
    per_cell_path, metadata_path = _make_per_cell(tmp_path, conditions=["a", "b", "c"])
    result = run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)
    assert result["p_value"] is None
    assert result["note"] is not None


def test_missing_per_cell_raises_fnf(tmp_path):
    _, metadata_path = _make_per_cell(tmp_path)
    with pytest.raises(FileNotFoundError):
        run_polarity_by_condition(
            tmp_path / "does_not_exist.parquet", metadata_path, tmp_path
        )


def test_missing_metadata_raises_fnf(tmp_path):
    per_cell_path, _ = _make_per_cell(tmp_path)
    with pytest.raises(FileNotFoundError):
        run_polarity_by_condition(per_cell_path, tmp_path / "no_metadata.csv", tmp_path)


def test_missing_magnitude_col_raises_value_error(tmp_path):
    per_cell_path, metadata_path = _make_per_cell(tmp_path)
    with pytest.raises(ValueError):
        run_polarity_by_condition(
            per_cell_path, metadata_path, tmp_path, magnitude_col="nonexistent_col"
        )


def test_missing_condition_col_raises_value_error(tmp_path):
    per_cell_path, metadata_path = _make_per_cell(tmp_path)
    with pytest.raises(ValueError):
        run_polarity_by_condition(
            per_cell_path, metadata_path, tmp_path, condition_col="no_such_condition"
        )


def test_fewer_than_two_groups_raises(tmp_path):
    """Only one condition value → ValueError."""
    rng = np.random.default_rng(1)
    fov_ids = [f"fov{i:02d}" for i in range(10)]
    df = pd.DataFrame({"fov_id": fov_ids, "magnitude": rng.uniform(0.1, 1.0, 10)})
    per_cell_path = tmp_path / "per_cell.parquet"
    df.to_parquet(per_cell_path, index=False)

    meta = pd.DataFrame({"fov_id": fov_ids, "condition": ["only_group"] * 10})
    metadata_path = tmp_path / "metadata.csv"
    meta.to_csv(metadata_path, index=False)

    with pytest.raises(ValueError):
        run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)


def test_tsv_metadata_supported(tmp_path):
    """TSV metadata file (tab-separated) is read correctly."""
    rng = np.random.default_rng(2)
    n = 20
    fov_ids = [f"fov{i:02d}" for i in range(n)]
    df = pd.DataFrame({"fov_id": fov_ids, "magnitude": rng.uniform(0.1, 1.0, n)})
    per_cell_path = tmp_path / "per_cell.parquet"
    df.to_parquet(per_cell_path, index=False)

    cond_list = ["ctrl" if i % 2 == 0 else "treat" for i in range(n)]
    meta = pd.DataFrame({"fov_id": fov_ids, "condition": cond_list})
    metadata_path = tmp_path / "metadata.tsv"
    meta.to_csv(metadata_path, sep="\t", index=False)

    result = run_polarity_by_condition(per_cell_path, metadata_path, tmp_path)
    assert set(result["groups"]) == {"ctrl", "treat"}
    assert sum(result["n_per_group"]) == n
