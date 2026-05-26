"""Real `quantipy run` — single-shot pipeline orchestrator.

Behavior:
  - Default (no flags): refuses to overwrite a non-empty output dir.
    Error message suggests --resume or --force.
  - --resume: skips stages already in 'done' state with matching config_hash.
  - --force: ignores all stage caches; re-runs from scratch.
  - --stage STAGE (repeatable): run only the named stage(s) in canonical order.
"""

from __future__ import annotations

from pathlib import Path

import click
import structlog

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config

log = structlog.get_logger()


@main.command("run", short_help="Single-shot: input → all outputs")
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
    "--resume",
    is_flag=True,
    default=False,
    help="Skip stages already marked done with matching config hash.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Ignore stage caches; re-run all stages from scratch.",
)
@click.option(
    "--stage",
    "stages",
    multiple=True,
    default=None,
    help="Run only this stage (repeatable). Default: all stages.",
)
def run_cmd(
    config_path: Path,
    output_path: Path | None,
    resume: bool,
    force: bool,
    stages: tuple[str, ...],
) -> None:
    """Single-shot pipeline: input → segmentation → polarity → front → figures → report.

    \b
    Modes:
      (default)  Refuses to overwrite non-empty output dir.
      --resume   Skip stages already done with matching config hash.
      --force    Wipe stage cache, re-run everything.
      --stage    Run only named stage(s) in canonical order (Advanced).

    Stage order: ingest → segment → polarity → front → aggregate → plot → report
    """
    from quantipy_polarity.pipeline.run import run_pipeline

    cfg = Config.from_yaml(config_path)
    out_dir = Path(output_path or cfg.project.output_dir)

    # Safety check: refuse to overwrite without explicit --resume or --force
    if out_dir.exists() and any(out_dir.iterdir()):
        if not resume and not force:
            raise click.ClickException(
                f"Output directory {out_dir} is non-empty. "
                "Use --resume to continue from the last successful stage, "
                "or --force to wipe and restart."
            )

    stage_list: list[str] | None = list(stages) if stages else None

    try:
        run_pipeline(cfg, out_dir, force=force, stages=stage_list)
    except RuntimeError as exc:
        # run_pipeline already wrote status=failed and logged the error
        raise click.ClickException(str(exc)) from exc

    click.echo(f"\nPipeline complete. Report: {out_dir / 'report.html'}")
