"""Pipeline orchestration package.

Provides StageState, run_pipeline, and the stage DAG.
Stages run in-process; no subprocess calls.
"""

from quantipy_polarity.pipeline.state import StageState, read_stage_state, write_stage_state
from quantipy_polarity.pipeline.dag import STAGES, should_skip_stage
from quantipy_polarity.pipeline.run import run_pipeline

__all__ = [
    "StageState",
    "read_stage_state",
    "write_stage_state",
    "STAGES",
    "should_skip_stage",
    "run_pipeline",
]
