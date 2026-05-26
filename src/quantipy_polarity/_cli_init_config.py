"""`quantipy init-config` — write a mode-specific YAML scaffold.

Registers itself on import (see cli.py footer).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import click

from quantipy_polarity.cli import main
from quantipy_polarity.config import (
    Config,
    InputMasks,
    InputND2,
    InputTIF,
    ProjectConfig,
)


def _build_config(mode: Literal["nd2", "tif", "masks"]) -> Config:
    project = ProjectConfig(name="my_experiment", output_dir=Path("./results"))
    if mode == "nd2":
        return Config(
            project=project,
            input=InputND2(
                mode="nd2",
                path=Path("./raw"),
                z_policy="mip",
                channel_membrane=1,
                channel_segmentation=1,
                pixel_size_um=0.65,
            ),
        )
    if mode == "tif":
        return Config(
            project=project,
            input=InputTIF(
                mode="tif",
                path=Path("./raw"),
                z_policy="none",
                channel_membrane=0,
                channel_segmentation=0,
                pixel_size_um=0.65,
            ),
        )
    return Config(
        project=project,
        input=InputMasks(
            mode="masks",
            path=Path("./membrane_tifs"),
            masks_dir=Path("./label_masks"),
            pixel_size_um=0.65,
        ),
    )


@main.command("init-config", short_help="Scaffold a config YAML for a given input mode")
@click.option(
    "--mode",
    type=click.Choice(["nd2", "tif", "masks"], case_sensitive=False),
    required=True,
    help="Which input mode the config should be wired for.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("config.yaml"),
    show_default=True,
    help="Path to write the YAML.",
)
@click.option("--force", is_flag=True, help="Overwrite if --output already exists.")
def init_config_cmd(mode: str, output: Path, force: bool) -> None:
    """Write a Pydantic-valid YAML scaffold for the chosen input mode.

    Example: quantipy init-config --mode masks --output config.yaml
    """
    if output.exists() and not force:
        raise click.ClickException(
            f"{output} already exists. Pass --force to overwrite."
        )
    cfg = _build_config(mode.lower())  # type: ignore[arg-type]
    cfg.to_yaml(output)
    click.echo(f"Wrote {output} (mode={mode})")
