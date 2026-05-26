"""Tests for viz/vector_map.py.

Tests verify file creation and valid PNG/PDF headers; NOT pixel content.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd

from tests.fixtures._build import build_synthetic_fov


def _make_fov_df(data: dict, fov_id: str = "FOV_01") -> pd.DataFrame:
    theta = data["theta_truth"]
    centroids = data["centroids"]
    rows = []
    for cid, ang in theta.items():
        if cid not in centroids:
            continue
        cy, cx = centroids[cid]
        rows.append(
            {
                "fov_id": fov_id,
                "cell_id": cid,
                "centroid_y": cy,
                "centroid_x": cx,
                "axis_deg": ang,
                "magnitude": float(np.random.default_rng(cid).uniform(0.2, 0.9)),
            }
        )
    return pd.DataFrame(rows)


def test_save_vector_map_writes_png_and_pdf() -> None:
    from quantipy_polarity.viz.vector_map import save_vector_map

    data = build_synthetic_fov(n_cells=10, image_size=64, seed=1)
    df = _make_fov_df(data)
    with tempfile.TemporaryDirectory() as td:
        paths = save_vector_map(
            data["membrane"],
            data["label_mask"],
            df,
            Path(td) / "vec_map",
            pixel_size_um=0.65,
            title="Test FOV",
        )
        assert len(paths) == 2
        for p in paths:
            assert p.exists()
            assert p.stat().st_size > 0
        # Check headers
        pngs = [p for p in paths if p.suffix == ".png"]
        pdfs = [p for p in paths if p.suffix == ".pdf"]
        assert pngs[0].read_bytes()[:4] == b"\x89PNG"
        assert pdfs[0].read_bytes()[:4] == b"%PDF"


def test_vector_map_empty_df_does_not_crash() -> None:
    from quantipy_polarity.viz.vector_map import plot_vector_map
    import matplotlib.pyplot as plt

    data = build_synthetic_fov(n_cells=5, image_size=64, seed=2)
    empty_df = pd.DataFrame(
        columns=["cell_id", "centroid_y", "centroid_x", "axis_deg", "magnitude"]
    )
    fig = plot_vector_map(data["membrane"], data["label_mask"], empty_df)
    assert fig is not None
    plt.close(fig)


def test_vector_map_returns_figure_object() -> None:
    from quantipy_polarity.viz.vector_map import plot_vector_map
    import matplotlib.pyplot as plt

    data = build_synthetic_fov(n_cells=8, image_size=64, seed=3)
    df = _make_fov_df(data)
    fig = plot_vector_map(data["membrane"], data["label_mask"], df)
    assert hasattr(fig, "savefig")
    plt.close(fig)
