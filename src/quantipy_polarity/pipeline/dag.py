"""Pipeline stage DAG for quantipy run.

Stages run in order; each stage is a string identifier that maps to a
callable in pipeline/run.py. There is no branching in v0.1.0.

Stage identifiers must match the keys written to stage_status/<name>.json.
"""

from __future__ import annotations

from typing import Callable

from quantipy_polarity.pipeline.state import StageState


# Canonical stage order. All stages run in sequence; skipping is per-stage.
STAGES: tuple[str, ...] = (
    "ingest",
    "segment",
    "polarity",
    "front",
    "aggregate",
    "plot",
    "report",
)


def should_skip_stage(
    state: StageState | None,
    current_config_hash: str,
    *,
    force: bool = False,
) -> bool:
    """Return True if this stage should be skipped (already done, same config).

    Skip condition (all must hold):
      - force is False
      - state is not None
      - state.status == "done"
      - state.config_hash == current_config_hash

    Args:
        state: Existing StageState from disk, or None if no JSON present.
        current_config_hash: Hash of the current run's config.
        force: If True, never skip.

    Returns:
        True if the stage should be skipped.
    """
    if force:
        return False
    if state is None:
        return False
    return state.status == "done" and state.config_hash == current_config_hash


def filter_stages(
    requested: list[str] | None,
) -> list[str]:
    """Return the ordered list of stages to run.

    Args:
        requested: Explicit stage list (e.g. ["segment", "polarity"]).
            None means all stages in STAGES order.

    Returns:
        Ordered list of stage names to execute.

    Raises:
        ValueError: If any requested stage name is not in STAGES.
    """
    if requested is None:
        return list(STAGES)
    unknown = [s for s in requested if s not in STAGES]
    if unknown:
        raise ValueError(f"Unknown stage(s): {unknown!r}. Valid stages: {list(STAGES)}")
    # Preserve canonical order even if caller provided a different order
    return [s for s in STAGES if s in requested]
