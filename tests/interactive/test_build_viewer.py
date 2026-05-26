"""Tests for quantipy_polarity.interactive.build_viewer."""

from __future__ import annotations

import base64
import struct
import zlib
from pathlib import Path

import pandas as pd
import pytest

from quantipy_polarity.interactive.build_viewer import build_viewer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_png(path: Path) -> None:
    """Write a 1x1 white PNG to path (pure Python, no PIL/skimage required)."""

    def _crc(data: bytes) -> bytes:
        return struct.pack(">I", zlib.crc32(data) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_chunk = b"IHDR" + ihdr_data
    ihdr = struct.pack(">I", 13) + ihdr_chunk + _crc(ihdr_chunk)
    raw_row = b"\x00\xff\xff\xff"  # filter byte + RGB
    idat_data = zlib.compress(raw_row)
    idat_chunk = b"IDAT" + idat_data
    idat = struct.pack(">I", len(idat_data)) + idat_chunk + _crc(idat_chunk)
    iend_chunk = b"IEND"
    iend = struct.pack(">I", 0) + iend_chunk + _crc(iend_chunk)
    path.write_bytes(sig + ihdr + idat + iend)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def results_dir(tmp_path: Path) -> Path:
    """Minimal results directory with per_cell.parquet + one polarity map PNG."""
    agg_dir = tmp_path / "05_aggregated"
    agg_dir.mkdir(parents=True)
    maps_dir = tmp_path / "03_polarity" / "maps"
    maps_dir.mkdir(parents=True)

    df = pd.DataFrame(
        {
            "fov_id": ["fov_A", "fov_A", "fov_B"],
            "cell_id": [1, 2, 3],
            "qp_magnitude": [0.3, 0.7, 0.5],
            "qp_axis_deg": [45.0, 90.0, 120.0],
            "centroid_x": [100.0, 200.0, 150.0],
            "centroid_y": [100.0, 200.0, 150.0],
        }
    )
    df.to_parquet(agg_dir / "per_cell.parquet", index=False)
    _make_minimal_png(maps_dir / "fov_A_polarity_map.png")
    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_build_viewer_writes_html_file(results_dir: Path, tmp_path: Path) -> None:
    """build_viewer creates the file at output_path."""
    output_path = tmp_path / "out" / "viewer.html"
    build_viewer(results_dir, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_html_is_self_contained(results_dir: Path, tmp_path: Path) -> None:
    """Output HTML does not contain any http:// or https:// URL outside data URIs."""
    import re

    output_path = tmp_path / "viewer.html"
    build_viewer(results_dir, output_path)
    html = output_path.read_text(encoding="utf-8")

    # Remove all data URI occurrences so only external URLs remain
    html_no_data_uris = re.sub(r'data:[^"\';\s]+', "", html)
    assert "http://" not in html_no_data_uris
    assert "https://" not in html_no_data_uris


def test_html_contains_fov_id(results_dir: Path, tmp_path: Path) -> None:
    """FOV IDs from the parquet appear in the HTML."""
    output_path = tmp_path / "viewer.html"
    build_viewer(results_dir, output_path)
    html = output_path.read_text(encoding="utf-8")
    assert "fov_A" in html
    assert "fov_B" in html


def test_html_contains_cells_json(results_dir: Path, tmp_path: Path) -> None:
    """The string 'ALL_CELLS' appears in the HTML (JS constant name)."""
    output_path = tmp_path / "viewer.html"
    build_viewer(results_dir, output_path)
    html = output_path.read_text(encoding="utf-8")
    assert "ALL_CELLS" in html


def test_html_contains_base64_image(results_dir: Path, tmp_path: Path) -> None:
    """If a PNG exists in 03_polarity/maps/, the output contains data:image/png;base64,."""
    output_path = tmp_path / "viewer.html"
    build_viewer(results_dir, output_path)
    html = output_path.read_text(encoding="utf-8")
    assert "data:image/png;base64," in html


def test_html_no_image_placeholder(tmp_path: Path) -> None:
    """If no PNG exists, the output contains fov-placeholder (graceful missing-image handling)."""
    # Create a results dir without any PNG files
    agg_dir = tmp_path / "05_aggregated"
    agg_dir.mkdir(parents=True)
    # No maps dir created — maps_dir will not exist

    df = pd.DataFrame(
        {
            "fov_id": ["fov_X"],
            "cell_id": [1],
            "qp_magnitude": [0.5],
            "qp_axis_deg": [30.0],
            "centroid_x": [50.0],
            "centroid_y": [50.0],
        }
    )
    df.to_parquet(agg_dir / "per_cell.parquet", index=False)

    output_path = tmp_path / "viewer.html"
    build_viewer(tmp_path, output_path)
    html = output_path.read_text(encoding="utf-8")
    assert "fov-placeholder" in html


def test_build_viewer_fov_filter(results_dir: Path, tmp_path: Path) -> None:
    """build_viewer(..., fov='fov_A') only embeds cells with fov_id == 'fov_A'."""
    output_path = tmp_path / "viewer.html"
    build_viewer(results_dir, output_path, fov="fov_A")
    html = output_path.read_text(encoding="utf-8")
    # fov_A cells (cell_id 1, 2) must appear; fov_B cell (cell_id 3) must not
    assert "fov_A" in html
    # fov_B should not appear as a data row (it may appear nowhere, or only if
    # the template renders the FOV selector, but the cells JSON must not include it)
    import json
    import re

    match = re.search(r"const ALL_CELLS\s*=\s*(\[.*?\]);", html, re.DOTALL)
    assert match is not None, "ALL_CELLS not found in HTML"
    cells = json.loads(match.group(1))
    fov_ids = {c["fov_id"] for c in cells}
    assert fov_ids == {"fov_A"}


def test_build_viewer_missing_parquet_raises(tmp_path: Path) -> None:
    """build_viewer raises FileNotFoundError when the parquet does not exist."""
    empty_results = tmp_path / "empty_results"
    empty_results.mkdir()
    output_path = tmp_path / "viewer.html"
    with pytest.raises(FileNotFoundError):
        build_viewer(empty_results, output_path)


def test_build_viewer_empty_parquet_raises(tmp_path: Path) -> None:
    """build_viewer raises ValueError when parquet has no rows."""
    agg_dir = tmp_path / "05_aggregated"
    agg_dir.mkdir(parents=True)
    empty_df = pd.DataFrame(
        columns=["fov_id", "cell_id", "qp_magnitude", "qp_axis_deg"]
    )
    empty_df.to_parquet(agg_dir / "per_cell.parquet", index=False)
    output_path = tmp_path / "viewer.html"
    with pytest.raises(ValueError, match="no rows"):
        build_viewer(tmp_path, output_path)


def test_build_viewer_missing_required_column_raises(tmp_path: Path) -> None:
    """build_viewer raises ValueError when a required column is absent."""
    agg_dir = tmp_path / "05_aggregated"
    agg_dir.mkdir(parents=True)
    # Missing qp_axis_deg
    df = pd.DataFrame(
        {
            "fov_id": ["fov_A"],
            "cell_id": [1],
            "qp_magnitude": [0.5],
            # qp_axis_deg intentionally omitted
        }
    )
    df.to_parquet(agg_dir / "per_cell.parquet", index=False)
    output_path = tmp_path / "viewer.html"
    with pytest.raises(ValueError, match="missing required columns"):
        build_viewer(tmp_path, output_path)


def test_build_viewer_atomic_write(results_dir: Path, tmp_path: Path) -> None:
    """If output_path already exists, the old content is replaced (not left partially written)."""
    output_path = tmp_path / "viewer.html"
    output_path.write_text("OLD CONTENT", encoding="utf-8")
    build_viewer(results_dir, output_path)
    html = output_path.read_text(encoding="utf-8")
    assert "OLD CONTENT" not in html
    assert "ALL_CELLS" in html


def test_build_viewer_creates_parent_dir(results_dir: Path, tmp_path: Path) -> None:
    """Parent directory of output_path is created if it does not exist."""
    nested_output = tmp_path / "nested" / "deep" / "viewer.html"
    assert not nested_output.parent.exists()
    build_viewer(results_dir, nested_output)
    assert nested_output.exists()
