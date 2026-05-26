# QuantiPy Polarity

Single-shot planar polarity quantification from raw microscopy images — a
Python implementation and packaging of the QuantifyPolarity (QP) PCA
cell-by-cell polarity pipeline, plus migration-front detection, rose plots,
polarity vector maps, and a self-contained HTML report.

## Status: v0.1.0 Phase 1 (scaffolding) complete

This repository now installs and exposes the full CLI surface, with most
subcommands stubbed for later phases. See `docs/superpowers/plans/` for the
phased roadmap.

- ✅ Phase 1 — CLI shell, config schema, init-config, fast-tier CI
- ✅ Phase 2 — Masks → polarity (smallest viable pipeline) — `quantipy polarity` + `quantipy aggregate`
- ⏳ Phase 3 — TIF / ND2 ingest + Cellpose segmentation
- ⏳ Phase 4 — Migration front + visualization
- ⏳ Phase 5 — Run orchestration + HTML report + resume/atomic-writes
- ⏳ Phase 6 — Validation + demo bundle + GitHub Release
- ⏳ Phase 7 — Interactive viewer + experimental analyses + docs
- ⏳ Phase 8 — Research-dir upstream migration

## Install (Phase 1 — CLI only)

```bash
git clone https://github.com/mcleanT/QuantiPy-Polarity.git
cd QuantiPy-Polarity
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

## Verify

```bash
quantipy --version          # 0.1.0
quantipy --help             # primary + advanced command groups
quantipy init-config --mode masks --output config.yaml
cat config.yaml             # mode: masks, valid Pydantic schema
quantipy run                # stubbed: "not implemented in v0.1.0 Phase 1"
```

## Planned full quickstart (lands at Phase 6)

```bash
conda env create -f environment.yml && conda activate quantipy && pip install -e .
quantipy download-demo
quantipy init-config --mode masks --output config.yaml
quantipy run --config config.yaml --output ./results
open ./results/report.html
```

## Design + reviews

- Design spec (rev 1): `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md`
- Adversarial review (codex / gpt-5.5): `docs/superpowers/specs/2026-05-26-quantipy-polarity-design-codex-review.txt`
- Phase 1 plan: `docs/superpowers/plans/2026-05-26-quantipy-polarity-phase1-scaffolding.md`

## License

MIT — see [`LICENSE`](LICENSE).

## Citation

A `CITATION.cff` will be added before the v0.1.0 tag. The original
QuantifyPolarity tool this project reimplements is cited there.

## Developer workflow

See [`docs/developer-workflow.md`](docs/developer-workflow.md) for optional
Claude Code integrations and test/CI setup.
