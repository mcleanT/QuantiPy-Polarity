# Validation

## Purpose

QuantiPy Polarity ships a reproducible QP-vs-Python comparison analysis. Running
`quantipy validate` confirms that you can reproduce the same figure from the
committed paired parquet — it does **not** require QuantifyPolarity to be
installed on your machine. The goal is reproducibility of the analysis alongside
honest reporting of algorithmic differences.

## Validation Data (v0.1.3+)

v0.1.3 ships a single combined parquet with pre-paired per-cell measurements:

- `data/validation/qp_vs_python_real.parquet` — 94,386 cells, 7 columns

Columns:

| Column | Description |
|--------|-------------|
| `clone` | Cell clone identifier (C10 or D11) |
| `fov` | Field-of-view identifier (28 FOVs) |
| `cell_identity` | Per-FOV cell index |
| `qp_magnitude` | QuantifyPolarity polarity magnitude |
| `qp_angle_deg` | QuantifyPolarity polarity axis angle (°) |
| `py_magnitude` | Python (QuantiPy) polarity magnitude |
| `py_angle_deg` | Python (QuantiPy) polarity axis angle (°) |

### Dataset provenance

The data are derived from a 25 h wound-healing migration experiment with two cell
clones (C10, D11). Each cell was measured independently by the Mathematica
QuantifyPolarity tool and by `quantipy polarity`. Cell identity is established by
`(fov, cell_identity)` pair — no centroid matching is needed.

### Real validation metrics (v0.1.4)

| Component | Metric | All cells | mag > 0.05 cells |
|-----------|--------|-----------|-----------------|
| Magnitude | R² | 0.816 | — |
| Magnitude | Slope | 0.668 | — |
| Axis | Median axial Δθ | 6.4° | **4.5°** |
| Axis | Mean cos(2Δθ) | 0.887 | **0.965** |
| Axis | Stokes R² (S₁) | 0.810 | **0.939** |
| Axis | Stokes R² (S₂) | — | **0.921** |

**n_total = 94,386 cells** (no nulls; no downsampling).
**n_angle_filtered = 20,784 cells** (both qp_magnitude > 0.05 AND py_magnitude > 0.05).

## Axial Angle Methodology

### Why polarity axes are axial (mod 180°, not mod 360°)

A polarity *axis* has no intrinsic "head" or "tail" — a cell pointing northeast is
identical to one pointing southwest. Formally, axis angles live in the projective
circle RP¹, which is equivalent to the circle S¹ with antipodal points identified.
In practice this means angles are defined modulo 180°, not 360°.

The consequence for metric design: a cell at +89° and one at −89° are 2° apart
in axis space, but 178° apart in raw angle space. Any metric that treats angle
differences linearly (including Pearson R² on raw angles) will be confounded by
this **axial wraparound** at ±90°. For our data, approximately 5% of well-polarised
cells straddle the ±90° boundary, which is enough to substantially deflate naive R².

### Why magnitude filtering is required

Polarity magnitude measures *how* polarised a cell is. When magnitude is near zero,
both QP and Python return axis angles that are dominated by noise — the polarity
vector is too short to have a stable direction. Comparing axis angles for these
cells does not measure algorithmic agreement; it measures noise vs. noise.

In our 94k-cell dataset, approximately 78% of cells have qp_magnitude < 0.05.
Including them in the angle comparison inflates apparent disagreement without
providing biological signal. We therefore require both qp_magnitude > 0.05 AND
py_magnitude > 0.05 before computing axis agreement metrics.

The threshold `MAGNITUDE_THRESHOLD = 0.05` is defined as a named constant in
`validation/qp_vs_python.py` and applies to all angle metrics.

### Axial Δθ

The correct axial angular difference between two axis angles a and b is:

```
Δθ = |((a − b + 90) % 180) − 90|
```

This maps the difference to [0°, 90°], is symmetric, and handles the ±90° wrap
correctly. We report the **median axial Δθ** as the primary axis agreement metric
because it is robust to outliers and has an intuitive physical interpretation
(half of well-polarised cells agree within median Δθ degrees).

