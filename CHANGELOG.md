# Changelog

All notable changes to QuantiPy Polarity are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
