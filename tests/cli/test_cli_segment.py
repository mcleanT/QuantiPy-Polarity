"""CLI tests for quantipy segment.

Fast-tier tests: reject masks-mode input; help text presence; config parsing.
Nightly-gated tests: real TIF → Cellpose → on-disk masks roundtrip.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import tifffile
from click.testing import CliRunner

from quantipy_polarity.cli import main
from tests.fixtures._build import write_synthetic_tif_stack


# ---------------------------------------------------------------------------
# Fast-tier tests (no cellpose invocation)
# ---------------------------------------------------------------------------


def _write_masks_config(tmp_path: Path) -> Path:
    cfg_text = f"""
project:
  name: test
  output_dir: {tmp_path / "results"}
input:
  mode: masks
  path: {tmp_path / "masks"}
  masks_dir: {tmp_path / "masks_dir"}
  pixel_size_um: 0.65
"""
    p = tmp_path / "config.yaml"
    p.write_text(cfg_text.strip())
    return p


def _write_tif_config(tmp_path: Path, input_path: Path) -> Path:
    cfg_text = f"""
project:
  name: test
  output_dir: {tmp_path / "results"}
input:
  mode: tif
  path: {input_path}
  channel_membrane: 0
  channel_segmentation: 1
  pixel_size_um: 0.65
  tif_scheme: stack
"""
    p = tmp_path / "config.yaml"
    p.write_text(cfg_text.strip())
    return p


def test_segment_cmd_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["segment", "--help"])
    assert result.exit_code == 0
    assert "Cellpose-SAM" in result.output or "segment" in result.output.lower()


def test_segment_cmd_rejects_masks_mode(tmp_path: Path) -> None:
    """quantipy segment should fail cleanly when mode=masks."""
    cfg_path = _write_masks_config(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["segment", "--config", str(cfg_path)])
    assert result.exit_code != 0
    assert "masks" in result.output.lower() or "polarity" in result.output.lower()


def test_segment_cmd_config_missing_file() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["segment", "--config", "/nonexistent/config.yaml"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Nightly-gated test: full TIF → Cellpose → on-disk masks
# ---------------------------------------------------------------------------

cellpose = pytest.importorskip(
    "cellpose", reason="cellpose not installed; nightly-tier test only"
)


def test_segment_cmd_tif_to_masks_e2e(tmp_path: Path) -> None:
    """Full smoke: synthetic TIF → quantipy segment → validates mask output files."""
    input_dir = tmp_path / "input"
    for fov_name in ("FOV_01", "FOV_02"):
        write_synthetic_tif_stack(input_dir, fov_name, n_cells=20, image_size=128)

    cfg_path = _write_tif_config(tmp_path, input_dir)
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["segment", "--config", str(cfg_path), "--output", str(tmp_path / "results")],
    )
    assert result.exit_code == 0, f"CLI failed:\n{result.output}"

    seg_dir = tmp_path / "results" / "02_segmentation"
    assert seg_dir.exists(), "02_segmentation/ was not created"

    for fov_name in ("FOV_01", "FOV_02"):
        mask_path = seg_dir / f"{fov_name}_mask.tif"
        mem_path = seg_dir / f"{fov_name}_membrane.tif"
        assert mask_path.exists(), f"Missing mask: {mask_path}"
        assert mem_path.exists(), f"Missing membrane: {mem_path}"

        mask = tifffile.imread(str(mask_path))
        assert mask.dtype == np.uint16, f"Mask not uint16: {mask.dtype}"
        assert mask.shape == (128, 128), f"Mask shape wrong: {mask.shape}"
        n_cells = int(mask.max())
        assert n_cells >= 5, f"Suspiciously few cells ({n_cells}) for FOV {fov_name}"

    status_path = seg_dir / "_stage_status.json"
    assert status_path.exists()
    import json

    status = json.loads(status_path.read_text())
    assert status["status"] == "complete"
