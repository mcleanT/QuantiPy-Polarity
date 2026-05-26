"""Scatter of polarity magnitude vs distance-to-front with Theil-Sen robust regression."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from quantipy_polarity.viz._style import apply_nature_style


def run_magnitude_vs_distance(
    per_cell_path: Path,
    output_dir: Path,
    *,
    magnitude_col: str = "qp_magnitude",
    distance_col: str = "dist_to_front_px",
    max_cells: int = 5000,
) -> dict:
    """Scatter of polarity magnitude vs distance-to-front with robust regression.

    Args:
        per_cell_path: Path to per_cell.parquet. Must contain magnitude_col and
            distance_col. If distance_col is absent, emits a JSON noting the
            column is missing and writes no figure (exits cleanly — front detection
            may not have been run).
        output_dir: Directory to write ``magnitude_vs_distance.pdf`` and
            ``magnitude_vs_distance_results.json``.
        magnitude_col: Column name for polarity magnitude.
        distance_col: Column name for distance to migration front (pixels).
        max_cells: Subsample to this many cells for scatter legibility (random seed=42).

    Returns:
        dict with keys: n_cells, slope, intercept, r_squared, distance_col_found.

    Raises:
        FileNotFoundError: If per_cell_path does not exist.
        ValueError: If magnitude_col is absent.
    """
    per_cell_path, output_dir = Path(per_cell_path), Path(output_dir)
    if not per_cell_path.exists():
        raise FileNotFoundError(f"File not found: {per_cell_path}")

    df = pd.read_parquet(per_cell_path)
    if magnitude_col not in df.columns:
        raise ValueError(f"Column {magnitude_col!r} not found in parquet")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle missing distance column gracefully
    if distance_col not in df.columns:
        results = {
            "n_cells": len(df),
            "slope": None,
            "intercept": None,
            "r_squared": None,
            "distance_col_found": False,
            "note": (
                f"Column {distance_col!r} not found. "
                "Run `quantipy front` to compute migration distances, then re-run this analysis."
            ),
        }
        (output_dir / "magnitude_vs_distance_results.json").write_text(
            json.dumps(results, indent=2)
        )
        return results

    df_clean = df[[magnitude_col, distance_col]].dropna()
    if len(df_clean) > max_cells:
        df_clean = df_clean.sample(max_cells, random_state=42)

    x = df_clean[distance_col].values.astype(float)
    y = df_clean[magnitude_col].values.astype(float)

    # Theil-Sen robust regression
    slope, intercept, low_slope, high_slope = stats.theilslopes(y, x)
    slope, intercept = float(slope), float(intercept)

    # R² (Pearson, for reporting alongside the robust line)
    r, _ = stats.pearsonr(x, y)
    r_squared = float(r**2)

    # Figure
    apply_nature_style()
    fig, ax = plt.subplots(figsize=(3.5, 3.0))
    ax.scatter(x, y, s=4, alpha=0.3, color="#5B8FD6", linewidths=0, rasterized=True)
    x_line = np.linspace(x.min(), x.max(), 200)
    ax.plot(
        x_line,
        slope * x_line + intercept,
        color="#D24B40",
        linewidth=1.5,
        label=f"Theil-Sen  slope={slope:.3f}  R²={r_squared:.2f}",
    )
    ax.set_xlabel("Distance to front (px)", fontsize=7)
    ax.set_ylabel("Polarity magnitude", fontsize=7)
    ax.legend(fontsize=6, frameon=False)

    fig_path = output_dir / "magnitude_vs_distance.pdf"
    fig.savefig(fig_path, bbox_inches="tight", dpi=600)
    plt.close(fig)

    results = {
        "n_cells": int(len(df_clean)),
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "distance_col_found": True,
    }
    (output_dir / "magnitude_vs_distance_results.json").write_text(
        json.dumps(results, indent=2)
    )
    return results
