# Developer Workflow

This page describes optional integrations for development workflows. **None
are required to use the tool** — `quantipy` is a standard Python CLI.

## Claude Code integration

If you use Claude Code, the repo ships:
- `CLAUDE.md` — orients a session opened in this directory
- `.claude/settings.json` — pre-approves safe read-only commands so you avoid
  permission prompts on first run; writes/pushes/installs still prompt
- `.claude/commands/quantipy-run.md` — `/quantipy-run` slash command
- `.claude/commands/quantipy-debug-fov.md` — `/quantipy-debug-fov [FOV]`
- `.claude/commands/quantipy-front-qc.md` — `/quantipy-front-qc`

## Running tests

```bash
pip install -e .[dev]
pytest -v
```

## Running the fast-tier CI locally

```bash
pytest tests/
```

The fast tier deliberately excludes Cellpose-SAM (which lands in Phase 3 and
is gated on the nightly CI tier).
