"""Tests for `quantipy polarity` and `quantipy aggregate` end-to-end."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import tifffile
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config, InputMasks, ProjectConfig
from quantipy_polarity.contracts import PER_CELL_COLUMNS


def _write_mask_fov_dir(tmp_path: Path, fov_id: str = "FOV_01") -> tuple[Path, Path]:
    """Create one paired (membrane, mask) FOV under tmp_path; return (mem_dir, mask_dir)."""
    mdir = tmp_path / "membrane"
    mskdir = tmp_path / "masks"
    mdir.mkdir(exist_ok=True)
    mskdir.mkdir(exist_ok=True)
    msk = np.zeros((48, 48), dtype=np.uint16)
    msk[8:24, 8:24] = 1
    msk[28:44, 28:44] = 2
    mem = np.zeros_like(msk, dtype=np.uint16)
    mem[8:24, 8:24] = 30000
    mem[28:44, 28:44] = 30000
    tifffile.imwrite(mdir / f"{fov_id}.tif", mem)
    tifffile.imwrite(mskdir / f"{fov_id}.tif", msk)
    return mdir, mskdir


def _write_config(tmp_path: Path, mem_dir: Path, mask_dir: Path) -> Path:
    cfg = Config(
        project=ProjectConfig(name="test", output_dir=tmp_path / "results"),
        input=InputMasks(
            mode="masks",
            path=mem_dir,
            masks_dir=mask_dir,
            pixel_size_um=0.5,
            channel_membrane=0,
        ),
    )
    cfg_path = tmp_path / "config.yaml"
    cfg.to_yaml(cfg_path)
    return cfg_path


def test_polarity_command_produces_per_fov_parquet(tmp_path: Path) -> None:
    mem_dir, mask_dir = _write_mask_fov_dir(tmp_path, "FOV_01")
    cfg_path = _write_config(tmp_path, mem_dir, mask_dir)
    output = tmp_path / "results"
    runner = CliRunner()
    result = runner.invoke(main, ["polarity", "--config", str(cfg_path), "--output", str(output)])
    assert result.exit_code == 0, result.output
    out_parquet = output / "03_polarity" / "per_fov" / "FOV_01.parquet"
    assert out_parquet.exists()
    df = pd.read_parquet(out_parquet)
    assert list(df.columns) == list(PER_CELL_COLUMNS)
    assert (df["fov_id"] == "FOV_01").all()
    assert df.shape[0] == 2


def test_polarity_rejects_non_masks_mode(tmp_path: Path) -> None:
    cfg_data = {
        "input": {
            "mode": "nd2",
            "path": str(tmp_path / "raw"),
            "channel_membrane": 0,
            "channel_segmentation": 0,
            "pixel_size_um": 0.5,
        }
    }
    import yaml
    cfg_path = tmp_path / "c.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg_data))
    runner = CliRunner()
    result = runner.invoke(main, ["polarity", "--config", str(cfg_path), "--output", str(tmp_path / "out")])
    assert result.exit_code != 0
    assert "input.mode='masks'" in result.output or "only supports" in result.output


def test_aggregate_command_concatenates(tmp_path: Path) -> None:
    mem_dir, mask_dir = _write_mask_fov_dir(tmp_path, "FOV_01")
    _write_mask_fov_dir(tmp_path, "FOV_02")
    cfg_path = _write_config(tmp_path, mem_dir, mask_dir)
    output = tmp_path / "results"
    runner = CliRunner()
    pol_result = runner.invoke(main, ["polarity", "--config", str(cfg_path), "--output", str(output)])
    assert pol_result.exit_code == 0, pol_result.output

    agg_out = output / "05_aggregated" / "per_cell.parquet"
    agg_result = runner.invoke(
        main,
        [
            "aggregate",
            "--input",
            str(output / "03_polarity" / "per_fov"),
            "--output",
            str(agg_out),
        ],
    )
    assert agg_result.exit_code == 0, agg_result.output
    assert agg_out.exists()
    df = pd.read_parquet(agg_out)
    assert df.shape[0] == 4
    assert set(df["fov_id"].unique()) == {"FOV_01", "FOV_02"}


def test_aggregate_no_input_files(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    runner = CliRunner()
    result = runner.invoke(
        main, ["aggregate", "--input", str(tmp_path / "empty"), "--output", str(tmp_path / "x.parquet")]
    )
    assert result.exit_code != 0
    assert "No *.parquet" in result.output
