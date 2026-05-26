"""Real `quantipy ingest` command — nd2/tif → normalized per-FOV TIFs.

Writes per-FOV membrane TIFs to <output>/01_ingest/.
Records stage status in <output>/stage_status/ingest.json.
Skipped automatically for masks input mode (pre-segmented inputs need no ingest).
"""

from __future__ import annotations

from pathlib import Path

import click
import structlog

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config

log = structlog.get_logger()


@main.command(
    "ingest",
    short_help="[Advanced] nd2/tif → normalized per-FOV TIFs (01_ingest/)",
)
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to quantipy YAML config.",
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
    "--force",
    is_flag=True,
    default=False,
    help="Re-run even if stage already done.",
)
def ingest_cmd(
    config_path: Path,
    output_path: Path | None,
    force: bool,
) -> None:
    """Ingest nd2/tif inputs → normalized per-FOV membrane TIFs in 01_ingest/.

    \b
    Outputs (in <output>/01_ingest/):
        <fov_id>_membrane.tif   uint16 normalized membrane channel
    Stage status written to <output>/stage_status/ingest.json.
    Skipped for input.mode = 'masks' (no ingest needed).
    """
    from quantipy_polarity.config import InputMasks
    from quantipy_polarity.io.ingest import ingest_fovs
    from quantipy_polarity.pipeline.state import (
        config_hash,
        read_stage_state,
        write_stage_state,
    )
    from quantipy_polarity.pipeline.dag import should_skip_stage

    cfg = Config.from_yaml(config_path)
    out_dir = Path(output_path or cfg.project.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(cfg.input, InputMasks):
        click.echo(
            "input.mode = 'masks': ingest is not needed — "
            "your masks and membranes are already on disk. "
            "Run `quantipy polarity` next."
        )
        return

    chash = config_hash(cfg)
    state = read_stage_state(out_dir, "ingest")
    if should_skip_stage(state, chash, force=force):
        click.echo("Ingest already done (matching config_hash). Use --force to re-run.")
        return

    write_stage_state(out_dir, "ingest", "running", cfg=cfg)
    try:
        fov_ids = ingest_fovs(cfg, out_dir)
        write_stage_state(
            out_dir, "ingest", "done",
            cfg=cfg,
            preserve_started_at=True,
            output_paths=[str(out_dir / "01_ingest" / f"{fid}_membrane.tif") for fid in fov_ids],
        )
    except Exception:
        write_stage_state(out_dir, "ingest", "failed", cfg=cfg, preserve_started_at=True)
        raise

    click.echo(f"Ingest complete. {len(fov_ids)} FOV(s) written to {out_dir / '01_ingest'}")
