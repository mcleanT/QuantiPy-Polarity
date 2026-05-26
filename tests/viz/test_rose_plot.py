"""Tests for viz/rose_plot.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def test_plot_rose_returns_figure_and_axes() -> None:
    from quantipy_polarity.viz.rose_plot import plot_rose

    rng = np.random.default_rng(0)
    angles = rng.uniform(0, 180, 50)
    fig, ax = plot_rose(angles, n_bins=12)
    assert hasattr(fig, "savefig")
    assert ax is not None
    plt.close(fig)


def test_plot_rose_handles_empty_angles() -> None:
    from quantipy_polarity.viz.rose_plot import plot_rose

    fig, ax = plot_rose(np.array([]), n_bins=12)
    assert fig is not None
    plt.close(fig)


def test_plot_rose_full_disk() -> None:
    from quantipy_polarity.viz.rose_plot import plot_rose

    rng = np.random.default_rng(1)
    angles = rng.uniform(0, 360, 40)
    fig, ax = plot_rose(angles, half_disk=False, n_bins=24)
    assert fig is not None
    plt.close(fig)


def test_save_rose_writes_png_and_pdf() -> None:
    from quantipy_polarity.viz.rose_plot import save_rose

    rng = np.random.default_rng(2)
    angles = rng.uniform(0, 180, 60)
    with tempfile.TemporaryDirectory() as td:
        paths = save_rose(angles, Path(td) / "rose_test", n_bins=12)
        assert len(paths) == 2
        for p in paths:
            assert p.exists()
        pngs = [p for p in paths if p.suffix == ".png"]
        pdfs = [p for p in paths if p.suffix == ".pdf"]
        assert pngs[0].read_bytes()[:4] == b"\x89PNG"
        assert pdfs[0].read_bytes()[:4] == b"%PDF"


def test_plot_rose_grouped_single_condition() -> None:
    from quantipy_polarity.viz.rose_plot import plot_rose_grouped

    rng = np.random.default_rng(3)
    df = pd.DataFrame({"axis_deg": rng.uniform(0, 180, 40), "condition": "A"})
    fig = plot_rose_grouped(df)
    assert fig is not None
    plt.close(fig)


def test_plot_rose_grouped_two_conditions() -> None:
    from quantipy_polarity.viz.rose_plot import plot_rose_grouped

    rng = np.random.default_rng(4)
    df = pd.DataFrame(
        {
            "axis_deg": rng.uniform(0, 180, 80),
            "condition": ["A"] * 40 + ["B"] * 40,
        }
    )
    fig = plot_rose_grouped(df)
    assert fig is not None
    plt.close(fig)


def test_plot_rose_grouped_no_condition_col() -> None:
    from quantipy_polarity.viz.rose_plot import plot_rose_grouped

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"axis_deg": rng.uniform(0, 180, 30)})
    fig = plot_rose_grouped(df)
    assert fig is not None
    plt.close(fig)
