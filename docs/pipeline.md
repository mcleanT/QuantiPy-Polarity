# Pipeline Orchestration

## Overview

`quantipy run --config config.yaml --output ./results` is the single-shot
entry point for a complete QuantiPy Polarity analysis.  It runs the following
seven stages in order:

1. **ingest** — nd2/tif → normalised per-FOV TIFs in `01_ingest/`
2. **segment** — membrane TIFs → uint16 Cellpose-SAM label masks in `02_segmentation/`
3. **polarity** — masks → per-FOV parquets in `03_polarity/per_fov/`
4. **aggregate** — per-FOV parquets → experiment-wide `05_aggregated/per_cell.parquet`
5. **front** — per-cell parquet → migration-front distances + QC PNGs in `04_migration/`
6. **plot** — `per_cell.parquet` + front parquet → all figures in `06_plots/`
7. **report** — all figures + metrics → self-contained `report.html`

Each stage is skippable when its `stage_status/<name>.json` records
`status: done` and the stored `config_hash` matches the current run hash.

---

## Stage descriptions

### 1 · ingest

Converts raw microscopy input to normalised per-FOV membrane TIFs.  For
`mode: nd2` the `.nd2` file is loaded via `nd2reader`; z-stacks are projected
by `z_policy` (mip / substack / none).  For `mode: tif` the stack or multifile
scheme is applied.  For `mode: masks` this stage is skipped automatically —
pre-segmented masks are used directly.  Outputs are float32 [0, 1] TIFs written
atomically to `01_ingest/<fov_id>_membrane.tif`.

### 2 · segment

Passes each normalised membrane TIF to Cellpose-SAM
(`pretrained_model="cpsam"`, Cellpose ≥ 3.0).  Label masks are validated for
contiguous IDs (1..N, background = 0) and written as uint16 TIFs to
`02_segmentation/<fov_id>_mask.tif`.  Skipped when `mode: masks`.

### 3 · polarity

Runs the Fourier-k = 2 boundary-PCA polarity algorithm on every cell in every
FOV.  Reads mask + membrane TIFs from `02_segmentation/` (or `input.masks_dir`
in `masks` mode).  Writes one Parquet per FOV to `03_polarity/per_fov/`.

### 4 · aggregate

Concatenates all per-FOV Parquets into the experiment-wide
`05_aggregated/per_cell.parquet` matching the `PER_CELL_COLUMNS` schema in
`contracts.py`.

### 5 · front

Detects the migration front from the per-cell centroid data, computes
`dist_to_front_um`, `mig_dir_deg`, and `mig_alignment`, and writes
`04_migration/front_um_per_fov.parquet` plus QC PNGs.  Skipped when
`migration.detect_front: false`.

### 6 · plot

Re-generates all figures — polarity vector maps, rose plots, overlay images,
and per-experiment summary — from the existing parquets.  Outputs land in
`06_plots/`.  This stage is idempotent: re-running it on an existing results
directory updates the figures without touching the parquets.

### 7 · report

Builds a self-contained `report.html` from the figures in `06_plots/` and
summary statistics from `per_cell.parquet`.  Figures are downscaled to
thumbnail size (longest edge ≤ 400 px, ~50–100 KB each) and base64-encoded
inline; the final HTML file stays under ~ 5 MB for experiments with 20+ FOVs.
Full-resolution PNGs remain on disk; the HTML includes relative path hints.

---

## Resume semantics

Each stage writes a `stage_status/<name>.json` file on completion:

```json
{
  "stage": "polarity",
  "status": "done",
  "config_hash": "a3f1…",
  "completed_at": "2026-05-26T12:00:00Z"
}
```

`config_hash` is the SHA-256 of the serialised config (excluding output-path
fields).  On the next run, `pipeline/dag.py` reads each status file and skips
the stage when **all three** conditions hold:

1. `status == "done"`
2. `config_hash` matches the current run
3. `--force` is **not** set

**`--resume`** (default if neither flag is given): skip stages with `done`
status; restart from the first `failed` or missing stage.

**`--force`**: delete all `stage_status/*.json` files before running, so every
stage is re-executed regardless of prior results.

If a stage raises mid-run, its JSON is updated to `status: failed`.  A
subsequent `quantipy run --resume` (or a plain re-run without `--force`) skips
all `done` stages and retries from the `failed` one.

---

## Run directory layout

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
├── 01_ingest/                # per-FOV normalised TIFs from quantipy ingest
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

`stage_status/` is new in Phase 5.  The numbered `01_`–`06_` directories are
the same directories that Phases 2–4 already write; `run_pipeline()` calls
into the same functions that write them.

---

## In-process execution

All stages run in the **same Python process** — there are no subprocess calls.
This means Cellpose memory is held for the entire duration of the `segment`
stage and released only when that stage function returns.  For very large
experiments, consider using `quantipy segment` as a standalone command first
and then calling `quantipy run` (which will skip the `segment` stage via the
status cache).

`run.log` is written via `structlog` to `<out_dir>/run.log` in JSON-lines
format so it can be parsed programmatically or tailed during a long run.

---

## Calling pipeline stages programmatically

```python
from pathlib import Path
from quantipy_polarity.config import load_config
from quantipy_polarity.pipeline.run import run_pipeline

cfg = load_config(Path("config.yaml"))
out_dir = Path("./results")

# Full run (honours stage_status cache)
run_pipeline(cfg, out_dir)

# Force re-run from scratch
run_pipeline(cfg, out_dir, force=True)

# Resume from a previously failed stage
run_pipeline(cfg, out_dir)  # --resume is the default
```

`run_pipeline()` is synchronous and raises `RuntimeError` on the first stage
failure (after writing `status: failed` to the relevant `stage_status` JSON).
