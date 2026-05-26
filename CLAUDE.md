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
| `quantipy run` | stubbed (Phase 5) | Single-shot pipeline |
| `quantipy ingest` / `segment` / `polarity` / `front` / `aggregate` / `plot` / `report` | stubbed (Phases 2–5) | Stage-resume commands |
| `quantipy debug` | stubbed (Phase 7) | Read-only per-cell viewer |
| `quantipy validate` | stubbed (Phase 6) | QP-vs-Python figure regeneration |
| `quantipy download-demo` | stubbed (Phase 6) | Pull demo bundle from Release |
| `quantipy analyze <name>` | stubbed (Phase 7) | Experimental analyses |

## Where things live

- `src/quantipy_polarity/cli.py` — Click root, `_GroupedHelp` class
- `src/quantipy_polarity/config.py` — Pydantic schema (input mode discriminator)
- `src/quantipy_polarity/contracts.py` — `PerCellRow` schema, QC bit flags, coord conventions
- `docs/superpowers/specs/` — design spec + codex review
- `docs/superpowers/plans/` — phased implementation plans
- `tests/` — pytest suite

## Guard

Read `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` (rev 1)
before modifying any module — the spec defines stable contracts (per_cell
schema, coord conventions, axial angle range) that downstream phases depend on.

## Slash commands available

`/quantipy-run`, `/quantipy-debug-fov`, `/quantipy-front-qc` — see `.claude/commands/`.
