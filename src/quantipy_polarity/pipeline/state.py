"""Per-stage state tracking for pipeline resume/force semantics.

Each stage emits a JSON file at:
    <out_dir>/stage_status/<stage_name>.json

Schema (StageState):
    stage       : str    — stage identifier (e.g. "ingest", "segment")
    status      : str    — "pending" | "running" | "done" | "failed"
    started_at  : str | None  — ISO-8601 UTC timestamp
    finished_at : str | None  — ISO-8601 UTC timestamp
    config_hash : str | None  — first 16 hex chars of SHA-256(config JSON)
    input_paths : list[str]   — paths consumed by this stage
    output_paths: list[str]   — paths produced by this stage

Atomic write contract: always write to a .tmp file in the same directory,
then os.replace() to the final path. This ensures no partial JSON is ever
visible to a concurrent reader.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from quantipy_polarity.config import Config


_STAGE_STATUS_DIR = "stage_status"


class StageState(BaseModel):
    """State record for a single pipeline stage."""

    stage: str
    status: Literal["pending", "running", "done", "failed"] = "pending"
    started_at: str | None = None
    finished_at: str | None = None
    config_hash: str | None = None
    input_paths: list[str] = Field(default_factory=list)
    output_paths: list[str] = Field(default_factory=list)


def _stage_status_path(out_dir: Path, stage_name: str) -> Path:
    return Path(out_dir) / _STAGE_STATUS_DIR / f"{stage_name}.json"


def config_hash(cfg: Config) -> str:
    """Return first 16 hex characters of SHA-256 of the canonical config JSON.

    Args:
        cfg: Loaded Config object.

    Returns:
        16-character hex string.
    """
    canonical = cfg.model_dump_json(exclude_defaults=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def read_stage_state(out_dir: Path, stage_name: str) -> StageState | None:
    """Read the stage_status JSON for the given stage, or return None if absent.

    Args:
        out_dir: Base output directory.
        stage_name: Stage identifier string.

    Returns:
        StageState if the JSON exists and parses, else None.
    """
    path = _stage_status_path(out_dir, stage_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return StageState.model_validate(data)
    except Exception:
        return None


def write_stage_state(
    out_dir: Path,
    stage_name: str,
    status: str,
    *,
    cfg: Config | None = None,
    input_paths: list[str] | None = None,
    output_paths: list[str] | None = None,
    preserve_started_at: bool = False,
) -> StageState:
    """Write (or update) the stage_status JSON for the given stage atomically.

    Preserves existing started_at when preserve_started_at=True (used when
    transitioning from "running" → "done"/"failed").

    Args:
        out_dir: Base output directory.
        stage_name: Stage identifier string.
        status: New status value.
        cfg: Config object; when provided, config_hash is computed and stored.
        input_paths: Paths consumed by this stage (optional).
        output_paths: Paths produced by this stage (optional).
        preserve_started_at: If True, keep existing started_at from disk.

    Returns:
        The written StageState.
    """
    status_dir = Path(out_dir) / _STAGE_STATUS_DIR
    status_dir.mkdir(parents=True, exist_ok=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    existing = read_stage_state(out_dir, stage_name)

    chash = (
        config_hash(cfg)
        if cfg is not None
        else (existing.config_hash if existing else None)
    )

    started_at: str | None = None
    finished_at: str | None = None

    if status == "running":
        started_at = now
    elif status in ("done", "failed"):
        finished_at = now
        if preserve_started_at and existing and existing.started_at:
            started_at = existing.started_at
        else:
            started_at = existing.started_at if existing else None

    state = StageState(
        stage=stage_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        config_hash=chash,
        input_paths=input_paths or [],
        output_paths=output_paths or [],
    )

    path = _stage_status_path(out_dir, stage_name)
    fd, tmp = tempfile.mkstemp(dir=status_dir, suffix=".tmp.json")
    os.close(fd)
    try:
        with open(tmp, "w") as f:
            json.dump(state.model_dump(), f, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return state
