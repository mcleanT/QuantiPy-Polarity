# QuantiPy Polarity — Phase 5: Pipeline Orchestration, Ingest, and HTML Report

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `quantipy run` from a stub into a real in-process pipeline orchestrator with resume/force semantics, implement `quantipy ingest` as a real command (nd2/tif → normalized per-FOV TIFs), implement `quantipy report` to generate a self-contained single-file HTML report, and add a `pipeline/` and `report/build.py` package that the CLI commands delegate to. All existing `quantipy polarity`, `segment`, `front`, `plot`, `aggregate` commands continue to work standalone with no behavior change.

**Architecture overview:** A new `pipeline/` sub-package provides `state.py` (Pydantic `StageState` model + atomic read/write helpers), `dag.py` (ordered stage list, skip logic), and `run.py` (top-level `run_pipeline()`). Each stage in `run_pipeline()` calls the same Python functions that the individual CLI commands already use — never subprocess. `report/build.py` assembles the HTML file by reading the run directory, rescaling figures to thumbnail size (max 400 px on longest edge), and base64-encoding them inline; Jinja2 renders the final HTML. A new `_cli_ingest.py` extracts the per-FOV TIF iteration that `_cli_segment.py` currently does inline, promotes it to a `write_ingest_outputs()` helper in `io/ingest.py`, and registers `quantipy ingest`. `_cli_run.py` and `_cli_report.py` replace their stubs.

**Run directory layout (locked):**
```
results/
├── stage_status/             # one JSON per stage (via pipeline/state.py)
│   ├── ingest.json
│   ├── segment.json
│   ├── polarity.json
│   ├── front.json
│   ├── aggregate.json
│   ├── plot.json
│   └── report.json
├── 01_ingest/                # per-FOV normalized TIFs from quantipy ingest
│   └── <fov_id>_membrane.tif
├── 02_segmentation/          # uint16 masks (unchanged from Phase 3)
│   └── <fov_id>_mask.tif
├── 03_polarity/per_fov/      # per-FOV parquets (unchanged from Phase 2)
│   └── <fov_id>.parquet
├── 04_migration/             # front parquet + QC (unchanged from Phase 4)
│   └── front_um_per_fov.parquet
├── 05_aggregated/            # experiment-wide parquet (unchanged from Phase 2)
│   └── per_cell.parquet
├── 06_plots/                 # all figures (unchanged from Phase 4)
├── config.snapshot.yaml      # frozen config used for this run
├── run.log                   # structlog output
└── report.html               # self-contained HTML (last stage)
```

Note: `stage_status/` is new in Phase 5. The numbered `01_`–`06_` directories are the same directories that Phases 2–4 already write; `run_pipeline()` calls into the same functions that write them.

**Spec sources:** `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` rev 1 §§5 (CLI surface), 7 (output layout + resume semantics), and §8 (interactive — confirms `quantipy ingest` is the nd2/tif→TIF step).

**Baseline:** 169 tests passing (1 skipped), tag `phase-4-complete`.

**Acceptance criteria:**
1. `quantipy run --config config.yaml` (masks mode) completes end-to-end on `tests/fixtures/synthetic_fov.npz` and writes all six stage directories plus `report.html`.
2. A second `quantipy run --config config.yaml` without `--force` on the same output dir skips all stages already in `done` state and exits zero.
3. `quantipy run --config config.yaml --force` wipes stage state and reruns from scratch.
4. `quantipy run` with a stage that raises mid-run writes `status=failed` in that stage's JSON and exits non-zero; a subsequent `--resume` restarts from that stage.
5. `quantipy ingest --config config.yaml --output ./results` writes `01_ingest/` TIFs and a `stage_status/ingest.json`.
6. `quantipy report --results ./results --output report.html` (re)generates the HTML without rerunning any stage.
7. `report.html` is a single self-contained file (no external URLs, no CDN); all images are base64-inline.
8. `quantipy polarity`, `segment`, `front`, `aggregate`, `plot` still work standalone, unchanged.
9. Full pytest suite: 169 (Phase 4) + ≥28 new tests = **≥197 passed**. All new tests are fast-tier (synthetic fixtures, no real microscopy, no cellpose calls in new tests).
10. `quantipy --help` still shows all commands; no import errors on cold start.
11. README and CLAUDE.md updated; tag `phase-5-complete` pushed.

---

## File Structure (locked at planning time)

```
QuantiPy-Polarity/
├── src/quantipy_polarity/
│   ├── io/
│   │   └── ingest.py                          # Create Task 1: write_ingest_outputs() + ingest_fovs()
│   ├── pipeline/
│   │   ├── __init__.py                        # Create Task 2
│   │   ├── state.py                           # Create Task 3: StageState + read/write helpers
│   │   ├── dag.py                             # Create Task 4: STAGES list, skip logic
│   │   └── run.py                             # Create Task 5: run_pipeline()
│   ├── report/
│   │   ├── __init__.py                        # Modify Task 6 (currently one-line stub)
│   │   ├── build.py                           # Create Task 7: gather_report_inputs() + build_report()
│   │   └── templates/
│   │       └── report.html.j2                 # Create Task 8: Jinja2 template
│   ├── _cli_ingest.py                         # Create Task 9: real `quantipy ingest`
│   ├── _cli_run.py                            # Create Task 10: real `quantipy run`
│   ├── _cli_report.py                         # Create Task 11: real `quantipy report`
│   ├── _cli_segment.py                        # Modify Task 12: extract _run_segment → delegates to io/ingest.py helpers; no behavior change
│   ├── _stubs.py                              # Modify Task 13: remove run, report, ingest stubs
│   └── cli.py                                 # Modify Task 13: import new CLI modules
├── tests/
│   ├── pipeline/
│   │   ├── __init__.py                        # Create Task 14
│   │   ├── test_state.py                      # Create Task 14: StageState round-trip, atomic write, config_hash
│   │   ├── test_dag.py                        # Create Task 15: stage order, skip logic, force override
│   │   └── test_run_pipeline.py               # Create Task 16: end-to-end orchestration, resume, failure
│   ├── report/
│   │   ├── __init__.py                        # Create Task 17
│   │   ├── test_build.py                      # Create Task 17: HTML self-contained, images embedded, sections present
│   │   └── test_template.py                   # Create Task 18: Jinja2 rendering with mock data
│   ├── io/
│   │   └── test_ingest.py                     # Create Task 19: ingest_fovs() writes 01_ingest/ TIFs
│   └── cli/
│       ├── test_cli_run.py                    # Create Task 20: CLI flag wiring, --force, --resume, --stage
│       ├── test_cli_report.py                 # Create Task 21: report regen from existing run dir
│       └── test_cli_ingest.py                 # Create Task 22: ingest CLI writes stage_status JSON
├── docs/
│   ├── pipeline.md                            # Create Task 23: pipeline internals + resume semantics
│   └── concepts.md                            # Modify Task 23: add ingest stage note
├── README.md                                  # Modify Task 24: Phase 5 badge, run example
└── CLAUDE.md                                  # Modify Task 24: update command table, run status
```

---

## Task 1: Create `io/ingest.py` — FOV normalization helpers

**Files:** Create `src/quantipy_polarity/io/ingest.py`

Extract the per-FOV iteration logic that `_cli_segment.py` currently performs inline (`_build_fov_iterator`) into a reusable function, and add a new `write_ingest_outputs()` function that writes per-FOV normalized TIFs to `01_ingest/`. This lets `pipeline/run.py` call ingest independently of `segment`, and lets `_cli_segment.py` reuse the same helpers without duplication.

- [ ] **Step 1: Read `src/quantipy_polarity/_cli_segment.py` lines 163–204**

  Note the `_build_fov_iterator(cfg)` function and what it returns (an iterable of `TIFFOV` or `ND2FOV`-like objects with `.fov_id`, `.membrane` attributes).

- [ ] **Step 2: Read `src/quantipy_polarity/io/tif.py` and `src/quantipy_polarity/io/nd2.py`** (first 50 lines of each)

  Note the return type and field names of the FOV objects those modules yield.

- [ ] **Step 3: Create `src/quantipy_polarity/io/ingest.py`**

  ```python
  """FOV normalization: nd2/tif → per-FOV float32 membrane arrays + disk TIFs.

  Provides:
      build_fov_iterator(cfg) -> Iterable[FOVData]
          Unified iterator over all input modes (nd2, tif, masks).
          Consolidates the _build_fov_iterator logic from _cli_segment.py.

      write_ingest_outputs(out_dir, fov_id, membrane_float) -> Path
          Write a normalized per-FOV membrane TIF to 01_ingest/<fov_id>_membrane.tif.
          Atomic write (tmp + os.replace). Returns the written path.

      ingest_fovs(cfg, out_dir) -> list[str]
          Iterate all FOVs, call write_ingest_outputs for each, return list of fov_ids.
  """

  from __future__ import annotations

  import os
  import tempfile
  from pathlib import Path
  from typing import TYPE_CHECKING

  import numpy as np
  import structlog
  import tifffile

  if TYPE_CHECKING:
      from quantipy_polarity.config import Config

  log = structlog.get_logger()

  _INGEST_DIR = "01_ingest"


  def build_fov_iterator(cfg: "Config"):
      """Return an iterable of FOV objects for the configured input mode.

      Works for all three input modes: nd2, tif, masks.
      Each yielded object has .fov_id (str) and .membrane (float32 H×W array [0,1]).

      Args:
          cfg: Loaded Config object.

      Returns:
          Iterable of FOV data objects.
      """
      from quantipy_polarity.config import InputMasks, InputND2, InputTIF

      input_cfg = cfg.input

      if input_cfg.mode == "tif":
          from quantipy_polarity.io.tif import iter_tif_dataset

          return iter_tif_dataset(
              tif_dir=input_cfg.path,
              channel_membrane=input_cfg.channel_membrane,
              channel_segmentation=input_cfg.channel_segmentation,
              pixel_size_um=input_cfg.pixel_size_um,
              scheme=getattr(input_cfg, "tif_scheme", "stack"),
              channel_suffix_template=getattr(input_cfg, "channel_suffix_template", "_ch{ch}"),
          )
      elif input_cfg.mode == "nd2":
          from quantipy_polarity.io.nd2 import iter_nd2_dataset

          nd2_files = sorted(Path(input_cfg.path).glob("*.nd2"))
          if not nd2_files:
              raise FileNotFoundError(f"No .nd2 files found in {input_cfg.path}")

          def _gen():
              for nd2_path in nd2_files:
                  yield from iter_nd2_dataset(
                      nd2_path=nd2_path,
                      channel_membrane=input_cfg.channel_membrane,
                      channel_segmentation=input_cfg.channel_segmentation,
                      pixel_size_um_fallback=input_cfg.pixel_size_um,
                      z_policy=input_cfg.z_policy,
                      substack_range=input_cfg.substack_range,
                      fov_id_prefix="FOV",
                  )

          return _gen()
      elif input_cfg.mode == "masks":
          from quantipy_polarity.io.masks import iter_mask_dataset

          return iter_mask_dataset(
              membrane_dir=input_cfg.path,
              masks_dir=input_cfg.masks_dir,
              channel_membrane=input_cfg.channel_membrane,
          )
      else:
          raise ValueError(f"Unknown input.mode: {input_cfg.mode!r}")


  def write_ingest_outputs(out_dir: Path, fov_id: str, membrane_float: np.ndarray) -> Path:
      """Write a normalized per-FOV membrane TIF to 01_ingest/ atomically.

      The TIF is written as uint16 (membrane_float * 65535, clipped) so it is
      consistent with the format used by segment/_writer.py for the membrane channel.

      Args:
          out_dir: Base output directory (01_ingest/ is created inside here).
          fov_id: FOV identifier string.
          membrane_float: (H, W) float32 array in [0, 1].

      Returns:
          Path to the written TIF file.
      """
      ingest_dir = Path(out_dir) / _INGEST_DIR
      ingest_dir.mkdir(parents=True, exist_ok=True)

      out_path = ingest_dir / f"{fov_id}_membrane.tif"
      membrane_u16 = (membrane_float * 65535).clip(0, 65535).astype(np.uint16)

      fd, tmp = tempfile.mkstemp(dir=ingest_dir, suffix=".tmp.tif")
      os.close(fd)
      try:
          tifffile.imwrite(tmp, membrane_u16)
          os.replace(tmp, out_path)
      except Exception:
          try:
              os.unlink(tmp)
          except OSError:
              pass
          raise

      log.info("wrote ingest TIF", fov_id=fov_id, path=str(out_path))
      return out_path


  def ingest_fovs(cfg: "Config", out_dir: Path) -> list[str]:
      """Iterate all FOVs, write per-FOV membrane TIFs, return list of fov_ids.

      Args:
          cfg: Loaded Config object.
          out_dir: Base output directory.

      Returns:
          List of fov_id strings in the order processed.
      """
      fov_ids: list[str] = []
      for fov in build_fov_iterator(cfg):
          write_ingest_outputs(out_dir, fov.fov_id, fov.membrane)
          fov_ids.append(fov.fov_id)
      log.info("ingest complete", n_fovs=len(fov_ids))
      return fov_ids
  ```

