"""Nature-style matplotlib configuration for QuantiPy Polarity figures.

Tries to import from ``Science/styles/figstyle.py`` (lab monorepo, developer
machines). Falls back to a self-contained copy of the relevant settings so the
public repo works without any external path.

Public API
----------
apply_nature_style()     Apply lab rcParams.
PALETTE                  CB-safe colour dict.
save_figure(fig, stem)   Save PNG (600 DPI) + PDF (fonttype=42) atomically.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # non-interactive; caller can override before importing
import matplotlib.pyplot as plt


# ── Attempt to import the canonical lab figstyle ─────────────────────────────
_FIGSTYLE_IMPORTED = False
_MONOREPO_STYLES = Path(__file__).resolve().parents[6] / "styles" / "figstyle.py"

if _MONOREPO_STYLES.exists():
    import importlib.util as _ilu

    _spec = _ilu.spec_from_file_location("_lab_figstyle", _MONOREPO_STYLES)
    if _spec and _spec.loader:
        _lab = _ilu.module_from_spec(_spec)
        try:
            _spec.loader.exec_module(_lab)  # type: ignore[union-attr]
            _FIGSTYLE_IMPORTED = True
        except Exception:
            pass


# ── Palette (identical to Science/styles/figstyle.py PALETTE) ─────────────────
PALETTE: dict[str, str] = {
    "phase1": "#5B8FD6",
    "phase2": "#E28E2C",
    "phase3": "#7BAA5B",
    "phase4": "#C45AD6",
    "failure": "#D24B40",
    "composite": "#272727",
    "neutral_bg": "#F2E6D9",
    "cat5": "#E69F00",
    "cat6": "#56B4E9",
    "cat7": "#5DA88F",
}

# Semantic aliases used by Phase 4 figures
COLOR_POLARITY = PALETTE["phase1"]  # arrows coloured by magnitude default
COLOR_FRONT = PALETTE["phase2"]  # front overlay line
COLOR_CELL = PALETTE["composite"]  # cell outlines
COLOR_FAILURE = PALETTE["failure"]


# ── rcParams (baked-in fallback, matches Science/styles/figstyle.py) ──────────
_RCPARAMS: dict[str, Any] = {
    "font.family": "Arial",
    "font.size": 7,
    "axes.titlesize": 8,
    "axes.titleweight": "bold",
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "lines.linewidth": 0.8,
    "patch.linewidth": 0.5,
    "legend.fontsize": 6,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "axes.spines.top": False,
    "axes.spines.right": False,
}


def apply_nature_style() -> None:
    """Apply lab Nature-style rcParams to the current matplotlib session."""
    if _FIGSTYLE_IMPORTED and hasattr(_lab, "apply_nature_style"):
        _lab.apply_nature_style()
    else:
        plt.rcParams.update(_RCPARAMS)


def save_figure(fig: plt.Figure, stem: str | Path, dpi: int = 600) -> list[Path]:
    """Save figure as PNG (raster, 600 DPI) and PDF (vector, fonttype=42).

    Uses atomic write (temp file + os.replace) for both outputs.
    Avoids combining constrained_layout with bbox_inches="tight".

    Parameters
    ----------
    fig : matplotlib Figure.
    stem : path stem without extension (e.g. ``results/06_plots/rose_FOV_01``).
    dpi : raster DPI (default 600 per lab standard).

    Returns
    -------
    List of Path objects for the written files: [<stem>.png, <stem>.pdf].
    """
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for ext, kwargs in [
        (".png", {"dpi": dpi, "bbox_inches": "tight"}),
        (".pdf", {"dpi": dpi}),
    ]:
        out = stem.with_suffix(ext)
        fd, tmp = tempfile.mkstemp(dir=stem.parent, prefix=".fig_tmp_", suffix=ext)
        os.close(fd)
        try:
            fig.savefig(tmp, **kwargs)
            os.replace(tmp, out)
            written.append(out)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return written
