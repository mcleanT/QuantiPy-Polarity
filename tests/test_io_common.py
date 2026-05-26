"""Unit tests for io/_common.py utilities."""

from pathlib import Path

import pytest

from quantipy_polarity.io._common import (
    fov_id_from_path,
    pair_masks_with_membranes,
    pair_tifs_by_channel,
)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("FOV_01.tif", "FOV_01"),
        ("FOV01.tif", "FOV_01"),
        ("FOV-001.tif", "FOV_001"),
        ("fov_42_membrane.tif", "FOV_42"),
        ("/a/b/c/FOV_007_mip.tif", "FOV_007"),
        ("sample_x.tif", "sample_x"),
        ("no_fov_marker", "no_fov_marker"),
    ],
)
def test_fov_id_from_path(path: str, expected: str) -> None:
    assert fov_id_from_path(path) == expected


def test_pair_masks_finds_matches(tmp_path: Path) -> None:
    mdir = tmp_path / "membrane"
    mskdir = tmp_path / "masks"
    mdir.mkdir()
    mskdir.mkdir()
    for fov in ("FOV_01", "FOV_02", "FOV_03"):
        (mdir / f"{fov}_membrane.tif").write_bytes(b"")
        (mskdir / f"{fov}_mask.tif").write_bytes(b"")
    pairs = pair_masks_with_membranes(mdir, mskdir)
    assert len(pairs) == 3
    fov_ids = [p[0] for p in pairs]
    assert fov_ids == ["FOV_01", "FOV_02", "FOV_03"]


def test_pair_raises_on_unmatched_membrane(tmp_path: Path) -> None:
    mdir = tmp_path / "membrane"
    mskdir = tmp_path / "masks"
    mdir.mkdir()
    mskdir.mkdir()
    (mdir / "FOV_01.tif").write_bytes(b"")
    (mdir / "FOV_99.tif").write_bytes(b"")
    (mskdir / "FOV_01.tif").write_bytes(b"")
    # FOV_99 has no mask
    with pytest.raises(FileNotFoundError, match="FOV_99"):
        pair_masks_with_membranes(mdir, mskdir)


def test_pair_raises_on_empty_dir(tmp_path: Path) -> None:
    mdir = tmp_path / "membrane"
    mskdir = tmp_path / "masks"
    mdir.mkdir()
    mskdir.mkdir()
    with pytest.raises(FileNotFoundError, match="No .tif files found"):
        pair_masks_with_membranes(mdir, mskdir)


# ---------------------------------------------------------------------------
# pair_tifs_by_channel tests
# ---------------------------------------------------------------------------


def test_pair_tifs_by_channel_no_seg(tmp_path: Path) -> None:
    """Pairs membrane-only files; seg_path is None when channel_segmentation is None."""
    for fov in ("FOV_01", "FOV_02"):
        (tmp_path / f"{fov}_ch0.tif").write_bytes(b"")
        (tmp_path / f"{fov}_ch1.tif").write_bytes(b"")

    pairs = pair_tifs_by_channel(tmp_path, channel_membrane=0)
    assert len(pairs) == 2
    fov_ids = [p[0] for p in pairs]
    assert fov_ids == ["FOV_01", "FOV_02"]
    assert all(p[2] is None for p in pairs)


def test_pair_tifs_by_channel_with_seg(tmp_path: Path) -> None:
    """Returns (fov_id, mem_path, seg_path) tuples when segmentation channel given."""
    for fov in ("FOV_01", "FOV_02"):
        (tmp_path / f"{fov}_ch0.tif").write_bytes(b"")
        (tmp_path / f"{fov}_ch1.tif").write_bytes(b"")

    pairs = pair_tifs_by_channel(tmp_path, channel_membrane=0, channel_segmentation=1)
    assert len(pairs) == 2
    for fov_id, mem_path, seg_path in pairs:
        assert fov_id in ("FOV_01", "FOV_02")
        assert mem_path.name.endswith("_ch0.tif")
        assert seg_path is not None
        assert seg_path.name.endswith("_ch1.tif")


def test_pair_tifs_by_channel_missing_seg_raises(tmp_path: Path) -> None:
    """Raises FileNotFoundError when a membrane file has no matching seg channel file."""
    (tmp_path / "FOV_01_ch0.tif").write_bytes(b"")
    # No FOV_01_ch1.tif
    with pytest.raises(FileNotFoundError, match="FOV_01_ch1.tif"):
        pair_tifs_by_channel(tmp_path, channel_membrane=0, channel_segmentation=1)


def test_pair_tifs_by_channel_empty_dir_raises(tmp_path: Path) -> None:
    """Raises FileNotFoundError when no membrane-channel files exist."""
    with pytest.raises(FileNotFoundError):
        pair_tifs_by_channel(tmp_path, channel_membrane=0)
