# Contributing to QuantiPy Polarity

Thanks for your interest. The project is in early development (v0.1.0,
phased rollout — see `docs/superpowers/plans/`).

## Development setup

```bash
git clone https://github.com/mcleanT/QuantiPy-Polarity.git
cd QuantiPy-Polarity
# Option A: conda (recommended for the full algorithm stack)
conda env create -f environment.yml
conda activate quantipy
# Option B: venv + pip
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,pipeline]
```

## Running tests

```bash
pytest -v
```

The fast tier (CI default) excludes Cellpose-SAM. The slow tier runs nightly
and is allowed to flake without blocking releases.

## Pull requests

- Open against `main`.
- Reference the spec section your change affects:
  `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md`.
- New code requires tests. Coverage must stay ≥ 85% for modules you touch.
- The `per_cell.parquet` schema in `src/quantipy_polarity/contracts.py` is
  a SemVer-stable public API; column rename/removal is a major version bump.

## Reporting bugs

GitHub issues. Include:
- `quantipy --version`
- A minimal config + input bundle (synthetic is fine)
- The full traceback