- [ ] **Step 4: Verify import**

  ```bash
  python -c "from quantipy_polarity.io.ingest import build_fov_iterator, write_ingest_outputs, ingest_fovs; print('ingest OK')"
  ```

  Expected: `ingest OK`

- [ ] **Step 5: Run baseline tests**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `169 passed, 1 skipped` (no regressions).

- [ ] **Step 6: Commit**

  ```bash
  git add src/quantipy_polarity/io/ingest.py
  git commit -m "feat(io): add ingest.py — unified FOV iterator + atomic TIF writer"
  ```

---

## Task 2: Create `pipeline/__init__.py`

**Files:** Create `src/quantipy_polarity/pipeline/__init__.py`

- [ ] **Step 1: Create `src/quantipy_polarity/pipeline/__init__.py`**

  ```python
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
  ```

- [ ] **Step 2: Verify**

  ```bash
  python -c "import quantipy_polarity.pipeline; print('pipeline pkg OK')"
  ```

  This will fail until Tasks 3–5 create the sub-modules, which is expected at this step. Verify once Task 5 is complete.

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/pipeline/__init__.py
  git commit -m "feat(pipeline): scaffold pipeline package __init__"
  ```

---

## Task 3: Create `pipeline/state.py` — `StageState` Pydantic model + helpers

**Files:** Create `src/quantipy_polarity/pipeline/state.py`

This module owns the canonical `stage_status.json` format. All reads and writes go through these helpers so the format never drifts. The `write_stage_state()` here is **stage-agnostic** (takes a `stage_name` argument) unlike `segment/_writer.py`'s `write_stage_status()` which is hardcoded to `02_segmentation/`. Phase 5 adds `stage_status/` as a separate top-level directory so all stage JSONs live together.

Note: `segment/_writer.py` keeps its own `write_stage_status()` to preserve backward compat for `quantipy segment` standalone. The pipeline calls `pipeline/state.py` exclusively.

- [ ] **Step 1: Create `src/quantipy_polarity/pipeline/state.py`**

  ```python
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

      chash = config_hash(cfg) if cfg is not None else (existing.config_hash if existing else None)

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
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity.pipeline.state import StageState, config_hash, read_stage_state, write_stage_state; print('state OK')"
  ```

  Expected: `state OK`

- [ ] **Step 3: Run baseline tests**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `169 passed, 1 skipped`.

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/pipeline/state.py
  git commit -m "feat(pipeline): add state.py — StageState model + atomic read/write"
  ```

---

## Task 4: Create `pipeline/dag.py` — stage list and skip logic

**Files:** Create `src/quantipy_polarity/pipeline/dag.py`

The DAG is a simple ordered list (no branching in v0.1.0). Dependencies are implicit: each stage consumes the previous stage's outputs. Skip logic: a stage is skippable when its `stage_status.json` says `done` AND the `config_hash` matches the current run's hash AND `--force` is False.

