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
| 6 | Validation + Demo + Release | ✅ complete |
| 7 | Interactive viewer + experimental analyses | 🔲 Planned |

## Quickstart

```bash
# 1. Install
pip install -e ".[dev,pipeline]"

# 2. Download the demo bundle (~5 MB, synthetic cells)
quantipy download-demo
# → extracts to ~/.cache/quantipy/demo/

# 3. Run the pipeline (masks mode, no GPU required)
quantipy run --config ~/.cache/quantipy/demo/config.yaml --output ./demo_results

# 4. Open the report
open ./demo_results/report.html      # macOS
xdg-open ./demo_results/report.html  # Linux
```

For developers who have cloned the repo, the demo files are also available directly at `demo/`:

```bash
quantipy run --config demo/config.yaml --output ./demo_results
```

To regenerate the QP-vs-Python validation figure:

```bash
quantipy validate
# → prints R², slope; writes validation_qp_vs_python.pdf to ~/.cache/quantipy/validation/
```

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
