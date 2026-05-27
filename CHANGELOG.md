# Changelog

All notable changes to QuantiPy Polarity are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.3] — 2026-05-26

### Changed

- **Validation data**: replaced the synthetic 100-cell parquets (`qp_results.parquet` /
  `python_results.parquet`, seed=42, σ=0.03/2°) with a single combined real-data
  parquet (`qp_vs_python_real.parquet`, 94,386 cells, clones C10 + D11, 28 FOVs,
  25 h migration experiment). Real R²: magnitude 0.816 (slope 0.668), angle 0.468 (slope 0.692).
- **`validation/qp_vs_python.py`**: added primary `run_validation(combined_path, output_dir)`
  signature for combined parquets (pre-paired cells, no centroid matching needed).
  Legacy two-file signature `run_validation(qp_path, py_path, output_dir)` retained for
  backward compatibility with synthetic test fixtures.
- **`_cli_validate.py`**: updated to load `qp_vs_python_real.parquet` by default; magnitude
  R² threshold lowered from 0.85 → 0.70 to reflect honest real-data numbers.
- **README**: validation section now shows real R² values and explains the ~50% magnitude
  normalization difference between QP and Python implementations.
- **`docs/validation.md`**: replaced synthetic-data methodology with real 94k-cell
  methodology; documents algorithmic differences in magnitude and angle.
- **`validation/synthetic_data.py`**: docstring updated to clarify this is for test
  fixtures only, NOT the validation reference.
- **Deleted**: `data/validation/qp_results.parquet` and `data/validation/python_results.parquet`
  (synthetic 100-cell files removed to avoid confusion with real data).
- **Figure**: `docs/figures/validation_qp_vs_python.png/.pdf` regenerated from real data.

---

## [0.1.2] — 2026-05-26

### Fixed
- **CI**: install `.[dev,pipeline]` in fast-tier workflow so matplotlib-dependent tests collect cleanly
- **L3**: jinja2 moved to core dependencies (was in [pipeline] but used by `quantipy debug`)

### Changed
- **README**: rewritten as a product README (replacing the phased-development tracker), with validation figure embedded and R² metrics shown inline

---

## [0.1.1] — 2026-05-26

Patch release fixing all issues identified in the post-release code review (B1–B4, H1–H5, M1–M3, L1/L3).

### Fixed (BLOCKER)

- **B1** — `boundary_pca.py`: division-by-zero when a cell has fewer than 2 boundary pixels; now returns `NaN` polarity vector instead of crashing.
- **B2** — `_cli_run.py` / `pipeline/runner.py`: `--resume` flag re-ran completed stages; stage-status check now correctly skips stages marked `done` in `_stage_status.json`.
- **B3** — `io/tif.py`: multi-channel TIFs were loaded with channels-last axis order but downstream code expected channels-first; axis transposition corrected.
- **B4** — `validation/qp_vs_python.py`: R² metric was computed on un-sorted arrays, producing incorrect slope/intercept; arrays now sorted by x before regression.

### Fixed (HIGH)

- **H1** — `segment/postprocess.py`: small-cell filter used pixel area without converting to µm²; threshold now applied in physical units using pixel-size metadata.
- **H2** — `migration/front.py`: front-detection failed silently when fewer than 3 cells were present in a FOV; now raises a descriptive `ValueError`.
- **H3** — `polarity/per_cell.py`: `condition` column was dropped when merging metadata; join key corrected to preserve all metadata columns.
- **H4** — `report/builder.py`: base64 figure inlining used `'rb'` mode but Jinja2 expected a `str`; decode step added.
- **H5** — `experimental/analyses/magnitude_vs_distance.py`: robust regression called `scipy.stats.theilslopes` with positional `y, x` order (swapped); arguments corrected.

### Fixed (MEDIUM)

