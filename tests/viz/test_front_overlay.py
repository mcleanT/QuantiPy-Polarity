"""Tests for viz/front_overlay.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tests.fixtures._build import build_synthetic_fov


def _make_front_mask(size: int = 64) -> np.ndarray:
    mask = np.zeros((size, size), bool)
    mask[size // 2, 5 : size - 5] = True
    return mask


def test_plot_front_overlay_returns_figure() -> None:
    from quantipy_polarity.viz.front_overlay import plot_front_overlay
    data = build_synthetic_fov(n_cells=5, image_size=64, seed=10)
    front = _make_front_mask(64)
    fig = plot_front_overlay(data["membrane"], data["label_mask"], front)
    assert hasattr(fig, "savefig")
    plt.close(fig)


def test_plot_front_overlay_no_front() -> None:
    from quantipy_polarity.viz.front_overlay import plot_front_overlay
    data = build_synthetic_fov(n_cells=5, image_size=64, seed=11)
    empty_front = np.zeros((64, 64), bool)
    fig = plot_front_overlay(data["membrane"], data["label_mask"], empty_front)
    assert fig is not None
    plt.close(fig)


def test_save_front_overlay_writes_png() -> None:
    from quantipy_polarity.viz.front_overlay import save_front_overlay
    data = build_synthetic_fov(n_cells=5, image_size=64, seed=12)
    front = _make_front_mask(64)
    with tempfile.TemporaryDirectory() as td:
        out = save_front_overlay(
            data["membrane"], data["label_mask"], front,
            Path(td) / "overlay_test"
        )
        assert out.exists()
        assert out.suffix == ".png"
        assert out.read_bytes()[:4] == b"\x89PNG"


def test_plot_front_overlay_with_migration_arrows() -> None:
    from quantipy_polarity.viz.front_overlay import plot_front_overlay
    data = build_synthetic_fov(n_cells=5, image_size=64, seed=13)
    front = _make_front_mask(64)
    size = 64
    vx = np.ones((size, size), np.float32) * 3.0
    vy = np.zeros((size, size), np.float32)
    centroids = data["centroids"]
    fov_df = pd.DataFrame([
        {"cell_id": cid, "centroid_y": cy, "centroid_x": cx}
        for cid, (cy, cx) in list(centroids.items())[:3]
    ])
    fig = plot_front_overlay(
        data["membrane"], data["label_mask"], front,
        fov_df=fov_df, vx=vx, vy=vy,
    )
    assert fig is not None
    plt.close(fig)
