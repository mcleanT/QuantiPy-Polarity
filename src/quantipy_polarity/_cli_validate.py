"""Real `quantipy validate` command (Phase 6, updated v0.1.3).

Regenerates the QP-vs-Python comparison figure from the bundled real
validation parquet shipped inside the package at
``quantipy_polarity/data/validation/qp_vs_python_real.parquet``.

This file contains 94,386 pre-paired cells from a 25 h migration
experiment (clones C10 + D11, 28 FOVs) with columns:
    clone, fov, cell_identity,
    qp_magnitude, py_magnitude, qp_angle_deg, py_angle_deg

Parquet resolution order:
  1. $QUANTIPY_VALIDATION_DIR env var (override for testing or custom data)
     — must point to a directory containing ``qp_vs_python_real.parquet``
     OR the legacy pair ``qp_results.parquet`` + ``python_results.parquet``
  2. Package-relative path: quantipy_polarity/data/validation/
     (works for both editable installs and non-editable wheel installs)
"""

from __future__ import annotations

import os
from pathlib import Path

import click

from quantipy_polarity.cli import main


_DEFAULT_OUTPUT = Path.home() / ".cache" / "quantipy" / "validation"

# Package-bundled validation data directory (works for editable and wheel installs).
_PACKAGE_DATA_DIR = Path(__file__).resolve().parent / "data" / "validation"


def _find_validation_parquet() -> tuple[Path, Path | None]:
    """Resolve bundled validation parquet(s).

    Returns (combined_path, None) for the new single-file format, or
    (qp_path, py_path) for the legacy two-file format.
    """
    # 1. Env-var override (tests + custom datasets)
    env = os.environ.get("QUANTIPY_VALIDATION_DIR")
    data_dir = Path(env) if env else _PACKAGE_DATA_DIR

    if env and not data_dir.is_dir():
        raise click.ClickException(
            f"QUANTIPY_VALIDATION_DIR={env!r} does not exist or is not a directory."
        )

    # Prefer combined parquet
    combined = data_dir / "qp_vs_python_real.parquet"
    if combined.exists():
        return combined, None

    # Fall back to legacy two-file format
    qp_path = data_dir / "qp_results.parquet"
    py_path = data_dir / "python_results.parquet"
    if qp_path.exists() and py_path.exists():
        return qp_path, py_path

    raise click.ClickException(
        "Could not find bundled validation parquet inside the installed package. "
        "Expected quantipy_polarity/data/validation/qp_vs_python_real.parquet. "
        "Reinstall the package or set QUANTIPY_VALIDATION_DIR to a directory "
        "containing qp_vs_python_real.parquet."
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
    help="(Legacy two-file mode only) Max centroid distance (pixels) for NN cell matching.",
)
def validate_cmd(output: Path | None, tolerance: float) -> None:
    """Regenerate QP-vs-Python comparison figure from bundled real validation data.

    Ships 94,386 pre-paired cells from a 25 h migration experiment
    (clones C10 + D11). See docs/validation.md for methodology.
    """
    try:
        from quantipy_polarity.validation.qp_vs_python import run_validation
    except ImportError:
        raise click.ClickException(
            "validate requires matplotlib — install with: pip install -e .[pipeline]"
        )

    output_dir = output or _DEFAULT_OUTPUT
    primary, secondary = _find_validation_parquet()

    if secondary is None:
        click.echo(f"Loading real validation data from {primary} ...")
        result = run_validation(primary, output_dir)
    else:
        click.echo(f"Loading legacy validation data from {primary.parent} ...")
        result = run_validation(primary, secondary, output_dir, tolerance_px=tolerance)

    click.echo(f"\nValidation complete ({result.n_matched:,} cells):")
    click.echo(
        f"  Magnitude  R² = {result.r2_magnitude:.4f}  slope = {result.slope_magnitude:.4f}"
    )
    click.echo(
        f"  Axis angle R² = {result.r2_angle:.4f}  slope = {result.slope_angle:.4f}"
    )
    click.echo(f"  Figures saved to {output_dir}")

    # Threshold reflects real data (lower R² is honest, not a failure)
    if result.r2_magnitude < 0.70:
        raise click.ClickException(
            f"Magnitude R² = {result.r2_magnitude:.4f} is below threshold 0.70. "
            "The validation data may be corrupted."
        )
