"""Tests for pipeline/state.py — round-trip, atomic write, config_hash."""

from __future__ import annotations

import re
from pathlib import Path


from quantipy_polarity.config import Config, InputMasks
from quantipy_polarity.pipeline.state import (
    config_hash,
    read_stage_state,
    write_stage_state,
)


def _minimal_config(tmp_path: Path) -> Config:
    """Construct a minimal Config using masks input mode."""
    masks_dir = tmp_path / "masks"
    masks_dir.mkdir()
    return Config(
        input=InputMasks(
            mode="masks",
            path=masks_dir,
            masks_dir=masks_dir,
            pixel_size_um=0.5,
        )
    )


def test_write_and_read_round_trip(tmp_path: Path) -> None:
    """Write 'running' then 'done'; read back; assert key fields."""
    cfg = _minimal_config(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    write_stage_state(out_dir, "ingest", "running", cfg=cfg)
    write_stage_state(out_dir, "ingest", "done", cfg=cfg, preserve_started_at=True)

    state = read_stage_state(out_dir, "ingest")
    assert state is not None
    assert state.stage == "ingest"
    assert state.status == "done"
    assert state.started_at is not None
    assert state.finished_at is not None
    assert state.config_hash is not None


def test_atomic_write_produces_no_tmp_file(tmp_path: Path) -> None:
    """After write_stage_state, no .tmp.json files remain in stage_status/."""
    cfg = _minimal_config(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    write_stage_state(out_dir, "segment", "running", cfg=cfg)

    status_dir = out_dir / "stage_status"
    tmp_files = list(status_dir.glob("*.tmp.json"))
    assert tmp_files == [], f"Leftover .tmp.json files found: {tmp_files}"


def test_read_returns_none_if_absent(tmp_path: Path) -> None:
    """read_stage_state returns None when no JSON exists for the stage."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = read_stage_state(out_dir, "nonexistent_stage")
    assert result is None


def test_config_hash_is_16_hex_chars(tmp_path: Path) -> None:
    """config_hash returns a 16-character lowercase hex string."""
    cfg = _minimal_config(tmp_path)
    h = config_hash(cfg)
    assert len(h) == 16
    assert re.fullmatch(r"[0-9a-f]{16}", h), f"Not a 16-char hex string: {h!r}"


def test_write_state_preserve_started_at(tmp_path: Path) -> None:
    """Writing 'running' then 'done' with preserve_started_at=True keeps original started_at."""
    cfg = _minimal_config(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    running_state = write_stage_state(out_dir, "polarity", "running", cfg=cfg)
    original_started_at = running_state.started_at

    done_state = write_stage_state(
        out_dir, "polarity", "done", cfg=cfg, preserve_started_at=True
    )

    assert done_state.started_at == original_started_at
    assert done_state.finished_at is not None
    assert done_state.status == "done"


def test_write_state_creates_stage_status_dir(tmp_path: Path) -> None:
    """write_stage_state creates stage_status/ directory if it does not exist."""
    cfg = _minimal_config(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    status_dir = out_dir / "stage_status"
    assert not status_dir.exists(), "stage_status/ should not exist before write"

    write_stage_state(out_dir, "migration", "running", cfg=cfg)

    assert status_dir.is_dir(), "stage_status/ should be created by write_stage_state"
