"""Tests for the `quantipy front` CLI command."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import tifffile
from click.testing import CliRunner

from quantipy_polarity.cli import main
from tests.fixtures._build import build_synthetic_fov


def _write_seg_dir(tmp: Path, n_fovs: int = 2, size: int = 64) -> Path:
    """Write synthetic mask TIFs into a 02_segmentation/ layout."""
    seg = tmp / "02_segmentation"
    seg.mkdir(parents=True)
    for i in range(1, n_fovs + 1):
        fov_id = f"FOV_{i:02d}"
        data = build_synthetic_fov(n_cells=10, image_size=size, seed=i * 7)
        tifffile.imwrite(str(seg / f"{fov_id}_mask.tif"), data["label_mask"])
        mem_u16 = (data["membrane"] * 65535).clip(0, 65535).astype(np.uint16)
        tifffile.imwrite(str(seg / f"{fov_id}_membrane.tif"), mem_u16)
    return seg


def _write_config(tmp: Path) -> Path:
    cfg_text = (
        "project:\n  name: test\n  output_dir: ./results\n"
        "input:\n  mode: masks\n  path: ./input\n"
        "  masks_dir: ./input\n  pixel_size_um: 0.65\n"
        "  membrane_channel: 0\n"
        "polarity:\n  method: boundary_pca\n  axial: true\n"
        "  weight: magnitude\n  exclude_edge_cells: false\n"
    )
    cfg = tmp / "config.yaml"
    cfg.write_text(cfg_text)
    return cfg


def test_front_writes_parquet() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _write_seg_dir(tmp, n_fovs=2, size=64)
        cfg = _write_config(tmp)
        out = tmp / "results"
        result = runner.invoke(main, [
            "front",
            "--config", str(cfg),
            "--input", str(tmp),
            "--output", str(out),
        ])
        assert result.exit_code == 0, result.output
        parquet = out / "04_migration" / "front_um_per_fov.parquet"
        assert parquet.exists()
        df = pd.read_parquet(parquet)
        assert set(df["fov_id"]) == {"FOV_01", "FOV_02"}
        assert "front_y_um" in df.columns
        assert "n_front_px" in df.columns


def test_front_qc_flag_writes_overlay_pngs() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _write_seg_dir(tmp, n_fovs=1, size=64)
        cfg = _write_config(tmp)
        out = tmp / "results"
        result = runner.invoke(main, [
            "front", "--config", str(cfg),
            "--input", str(tmp), "--output", str(out), "--qc",
        ])
        assert result.exit_code == 0, result.output
        qc_dir = out / "04_migration" / "qc"
        pngs = list(qc_dir.glob("*.png"))
        assert len(pngs) >= 1
        assert pngs[0].read_bytes()[:4] == b"\x89PNG"


def test_front_updates_per_cell_when_present() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _write_seg_dir(tmp, n_fovs=1, size=64)
        cfg = _write_config(tmp)
        out = tmp / "results"
        # Pre-write a per_cell.parquet with NaN migration columns
        agg_dir = out / "05_aggregated"
        agg_dir.mkdir(parents=True)
        data = build_synthetic_fov(n_cells=10, image_size=64, seed=7)
        cell_ids = sorted(data["theta_truth"].keys())
        n = len(cell_ids)
        centroids = data["centroids"]
        pc = pd.DataFrame({
            "fov_id": ["FOV_01"] * n,
            "cell_id": cell_ids,
            "axis_deg": [float(data["theta_truth"][c]) for c in cell_ids],
            "magnitude": [0.5] * n,
            "centroid_y": [float(centroids[c][0]) if c in centroids else 32.0 for c in cell_ids],
            "centroid_x": [float(centroids[c][1]) if c in centroids else 32.0 for c in cell_ids],
            "area_px": [200] * n,
            "qc_flags": [0] * n,
            "dist_to_front_um": [float("nan")] * n,
            "mig_dir_deg": [float("nan")] * n,
            "mig_alignment": [float("nan")] * n,
        })
        pc.to_parquet(agg_dir / "per_cell.parquet", index=False)
        result = runner.invoke(main, [
            "front", "--config", str(cfg),
            "--input", str(tmp), "--output", str(out),
        ])
        assert result.exit_code == 0, result.output
        updated = pd.read_parquet(agg_dir / "per_cell.parquet")
        assert "dist_to_front_um" in updated.columns
        assert "mig_dir_deg" in updated.columns


def test_front_no_mask_files_raises_error() -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cfg = _write_config(tmp)
        empty_in = tmp / "empty_seg"
        empty_in.mkdir()
        out = tmp / "results"
        result = runner.invoke(main, [
            "front", "--config", str(cfg),
            "--input", str(empty_in), "--output", str(out),
        ])
        assert result.exit_code != 0
