"""Tests for viz/summary.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _make_per_cell(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    return pd.DataFrame({
        "fov_id": [f"FOV_{i % 3 + 1:02d}" for i in range(n)],
        "cell_id": list(range(1, n + 1)),
        "axis_deg": rng.uniform(0, 180, n),
        "magnitude": rng.uniform(0.1, 1.0, n),
        "dist_to_front_um": rng.uniform(0, 100, n),
    })


def test_plot_population_summary_returns_figure() -> None:
    from quantipy_polarity.viz.summary import plot_population_summary
    df = _make_per_cell(40)
    fig = plot_population_summary(df)
    assert hasattr(fig, "savefig")
    plt.close(fig)


def test_plot_population_summary_no_dist_col() -> None:
    from quantipy_polarity.viz.summary import plot_population_summary
    df = _make_per_cell(20).drop(columns=["dist_to_front_um"])
    fig = plot_population_summary(df)
    assert fig is not None
    plt.close(fig)


def test_plot_population_summary_all_dist_nan() -> None:
    from quantipy_polarity.viz.summary import plot_population_summary
    df = _make_per_cell(20)
    df["dist_to_front_um"] = np.nan
    fig = plot_population_summary(df)
    assert fig is not None
    plt.close(fig)


def test_save_population_summary_writes_png_and_pdf() -> None:
    from quantipy_polarity.viz.summary import save_population_summary
    df = _make_per_cell(30)
    with tempfile.TemporaryDirectory() as td:
        paths = save_population_summary(df, Path(td) / "summary_test")
        assert len(paths) == 2
        for p in paths:
            assert p.exists()
        pngs = [p for p in paths if p.suffix == ".png"]
        pdfs = [p for p in paths if p.suffix == ".pdf"]
        assert pngs[0].read_bytes()[:4] == b"\x89PNG"
        assert pdfs[0].read_bytes()[:4] == b"%PDF"
