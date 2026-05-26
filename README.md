# QuantiPy Polarity

Single-shot planar polarity quantification from raw microscopy images — a Python implementation and packaging of the QuantifyPolarity (QP) PCA cell-by-cell polarity pipeline, plus migration-front detection, rose plots, polarity vector maps, and a self-contained HTML report.

## Status: v0.1.0 design phase

This repository currently contains the design specification for v0.1.0. Implementation has not yet begun.

- **Design spec (rev 1):** [`docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md`](docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md)
- **Adversarial review (codex / gpt-5.5):** [`docs/superpowers/specs/2026-05-26-quantipy-polarity-design-codex-review.txt`](docs/superpowers/specs/2026-05-26-quantipy-polarity-design-codex-review.txt)

The spec covers package layout, CLI surface, input modes (`.nd2` / multi-page `.tif` / pre-segmented label masks), output bundle (per-FOV polarity maps + rose plots + quantitative tables + migration overlays + HTML report), validation evidence (QP-vs-Python linear-relationship analysis on ~114k cells), resume/atomic-write semantics, dependency strategy, testing tiers, and the carve-out plan from the upstream research project.

## Planned quickstart (not yet runnable)

```bash
conda env create -f environment.yml && conda activate quantipy && pip install -e .
quantipy download-demo
quantipy init-config --mode masks --output config.yaml
quantipy run --config config.yaml --output ./results
open ./results/report.html
```

## License

MIT — see [`LICENSE`](LICENSE).

## Citation

A `CITATION.cff` will be added before the v0.1.0 tag. The original QuantifyPolarity tool this project reimplements will be cited there.
