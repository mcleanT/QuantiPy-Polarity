"""Real implementation of `quantipy front`.

Detects the migration front from label masks, writes front_um_per_fov.parquet,
writes per-FOV QC overlay PNGs, and populates mig_dir_deg / dist_to_front_um /
mig_alignment in per_cell.parquet.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import numpy as np
import pandas as pd
import structlog
import tifffile

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config
from quantipy_polarity.migration.front_detect import (
    _compute_migration_field_v6,
    detect_front,
)
from quantipy_polarity.migration.front_io import write_front_parquet, read_front_parquet
from quantipy_polarity.migration.distance import compute_per_cell_migration

log = structlog.get_logger()


@main.command("front", short_help="[Advanced] Migration-front detection (auto only in v0.1.0)")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True),
              help="Path to quantipy YAML config.")
@click.option("--input", "input_dir", required=True, type=click.Path(exists=True),
              help="Directory containing 02_segmentation/ label masks.")
@click.option("--output", "output_dir", required=True, type=click.Path(),
              help="Results directory; 04_migration/ written here.")
@click.option("--qc", is_flag=True, default=False,
              help="Write per-FOV QC overlay PNGs into 04_migration/qc/.")
@click.option("--resume", is_flag=True, default=False,
              help="Skip FOVs already in front_um_per_fov.parquet.")
def front_cmd(
    config_path: str,
    input_dir: str,
    output_dir: str,
    qc: bool,
    resume: bool,
) -> None:
    """Detect migration front from label masks (automated v6 algorithm).

    Writes:
        <output>/04_migration/front_um_per_fov.parquet
        <output>/04_migration/qc/<fov_id>_front_overlay.png  (if --qc)
        Updates dist_to_front_um, mig_dir_deg, mig_alignment in
        <output>/05_aggregated/per_cell.parquet (if that file exists).
    """
    cfg = Config.from_yaml(Path(config_path))
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    seg_dir = input_path / "02_segmentation"
    if not seg_dir.exists():
        # Fallback: input_dir itself may already be 02_segmentation
        seg_dir = input_path

    mask_files = sorted(seg_dir.glob("*_mask.tif"))
    if not mask_files:
        raise click.ClickException(
            f"No *_mask.tif files found in {seg_dir}. "
            "Run `quantipy segment` first or check --input path."
        )

    mig_dir = output_path / "04_migration"
    mig_dir.mkdir(parents=True, exist_ok=True)
    front_parquet = mig_dir / "front_um_per_fov.parquet"

    # Load existing parquet for resume
    already_done: set[str] = set()
    if resume and front_parquet.exists():
        existing = read_front_parquet(front_parquet)
        already_done = set(existing["fov_id"].tolist())
        log.info("resume: skipping FOVs already in parquet", n=len(already_done))

    pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)

    from quantipy_polarity.contracts import FrontResult
    results: list[FrontResult] = []
    vx_by_fov: dict[str, np.ndarray] = {}
    vy_by_fov: dict[str, np.ndarray] = {}
    labels_by_fov: dict[str, np.ndarray] = {}

    for mask_file in mask_files:
        fov_id = mask_file.stem.replace("_mask", "")
        if fov_id in already_done:
            log.info("skipping (resume)", fov_id=fov_id)
            continue
        log.info("detecting front", fov_id=fov_id)
        labels = tifffile.imread(str(mask_file)).astype(np.int32)
        if labels.ndim != 2:
            log.warning("label mask is not 2-D, skipping", fov_id=fov_id, shape=labels.shape)
            continue

        result = detect_front(labels, pixel_size_um=pixel_size_um, fov_id=fov_id)
        results.append(result)

        vx, vy, _front_mask = _compute_migration_field_v6(labels)
        vx_by_fov[fov_id] = vx
        vy_by_fov[fov_id] = vy
        labels_by_fov[fov_id] = labels

        if qc:
            _write_qc_overlay(
                mask_file, labels, _front_mask, mig_dir / "qc", fov_id
            )

    if results:
        write_front_parquet(results, front_parquet)
        log.info("wrote front parquet", path=str(front_parquet), n_fovs=len(results))

    # Update per_cell.parquet if it exists
    per_cell_path = output_path / "05_aggregated" / "per_cell.parquet"
    if per_cell_path.exists() and results:
        _update_per_cell(
            per_cell_path, labels_by_fov, vx_by_fov, vy_by_fov,
            {r.fov_id: r for r in results}
        )


def _write_qc_overlay(
    mask_file: Path,
    labels: np.ndarray,
    front_mask: np.ndarray,
    qc_dir: Path,
    fov_id: str,
) -> None:
    """Write a front QC overlay PNG next to the mask file."""
    from quantipy_polarity.viz.front_overlay import save_front_overlay
    qc_dir.mkdir(parents=True, exist_ok=True)
    # Membrane TIF is expected as <fov_id>_membrane.tif sibling
    mem_path = mask_file.parent / f"{fov_id}_membrane.tif"
    if mem_path.exists():
        membrane = tifffile.imread(str(mem_path)).astype(np.float32)
        if membrane.ndim == 3:
            membrane = membrane[..., 0]
    else:
        membrane = (labels > 0).astype(np.float32)

    save_front_overlay(
        membrane, labels, front_mask,
        qc_dir / f"{fov_id}_front_overlay",
        title=fov_id,
    )
    log.info("wrote QC overlay", fov_id=fov_id)


def _update_per_cell(
    per_cell_path: Path,
    labels_by_fov: dict[str, np.ndarray],
    vx_by_fov: dict[str, np.ndarray],
    vy_by_fov: dict[str, np.ndarray],
    results_by_fov: dict,
) -> None:
    """Update migration columns in per_cell.parquet in-place (atomic)."""
    from quantipy_polarity.migration.distance import compute_all_fovs
    import os, tempfile

    df = pd.read_parquet(per_cell_path)
    updated = compute_all_fovs(
        df, labels_by_fov,
        {fov: (vx_by_fov[fov], vy_by_fov[fov]) for fov in vx_by_fov},
        results_by_fov,
    )
    fd, tmp = tempfile.mkstemp(
        dir=per_cell_path.parent, prefix=".per_cell_tmp_", suffix=".parquet"
    )
    os.close(fd)
    try:
        updated.to_parquet(tmp, index=False)
        os.replace(tmp, per_cell_path)
        log.info("updated per_cell.parquet with migration columns",
                 path=str(per_cell_path), n_rows=len(updated))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
