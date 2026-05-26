"""Tests for io/ingest.py — TIF write, uint16 dtype, atomic write, scaling, ingest_fovs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import tifffile

from quantipy_polarity.io.ingest import ingest_fovs, write_ingest_outputs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rand_membrane(h: int = 64, w: int = 64) -> np.ndarray:
    """Return a random float32 (H, W) array in [0, 1]."""
    rng = np.random.default_rng(0)
    return rng.random((h, w)).astype(np.float32)


# ---------------------------------------------------------------------------
# write_ingest_outputs tests
# ---------------------------------------------------------------------------


def test_write_ingest_outputs_creates_tif(tmp_path: Path) -> None:
    """write_ingest_outputs creates <out_dir>/01_ingest/<fov_id>_membrane.tif."""
    membrane = _rand_membrane()
    write_ingest_outputs(tmp_path, "FOV_01", membrane)
    expected = tmp_path / "01_ingest" / "FOV_01_membrane.tif"
    assert expected.exists(), f"Expected TIF not found: {expected}"
    # Validate it is a readable TIF
    data = tifffile.imread(expected)
    assert data is not None
    assert data.shape == (64, 64)


def test_write_ingest_outputs_is_uint16(tmp_path: Path) -> None:
    """Written TIF has dtype uint16."""
    membrane = _rand_membrane()
    write_ingest_outputs(tmp_path, "FOV_01", membrane)
    out_path = tmp_path / "01_ingest" / "FOV_01_membrane.tif"
    data = tifffile.imread(out_path)
    assert data.dtype == np.uint16, f"Expected uint16, got {data.dtype}"


def test_write_ingest_outputs_atomic_no_tmp_left(tmp_path: Path) -> None:
    """After writing, no .tmp.tif files remain in 01_ingest/."""
    membrane = _rand_membrane()
    write_ingest_outputs(tmp_path, "FOV_02", membrane)
    ingest_dir = tmp_path / "01_ingest"
    tmp_files = list(ingest_dir.glob("*.tmp.tif"))
    assert tmp_files == [], f"Leftover .tmp.tif files: {tmp_files}"


def test_write_ingest_outputs_scales_correctly(tmp_path: Path) -> None:
    """All-ones float32 membrane writes as max pixel = 65535."""
    membrane = np.ones((64, 64), dtype=np.float32)
    write_ingest_outputs(tmp_path, "FOV_03", membrane)
    out_path = tmp_path / "01_ingest" / "FOV_03_membrane.tif"
    data = tifffile.imread(out_path)
    assert int(data.max()) == 65535, f"Expected max=65535, got {data.max()}"


# ---------------------------------------------------------------------------
# ingest_fovs test
# ---------------------------------------------------------------------------


def test_ingest_fovs_masks_mode_returns_fov_ids(tmp_path: Path) -> None:
    """ingest_fovs with masks mode runs without error and returns a list of strings."""
    from quantipy_polarity.config import Config, InputMasks

    # Create minimal fixture directories
    membrane_dir = tmp_path / "membranes"
    masks_dir = tmp_path / "masks"
    out_dir = tmp_path / "results"
    membrane_dir.mkdir()
    masks_dir.mkdir()

    # Write paired TIFs: one FOV
    arr_f32 = _rand_membrane()
    arr_u16 = (arr_f32 * 65535).astype(np.uint16)
    tifffile.imwrite(str(membrane_dir / "FOV_01_membrane.tif"), arr_f32)
    tifffile.imwrite(str(masks_dir / "FOV_01_mask.tif"), arr_u16)

    cfg = Config(
        input=InputMasks(
            mode="masks",
            path=membrane_dir,
            masks_dir=masks_dir,
            pixel_size_um=0.325,
            channel_membrane=0,
        )
    )

    fov_ids = ingest_fovs(cfg, out_dir)

    assert isinstance(fov_ids, list), "ingest_fovs should return a list"
    assert len(fov_ids) > 0, "Expected at least one FOV ID"
    assert all(isinstance(fid, str) for fid in fov_ids), "All FOV IDs must be strings"
