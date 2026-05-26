"""quantipy analyze <subcommand> — curated experimental analyses (experimental API).

Subcommands:
    polarity-by-condition   Boxplot + Mann-Whitney U
    magnitude-vs-distance   Scatter + Theil-Sen robust regression
"""

from __future__ import annotations

from pathlib import Path

import click

from quantipy_polarity.cli import main


@main.group("analyze", short_help="[Advanced] Run a curated experimental analysis")
def analyze_group() -> None:
    """Run a curated experimental analysis (experimental API — may change).

    Use ``quantipy analyze <name> --help`` for subcommand options.
    """


@analyze_group.command("polarity-by-condition")
@click.option(
    "--per-cell",
    "per_cell_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to per_cell.parquet from a quantipy run.",
)
@click.option(
    "--metadata",
    "metadata_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="CSV or TSV with columns [fov_id, condition] (or --condition-col).",
)
@click.option(
    "--output-dir",
    default="./analyze_results",
    type=click.Path(path_type=Path),
    show_default=True,
    help="Directory for output PDF + JSON.",
)
@click.option(
    "--condition-col",
    default="condition",
    show_default=True,
    help="Column name in metadata for the grouping variable.",
)
@click.option(
    "--magnitude-col",
    default="magnitude",
    show_default=True,
    help="Column name in per_cell.parquet for polarity magnitude.",
)
def polarity_by_condition_cmd(
    per_cell_path: Path,
    metadata_path: Path,
    output_dir: Path,
    condition_col: str,
    magnitude_col: str,
) -> None:
    """Boxplot of polarity magnitude grouped by experimental condition."""
    from quantipy_polarity.experimental.analyses.polarity_by_condition import (
        run_polarity_by_condition,
    )

    try:
        results = run_polarity_by_condition(
            per_cell_path,
            metadata_path,
            output_dir,
            condition_col=condition_col,
            magnitude_col=magnitude_col,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    p = results.get("p_value")
    p_str = f"{p:.3g}" if p is not None else "n/a"
    click.echo(f"Groups: {results['groups']}")
    click.echo(f"N per group: {results['n_per_group']}")
    click.echo(f"Medians: {[round(m, 4) for m in results['medians']]}")
    click.echo(f"p-value ({results.get('test_used', '—')}): {p_str}")
    click.echo(f"Output → {output_dir}/")


@analyze_group.command("magnitude-vs-distance")
@click.option(
    "--per-cell",
    "per_cell_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to per_cell.parquet from a quantipy run.",
)
@click.option(
    "--output-dir",
    default="./analyze_results",
    type=click.Path(path_type=Path),
    show_default=True,
    help="Directory for output PDF + JSON.",
)
@click.option(
    "--distance-col",
    default="dist_to_front_px",
    show_default=True,
    help="Column name for distance to migration front.",
)
@click.option(
    "--magnitude-col",
    default="magnitude",
    show_default=True,
    help="Column name for polarity magnitude.",
)
@click.option(
    "--max-cells",
    default=5000,
    show_default=True,
    type=int,
    help="Maximum cells to plot (random subsample for legibility).",
)
def magnitude_vs_distance_cmd(
    per_cell_path: Path,
    output_dir: Path,
    distance_col: str,
    magnitude_col: str,
    max_cells: int,
) -> None:
    """Scatter of polarity magnitude vs distance-to-front with robust regression."""
    from quantipy_polarity.experimental.analyses.magnitude_vs_distance import (
        run_magnitude_vs_distance,
    )

    try:
        results = run_magnitude_vs_distance(
            per_cell_path,
            output_dir,
            magnitude_col=magnitude_col,
            distance_col=distance_col,
            max_cells=max_cells,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if not results.get("distance_col_found"):
        click.echo(f"Note: {results.get('note', '')}")
        click.echo(f"JSON written → {output_dir}/magnitude_vs_distance_results.json")
        return

    click.echo(f"N cells: {results['n_cells']}")
    click.echo(f"Theil-Sen slope: {results['slope']:.4f}")
    click.echo(f"R²: {results['r_squared']:.4f}")
    click.echo(f"Output → {output_dir}/")