### Stokes-space R²

The standard mathematical representation for axial/orientation data is the
Stokes parameter map:

```
S₁ = cos(2θ)
S₂ = sin(2θ)
```

This maps each axis angle to a point on the unit circle in a *doubled* angle
space where antipodal points (+90° and −90°) map to the same location. Pearson
R² computed separately on the S₁ and S₂ components is a valid regression metric
for axial data that is not confounded by wraparound.

Reference: Mardia & Jupp, "Directional Statistics" (Wiley, 2000), §2.2 and §8.3.

### Mean cos(2Δθ)

The scalar alignment score `mean(cos(2 * Δθ))` is analogous to the mean resultant
length for circular data, adapted to the axial case. Values near 1 indicate
excellent agreement; near 0 indicates random relationship; near −1 indicates
systematic anti-alignment. Our filtered dataset achieves 0.965, which is excellent.

### Why the naive metric was misleading

The v0.1.3 README showed angle R² = 0.468 computed as Pearson R² on raw angle
values. This number is **wrong for axial data** for two reasons:

1. **Axial wraparound**: Cells near ±90° appear as outliers in raw-angle scatter,
   artificially deflating R².
2. **Near-zero-magnitude noise**: ~78% of cells contribute only noise to the angle
   comparison, further deflating apparent agreement.

The corrected metrics (Stokes R² ≈ 0.94, median Δθ = 4.5°, cos(2Δθ) = 0.965)
show that the axis agreement on well-polarised cells is actually excellent.

## Algorithmic Differences

### Magnitude

QP reports magnitudes approximately 50% larger than the Python implementation.
This is a systematic normalization difference: both tools use boundary-PCA
on the Fourier k=2 component, but the Mathematica and Python implementations
use different normalization conventions for the PCA eigenvalue ratio. The
linear relationship is preserved (slope 0.668, R² = 0.816); magnitudes from
the two tools should not be compared directly without the ~1.5× scaling factor.

### Axis angle

Axis agreement on well-polarised cells (magnitude > 0.05) is excellent:
median Δθ = 4.5°, cos(2Δθ) = 0.965, Stokes R² ≈ 0.93. The small residual
disagreement is expected: both tools implement boundary-PCA independently,
with minor differences in how boundary pixels are selected, how edges are
handled, and how the 180° symmetry axis is resolved. These differences are
small (< 5° median) and do not affect biological interpretation.

## Acceptance Thresholds (v0.1.4)

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Magnitude R² | > 0.70 | Real data R² = 0.816; threshold allows for subsets |
| cos(2Δθ) | > 0.85 OR median Δθ < 10° | Lenient; real data achieves 0.965 / 4.5° |

Runs that fall below the magnitude threshold, or fail both angle criteria,
exit with a non-zero status and print a diagnostic message.

## Synthetic Data (test fixtures only)

`validation/synthetic_data.py` generates deterministic fake parquets for unit
tests. **This is not the validation reference** — it is used only by the test
suite as a lightweight in-memory fixture that does not require the real 3 MB
parquet to be loaded during tests.

Synthetic data properties (seed=42): R² ≈ 0.97, slope ≈ 1.0, σ_mag=0.03,
σ_angle=2°. These unrealistically tight numbers are intentional: they make
tests deterministic and fast, while the real parquet captures true algorithmic
behavior.

## Output Figure

`quantipy validate` produces a 2-panel figure:

- **Panel A** — Magnitude scatter (QP vs Python), with identity line and best-fit
  regression. Unchanged from v0.1.3.
- **Panel B** — Axial Δθ histogram with two overlays: all cells (light blue) and
  magnitude-filtered cells (dark blue). Median Δθ annotated for both populations.
  X-axis runs 0°–90° (the full axial range).

Both PDF (vector, editable text) and PNG (600 DPI) are saved to
`~/.cache/quantipy/validation/` by default.

## Reproducibility

`quantipy validate` is deterministic given the committed parquet. CI checks that
the command runs without error and that metrics exceed the acceptance thresholds.