- [ ] **Step 1: Create `src/quantipy_polarity/pipeline/dag.py`**

  ```python
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
          raise ValueError(
              f"Unknown stage(s): {unknown!r}. Valid stages: {list(STAGES)}"
          )
      # Preserve canonical order even if caller provided a different order
      return [s for s in STAGES if s in requested]
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity.pipeline.dag import STAGES, should_skip_stage, filter_stages; print('dag OK:', STAGES)"
  ```

  Expected: `dag OK: ('ingest', 'segment', 'polarity', 'front', 'aggregate', 'plot', 'report')`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/pipeline/dag.py
  git commit -m "feat(pipeline): add dag.py — stage list, skip logic, filter_stages"
  ```

---

## Task 5: Create `pipeline/run.py` — top-level orchestrator

**Files:** Create `src/quantipy_polarity/pipeline/run.py`

`run_pipeline()` is the single entry point called by `_cli_run.py`. It calls the same Python functions that each individual CLI module already uses — never subprocess. Each stage follows the same pattern: `write_stage_state(..., "running")` → execute → `write_stage_state(..., "done")`, with a `try/except` that writes `"failed"` and re-raises on error. Before executing, each stage checks `should_skip_stage()` and logs a skip if appropriate.

The `masks` input mode skips `ingest` and `segment` automatically (they require nd2/tif input). The `front` stage skips itself silently when `cfg.migration.front_method == "none"`.

- [ ] **Step 1: Read `src/quantipy_polarity/_cli_polarity.py`** (already read; recall `_run_segment` pattern from `_cli_segment.py` and the equivalent logic in `polarity_cmd` and `aggregate_cmd`)

- [ ] **Step 2: Create `src/quantipy_polarity/pipeline/run.py`**

  ```python
  """Top-level pipeline orchestrator for `quantipy run`.

  run_pipeline(cfg, out_dir, *, force, stages) executes the full pipeline
  (or a subset of named stages) in-process. Each stage writes its state to
  stage_status/<name>.json via pipeline/state.py.

  Stage functions are private to this module; they call the same Python
  functions used by the individual CLI subcommands.
  """

  from __future__ import annotations

  import shutil
  from pathlib import Path

  import structlog

  from quantipy_polarity.config import Config
  from quantipy_polarity.pipeline.dag import STAGES, filter_stages, should_skip_stage
  from quantipy_polarity.pipeline.state import (
      StageState,
      config_hash,
      read_stage_state,
      write_stage_state,
  )

  log = structlog.get_logger()


  def run_pipeline(
      cfg: Config,
      out_dir: Path,
      *,
      force: bool = False,
      stages: list[str] | None = None,
  ) -> None:
      """Execute the full pipeline (or a subset) for the given config.

      Args:
          cfg: Validated Config object.
          out_dir: Base output directory. Created if absent.
          force: If True, ignore all stage_status caches and re-run everything.
          stages: List of stage names to run (None = all). Preserves canonical order.

      Raises:
          RuntimeError: If any stage fails (after writing status=failed to JSON).
          ValueError: If stages contains an unknown stage name.
      """
      out_dir = Path(out_dir)
      out_dir.mkdir(parents=True, exist_ok=True)

      chash = config_hash(cfg)
      ordered = filter_stages(stages)

      # Write frozen config snapshot
      snapshot_path = out_dir / "config.snapshot.yaml"
      cfg.to_yaml(snapshot_path)
      log.info("pipeline_start", stages=ordered, out_dir=str(out_dir), config_hash=chash)

      _STAGE_FN: dict[str, object] = {
          "ingest": _stage_ingest,
          "segment": _stage_segment,
          "polarity": _stage_polarity,
          "front": _stage_front,
          "aggregate": _stage_aggregate,
          "plot": _stage_plot,
          "report": _stage_report,
      }

      for stage_name in ordered:
          state = read_stage_state(out_dir, stage_name)
          if should_skip_stage(state, chash, force=force):
              log.info("stage_skipped", stage=stage_name, reason="already_done")
              continue

          log.info("stage_start", stage=stage_name)
          write_stage_state(out_dir, stage_name, "running", cfg=cfg)

          try:
              fn = _STAGE_FN[stage_name]
              fn(cfg, out_dir)  # type: ignore[operator]
          except Exception as exc:
              write_stage_state(
                  out_dir, stage_name, "failed", cfg=cfg, preserve_started_at=True
              )
              log.error("stage_failed", stage=stage_name, error=str(exc))
              raise RuntimeError(f"Stage '{stage_name}' failed: {exc}") from exc

          write_stage_state(out_dir, stage_name, "done", cfg=cfg, preserve_started_at=True)
          log.info("stage_done", stage=stage_name)

      log.info("pipeline_complete", out_dir=str(out_dir))


  # ---------------------------------------------------------------------------
  # Stage implementations — each calls the same functions the CLI modules use
  # ---------------------------------------------------------------------------


  def _stage_ingest(cfg: Config, out_dir: Path) -> None:
      """Ingest: nd2/tif → normalized per-FOV TIFs in 01_ingest/."""
      from quantipy_polarity.config import InputMasks

      if isinstance(cfg.input, InputMasks):
          log.info("stage_ingest_skipped_masks_mode")
          return
      from quantipy_polarity.io.ingest import ingest_fovs

      ingest_fovs(cfg, out_dir)


  def _stage_segment(cfg: Config, out_dir: Path) -> None:
      """Segment: membrane TIFs → uint16 label masks in 02_segmentation/."""
      from quantipy_polarity.config import InputMasks

      if isinstance(cfg.input, InputMasks):
          log.info("stage_segment_skipped_masks_mode")
          return
      from quantipy_polarity._cli_segment import _run_segment

      _run_segment(cfg, out_dir, gpu=False)


  def _stage_polarity(cfg: Config, out_dir: Path) -> None:
      """Polarity: masks → per-FOV parquets in 03_polarity/per_fov/."""
      from quantipy_polarity.config import InputMasks
      from quantipy_polarity.io.masks import iter_mask_dataset
      from quantipy_polarity.polarity.boundary_pca import compute_cell_polarity
      from quantipy_polarity.polarity.per_cell import per_fov_to_parquet

      per_fov_dir = out_dir / "03_polarity" / "per_fov"
      per_fov_dir.mkdir(parents=True, exist_ok=True)

      # Determine mask source: 02_segmentation/ (from segment stage) or input.masks_dir
      if isinstance(cfg.input, InputMasks):
          mask_source = cfg.input.masks_dir
          membrane_source = cfg.input.path
          channel_membrane = cfg.input.channel_membrane
      else:
          mask_source = out_dir / "02_segmentation"
          membrane_source = out_dir / "02_segmentation"
          channel_membrane = 0  # written by _writer as single-channel uint16

      for fov in iter_mask_dataset(
          membrane_dir=membrane_source,
          masks_dir=mask_source,
          channel_membrane=channel_membrane,
      ):
          result = compute_cell_polarity(fov.membrane, fov.label_mask)
          out_path = per_fov_dir / f"{fov.fov_id}.parquet"
          per_fov_to_parquet(
              result,
              fov_id=fov.fov_id,
              label_mask=fov.label_mask,
              out_path=out_path,
              condition=None,
              overwrite=True,
          )
          log.info("polarity_fov_done", fov_id=fov.fov_id)


  def _stage_aggregate(cfg: Config, out_dir: Path) -> None:
      """Aggregate: per-FOV parquets → experiment-wide per_cell.parquet."""
      from quantipy_polarity.polarity.per_cell import aggregate_experiment

      per_fov_dir = out_dir / "03_polarity" / "per_fov"
      parquets = sorted(per_fov_dir.glob("*.parquet"))
      if not parquets:
          raise FileNotFoundError(f"No per-FOV parquets found in {per_fov_dir}")
      agg_dir = out_dir / "05_aggregated"
      agg_dir.mkdir(parents=True, exist_ok=True)
      out_path = agg_dir / "per_cell.parquet"
      aggregate_experiment(parquets, out_path, overwrite=True)
      log.info("aggregate_done", n_fovs=len(parquets), path=str(out_path))


  def _stage_front(cfg: Config, out_dir: Path) -> None:
      """Front: label masks → front_um_per_fov.parquet + per_cell migration cols."""
      if cfg.migration.front_method == "none":
          log.info("stage_front_skipped_method_none")
          return

      import numpy as np
      import tifffile

      from quantipy_polarity.contracts import FrontResult
      from quantipy_polarity.migration.front_detect import (
          _compute_migration_field_v6,
          detect_front,
      )
      from quantipy_polarity.migration.front_io import write_front_parquet

      # Determine mask source
      from quantipy_polarity.config import InputMasks
      if isinstance(cfg.input, InputMasks):
          seg_dir = cfg.input.masks_dir
      else:
          seg_dir = out_dir / "02_segmentation"

      mask_files = sorted(Path(seg_dir).glob("*_mask.tif"))
      if not mask_files:
          raise FileNotFoundError(f"No *_mask.tif files in {seg_dir}")

      pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)
      mig_dir = out_dir / "04_migration"
      mig_dir.mkdir(parents=True, exist_ok=True)
      front_parquet = mig_dir / "front_um_per_fov.parquet"

      results: list[FrontResult] = []
      vx_by_fov: dict[str, np.ndarray] = {}
      vy_by_fov: dict[str, np.ndarray] = {}
      labels_by_fov: dict[str, np.ndarray] = {}

      for mask_file in mask_files:
          fov_id = mask_file.stem.replace("_mask", "")
          labels = tifffile.imread(str(mask_file)).astype(np.int32)
          if labels.ndim != 2:
              log.warning("non_2d_mask_skipped", fov_id=fov_id, shape=labels.shape)
              continue
          result = detect_front(labels, pixel_size_um=pixel_size_um, fov_id=fov_id)
          results.append(result)
          vx, vy, _ = _compute_migration_field_v6(labels)
          vx_by_fov[fov_id] = vx
          vy_by_fov[fov_id] = vy
          labels_by_fov[fov_id] = labels
          log.info("front_fov_done", fov_id=fov_id)

      if results:
          write_front_parquet(results, front_parquet)

      per_cell_path = out_dir / "05_aggregated" / "per_cell.parquet"
      if per_cell_path.exists() and results:
          import pandas as pd
          from quantipy_polarity.migration.distance import compute_all_fovs
          import os, tempfile

          df = pd.read_parquet(per_cell_path)
          updated = compute_all_fovs(
              df,
              labels_by_fov,
              {fov: (vx_by_fov[fov], vy_by_fov[fov]) for fov in vx_by_fov},
              {r.fov_id: r for r in results},
          )
          fd, tmp = tempfile.mkstemp(dir=per_cell_path.parent, suffix=".parquet")
          os.close(fd)
          try:
              updated.to_parquet(tmp, index=False)
              os.replace(tmp, per_cell_path)
          except Exception:
              try:
                  os.unlink(tmp)
              except OSError:
                  pass
              raise


  def _stage_plot(cfg: Config, out_dir: Path) -> None:
      """Plot: per_cell.parquet → all figures in 06_plots/."""
      from quantipy_polarity._cli_figures import (
          _generate_vector_maps,
          _generate_rose_plots,
          _generate_front_overlays,
          _generate_summary,
      )
      import pandas as pd
      from quantipy_polarity.migration.front_io import read_front_parquet

      per_cell_path = out_dir / "05_aggregated" / "per_cell.parquet"
      if not per_cell_path.exists():
          raise FileNotFoundError(f"per_cell.parquet not found: {per_cell_path}")

      per_cell = pd.read_parquet(per_cell_path)
      plots_dir = out_dir / "06_plots"
      plots_dir.mkdir(parents=True, exist_ok=True)
      pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)

      from quantipy_polarity.config import InputMasks
      seg_dir = (
          cfg.input.masks_dir if isinstance(cfg.input, InputMasks) else out_dir / "02_segmentation"
      )

      front_parquet_path = out_dir / "04_migration" / "front_um_per_fov.parquet"
      front_df = read_front_parquet(front_parquet_path) if front_parquet_path.exists() else None

      _generate_vector_maps(per_cell, seg_dir, plots_dir, pixel_size_um, cfg.viz)
      _generate_rose_plots(per_cell, plots_dir, cfg.viz)
      if front_df is not None:
          _generate_front_overlays(per_cell, seg_dir, front_df, plots_dir, pixel_size_um)
      _generate_summary(per_cell, plots_dir)


  def _stage_report(cfg: Config, out_dir: Path) -> None:
      """Report: gather all outputs → self-contained report.html."""
      from quantipy_polarity.report.build import build_report

      out_html = out_dir / "report.html"
      build_report(out_dir, out_html, cfg=cfg)
      log.info("report_written", path=str(out_html))
  ```

- [ ] **Step 3: Verify the full pipeline package imports**

  ```bash
  python -c "from quantipy_polarity.pipeline import run_pipeline, STAGES, StageState; print('pipeline OK')"
  ```

  Expected: `pipeline OK`

- [ ] **Step 4: Run baseline tests**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `169 passed, 1 skipped`.

- [ ] **Step 5: Commit**

  ```bash
  git add src/quantipy_polarity/pipeline/run.py
  git commit -m "feat(pipeline): add run.py — in-process stage orchestrator"
  ```

---

## Task 6: Update `report/__init__.py` and create `report/templates/` directory

**Files:** Modify `src/quantipy_polarity/report/__init__.py`; create `src/quantipy_polarity/report/templates/` (directory only, no file yet — the template lands in Task 8)

The existing `report/__init__.py` is a one-line stub. Replace it with a proper public API export once `build.py` exists.

- [ ] **Step 1: Read `src/quantipy_polarity/report/__init__.py`**

  Current content: `"""Self-contained HTML report. Implemented in Phase 5."""`

- [ ] **Step 2: Replace `src/quantipy_polarity/report/__init__.py`**

  ```python
  """Self-contained HTML report generation.

  Public API:
      build_report(results_dir, output_html, *, cfg=None) -> None
  """

  from quantipy_polarity.report.build import build_report

  __all__ = ["build_report"]
  ```

- [ ] **Step 3: Create the `templates/` directory with a placeholder**

  Create `src/quantipy_polarity/report/templates/.gitkeep` (empty file, so git tracks the directory). The real template is added in Task 8.

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/report/__init__.py src/quantipy_polarity/report/templates/.gitkeep
  git commit -m "feat(report): update __init__.py export; scaffold templates/ dir"
  ```

---

## Task 7: Create `report/build.py` — HTML assembly logic

**Files:** Create `src/quantipy_polarity/report/build.py`

`build_report()` reads the run directory, rescales figure PNGs to thumbnails (max 400 px longest edge using PIL/Pillow — already a transitive dependency via scikit-image and matplotlib), base64-encodes them, collects summary metrics from `per_cell.parquet`, and renders the Jinja2 template to a single HTML file. The output HTML has no external URLs; all CSS is inline in the template; all images are `data:image/png;base64,...`.

Decision on large per-FOV PNGs: **downscale to thumbnail** (max 400 px longest edge) before base64-encoding. This caps each thumbnail at ~50–100 KB, keeping the HTML file under ~5 MB even for 20+ FOV experiments. Full-resolution images remain on disk in `06_plots/`; the HTML includes a relative path hint for users who want to open the originals.

