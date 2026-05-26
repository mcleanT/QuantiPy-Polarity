"""CLI tests for `quantipy run`.

Uses CliRunner + mocks — no real pipeline execution or data loading.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from quantipy_polarity.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_masks_config(tmp_path: Path, output_dir: Path | None = None) -> Path:
    out = output_dir or (tmp_path / "results")
    cfg_text = f"""
project:
  name: test_run
  output_dir: {out}
input:
  mode: masks
  path: {tmp_path / "masks"}
  masks_dir: {tmp_path / "masks_dir"}
  pixel_size_um: 0.65
""".strip()
    p = tmp_path / "config.yaml"
    p.write_text(cfg_text)
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_cmd_requires_config(tmp_path: Path) -> None:
    """Invoking run without --config must fail (non-zero exit)."""
    runner = CliRunner()
    result = runner.invoke(main, ["run"])
    assert result.exit_code != 0


def test_run_cmd_nonempty_dir_without_resume_or_force_exits_nonzero(
    tmp_path: Path,
) -> None:
    """Non-empty output dir without --resume or --force → ClickException (exit 1)."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    # Create a sentinel file so the directory is non-empty
    (out_dir / "sentinel.txt").write_text("occupied")

    cfg = _write_masks_config(tmp_path, output_dir=out_dir)
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--config", str(cfg)])
    assert result.exit_code != 0


def test_run_cmd_force_calls_run_pipeline(tmp_path: Path) -> None:
    """--force invocation should call run_pipeline with force=True."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg = _write_masks_config(tmp_path, output_dir=out_dir)

    runner = CliRunner()
    with patch("quantipy_polarity.pipeline.run.run_pipeline") as mock_run:
        result = runner.invoke(main, ["run", "--config", str(cfg), "--force"])
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("force") is True


def test_run_cmd_resume_calls_run_pipeline(tmp_path: Path) -> None:
    """--resume invocation should call run_pipeline with force=False."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg = _write_masks_config(tmp_path, output_dir=out_dir)

    runner = CliRunner()
    with patch("quantipy_polarity.pipeline.run.run_pipeline") as mock_run:
        result = runner.invoke(main, ["run", "--config", str(cfg), "--resume"])
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("force") is False


def test_run_cmd_stage_flag_passes_list(tmp_path: Path) -> None:
    """--stage flags should be passed as a list, canonicalized by filter_stages."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg = _write_masks_config(tmp_path, output_dir=out_dir)

    runner = CliRunner()
    with patch("quantipy_polarity.pipeline.run.run_pipeline") as mock_run:
        result = runner.invoke(
            main,
            [
                "run",
                "--config",
                str(cfg),
                "--force",
                "--stage",
                "polarity",
                "--stage",
                "aggregate",
            ],
        )
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    # filter_stages preserves canonical order: polarity before aggregate
    assert kwargs.get("stages") == ["polarity", "aggregate"]


def test_run_cmd_runtime_error_exits_nonzero(tmp_path: Path) -> None:
    """RuntimeError from run_pipeline → exit code 1 with error text in output."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg = _write_masks_config(tmp_path, output_dir=out_dir)

    runner = CliRunner()
    with patch(
        "quantipy_polarity.pipeline.run.run_pipeline",
        side_effect=RuntimeError("oops"),
    ):
        result = runner.invoke(main, ["run", "--config", str(cfg), "--force"])
    assert result.exit_code != 0
    assert "oops" in result.output
