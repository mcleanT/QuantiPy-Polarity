"""Real implementation of `quantipy plot`.

Generates polarity vector maps, rose plots, front overlays, and a
population summary panel from a completed pipeline output directory.
"""

from __future__ import annotations

from pathlib import Path

import click
import numpy as np
import pandas as pd
import structlog
import tifffile

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config

log = structlog.get_logger()


@main.command("plot", short_help="[Advanced] Regenerate plots from aggregated parquet")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to quantipy YAML config.")
@click.option("--output", "output_dir", required=True, type=click.Path(exists=True),
              help="Results directory containing 05_aggregated/per_cell.parquet.")
@click.option("--per-fov-maps", is_flag=True, default=True, show_default=True,
              help="Generate per-FOV polarity vector maps.")
@click.option("--rose", is_flag=True, default=True, show_default=True,
              help="Generate per-FOV and aggregate rose plots.")
@click.option("--summary", is_flag=True, default=True, show_default=True,
              help="Generate population summary panel.")
@click.option("--front-overlays", is_flag=True, default=True, show_default=True,
              help="Generate front overlay PNGs (requires 04_migration/).")
def figures_cmd(
    config_path: str,
    output_dir: str,
    per_fov_maps: bool,
    rose: bool,
    summary: bool,
    front_overlays: bool,
) -> None:
    """Regenerate plots from an existing pipeline output directory.

    Reads per_cell.parquet from <output>/05_aggregated/.
    Writes all figures into <output>/06_plots/.
    Does NOT re-run any pipeline stages.
    """
    cfg = Config.from_yaml(Path(config_path))
    out = Path(output_dir)
    plots_dir = out / "06_plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    per_cell_path = out / "05_aggregated" / "per_cell.parquet"
    if not per_cell_path.exists():
        raise click.ClickException(
            f"per_cell.parquet not found at {per_cell_path}. "
            "Run `quantipy polarity` and `quantipy aggregate` first."
        )
    per_cell = pd.read_parquet(per_cell_path)
    log.info("loaded per_cell", n_cells=len(per_cell), n_fovs=per_cell["fov_id"].nunique())

    pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)

    # Load front parquet if available
    front_parquet = out / "04_migration" / "front_um_per_fov.parquet"
    front_df: pd.DataFrame | None = None
    if front_parquet.exists():
        from quantipy_polarity.migration.front_io import read_front_parquet
        front_df = read_front_parquet(front_parquet)
        log.info("loaded front parquet", n_fovs=len(front_df))

    seg_dir = out / "02_segmentation"

    if per_fov_maps:
        _generate_vector_maps(per_cell, seg_dir, plots_dir, pixel_size_um,
                              getattr(cfg, "viz", None))

    if rose:
        _generate_rose_plots(per_cell, plots_dir,
                             getattr(cfg, "viz", None))

    if front_overlays and front_df is not None:
        _generate_front_overlays(per_cell, seg_dir, front_df, plots_dir, pixel_size_um)

    if summary:
        _generate_summary(per_cell, plots_dir)

    log.info("figures complete", plots_dir=str(plots_dir))


def _generate_vector_maps(
    per_cell: pd.DataFrame,
    seg_dir: Path,
    plots_dir: Path,
    pixel_size_um: float,
    viz_cfg: object,
) -> None:
    from quantipy_polarity.viz.vector_map import save_vector_map
    vec_dir = plots_dir / "vector_maps"
    vec_dir.mkdir(parents=True, exist_ok=True)
    vector_scale = float(getattr(viz_cfg, "vector_scale", 1.0)) if viz_cfg else 1.0

    for fov_id, fov_df in per_cell.groupby("fov_id"):
        fov_id = str(fov_id)
        mask_path = seg_dir / f"{fov_id}_mask.tif"
        mem_path = seg_dir / f"{fov_id}_membrane.tif"
        if not mask_path.exists():
            log.warning("mask not found for FOV, skipping vector map", fov_id=fov_id)
            continue
        labels = tifffile.imread(str(mask_path)).astype(np.uint16)
        membrane = (
            tifffile.imread(str(mem_path)).astype(np.float32)
            if mem_path.exists()
            else (labels > 0).astype(np.float32)
        )
        if membrane.ndim == 3:
            membrane = membrane[..., 0]
        save_vector_map(
            membrane, labels, fov_df,
            vec_dir / fov_id,
            pixel_size_um=pixel_size_um,
            vector_scale=vector_scale,
            title=fov_id,
        )
        log.info("wrote vector map", fov_id=fov_id)


def _generate_rose_plots(
    per_cell: pd.DataFrame,
    plots_dir: Path,
    viz_cfg: object,
) -> None:
    from quantipy_polarity.viz.rose_plot import save_rose, plot_rose_grouped
    from quantipy_polarity.viz._style import save_figure
    import matplotlib.pyplot as plt
    rose_dir = plots_dir / "roses"
    rose_dir.mkdir(parents=True, exist_ok=True)
    n_bins = int(getattr(viz_cfg, "rose_bins", 24)) if viz_cfg else 24

    # Per-FOV roses
    for fov_id, fov_df in per_cell.groupby("fov_id"):
        fov_id = str(fov_id)
        angles = fov_df["axis_deg"].dropna().to_numpy(dtype=float)
        save_rose(angles, rose_dir / f"rose_{fov_id}", n_bins=n_bins, title=fov_id)
        log.info("wrote rose", fov_id=fov_id)

    # Aggregate rose (all conditions grouped)
    fig = plot_rose_grouped(per_cell, angle_col="axis_deg", n_bins=n_bins)
    save_figure(fig, plots_dir / "rose_aggregate")
    plt.close(fig)
    log.info("wrote aggregate rose")


def _generate_front_overlays(
    per_cell: pd.DataFrame,
    seg_dir: Path,
    front_df: pd.DataFrame,
    plots_dir: Path,
    pixel_size_um: float,
) -> None:
    from quantipy_polarity.viz.front_overlay import save_front_overlay
    from quantipy_polarity.migration.front_detect import _compute_migration_field_v6
    overlay_dir = plots_dir / "front_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    for _, front_row in front_df.iterrows():
        fov_id = str(front_row["fov_id"])
        mask_path = seg_dir / f"{fov_id}_mask.tif"
        if not mask_path.exists():
            continue
        labels = tifffile.imread(str(mask_path)).astype(np.int32)
        mem_path = seg_dir / f"{fov_id}_membrane.tif"
        membrane = (
            tifffile.imread(str(mem_path)).astype(np.float32)
            if mem_path.exists()
            else (labels > 0).astype(np.float32)
        )
        if membrane.ndim == 3:
            membrane = membrane[..., 0]
        _vx, _vy, front_mask = _compute_migration_field_v6(labels)
        fov_df = per_cell[per_cell["fov_id"] == fov_id] if len(per_cell) else None
        save_front_overlay(
            membrane, labels, front_mask,
            overlay_dir / f"{fov_id}_front",
            fov_df=fov_df if (fov_df is not None and len(fov_df) > 0) else None,
            vx=_vx, vy=_vy, title=fov_id,
        )
        log.info("wrote front overlay", fov_id=fov_id)


def _generate_summary(per_cell: pd.DataFrame, plots_dir: Path) -> None:
    from quantipy_polarity.viz.summary import save_population_summary
    n_fovs = per_cell["fov_id"].nunique()
    n_cells = len(per_cell)
    save_population_summary(
        per_cell,
        plots_dir / "population_summary",
        suptitle=f"Population summary — {n_fovs} FOVs, {n_cells} cells",
    )
    log.info("wrote population summary")
