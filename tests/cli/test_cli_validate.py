"""CLI tests for `quantipy validate`."""

import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity.validation.synthetic_data import write_validation_parquets


@pytest.fixture()
def val_dir(tmp_path):
    write_validation_parquets(tmp_path)
    return tmp_path


def test_validate_runs_successfully(val_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTIPY_VALIDATION_DIR", str(val_dir))
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--output", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    assert "R²" in result.output or "r2" in result.output.lower()
    assert (tmp_path / "out" / "validation_qp_vs_python.pdf").exists()


def test_validate_default_output(val_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTIPY_VALIDATION_DIR", str(val_dir))
    monkeypatch.setenv("HOME", str(tmp_path))  # redirect ~/.cache
    runner = CliRunner()
    result = runner.invoke(main, ["validate"])
    assert result.exit_code == 0, result.output


def test_validate_missing_data_dir(monkeypatch):
    monkeypatch.setenv("QUANTIPY_VALIDATION_DIR", "/nonexistent/path/abc123")
    runner = CliRunner()
    result = runner.invoke(main, ["validate"])
    assert result.exit_code != 0


def test_validate_custom_tolerance(val_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTIPY_VALIDATION_DIR", str(val_dir))
    runner = CliRunner()
    result = runner.invoke(
        main, ["validate", "--tolerance", "10.0", "--output", str(tmp_path / "out")]
    )
    assert result.exit_code == 0, result.output


def test_validate_help():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--tolerance" in result.output
