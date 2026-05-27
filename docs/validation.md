# Validation

## Purpose

QuantiPy Polarity ships a reproducible QP-vs-Python comparison analysis. Running
`quantipy validate` confirms that you can reproduce the same regression figure from
the committed paired parquet — it does **not** require QuantifyPolarity to be
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

### Real validation metrics

| Metric | r | R² | Slope | Intercept |
|--------|---|-----|-------|-----------|
| Magnitude | 0.904 | 0.816 | 0.668 | 0.003 |
| Axis angle | 0.684 | 0.468 | 0.692 | 1.170 |

**n = 94,386 cells** (no nulls; no downsampling).

## Algorithmic Differences

### Magnitude

QP reports magnitudes approximately 50% larger than the Python implementation.
This is a systematic normalization difference: both tools use boundary-PCA
on the Fourier k=2 component, but the Mathematica and Python implementations
use different normalization conventions for the PCA eigenvalue ratio. The
linear relationship is preserved (slope 0.668, R² = 0.816); magnitudes from
the two tools should not be compared directly without the ~1.5× scaling factor.

### Axis angle

The angle correlation is moderate (R² = 0.468). Angles are defined on [−180°, 180°]
for both tools but the convention for resolving the 180° ambiguity differs slightly.
For cells with low magnitude (near-zero polarity), the axis angle is ill-defined and
both tools return noisy estimates; these cells dominate the angle variance.

## Acceptance Thresholds (v0.1.3)

| Metric         | Threshold         | Rationale |
|----------------|-------------------|-----------|
| Magnitude R²   | > 0.70            | Real data R² = 0.816; threshold allows for subsets |

Runs that fall below the threshold exit with a non-zero status and print a
diagnostic message.

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

`quantipy validate` produces a 2-panel scatter plot (magnitude left, angle right)
with both an identity line (y = x, black dashed) and a best-fit regression line
(orange), saved as both PDF and PNG to `~/.cache/quantipy/validation/`.

## Reproducibility

`quantipy validate` is deterministic given the committed parquet. CI checks that
the command runs without error and that R² exceeds the acceptance threshold.