- [ ] **Step 1: Create `src/quantipy_polarity/report/build.py`**

  ```python
  """HTML report builder for quantipy run outputs.

  Gathers all pipeline outputs from a run directory, downscales figure PNGs
  to thumbnails (max 400 px longest edge), base64-encodes them, and renders
  the Jinja2 template to a single self-contained HTML file.

  No external URLs, no CDN dependencies. All CSS is inline in the template.
  """

  from __future__ import annotations

  import base64
  import io
  import os
  import tempfile
  from pathlib import Path
  from typing import TYPE_CHECKING

  import structlog

  if TYPE_CHECKING:
      from quantipy_polarity.config import Config

  log = structlog.get_logger()

  _THUMBNAIL_MAX_PX = 400  # longest edge of embedded thumbnails


  def _encode_png_thumbnail(path: Path, max_px: int = _THUMBNAIL_MAX_PX) -> str:
      """Load a PNG, downscale to max_px on longest edge, return base64 data URI.

      Uses PIL (Pillow) which is a transitive dependency via matplotlib/scikit-image.

      Args:
          path: Path to PNG file.
          max_px: Maximum pixels on the longest edge.

      Returns:
          base64 data URI string: "data:image/png;base64,<data>"
      """
      from PIL import Image

      img = Image.open(path)
      img.thumbnail((max_px, max_px), Image.LANCZOS)
      buf = io.BytesIO()
      img.save(buf, format="PNG", optimize=True)
      data = base64.b64encode(buf.getvalue()).decode("ascii")
      return f"data:image/png;base64,{data}"


  def _encode_file_b64(path: Path) -> str:
      """Base64-encode any binary file as a data URI (PDF → application/pdf)."""
      ext = path.suffix.lower()
      mime = "application/pdf" if ext == ".pdf" else "image/png"
      data = base64.b64encode(path.read_bytes()).decode("ascii")
      return f"data:{mime};base64,{data}"


  def gather_report_inputs(results_dir: Path) -> dict:
      """Collect all inputs needed to render the HTML report template.

      Args:
          results_dir: Base run output directory.

      Returns:
          Dictionary with keys used by the Jinja2 template.
      """
      import pandas as pd
      import yaml

      data: dict = {
          "project_name": results_dir.name,
          "results_dir": str(results_dir),
          "n_fovs": 0,
          "n_cells": 0,
          "median_magnitude": None,
          "config_yaml": "",
          "fov_rows": [],
          "has_rose": False,
          "aggregate_rose_b64": None,
          "has_summary": False,
          "population_summary_b64": None,
          "stage_statuses": {},
      }

      # Load per_cell parquet for summary metrics
      per_cell_path = results_dir / "05_aggregated" / "per_cell.parquet"
      if per_cell_path.exists():
          df = pd.read_parquet(per_cell_path)
          data["n_cells"] = len(df)
          data["n_fovs"] = int(df["fov_id"].nunique())
          if "magnitude" in df.columns and len(df) > 0:
              data["median_magnitude"] = round(float(df["magnitude"].median()), 4)

      # Load config snapshot
      config_snapshot = results_dir / "config.snapshot.yaml"
      if config_snapshot.exists():
          data["config_yaml"] = config_snapshot.read_text()

      # Load stage statuses
      stage_status_dir = results_dir / "stage_status"
      if stage_status_dir.exists():
          for json_path in sorted(stage_status_dir.glob("*.json")):
              import json as _json
              try:
                  rec = _json.loads(json_path.read_text())
                  data["stage_statuses"][json_path.stem] = rec.get("status", "unknown")
              except Exception:
                  data["stage_statuses"][json_path.stem] = "unreadable"

      # Per-FOV gallery: vector map PNG + rose PNG per FOV
      plots_dir = results_dir / "06_plots"
      fov_rows: list[dict] = []
      if plots_dir.exists():
          vec_dir = plots_dir / "vector_maps"
          rose_dir = plots_dir / "roses"
          # Collect all known FOV IDs from vector maps
          fov_ids: list[str] = []
          if vec_dir.exists():
              fov_ids = sorted(
                  p.stem.replace("_vector_map", "").replace("_polarity_map", "")
                  for p in vec_dir.glob("*.png")
              )
          for fov_id in fov_ids:
              row: dict = {"fov_id": fov_id, "vector_b64": None, "rose_b64": None, "n_cells": 0}
              vec_png = vec_dir / f"{fov_id}.png"
              if not vec_png.exists():
                  # Try alternate naming patterns written by viz/vector_map.py
                  candidates = list(vec_dir.glob(f"{fov_id}*.png"))
                  vec_png = candidates[0] if candidates else vec_png
              if vec_png.exists():
                  row["vector_b64"] = _encode_png_thumbnail(vec_png)
              rose_png = rose_dir / f"rose_{fov_id}.png" if rose_dir.exists() else None
              if rose_png and rose_png.exists():
                  row["rose_b64"] = _encode_png_thumbnail(rose_png)
              # Cell count for this FOV
              if per_cell_path.exists():
                  df = pd.read_parquet(per_cell_path)
                  n = int((df["fov_id"] == fov_id).sum())
                  row["n_cells"] = n
              fov_rows.append(row)
      data["fov_rows"] = fov_rows

      # Aggregate rose
      agg_rose = plots_dir / "rose_aggregate.png" if plots_dir.exists() else None
      if agg_rose and agg_rose.exists():
          data["has_rose"] = True
          data["aggregate_rose_b64"] = _encode_png_thumbnail(agg_rose, max_px=600)

      # Population summary
      summary_png = plots_dir / "population_summary.png" if plots_dir.exists() else None
      if summary_png and summary_png.exists():
          data["has_summary"] = True
          data["population_summary_b64"] = _encode_png_thumbnail(summary_png, max_px=800)

      return data


  def build_report(
      results_dir: Path,
      output_html: Path,
      *,
      cfg: "Config | None" = None,
  ) -> None:
      """Render the self-contained HTML report and write it atomically.

      Args:
          results_dir: Base run output directory.
          output_html: Destination HTML file path.
          cfg: Optional Config object (used for project.name if available).
      """
      from importlib.resources import files as _pkg_files
      from jinja2 import Environment, BaseLoader

      template_path = Path(__file__).parent / "templates" / "report.html.j2"
      if not template_path.exists():
          raise FileNotFoundError(
              f"Report template not found: {template_path}. "
              "This is a packaging error — template should be included with the package."
          )

      template_source = template_path.read_text(encoding="utf-8")
      env = Environment(loader=BaseLoader(), autoescape=True)
      template = env.from_string(template_source)

      template_data = gather_report_inputs(results_dir)
      if cfg is not None and cfg.project.name:
          template_data["project_name"] = cfg.project.name

      html_content = template.render(**template_data)

      output_html = Path(output_html)
      output_html.parent.mkdir(parents=True, exist_ok=True)
      fd, tmp = tempfile.mkstemp(dir=output_html.parent, suffix=".tmp.html")
      os.close(fd)
      try:
          with open(tmp, "w", encoding="utf-8") as f:
              f.write(html_content)
          os.replace(tmp, output_html)
      except Exception:
          try:
              os.unlink(tmp)
          except OSError:
              pass
          raise

      log.info("report_html_written", path=str(output_html), size_kb=output_html.stat().st_size // 1024)
  ```

- [ ] **Step 2: Run baseline tests (build.py imports but template is not yet created — that is OK)**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `169 passed, 1 skipped`.

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/report/build.py
  git commit -m "feat(report): add build.py — gather_report_inputs + build_report with thumbnail encoding"
  ```

---

## Task 8: Create `report/templates/report.html.j2` — Jinja2 HTML template

**Files:** Create `src/quantipy_polarity/report/templates/report.html.j2`

The template must be fully self-contained: all CSS inline in a `<style>` block, no `<link>` tags to external stylesheets, no `<script src="...">` tags pointing outside the file. Images are referenced only via the base64 data URIs passed in from `build.py`. The template is intentionally minimal — clean tabular layout, readable on any browser.

Sections in order:
1. Header: project name, timestamp, results directory path.
2. Summary metrics table: N FOVs, N cells, median magnitude.
3. Stage status table: each stage name → status badge (color-coded: done=green, failed=red, running=yellow, pending=grey).
4. Per-FOV gallery: one row per FOV with vector map thumbnail, rose thumbnail (if available), N cells chip.
5. Aggregate rose (if available).
6. Population summary (if available).
7. Config block: expandable `<details><summary>` containing the YAML snapshot.

- [ ] **Step 1: Create `src/quantipy_polarity/report/templates/report.html.j2`**

  Write the full Jinja2 template. Key Jinja2 variables used (must match `gather_report_inputs()` keys):
  - `project_name`, `results_dir`, `n_fovs`, `n_cells`, `median_magnitude`
  - `stage_statuses` (dict: stage_name → status string)
  - `fov_rows` (list of dicts: fov_id, vector_b64, rose_b64, n_cells)
  - `has_rose`, `aggregate_rose_b64`
  - `has_summary`, `population_summary_b64`
  - `config_yaml`

  Template structure:

  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QuantiPy Report — {{ project_name }}</title>
  <style>
  /* --- Reset + base --- */
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 12px;
         color: #222; background: #f8f8f8; padding: 20px; }
  h1 { font-size: 18px; font-weight: bold; margin-bottom: 4px; }
  h2 { font-size: 14px; font-weight: bold; margin: 20px 0 8px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
  p  { margin-bottom: 6px; color: #555; font-size: 11px; }
  table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
  th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; vertical-align: middle; }
  th { background: #eee; font-weight: bold; }
  img { max-width: 100%; height: auto; display: block; border: 1px solid #ddd; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #fff; }
  .badge-done    { background: #4a8c4a; }
  .badge-failed  { background: #b03030; }
  .badge-running { background: #c47a20; }
  .badge-pending { background: #888; }
  .badge-unknown { background: #aaa; }
  details { margin-top: 8px; }
  summary { cursor: pointer; font-weight: bold; font-size: 12px; }
  pre { background: #f0f0f0; padding: 12px; font-size: 10px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #ddd; margin-top: 6px; }
  .fov-cell { text-align: center; font-size: 10px; }
  </style>
  </head>
  <body>

  <h1>QuantiPy Polarity Report</h1>
  <p><strong>Project:</strong> {{ project_name }}</p>
  <p><strong>Results:</strong> {{ results_dir }}</p>
  <p><strong>Generated:</strong> {{ now }}</p>

  <h2>Summary</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>FOVs</td><td>{{ n_fovs }}</td></tr>
    <tr><td>Cells</td><td>{{ n_cells }}</td></tr>
    <tr><td>Median polarity magnitude</td><td>{% if median_magnitude is not none %}{{ median_magnitude }}{% else %}—{% endif %}</td></tr>
  </table>

  <h2>Pipeline Stage Status</h2>
  <table>
    <tr><th>Stage</th><th>Status</th></tr>
    {% for stage, status in stage_statuses.items() %}
    <tr>
      <td>{{ stage }}</td>
      <td><span class="badge badge-{{ status }}">{{ status }}</span></td>
    </tr>
    {% else %}
    <tr><td colspan="2">No stage status files found.</td></tr>
    {% endfor %}
  </table>

  {% if fov_rows %}
  <h2>Per-FOV Gallery</h2>
  <table>
    <tr><th>FOV</th><th>Vector Map</th><th>Rose Plot</th><th>N Cells</th></tr>
    {% for row in fov_rows %}
    <tr>
      <td>{{ row.fov_id }}</td>
      <td class="fov-cell">
        {% if row.vector_b64 %}<img src="{{ row.vector_b64 }}" alt="vector map {{ row.fov_id }}">{% else %}—{% endif %}
      </td>
      <td class="fov-cell">
        {% if row.rose_b64 %}<img src="{{ row.rose_b64 }}" alt="rose {{ row.fov_id }}">{% else %}—{% endif %}
      </td>
      <td>{{ row.n_cells }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}

  {% if has_rose and aggregate_rose_b64 %}
  <h2>Aggregate Rose Plot</h2>
  <img src="{{ aggregate_rose_b64 }}" alt="aggregate rose plot" style="max-width: 500px; margin: 0 auto;">
  {% endif %}

  {% if has_summary and population_summary_b64 %}
  <h2>Population Summary</h2>
  <img src="{{ population_summary_b64 }}" alt="population summary" style="max-width: 700px; margin: 0 auto;">
  {% endif %}

  <h2>Run Configuration</h2>
  <details>
    <summary>Expand YAML snapshot</summary>
    <pre>{{ config_yaml }}</pre>
  </details>

  <p style="margin-top: 24px; color: #aaa; font-size: 10px;">
    Generated by QuantiPy Polarity. Images are embedded as base64 thumbnails (max {{ thumbnail_max_px }}px); originals in results/06_plots/.
  </p>

  </body>
  </html>
  ```

  Note: `now` and `thumbnail_max_px` must be injected by `build_report()`. Update `build_report()` in Task 7 to pass them:
  - `template_data["now"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())`
  - `template_data["thumbnail_max_px"] = _THUMBNAIL_MAX_PX`

  Also update `build.py` to import `time` at the top and add these two lines before `template.render(...)`.

