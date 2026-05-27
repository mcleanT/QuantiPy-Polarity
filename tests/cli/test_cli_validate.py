"""CLI tests for `quantipy validate`."""

import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity.validation.synthetic_data import generate_validation_parquets


@pytest.fixture()
def val_dir(tmp_path):
    """Write a combined qp_vs_python_real.parquet fixture to tmp_path."""
    qp_df, py_df = generate_validation_parquets()
    combined = qp_df[["fov_id", "cell_id", "qp_magnitude", "qp_axis_deg"]].copy()
    combined["py_magnitude"] = py_df["py_magnitude"].values
    combined["py_axis_deg"] = py_df["py_axis_deg"].values
    combined = combined.rename(
        columns={"qp_axis_deg": "qp_angle_deg", "py_axis_deg": "py_angle_deg"}
    )
    combined.to_parquet(tmp_path / "qp_vs_python_real.parquet", index=False)
    return tmp_path


def test_validate_runs_successfully(val_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTIPY_VALIDATION_DIR", str(val_dir))
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--output", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    # New output format: "Magnitude R²=..." and "Angle: median Δθ=..."
    assert "R²" in result.output or "r2" in result.output.lower()
    assert "median" in result.output.lower() or "Δθ" in result.output
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


def test_validate_help():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--tolerance" in result.output
