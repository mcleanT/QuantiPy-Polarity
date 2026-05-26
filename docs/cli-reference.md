# CLI Reference

This document covers every `quantipy` subcommand.  For installation and a
worked example see the [README](../README.md).  For stage-by-stage pipeline
details see [docs/pipeline.md](pipeline.md).

---

## Primary commands

These are the commands most users need day-to-day.

### quantipy init-config

**Synopsis**

```
quantipy init-config --mode <nd2|tif|masks> [OPTIONS]
```

**Description**

Writes a Pydantic-valid YAML scaffold for the chosen input mode so you can
fill in paths and run `quantipy run` straight away.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--mode` | `nd2 \| tif \| masks` | *(required)* | Input mode to scaffold. |
| `--output`, `-o` | path | `config.yaml` | Path to write the YAML. |
| `--force` | flag | `False` | Overwrite if `--output` already exists. |

**Example**

```bash
quantipy init-config --mode masks --output config.yaml
```

---

### quantipy download-demo

**Synopsis**

```
quantipy download-demo [OPTIONS]
```

**Description**

Downloads and extracts the synthetic demo bundle (~5 MB) to a local cache
directory.  The demo bundle includes a pre-configured `config.yaml`, membrane
TIFs, and pre-computed masks so the pipeline runs without GPU or ND2 files.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output`, `-o` | path | `~/.cache/quantipy/demo/` | Destination directory. |
| `--force`, `-f` | flag | `False` | Re-download even if the demo already exists. |

**Example**

```bash
quantipy download-demo
quantipy run --config ~/.cache/quantipy/demo/config.yaml --output ./demo_results
```

---

### quantipy run

**Synopsis**

```
quantipy run --config <path> [OPTIONS]
```

**Description**

Orchestrates the full pipeline (ingest → segment → polarity → front → figures
→ report) for a single experiment config.  Stages are executed in order; by
default already-completed stages are skipped (resume semantics).

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config` | path | *(required)* | Path to a quantipy YAML config. |
| `--output` | path | from config | Output directory; overrides `project.output_dir` in the config. |
| `--resume` | flag | `False` | Skip stages already marked done with a matching config hash. |
| `--force` | flag | `False` | Ignore all stage caches; re-run every stage from scratch. |
| `--stage` | str (repeatable) | all stages | Run only this stage.  Repeat for multiple stages, e.g. `--stage polarity --stage figures`. |

**Example**

```bash
# Full run
quantipy run --config config.yaml --output ./results

# Re-run only the figures and report stages
quantipy run --config config.yaml --output ./results --stage figures --stage report

# Force everything from scratch
quantipy run --config config.yaml --output ./results --force
```

---

### quantipy debug

**Synopsis**

```
quantipy debug --results <path> [OPTIONS]
```

**Description**

Builds a self-contained HTML per-cell viewer from a completed run directory
and opens it in the default browser.  Useful for inspecting individual cells
without rerunning the pipeline.  See [docs/interactive-viewer.md](interactive-viewer.md)
for a full usage guide.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--results` | path | *(required)* | Path to a completed quantipy run directory. |
| `--output` | path | `<results>/viewer.html` | Output HTML path. |
| `--fov` | str | all FOVs | Limit the viewer to a single FOV ID. |

**Example**

```bash
quantipy debug --results ./demo_results
open ./demo_results/viewer.html
```

---

### quantipy validate

**Synopsis**

```
quantipy validate [OPTIONS]
```

**Description**

Runs the QP-vs-Python comparison on paired parquets from the validation data
bundle.  Prints R², slope, and match counts; writes a PDF figure and a JSON
metrics file.  See [docs/validation.md](validation.md) for methodology.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output`, `-o` | path | `~/.cache/quantipy/validation/` | Directory for output PDF/PNG and metrics JSON. |
| `--tolerance`, `-t` | float | `5.0` | Max centroid distance (pixels) for nearest-neighbour cell matching. |

**Example**

```bash
quantipy validate
# → prints R²=0.998, slope=1.001; writes validation_qp_vs_python.pdf
```

---

## Advanced commands

These commands correspond to individual pipeline stages and are intended for
debugging, partial reruns, or integration into external workflows.

### quantipy ingest

**Synopsis**

```
quantipy ingest --config <path> [OPTIONS]
```

**Description**

Runs the ingest stage: reads raw images (ND2, TIF, or existing masks) and
writes standardised per-FOV TIF stacks to `01_ingest/`.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config` | path | *(required)* | Path to quantipy YAML config. |
| `--output` | path | from config | Output directory; overrides `project.output_dir`. |
| `--force` | flag | `False` | Re-run even if the stage is already marked done. |

**Example**

```bash
quantipy ingest --config config.yaml --output ./results
```

---

### quantipy segment

**Synopsis**

```
quantipy segment --config <path> [OPTIONS]
```

**Description**