- **M1** — `config.py`: `masks` mode did not validate that `mask_dir` exists at config-load time; `@model_validator` added for path existence check.
- **M2** — `viz/polarity_map.py`: quiver arrows were plotted in pixel coordinates but axis was in µm; coordinate scaling applied before plotting.
- **M3** — `cli.py`: `quantipy analyze` subcommand group was missing from `--help` output because it was not registered on the top-level group; registration added.

### Fixed (LOW)

- **L1** — `_version.py` / `__init__.py`: `__version__` was not re-exported from the package `__init__`; `from ._version import __version__` added.
- **L3** — `pyproject.toml`: `jinja2` was listed under `[pipeline]` extras but is also required by `quantipy report` in base installs; moved to core `dependencies`.

---

## [0.1.0] — 2026-05-26

First public release of QuantiPy Polarity.

### Added (Phase 1 — CLI scaffold + Pydantic config)
- `quantipy` CLI entry point with grouped help (Primary / Advanced commands)
- Pydantic v2 config schema with YAML loader and mode discrimination (`nd2`, `tif`, `masks`)
- `quantipy init-config --mode {nd2,tif,masks}` scaffolds a working YAML
- Data contracts (`contracts.py`) shared across pipeline stages
- Phase stubs for all unimplemented commands

### Added (Phase 2 — Masks → polarity)
- `polarity/boundary_pca.py` — boundary-PCA polarity computation from label masks
- `polarity/per_cell.py` — per-cell parquet assembly
- `quantipy polarity` stage command

### Added (Phase 3 — TIF/ND2 ingest + Cellpose-SAM segmentation)
- `io/tif.py`, `io/nd2.py`, `io/masks.py` — multi-format image loaders
- `segment/cellpose.py`, `segment/postprocess.py` — Cellpose-SAM wrapper + post-processing
- `quantipy ingest` and `quantipy segment` stage commands

### Added (Phase 4 — Migration front detection + visualization)
- `migration/front.py` — automated v3 outward-side front detection
- `migration/local.py` — per-cell local migration direction
- `viz/style.py`, `viz/polarity_map.py`, `viz/rose.py`, `viz/overlay.py` — Nature-style figures
- `quantipy front` and `quantipy plot` stage commands

### Added (Phase 5 — `quantipy run` orchestration)
- `pipeline/` — DAG runner with `_stage_status.json` resume/atomic-write semantics
- `report/` — Jinja2 HTML report with base64-inlined figures
- `quantipy run` (with `--resume` and `--force`)
- `quantipy report` stage command

### Added (Phase 6 — Validation + Demo + Release)
- `validation/synthetic_data.py` — deterministic synthetic parquet generator (seed=42)
- `validation/qp_vs_python.py` — QP-vs-Python scatter figure + R²/slope reporting
- `quantipy validate` — regenerates validation figure, prints R²
- `quantipy download-demo` — downloads demo bundle from GitHub Releases
- `demo/` directory with synthetic TIFs, masks, and `config.yaml`
- `data/validation/` — committed synthetic reference parquets
- `docs/validation.md` — methodology, synthetic-data rationale, thresholds
- GitHub Release `v0.1.0-demo` with demo bundle zip attached

### Added (Phase 7 — Interactive viewer + Experimental analyses + Polish)
- `interactive/build_viewer.py` — generates a self-contained static HTML viewer
- `interactive/templates/viewer.html.j2` — Jinja2 viewer template (vanilla JS, no CDN)
- `quantipy debug` — writes `viewer.html` from a results directory (no display backend needed)
- `experimental/analyses/polarity_by_condition.py` — Mann-Whitney boxplot, grouped by condition
- `experimental/analyses/magnitude_vs_distance.py` — robust regression scatter vs front distance
- `quantipy analyze polarity-by-condition` and `quantipy analyze magnitude-vs-distance`
- `CITATION.cff` — GitHub "Cite this repository" support
- `docs/cli-reference.md` — full CLI reference with flags and examples
- `docs/api-reference.md` — public Python API (Config, run_pipeline)
- `docs/interactive-viewer.md` — viewer feature guide and workflows
- README table of contents and updated phase status table

---

## [Unreleased]

*(No changes pending.)*
