"""CLI tests for `quantipy analyze` and its subcommands.

Uses CliRunner + synthetic data — no real pipeline outputs required.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from click.testing import CliRunner

from quantipy_polarity.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_per_cell_parquet(path: Path, *, include_distance: bool = False) -> Path:
    """Write a minimal per_cell.parquet that the analyze commands accept."""
    rng = np.random.default_rng(42)
    n = 40
    data: dict = {
        "fov_id": [f"fov_{i % 4:02d}" for i in range(n)],
        "cell_id": list(range(n)),
        "magnitude": rng.uniform(0.1, 0.9, size=n).tolist(),
        "axis_deg": rng.uniform(0, 360, size=n).tolist(),
    }
    if include_distance:
        data["dist_to_front_px"] = rng.uniform(0, 200, size=n).tolist()
    df = pd.DataFrame(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def _write_metadata_csv(path: Path) -> Path:
    """Write a minimal metadata CSV with fov_id + condition columns."""
    meta = pd.DataFrame(
        {
            "fov_id": [f"fov_{i:02d}" for i in range(4)],
            "condition": ["ctrl", "ctrl", "treated", "treated"],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    meta.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_analyze_help() -> None:
    """quantipy analyze --help exits 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "--help"])
    assert result.exit_code == 0


def test_analyze_polarity_by_condition_help() -> None:
    """quantipy analyze polarity-by-condition --help exits 0 and mentions --per-cell."""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "polarity-by-condition", "--help"])
    assert result.exit_code == 0
    assert "--per-cell" in result.output


def test_analyze_magnitude_vs_distance_help() -> None:
    """quantipy analyze magnitude-vs-distance --help exits 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "magnitude-vs-distance", "--help"])
    assert result.exit_code == 0


def test_polarity_by_condition_missing_per_cell_exits_nonzero(tmp_path: Path) -> None:
    """Invoking polarity-by-condition with missing --per-cell exits != 0 with a clean error."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "analyze",
            "polarity-by-condition",
            "--per-cell",
            str(tmp_path / "nonexistent.parquet"),
            "--metadata",
            str(tmp_path / "meta.csv"),
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code != 0


def test_polarity_by_condition_runs_end_to_end(tmp_path: Path) -> None:
    """With valid synthetic parquet + metadata CSV, exits 0 and writes PDF + JSON."""
    per_cell = _write_per_cell_parquet(tmp_path / "per_cell.parquet")
    metadata = _write_metadata_csv(tmp_path / "meta.csv")
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "analyze",
            "polarity-by-condition",
            "--per-cell",
            str(per_cell),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "polarity_by_condition.pdf").exists()
    assert (out_dir / "polarity_by_condition_results.json").exists()


def test_magnitude_vs_distance_runs_end_to_end(tmp_path: Path) -> None:
    """With synthetic parquet including distance col, exits 0."""
    per_cell = _write_per_cell_parquet(
        tmp_path / "per_cell.parquet", include_distance=True
    )
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "analyze",
            "magnitude-vs-distance",
            "--per-cell",
            str(per_cell),
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output


def test_magnitude_vs_distance_no_distance_col_exits_zero(tmp_path: Path) -> None:
    """Without distance col, exits 0 (graceful) and prints the note."""
    per_cell = _write_per_cell_parquet(
        tmp_path / "per_cell.parquet", include_distance=False
    )
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "analyze",
            "magnitude-vs-distance",
            "--per-cell",
            str(per_cell),
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Note:" in result.output


def test_analyze_unknown_subcommand_shows_help() -> None:
    """quantipy analyze unknown-name exits non-zero with usage help."""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "unknown-name"])
    assert result.exit_code != 0
    # Click prints "No such command" for unknown subcommands
    output_lower = result.output.lower()
    assert "no such command" in output_lower or "usage" in output_lower
