"""Unit tests for io/masks.py."""
from pathlib import Path

import numpy as np
import pytest
import tifffile

from quantipy_polarity.io.masks import MaskFOV, iter_mask_dataset, load_mask_fov


def _write_pair(tmp_path: Path, fov_id: str, shape=(64, 64)) -> tuple[Path, Path]:
    """Write a tiny matching (membrane, mask) pair under tmp_path/membrane/ and tmp_path/masks/."""
    mdir = tmp_path / "membrane"
    mskdir = tmp_path / "masks"
    mdir.mkdir(exist_ok=True)
    mskdir.mkdir(exist_ok=True)
    mem = (np.random.default_rng(0).random(shape) * 65535).astype(np.uint16)
    msk = np.zeros(shape, dtype=np.uint16)
    msk[10:30, 10:30] = 1
    msk[40:60, 40:60] = 2
    mp = mdir / f"{fov_id}.tif"
    mskp = mskdir / f"{fov_id}.tif"
    tifffile.imwrite(mp, mem)
    tifffile.imwrite(mskp, msk)
    return mp, mskp


def test_mask_fov_validates_shape() -> None:
    with pytest.raises(ValueError, match="mask shape"):
        MaskFOV(
            fov_id="FOV_01",
            label_mask=np.zeros((10, 10), dtype=np.uint16),
            membrane=np.zeros((20, 20), dtype=np.float32),
        )


def test_mask_fov_validates_2d_mask() -> None:
    with pytest.raises(ValueError, match="must be 2D"):
        MaskFOV(
            fov_id="FOV_01",
            label_mask=np.zeros((5, 5, 5), dtype=np.uint16),
            membrane=np.zeros((5, 5, 5), dtype=np.float32),
        )


def test_mask_fov_validates_unsigned() -> None:
    with pytest.raises(ValueError, match="unsigned int"):
        MaskFOV(
            fov_id="FOV_01",
            label_mask=np.zeros((10, 10), dtype=np.float32),
            membrane=np.zeros((10, 10), dtype=np.float32),
        )


def test_load_mask_fov_2d(tmp_path: Path) -> None:
    mp, mskp = _write_pair(tmp_path, "FOV_01")
    fov = load_mask_fov(mp, mskp, "FOV_01")
    assert fov.fov_id == "FOV_01"
    assert fov.label_mask.shape == (64, 64)
    assert fov.label_mask.dtype.kind == "u"
    assert fov.membrane.dtype == np.float32
    assert 0.0 <= fov.membrane.min() <= fov.membrane.max() <= 1.0


def test_load_mask_fov_multichannel(tmp_path: Path) -> None:
    mdir = tmp_path / "m"
    mskdir = tmp_path / "k"
    mdir.mkdir()
    mskdir.mkdir()
    # 2-channel membrane (H, W, C)
    mem = np.zeros((32, 32, 2), dtype=np.uint16)
    mem[..., 1] = 12345
    msk = np.ones((32, 32), dtype=np.uint16)
    tifffile.imwrite(mdir / "FOV_05.tif", mem)
    tifffile.imwrite(mskdir / "FOV_05.tif", msk)
    fov = load_mask_fov(mdir / "FOV_05.tif", mskdir / "FOV_05.tif", "FOV_05", channel_membrane=1)
    # All pixels in channel 1 are 12345 / 65535
    assert np.isclose(fov.membrane.max(), 12345 / 65535, atol=1e-4)


def test_load_mask_fov_invalid_channel(tmp_path: Path) -> None:
    mdir = tmp_path / "m"
    mskdir = tmp_path / "k"
    mdir.mkdir()
    mskdir.mkdir()
    mem = np.zeros((16, 16, 2), dtype=np.uint16)
    msk = np.ones((16, 16), dtype=np.uint16)
    tifffile.imwrite(mdir / "FOV_01.tif", mem)
    tifffile.imwrite(mskdir / "FOV_01.tif", msk)
    with pytest.raises(IndexError, match="channel 5"):
        load_mask_fov(mdir / "FOV_01.tif", mskdir / "FOV_01.tif", "FOV_01", channel_membrane=5)


def test_iter_mask_dataset(tmp_path: Path) -> None:
    for fov in ("FOV_01", "FOV_02", "FOV_03"):
        _write_pair(tmp_path, fov)
    fovs = list(iter_mask_dataset(tmp_path / "membrane", tmp_path / "masks"))
    assert [f.fov_id for f in fovs] == ["FOV_01", "FOV_02", "FOV_03"]
    assert all(isinstance(f, MaskFOV) for f in fovs)


def test_iter_mask_dataset_empty(tmp_path: Path) -> None:
    (tmp_path / "membrane").mkdir()
    (tmp_path / "masks").mkdir()
    with pytest.raises(FileNotFoundError):
        list(iter_mask_dataset(tmp_path / "membrane", tmp_path / "masks"))