- [ ] **Step 2: Update `report/build.py`**

  In `build_report()`, just before `html_content = template.render(...)`, add:
  ```python
  import time as _time
  template_data["now"] = _time.strftime("%Y-%m-%d %H:%M UTC", _time.gmtime())
  template_data["thumbnail_max_px"] = _THUMBNAIL_MAX_PX
  ```

- [ ] **Step 3: Verify template renders with empty data**

  ```bash
  python -c "
  from pathlib import Path
  from jinja2 import Environment, BaseLoader
  tmpl = (Path('src/quantipy_polarity/report/templates/report.html.j2')).read_text()
  env = Environment(loader=BaseLoader(), autoescape=True)
  t = env.from_string(tmpl)
  html = t.render(project_name='test', results_dir='/tmp', n_fovs=0, n_cells=0,
                  median_magnitude=None, stage_statuses={}, fov_rows=[], has_rose=False,
                  aggregate_rose_b64=None, has_summary=False, population_summary_b64=None,
                  config_yaml='', now='2026-05-26', thumbnail_max_px=400)
  assert '<!DOCTYPE html>' in html
  assert 'QuantiPy Polarity Report' in html
  print('template renders OK, len:', len(html))
  "
  ```

  Expected: `template renders OK, len: <some positive number>`

- [ ] **Step 4: Run baseline tests**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `169 passed, 1 skipped`.

- [ ] **Step 5: Commit**

  ```bash
  git add src/quantipy_polarity/report/templates/report.html.j2 src/quantipy_polarity/report/build.py
  git commit -m "feat(report): add Jinja2 HTML template + inject now/thumbnail_max_px in build_report"
  ```

---

## Task 9: Create `_cli_ingest.py` — real `quantipy ingest`

**Files:** Create `src/quantipy_polarity/_cli_ingest.py`

`quantipy ingest` is an "Advanced" command that runs just the ingest stage: nd2/tif → normalized per-FOV TIFs in `01_ingest/`. For `masks` mode, it exits with a clear message that ingest is not needed (masks are already the source). It writes a `stage_status/ingest.json` via `pipeline/state.py`.

- [ ] **Step 1: Create `src/quantipy_polarity/_cli_ingest.py`**

  ```python
  """Real `quantipy ingest` command — nd2/tif → normalized per-FOV TIFs.

  Writes per-FOV membrane TIFs to <output>/01_ingest/.
  Records stage status in <output>/stage_status/ingest.json.
  Skipped automatically for masks input mode (pre-segmented inputs need no ingest).
  """

  from __future__ import annotations

  from pathlib import Path

  import click
  import structlog

  from quantipy_polarity.cli import main
  from quantipy_polarity.config import Config

  log = structlog.get_logger()


  @main.command(
      "ingest",
      short_help="[Advanced] nd2/tif → normalized per-FOV TIFs (01_ingest/)",
  )
  @click.option(
      "--config",
      "config_path",
      required=True,
      type=click.Path(exists=True, path_type=Path),
      help="Path to quantipy YAML config.",
  )
  @click.option(
      "--output",
      "output_path",
      required=False,
      type=click.Path(path_type=Path),
      default=None,
      help="Output directory (overrides config project.output_dir).",
  )
  @click.option(
      "--force",
      is_flag=True,
      default=False,
      help="Re-run even if stage already done.",
  )
  def ingest_cmd(
      config_path: Path,
      output_path: Path | None,
      force: bool,
  ) -> None:
      """Ingest nd2/tif inputs → normalized per-FOV membrane TIFs in 01_ingest/.

      \b
      Outputs (in <output>/01_ingest/):
          <fov_id>_membrane.tif   uint16 normalized membrane channel
      Stage status written to <output>/stage_status/ingest.json.
      Skipped for input.mode = 'masks' (no ingest needed).
      """
      from quantipy_polarity.config import InputMasks
      from quantipy_polarity.io.ingest import ingest_fovs
      from quantipy_polarity.pipeline.state import (
          config_hash,
          read_stage_state,
          write_stage_state,
      )
      from quantipy_polarity.pipeline.dag import should_skip_stage

      cfg = Config.from_yaml(config_path)
      out_dir = Path(output_path or cfg.project.output_dir)
      out_dir.mkdir(parents=True, exist_ok=True)

      if isinstance(cfg.input, InputMasks):
          click.echo(
              "input.mode = 'masks': ingest is not needed — "
              "your masks and membranes are already on disk. "
              "Run `quantipy polarity` next."
          )
          return

      chash = config_hash(cfg)
      state = read_stage_state(out_dir, "ingest")
      if should_skip_stage(state, chash, force=force):
          click.echo("Ingest already done (matching config_hash). Use --force to re-run.")
          return

      write_stage_state(out_dir, "ingest", "running", cfg=cfg)
      try:
          fov_ids = ingest_fovs(cfg, out_dir)
          write_stage_state(
              out_dir, "ingest", "done",
              cfg=cfg,
              preserve_started_at=True,
              output_paths=[str(out_dir / "01_ingest" / f"{fid}_membrane.tif") for fid in fov_ids],
          )
      except Exception:
          write_stage_state(out_dir, "ingest", "failed", cfg=cfg, preserve_started_at=True)
          raise

      click.echo(f"Ingest complete. {len(fov_ids)} FOV(s) written to {out_dir / '01_ingest'}")
  ```

- [ ] **Step 2: Verify import (the command is not yet registered in cli.py — done in Task 13)**

  ```bash
  python -c "from quantipy_polarity._cli_ingest import ingest_cmd; print('ingest_cmd OK')"
  ```

  Expected: `ingest_cmd OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/_cli_ingest.py
  git commit -m "feat(cli): add _cli_ingest.py — real quantipy ingest command"
  ```

---

## Task 10: Create `_cli_run.py` — real `quantipy run`

**Files:** Create `src/quantipy_polarity/_cli_run.py`

Replace the stub. `quantipy run` is the Primary command. It calls `run_pipeline()` and handles the three safety modes: default (refuses to overwrite non-empty results dir), `--resume`, and `--force`. Also accepts `--stage` (repeatable) to run a subset of stages (used in tests).

- [ ] **Step 1: Create `src/quantipy_polarity/_cli_run.py`**

  ```python
  """Real `quantipy run` — single-shot pipeline orchestrator.

  Behavior:
    - Default (no flags): refuses to overwrite a non-empty output dir.
      Error message suggests --resume or --force.
    - --resume: skips stages already in 'done' state with matching config_hash.
    - --force: ignores all stage caches; re-runs from scratch.
    - --stage STAGE (repeatable): run only the named stage(s) in canonical order.
  """

  from __future__ import annotations

  import sys
  from pathlib import Path

  import click
  import structlog

  from quantipy_polarity.cli import main
  from quantipy_polarity.config import Config

  log = structlog.get_logger()


  @main.command("run", short_help="Single-shot: input → all outputs")
  @click.option(
      "--config",
      "config_path",
      required=True,
      type=click.Path(exists=True, path_type=Path),
      help="Path to quantipy YAML config.",
  )
  @click.option(
      "--output",
      "output_path",
      required=False,
      type=click.Path(path_type=Path),
      default=None,
      help="Output directory (overrides config project.output_dir).",
  )
  @click.option(
      "--resume",
      is_flag=True,
      default=False,
      help="Skip stages already marked done with matching config hash.",
  )
  @click.option(
      "--force",
      is_flag=True,
      default=False,
      help="Ignore stage caches; re-run all stages from scratch.",
  )
  @click.option(
      "--stage",
      "stages",
      multiple=True,
      default=None,
      help="Run only this stage (repeatable). Default: all stages.",
  )
  def run_cmd(
      config_path: Path,
      output_path: Path | None,
      resume: bool,
      force: bool,
      stages: tuple[str, ...],
  ) -> None:
      """Single-shot pipeline: input → segmentation → polarity → front → figures → report.

      \b
      Modes:
        (default)  Refuses to overwrite non-empty output dir.
        --resume   Skip stages already done with matching config hash.
        --force    Wipe stage cache, re-run everything.
        --stage    Run only named stage(s) in canonical order (Advanced).

      Stage order: ingest → segment → polarity → front → aggregate → plot → report
      """
      from quantipy_polarity.pipeline.run import run_pipeline
      from quantipy_polarity.pipeline.state import read_stage_state

      cfg = Config.from_yaml(config_path)
      out_dir = Path(output_path or cfg.project.output_dir)

      # Safety check: refuse to overwrite without explicit --resume or --force
      if out_dir.exists() and any(out_dir.iterdir()):
          if not resume and not force:
              raise click.ClickException(
                  f"Output directory {out_dir} is non-empty. "
                  "Use --resume to continue from the last successful stage, "
                  "or --force to wipe and restart."
              )

      stage_list: list[str] | None = list(stages) if stages else None

      try:
          run_pipeline(cfg, out_dir, force=force, stages=stage_list)
      except RuntimeError as exc:
          # run_pipeline already wrote status=failed and logged the error
          raise click.ClickException(str(exc)) from exc

      click.echo(f"\nPipeline complete. Report: {out_dir / 'report.html'}")
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity._cli_run import run_cmd; print('run_cmd OK')"
  ```

  Expected: `run_cmd OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/_cli_run.py
  git commit -m "feat(cli): add _cli_run.py — real quantipy run with resume/force/stage"
  ```

---

## Task 11: Create `_cli_report.py` — real `quantipy report`

**Files:** Create `src/quantipy_polarity/_cli_report.py`

`quantipy report` regenerates `report.html` from an existing run directory without re-running any pipeline stage. This is the "Advanced" standalone report command. It calls `build_report()` directly.

- [ ] **Step 1: Create `src/quantipy_polarity/_cli_report.py`**

  ```python
  """Real `quantipy report` — regenerate HTML report from a completed run directory.

  Does not re-run any pipeline stage. Reads whatever outputs currently exist
  in the run directory. Useful after editing config or adding annotations.
  """

  from __future__ import annotations

  from pathlib import Path

  import click

  from quantipy_polarity.cli import main


  @main.command(
      "report",
      short_help="[Advanced] Regenerate HTML report from a run directory",
  )
  @click.option(
      "--results",
      "results_dir",
      required=True,
      type=click.Path(exists=True, path_type=Path),
      help="Run directory (the output directory from quantipy run).",
  )
  @click.option(
      "--output",
      "output_html",
      required=False,
      type=click.Path(path_type=Path),
      default=None,
      help="Output HTML path. Default: <results>/report.html.",
  )
  @click.option(
      "--config",
      "config_path",
      required=False,
      type=click.Path(exists=True, path_type=Path),
      default=None,
      help="Optional config YAML for project.name injection.",
  )
  def report_cmd(
      results_dir: Path,
      output_html: Path | None,
      config_path: Path | None,
  ) -> None:
      """Regenerate the self-contained HTML report from an existing run directory.

      Reads 05_aggregated/per_cell.parquet, 06_plots/, and stage_status/ from
      <results>. Does NOT re-run segmentation, polarity, or any other stage.

      Output is a single self-contained HTML file with all images base64-embedded.
      """
      from quantipy_polarity.config import Config
      from quantipy_polarity.report.build import build_report

      cfg: "Config | None" = None
      if config_path is not None:
          cfg = Config.from_yaml(config_path)

      out_html = output_html or (results_dir / "report.html")
      build_report(results_dir, out_html, cfg=cfg)
      click.echo(f"Report written: {out_html}")
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity._cli_report import report_cmd; print('report_cmd OK')"
  ```

  Expected: `report_cmd OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/_cli_report.py
  git commit -m "feat(cli): add _cli_report.py — real quantipy report command"
  ```

