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


def run_polarity_by_condition(
    per_cell_path: Path,
    metadata_path: Path,
    output_dir: Path,
    *,
    condition_col: str = "condition",
    magnitude_col: str = "magnitude",
) -> dict:
    """Boxplot of polarity magnitude grouped by experimental condition.

    Args:
        per_cell_path: Path to per_cell.parquet (must contain ``fov_id`` + magnitude_col).
        metadata_path: Path to CSV/TSV with columns [fov_id, condition_col].
        output_dir: Directory to write ``polarity_by_condition.pdf`` and
            ``polarity_by_condition_results.json``.
        condition_col: Column name in metadata for the grouping variable.
        magnitude_col: Column name in per_cell for polarity magnitude.

    Returns:
        dict with keys: groups, n_per_group, medians, p_value (or None), test_used.

    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If required columns are missing or fewer than 2 groups found.
    """
    per_cell_path, metadata_path, output_dir = (
        Path(per_cell_path),
        Path(metadata_path),
        Path(output_dir),
    )
    for p in (per_cell_path, metadata_path):
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

    df = pd.read_parquet(per_cell_path)
    sep = "\t" if str(metadata_path).endswith(".tsv") else ","
    meta = pd.read_csv(metadata_path, sep=sep)

    for col, src in [
        (magnitude_col, "per_cell"),
        ("fov_id", "per_cell"),
        (condition_col, "metadata"),
        ("fov_id", "metadata"),
    ]:
        src_df = df if src == "per_cell" else meta
        if col not in src_df.columns:
            raise ValueError(f"Column {col!r} not found in {src} file")

    merged = df.merge(meta[["fov_id", condition_col]], on="fov_id", how="inner")
    groups = sorted(merged[condition_col].dropna().unique().tolist())
    if len(groups) < 2:
        raise ValueError(
            f"Fewer than 2 groups found in column {condition_col!r}: {groups}"
        )

    group_data = [
        merged.loc[merged[condition_col] == g, magnitude_col].dropna().values
        for g in groups
    ]
    n_per_group = [int(len(d)) for d in group_data]
    medians = [float(np.median(d)) for d in group_data]

    p_value = None
    test_used = None
    note = None
    if len(groups) == 2:
        stat, p_value = stats.mannwhitneyu(
            group_data[0], group_data[1], alternative="two-sided"
        )
        p_value = float(p_value)
        test_used = "Mann-Whitney U"
    else:
        note = f"Statistical test skipped: {len(groups)} groups (only performed for 2 groups)."

    # Figure
    apply_nature_style()
    fig, ax = plt.subplots(figsize=(1.6 * len(groups) + 0.8, 3.0))
    bp = ax.boxplot(
        group_data,
        patch_artist=True,
        widths=0.5,
        medianprops={"color": "#272727", "linewidth": 1.5},
    )
    palette = ["#5B8FD6", "#E28E2C", "#7BAA5B", "#C45AD6", "#D24B40"]
    for patch, color in zip(bp["boxes"], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks(range(1, len(groups) + 1))
    ax.set_xticklabels(
        [f"{g}\n(N={n})" for g, n in zip(groups, n_per_group)], fontsize=6
    )
    ax.set_ylabel("Polarity magnitude", fontsize=7)
    ax.set_xlabel(condition_col, fontsize=7)
    if p_value is not None:
        sig = (
            "***"
            if p_value < 0.001
            else "**"
            if p_value < 0.01
            else "*"
            if p_value < 0.05
            else "ns"
        )
        ax.set_title(f"Mann-Whitney U  p={p_value:.3g}  {sig}", fontsize=7)

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_path = output_dir / "polarity_by_condition.pdf"
    fig.savefig(fig_path, bbox_inches="tight", dpi=600)
    plt.close(fig)

    results = {
        "groups": groups,
        "n_per_group": n_per_group,
        "medians": medians,
        "p_value": p_value,
        "test_used": test_used,
        "note": note,
    }
    json_path = output_dir / "polarity_by_condition_results.json"
    json_path.write_text(json.dumps(results, indent=2))
    return results
