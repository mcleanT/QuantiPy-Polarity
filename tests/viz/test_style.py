"""Tests for viz/_style.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def test_apply_nature_style_sets_rcparams() -> None:
    from quantipy_polarity.viz._style import apply_nature_style

    apply_nature_style()
    import matplotlib as mpl

    assert mpl.rcParams["pdf.fonttype"] == 42
    assert mpl.rcParams["svg.fonttype"] == "none"
    assert mpl.rcParams["axes.linewidth"] == 0.5


def test_palette_has_required_keys() -> None:
    from quantipy_polarity.viz._style import PALETTE

    required = {
        "phase1",
        "phase2",
        "phase3",
        "phase4",
        "failure",
        "composite",
        "neutral_bg",
    }
    assert required.issubset(PALETTE.keys())
    # All values are valid hex colours
    for k, v in PALETTE.items():
        assert v.startswith("#") and len(v) == 7, f"bad hex colour for {k}: {v}"


def test_save_figure_writes_png_and_pdf() -> None:
    from quantipy_polarity.viz._style import save_figure, apply_nature_style

    apply_nature_style()
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.plot([0, 1], [0, 1])
    with tempfile.TemporaryDirectory() as td:
        written = save_figure(fig, Path(td) / "test_fig")
        paths = {p.suffix: p for p in written}
        assert ".png" in paths
        assert ".pdf" in paths
        assert paths[".png"].exists()
        assert paths[".pdf"].exists()
        # PNG starts with PNG header
        assert paths[".png"].read_bytes()[:4] == b"\x89PNG"
        # PDF starts with PDF header
        assert paths[".pdf"].read_bytes()[:4] == b"%PDF"
    plt.close(fig)


def test_save_figure_creates_parent_dirs() -> None:
    from quantipy_polarity.viz._style import save_figure

    fig, ax = plt.subplots(figsize=(1, 1))
    ax.plot([0], [0])
    with tempfile.TemporaryDirectory() as td:
        stem = Path(td) / "nested" / "subdir" / "fig"
        save_figure(fig, stem)
        assert (stem.parent).is_dir()
    plt.close(fig)