---

## Task 12: Refactor `_cli_segment.py` — delegate to `io/ingest.py`

**Files:** Modify `src/quantipy_polarity/_cli_segment.py`

Replace the inline `_build_fov_iterator()` function with a call to `io/ingest.build_fov_iterator()` from Task 1. This eliminates duplication without changing any behavior (all tests still pass). The `_run_segment()` and `segment_cmd` functions are unchanged.

- [ ] **Step 1: Read the current `_build_fov_iterator` implementation in `_cli_segment.py` (lines 163–204, already read above)**

- [ ] **Step 2: Replace `_build_fov_iterator` in `_cli_segment.py`**

  Remove the 42-line `_build_fov_iterator()` function body and replace it with a one-line delegation:

  ```python
  def _build_fov_iterator(cfg: Config):
      """Return an iterable of FOV objects. Delegates to io/ingest.build_fov_iterator."""
      from quantipy_polarity.io.ingest import build_fov_iterator
      return build_fov_iterator(cfg)
  ```

  All other lines in `_cli_segment.py` remain unchanged.

- [ ] **Step 3: Verify `_build_fov_iterator` still works**

  ```bash
  python -c "from quantipy_polarity._cli_segment import _build_fov_iterator; print('delegation OK')"
  ```

  Expected: `delegation OK`

- [ ] **Step 4: Run full pytest suite**

  ```bash
  pytest -q 2>&1 | tail -5
  ```

  Expected: `169 passed, 1 skipped`. No regressions from this refactor.

- [ ] **Step 5: Commit**

  ```bash
  git add src/quantipy_polarity/_cli_segment.py
  git commit -m "refactor(segment): delegate _build_fov_iterator to io/ingest.build_fov_iterator"
  ```

---

## Task 13: Wire new CLI commands; remove stubs for `run`, `report`, `ingest`

**Files:** Modify `src/quantipy_polarity/_stubs.py`; modify `src/quantipy_polarity/cli.py`

Remove the three stub entries for `run`, `report`, and `ingest` from `_stubs.py`. Import the three new CLI modules in `cli.py`. The remaining stubs (`download-demo`, `debug`, `validate`, `analyze`) are untouched.

- [ ] **Step 1: Edit `_stubs.py`** — remove the `"run"`, `"report"`, and `"ingest"` entries from `_STUBS`

  After the edit, `_STUBS` should contain only: `"download-demo"`, `"debug"`, `"validate"`, `"analyze"`.

- [ ] **Step 2: Edit `cli.py`** — add three import lines after the existing Phase 4 imports

  ```python
  from quantipy_polarity import _cli_ingest as _cli_ingest  # noqa: E402,F401
  from quantipy_polarity import _cli_run as _cli_run  # noqa: E402,F401
  from quantipy_polarity import _cli_report as _cli_report  # noqa: E402,F401
  ```

- [ ] **Step 3: Verify no import errors and command list**

  ```bash
  python -c "from quantipy_polarity.cli import main; cmds = list(main.commands.keys()); print(sorted(cmds))"
  ```

  Expected output includes: `['aggregate', 'analyze', 'debug', 'download-demo', 'front', 'ingest', 'init-config', 'plot', 'polarity', 'report', 'run', 'segment', 'validate']`

- [ ] **Step 4: Confirm `quantipy run --help` no longer shows stub message**

  ```bash
  quantipy run --help 2>&1 | head -5
  ```

  Expected: Shows real help text with `--config`, `--resume`, `--force` options.

- [ ] **Step 5: Run full pytest suite**

  ```bash
  pytest -q 2>&1 | tail -5
  ```

  Expected: `169 passed, 1 skipped`. (The three stub tests for run/report/ingest in `test_cli_stubs.py` should now fail if they assert the stub error message — see Task 13 notes.)

  Note: If `tests/test_cli_stubs.py` asserts that `run`, `report`, and `ingest` emit the stub error message, those assertions will now fail because the real commands are wired. Update `test_cli_stubs.py` to remove those three command names from the stub test. This is a one-line change per removed command; the test file tests that the remaining stubs (`download-demo`, `debug`, `validate`, `analyze`) still emit error messages.

- [ ] **Step 6: Update `test_cli_stubs.py` if needed**

  ```bash
  grep -n '"run"\|"report"\|"ingest"' tests/test_cli_stubs.py
  ```

  Remove any references to `"run"`, `"report"`, `"ingest"` from the stub test parameters.

- [ ] **Step 7: Re-run pytest**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `169 passed, 1 skipped` (or slightly fewer if stub tests for those 3 commands existed; the count may change by ≤3 depending on test parameterization).

- [ ] **Step 8: Commit**

  ```bash
  git add src/quantipy_polarity/_stubs.py src/quantipy_polarity/cli.py tests/test_cli_stubs.py
  git commit -m "feat(cli): wire run/report/ingest real commands; remove their stubs"
  ```

---

## Task 14: Tests for `pipeline/state.py`

**Files:** Create `tests/pipeline/__init__.py`; create `tests/pipeline/test_state.py`

- [ ] **Step 1: Create `tests/pipeline/__init__.py`** (empty)

- [ ] **Step 2: Create `tests/pipeline/test_state.py`**

  Tests:
  1. `test_write_and_read_round_trip` — write `"running"` then `"done"` state; read back; assert fields.
  2. `test_atomic_write_produces_no_tmp_file` — after `write_stage_state`, assert no `.tmp.json` files remain.
  3. `test_read_returns_none_if_absent` — calling `read_stage_state` with no JSON returns None.
  4. `test_config_hash_is_16_hex_chars` — `config_hash(cfg)` returns a 16-char hex string.
  5. `test_write_state_preserve_started_at` — writing `"running"` then `"done"` with `preserve_started_at=True` keeps the original `started_at`.
  6. `test_write_state_creates_stage_status_dir` — `write_stage_state` creates `stage_status/` if absent.

  Each test uses `tmp_path` fixture. Construct a minimal Config with `masks` mode.

- [ ] **Step 3: Run new tests**

  ```bash
  pytest tests/pipeline/test_state.py -v 2>&1 | tail -15
  ```

  Expected: 6 passed.

- [ ] **Step 4: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: 175+ passed (169 + 6 new).

- [ ] **Step 5: Commit**

  ```bash
  git add tests/pipeline/__init__.py tests/pipeline/test_state.py
  git commit -m "test(pipeline): add state.py tests — round-trip, atomic write, config_hash"
  ```

---

## Task 15: Tests for `pipeline/dag.py`

**Files:** Create `tests/pipeline/test_dag.py`

- [ ] **Step 1: Create `tests/pipeline/test_dag.py`**

  Tests:
  1. `test_stages_canonical_order` — `STAGES` = `("ingest", "segment", "polarity", "front", "aggregate", "plot", "report")`.
  2. `test_should_skip_done_matching_hash` — `should_skip_stage(done_state, same_hash)` returns True.
  3. `test_should_not_skip_failed_stage` — `should_skip_stage(failed_state, same_hash)` returns False.
  4. `test_should_not_skip_hash_mismatch` — `should_skip_stage(done_state, different_hash)` returns False.
  5. `test_should_not_skip_when_force` — `should_skip_stage(done_state, same_hash, force=True)` returns False.
  6. `test_should_not_skip_none_state` — `should_skip_stage(None, any_hash)` returns False.
  7. `test_filter_stages_none_returns_all` — `filter_stages(None)` returns all 7 in canonical order.
  8. `test_filter_stages_subset_preserves_order` — `filter_stages(["report", "polarity"])` returns `["polarity", "report"]`.
  9. `test_filter_stages_unknown_raises` — `filter_stages(["bogus"])` raises `ValueError`.

- [ ] **Step 2: Run new tests**

  ```bash
  pytest tests/pipeline/test_dag.py -v 2>&1 | tail -15
  ```

  Expected: 9 passed.

- [ ] **Step 3: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add tests/pipeline/test_dag.py
  git commit -m "test(pipeline): add dag.py tests — stage order, skip logic, filter_stages"
  ```

---

## Task 16: Tests for `pipeline/run.py` — orchestrator behaviour

**Files:** Create `tests/pipeline/test_run_pipeline.py`

These tests use synthetic data (the existing `tests/fixtures/` NPZ fixture) and mock the heavy per-stage functions to keep tests fast. The orchestrator logic (state writes, skip, force, failure propagation) can be tested by patching `_stage_ingest`, `_stage_segment`, etc.

- [ ] **Step 1: Create `tests/pipeline/test_run_pipeline.py`**

  Tests:
  1. `test_run_pipeline_all_stages_called` — mock all 7 `_stage_*` functions; verify each called once.
  2. `test_run_pipeline_skips_done_stage` — pre-write a `done` state for one stage with matching config_hash; verify that stage's mock is NOT called.
  3. `test_run_pipeline_force_overrides_skip` — pre-write `done` state; call with `force=True`; verify mock IS called.
  4. `test_run_pipeline_writes_stage_status` — let one real stage run (use `_stage_ingest` on a masks-mode config — it exits early); assert `stage_status/ingest.json` exists and reads `done`.
  5. `test_run_pipeline_failed_stage_writes_failed_status` — patch one `_stage_*` to raise; call `run_pipeline`; assert that stage's JSON has `status=failed`; assert `RuntimeError` is raised.
  6. `test_run_pipeline_failed_stage_halts_downstream` — patch `_stage_polarity` to raise; assert `_stage_aggregate` mock is NOT called.
  7. `test_run_pipeline_subset_stages` — call with `stages=["polarity", "aggregate"]` (mocked); verify only those two mocks are called.
  8. `test_run_pipeline_writes_config_snapshot` — call with mocked stages; assert `config.snapshot.yaml` exists in out_dir.

  Use `unittest.mock.patch` to patch the stage functions. Construct a minimal `masks`-mode Config using `tmp_path`.

- [ ] **Step 2: Run new tests**

  ```bash
  pytest tests/pipeline/test_run_pipeline.py -v 2>&1 | tail -20
  ```

  Expected: 8 passed.

- [ ] **Step 3: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add tests/pipeline/test_run_pipeline.py
  git commit -m "test(pipeline): add run_pipeline tests — stages, skip, force, failure, subset"
  ```

---

## Task 17: Tests for `report/build.py`

**Files:** Create `tests/report/__init__.py`; create `tests/report/test_build.py`

- [ ] **Step 1: Create `tests/report/__init__.py`** (empty)

