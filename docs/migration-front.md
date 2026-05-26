# Migration-Front Detection

## Algorithm overview

`quantipy front` uses the **v6 real-bg classification** algorithm, lifted from
`pipeline/debug_polarity.py:compute_migration_field` in the research repo
(optoCelsr 25h migration, validated on 50 FOVs across C10 and D11 clones).

### Pipeline

1. **Cell-density field.** Gaussian-filter the binary cell mask
   (`sigma = density_sigma_px`, default 80 px; `mode='reflect'` avoids artificial
   edge-density suppression). This smooths sparse cells and preserves the
   dense-mass / open-region boundary.

2. **Mass region.** Threshold the density field (`density_threshold`, default 0.4).
   Take the single largest connected component; fill holes. This is the cell mass.

3. **Real background classification.** Find connected components of `~mass`.
   Erode each by `border_margin_px` (default 15) to kill thin FOV-edge slivers.
   Keep all blobs that survive erosion AND meet a joint size filter:
   area ≥ max(`min_bg_blob_frac × FOV_area`, `min_bg_blob_rel × largest_surviving_blob_area`).
   This preserves multiple co-equal open regions fragmented by cell protrusions
   (affects ~16/50 FOVs in the optoCelsr dataset).

4. **Front pixels.** Dilate the kept background mask by 1 pixel; intersect with
   mass. Strip `edge_skip_px` (default 2) from image boundaries. Drop front
   segments smaller than `min_segment_px` (default 200 px).

5. **Per-pixel displacement.** `scipy.ndimage.distance_transform_edt` gives the
   nearest front pixel for every pixel. The (vx, vy) displacement vectors drive
   per-cell distance and migration-direction calculations.

## Outputs

| File | Contents |
|------|----------|
| `04_migration/front_um_per_fov.parquet` | `fov_id, front_y_um, front_angle_deg, n_front_px, pixel_size_um` |
| `04_migration/qc/<fov_id>_front_overlay.png` | Membrane + cell outlines + orange front ribbon (written with `--qc`) |

The `front_angle_deg` column is the PCA principal-axis angle of the front-pixel
coordinates, in degrees [0, 180). 0° = horizontal front (cells migrate vertically).

## Tuning

Tune via the `migration.*` YAML block:

```yaml
migration:
  detect_front: true
  front_method: v3_outward    # only supported method in v0.1.0
  erosion_px: 10              # border_margin_px
  classify_fragments: true    # enables the relative-size filter
```

After editing, regenerate overlays with `quantipy front --qc --resume` and compare
the `qc/` directory against `qc_prev/` (created automatically on `--resume`).

## Algorithm provenance

Research repo source: `Hughes Lab/Sachin/Polarity Quantification/pipeline/debug_polarity.py`,
function `compute_migration_field` (v6 real-bg classification, ~125 lines).
Research validation: 50 FOVs, C10 (22 FOVs) + D11 (28 FOVs), 25h optoCelsr migration.
Commit at lift: `phase-3-complete` tag of QuantiPy-Polarity.
