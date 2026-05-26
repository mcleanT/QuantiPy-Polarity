# QuantiPy Polarity

Single-shot planar polarity quantification from raw microscopy images — a
Python implementation and packaging of the QuantifyPolarity (QP) PCA
cell-by-cell polarity pipeline, plus migration-front detection, rose plots,
polarity vector maps, and a self-contained HTML report.

## Contents

- [Quickstart](#quickstart)
- [Documentation](#documentation)
- [CLI reference](#cli-reference)
- [Developer workflow](#developer-workflow)
- [Citation](#citation)

## Status: v0.1.0 — all phases complete

This repository implements the full end-to-end pipeline.  `quantipy run`
orchestrates all stages and writes a self-contained `report.html`.

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | CLI scaffold, Pydantic config | ✅ Complete |
| 2 | Masks → polarity pipeline | ✅ Complete |
| 3 | TIF/ND2 ingest + Cellpose-SAM segmentation | ✅ Complete |
| 4 | Migration front detection + visualization | ✅ Complete |
| 5 | `quantipy run` orchestration + resume/atomic writes | ✅ Complete |
| 6 | Validation + Demo + Release | ✅ Complete |
| 7 | Interactive viewer + experimental analyses | ✅ Complete |

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

## Documentation

| Document | Contents |
|----------|----------|
| [docs/concepts.md](docs/concepts.md) | Biological assumptions, PCA polarity method |
| [docs/pipeline.md](docs/pipeline.md) | Stage-by-stage pipeline description |
| [docs/cli-reference.md](docs/cli-reference.md) | All CLI commands, flags, examples |
| [docs/api-reference.md](docs/api-reference.md) | Public Python API |
| [docs/interactive-viewer.md](docs/interactive-viewer.md) | Per-cell viewer usage guide |
| [docs/migration-front.md](docs/migration-front.md) | Front detection algorithm |
| [docs/validation.md](docs/validation.md) | QP-vs-Python comparison methodology |
| [docs/developer-workflow.md](docs/developer-workflow.md) | Claude-Code integration, slash commands |

## CLI reference

See [`docs/cli-reference.md`](docs/cli-reference.md) for the full command catalogue with
options tables and examples.

## Design + reviews

- Design spec (rev 1): `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md`
- Adversarial review (codex / gpt-5.5): `docs/superpowers/specs/2026-05-26-quantipy-polarity-design-codex-review.txt`
- Phase 1 plan: `docs/superpowers/plans/2026-05-26-quantipy-polarity-phase1-scaffolding.md`

## License

MIT — see [`LICENSE`](LICENSE).

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the full version history.

## Citation

If you use QuantiPy Polarity in your research, please cite it (see `CITATION.cff`):

```bibtex
@software{mclean_quantipy_polarity_2026,
  author  = {McLean, Taggart},
  title   = {{QuantiPy Polarity}},
  year    = {2026},
  version = {0.1.0},
  url     = {https://github.com/mcleanT/QuantiPy-Polarity},
  license = {MIT}
}
```

Please also cite the original QuantifyPolarity tool from the Hughes Lab, whose
boundary-PCA algorithm this package reimplements.

## Developer workflow

See [`docs/developer-workflow.md`](docs/developer-workflow.md) for optional
Claude Code integrations and test/CI setup.
