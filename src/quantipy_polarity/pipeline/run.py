"""Top-level pipeline orchestrator for `quantipy run`.

run_pipeline(cfg, out_dir, *, force, stages) executes the full pipeline
(or a subset of named stages) in-process. Each stage writes its state to
stage_status/<name>.json via pipeline/state.py.

Stage functions are private to this module; they call the same Python
functions used by the individual CLI subcommands.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import structlog

from quantipy_polarity.config import Config
from quantipy_polarity.pipeline.dag import STAGES, filter_stages, should_skip_stage
from quantipy_polarity.pipeline.state import (
    StageState,
    config_hash,
    read_stage_state,
    write_stage_state,
)

log = structlog.get_logger()


def run_pipeline(
    cfg: Config,
    out_dir: Path,
    *,
    force: bool = False,
    stages: list[str] | None = None,
) -> None:
    """Execute the full pipeline (or a subset) for the given config.

    Args:
        cfg: Validated Config object.
        out_dir: Base output directory. Created if absent.
        force: If True, ignore all stage_status caches and re-run everything.
        stages: List of stage names to run (None = all). Preserves canonical order.

    Raises:
        RuntimeError: If any stage fails (after writing status=failed to JSON).
        ValueError: If stages contains an unknown stage name.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chash = config_hash(cfg)
    ordered = filter_stages(stages)

    # Write frozen config snapshot
    snapshot_path = out_dir / "config.snapshot.yaml"
    cfg.to_yaml(snapshot_path)
    log.info("pipeline_start", stages=ordered, out_dir=str(out_dir), config_hash=chash)

    _STAGE_FN: dict[str, object] = {
        "ingest": _stage_ingest,
        "segment": _stage_segment,
        "polarity": _stage_polarity,
        "front": _stage_front,
        "aggregate": _stage_aggregate,
        "plot": _stage_plot,
        "report": _stage_report,
    }

    for stage_name in ordered:
        state = read_stage_state(out_dir, stage_name)
        if should_skip_stage(state, chash, force=force):
            log.info("stage_skipped", stage=stage_name, reason="already_done")
            continue

        log.info("stage_start", stage=stage_name)
        write_stage_state(out_dir, stage_name, "running", cfg=cfg)

        try:
            fn = _STAGE_FN[stage_name]
            fn(cfg, out_dir)  # type: ignore[operator]
        except Exception as exc:
            write_stage_state(
                out_dir, stage_name, "failed", cfg=cfg, preserve_started_at=True
            )
            log.error("stage_failed", stage=stage_name, error=str(exc))
            raise RuntimeError(f"Stage '{stage_name}' failed: {exc}") from exc

        write_stage_state(
            out_dir, stage_name, "done", cfg=cfg, preserve_started_at=True
        )
        log.info("stage_done", stage=stage_name)

    log.info("pipeline_complete", out_dir=str(out_dir))


# ---------------------------------------------------------------------------
# Stage implementations — each calls the same functions the CLI modules use
# ---------------------------------------------------------------------------


def _stage_ingest(cfg: Config, out_dir: Path) -> None:
    """Ingest: nd2/tif → normalized per-FOV TIFs in 01_ingest/."""
    from quantipy_polarity.config import InputMasks

    if isinstance(cfg.input, InputMasks):
        log.info("stage_ingest_skipped_masks_mode")
        return
    from quantipy_polarity.io.ingest import ingest_fovs

    ingest_fovs(cfg, out_dir)


def _stage_segment(cfg: Config, out_dir: Path) -> None:
    """Segment: membrane TIFs → uint16 label masks in 02_segmentation/."""
    from quantipy_polarity.config import InputMasks

    if isinstance(cfg.input, InputMasks):
        log.info("stage_segment_skipped_masks_mode")
        return
    from quantipy_polarity._cli_segment import _run_segment

    _run_segment(cfg, out_dir, gpu=False)


def _stage_polarity(cfg: Config, out_dir: Path) -> None:
    """Polarity: masks → per-FOV parquets in 03_polarity/per_fov/."""
    from quantipy_polarity.config import InputMasks
    from quantipy_polarity.io.masks import iter_mask_dataset
    from quantipy_polarity.polarity.boundary_pca import compute_cell_polarity
    from quantipy_polarity.polarity.per_cell import per_fov_to_parquet

    per_fov_dir = out_dir / "03_polarity" / "per_fov"
    per_fov_dir.mkdir(parents=True, exist_ok=True)

    # Determine mask source: 02_segmentation/ (from segment stage) or input.masks_dir
    if isinstance(cfg.input, InputMasks):
        mask_source = cfg.input.masks_dir
        membrane_source = cfg.input.path
        channel_membrane = cfg.input.channel_membrane
    else:
        mask_source = out_dir / "02_segmentation"
        membrane_source = out_dir / "02_segmentation"
        channel_membrane = 0  # written by _writer as single-channel uint16

    for fov in iter_mask_dataset(
        membrane_dir=membrane_source,
        masks_dir=mask_source,
        channel_membrane=channel_membrane,
    ):
        result = compute_cell_polarity(fov.membrane, fov.label_mask)
        out_path = per_fov_dir / f"{fov.fov_id}.parquet"
        per_fov_to_parquet(
            result,
            fov_id=fov.fov_id,
            label_mask=fov.label_mask,
            out_path=out_path,
            condition=None,
            overwrite=True,
        )
        log.info("polarity_fov_done", fov_id=fov.fov_id)


