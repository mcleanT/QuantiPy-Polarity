"""Tests for the top-level `quantipy --help` and `--version`."""
from click.testing import CliRunner

from quantipy_polarity import __version__
from quantipy_polarity.cli import main


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_both_groups() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Primary commands" in result.output
    assert "Advanced commands" in result.output


def test_help_lists_primary_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    for cmd in ("init-config", "download-demo", "run", "debug", "validate"):
        assert cmd in result.output


def test_help_lists_advanced_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    for cmd in ("ingest", "segment", "polarity", "front", "aggregate", "plot", "report", "analyze"):
        assert cmd in result.output


def test_short_help_flag_works() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["-h"])
    assert result.exit_code == 0
    assert "QuantiPy Polarity" in result.output
