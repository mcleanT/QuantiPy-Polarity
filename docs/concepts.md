# Concepts (Phase 2 scope)

## Planar polarity, briefly

Planar cell polarity (PCP) is the asymmetric distribution of a protein along
the in-plane axis of a cell. In epithelial sheets, polarity proteins like
Vangl, Frizzled, Celsr1, and Crumbs accumulate at one side of the cell
periphery (or in a graded pattern), defining a tissue-scale orientation.

## What QuantiPy measures

For each segmented cell, QuantiPy computes:
- **`axis_deg`** — the dominant axis of the membrane-marker distribution, as
  an axial angle (mod 180°). 0° = horizontal, 90° = vertical.
- **`magnitude`** — a unit-less polarization strength in [0, 1]. 0 = uniform
  signal around the cell perimeter, 1 = perfectly bilobed (signal concentrated
  on one axis).

The algorithm is a Fourier-k=2 decomposition of mean-subtracted membrane
intensity along boundary pixels, weighted by their distance from the cell
interior centroid. Mathematically equivalent (to within boundary-pixel
attribution) to the QP PCA-Cell-by-Cell algorithm — see `docs/validation.md`
(Phase 6) for the QP-vs-Python equivalence evidence.

## Phase 2 inputs / outputs

- **Input:** paired directories of membrane TIFs and pre-segmented label-mask
  TIFs (one mask per FOV, uint16, 0 = background, 1..N = cells).
- **Output:** per-FOV parquets in `results/03_polarity/per_fov/<fov_id>.parquet`
  and one experiment-wide parquet at `results/05_aggregated/per_cell.parquet`,
  both matching the `PER_CELL_COLUMNS` schema in `contracts.py`.

## What's deferred to later phases

- ND2 / TIF ingest + Cellpose-SAM segmentation (Phase 3)
- Migration-front detection + per-cell migration alignment (Phase 4)
- Plots + HTML report (Phases 4–5)
- Interactive viewer + curated analyses (Phase 7)
