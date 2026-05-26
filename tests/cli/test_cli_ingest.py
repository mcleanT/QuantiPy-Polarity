"""CLI tests for `quantipy ingest`.

Uses CliRunner + mocks — no real nd2/tif loading or pipeline execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _write_masks_config(tmp_path: Path, output_dir: Path | None = None) -> Path:
    out = output_dir or (tmp_path / "results")
    cfg_text = f"""
project:
  name: test_ingest
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


def _write_tif_config(tmp_path: Path, output_dir: Path | None = None) -> Path:
    out = output_dir or (tmp_path / "results")
    input_path = tmp_path / "input_tifs"
    input_path.mkdir(parents=True, exist_ok=True)
    cfg_text = f"""
project:
  name: test_ingest_tif
  output_dir: {out}
input:
  mode: tif
  path: {input_path}
  channel_membrane: 0
  channel_segmentation: 1
  pixel_size_um: 0.65
""".strip()
    p = tmp_path / "config_tif.yaml"
    p.write_text(cfg_text)
    return p


def _write_done_state(out_dir: Path, cfg_hash: str) -> None:
    """Write a stage_status/ingest.json in 'done' state with the given config_hash."""
    status_dir = out_dir / "stage_status"
    status_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "stage": "ingest",
        "status": "done",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:01:00Z",
        "config_hash": cfg_hash,
        "input_paths": [],
        "output_paths": [],
    }
    (status_dir / "ingest.json").write_text(json.dumps(state))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ingest_cmd_masks_mode_prints_skip_message(tmp_path: Path) -> None:
    """Masks-mode config should print skip message and exit 0 without running ingest."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg = _write_masks_config(tmp_path, output_dir=out_dir)

    runner = CliRunner()
    result = runner.invoke(main, ["ingest", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "ingest is not needed" in result.output


def test_ingest_cmd_requires_config(tmp_path: Path) -> None:
    """Invoking ingest without --config must fail (non-zero exit)."""
    runner = CliRunner()
    result = runner.invoke(main, ["ingest"])
    assert result.exit_code != 0


def test_ingest_cmd_already_done_skips_without_force(tmp_path: Path) -> None:
    """If stage_status/ingest.json is 'done' with matching config_hash, ingest_fovs is NOT called."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg_path = _write_tif_config(tmp_path, output_dir=out_dir)

    # Compute the config_hash the CLI will see
    from quantipy_polarity.config import Config
    from quantipy_polarity.pipeline.state import config_hash

    cfg = Config.from_yaml(cfg_path)
    chash = config_hash(cfg)
    _write_done_state(out_dir, chash)

    runner = CliRunner()
    with patch("quantipy_polarity.io.ingest.ingest_fovs") as mock_ingest:
        result = runner.invoke(
            main, ["ingest", "--config", str(cfg_path), "--output", str(out_dir)]
        )
    assert result.exit_code == 0, result.output
    mock_ingest.assert_not_called()


def test_ingest_cmd_force_reruns(tmp_path: Path) -> None:
    """With --force, ingest_fovs IS called even when stage_status/ingest.json is 'done'."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg_path = _write_tif_config(tmp_path, output_dir=out_dir)

    from quantipy_polarity.config import Config
    from quantipy_polarity.pipeline.state import config_hash

    cfg = Config.from_yaml(cfg_path)
    chash = config_hash(cfg)
    _write_done_state(out_dir, chash)

    runner = CliRunner()
    with patch(
        "quantipy_polarity.io.ingest.ingest_fovs", return_value=[]
    ) as mock_ingest:
        result = runner.invoke(
            main,
            ["ingest", "--config", str(cfg_path), "--output", str(out_dir), "--force"],
        )
    assert result.exit_code == 0, result.output
    mock_ingest.assert_called_once()


def test_ingest_cmd_writes_stage_status_on_success(tmp_path: Path) -> None:
    """Successful ingest should write stage_status/ingest.json with status 'done'."""
    out_dir = tmp_path / "results"
    out_dir.mkdir(parents=True)
    cfg_path = _write_tif_config(tmp_path, output_dir=out_dir)

    runner = CliRunner()
    with patch(
        "quantipy_polarity.io.ingest.ingest_fovs", return_value=["FOV_01"]
    ):
        result = runner.invoke(
            main,
            ["ingest", "--config", str(cfg_path), "--output", str(out_dir), "--force"],
        )
    assert result.exit_code == 0, result.output

    status_file = out_dir / "stage_status" / "ingest.json"
    assert status_file.exists(), "stage_status/ingest.json should exist after ingest"
    state_data = json.loads(status_file.read_text())
    assert state_data["status"] == "done"
