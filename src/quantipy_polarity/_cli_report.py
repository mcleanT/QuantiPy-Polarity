"""Real `quantipy report` — regenerate HTML report from a completed run directory.

Does not re-run any pipeline stage. Reads whatever outputs currently exist
in the run directory. Useful after editing config or adding annotations.
"""

from __future__ import annotations

from pathlib import Path

import click

from quantipy_polarity.cli import main


@main.command(
    "report",
    short_help="[Advanced] Regenerate HTML report from a run directory",
)
@click.option(
    "--results",
    "results_dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Run directory (the output directory from quantipy run).",
)
@click.option(
    "--output",
    "output_html",
    required=False,
    type=click.Path(path_type=Path),
    default=None,
    help="Output HTML path. Default: <results>/report.html.",
)
@click.option(
    "--config",
    "config_path",
    required=False,
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional config YAML for project.name injection.",
)
def report_cmd(
    results_dir: Path,
    output_html: Path | None,
    config_path: Path | None,
) -> None:
    """Regenerate the self-contained HTML report from an existing run directory.

    Reads 05_aggregated/per_cell.parquet, 06_plots/, and stage_status/ from
    <results>. Does NOT re-run segmentation, polarity, or any other stage.

    Output is a single self-contained HTML file with all images base64-embedded.
    """
    from quantipy_polarity.config import Config
    from quantipy_polarity.report.build import build_report

    cfg: "Config | None" = None
    if config_path is not None:
        cfg = Config.from_yaml(config_path)

    out_html = output_html or (results_dir / "report.html")
    build_report(results_dir, out_html, cfg=cfg)
    click.echo(f"Report written: {out_html}")
