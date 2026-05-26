"""Real `quantipy validate` command (Phase 6).

Regenerates the QP-vs-Python comparison figure from the bundled synthetic
validation parquets committed to data/validation/.

Parquet resolution order (editable install / dev only in v0.1.0):
  1. $QUANTIPY_VALIDATION_DIR env var (override for testing or custom data)
  2. {repo_root}/data/validation/  (resolved relative to this file's location)

For a pip-installed non-editable package, the parquets are not bundled and
the command will raise a helpful error. This will be fixed in a minor release
by moving data/ into the package tree.
"""

from __future__ import annotations

import os
from pathlib import Path

import click

from quantipy_polarity.cli import main


_DEFAULT_OUTPUT = Path.home() / ".cache" / "quantipy" / "validation"


def _find_validation_data_dir() -> Path:
    """Resolve bundled validation parquets directory."""
    # 1. Env-var override (tests + custom datasets)
    env = os.environ.get("QUANTIPY_VALIDATION_DIR")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
        raise click.ClickException(
            f"QUANTIPY_VALIDATION_DIR={env!r} does not exist or is not a directory."
        )
    # 2. Repo-relative path (editable dev install)
    candidate = (
        Path(__file__).resolve().parent.parent.parent / "data" / "validation"
    )
    if candidate.is_dir() and (candidate / "qp_results.parquet").exists():
        return candidate
    raise click.ClickException(
        "Could not find bundled validation parquets. "
        "Expected data/validation/qp_results.parquet relative to the repo root. "
        "Run `git clone https://github.com/mcleanT/QuantiPy-Polarity` and "
        "`pip install -e .[dev]` to get the bundled data, or set "
        "QUANTIPY_VALIDATION_DIR to a directory containing qp_results.parquet "
        "and python_results.parquet."
    )


@main.command("validate")
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    help="Directory to write validation_qp_vs_python.pdf/.png and metrics JSON. "
    f"Defaults to {_DEFAULT_OUTPUT}.",
)
@click.option(
    "--tolerance",
    "-t",
    type=float,
    default=5.0,
    show_default=True,
    help="Max centroid distance (pixels) for NN cell matching.",
)
def validate_cmd(output: Path | None, tolerance: float) -> None:
    """Regenerate QP-vs-Python comparison figure from bundled synthetic data."""
    try:
        from quantipy_polarity.validation.qp_vs_python import run_validation
    except ImportError:
        raise click.ClickException(
            "validate requires matplotlib — install with: pip install -e .[pipeline]"
        )

    output_dir = output or _DEFAULT_OUTPUT
    data_dir = _find_validation_data_dir()
    qp_path = data_dir / "qp_results.parquet"
    py_path = data_dir / "python_results.parquet"

    click.echo(f"Loading validation data from {data_dir} ...")
    result = run_validation(qp_path, py_path, output_dir, tolerance_px=tolerance)

    click.echo(f"\nValidation complete ({result.n_matched} matched cells):")
    click.echo(
        f"  Magnitude  R² = {result.r2_magnitude:.4f}  slope = {result.slope_magnitude:.4f}"
    )
    click.echo(
        f"  Axis angle R² = {result.r2_angle:.4f}  slope = {result.slope_angle:.4f}"
    )
    click.echo(f"  Figures saved to {output_dir}")

    if result.r2_magnitude < 0.85:
        raise click.ClickException(
            f"Magnitude R² = {result.r2_magnitude:.4f} is below threshold 0.85. "
            "The validation data may be corrupted."
        )
