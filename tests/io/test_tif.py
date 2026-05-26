"""Tests for io/tif.py — TIF ingest with stack and multifile schemes."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import tifffile

from quantipy_polarity.io.tif import (
    TIFFOV,
    _extract_channels_stack,
    _normalize_channel,
    iter_tif_dataset,
    load_tif_fov_multifile,
    load_tif_fov_stack,
)
from tests.fixtures._build import write_synthetic_tif_stack, write_synthetic_tif_multifile


# ---------------------------------------------------------------------------
# _normalize_channel
# ---------------------------------------------------------------------------

def test_normalize_uint16_max() -> None:
    arr = np.array([[65535]], dtype=np.uint16)
    out = _normalize_channel(arr)
    assert out.dtype == np.float32
    assert np.isclose(out[0, 0], 1.0)


def test_normalize_uint16_zero() -> None:
    arr = np.zeros((4, 4), dtype=np.uint16)
    out = _normalize_channel(arr)
    assert out.min() == 0.0 and out.max() == 0.0


def test_normalize_float32_passthrough() -> None:
    arr = np.array([[0.5]], dtype=np.float32)
    out = _normalize_channel(arr)
    assert out.dtype == np.float32
    assert np.isclose(out[0, 0], 0.5)


# ---------------------------------------------------------------------------
# _extract_channels_stack
# ---------------------------------------------------------------------------

def test_extract_channels_stack_chw() -> None:
    """(C, H, W) layout: first axis is channels."""
    arr = np.zeros((3, 64, 64), dtype=np.uint16)
    arr[1] = 1000  # channel 1 = membrane
    mem, nuc = _extract_channels_stack(arr, channel_membrane=1, channel_segmentation=0, fov_id="T")
    assert mem.shape == (64, 64)
    assert mem[0, 0] == 1000
    assert nuc is not None and nuc.shape == (64, 64)


def test_extract_channels_stack_hwc() -> None:
    """(H, W, C) layout: last axis is channels when first axis > 8."""
    arr = np.zeros((64, 64, 3), dtype=np.uint16)
    arr[..., 2] = 2000  # channel 2 = membrane
    mem, nuc = _extract_channels_stack(arr, channel_membrane=2, channel_segmentation=None, fov_id="T")
    assert mem.shape == (64, 64)
    assert mem[0, 0] == 2000
    assert nuc is None


def test_extract_channels_stack_out_of_range() -> None:
    arr = np.zeros((2, 64, 64), dtype=np.uint16)
    with pytest.raises(IndexError, match="channel_membrane=5"):
        _extract_channels_stack(arr, 5, None, "T")


# ---------------------------------------------------------------------------
# load_tif_fov_stack
# ---------------------------------------------------------------------------

def test_load_tif_fov_stack_roundtrip(tmp_path: Path) -> None:
    data = write_synthetic_tif_stack(tmp_path, "FOV_01", n_cells=10, image_size=64)
    fov = load_tif_fov_stack(
        tmp_path / "FOV_01.tif",
        fov_id="FOV_01",
        channel_membrane=0,
        channel_segmentation=1,
        pixel_size_um=0.65,
    )
    assert isinstance(fov, TIFFOV)
    assert fov.fov_id == "FOV_01"
    assert fov.membrane.shape == (64, 64)
    assert fov.membrane.dtype == np.float32
    assert 0.0 <= fov.membrane.min() and fov.membrane.max() <= 1.0
    assert fov.nuclear is not None
    assert fov.nuclear.shape == (64, 64)
    assert fov.pixel_size_um == 0.65


def test_load_tif_fov_stack_no_nuclear(tmp_path: Path) -> None:
    data = write_synthetic_tif_stack(tmp_path, "FOV_01", n_cells=10, image_size=64)
    fov = load_tif_fov_stack(
        tmp_path / "FOV_01.tif",
        fov_id="FOV_01",
        channel_membrane=0,
        channel_segmentation=None,
        pixel_size_um=0.65,
    )
    assert fov.nuclear is None


# ---------------------------------------------------------------------------
# load_tif_fov_multifile
# ---------------------------------------------------------------------------

def test_load_tif_fov_multifile_roundtrip(tmp_path: Path) -> None:
    write_synthetic_tif_multifile(tmp_path, "FOV_01", n_cells=10, image_size=64)
    fov = load_tif_fov_multifile(
        membrane_path=tmp_path / "FOV_01_ch0.tif",
        nuclear_path=tmp_path / "FOV_01_ch1.tif",
        fov_id="FOV_01",
        pixel_size_um=0.65,
    )
    assert fov.fov_id == "FOV_01"
    assert fov.membrane.shape == (64, 64)
    assert fov.nuclear is not None


# ---------------------------------------------------------------------------
# iter_tif_dataset — stack scheme
# ---------------------------------------------------------------------------

def test_iter_tif_dataset_stack(tmp_path: Path) -> None:
    for fov_name in ("FOV_01", "FOV_02", "FOV_03"):
        write_synthetic_tif_stack(tmp_path, fov_name, n_cells=10, image_size=64)
    fovs = list(iter_tif_dataset(tmp_path, 0, None, 0.65, scheme="stack"))
    assert len(fovs) == 3
    assert [f.fov_id for f in fovs] == ["FOV_01", "FOV_02", "FOV_03"]
    assert all(isinstance(f, TIFFOV) for f in fovs)


def test_iter_tif_dataset_stack_empty_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        list(iter_tif_dataset(tmp_path, 0, None, 0.65, scheme="stack"))


# ---------------------------------------------------------------------------
# iter_tif_dataset — multifile scheme
# ---------------------------------------------------------------------------

def test_iter_tif_dataset_multifile(tmp_path: Path) -> None:
    for fov_name in ("FOV_01", "FOV_02"):
        write_synthetic_tif_multifile(tmp_path, fov_name, n_cells=10, image_size=64)
    fovs = list(iter_tif_dataset(tmp_path, 0, 1, 0.65, scheme="multifile"))
    assert len(fovs) == 2
    assert all(f.nuclear is not None for f in fovs)


def test_iter_tif_dataset_unknown_scheme(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown TIF scheme"):
        list(iter_tif_dataset(tmp_path, 0, None, 0.65, scheme="bad_scheme"))
