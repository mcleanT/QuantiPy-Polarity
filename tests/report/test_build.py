"""Tests for report/build.py."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantipy_polarity.contracts import PER_CELL_COLUMNS
from quantipy_polarity.report.build import (
    _encode_png_thumbnail,
    build_report,
    gather_report_inputs,
)


def _make_per_cell_parquet(dest: Path, n_cells: int = 4, n_fovs: int = 2) -> Path:
    """Write a minimal per_cell.parquet with PER_CELL_COLUMNS schema."""
    fov_ids = [f"fov_{i % n_fovs:02d}" for i in range(n_cells)]
    df = pd.DataFrame(
        {
            "fov_id": fov_ids,
            "cell_id": list(range(n_cells)),
            "centroid_y": [10.0] * n_cells,
            "centroid_x": [20.0] * n_cells,
            "area_px": [100] * n_cells,
            "axis_deg": [45.0] * n_cells,
            "magnitude": [0.5] * n_cells,
            "qc_flags": [0] * n_cells,
            "condition": ["ctrl"] * n_cells,
            "mig_dir_deg": [0.0] * n_cells,
            "mig_alignment": [0.5] * n_cells,
            "dist_to_front_um": [5.0] * n_cells,
        }
    )
    # Ensure column order matches contract
    df = df[list(PER_CELL_COLUMNS)]
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / "per_cell.parquet"
    df.to_parquet(out, index=False)
    return out


def _make_tiny_png(path: Path, width: int = 1000, height: int = 1000) -> None:
    """Create a minimal PNG using PIL."""
    from PIL import Image

    img = Image.fromarray(
        np.zeros((height, width, 3), dtype=np.uint8), mode="RGB"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


# ---------------------------------------------------------------------------
# Test 1: empty dir returns zeroed dict
# ---------------------------------------------------------------------------


def test_gather_report_inputs_empty_dir(tmp_path: Path) -> None:
    result = gather_report_inputs(tmp_path)
    assert result["n_cells"] == 0
    assert result["fov_rows"] == []


# ---------------------------------------------------------------------------
# Test 2: parquet present → n_cells and n_fovs correct
# ---------------------------------------------------------------------------


def test_gather_report_inputs_with_parquet(tmp_path: Path) -> None:
    agg_dir = tmp_path / "05_aggregated"
    _make_per_cell_parquet(agg_dir, n_cells=6, n_fovs=3)

    result = gather_report_inputs(tmp_path)
    assert result["n_cells"] == 6
    assert result["n_fovs"] == 3


# ---------------------------------------------------------------------------
# Test 3: config.snapshot.yaml is read as-is
# ---------------------------------------------------------------------------


def test_gather_report_inputs_loads_config_yaml(tmp_path: Path) -> None:
    config_file = tmp_path / "config.snapshot.yaml"
    config_file.write_text("foo: bar\n", encoding="utf-8")

    result = gather_report_inputs(tmp_path)
    assert result["config_yaml"] == "foo: bar\n"


# ---------------------------------------------------------------------------
# Test 4: stage_status JSON files populate stage_statuses dict
# ---------------------------------------------------------------------------


def test_gather_report_inputs_loads_stage_statuses(tmp_path: Path) -> None:
    stage_dir = tmp_path / "stage_status"
    stage_dir.mkdir()
    (stage_dir / "01_segment.json").write_text(
        json.dumps({"status": "done"}), encoding="utf-8"
    )
    (stage_dir / "02_polarity.json").write_text(
        json.dumps({"status": "done"}), encoding="utf-8"
    )

    result = gather_report_inputs(tmp_path)
    assert "01_segment" in result["stage_statuses"]
    assert "02_polarity" in result["stage_statuses"]
    assert result["stage_statuses"]["01_segment"] == "done"
    assert result["stage_statuses"]["02_polarity"] == "done"


# ---------------------------------------------------------------------------
# Test 5: build_report creates an HTML file with <!DOCTYPE html>
# ---------------------------------------------------------------------------


def test_build_report_creates_html_file(tmp_path: Path) -> None:
    out_html = tmp_path / "out.html"
    build_report(tmp_path, out_html)
    assert out_html.exists()
    content = out_html.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content or "<!doctype html>" in content.lower()


# ---------------------------------------------------------------------------
# Test 6: no external URLs — fully self-contained
# ---------------------------------------------------------------------------


def test_build_report_no_external_urls(tmp_path: Path) -> None:
    out_html = tmp_path / "report.html"
    build_report(tmp_path, out_html)
    content = out_html.read_text(encoding="utf-8")
    assert "http" not in content, "HTML contains external URL references (not self-contained)"


# ---------------------------------------------------------------------------
# Test 7: atomic write — no .tmp.html files remain after build_report
# ---------------------------------------------------------------------------


def test_build_report_atomic_write_no_tmp_left(tmp_path: Path) -> None:
    out_html = tmp_path / "report.html"
    build_report(tmp_path, out_html)
    tmp_files = list(tmp_path.glob("*.tmp.html"))
    assert tmp_files == [], f"Leftover temp files: {tmp_files}"


# ---------------------------------------------------------------------------
# Test 8: _encode_png_thumbnail downscales a 1000×1000 PNG to ≤400 px
# ---------------------------------------------------------------------------


def test_encode_png_thumbnail_downscales(tmp_path: Path) -> None:
    from PIL import Image

    big_png = tmp_path / "big.png"
    _make_tiny_png(big_png, width=1000, height=1000)

    data_uri = _encode_png_thumbnail(big_png)
    assert data_uri.startswith("data:image/png;base64,")

    b64_data = data_uri.split(",", 1)[1]
    decoded = base64.b64decode(b64_data)
    import io as _io

    img = Image.open(_io.BytesIO(decoded))
    w, h = img.size
    assert max(w, h) <= 400, f"Thumbnail too large: {w}x{h}"
