"""CLI tests for `quantipy report`.

Uses CliRunner + mocks — no real report generation or data loading.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_report_cmd_requires_results(tmp_path: Path) -> None:
    """Invoking report without --results must fail (non-zero exit)."""
    runner = CliRunner()
    result = runner.invoke(main, ["report"])
    assert result.exit_code != 0


def test_report_cmd_calls_build_report(tmp_path: Path) -> None:
    """Invoking report with a valid --results dir should call build_report."""
    results_dir = tmp_path / "run_output"
    results_dir.mkdir(parents=True)

    runner = CliRunner()
    with patch("quantipy_polarity.report.build.build_report") as mock_build:
        result = runner.invoke(main, ["report", "--results", str(results_dir)])
    assert result.exit_code == 0, result.output
    mock_build.assert_called_once()
    args, kwargs = mock_build.call_args
    # First positional arg is results_dir
    assert args[0] == results_dir


def test_report_cmd_default_output_path(tmp_path: Path) -> None:
    """Default output_html should be <results>/report.html."""
    results_dir = tmp_path / "run_output"
    results_dir.mkdir(parents=True)

    runner = CliRunner()
    with patch("quantipy_polarity.report.build.build_report") as mock_build:
        result = runner.invoke(main, ["report", "--results", str(results_dir)])
    assert result.exit_code == 0, result.output
    args, kwargs = mock_build.call_args
    # Second positional arg is output_html
    assert args[1] == results_dir / "report.html"


def test_report_cmd_custom_output_path(tmp_path: Path) -> None:
    """--output flag should pass a custom path to build_report."""
    results_dir = tmp_path / "run_output"
    results_dir.mkdir(parents=True)
    custom_html = Path("/tmp/x.html")

    runner = CliRunner()
    with patch("quantipy_polarity.report.build.build_report") as mock_build:
        result = runner.invoke(
            main,
            [
                "report",
                "--results",
                str(results_dir),
                "--output",
                str(custom_html),
            ],
        )
    assert result.exit_code == 0, result.output
    args, kwargs = mock_build.call_args
    assert args[1] == custom_html
