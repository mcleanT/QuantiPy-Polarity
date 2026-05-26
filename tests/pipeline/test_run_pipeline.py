"""Tests for pipeline/run.py — orchestrator behaviour.

Uses mocks to verify stage dispatch, skip semantics, force override,
status writes, failure propagation, downstream halting, subset execution,
and config snapshot generation. No heavy stage logic (Cellpose etc.) runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quantipy_polarity.config import Config
from quantipy_polarity.pipeline.run import run_pipeline
from quantipy_polarity.pipeline.state import config_hash, write_stage_state

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STAGE_NAMES = [
    "ingest",
    "segment",
    "polarity",
    "front",
    "aggregate",
    "plot",
    "report",
]

_STAGE_PATHS = [
    f"quantipy_polarity.pipeline.run._stage_{name}" for name in _STAGE_NAMES
]


def _masks_config(tmp_path: Path) -> Config:
    """Return a minimal masks-mode Config pointing at tmp_path subdirs."""
    mem_dir = tmp_path / "membrane"
    msk_dir = tmp_path / "masks"
    mem_dir.mkdir(parents=True, exist_ok=True)
    msk_dir.mkdir(parents=True, exist_ok=True)
    return Config.model_validate(
        {
            "input": {
                "mode": "masks",
                "path": str(mem_dir),
                "masks_dir": str(msk_dir),
                "pixel_size_um": 0.65,
            }
        }
    )


# ---------------------------------------------------------------------------
# Test 1: all 7 stage functions called once when running full pipeline
# ---------------------------------------------------------------------------


def test_run_pipeline_all_stages_called(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"

    with (
        patch("quantipy_polarity.pipeline.run._stage_ingest") as m_ingest,
        patch("quantipy_polarity.pipeline.run._stage_segment") as m_segment,
        patch("quantipy_polarity.pipeline.run._stage_polarity") as m_polarity,
        patch("quantipy_polarity.pipeline.run._stage_front") as m_front,
        patch("quantipy_polarity.pipeline.run._stage_aggregate") as m_aggregate,
        patch("quantipy_polarity.pipeline.run._stage_plot") as m_plot,
        patch("quantipy_polarity.pipeline.run._stage_report") as m_report,
    ):
        run_pipeline(cfg, out_dir, force=False)

    m_ingest.assert_called_once()
    m_segment.assert_called_once()
    m_polarity.assert_called_once()
    m_front.assert_called_once()
    m_aggregate.assert_called_once()
    m_plot.assert_called_once()
    m_report.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: stage with matching done state is skipped
# ---------------------------------------------------------------------------


def test_run_pipeline_skips_done_stage(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    chash = config_hash(cfg)
    # Pre-write "done" state with matching config hash for "polarity"
    write_stage_state(out_dir, "polarity", "done", cfg=cfg)

    with (
        patch("quantipy_polarity.pipeline.run._stage_ingest"),
        patch("quantipy_polarity.pipeline.run._stage_segment"),
        patch("quantipy_polarity.pipeline.run._stage_polarity") as m_polarity,
        patch("quantipy_polarity.pipeline.run._stage_front"),
        patch("quantipy_polarity.pipeline.run._stage_aggregate"),
        patch("quantipy_polarity.pipeline.run._stage_plot"),
        patch("quantipy_polarity.pipeline.run._stage_report"),
    ):
        run_pipeline(cfg, out_dir, force=False)

    m_polarity.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: force=True overrides skip even when stage is done
# ---------------------------------------------------------------------------


def test_run_pipeline_force_overrides_skip(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pre-write "done" state for "segment"
    write_stage_state(out_dir, "segment", "done", cfg=cfg)

    with (
        patch("quantipy_polarity.pipeline.run._stage_ingest"),
        patch("quantipy_polarity.pipeline.run._stage_segment") as m_segment,
        patch("quantipy_polarity.pipeline.run._stage_polarity"),
        patch("quantipy_polarity.pipeline.run._stage_front"),
        patch("quantipy_polarity.pipeline.run._stage_aggregate"),
        patch("quantipy_polarity.pipeline.run._stage_plot"),
        patch("quantipy_polarity.pipeline.run._stage_report"),
    ):
        run_pipeline(cfg, out_dir, force=True)

    m_segment.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: stage status JSON is written as "done" after a successful stage
# ---------------------------------------------------------------------------


def test_run_pipeline_writes_stage_status(tmp_path: Path) -> None:
    """_stage_ingest on a masks-mode config exits early without side effects."""
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"

    # Mock all except ingest — ingest exits early in masks mode (no-op return)
    with (
        patch("quantipy_polarity.pipeline.run._stage_segment"),
        patch("quantipy_polarity.pipeline.run._stage_polarity"),
        patch("quantipy_polarity.pipeline.run._stage_front"),
        patch("quantipy_polarity.pipeline.run._stage_aggregate"),
        patch("quantipy_polarity.pipeline.run._stage_plot"),
        patch("quantipy_polarity.pipeline.run._stage_report"),
    ):
        run_pipeline(cfg, out_dir, force=False)

    status_path = out_dir / "stage_status" / "ingest.json"
    assert status_path.exists(), "ingest.json not written"
    state = json.loads(status_path.read_text())
    assert state["status"] == "done"


# ---------------------------------------------------------------------------
# Test 5: failed stage writes status=failed and raises RuntimeError
# ---------------------------------------------------------------------------


def test_run_pipeline_failed_stage_writes_failed_status(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"

    with (
        patch(
            "quantipy_polarity.pipeline.run._stage_ingest",
            side_effect=RuntimeError("ingest boom"),
        ),
        patch("quantipy_polarity.pipeline.run._stage_segment"),
        patch("quantipy_polarity.pipeline.run._stage_polarity"),
        patch("quantipy_polarity.pipeline.run._stage_front"),
        patch("quantipy_polarity.pipeline.run._stage_aggregate"),
        patch("quantipy_polarity.pipeline.run._stage_plot"),
        patch("quantipy_polarity.pipeline.run._stage_report"),
    ):
        with pytest.raises(RuntimeError, match="ingest"):
            run_pipeline(cfg, out_dir, force=False)

    status_path = out_dir / "stage_status" / "ingest.json"
    assert status_path.exists(), "ingest.json not written after failure"
    state = json.loads(status_path.read_text())
    assert state["status"] == "failed"


# ---------------------------------------------------------------------------
# Test 6: failed stage halts downstream stages
# ---------------------------------------------------------------------------


def test_run_pipeline_failed_stage_halts_downstream(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"

    with (
        patch("quantipy_polarity.pipeline.run._stage_ingest"),
        patch("quantipy_polarity.pipeline.run._stage_segment"),
        patch(
            "quantipy_polarity.pipeline.run._stage_polarity",
            side_effect=ValueError("polarity exploded"),
        ),
        patch("quantipy_polarity.pipeline.run._stage_front"),
        patch("quantipy_polarity.pipeline.run._stage_aggregate") as m_aggregate,
        patch("quantipy_polarity.pipeline.run._stage_plot"),
        patch("quantipy_polarity.pipeline.run._stage_report"),
    ):
        with pytest.raises(RuntimeError):
            run_pipeline(cfg, out_dir, force=False)

    m_aggregate.assert_not_called()


# ---------------------------------------------------------------------------
# Test 7: subset of stages — only requested stages are called
# ---------------------------------------------------------------------------


def test_run_pipeline_subset_stages(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"

    with (
        patch("quantipy_polarity.pipeline.run._stage_ingest") as m_ingest,
        patch("quantipy_polarity.pipeline.run._stage_segment") as m_segment,
        patch("quantipy_polarity.pipeline.run._stage_polarity") as m_polarity,
        patch("quantipy_polarity.pipeline.run._stage_front") as m_front,
        patch("quantipy_polarity.pipeline.run._stage_aggregate") as m_aggregate,
        patch("quantipy_polarity.pipeline.run._stage_plot") as m_plot,
        patch("quantipy_polarity.pipeline.run._stage_report") as m_report,
    ):
        run_pipeline(cfg, out_dir, stages=["polarity", "aggregate"])

    m_polarity.assert_called_once()
    m_aggregate.assert_called_once()
    m_ingest.assert_not_called()
    m_segment.assert_not_called()
    m_front.assert_not_called()
    m_plot.assert_not_called()
    m_report.assert_not_called()


# ---------------------------------------------------------------------------
# Test 8: config snapshot YAML is written to out_dir
# ---------------------------------------------------------------------------


def test_run_pipeline_writes_config_snapshot(tmp_path: Path) -> None:
    cfg = _masks_config(tmp_path)
    out_dir = tmp_path / "out"

    with (
        patch("quantipy_polarity.pipeline.run._stage_ingest"),
        patch("quantipy_polarity.pipeline.run._stage_segment"),
        patch("quantipy_polarity.pipeline.run._stage_polarity"),
        patch("quantipy_polarity.pipeline.run._stage_front"),
        patch("quantipy_polarity.pipeline.run._stage_aggregate"),
        patch("quantipy_polarity.pipeline.run._stage_plot"),
        patch("quantipy_polarity.pipeline.run._stage_report"),
    ):
        run_pipeline(cfg, out_dir, force=False)

    snapshot = out_dir / "config.snapshot.yaml"
    assert snapshot.exists(), "config.snapshot.yaml not written"