Runs the segmentation stage: calls Cellpose-SAM on the `01_ingest/` TIFs and
writes label-mask PNGs to `02_segmentation/`.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config` | path | *(required)* | Path to quantipy YAML config. |
| `--input` | path | from config | Input directory; overrides `config.input.path`. |
| `--output` | path | from config | Output directory; overrides `project.output_dir`. |
| `--gpu/--no-gpu` | flag | `--no-gpu` | Use GPU acceleration for Cellpose. |

**Example**

```bash
quantipy segment --config config.yaml --output ./results --gpu
```

---

### quantipy polarity

**Synopsis**

```
quantipy polarity --config <path> --output <path> [OPTIONS]
```

**Description**

Runs the polarity stage: computes per-cell polarity angles and magnitudes from
paired membrane TIFs and label masks, writing per-FOV parquets to
`03_polarity/per_fov/`.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config`, `-c` | path | *(required)* | Path to YAML config (`input.mode` must be `masks` in v0.1.0). |
| `--output`, `-o` | path | *(required)* | Output directory. |
| `--overwrite` | flag | `False` | Overwrite existing per-FOV parquets. |
| `--condition` | str | `None` | Optional condition label applied to all FOVs. |

**Example**

```bash
quantipy polarity --config config.yaml --output ./results
```

---

### quantipy front

**Synopsis**

```
quantipy front --config <path> --input <path> --output <path> [OPTIONS]
```

**Description**

Detects the migration front for each FOV and annotates per-cell distances in
`04_migration/`.  See [docs/migration-front.md](migration-front.md) for the
algorithm.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config` | path | *(required)* | Path to quantipy YAML config. |
| `--input` | path | *(required)* | Directory containing `02_segmentation/` label masks. |
| `--output` | path | *(required)* | Results directory; `04_migration/` is written here. |
| `--qc` | flag | `False` | Write per-FOV QC overlay PNGs to `04_migration/qc/`. |
| `--resume` | flag | `False` | Skip FOVs already present in `front_um_per_fov.parquet`. |

**Example**

```bash
quantipy front --config config.yaml --input ./results --output ./results --qc
```

---

### quantipy plot

**Synopsis**

```
quantipy plot --config <path> --output <path> [OPTIONS]
```

**Description**

Generates publication-ready figures from `05_aggregated/per_cell.parquet`:
per-FOV polarity vector maps, per-FOV and aggregate rose plots, a population
summary panel, and (optionally) migration-front overlays.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config` | path | *(required)* | Path to quantipy YAML config. |
| `--output` | path | *(required)* | Results directory containing `05_aggregated/per_cell.parquet`. |
| `--per-fov-maps/--no-per-fov-maps` | flag | `True` | Generate per-FOV polarity vector maps. |
| `--rose/--no-rose` | flag | `True` | Generate per-FOV and aggregate rose plots. |
| `--summary/--no-summary` | flag | `True` | Generate population summary panel. |
| `--front-overlays/--no-front-overlays` | flag | `True` | Generate front overlay PNGs (requires `04_migration/`). |

**Example**

```bash
quantipy plot --config config.yaml --output ./results --no-front-overlays
```

---

### quantipy report

**Synopsis**

```
quantipy report --results <path> [OPTIONS]
```

**Description**

Assembles a self-contained `report.html` from the figures and data in a
completed run directory.  The HTML file embeds all images as base64 and
requires no network access to view.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--results` | path | *(required)* | Run directory (output from `quantipy run`). |
| `--output` | path | `<results>/report.html` | Output HTML path. |
| `--config` | path | `None` | Optional config YAML for `project.name` injection. |

**Example**

```bash
quantipy report --results ./demo_results
open ./demo_results/report.html
```

---

### quantipy analyze

**Synopsis**

```
quantipy analyze <subcommand> [OPTIONS]
```

**Description**

Group command containing experimental analysis subcommands.  Run
`quantipy analyze --help` for the full list.

---

#### quantipy analyze polarity-by-condition

**Synopsis**

```
quantipy analyze polarity-by-condition --per-cell <path> --metadata <path> [OPTIONS]
```

**Description**

Compares polarity magnitude between experimental conditions using a
Kruskal-Wallis test followed by pairwise Mann-Whitney U tests with
Benjamini-Hochberg correction.  Writes a PDF violin plot and a JSON summary.

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--per-cell` | path | *(required)* | Path to `per_cell.parquet` from a quantipy run. |
| `--metadata` | path | *(required)* | CSV or TSV with columns `[fov_id, condition]` (or `--condition-col`). |
| `--output-dir` | path | `./analyze_results` | Directory for output PDF + JSON. |
| `--condition-col` | str | `condition` | Column name in metadata for the grouping variable. |
| `--magnitude-col` | str | `qp_magnitude` | Column name in `per_cell.parquet` for polarity magnitude. |

**Example**

```bash
quantipy analyze polarity-by-condition \
  --per-cell ./results/05_aggregated/per_cell.parquet \
  --metadata ./metadata.csv \
  --output-dir ./analysis
```

---

#### quantipy analyze magnitude-vs-distance

**Synopsis**

```
quantipy analyze magnitude-vs-distance --per-cell <path> [OPTIONS]
```

**Description**

Plots polarity magnitude against distance to the migration front and fits a
linear trend.  Requires `dist_to_front_px` in `per_cell.parquet` (i.e., the
`front` stage must have run).

**Options**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--per-cell` | path | *(required)* | Path to `per_cell.parquet` from a quantipy run. |
| `--output-dir` | path | `./analyze_results` | Directory for output PDF + JSON. |
| `--distance-col` | str | `dist_to_front_px` | Column name for distance to migration front. |
| `--magnitude-col` | str | `qp_magnitude` | Column name for polarity magnitude. |
| `--max-cells` | int | `5000` | Maximum cells to plot (random subsample for legibility). |

**Example**

```bash
quantipy analyze magnitude-vs-distance \
  --per-cell ./results/05_aggregated/per_cell.parquet \
  --output-dir ./analysis
```
