# QuantiPy Polarity — Claude Code Orientation

This file orients Claude Code sessions opened in this repo. The tool does NOT
require Claude Code — see README.md for the standard CLI workflow.

## What this is

QuantiPy Polarity is a Python CLI tool for planar-polarity quantification from
microscopy images. The `quantipy` command is installed by
`pip install -e .` (or via the conda recipe in `environment.yml`).

## CLI command map

| Command | Status (Phase 1) | Purpose |
|---|---|---|
| `quantipy init-config --mode {nd2,tif,masks}` | implemented | Scaffold a config YAML |
| `quantipy --version` / `--help` | implemented | CLI introspection |
| `quantipy run` | implemented (Phase 5) | Single-shot pipeline; --resume/--force |
| `quantipy polarity` / `aggregate` | implemented (Phase 2) | Masks→per-cell→experiment parquet |
| `quantipy segment` | implemented (Phase 3) | TIF/ND2 → Cellpose-SAM → label masks |
| `quantipy front` | implemented (Phase 4) | Migration-front detection; writes `04_migration/front_um_per_fov.parquet` + QC PNGs |
| `quantipy plot` | implemented (Phase 4) | Regenerate all figures (vector maps, roses, overlays, summary) from existing parquet |
| `quantipy ingest` | implemented (Phase 5) | nd2/tif → normalized per-FOV TIFs |
| `quantipy report` | implemented (Phase 5) | Regenerate self-contained HTML report |
| `quantipy debug` | stubbed (Phase 7) | Read-only per-cell viewer |
| `quantipy validate` | implemented (Phase 6) | QP-vs-Python figure regeneration |
| `quantipy download-demo` | implemented (Phase 6) | Pull demo bundle from Release |
| `quantipy analyze <name>` | stubbed (Phase 7) | Experimental analyses |

## Where things live

- `src/quantipy_polarity/cli.py` — Click root, `_GroupedHelp` class
- `src/quantipy_polarity/config.py` — Pydantic schema (input mode discriminator)
- `src/quantipy_polarity/contracts.py` — `PerCellRow` schema, QC bit flags, coord conventions
- `src/quantipy_polarity/polarity/boundary_pca.py` — Fourier-k=2 PCA polarity algorithm (lifted from research repo)
- `src/quantipy_polarity/polarity/per_cell.py` — per-FOV → experiment parquet
- `src/quantipy_polarity/io/masks.py` — paired (mask, membrane) FOV loader
- `src/quantipy_polarity/io/tif.py` — TIF ingest (stack + multifile schemes)
- `src/quantipy_polarity/io/nd2.py` — ND2 ingest via nd2reader
- `src/quantipy_polarity/segment/cellpose_sam.py` — Cellpose-SAM wrapper
- `src/quantipy_polarity/_cli_segment.py` — quantipy segment command
- `tests/fixtures/_build.py` + `synthetic_fov.npz` — ground-truth fixture
- `docs/superpowers/specs/` — design spec + codex review
- `docs/superpowers/plans/` — phased implementation plans
- `docs/pipeline.md` — orchestration architecture: stages, state management, resume/force, output layout, run.log
- `tests/` — pytest suite

## Guard

Read `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` (rev 1)
before modifying any module — the spec defines stable contracts (per_cell
schema, coord conventions, axial angle range) that downstream phases depend on.

## Implementation phases

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | CLI scaffold, Pydantic config | ✅ implemented |
| 2 | Masks → polarity pipeline | ✅ implemented |
| 3 | TIF/ND2 ingest + Cellpose-SAM segmentation | ✅ implemented |
| 4 | Migration front detection + visualization | ✅ implemented |
| 5 | `quantipy run` orchestration + resume/atomic writes | ✅ implemented |
| 6 | Validation + Demo + Release | ✅ implemented |
| 7 | Interactive viewer + experimental analyses | 🔲 planned |

### Phase 6 summary

- `quantipy download-demo` — fetches the synthetic demo bundle (~5 MB) from the GitHub Release asset and extracts it to `~/.cache/quantipy/demo/`; falls back to `demo/` if already present in the repo clone.
- `quantipy validate` — runs the QP-vs-Python cross-validation, prints R² and slope to stdout, and writes `validation_qp_vs_python.pdf` to `~/.cache/quantipy/validation/`.
- Demo config at `demo/config.yaml` enables a full end-to-end run with no GPU required.

## Slash commands available

`/quantipy-run`, `/quantipy-debug-fov`, `/quantipy-front-qc` — see `.claude/commands/`.
