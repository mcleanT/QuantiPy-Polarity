"""Unit tests for io/_common.py utilities."""
from pathlib import Path

import pytest

from quantipy_polarity.io._common import fov_id_from_path, pair_masks_with_membranes


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
