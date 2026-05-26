"""quantipy debug — write a self-contained per-cell HTML viewer.

Usage:
    quantipy debug --results ./demo_results
    quantipy debug --results ./demo_results --output /tmp/viewer.html --fov fov_A
"""

from __future__ import annotations

from pathlib import Path

import click

from quantipy_polarity.cli import main
from quantipy_polarity.interactive import build_viewer


@main.command("debug")
@click.option(
    "--results",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to a completed quantipy run directory.",
)
@click.option(
    "--output",
    default=None,
    type=click.Path(path_type=Path),
    help="Output HTML path. Default: <results>/viewer.html",
)
@click.option(
    "--fov",
    default=None,
    type=str,
    help="Limit viewer to a single FOV ID (default: all FOVs).",
)
def debug_cmd(results: Path, output: Path | None, fov: str | None) -> None:
    """Write a self-contained HTML per-cell viewer for a completed run."""
    if output is None:
        output = results / "viewer.html"

    try:
        build_viewer(results, output, fov=fov)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Viewer written → {output}")
    click.echo("Open in any browser: no server required.")
