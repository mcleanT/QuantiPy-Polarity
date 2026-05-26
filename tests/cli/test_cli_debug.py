"""CLI tests for `quantipy debug`.

Uses CliRunner + mocks — no real pipeline outputs or browser opening.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_minimal_results(results_dir: Path) -> Path:
    """Write a minimal results layout that build_viewer accepts."""
    agg_dir = results_dir / "05_aggregated"
    agg_dir.mkdir(parents=True)

    df = pd.DataFrame(
        {
            "fov_id": ["fov_A", "fov_A", "fov_B"],
            "cell_id": [1, 2, 3],
            "qp_magnitude": [0.5, 0.6, 0.7],
            "qp_axis_deg": [10.0, 20.0, 30.0],
        }
    )
    df.to_parquet(agg_dir / "per_cell.parquet", index=False)
    return results_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_debug_writes_html(tmp_path: Path) -> None:
    """quantipy debug --results <results_dir> writes viewer.html in the results dir."""
    results = _write_minimal_results(tmp_path / "results")
    runner = CliRunner()
    result = runner.invoke(main, ["debug", "--results", str(results)])
    assert result.exit_code == 0, result.output
    assert (results / "viewer.html").exists()


def test_debug_custom_output_path(tmp_path: Path) -> None:
    """--output /tmp/custom.html writes to the specified path."""
    results = _write_minimal_results(tmp_path / "results")
    custom_out = tmp_path / "custom.html"
    runner = CliRunner()
    result = runner.invoke(
        main, ["debug", "--results", str(results), "--output", str(custom_out)]
    )
    assert result.exit_code == 0, result.output
    assert custom_out.exists()


def test_debug_fov_flag(tmp_path: Path) -> None:
    """--fov fov_A produces HTML containing 'fov_A'."""
    results = _write_minimal_results(tmp_path / "results")
    out_path = tmp_path / "viewer_fov.html"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["debug", "--results", str(results), "--output", str(out_path), "--fov", "fov_A"],
    )
    assert result.exit_code == 0, result.output
    assert out_path.exists()
    html_text = out_path.read_text()
    assert "fov_A" in html_text


def test_debug_missing_results_dir_exits_nonzero(tmp_path: Path) -> None:
    """Passing a non-existent path exits with code != 0."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["debug", "--results", str(tmp_path / "does_not_exist")]
    )
    assert result.exit_code != 0


def test_debug_missing_parquet_exits_nonzero(tmp_path: Path) -> None:
    """A results dir that exists but has no parquet exits with code != 0."""
    results = tmp_path / "empty_results"
    results.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["debug", "--results", str(results)])
    assert result.exit_code != 0


def test_debug_no_browser_opened(tmp_path: Path) -> None:
    """Output message says 'no server required' and webbrowser.open is NOT called."""
    results = _write_minimal_results(tmp_path / "results")
    runner = CliRunner()
    with patch("webbrowser.open") as mock_open:
        result = runner.invoke(main, ["debug", "--results", str(results)])
    assert result.exit_code == 0, result.output
    assert "no server required" in result.output
    mock_open.assert_not_called()


def test_debug_help_flag() -> None:
    """quantipy debug --help exits 0 and mentions --results."""
    runner = CliRunner()
    result = runner.invoke(main, ["debug", "--help"])
    assert result.exit_code == 0
    assert "--results" in result.output