def _stage_aggregate(cfg: Config, out_dir: Path) -> None:
    """Aggregate: per-FOV parquets → experiment-wide per_cell.parquet."""
    from quantipy_polarity.polarity.per_cell import aggregate_experiment

    per_fov_dir = out_dir / "03_polarity" / "per_fov"
    parquets = sorted(per_fov_dir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError(f"No per-FOV parquets found in {per_fov_dir}")
    agg_dir = out_dir / "05_aggregated"
    agg_dir.mkdir(parents=True, exist_ok=True)
    out_path = agg_dir / "per_cell.parquet"
    aggregate_experiment(parquets, out_path, overwrite=True)
    log.info("aggregate_done", n_fovs=len(parquets), path=str(out_path))


def _stage_front(cfg: Config, out_dir: Path) -> None:
    """Front: label masks → front_um_per_fov.parquet + per_cell migration cols."""
    if cfg.migration.front_method == "none":
        log.info("stage_front_skipped_method_none")
        return

    import numpy as np
    import tifffile

    from quantipy_polarity.contracts import FrontResult
    from quantipy_polarity.migration.front_detect import (
        _compute_migration_field_v6,
        detect_front,
    )
    from quantipy_polarity.migration.front_io import write_front_parquet

    # Determine mask source
    from quantipy_polarity.config import InputMasks

    if isinstance(cfg.input, InputMasks):
        seg_dir = cfg.input.masks_dir
    else:
        seg_dir = out_dir / "02_segmentation"

    mask_files = sorted(Path(seg_dir).glob("*_mask.tif"))
    if not mask_files:
        raise FileNotFoundError(f"No *_mask.tif files in {seg_dir}")

    pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)
    mig_dir = out_dir / "04_migration"
    mig_dir.mkdir(parents=True, exist_ok=True)
    front_parquet = mig_dir / "front_um_per_fov.parquet"

    results: list[FrontResult] = []
    vx_by_fov: dict[str, np.ndarray] = {}
    vy_by_fov: dict[str, np.ndarray] = {}
    labels_by_fov: dict[str, np.ndarray] = {}

    for mask_file in mask_files:
        fov_id = mask_file.stem.replace("_mask", "")
        labels = tifffile.imread(str(mask_file)).astype(np.int32)
        if labels.ndim != 2:
            log.warning("non_2d_mask_skipped", fov_id=fov_id, shape=labels.shape)
            continue
        result = detect_front(labels, pixel_size_um=pixel_size_um, fov_id=fov_id)
        results.append(result)
        vx, vy, _ = _compute_migration_field_v6(labels)
        vx_by_fov[fov_id] = vx
        vy_by_fov[fov_id] = vy
        labels_by_fov[fov_id] = labels
        log.info("front_fov_done", fov_id=fov_id)

    if results:
        write_front_parquet(results, front_parquet)

    per_cell_path = out_dir / "05_aggregated" / "per_cell.parquet"
    if per_cell_path.exists() and results:
        import pandas as pd
        from quantipy_polarity.migration.distance import compute_all_fovs
        import os, tempfile

        df = pd.read_parquet(per_cell_path)
        updated = compute_all_fovs(
            df,
            labels_by_fov,
            {fov: (vx_by_fov[fov], vy_by_fov[fov]) for fov in vx_by_fov},
            {r.fov_id: r for r in results},
        )
        fd, tmp = tempfile.mkstemp(dir=per_cell_path.parent, suffix=".parquet")
        os.close(fd)
        try:
            updated.to_parquet(tmp, index=False)
            os.replace(tmp, per_cell_path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


def _stage_plot(cfg: Config, out_dir: Path) -> None:
    """Plot: per_cell.parquet → all figures in 06_plots/."""
    from quantipy_polarity._cli_figures import (
        _generate_vector_maps,
        _generate_rose_plots,
        _generate_front_overlays,
        _generate_summary,
    )
    import pandas as pd
    from quantipy_polarity.migration.front_io import read_front_parquet

    per_cell_path = out_dir / "05_aggregated" / "per_cell.parquet"
    if not per_cell_path.exists():
        raise FileNotFoundError(f"per_cell.parquet not found: {per_cell_path}")

    per_cell = pd.read_parquet(per_cell_path)
    plots_dir = out_dir / "06_plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)

    from quantipy_polarity.config import InputMasks

    seg_dir = (
        cfg.input.masks_dir
        if isinstance(cfg.input, InputMasks)
        else out_dir / "02_segmentation"
    )

    front_parquet_path = out_dir / "04_migration" / "front_um_per_fov.parquet"
    front_df = (
        read_front_parquet(front_parquet_path) if front_parquet_path.exists() else None
    )

    _generate_vector_maps(per_cell, seg_dir, plots_dir, pixel_size_um, cfg.viz)
    _generate_rose_plots(per_cell, plots_dir, cfg.viz)
    if front_df is not None:
        _generate_front_overlays(per_cell, seg_dir, front_df, plots_dir, pixel_size_um)
    _generate_summary(per_cell, plots_dir)


def _stage_report(cfg: Config, out_dir: Path) -> None:
    """Report: gather all outputs → self-contained report.html."""
    from quantipy_polarity.report.build import build_report

    out_html = out_dir / "report.html"
    build_report(out_dir, out_html, cfg=cfg)
    log.info("report_written", path=str(out_html))
