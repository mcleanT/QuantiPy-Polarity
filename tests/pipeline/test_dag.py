"""Tests for pipeline/dag.py — stage order, skip logic, and filter_stages."""

from __future__ import annotations

import pytest

from quantipy_polarity.pipeline.dag import STAGES, filter_stages, should_skip_stage
from quantipy_polarity.pipeline.state import StageState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HASH_A = "abc123"
HASH_B = "def456"


def _done_state(config_hash: str = HASH_A) -> StageState:
    return StageState(stage="ingest", status="done", config_hash=config_hash)


def _failed_state(config_hash: str = HASH_A) -> StageState:
    return StageState(stage="ingest", status="failed", config_hash=config_hash)


# ---------------------------------------------------------------------------
# STAGES canonical order
# ---------------------------------------------------------------------------


def test_stages_canonical_order() -> None:
    assert STAGES == ("ingest", "segment", "polarity", "front", "aggregate", "plot", "report")


# ---------------------------------------------------------------------------
# should_skip_stage
# ---------------------------------------------------------------------------


def test_should_skip_done_matching_hash() -> None:
    assert should_skip_stage(_done_state(HASH_A), HASH_A) is True


def test_should_not_skip_failed_stage() -> None:
    assert should_skip_stage(_failed_state(HASH_A), HASH_A) is False


def test_should_not_skip_hash_mismatch() -> None:
    assert should_skip_stage(_done_state(HASH_A), HASH_B) is False


def test_should_not_skip_when_force() -> None:
    assert should_skip_stage(_done_state(HASH_A), HASH_A, force=True) is False


def test_should_not_skip_none_state() -> None:
    assert should_skip_stage(None, HASH_A) is False


# ---------------------------------------------------------------------------
# filter_stages
# ---------------------------------------------------------------------------


def test_filter_stages_none_returns_all() -> None:
    result = filter_stages(None)
    assert result == list(STAGES)
    assert len(result) == 7


def test_filter_stages_subset_preserves_order() -> None:
    result = filter_stages(["report", "polarity"])
    assert result == ["polarity", "report"]


def test_filter_stages_unknown_raises() -> None:
    with pytest.raises(ValueError, match="bogus"):
        filter_stages(["bogus"])
