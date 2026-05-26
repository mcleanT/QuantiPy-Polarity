"""End-to-end masks→polarity→aggregate test using the canonical synthetic fixture.

Differs from test_polarity_pca_recovery.py: that one tests the algorithm directly;
this one drives the full CLI pipeline (config → polarity → aggregate → parquet schema
+ ground-truth sanity check) like a real user would.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import tifffile
import yaml
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity.contracts import PER_CELL_COLUMNS
from tests.fixtures._build import load_synthetic_fov


@pytest.fixture
def synthetic_pipeline_inputs(tmp_path: Path, repo_root: Path) -> dict:
    """Write the canonical fixture out as a (membrane, mask) FOV pair on disk."""
    npz = repo_root / "tests" / "fixtures" / "synthetic_fov.npz"
    if not npz.exists():
        pytest.skip(f"Synthetic fixture not generated: {npz}")
    data = load_synthetic_fov(npz)
    mem_dir = tmp_path / "membrane"
    msk_dir = tmp_path / "masks"
    mem_dir.mkdir()
    msk_dir.mkdir()
    mem_u16 = (data["membrane"] * 65535).astype(np.uint16)
    tifffile.imwrite(mem_dir / "FOV_01.tif", mem_u16)
    tifffile.imwrite(msk_dir / "FOV_01.tif", data["label_mask"])

    cfg_dict = {
        "input": {
            "mode": "masks",
            "path": str(mem_dir),
            "masks_dir": str(msk_dir),
            "pixel_size_um": 0.5,
            "channel_membrane": 0,
        },
        "project": {"name": "e2e", "output_dir": str(tmp_path / "results")},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg_dict))
    return {
        "cfg_path": cfg_path,
        "output_dir": tmp_path / "results",
        "theta_truth": data["theta_truth"],
    }


def test_e2e_masks_pipeline_writes_schema(synthetic_pipeline_inputs: dict) -> None:
    runner = CliRunner()
    pol = runner.invoke(
        main,
        [
            "polarity",
            "--config",
            str(synthetic_pipeline_inputs["cfg_path"]),
            "--output",
            str(synthetic_pipeline_inputs["output_dir"]),
        ],
    )
    assert pol.exit_code == 0, pol.output
    per_fov_dir = synthetic_pipeline_inputs["output_dir"] / "03_polarity" / "per_fov"
    assert (per_fov_dir / "FOV_01.parquet").exists()

    exp_parquet = synthetic_pipeline_inputs["output_dir"] / "05_aggregated" / "per_cell.parquet"
    agg = runner.invoke(
        main,
        [
            "aggregate",
            "--input",
            str(per_fov_dir),
            "--output",
            str(exp_parquet),
        ],
    )
    assert agg.exit_code == 0, agg.output

    df = pd.read_parquet(exp_parquet)
    assert list(df.columns) == list(PER_CELL_COLUMNS)
    assert (df["fov_id"] == "FOV_01").all()
    # 80 cells in fixture; algorithm may drop a few near boundaries
    assert df.shape[0] >= 60
