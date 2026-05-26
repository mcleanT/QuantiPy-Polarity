"""Unit tests for polarity/per_cell.py."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantipy_polarity.contracts import PER_CELL_COLUMNS
from quantipy_polarity.polarity.per_cell import aggregate_experiment, per_fov_to_parquet


def _toy_label_mask() -> np.ndarray:
    msk = np.zeros((40, 40), dtype=np.uint16)
    msk[5:15, 5:15] = 1
    msk[20:30, 20:30] = 2
    return msk


def _toy_polarity_result_qp_style() -> pd.DataFrame:
    """Mimic what compute_cell_polarity returns: QP-style column names."""
    return pd.DataFrame(
        {
            "Cell Identity": [1, 2],
            "PCA Angle (°)": [45.0, 120.0],
            "PCA Magnitude": [0.3, 0.5],
            "n_boundary_px": [40, 40],
            "intensity_sum": [1.0, 2.0],
        }
    )


def _toy_polarity_result_contracts_style() -> pd.DataFrame:
    """Alternative input shape: already using contracts column names."""
    return pd.DataFrame(
        {
            "cell_id": [1, 2],
            "axis_deg": [45.0, 120.0],
            "magnitude": [0.3, 0.5],
        }
    )


def test_per_fov_to_parquet_renames_qp_columns(tmp_path: Path) -> None:
    out = tmp_path / "fov_01.parquet"
    per_fov_to_parquet(
        _toy_polarity_result_qp_style(),
        fov_id="FOV_01",
        label_mask=_toy_label_mask(),
        out_path=out,
    )
    df = pd.read_parquet(out)
    assert list(df.columns) == list(PER_CELL_COLUMNS)
    assert (df["fov_id"] == "FOV_01").all()
    assert df["cell_id"].tolist() == [1, 2]
    assert df["axis_deg"].tolist() == [45.0, 120.0]
    assert df["magnitude"].tolist() == [0.3, 0.5]
    # Computed from label mask
    assert df["area_px"].tolist() == [100, 100]
    assert df["mig_dir_deg"].isna().all()


def test_per_fov_to_parquet_accepts_contracts_style(tmp_path: Path) -> None:
    out = tmp_path / "fov_02.parquet"
    per_fov_to_parquet(
        _toy_polarity_result_contracts_style(),
        fov_id="FOV_02",
        label_mask=_toy_label_mask(),
        out_path=out,
    )
    df = pd.read_parquet(out)
    assert list(df.columns) == list(PER_CELL_COLUMNS)
    assert df.shape[0] == 2


def test_per_fov_to_parquet_refuses_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "fov_01.parquet"
    out.write_bytes(b"placeholder")
    with pytest.raises(FileExistsError):
        per_fov_to_parquet(
            _toy_polarity_result_qp_style(),
            fov_id="FOV_01",
            label_mask=_toy_label_mask(),
            out_path=out,
        )


def test_per_fov_to_parquet_overwrite_ok(tmp_path: Path) -> None:
    out = tmp_path / "fov_01.parquet"
    out.write_bytes(b"placeholder")
    per_fov_to_parquet(
        _toy_polarity_result_qp_style(),
        fov_id="FOV_01",
        label_mask=_toy_label_mask(),
        out_path=out,
        overwrite=True,
    )
    assert pd.read_parquet(out).shape[0] == 2


def test_per_fov_atomic_write_no_tmp_left(tmp_path: Path) -> None:
    out = tmp_path / "fov_01.parquet"
    per_fov_to_parquet(
        _toy_polarity_result_qp_style(),
        fov_id="FOV_01",
        label_mask=_toy_label_mask(),
        out_path=out,
    )
    assert not (tmp_path / "fov_01.parquet.tmp").exists()


def test_aggregate_concats_in_order(tmp_path: Path) -> None:
    paths = []
    for fov in ("FOV_01", "FOV_02"):
        p = tmp_path / f"{fov}.parquet"
        per_fov_to_parquet(
            _toy_polarity_result_qp_style(),
            fov_id=fov,
            label_mask=_toy_label_mask(),
            out_path=p,
        )
        paths.append(p)
    out = tmp_path / "experiment.parquet"
    aggregate_experiment(paths, out)
    agg = pd.read_parquet(out)
    assert agg.shape[0] == 4
    assert set(agg["fov_id"].unique()) == {"FOV_01", "FOV_02"}
    assert list(agg.columns) == list(PER_CELL_COLUMNS)


def test_aggregate_empty_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no input parquets"):
        aggregate_experiment([], tmp_path / "x.parquet")
