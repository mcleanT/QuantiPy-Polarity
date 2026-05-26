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

## Input Modes: TIF and ND2 Ingest (Phase 3+)

QuantiPy Polarity supports three input modes. The `masks` mode (Phase 2) requires
pre-segmented label masks. The `tif` and `nd2` modes (Phase 3) accept raw
microscopy images and segment them using Cellpose-SAM.

### TIF ingest

Two schemes are supported:

**Stack scheme** (`tif_scheme: stack`): A single multi-page TIF per FOV with
channels as the first axis `(C, H, W)`. This is the default.

**Multifile scheme** (`tif_scheme: multifile`): One TIF per channel per FOV,
named `<fov_id>_ch{N}.tif` (controlled by `channel_suffix_template`).

Both schemes normalize the membrane channel to float32 [0, 1] before
segmentation. The `channel_membrane` config field selects which channel
to use (0-indexed).

### ND2 ingest

`.nd2` files are loaded via `nd2reader` (included in `[pipeline]` extras).
Pixel size is read from ND2 metadata and falls back to `pixel_size_um` from
config if metadata is missing or invalid.

Z-projection policy is controlled by `z_policy`:
- `mip`: maximum intensity projection (recommended for thick samples)
- `substack`: MIP over a specific z-range (`substack_range: [z_min, z_max]`)
- `none`: use the middle z-plane

### Cellpose-SAM segmentation

After ingest, the membrane channel (uint16) is passed to Cellpose-SAM
(`pretrained_model="cpsam"`, Cellpose ≥3.0). The `segment.diameter_px` config
field sets the expected cell diameter in pixels. Label masks are validated
for contiguous IDs (1..N, background=0) and written as uint16 TIFs.

Label masks and membrane TIFs written by `quantipy segment` are fully
compatible with `quantipy polarity` (Phase 2 masks-mode contract).

### Coordinate conventions reminder

All operations use `(y, x)` pixel coordinates (numpy/scikit-image convention).
Angles are in degrees: `[0, 180)` for axial polarity. See the contract table
in `src/quantipy_polarity/contracts.py` for the full schema.

## Migration front

`quantipy front` detects the spatial boundary between the dense cell mass and the
open region (wound space or leading edge). It computes:

- `dist_to_front_um`: Euclidean distance from each cell centroid to the nearest
  front pixel, in microns.
- `mig_dir_deg`: direction from the cell toward the front, in degrees [0, 360).
- `mig_alignment`: magnitude-weighted alignment score in [-1, +1].
  Positive = cells on average point *toward* the front (biologically expected for
  polarised collective migration). Zero = random alignment. Negative = cells point
  away from front.

**Validity requirement:** a definable front must exist. Random-walk, rotational,
or non-migrating tissue should skip migration analysis (`migration.detect_front: false`).
See `docs/migration-front.md` for the algorithm and tuning guide.

## Ingest stage (Phase 5)

The `ingest` stage is the first step of `quantipy run` and is also available as
`quantipy ingest --config config.yaml --output ./results`.

It converts raw microscopy input (`.nd2` or multi-page / multifile `.tif`) into
normalised per-FOV membrane TIFs at `01_ingest/<fov_id>_membrane.tif`.
Normalisation converts the selected membrane channel to float32 [0, 1].

**Masks mode skips this stage automatically.** When `mode: masks`, QuantiPy
reads pre-segmented label masks directly from `input.masks_dir`; the `01_ingest/`
directory is not created and `stage_status/ingest.json` is written with
`status: skipped`.

See `docs/pipeline.md` for the full seven-stage orchestration architecture,
resume semantics, and run directory layout.
