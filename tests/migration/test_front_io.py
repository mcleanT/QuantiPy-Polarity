"""Tests for migration/front_io.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from quantipy_polarity.contracts import FrontResult
from quantipy_polarity.migration.front_io import read_front_parquet, write_front_parquet


def _make_results() -> list[FrontResult]:
    return [
        FrontResult(
            fov_id="FOV_01",
            front_y_um=45.5,
            front_angle_deg=87.3,
            n_front_px=320,
            front_mask_shape=(128, 128),
            pixel_size_um=0.65,
        ),
        FrontResult(
            fov_id="FOV_02",
            front_y_um=None,
            front_angle_deg=None,
            n_front_px=0,
            front_mask_shape=(128, 128),
            pixel_size_um=0.65,
        ),
    ]


def test_write_creates_parquet_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "front_um_per_fov.parquet"
        write_front_parquet(_make_results(), out)
        assert out.exists()
        assert out.stat().st_size > 0


def test_roundtrip_preserves_values() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "front.parquet"
        write_front_parquet(_make_results(), out)
        df = read_front_parquet(out)
        assert list(df["fov_id"]) == ["FOV_01", "FOV_02"]
        assert abs(df.loc[0, "front_y_um"] - 45.5) < 1e-6
        assert df.loc[1, "n_front_px"] == 0
        assert pd.isna(df.loc[1, "front_y_um"])


def test_write_is_atomic_no_partial_file_on_error() -> None:
    """write_front_parquet cleans up temp file if serialisation fails."""
    import unittest.mock as mock

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "front.parquet"
        with mock.patch(
            "pandas.DataFrame.to_parquet", side_effect=RuntimeError("disk full")
        ):
            with pytest.raises(RuntimeError, match="disk full"):
                write_front_parquet(_make_results(), out)
        # Output file must not exist after failed write
        assert not out.exists()
        # No leftover temp file
        assert len(list(Path(td).glob(".front_tmp_*"))) == 0


def test_read_validates_required_columns() -> None:
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.parquet"
        pd.DataFrame({"fov_id": ["FOV_01"]}).to_parquet(bad, index=False)
        with pytest.raises(ValueError, match="missing columns"):
            read_front_parquet(bad)


def test_empty_results_writes_zero_row_parquet() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "empty.parquet"
        write_front_parquet([], out)
        df = read_front_parquet(out)
        assert len(df) == 0
