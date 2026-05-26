"""Tests for the `quantipy plot` CLI command."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from click.testing import CliRunner

from quantipy_polarity.cli import main
from tests.fixtures._build import build_synthetic_fov


def _write_pipeline_outputs(tmp: Path, n_fovs: int = 2, size: int = 64) -> dict:
    """Write a minimal completed-pipeline layout for quantipy plot tests."""
    seg_dir = tmp / "02_segmentation"
    seg_dir.mkdir(parents=True)
    agg_dir = tmp / "05_aggregated"
    agg_dir.mkdir(parents=True)

    rows = []
    for i in range(1, n_fovs + 1):
        fov_id = f"FOV_{i:02d}"
        data = build_synthetic_fov(n_cells=8, image_size=size, seed=i * 13)
        tifffile.imwrite(str(seg_dir / f"{fov_id}_mask.tif"), data["label_mask"])
        mem_u16 = (data["membrane"] * 65535).clip(0, 65535).astype(np.uint16)
        tifffile.imwrite(str(seg_dir / f"{fov_id}_membrane.tif"), mem_u16)
        for cid, ang in data["theta_truth"].items():
            if cid not in data["centroids"]:
                continue
            cy, cx = data["centroids"][cid]
            rows.append(
                {
                    "fov_id": fov_id,
                    "cell_id": cid,
                    "centroid_y": cy,
                    "centroid_x": cx,
                    "axis_deg": ang,
                    "magnitude": float(
                        np.random.default_rng(cid + i).uniform(0.2, 0.9)
                    ),
                    "area_px": 200,
                    "qc_flags": 0,
                    "dist_to_front_um": float("nan"),
                    "mig_dir_deg": float("nan"),
                    "mig_alignment": float("nan"),
                }
            )
    df = pd.DataFrame(rows)
    df.to_parquet(agg_dir / "per_cell.parquet", index=False)
    return {"seg_dir": seg_dir, "agg_dir": agg_dir, "per_cell": df}


def _write_config(tmp: Path) -> Path:
    cfg_text = (
        "project:\n  name: test\n  output_dir: ./results\n"
        "input:\n  mode: masks\n  path: ./input\n"
        "  masks_dir: ./input\n  pixel_size_um: 0.65\n"
        "  membrane_channel: 0\n"
        "polarity:\n  method: boundary_pca\n  axial: true\n"
        "  weight: magnitude\n  exclude_edge_cells: false\n"
        "viz:\n  rose_bins: 12\n  vector_scale: 1.0\n"
        "  per_fov_maps: true\n  overlay_dpi: 150\n"
    )
    cfg = tmp / "config.yaml"
    cfg.write_text(cfg_text)
    return cfg


def test_plot_writes_summary_pdf() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _write_pipeline_outputs(tmp, n_fovs=2, size=64)
        cfg = _write_config(tmp)
        result = runner.invoke(
            main,
            [
                "plot",
                "--config",
                str(cfg),
                "--output",
                str(tmp),
            ],
        )
        assert result.exit_code == 0, result.output
        summary_pdf = tmp / "06_plots" / "population_summary.pdf"
        assert summary_pdf.exists()
        assert summary_pdf.read_bytes()[:4] == b"%PDF"


def test_plot_writes_rose_plots() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _write_pipeline_outputs(tmp, n_fovs=2, size=64)
        cfg = _write_config(tmp)
        result = runner.invoke(
            main,
            [
                "plot",
                "--config",
                str(cfg),
                "--output",
                str(tmp),
            ],
        )
        assert result.exit_code == 0, result.output
        roses = list((tmp / "06_plots" / "roses").glob("*.pdf"))
        assert len(roses) >= 2  # one per FOV + aggregate


def test_plot_writes_vector_maps() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _write_pipeline_outputs(tmp, n_fovs=2, size=64)
        cfg = _write_config(tmp)
        result = runner.invoke(
            main,
            [
                "plot",
                "--config",
                str(cfg),
                "--output",
                str(tmp),
            ],
        )
        assert result.exit_code == 0, result.output
        maps = list((tmp / "06_plots" / "vector_maps").glob("*.png"))
        assert len(maps) >= 2


def test_plot_missing_per_cell_raises_error() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cfg = _write_config(tmp)
        tmp.mkdir(exist_ok=True)
        result = runner.invoke(
            main,
            [
                "plot",
                "--config",
                str(cfg),
                "--output",
                str(tmp),
            ],
        )
        assert result.exit_code != 0