- [ ] **Step 2: Create `tests/report/test_build.py`**

  Tests:
  1. `test_gather_report_inputs_empty_dir` — call `gather_report_inputs(tmp_path)` on an empty dir; assert returns a dict with `n_cells=0`, `fov_rows=[]`.
  2. `test_gather_report_inputs_with_parquet` — write a tiny per_cell parquet to `05_aggregated/per_cell.parquet`; assert `n_cells` and `n_fovs` correct.
  3. `test_gather_report_inputs_loads_config_yaml` — write `config.snapshot.yaml` with content "foo: bar"; assert `config_yaml == "foo: bar\n"`.
  4. `test_gather_report_inputs_loads_stage_statuses` — write two stage JSON files; assert `stage_statuses` dict populated.
  5. `test_build_report_creates_html_file` — call `build_report(tmp_path, tmp_path / "out.html")`; assert file exists and contains `<!DOCTYPE html>`.
  6. `test_build_report_no_external_urls` — build HTML from an empty dir; assert "http" does not appear in the file contents (no CDN references).
  7. `test_build_report_atomic_write_no_tmp_left` — after `build_report`, assert no `.tmp.html` files remain in output dir.
  8. `test_encode_png_thumbnail_downscales` — create a 1000×1000 px PNG; call `_encode_png_thumbnail`; decode the base64; open with PIL; assert longest edge ≤ 400.

  Use `tmp_path`. For the parquet tests, construct a minimal DataFrame with columns matching `PER_CELL_COLUMNS`.

- [ ] **Step 3: Run new tests**

  ```bash
  pytest tests/report/test_build.py -v 2>&1 | tail -20
  ```

  Expected: 8 passed.

- [ ] **Step 4: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add tests/report/__init__.py tests/report/test_build.py
  git commit -m "test(report): add build.py tests — HTML self-contained, thumbnail scaling, atomic write"
  ```

---

## Task 18: Tests for the Jinja2 template

**Files:** Create `tests/report/test_template.py`

- [ ] **Step 1: Create `tests/report/test_template.py`**

  Tests:
  1. `test_template_renders_project_name` — render with `project_name="My Exp"`; assert in HTML.
  2. `test_template_renders_stage_statuses` — render with `stage_statuses={"ingest": "done", "segment": "failed"}`; assert both stage names and badge classes appear.
  3. `test_template_renders_fov_row` — render with a `fov_rows` entry that has `vector_b64="data:image/png;base64,abc"`; assert the `<img src=` attribute appears in HTML.
  4. `test_template_no_http_refs` — render with empty data; assert `http://` and `https://` do not appear (no CDN).
  5. `test_template_config_yaml_in_details` — render with `config_yaml="k: v"`; assert in `<pre>` block.

  Load template directly from `Path("src/quantipy_polarity/report/templates/report.html.j2")`.

- [ ] **Step 2: Run new tests**

  ```bash
  pytest tests/report/test_template.py -v 2>&1 | tail -15
  ```

  Expected: 5 passed.

- [ ] **Step 3: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add tests/report/test_template.py
  git commit -m "test(report): add Jinja2 template rendering tests"
  ```

---

## Task 19: Tests for `io/ingest.py`

**Files:** Create `tests/io/test_ingest.py`

(A `tests/io/__init__.py` may already exist; check and create if absent.)

- [ ] **Step 1: Check if `tests/io/__init__.py` exists**

  ```bash
  ls tests/io/
  ```

  Create it if absent: `touch tests/io/__init__.py`

- [ ] **Step 2: Create `tests/io/test_ingest.py`**

  Tests:
  1. `test_write_ingest_outputs_creates_tif` — call `write_ingest_outputs(tmp_path, "FOV_01", membrane)`; assert `tmp_path/01_ingest/FOV_01_membrane.tif` exists and is a valid TIF.
  2. `test_write_ingest_outputs_is_uint16` — open the written TIF with tifffile; assert dtype is uint16.
  3. `test_write_ingest_outputs_atomic_no_tmp_left` — after writing, assert no `.tmp.tif` files remain.
  4. `test_write_ingest_outputs_scales_correctly` — write membrane of all-ones float32; assert max pixel value = 65535.
  5. `test_ingest_fovs_masks_mode_returns_fov_ids` — build a `masks`-mode config pointing at fixtures dir; call `ingest_fovs`; assert it runs without error and returns a list of strings.

  Use synthetic `np.random.rand(64, 64).astype(np.float32)` arrays. Construct configs with `masks` mode using `tmp_path` for directories.

- [ ] **Step 3: Run new tests**

  ```bash
  pytest tests/io/test_ingest.py -v 2>&1 | tail -15
  ```

  Expected: 5 passed.

- [ ] **Step 4: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add tests/io/test_ingest.py
  git commit -m "test(io): add ingest.py tests — TIF write, uint16 dtype, atomic write, scaling"
  ```

---

## Task 20: CLI tests for `run`, `report`, and `ingest`

**Files:** Create `tests/cli/test_cli_run.py`; create `tests/cli/test_cli_report.py`; create `tests/cli/test_cli_ingest.py`

These use `click.testing.CliRunner` and mock the underlying pipeline functions to stay fast. No real microscopy data is loaded.

- [ ] **Step 1: Create `tests/cli/test_cli_run.py`**

  Tests:
  1. `test_run_cmd_requires_config` — invoke `run` without `--config`; assert exit code != 0.
  2. `test_run_cmd_nonempty_dir_without_resume_or_force_exits_nonzero` — create a non-empty output dir; invoke `run` without `--resume` or `--force`; assert `ClickException` (exit code 1).
  3. `test_run_cmd_force_calls_run_pipeline` — patch `run_pipeline`; invoke with `--force`; assert `run_pipeline` called with `force=True`.
  4. `test_run_cmd_resume_calls_run_pipeline` — patch `run_pipeline`; invoke with `--resume`; assert `run_pipeline` called with `force=False`.
  5. `test_run_cmd_stage_flag_passes_list` — patch `run_pipeline`; invoke with `--stage polarity --stage aggregate`; assert `stages=["polarity", "aggregate"]` (order canonicalized by `filter_stages`).
  6. `test_run_cmd_runtime_error_exits_nonzero` — patch `run_pipeline` to raise `RuntimeError("oops")`; assert exit code 1 and error text in output.

  Construct a minimal masks-mode config YAML in `tmp_path`.

- [ ] **Step 2: Create `tests/cli/test_cli_report.py`**

  Tests:
  1. `test_report_cmd_requires_results` — invoke without `--results`; assert exit code != 0.
  2. `test_report_cmd_calls_build_report` — patch `build_report`; invoke with valid `--results tmp_path`; assert `build_report` called with `results_dir=tmp_path`.
  3. `test_report_cmd_default_output_path` — patch `build_report`; check the `output_html` argument is `tmp_path / "report.html"`.
  4. `test_report_cmd_custom_output_path` — patch `build_report`; invoke with `--output /tmp/x.html`; check argument.

- [ ] **Step 3: Create `tests/cli/test_cli_ingest.py`**

  Tests:
  1. `test_ingest_cmd_masks_mode_prints_skip_message` — build a masks config; invoke `ingest`; assert "ingest is not needed" in output; exit code 0.
  2. `test_ingest_cmd_requires_config` — invoke without `--config`; assert exit code != 0.
  3. `test_ingest_cmd_already_done_skips_without_force` — write a `done` state with matching config_hash; invoke `ingest` (no `--force`); assert `ingest_fovs` is NOT called.
  4. `test_ingest_cmd_force_reruns` — write a `done` state; invoke with `--force`; patch `ingest_fovs` to return []; assert it IS called.
  5. `test_ingest_cmd_writes_stage_status_on_success` — patch `ingest_fovs` to return `["FOV_01"]`; invoke with a tif-mode config; assert `stage_status/ingest.json` exists and reads `done`.

- [ ] **Step 4: Run all new CLI tests**

  ```bash
  pytest tests/cli/test_cli_run.py tests/cli/test_cli_report.py tests/cli/test_cli_ingest.py -v 2>&1 | tail -25
  ```

  Expected: 15 passed.

- [ ] **Step 5: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add tests/cli/test_cli_run.py tests/cli/test_cli_report.py tests/cli/test_cli_ingest.py
  git commit -m "test(cli): add run/report/ingest CLI tests — flags, skip logic, error handling"
  ```

---

## Task 21: Update the existing `test_cli_stubs.py` for removed stubs

**Files:** Modify `tests/test_cli_stubs.py`

Three stubs were removed (run, report, ingest). The stub test must no longer assert they error.

- [ ] **Step 1: Read `tests/test_cli_stubs.py`** (first 40 lines)

- [ ] **Step 2: Remove `"run"`, `"report"`, `"ingest"` from the stub test parameters**

  If the test is parameterized over `_STUBS.keys()`, add explicit exclusions for the three removed names. If it's a hardcoded list, remove those three entries.

- [ ] **Step 3: Add a positive assertion** — invoke `quantipy run --help` and assert exit code 0 (confirming the real command replaced the stub).

- [ ] **Step 4: Run `test_cli_stubs.py` in isolation**

  ```bash
  pytest tests/test_cli_stubs.py -v 2>&1 | tail -15
  ```

  Expected: all pass.

- [ ] **Step 5: Run full suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: 197+ passed.

- [ ] **Step 6: Commit**

  ```bash
  git add tests/test_cli_stubs.py
  git commit -m "test(cli): update stub tests — remove run/report/ingest; add run --help assertion"
  ```

---

## Task 22: End-to-end test for `quantipy run` with synthetic fixture

**Files:** Modify `tests/test_e2e_masks_pipeline.py`

The existing `test_e2e_masks_pipeline.py` tests the masks pipeline via individual commands. Add a new test that calls `run_pipeline()` directly (not via CLI) on the synthetic fixture, end-to-end. This validates that the orchestrator correctly chains all seven stages on real (synthetic) data.

- [ ] **Step 1: Read `tests/test_e2e_masks_pipeline.py`** (first 60 lines)

  Understand how the existing fixture is structured (where masks/membranes live, what config it uses).

- [ ] **Step 2: Add `test_run_pipeline_e2e_masks_synthetic` to `test_e2e_masks_pipeline.py`**

  ```python
  def test_run_pipeline_e2e_masks_synthetic(tmp_path, synthetic_masks_fixture):
      """Full run_pipeline() end-to-end on synthetic masks fixture.

      Asserts:
        - run_pipeline() exits without exception
        - 05_aggregated/per_cell.parquet exists and has rows
        - report.html exists and contains '<!DOCTYPE html>'
        - all 7 stage_status JSONs exist with status='done'
        - config.snapshot.yaml exists
      """
      from quantipy_polarity.pipeline.run import run_pipeline
      from quantipy_polarity.pipeline.dag import STAGES
      import json

      cfg, out_dir = synthetic_masks_fixture  # fixture returns (Config, tmp_path)
      # Run with force=True to ensure all stages execute
      run_pipeline(cfg, out_dir, force=True)

      per_cell = out_dir / "05_aggregated" / "per_cell.parquet"
      assert per_cell.exists(), "per_cell.parquet not written"
      import pandas as pd
      df = pd.read_parquet(per_cell)
      assert len(df) > 0, "per_cell.parquet is empty"

      report_html = out_dir / "report.html"
      assert report_html.exists(), "report.html not written"
      assert "<!DOCTYPE html>" in report_html.read_text()

      for stage in STAGES:
          sj = out_dir / "stage_status" / f"{stage}.json"
          assert sj.exists(), f"stage_status/{stage}.json missing"
          rec = json.loads(sj.read_text())
          assert rec["status"] == "done", f"stage {stage} status={rec['status']}"

      snapshot = out_dir / "config.snapshot.yaml"
      assert snapshot.exists(), "config.snapshot.yaml not written"
  ```

  If `synthetic_masks_fixture` does not exist as a conftest fixture, define it inline using the existing fixture pattern from `test_e2e_masks_pipeline.py`.

- [ ] **Step 3: Run the new test alone first**

  ```bash
  pytest tests/test_e2e_masks_pipeline.py::test_run_pipeline_e2e_masks_synthetic -v 2>&1 | tail -15
  ```

  Expected: 1 passed (may be slow — it runs all 7 stages on synthetic data).

- [ ] **Step 4: Run full pytest suite**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: 197+ passed.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/test_e2e_masks_pipeline.py
  git commit -m "test(e2e): add full run_pipeline() end-to-end test on synthetic masks fixture"
  ```

