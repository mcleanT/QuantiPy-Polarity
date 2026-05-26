"""`quantipy polarity` and `quantipy aggregate` — real subcommands (replacing Phase 1 stubs).

Registers on import (see cli.py footer).
"""

from __future__ import annotations

from pathlib import Path

import click

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config
from quantipy_polarity.io.masks import iter_mask_dataset
from quantipy_polarity.polarity.boundary_pca import compute_cell_polarity
from quantipy_polarity.polarity.per_cell import aggregate_experiment, per_fov_to_parquet


@main.command(
    "polarity", short_help="Label masks + membrane → per-cell axes (per-FOV parquets)"
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to YAML config (input.mode must be 'masks' in Phase 2).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory (per-FOV parquets land in <output>/03_polarity/per_fov/).",
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing per-FOV parquets.")
@click.option(
    "--condition", default=None, help="Optional condition label for all FOVs."
)
def polarity_cmd(
    config: Path, output: Path, overwrite: bool, condition: str | None
) -> None:
    """Compute per-cell polarity for every paired FOV under the configured masks dir.

    In v0.1.0 only `input.mode = masks` is supported here. Other modes will land in Phase 3.
    """
    cfg = Config.from_yaml(config)
    if cfg.input.mode != "masks":
        raise click.ClickException(
            f"`quantipy polarity` only supports input.mode='masks' in v0.1.0; got '{cfg.input.mode}'. "
            "Use `quantipy run` once Phase 3+ lands for nd2/tif inputs."
        )
    per_fov_dir = Path(output) / "03_polarity" / "per_fov"
    per_fov_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fov in iter_mask_dataset(
        membrane_dir=cfg.input.path,
        masks_dir=cfg.input.masks_dir,
        channel_membrane=cfg.input.channel_membrane,
    ):
        result = compute_cell_polarity(fov.membrane, fov.label_mask)
        out_path = per_fov_dir / f"{fov.fov_id}.parquet"
        per_fov_to_parquet(
            result,
            fov_id=fov.fov_id,
            label_mask=fov.label_mask,
            out_path=out_path,
            condition=condition,
            overwrite=overwrite,
        )
        written.append(out_path)
        click.echo(f"  wrote {out_path}")
    click.echo(f"Wrote {len(written)} per-FOV parquets under {per_fov_dir}")


@main.command("aggregate", short_help="Per-FOV parquets → experiment parquet")
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Directory containing per-FOV parquets (e.g. results/03_polarity/per_fov).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output path for the experiment-wide parquet.",
)
@click.option(
    "--overwrite", is_flag=True, help="Overwrite existing experiment parquet."
)
def aggregate_cmd(input_dir: Path, output: Path, overwrite: bool) -> None:
    """Concatenate every *.parquet in --input into a single experiment-wide parquet."""
    parquets = sorted(Path(input_dir).glob("*.parquet"))
    if not parquets:
        raise click.ClickException(f"No *.parquet files under {input_dir}")
    aggregate_experiment(parquets, Path(output), overwrite=overwrite)
    click.echo(f"Aggregated {len(parquets)} FOVs into {output}")
