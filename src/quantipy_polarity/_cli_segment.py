"""CLI command: quantipy segment.

Loads FOVs from TIF or ND2 (based on input.mode in config), runs Cellpose-SAM,
and writes label masks + membrane TIFs to 02_segmentation/ in the output dir.
The outputs are Phase-2-compatible: quantipy polarity can consume them directly.

Usage:
    quantipy segment --config config.yaml --input ./raw --output ./results
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import click
import structlog

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config, InputMasks

log = structlog.get_logger()


def _config_hash(cfg: Config) -> str:
    """SHA-256 of the canonical JSON config dump."""
    canonical = cfg.model_dump_json(exclude_defaults=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@main.command("segment", short_help="[Advanced] Cellpose-SAM → label masks")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to quantipy config YAML.",
)
@click.option(
    "--input",
    "input_path",
    required=False,
    type=click.Path(path_type=Path),
    default=None,
    help="Input directory (overrides config input.path).",
)
@click.option(
    "--output",
    "output_path",
    required=False,
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (overrides config project.output_dir).",
)
@click.option(
    "--gpu/--no-gpu", default=False, show_default=True, help="Use GPU for Cellpose."
)
def segment_cmd(
    config_path: Path,
    input_path: Path | None,
    output_path: Path | None,
    gpu: bool,
) -> None:
    """Run Cellpose-SAM segmentation: TIF/ND2 input → uint16 label masks.

    \b
    Output (in <output>/02_segmentation/):
        <fov_id>_mask.tif      uint16 label mask, Phase-2-compatible
        <fov_id>_membrane.tif  uint16 membrane channel
        <fov_id>_seg_meta.json segmentation metadata per FOV
        _stage_status.json     stage completion record
    """
    cfg = Config.from_yaml(config_path)

    if input_path is not None:
        # Override config input path without mutating the Pydantic model
        # (Pydantic v2: use model_copy with update)
        cfg = cfg.model_copy(
            update={"input": cfg.input.model_copy(update={"path": input_path})}
        )
    out_dir = output_path or cfg.project.output_dir
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_cfg = cfg.input
    if isinstance(input_cfg, InputMasks):
        raise click.ClickException(
            "quantipy segment requires input.mode = 'nd2' or 'tif'. "
            "Mode 'masks' means you already have segmented masks — "
            "use `quantipy polarity` directly."
        )

    seg_cfg = cfg.segment
    if seg_cfg.model == "user_supplied":
        raise click.ClickException(
            "segment.model = 'user_supplied' bypasses Cellpose — "
            "copy your masks to 02_segmentation/ and use `quantipy polarity` directly."
        )

    chash = _config_hash(cfg)
    from quantipy_polarity.segment._writer import write_stage_status

    write_stage_status(out_dir, "running", config_hash=chash)

    try:
        _run_segment(cfg, out_dir, gpu=gpu)
    except Exception:
        write_stage_status(out_dir, "failed", config_hash=chash)
        raise

    write_stage_status(out_dir, "complete", config_hash=chash)
    log.info("segment_complete", output_dir=str(out_dir))
    click.echo(f"Segmentation complete. Masks written to {out_dir / '02_segmentation'}")


def _run_segment(cfg: Config, out_dir: Path, *, gpu: bool) -> None:
    """Internal: iterate FOVs and segment each one."""
    from quantipy_polarity.segment.cellpose_sam import segment_fov
    from quantipy_polarity.segment._writer import write_fov_outputs

    input_cfg = cfg.input
    seg_cfg = cfg.segment

    try:
        from tqdm import tqdm as _tqdm

        progress = _tqdm
    except ImportError:

        def progress(x, **_):  # type: ignore[misc]
            return x

    fov_iter = _build_fov_iterator(cfg)
    fov_list = list(fov_iter)
    log.info("segment_start", n_fovs=len(fov_list), model=seg_cfg.model)

    for fov in progress(fov_list, desc="Segmenting FOVs"):
        log.info("segmenting_fov", fov_id=fov.fov_id)

        # Convert normalized float32 [0,1] membrane to uint16 for Cellpose
        import numpy as np

        image_u16 = (fov.membrane * 65535).clip(0, 65535).astype(np.uint16)

        masks, meta = segment_fov(
            image_u16,
            model=seg_cfg.model,
            diameter=float(seg_cfg.diameter_px) if seg_cfg.diameter_px else None,
            min_size_px=seg_cfg.min_size_px,
            gpu=gpu,
        )

        write_fov_outputs(
            out_dir,
            fov_id=fov.fov_id,
            label_mask=masks,
            membrane_float=fov.membrane,
            meta=meta,
        )


def _build_fov_iterator(cfg: Config):
    """Return an iterable of FOV objects. Delegates to io/ingest.build_fov_iterator."""
    from quantipy_polarity.io.ingest import build_fov_iterator

    return build_fov_iterator(cfg)