---

## Task 23: Create `docs/pipeline.md`; update `docs/concepts.md`

**Files:** Create `docs/pipeline.md`; modify `docs/concepts.md`

- [ ] **Step 1: Create `docs/pipeline.md`**

  Sections:
  1. **Overview** — what `quantipy run` does; the seven stages in order.
  2. **Stage descriptions** — one paragraph per stage: ingest, segment, polarity, front, aggregate, plot, report.
  3. **Resume semantics** — how `stage_status/<name>.json` works; `config_hash` invalidation; `--resume` vs `--force`.
  4. **Run directory layout** — verbatim copy of the locked layout from this plan.
  5. **In-process execution** — note that all stages run in the same Python process; no subprocess calls; this means Cellpose memory is held for the duration of the segment stage.
  6. **Calling pipeline stages programmatically** — show how to call `run_pipeline(cfg, out_dir)` from Python.

- [ ] **Step 2: Read `docs/concepts.md`** (first 40 lines)

- [ ] **Step 3: Append ingest stage note to `docs/concepts.md`**

  Add a short section: "Ingest stage: nd2/tif → per-FOV TIFs. Masks mode skips this stage automatically."

- [ ] **Step 4: Run tests** (docs changes don't affect tests; run as sanity check)

  ```bash
  pytest -q 2>&1 | tail -3
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add docs/pipeline.md docs/concepts.md
  git commit -m "docs: add pipeline.md (stage descriptions, resume semantics); update concepts.md"
  ```

---

## Task 24: Update README.md, CLAUDE.md; final checks; tag

**Files:** Modify `README.md`; modify `CLAUDE.md`

- [ ] **Step 1: Read `README.md`** (first 80 lines, to find Phase badge location)

- [ ] **Step 2: Update `README.md`**

  - Change Phase 4 badge/section header to Phase 5 complete.
  - Add `quantipy run --config config.yaml --output ./results` to the quickstart example.
  - Add one sentence: "`quantipy run` orchestrates all stages end-to-end and writes a self-contained `report.html`."
  - Note `--resume` and `--force` flags in a short "Pipeline resume" section.

- [ ] **Step 3: Update `CLAUDE.md`**

  In the command table, change:
  - `quantipy run` row: Status → `implemented (Phase 5)`, Purpose → `Single-shot pipeline; --resume/--force`
  - `quantipy ingest` row: Status → `implemented (Phase 5)`, Purpose → `nd2/tif → normalized per-FOV TIFs`
  - `quantipy report` row: Status → `implemented (Phase 5)`, Purpose → `Regenerate self-contained HTML report`

  Add a row for `docs/pipeline.md` in the "Where things live" section.

- [ ] **Step 4: Final full pytest run**

  ```bash
  pytest -q 2>&1 | tail -5
  ```

  Expected: **≥197 passed** (169 baseline + ≥28 new), 1 skipped.

- [ ] **Step 5: Verify `quantipy --help` shows correct command list**

  ```bash
  quantipy --help 2>&1
  ```

  Expected: `run` appears under "Primary commands"; `ingest`, `report`, `segment`, etc. under "Advanced commands".

- [ ] **Step 6: Commit README and CLAUDE.md**

  ```bash
  git add README.md CLAUDE.md
  git commit -m "docs: Phase 5 complete — update README quickstart + CLAUDE.md command table"
  ```

- [ ] **Step 7: Tag**

  ```bash
  git tag phase-5-complete
  git push origin main --tags
  ```

---

## Self-Review

### Spec coverage

| Deliverable | Task(s) |
|---|---|
| `pipeline/__init__.py` | Task 2 |
| `pipeline/state.py` — StageState + read/write + config_hash | Task 3 |
| `pipeline/dag.py` — stage list, skip logic | Task 4 |
| `pipeline/run.py` — `run_pipeline()` | Task 5 |
| `report/__init__.py` | Task 6 |
| `report/templates/report.html.j2` | Task 8 |
| `report/build.py` — `gather_report_inputs` + `build_report` | Task 7 |
| `_cli_run.py` | Task 10 |
| `_cli_report.py` | Task 11 |
| `_cli_ingest.py` | Task 9 |
| Refactor: extract `_build_fov_iterator` → `io/ingest.py` | Tasks 1, 12 |
| Tests — state, dag, run_pipeline, report, template, ingest, CLI | Tasks 14–22 |
| Docs — pipeline.md, concepts.md, README, CLAUDE.md | Tasks 23, 24 |
| Acceptance + tag | Task 24 |

### Placeholder scan

No task contains a placeholder. All function signatures are fully specified with concrete argument names and types. All import paths are complete and match the existing module structure.

### Function signature consistency

- `run_pipeline(cfg: Config, out_dir: Path, *, force: bool = False, stages: list[str] | None = None) -> None` — called consistently in `_cli_run.py` (Task 10) and tests (Task 16).
- `build_report(results_dir: Path, output_html: Path, *, cfg: Config | None = None) -> None` — called consistently in `_cli_report.py` (Task 11), `pipeline/run.py` (Task 5 `_stage_report`), and tests (Tasks 17, 20).
- `write_stage_state(out_dir, stage_name, status, *, cfg, input_paths, output_paths, preserve_started_at)` — called consistently in `_cli_ingest.py` (Task 9), `pipeline/run.py` (Task 5), and tests (Task 14).
- `build_fov_iterator(cfg: Config)` — called from `_cli_segment.py` delegation (Task 12) and `io/ingest.ingest_fovs()` (Task 1).

### Backward-compat check

- `quantipy polarity`, `aggregate`, `segment`, `front`, `plot`: None of these modules are modified in Phase 5 except the one-line delegation in `_cli_segment.py` (Task 12) which preserves the exact same external behavior.
- `segment/_writer.py`'s `write_stage_status()` is NOT touched. It remains as the per-segment-stage writer for standalone `quantipy segment`. The pipeline uses `pipeline/state.py` exclusively.
- `io/masks.py`, `io/tif.py`, `io/nd2.py`: untouched.
- The `_stubs.py` removal of three stubs cannot regress anything — those stubs only produced error messages before Phase 5.

---

## Report

**Task count:** 24 tasks.

**Files created:** `io/ingest.py`, `pipeline/__init__.py`, `pipeline/state.py`, `pipeline/dag.py`, `pipeline/run.py`, `report/build.py`, `report/templates/report.html.j2`, `_cli_ingest.py`, `_cli_run.py`, `_cli_report.py`, `tests/pipeline/__init__.py`, `tests/pipeline/test_state.py`, `tests/pipeline/test_dag.py`, `tests/pipeline/test_run_pipeline.py`, `tests/report/__init__.py`, `tests/report/test_build.py`, `tests/report/test_template.py`, `tests/io/test_ingest.py`, `tests/cli/test_cli_run.py`, `tests/cli/test_cli_report.py`, `tests/cli/test_cli_ingest.py`, `docs/pipeline.md`. (22 new files)

**Files modified:** `_cli_segment.py` (delegation refactor), `_stubs.py` (remove 3 stubs), `cli.py` (add 3 imports), `report/__init__.py` (upgrade from stub), `tests/test_cli_stubs.py` (remove 3 stub entries), `tests/test_e2e_masks_pipeline.py` (add e2e test), `docs/concepts.md`, `README.md`, `CLAUDE.md`. (9 modified files)

**Approach:** Phase 5 adds a thin `pipeline/` orchestration layer that calls the same Python functions already used by the Phase 2–4 CLI commands — no code duplication and no subprocess calls. The key design decision is a stage-agnostic `pipeline/state.py` that writes `stage_status/<name>.json` (a new top-level directory separate from the numbered output dirs), keeping the resume/force semantics cleanly decoupled from the stage implementations. The `io/ingest.py` module consolidates the FOV iterator that was duplicated between `_cli_segment.py` and what `_cli_polarity.py` does inline; `_cli_segment.py` is refactored to delegate without changing behavior.

**Spec ambiguities resolved:**

1. *Output directory layout discrepancy* — the prompt specified a flat `results/` layout (`ingest/`, `masks/`, `per_fov/`, etc.) but the existing codebase uses numbered directories (`01_ingest/`, `02_segmentation/`, `03_polarity/per_fov/`, etc.) that Phases 2–4 already write. Resolution: keep the existing numbered layout to preserve backward compat; the Phase 5 layout in the plan header reflects actual paths. The spec's §7 also uses numbered dirs, so this is consistent with the spec.

2. *`stage_status.json` location* — the spec (§7) writes `_stage_status.json` inside each stage directory. The prompt asked for `stage_status/` as a top-level directory. Resolution: use `stage_status/` as a new top-level directory (the prompt's layout wins; it is more organized and doesn't couple state files to output dirs). The existing `segment/_writer.py` keeps its own `_stage_status.json` inside `02_segmentation/` for standalone `quantipy segment` backward compat; `pipeline/state.py` writes only to `stage_status/`.

3. *`ingest` stage for `masks` mode* — masks mode has no nd2/tif to ingest. Resolution: `_stage_ingest` and `ingest_cmd` both detect `InputMasks` and exit early with a log/message. The `ingest` entry still appears in `stage_status/` as `done` so that resume logic is consistent.

**Deferred features:**

- `quantipy debug` (Phase 7 viewer) — untouched.
- `quantipy validate` (Phase 6) — untouched.
- `quantipy download-demo` (Phase 6) — untouched.
- `quantipy analyze` (Phase 7 experimental analyses) — untouched.
- Parallel stage execution (e.g., polarity across FOVs via `concurrent.futures`) — deferred to v0.2. Current implementation is single-threaded in-process.
- `--interactive` front tuner (deferred to v0.2 per spec §8).

**On HTML self-containment with large per-FOV PNGs:** `build.py` downscales every PNG to a maximum of 400 px on the longest edge before base64-encoding (using `PIL.Image.thumbnail()` + `optimize=True`). This caps each embedded thumbnail at approximately 30–80 KB, keeping the HTML file under ~3 MB even for 20-FOV experiments. The original full-resolution figures remain in `06_plots/` on disk; the HTML footer includes a note pointing users there. This is a firm design decision — it avoids the "100 MB HTML" failure mode while preserving the portability of a single self-contained file.
