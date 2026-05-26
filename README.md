# QuantiPy Polarity

Single-shot planar polarity quantification from raw microscopy images — a
Python implementation and packaging of the QuantifyPolarity (QP) PCA
cell-by-cell polarity pipeline, plus migration-front detection, rose plots,
polarity vector maps, and a self-contained HTML report.

## Status: v0.1.0 Phase 5 complete

This repository now implements the full end-to-end pipeline.  `quantipy run`
orchestrates all stages and writes a self-contained `report.html`.
See `docs/superpowers/plans/` for the phased roadmap.

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | CLI scaffold, Pydantic config | ✅ Complete |
| 2 | Masks → polarity pipeline | ✅ Complete |
| 3 | TIF/ND2 ingest + Cellpose-SAM segmentation | ✅ Complete |
| 4 | Migration front detection + visualization | ✅ Complete |
| 5 | `quantipy run` orchestration + resume/atomic writes | ✅ Complete |
| 6 | Demo bundle + validation + HTML report | 🔲 Planned |
| 7 | Interactive viewer + experimental analyses | 🔲 Planned |

## Quickstart (Phase 5)

```bash
pip install -e ".[dev,pipeline]"
quantipy init-config --mode masks --output config.yaml
quantipy run --config config.yaml --output ./results
open ./results/report.html
```

`quantipy run` orchestrates all stages end-to-end and writes a self-contained
`report.html`.  Re-running the same command on an existing results directory
**resumes automatically** — only stages that have not yet completed are
re-executed.

### Pipeline resume

| Flag | Behaviour |
|------|-----------|
| *(none)* / `--resume` | Skip stages already marked `done`; retry from the first `failed` stage |
| `--force` | Wipe all stage-status caches and re-run every stage from scratch |

See `docs/pipeline.md` for the full orchestration architecture, stage
descriptions, and run directory layout.

---

## Install (Phase 1 — CLI only)

```bash
git clone https://github.com/mcleanT/QuantiPy-Polarity.git
cd QuantiPy-Polarity
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

### Full pipeline install (TIF/ND2 ingest + Cellpose segmentation)

```bash
pip install -e ".[dev,pipeline]"
```

The `[pipeline]` extra installs `nd2reader`, `cellpose`, `matplotlib`, `tqdm`,
and other dependencies required for raw-image processing. The base install
(`pip install -e .`) is sufficient for the `masks` mode (Phase 2 quickstart).

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
