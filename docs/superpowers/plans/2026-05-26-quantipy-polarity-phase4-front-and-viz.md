# QuantiPy Polarity — Phase 4: Migration Front Detection + Visualization

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automated migration-front detection from label masks, per-cell distance/alignment computations, and a full matplotlib-based visualization suite (polarity vector maps, rose plots, front overlays, population summary). Replace the `front` and `plot` stubs with real commands. Populate the `dist_to_front_um`, `mig_alignment`, and `mig_dir_deg` columns in `per_cell.parquet` that were declared in Phase 1 but left null.

**Architecture:** Three new sub-packages fill in the previously empty `migration/` and `viz/` directories. `migration/front_detect.py` lifts the v6 real-bg `compute_migration_field` algorithm from `pipeline/debug_polarity.py` and wraps it to emit a typed `FrontResult` per FOV. `migration/front_io.py` serialises those results to `front_um_per_fov.parquet`. `migration/distance.py` reads both files to populate the three migration columns in `per_cell.parquet`. `viz/_style.py` imports from `Science/styles/figstyle.py` (absolute import via sys.path insert) with a self-contained fallback baked in so the public repo needs no external dependency. `viz/vector_map.py`, `viz/rose_plot.py`, `viz/front_overlay.py`, and `viz/summary.py` each produce one figure type. `_cli_front.py` and `_cli_figures.py` wire these into `quantipy front` and `quantipy plot`, replacing stubs. All tests are synthetic-fixture-based (no real microscopy). Figure tests verify file existence and binary header, not pixel content.

**Tech Stack:** Python 3.11+, numpy 1.26+, scipy 1.11+, scikit-image 0.22+, pandas 2.1+, pyarrow 14+, matplotlib 3.8+, Click 8.1+, Pydantic 2.5+, structlog 24+.

**Spec source:** `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` (rev 1), §§4 (layout), 5 (CLI), 6 (config + stage contracts), 7 (outputs), 14 (module lift table), 16 (data contracts).

**Working directory:** clone of `https://github.com/mcleanT/QuantiPy-Polarity`. Phase 3 already landed (tag `phase-3-complete`). Working tree should be clean on `main`. 122 tests passing.

**Lift sources** (research repo, read-only references):
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/debug_polarity.py` — `compute_migration_field` (v6 real-bg, lines 140–265); `draw_axial_line` drawing primitive; `cell_centroid_and_size`.
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/recompute_migration_v3.py` — per-cell `mig_angle_deg`, `mig_distance_px`, `axial_diff_deg` pattern.
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/compute_48h_local_migration.py` — `align_wt` weighted alignment score formula.
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/plot_rose_pair_halfdisk.py` — half-disk rose convention (axial mod 180), rcParams block.
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/plot_fov_polarity_panel.py` — polarity vector overlay pattern, coherence helper.
- `Science/styles/figstyle.py` — `apply_nature_style`, `PALETTE`, `save_figure` (canonical lab figstyle).

**Acceptance criteria for Phase 4 completion:**
1. `quantipy front --config config.yaml --input <seg_dir> --output <out_dir>` emits `<out_dir>/04_migration/front_um_per_fov.parquet` with columns `fov_id, front_y_um, front_angle_deg, n_front_px` plus per-FOV PNG QC overlays.
2. `quantipy front` also updates `dist_to_front_um`, `mig_dir_deg`, `mig_alignment` in `<out_dir>/05_aggregated/per_cell.parquet` (or writes `04_migration/per_cell_migration.parquet` with those columns added).
3. `quantipy plot --config config.yaml --output <out_dir>` writes vector maps (PNG+PDF), rose plots (PDF), front overlay PNGs, and a population summary PDF into `<out_dir>/06_plots/`.
4. Both commands replace their stubs: `quantipy front --help` and `quantipy plot --help` no longer show "(Phase 4 stub)" messages.
5. Full pytest suite: 122 (Phase 3) + ≥28 new tests = **≥150 passed**. All new tests are fast-tier (no real microscopy).
6. `quantipy --help` still shows all commands; no import errors on cold start.
7. README updated to reflect Phase 4 completion; tag `phase-4-complete` pushed.

---

## File Structure (locked at planning time)

```
QuantiPy-Polarity/
├── src/quantipy_polarity/
│   ├── migration/
│   │   ├── __init__.py                        # Modify Task 1: export public API
│   │   ├── front_detect.py                    # Create Task 2: FrontResult + detect_front()
│   │   ├── front_io.py                        # Create Task 3: write/read front_um_per_fov.parquet
│   │   └── distance.py                        # Create Task 4: per-cell dist + alignment
│   ├── viz/
│   │   ├── __init__.py                        # Modify Task 5: export public API
│   │   ├── _style.py                          # Create Task 5: figstyle import + fallback
│   │   ├── vector_map.py                      # Create Task 7: per-FOV polarity vector map
│   │   ├── rose_plot.py                       # Create Task 9: half-disk rose plot
│   │   ├── front_overlay.py                   # Create Task 11: front overlay PNG
│   │   └── summary.py                         # Create Task 13: population summary panel
│   ├── _cli_front.py                          # Create Task 15: real `quantipy front`
│   ├── _cli_figures.py                        # Create Task 17: real `quantipy plot`
│   ├── _stubs.py                              # Modify Task 19: remove front + plot stubs
│   └── cli.py                                 # Modify Task 19: register new CLI modules
├── tests/
│   ├── migration/
│   │   ├── __init__.py                        # Create Task 2
│   │   ├── test_front_detect.py               # Create Task 2
│   │   ├── test_front_io.py                   # Create Task 3
│   │   └── test_distance.py                   # Create Task 4
│   ├── viz/
│   │   ├── __init__.py                        # Create Task 6
│   │   ├── test_style.py                      # Create Task 6
│   │   ├── test_vector_map.py                 # Create Task 8
│   │   ├── test_rose_plot.py                  # Create Task 10
│   │   ├── test_front_overlay.py              # Create Task 12
│   │   └── test_summary.py                    # Create Task 14
│   └── cli/
│       ├── test_cli_front.py                  # Create Task 16
│       └── test_cli_figures.py                # Create Task 18
├── docs/
│   ├── migration-front.md                     # Modify Task 20: algorithm provenance
│   └── concepts.md                            # Modify Task 20: migration notes
├── README.md                                  # Modify Task 21: Phase 4 badge
└── CLAUDE.md                                  # Modify Task 21: update command map
```

---

## Task 1: Scaffold `migration/__init__.py` with typed `FrontResult` contract

**Files:** Modify `src/quantipy_polarity/migration/__init__.py`; modify `src/quantipy_polarity/contracts.py`

Add `FrontResult` Pydantic model to `contracts.py` and re-export from `migration/__init__.py`. All Phase 4 migration modules import `FrontResult` from `contracts`, never from each other.

- [ ] **Step 1: Read `src/quantipy_polarity/contracts.py`**

  Confirm existing content: `PerCellRow`, `PER_CELL_COLUMNS`, `FOVManifestEntry`, `SegmentationResult`. Note the `mig_dir_deg`, `mig_alignment`, `dist_to_front_um` fields on `PerCellRow` are `float | None = None`.

- [ ] **Step 2: Append `FrontResult` to `src/quantipy_polarity/contracts.py`**

  After the `SegmentationResult` class, append:

  ```python
  class FrontResult(BaseModel):
      """Per-FOV migration-front detection result.

      front_y_um: mean y-coordinate of front pixels, in microns from image top.
      front_angle_deg: orientation of the front polyline in degrees [0, 180).
          0° = horizontal front (cells migrate vertically).
          Computed as the principal axis angle of front-pixel coordinates.
          NaN when n_front_px == 0.
      n_front_px: number of pixels classified as front.
      front_mask_shape: (H, W) of the source label mask (for sanity checks).
      """

      fov_id: str
      front_y_um: float | None = None
      front_angle_deg: float | None = None
      n_front_px: int = Field(ge=0, default=0)
      front_mask_shape: tuple[int, int] = (0, 0)
      pixel_size_um: float = Field(gt=0, default=1.0)
  ```

- [ ] **Step 3: Replace content of `src/quantipy_polarity/migration/__init__.py`**

  ```python
  """Migration-front detection and per-cell distance/alignment. Phase 4."""

  from quantipy_polarity.contracts import FrontResult

  __all__ = ["FrontResult"]
  ```

- [ ] **Step 4: Verify import chain**

  ```bash
  python -c "from quantipy_polarity.migration import FrontResult; print('FrontResult OK:', FrontResult.__name__)"
  ```

  Expected: `FrontResult OK: FrontResult`

- [ ] **Step 5: Run baseline tests**

  ```bash
  pytest -q 2>&1 | tail -3
  ```

  Expected: `122 passed` (or `122 passed, 1 skipped`). No regressions.

- [ ] **Step 6: Commit**

  ```bash
  git add src/quantipy_polarity/contracts.py src/quantipy_polarity/migration/__init__.py
  git commit -m "feat(migration): add FrontResult contract + migration package public API"
  ```

---

## Task 2: Implement `migration/front_detect.py` + tests

**Files:** Create `src/quantipy_polarity/migration/front_detect.py`; create `tests/migration/__init__.py`; create `tests/migration/test_front_detect.py`

Lift the v6 `compute_migration_field` algorithm verbatim from `pipeline/debug_polarity.py` (lines 140–265), rename to `_compute_migration_field_v6`, and wrap it in a public `detect_front(labels, pixel_size_um, **kwargs) -> FrontResult` function that converts pixel outputs to physical units.

- [ ] **Step 1: Create `src/quantipy_polarity/migration/front_detect.py`**

  ```python
  """Automated migration-front detection from label masks.

  Algorithm: v6 real-bg classification lifted from
  ``pipeline/debug_polarity.py:compute_migration_field`` in the research repo.

  Public API
  ----------
  detect_front(labels, pixel_size_um, **kwargs) -> FrontResult
  """

  from __future__ import annotations

  import numpy as np
  from scipy import ndimage as ndi

  from quantipy_polarity.contracts import FrontResult


  def _compute_migration_field_v6(
      labels: np.ndarray,
      density_sigma_px: float = 80.0,
      density_threshold: float = 0.4,
      min_segment_px: int = 200,
      min_bg_blob_frac: float = 0.02,
      min_bg_blob_rel: float = 0.30,
      border_margin_px: int = 15,
      edge_skip_px: int = 2,
  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
      """Return (vx, vy, front_mask) per-pixel vectors toward the migration front.

      v6 real-bg classification: keeps all background blobs that survive a
      border erosion AND meet both absolute-size floor AND relative-size threshold
      vs the largest surviving blob. Kills thin FOV-edge slivers; preserves
      legitimate co-equal open regions fragmented by cell protrusions.

      Parameters
      ----------
      labels : (H, W) uint16/int32 label mask; 0 = background.
      density_sigma_px : Gaussian sigma for cell-density field (pixels).
      density_threshold : binarisation threshold on density field [0, 1].
      min_segment_px : minimum front-segment area in pixels.
      min_bg_blob_frac : absolute size floor as fraction of FOV area.
      min_bg_blob_rel : relative floor as fraction of largest surviving bg blob.
      border_margin_px : erosion radius for killing thin FOV-edge slivers.
      edge_skip_px : pixels to zero out at image boundary in front_mask.

      Returns
      -------
      vx, vy : (H, W) float32 displacement toward nearest front pixel.
      front_mask : (H, W) bool mask of front pixels.
      """
      H, W = labels.shape
      zero_vec = np.zeros((H, W), np.float32)
      empty_front = np.zeros((H, W), bool)

      cells = labels > 0
      if not cells.any():
          return zero_vec, zero_vec, empty_front

      D = ndi.gaussian_filter(
          cells.astype(np.float32), sigma=density_sigma_px, mode="reflect"
      )

      mass_raw = D > density_threshold
      if not mass_raw.any():
          return zero_vec, zero_vec, empty_front
      lbl, n = ndi.label(mass_raw, structure=ndi.generate_binary_structure(2, 2))
      if n == 0:
          return zero_vec, zero_vec, empty_front
      areas = np.bincount(lbl.ravel())
      areas[0] = 0
      mass = lbl == int(np.argmax(areas))
      mass = ndi.binary_fill_holes(mass)

      bg = ~mass
      bg_lbl, n_bg = ndi.label(bg, structure=ndi.generate_binary_structure(2, 2))
      if n_bg == 0:
          return zero_vec, zero_vec, empty_front
      bg_eroded = ndi.binary_erosion(bg, iterations=int(border_margin_px))
      survived_ids = set(np.unique(bg_lbl[bg_eroded]))
      survived_ids.discard(0)
      if not survived_ids:
          return zero_vec, zero_vec, empty_front
      fov_area = H * W
      surviving_areas = {bid: int((bg_lbl == bid).sum()) for bid in survived_ids}
      largest_area = max(surviving_areas.values())
      cutoff = max(min_bg_blob_frac * fov_area, min_bg_blob_rel * largest_area)
      kept_ids = [bid for bid, a in surviving_areas.items() if a >= cutoff]
      if not kept_ids:
          return zero_vec, zero_vec, empty_front
      fov_bg_kept = np.isin(bg_lbl, kept_ids)

      bg_dilated = ndi.binary_dilation(
          fov_bg_kept, structure=ndi.generate_binary_structure(2, 2)
      )
      front_mask = mass & bg_dilated
      if edge_skip_px > 0:
          front_mask[:edge_skip_px, :] = False
          front_mask[-edge_skip_px:, :] = False
          front_mask[:, :edge_skip_px] = False
          front_mask[:, -edge_skip_px:] = False

      seg_lbl, n_seg = ndi.label(
          front_mask, structure=ndi.generate_binary_structure(2, 2)
      )
      if n_seg == 0:
          return zero_vec, zero_vec, empty_front
      seg_areas = np.bincount(seg_lbl.ravel())
      seg_areas[0] = 0
      keep_seg = np.where(seg_areas >= min_segment_px)[0]
      if len(keep_seg) == 0:
          return zero_vec, zero_vec, empty_front
      front_mask = np.isin(seg_lbl, keep_seg)

      not_front = ~front_mask
      _, (nr, nc) = ndi.distance_transform_edt(not_front, return_indices=True)
      rows = np.arange(H)[:, None].astype(np.float32)
      cols = np.arange(W)[None, :].astype(np.float32)
      vy = nr.astype(np.float32) - rows
      vx = nc.astype(np.float32) - cols

      return vx, vy, front_mask


  def _front_principal_angle(front_mask: np.ndarray) -> float:
      """Return orientation of front pixels via PCA, degrees [0, 180).

      Fits a line to the (y, x) coordinates of front pixels; returns the
      angle of the first principal component in degrees. 0° = horizontal.
      Returns NaN if fewer than 3 front pixels.
      """
      ys, xs = np.nonzero(front_mask)
      if len(ys) < 3:
          return float("nan")
      coords = np.stack([xs.astype(float), ys.astype(float)], axis=1)
      coords -= coords.mean(axis=0)
      _, _, vt = np.linalg.svd(coords, full_matrices=False)
      dx, dy = vt[0]  # principal direction in (x, y)
      angle_deg = float(np.degrees(np.arctan2(dy, dx))) % 180.0
      return angle_deg


  def detect_front(
      labels: np.ndarray,
      pixel_size_um: float,
      fov_id: str = "FOV_00",
      **kwargs: object,
  ) -> FrontResult:
      """Detect the migration front from a label mask.

      Wraps _compute_migration_field_v6 and converts pixel coordinates to
      physical units (microns).

      Parameters
      ----------
      labels : (H, W) integer label mask; 0 = background.
      pixel_size_um : microns per pixel (from config input.pixel_size_um).
      fov_id : string identifier for this FOV.
      **kwargs : forwarded to _compute_migration_field_v6 (tuning parameters).

      Returns
      -------
      FrontResult with front_y_um, front_angle_deg, n_front_px populated.
      front_y_um is NaN and n_front_px == 0 when no front is detected.
      """
      labels = np.asarray(labels)
      if labels.ndim != 2:
          raise ValueError(f"labels must be 2-D, got shape {labels.shape}")

      _vx, _vy, front_mask = _compute_migration_field_v6(labels, **kwargs)
      n_front = int(front_mask.sum())

      if n_front == 0:
          return FrontResult(
              fov_id=fov_id,
              front_y_um=None,
              front_angle_deg=None,
              n_front_px=0,
              front_mask_shape=labels.shape,
              pixel_size_um=pixel_size_um,
          )

      ys, _xs = np.nonzero(front_mask)
      front_y_um = float(ys.mean() * pixel_size_um)
      front_angle_deg = _front_principal_angle(front_mask)
      if np.isnan(front_angle_deg):
          front_angle_deg = None

      return FrontResult(
          fov_id=fov_id,
          front_y_um=front_y_um,
          front_angle_deg=front_angle_deg,
          n_front_px=n_front,
          front_mask_shape=labels.shape,
          pixel_size_um=pixel_size_um,
      )
  ```

- [ ] **Step 2: Create `tests/migration/__init__.py`** (empty file)

  ```bash
  touch tests/migration/__init__.py
  ```

- [ ] **Step 3: Create `tests/migration/test_front_detect.py`**

  ```python
  """Tests for migration/front_detect.py.

  All tests use synthetic label masks — no real microscopy data.
  The dense-cells-on-left / open-space-on-right pattern reliably produces a
  vertical front (angle ~90°) that the v6 algorithm can detect.
  """

  from __future__ import annotations

  import numpy as np
  import pytest

  from quantipy_polarity.migration.front_detect import (
      _compute_migration_field_v6,
      _front_principal_angle,
      detect_front,
  )
  from quantipy_polarity.contracts import FrontResult


  def _make_half_dense_labels(
      H: int = 128, W: int = 128, cell_w: int = 8
  ) -> np.ndarray:
      """Left half filled with grid cells; right half empty background."""
      labels = np.zeros((H, W), dtype=np.uint16)
      cell_id = 1
      for r in range(0, H, cell_w):
          for c in range(0, W // 2, cell_w):
              labels[r : r + cell_w, c : c + cell_w] = cell_id
              cell_id += 1
      return labels


  def test_compute_migration_field_returns_correct_shapes() -> None:
      labels = _make_half_dense_labels(64, 64, 8)
      vx, vy, front_mask = _compute_migration_field_v6(labels, density_sigma_px=15.0, border_margin_px=3)
      assert vx.shape == (64, 64)
      assert vy.shape == (64, 64)
      assert front_mask.shape == (64, 64)
      assert front_mask.dtype == bool


  def test_compute_migration_field_detects_front_on_half_dense() -> None:
      labels = _make_half_dense_labels(128, 128, 8)
      _vx, _vy, front_mask = _compute_migration_field_v6(
          labels, density_sigma_px=20.0, border_margin_px=5
      )
      assert front_mask.sum() > 0, "expected a front to be detected"
      # Front pixels should cluster near x = W/2 (the cell-density boundary)
      _, xs = np.nonzero(front_mask)
      assert xs.mean() > 20, "front should be in the right half of image"


  def test_compute_migration_field_empty_labels_returns_zeros() -> None:
      labels = np.zeros((64, 64), dtype=np.uint16)
      vx, vy, front_mask = _compute_migration_field_v6(labels)
      assert front_mask.sum() == 0
      assert vx.sum() == 0.0
      assert vy.sum() == 0.0


  def test_front_principal_angle_horizontal_front() -> None:
      # Horizontal band of pixels → angle near 0°
      mask = np.zeros((64, 64), bool)
      mask[32, 5:60] = True
      angle = _front_principal_angle(mask)
      assert not np.isnan(angle)
      assert angle < 10.0 or angle > 170.0, f"expected near 0/180, got {angle}"


  def test_front_principal_angle_vertical_front() -> None:
      # Vertical band → angle near 90°
      mask = np.zeros((64, 64), bool)
      mask[5:60, 32] = True
      angle = _front_principal_angle(mask)
      assert not np.isnan(angle)
      assert 80.0 < angle < 100.0, f"expected near 90°, got {angle}"


  def test_front_principal_angle_too_few_pixels_returns_nan() -> None:
      mask = np.zeros((32, 32), bool)
      mask[10, 10] = True
      assert np.isnan(_front_principal_angle(mask))


  def test_detect_front_returns_front_result() -> None:
      labels = _make_half_dense_labels(128, 128, 8)
      result = detect_front(labels, pixel_size_um=0.65, fov_id="FOV_01",
                            density_sigma_px=20.0, border_margin_px=5)
      assert isinstance(result, FrontResult)
      assert result.fov_id == "FOV_01"
      assert result.pixel_size_um == 0.65
      assert result.front_mask_shape == (128, 128)


  def test_detect_front_populated_fields() -> None:
      labels = _make_half_dense_labels(128, 128, 8)
      result = detect_front(labels, pixel_size_um=0.65, fov_id="FOV_02",
                            density_sigma_px=20.0, border_margin_px=5)
      if result.n_front_px > 0:
          assert result.front_y_um is not None
          assert result.front_y_um > 0.0
          assert result.front_y_um < 128 * 0.65


  def test_detect_front_empty_image_gives_zero_front() -> None:
      labels = np.zeros((64, 64), dtype=np.uint16)
      result = detect_front(labels, pixel_size_um=0.5, fov_id="FOV_EMPTY")
      assert result.n_front_px == 0
      assert result.front_y_um is None
      assert result.front_angle_deg is None


  def test_detect_front_raises_on_wrong_dims() -> None:
      with pytest.raises(ValueError, match="2-D"):
          detect_front(np.zeros((4, 4, 4), dtype=np.uint16), pixel_size_um=0.5)
  ```

- [ ] **Step 4: Run new tests**

  ```bash
  pytest tests/migration/test_front_detect.py -v 2>&1 | tail -15
  ```

  Expected: all 9 tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/quantipy_polarity/migration/front_detect.py tests/migration/__init__.py tests/migration/test_front_detect.py
  git commit -m "feat(migration): implement detect_front() — v6 real-bg algorithm lifted from research repo"
  ```

---

## Task 3: Implement `migration/front_io.py` + tests

**Files:** Create `src/quantipy_polarity/migration/front_io.py`; create `tests/migration/test_front_io.py`

Write/read `front_um_per_fov.parquet`. Schema: `fov_id (str), front_y_um (float64, nullable), front_angle_deg (float64, nullable), n_front_px (int64), pixel_size_um (float64)`. Atomic write (temp + `os.replace`).

- [ ] **Step 1: Create `src/quantipy_polarity/migration/front_io.py`**

  ```python
  """Read/write front_um_per_fov.parquet.

  Schema (SemVer-stable in v0.1.0):
      fov_id          str
      front_y_um      float64  (nullable — None when no front detected)
      front_angle_deg float64  (nullable)
      n_front_px      int64
      pixel_size_um   float64
  """

  from __future__ import annotations

  import os
  import tempfile
  from pathlib import Path
  from typing import Sequence

  import pandas as pd

  from quantipy_polarity.contracts import FrontResult

  _COLUMNS: tuple[str, ...] = (
      "fov_id",
      "front_y_um",
      "front_angle_deg",
      "n_front_px",
      "pixel_size_um",
  )


  def write_front_parquet(
      results: Sequence[FrontResult],
      out_path: Path,
  ) -> Path:
      """Serialise a list of FrontResult objects to Parquet (atomic write).

      Parameters
      ----------
      results : sequence of FrontResult, one per FOV.
      out_path : destination .parquet file path (parent dir must exist).

      Returns
      -------
      Resolved absolute path of the written file.
      """
      out_path = Path(out_path).resolve()
      rows = [
          {
              "fov_id": r.fov_id,
              "front_y_um": r.front_y_um,
              "front_angle_deg": r.front_angle_deg,
              "n_front_px": r.n_front_px,
              "pixel_size_um": r.pixel_size_um,
          }
          for r in results
      ]
      df = pd.DataFrame(rows, columns=list(_COLUMNS))
      df["n_front_px"] = df["n_front_px"].astype("int64")
      df["pixel_size_um"] = df["pixel_size_um"].astype("float64")

      fd, tmp = tempfile.mkstemp(
          dir=out_path.parent, prefix=".front_tmp_", suffix=".parquet"
      )
      os.close(fd)
      try:
          df.to_parquet(tmp, index=False)
          os.replace(tmp, out_path)
      except Exception:
          try:
              os.unlink(tmp)
          except OSError:
              pass
          raise

      return out_path


  def read_front_parquet(path: Path) -> pd.DataFrame:
      """Read front_um_per_fov.parquet into a DataFrame.

      Validates that expected columns are present.

      Parameters
      ----------
      path : path to the .parquet file written by write_front_parquet.

      Returns
      -------
      DataFrame with columns from _COLUMNS.

      Raises
      ------
      ValueError if any required column is missing.
      """
      path = Path(path)
      df = pd.read_parquet(path)
      missing = [c for c in _COLUMNS if c not in df.columns]
      if missing:
          raise ValueError(
              f"front parquet at {path} is missing columns: {missing}"
          )
      return df[list(_COLUMNS)]
  ```

- [ ] **Step 2: Create `tests/migration/test_front_io.py`**

  ```python
  """Tests for migration/front_io.py."""

  from __future__ import annotations

  import math
  import tempfile
  from pathlib import Path

  import pandas as pd
  import pytest

  from quantipy_polarity.contracts import FrontResult
  from quantipy_polarity.migration.front_io import read_front_parquet, write_front_parquet


  def _make_results() -> list[FrontResult]:
      return [
          FrontResult(fov_id="FOV_01", front_y_um=45.5, front_angle_deg=87.3,
                      n_front_px=320, front_mask_shape=(128, 128), pixel_size_um=0.65),
          FrontResult(fov_id="FOV_02", front_y_um=None, front_angle_deg=None,
                      n_front_px=0, front_mask_shape=(128, 128), pixel_size_um=0.65),
      ]


  def test_write_creates_parquet_file() -> None:
      with tempfile.TemporaryDirectory() as td:
          out = Path(td) / "front_um_per_fov.parquet"
          write_front_parquet(_make_results(), out)
          assert out.exists()
          assert out.stat().st_size > 0


  def test_roundtrip_preserves_values() -> None:
      with tempfile.TemporaryDirectory() as td:
          out = Path(td) / "front.parquet"
          write_front_parquet(_make_results(), out)
          df = read_front_parquet(out)
          assert list(df["fov_id"]) == ["FOV_01", "FOV_02"]
          assert abs(df.loc[0, "front_y_um"] - 45.5) < 1e-6
          assert df.loc[1, "n_front_px"] == 0
          assert pd.isna(df.loc[1, "front_y_um"])


  def test_write_is_atomic_no_partial_file_on_error() -> None:
      """write_front_parquet cleans up temp file if serialisation fails."""
      import unittest.mock as mock
      with tempfile.TemporaryDirectory() as td:
          out = Path(td) / "front.parquet"
          with mock.patch("pandas.DataFrame.to_parquet", side_effect=RuntimeError("disk full")):
              with pytest.raises(RuntimeError, match="disk full"):
                  write_front_parquet(_make_results(), out)
          # Output file must not exist after failed write
          assert not out.exists()
          # No leftover temp file
          assert len(list(Path(td).glob(".front_tmp_*"))) == 0


  def test_read_validates_required_columns() -> None:
      with tempfile.TemporaryDirectory() as td:
          bad = Path(td) / "bad.parquet"
          pd.DataFrame({"fov_id": ["FOV_01"]}).to_parquet(bad, index=False)
          with pytest.raises(ValueError, match="missing columns"):
              read_front_parquet(bad)


  def test_empty_results_writes_zero_row_parquet() -> None:
      with tempfile.TemporaryDirectory() as td:
          out = Path(td) / "empty.parquet"
          write_front_parquet([], out)
          df = read_front_parquet(out)
          assert len(df) == 0
  ```

- [ ] **Step 3: Run tests**

  ```bash
  pytest tests/migration/test_front_io.py -v 2>&1 | tail -10
  ```

  Expected: 5 tests pass.

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/migration/front_io.py tests/migration/test_front_io.py
  git commit -m "feat(migration): implement write/read front_um_per_fov.parquet with atomic writes"
  ```

---

## Task 4: Implement `migration/distance.py` + tests

**Files:** Create `src/quantipy_polarity/migration/distance.py`; create `tests/migration/test_distance.py`

Per-cell distance to front (pixels → microns) and `mig_alignment` (magnitude-weighted alignment score lifted from `compute_48h_local_migration.py:align_wt`). Takes `per_cell` DataFrame + `FrontResult` + the raw `(vx, vy, front_mask)` tuple; returns DataFrame with three new columns populated.

- [ ] **Step 1: Create `src/quantipy_polarity/migration/distance.py`**

  ```python
  """Per-cell distance-to-front and migration alignment.

  Lifted from:
  - recompute_migration_v3.py: per-cell angle/distance pattern
  - compute_48h_local_migration.py:align_wt(): magnitude-weighted alignment
  """

  from __future__ import annotations

  import numpy as np
  import pandas as pd

  from quantipy_polarity.contracts import FrontResult


  def _axial_diff_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
      """Unsigned axial difference in [0, 90] degrees.

      Both inputs are axial angles (mod 180). Returns the minimum angular
      distance between them treating each angle as a headless line.
      """
      a = np.asarray(a, dtype=float)
      b = np.asarray(b, dtype=float)
      d = np.mod(a - b, 180.0)
      return np.where(d > 90.0, 180.0 - d, d)


  def compute_per_cell_migration(
      per_cell_df: pd.DataFrame,
      labels: np.ndarray,
      vx: np.ndarray,
      vy: np.ndarray,
      front_result: FrontResult,
  ) -> pd.DataFrame:
      """Add mig_dir_deg, dist_to_front_um, mig_alignment to per_cell_df rows.

      Operates on a single-FOV slice of per_cell_df (all rows must share the
      same fov_id matching front_result.fov_id).

      Parameters
      ----------
      per_cell_df : DataFrame with columns cell_id, axis_deg, magnitude.
          Must be a single-FOV slice (fov_id column must equal front_result.fov_id).
      labels : (H, W) label mask matching the FOV.
      vx, vy : (H, W) float32 displacement fields from _compute_migration_field_v6.
      front_result : FrontResult for this FOV (provides pixel_size_um).

      Returns
      -------
      Copy of per_cell_df with three columns updated:
          mig_dir_deg : angle toward front (degrees, [0, 360))
          dist_to_front_um : Euclidean distance to front (microns)
          mig_alignment : magnitude-weighted cos(2Δθ) alignment in [-1, +1]
              where Δθ = axial difference between polarity and migration direction.
      """
      df = per_cell_df.copy()
      px = front_result.pixel_size_um

      mig_dir = np.full(len(df), np.nan, dtype=float)
      dist_um = np.full(len(df), np.nan, dtype=float)

      n_front = front_result.n_front_px

      for i, row in df.iterrows():
          cid = int(row["cell_id"])
          mask = labels == cid
          if not mask.any() or n_front == 0:
              continue
          mean_vx = float(vx[mask].mean())
          mean_vy = float(vy[mask].mean())
          dist_px = float(np.hypot(mean_vx, mean_vy))
          dist_um[df.index.get_loc(i)] = dist_px * px
          # angle: +x = 0°, +y_image-up = +90° (image y-axis flipped)
          mig_dir[df.index.get_loc(i)] = float(
              np.degrees(np.arctan2(-mean_vy, mean_vx)) % 360.0
          )

      df["mig_dir_deg"] = mig_dir
      df["dist_to_front_um"] = dist_um

      # Alignment: magnitude-weighted cos(2Δθ) where Δθ is axial diff
      valid = (
          np.isfinite(mig_dir)
          & np.isfinite(df["axis_deg"].to_numpy())
          & np.isfinite(df["magnitude"].to_numpy())
      )
      if valid.sum() > 0:
          pol_deg = df["axis_deg"].to_numpy()[valid]
          mig_deg = mig_dir[valid]
          mags = df["magnitude"].to_numpy()[valid]
          # Axial: treat polarity as mod-180, migration as mod-360 → diff mod 180
          rel = _axial_diff_deg(pol_deg, mig_deg % 180.0)
          rel_rad = np.deg2rad(rel)
          # align_wt = sum(|p| * cos(2*rel)) / sum(|p|) lifted from align_wt()
          alignment = float(np.sum(mags * np.cos(2 * rel_rad)) / np.sum(mags))
      else:
          alignment = float("nan")

      df["mig_alignment"] = alignment  # scalar broadcast — same value per FOV
      return df


  def compute_all_fovs(
      per_cell_df: pd.DataFrame,
      labels_by_fov: dict[str, np.ndarray],
      fields_by_fov: dict[str, tuple[np.ndarray, np.ndarray]],
      results_by_fov: dict[str, FrontResult],
  ) -> pd.DataFrame:
      """Run compute_per_cell_migration for each FOV and concatenate.

      Parameters
      ----------
      per_cell_df : full experiment-wide per_cell DataFrame.
      labels_by_fov : mapping fov_id -> (H, W) label mask.
      fields_by_fov : mapping fov_id -> (vx, vy) displacement arrays.
      results_by_fov : mapping fov_id -> FrontResult.

      Returns
      -------
      Full per_cell DataFrame with migration columns populated where possible.
      """
      chunks = []
      for fov_id, grp in per_cell_df.groupby("fov_id"):
          fov_id = str(fov_id)
          if fov_id not in results_by_fov:
              chunks.append(grp)
              continue
          vx, vy = fields_by_fov[fov_id]
          labels = labels_by_fov[fov_id]
          result = results_by_fov[fov_id]
          chunks.append(
              compute_per_cell_migration(grp, labels, vx, vy, result)
          )
      if not chunks:
          return per_cell_df.copy()
      return pd.concat(chunks, ignore_index=True)
  ```

- [ ] **Step 2: Create `tests/migration/test_distance.py`**

  ```python
  """Tests for migration/distance.py."""

  from __future__ import annotations

  import numpy as np
  import pandas as pd
  import pytest

  from quantipy_polarity.contracts import FrontResult
  from quantipy_polarity.migration.distance import (
      _axial_diff_deg,
      compute_per_cell_migration,
      compute_all_fovs,
  )


  def _synthetic_df(n: int = 5, fov_id: str = "FOV_01") -> pd.DataFrame:
      rng = np.random.default_rng(42)
      return pd.DataFrame({
          "fov_id": fov_id,
          "cell_id": list(range(1, n + 1)),
          "axis_deg": rng.uniform(0, 180, n).tolist(),
          "magnitude": rng.uniform(0.1, 1.0, n).tolist(),
          "centroid_y": rng.uniform(10, 50, n).tolist(),
          "centroid_x": rng.uniform(10, 50, n).tolist(),
          "area_px": [200] * n,
          "qc_flags": [0] * n,
      })


  def _tiny_labels(n: int = 5, size: int = 64) -> np.ndarray:
      labels = np.zeros((size, size), dtype=np.uint16)
      step = size // (n + 1)
      for cid in range(1, n + 1):
          cy, cx = step * cid, step * cid
          labels[cy - 4:cy + 4, cx - 4:cx + 4] = cid
      return labels


  def test_axial_diff_deg_same_angle_is_zero() -> None:
      a = np.array([45.0, 90.0, 135.0])
      assert np.allclose(_axial_diff_deg(a, a), 0.0)


  def test_axial_diff_deg_orthogonal_is_90() -> None:
      assert abs(_axial_diff_deg(np.array([0.0]), np.array([90.0]))[0] - 90.0) < 1e-9


  def test_axial_diff_deg_antiparallel_is_zero() -> None:
      # 0° and 180° are the same axial direction
      assert abs(_axial_diff_deg(np.array([0.0]), np.array([180.0]))[0]) < 1e-9


  def test_compute_per_cell_migration_adds_columns() -> None:
      size = 64
      labels = _tiny_labels(5, size)
      vx = np.ones((size, size), np.float32) * 5.0
      vy = np.zeros((size, size), np.float32)
      result = FrontResult(fov_id="FOV_01", front_y_um=20.0, front_angle_deg=0.0,
                           n_front_px=100, front_mask_shape=(size, size), pixel_size_um=0.65)
      df = _synthetic_df(5)
      out = compute_per_cell_migration(df, labels, vx, vy, result)
      assert "mig_dir_deg" in out.columns
      assert "dist_to_front_um" in out.columns
      assert "mig_alignment" in out.columns


  def test_compute_per_cell_migration_no_front_gives_nans() -> None:
      size = 64
      labels = _tiny_labels(5, size)
      vx = np.zeros((size, size), np.float32)
      vy = np.zeros((size, size), np.float32)
      result = FrontResult(fov_id="FOV_01", front_y_um=None, front_angle_deg=None,
                           n_front_px=0, front_mask_shape=(size, size), pixel_size_um=0.65)
      df = _synthetic_df(5)
      out = compute_per_cell_migration(df, labels, vx, vy, result)
      assert out["dist_to_front_um"].isna().all()


  def test_compute_all_fovs_concatenates_correctly() -> None:
      size = 64
      labels = _tiny_labels(5, size)
      vx = np.ones((size, size), np.float32)
      vy = np.zeros((size, size), np.float32)
      r = FrontResult(fov_id="FOV_01", front_y_um=20.0, front_angle_deg=0.0,
                      n_front_px=50, front_mask_shape=(size, size), pixel_size_um=0.65)
      df1 = _synthetic_df(5, "FOV_01")
      df2 = _synthetic_df(3, "FOV_02")
      full = pd.concat([df1, df2], ignore_index=True)
      out = compute_all_fovs(
          full,
          labels_by_fov={"FOV_01": labels},
          fields_by_fov={"FOV_01": (vx, vy)},
          results_by_fov={"FOV_01": r},
      )
      assert len(out) == 8
      # FOV_02 rows have no FrontResult → pass through unchanged
      fov2 = out[out["fov_id"] == "FOV_02"]
      assert fov2["dist_to_front_um"].isna().all()
  ```

- [ ] **Step 3: Run tests**

  ```bash
  pytest tests/migration/ -v 2>&1 | tail -15
  ```

  Expected: all 17 migration tests pass.

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/migration/distance.py tests/migration/test_distance.py
  git commit -m "feat(migration): implement per-cell dist-to-front + mig_alignment computation"
  ```

---

## Task 5: Implement `viz/_style.py` + `viz/__init__.py`

**Files:** Create `src/quantipy_polarity/viz/_style.py`; modify `src/quantipy_polarity/viz/__init__.py`

Self-contained style module. Tries `Science/styles/figstyle.py` via path insertion; falls back to a local baked-in copy of the relevant rcParams + PALETTE if that file is not found. The public repo must work without the Science monorepo.

- [ ] **Step 1: Create `src/quantipy_polarity/viz/_style.py`**

  ```python
  """Nature-style matplotlib configuration for QuantiPy Polarity figures.

  Tries to import from ``Science/styles/figstyle.py`` (lab monorepo, developer
  machines). Falls back to a self-contained copy of the relevant settings so the
  public repo works without any external path.

  Public API
  ----------
  apply_nature_style()     Apply lab rcParams.
  PALETTE                  CB-safe colour dict.
  save_figure(fig, stem)   Save PNG (600 DPI) + PDF (fonttype=42) atomically.
  """

  from __future__ import annotations

  import os
  import tempfile
  from pathlib import Path
  from typing import Any

  import matplotlib
  matplotlib.use("Agg")  # non-interactive; caller can override before importing
  import matplotlib.pyplot as plt


  # ── Attempt to import the canonical lab figstyle ─────────────────────────────
  _FIGSTYLE_IMPORTED = False
  _MONOREPO_STYLES = Path(__file__).resolve().parents[6] / "styles" / "figstyle.py"

  if _MONOREPO_STYLES.exists():
      import importlib.util as _ilu
      _spec = _ilu.spec_from_file_location("_lab_figstyle", _MONOREPO_STYLES)
      if _spec and _spec.loader:
          _lab = _ilu.module_from_spec(_spec)
          try:
              _spec.loader.exec_module(_lab)  # type: ignore[union-attr]
              _FIGSTYLE_IMPORTED = True
          except Exception:
              pass


  # ── Palette (identical to Science/styles/figstyle.py PALETTE) ─────────────────
  PALETTE: dict[str, str] = {
      "phase1":     "#5B8FD6",
      "phase2":     "#E28E2C",
      "phase3":     "#7BAA5B",
      "phase4":     "#C45AD6",
      "failure":    "#D24B40",
      "composite":  "#272727",
      "neutral_bg": "#F2E6D9",
      "cat5":       "#E69F00",
      "cat6":       "#56B4E9",
      "cat7":       "#5DA88F",
  }

  # Semantic aliases used by Phase 4 figures
  COLOR_POLARITY = PALETTE["phase1"]   # arrows coloured by magnitude default
  COLOR_FRONT    = PALETTE["phase2"]   # front overlay line
  COLOR_CELL     = PALETTE["composite"]  # cell outlines
  COLOR_FAILURE  = PALETTE["failure"]


  # ── rcParams (baked-in fallback, matches Science/styles/figstyle.py) ──────────
  _RCPARAMS: dict[str, Any] = {
      "font.family":       "Arial",
      "font.size":          7,
      "axes.titlesize":     8,
      "axes.titleweight":   "bold",
      "axes.labelsize":     7,
      "xtick.labelsize":    6,
      "ytick.labelsize":    6,
      "axes.linewidth":     0.5,
      "xtick.major.width":  0.5,
      "ytick.major.width":  0.5,
      "lines.linewidth":    0.8,
      "patch.linewidth":    0.5,
      "legend.fontsize":    6,
      "legend.frameon":     False,
      "pdf.fonttype":       42,
      "svg.fonttype":       "none",
      "axes.spines.top":    False,
      "axes.spines.right":  False,
  }


  def apply_nature_style() -> None:
      """Apply lab Nature-style rcParams to the current matplotlib session."""
      if _FIGSTYLE_IMPORTED and hasattr(_lab, "apply_nature_style"):
          _lab.apply_nature_style()
      else:
          plt.rcParams.update(_RCPARAMS)


  def save_figure(fig: plt.Figure, stem: str | Path, dpi: int = 600) -> list[Path]:
      """Save figure as PNG (raster, 600 DPI) and PDF (vector, fonttype=42).

      Uses atomic write (temp file + os.replace) for both outputs.
      Avoids combining constrained_layout with bbox_inches="tight".

      Parameters
      ----------
      fig : matplotlib Figure.
      stem : path stem without extension (e.g. ``results/06_plots/rose_FOV_01``).
      dpi : raster DPI (default 600 per lab standard).

      Returns
      -------
      List of Path objects for the written files: [<stem>.png, <stem>.pdf].
      """
      stem = Path(stem)
      stem.parent.mkdir(parents=True, exist_ok=True)
      written: list[Path] = []
      for ext, kwargs in [
          (".png", {"dpi": dpi, "bbox_inches": "tight"}),
          (".pdf", {"dpi": dpi}),
      ]:
          out = stem.with_suffix(ext)
          fd, tmp = tempfile.mkstemp(dir=stem.parent, prefix=".fig_tmp_", suffix=ext)
          os.close(fd)
          try:
              fig.savefig(tmp, **kwargs)
              os.replace(tmp, out)
              written.append(out)
          except Exception:
              try:
                  os.unlink(tmp)
              except OSError:
                  pass
              raise
      return written
  ```

- [ ] **Step 2: Replace content of `src/quantipy_polarity/viz/__init__.py`**

  ```python
  """Polarity maps, rose plots, overlays, summary figures. Phase 4."""

  from quantipy_polarity.viz._style import PALETTE, apply_nature_style, save_figure

  __all__ = ["apply_nature_style", "PALETTE", "save_figure"]
  ```

- [ ] **Step 3: Verify import**

  ```bash
  python -c "from quantipy_polarity.viz import apply_nature_style, PALETTE, save_figure; apply_nature_style(); print('viz style OK, palette keys:', list(PALETTE)[:3])"
  ```

  Expected: prints `viz style OK, palette keys: ['phase1', 'phase2', 'phase3']`

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/viz/_style.py src/quantipy_polarity/viz/__init__.py
  git commit -m "feat(viz): add _style.py with Nature rcParams + PALETTE + atomic save_figure"
  ```

---

## Task 6: Tests for `viz/_style.py`

**Files:** Create `tests/viz/__init__.py`; create `tests/viz/test_style.py`

- [ ] **Step 1: Create `tests/viz/__init__.py`** (empty)

  ```bash
  touch tests/viz/__init__.py
  ```

- [ ] **Step 2: Create `tests/viz/test_style.py`**

  ```python
  """Tests for viz/_style.py."""

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt


  def test_apply_nature_style_sets_rcparams() -> None:
      from quantipy_polarity.viz._style import apply_nature_style
      apply_nature_style()
      import matplotlib as mpl
      assert mpl.rcParams["pdf.fonttype"] == 42
      assert mpl.rcParams["svg.fonttype"] == "none"
      assert mpl.rcParams["axes.linewidth"] == 0.5


  def test_palette_has_required_keys() -> None:
      from quantipy_polarity.viz._style import PALETTE
      required = {"phase1", "phase2", "phase3", "phase4", "failure", "composite", "neutral_bg"}
      assert required.issubset(PALETTE.keys())
      # All values are valid hex colours
      for k, v in PALETTE.items():
          assert v.startswith("#") and len(v) == 7, f"bad hex colour for {k}: {v}"


  def test_save_figure_writes_png_and_pdf() -> None:
      from quantipy_polarity.viz._style import save_figure, apply_nature_style
      apply_nature_style()
      fig, ax = plt.subplots(figsize=(2, 2))
      ax.plot([0, 1], [0, 1])
      with tempfile.TemporaryDirectory() as td:
          written = save_figure(fig, Path(td) / "test_fig")
          paths = {p.suffix: p for p in written}
          assert ".png" in paths
          assert ".pdf" in paths
          assert paths[".png"].exists()
          assert paths[".pdf"].exists()
          # PNG starts with PNG header
          assert paths[".png"].read_bytes()[:4] == b"\x89PNG"
          # PDF starts with PDF header
          assert paths[".pdf"].read_bytes()[:4] == b"%PDF"
      plt.close(fig)


  def test_save_figure_creates_parent_dirs() -> None:
      from quantipy_polarity.viz._style import save_figure
      fig, ax = plt.subplots(figsize=(1, 1))
      ax.plot([0], [0])
      with tempfile.TemporaryDirectory() as td:
          stem = Path(td) / "nested" / "subdir" / "fig"
          save_figure(fig, stem)
          assert (stem.parent).is_dir()
      plt.close(fig)
  ```

- [ ] **Step 3: Run style tests**

  ```bash
  pytest tests/viz/test_style.py -v 2>&1 | tail -10
  ```

  Expected: 4 tests pass.

- [ ] **Step 4: Commit**

  ```bash
  git add tests/viz/__init__.py tests/viz/test_style.py
  git commit -m "test(viz): add style module tests — rcParams, palette, save_figure file headers"
  ```

---

## Task 7: Implement `viz/vector_map.py`

**Files:** Create `src/quantipy_polarity/viz/vector_map.py`

Per-FOV polarity vector map: cell outlines + axial arrows coloured by polarity magnitude.

- [ ] **Step 1: Create `src/quantipy_polarity/viz/vector_map.py`**

  ```python
  """Per-FOV polarity vector map.

  Renders cell outlines on the membrane channel image with an axial arrow
  per cell coloured by polarity magnitude.

  Lifted from:
  - pipeline/plot_fov_polarity_panel.py: cell-outline + axis-line drawing
  - pipeline/debug_polarity.py:draw_axial_line(): angle/length convention
  """

  from __future__ import annotations

  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import matplotlib.colors as mcolors
  import numpy as np
  import pandas as pd
  from skimage.segmentation import find_boundaries

  from quantipy_polarity.viz._style import apply_nature_style, save_figure, PALETTE


  def _draw_axial_line(
      ax: plt.Axes,
      cx: float,
      cy: float,
      angle_deg: float,
      length: float,
      color: object,
      lw: float = 0.8,
  ) -> None:
      """Draw an axial line through (cx, cy) on ax.

      Angle 0° = horizontal (+x). Image y-axis points down so -sin converts
      screen-down pixel coords to math-frame-up angle convention.
      """
      th = np.radians(angle_deg)
      dx = np.cos(th) * length / 2.0
      dy = -np.sin(th) * length / 2.0
      ax.plot([cx - dx, cx + dx], [cy - dy, cy + dy],
              "-", color=color, lw=lw, solid_capstyle="round")


  def plot_vector_map(
      membrane: np.ndarray,
      labels: np.ndarray,
      fov_df: pd.DataFrame,
      *,
      pixel_size_um: float = 1.0,
      vector_scale: float = 1.0,
      cmap: str = "viridis",
      figsize: tuple[float, float] = (4.0, 4.0),
      title: str | None = None,
  ) -> plt.Figure:
      """Generate a per-FOV polarity vector map figure.

      Parameters
      ----------
      membrane : (H, W) float or uint16 membrane channel image.
      labels : (H, W) uint16 label mask.
      fov_df : DataFrame with columns cell_id, centroid_y, centroid_x,
               axis_deg, magnitude (single FOV).
      pixel_size_um : microns per pixel (used to scale arrow length).
      vector_scale : multiplicative scale applied to arrow length.
      cmap : matplotlib colourmap for magnitude colouring.
      figsize : figure size in inches.
      title : optional axis title.

      Returns
      -------
      matplotlib Figure (caller closes it after saving).
      """
      apply_nature_style()
      fig, ax = plt.subplots(1, 1, figsize=figsize, constrained_layout=True)

      mem = membrane.astype(float)
      vmin, vmax = np.percentile(mem[mem > 0], [2, 98]) if mem.max() > 0 else (0, 1)
      ax.imshow(mem, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")

      # Cell outlines
      outline = find_boundaries(labels, mode="outer")
      ax.contour(outline, levels=[0.5], colors=[PALETTE["composite"]],
                 linewidths=0.4, alpha=0.6)

      # Arrows coloured by magnitude
      if len(fov_df) > 0:
          mags = fov_df["magnitude"].to_numpy(dtype=float)
          norm = mcolors.Normalize(vmin=0, vmax=max(mags.max(), 1e-9))
          cmap_obj = plt.get_cmap(cmap)
          for _, row in fov_df.iterrows():
              cid = int(row["cell_id"])
              cy = float(row["centroid_y"])
              cx = float(row["centroid_x"])
              ang = float(row["axis_deg"])
              mag = float(row["magnitude"])
              # Arrow length: magnitude * scale * ~10 px reference
              length = mag * vector_scale * 10.0
              color = cmap_obj(norm(mag))
              _draw_axial_line(ax, cx, cy, ang, length, color=color, lw=1.0)

          sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
          sm.set_array([])
          cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
          cbar.set_label("Polarity magnitude", fontsize=6)
          cbar.ax.tick_params(labelsize=5)

      ax.set_axis_off()
      if title:
          ax.set_title(title, fontsize=8, fontweight="bold")

      return fig


  def save_vector_map(
      membrane: np.ndarray,
      labels: np.ndarray,
      fov_df: pd.DataFrame,
      stem: Path,
      **kwargs: object,
  ) -> list[Path]:
      """Convenience wrapper: plot and save, return written paths."""
      fig = plot_vector_map(membrane, labels, fov_df, **kwargs)
      paths = save_figure(fig, stem)
      plt.close(fig)
      return paths
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity.viz.vector_map import plot_vector_map; print('vector_map OK')"
  ```

  Expected: `vector_map OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/viz/vector_map.py
  git commit -m "feat(viz): implement per-FOV polarity vector map (cell outlines + magnitude-coloured arrows)"
  ```

---

## Task 8: Tests for `viz/vector_map.py`

**Files:** Create `tests/viz/test_vector_map.py`

- [ ] **Step 1: Create `tests/viz/test_vector_map.py`**

  ```python
  """Tests for viz/vector_map.py.

  Tests verify file creation and valid PNG/PDF headers; NOT pixel content.
  """

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import numpy as np
  import pandas as pd
  import pytest

  from tests.fixtures._build import build_synthetic_fov


  def _make_fov_df(data: dict, fov_id: str = "FOV_01") -> pd.DataFrame:
      labels = data["label_mask"]
      theta = data["theta_truth"]
      centroids = data["centroids"]
      rows = []
      for cid, ang in theta.items():
          if cid not in centroids:
              continue
          cy, cx = centroids[cid]
          rows.append({
              "fov_id": fov_id, "cell_id": cid,
              "centroid_y": cy, "centroid_x": cx,
              "axis_deg": ang, "magnitude": float(np.random.default_rng(cid).uniform(0.2, 0.9)),
          })
      return pd.DataFrame(rows)


  def test_save_vector_map_writes_png_and_pdf() -> None:
      from quantipy_polarity.viz.vector_map import save_vector_map
      data = build_synthetic_fov(n_cells=10, image_size=64, seed=1)
      df = _make_fov_df(data)
      with tempfile.TemporaryDirectory() as td:
          paths = save_vector_map(
              data["membrane"], data["label_mask"], df,
              Path(td) / "vec_map",
              pixel_size_um=0.65, title="Test FOV",
          )
          assert len(paths) == 2
          for p in paths:
              assert p.exists()
              assert p.stat().st_size > 0
          # Check headers
          pngs = [p for p in paths if p.suffix == ".png"]
          pdfs = [p for p in paths if p.suffix == ".pdf"]
          assert pngs[0].read_bytes()[:4] == b"\x89PNG"
          assert pdfs[0].read_bytes()[:4] == b"%PDF"


  def test_vector_map_empty_df_does_not_crash() -> None:
      from quantipy_polarity.viz.vector_map import plot_vector_map
      import matplotlib.pyplot as plt
      data = build_synthetic_fov(n_cells=5, image_size=32, seed=2)
      empty_df = pd.DataFrame(columns=["cell_id", "centroid_y", "centroid_x", "axis_deg", "magnitude"])
      fig = plot_vector_map(data["membrane"], data["label_mask"], empty_df)
      assert fig is not None
      plt.close(fig)


  def test_vector_map_returns_figure_object() -> None:
      from quantipy_polarity.viz.vector_map import plot_vector_map
      import matplotlib.pyplot as plt
      data = build_synthetic_fov(n_cells=8, image_size=64, seed=3)
      df = _make_fov_df(data)
      fig = plot_vector_map(data["membrane"], data["label_mask"], df)
      assert hasattr(fig, "savefig")
      plt.close(fig)
  ```

- [ ] **Step 2: Run tests**

  ```bash
  pytest tests/viz/test_vector_map.py -v 2>&1 | tail -8
  ```

  Expected: 3 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/viz/test_vector_map.py
  git commit -m "test(viz): add vector_map tests — file existence + PNG/PDF header checks"
  ```

---

## Task 9: Implement `viz/rose_plot.py`

**Files:** Create `src/quantipy_polarity/viz/rose_plot.py`

Half-disk rose plot (axial, 0–180°). Convention lifted verbatim from `plot_rose_pair_halfdisk.py`: `rel_mod180 = ((axis_deg) % 180 + 180) % 180`. Supports optional grouping by condition (one rose per condition, same axes for comparison). Returns a matplotlib Figure.

- [ ] **Step 1: Create `src/quantipy_polarity/viz/rose_plot.py`**

  ```python
  """Half-disk rose plot for axial polarity directions.

  Convention (lifted from plot_rose_pair_halfdisk.py in the research repo):
      angles plotted as ((axis_deg % 180) + 180) % 180  — all in [0, 180).
      0° / 180° = polarity PARALLEL to image horizontal.
      90° = polarity PERPENDICULAR to image horizontal (typical migration direction).

  Each cell appears once on the upper semicircle.
  """

  from __future__ import annotations

  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd

  from quantipy_polarity.viz._style import apply_nature_style, save_figure, PALETTE


  def _axial_mod180(angles_deg: np.ndarray) -> np.ndarray:
      a = np.asarray(angles_deg, dtype=float)
      return ((a % 180.0) + 180.0) % 180.0


  def plot_rose(
      angles_deg: np.ndarray,
      *,
      n_bins: int = 24,
      half_disk: bool = True,
      title: str | None = None,
      color: str | None = None,
      figsize: tuple[float, float] = (2.5, 2.5),
      ax: plt.Axes | None = None,
  ) -> tuple[plt.Figure, plt.Axes]:
      """Plot a single half-disk (or full) rose histogram of axial angles.

      Parameters
      ----------
      angles_deg : 1-D array of polarity axis angles in degrees.
      n_bins : number of histogram bins (default 24 → 7.5° per bin for half-disk).
      half_disk : if True plot [0, 180); if False plot [0, 360).
      title : optional axis title.
      color : bar colour; defaults to PALETTE['phase1'].
      figsize : figure size in inches.
      ax : existing polar Axes to draw into; if None a new figure is created.

      Returns
      -------
      (fig, ax) tuple.
      """
      apply_nature_style()
      if ax is None:
          fig, ax = plt.subplots(
              subplot_kw={"projection": "polar"},
              figsize=figsize,
              constrained_layout=True,
          )
      else:
          fig = ax.get_figure()

      if color is None:
          color = PALETTE["phase1"]

      a = _axial_mod180(angles_deg[np.isfinite(angles_deg)])
      if half_disk:
          span = np.pi  # 0 to π
          bins = np.linspace(0, span, n_bins + 1)
          counts, _ = np.histogram(np.deg2rad(a), bins=bins)
          theta = (bins[:-1] + bins[1:]) / 2.0
          width = span / n_bins
          ax.set_thetamin(0)
          ax.set_thetamax(180)
      else:
          span = 2 * np.pi
          bins = np.linspace(0, span, n_bins + 1)
          counts, _ = np.histogram(np.deg2rad(a) % span, bins=bins)
          theta = (bins[:-1] + bins[1:]) / 2.0
          width = span / n_bins

      ax.bar(theta, counts, width=width, color=color, alpha=0.8,
             edgecolor="white", linewidth=0.3, align="center")
      ax.set_theta_zero_location("E")
      ax.set_theta_direction(1)
      ax.tick_params(labelsize=5)
      ax.set_rlabel_position(90)
      ax.yaxis.set_tick_params(labelsize=4)
      ax.spines["polar"].set_linewidth(0.4)

      if title:
          ax.set_title(title, fontsize=7, fontweight="bold", pad=4)

      return fig, ax


  def plot_rose_grouped(
      df: pd.DataFrame,
      *,
      condition_col: str = "condition",
      angle_col: str = "axis_deg",
      n_bins: int = 24,
      half_disk: bool = True,
      figsize_per_panel: tuple[float, float] = (2.5, 2.5),
  ) -> plt.Figure:
      """Plot one rose per condition group in a row of subplots.

      Parameters
      ----------
      df : DataFrame with at least `angle_col` and optionally `condition_col`.
      condition_col : column used to split groups; if absent or all-None,
          treats entire df as one group.
      angle_col : column containing polarity angles in degrees.
      n_bins, half_disk : forwarded to plot_rose.
      figsize_per_panel : size of each individual panel.

      Returns
      -------
      matplotlib Figure.
      """
      apply_nature_style()
      conditions = (
          sorted(df[condition_col].dropna().unique())
          if condition_col in df.columns and df[condition_col].notna().any()
          else ["all"]
      )
      n = len(conditions)
      fig, axes = plt.subplots(
          1, n,
          subplot_kw={"projection": "polar"},
          figsize=(figsize_per_panel[0] * n, figsize_per_panel[1]),
          constrained_layout=True,
      )
      if n == 1:
          axes = [axes]

      palette_vals = list(PALETTE.values())
      for i, (cond, ax) in enumerate(zip(conditions, axes)):
          if cond == "all":
              angles = df[angle_col].to_numpy(dtype=float)
          else:
              angles = df[df[condition_col] == cond][angle_col].to_numpy(dtype=float)
          color = palette_vals[i % len(palette_vals)]
          plot_rose(angles, n_bins=n_bins, half_disk=half_disk,
                    title=str(cond), color=color, ax=ax)

      return fig


  def save_rose(
      angles_deg: np.ndarray,
      stem: Path,
      **kwargs: object,
  ) -> list[Path]:
      """Plot single-group rose and save; return written paths."""
      fig, _ax = plot_rose(angles_deg, **kwargs)
      paths = save_figure(fig, stem)
      plt.close(fig)
      return paths
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity.viz.rose_plot import plot_rose, plot_rose_grouped; print('rose_plot OK')"
  ```

  Expected: `rose_plot OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/viz/rose_plot.py
  git commit -m "feat(viz): implement half-disk rose plot with optional condition grouping"
  ```

---

## Task 10: Tests for `viz/rose_plot.py`

**Files:** Create `tests/viz/test_rose_plot.py`

- [ ] **Step 1: Create `tests/viz/test_rose_plot.py`**

  ```python
  """Tests for viz/rose_plot.py."""

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd


  def test_plot_rose_returns_figure_and_axes() -> None:
      from quantipy_polarity.viz.rose_plot import plot_rose
      rng = np.random.default_rng(0)
      angles = rng.uniform(0, 180, 50)
      fig, ax = plot_rose(angles, n_bins=12)
      assert hasattr(fig, "savefig")
      assert ax is not None
      plt.close(fig)


  def test_plot_rose_handles_empty_angles() -> None:
      from quantipy_polarity.viz.rose_plot import plot_rose
      fig, ax = plot_rose(np.array([]), n_bins=12)
      assert fig is not None
      plt.close(fig)


  def test_plot_rose_full_disk() -> None:
      from quantipy_polarity.viz.rose_plot import plot_rose
      rng = np.random.default_rng(1)
      angles = rng.uniform(0, 360, 40)
      fig, ax = plot_rose(angles, half_disk=False, n_bins=24)
      assert fig is not None
      plt.close(fig)


  def test_save_rose_writes_png_and_pdf() -> None:
      from quantipy_polarity.viz.rose_plot import save_rose
      rng = np.random.default_rng(2)
      angles = rng.uniform(0, 180, 60)
      with tempfile.TemporaryDirectory() as td:
          paths = save_rose(angles, Path(td) / "rose_test", n_bins=12)
          assert len(paths) == 2
          for p in paths:
              assert p.exists()
          pngs = [p for p in paths if p.suffix == ".png"]
          pdfs = [p for p in paths if p.suffix == ".pdf"]
          assert pngs[0].read_bytes()[:4] == b"\x89PNG"
          assert pdfs[0].read_bytes()[:4] == b"%PDF"


  def test_plot_rose_grouped_single_condition() -> None:
      from quantipy_polarity.viz.rose_plot import plot_rose_grouped
      rng = np.random.default_rng(3)
      df = pd.DataFrame({"axis_deg": rng.uniform(0, 180, 40), "condition": "A"})
      fig = plot_rose_grouped(df)
      assert fig is not None
      plt.close(fig)


  def test_plot_rose_grouped_two_conditions() -> None:
      from quantipy_polarity.viz.rose_plot import plot_rose_grouped
      rng = np.random.default_rng(4)
      df = pd.DataFrame({
          "axis_deg": rng.uniform(0, 180, 80),
          "condition": ["A"] * 40 + ["B"] * 40,
      })
      fig = plot_rose_grouped(df)
      assert fig is not None
      plt.close(fig)


  def test_plot_rose_grouped_no_condition_col() -> None:
      from quantipy_polarity.viz.rose_plot import plot_rose_grouped
      rng = np.random.default_rng(5)
      df = pd.DataFrame({"axis_deg": rng.uniform(0, 180, 30)})
      fig = plot_rose_grouped(df)
      assert fig is not None
      plt.close(fig)
  ```

- [ ] **Step 2: Run tests**

  ```bash
  pytest tests/viz/test_rose_plot.py -v 2>&1 | tail -10
  ```

  Expected: 7 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/viz/test_rose_plot.py
  git commit -m "test(viz): add rose_plot tests — figure objects + file header checks"
  ```

---

## Task 11: Implement `viz/front_overlay.py`

**Files:** Create `src/quantipy_polarity/viz/front_overlay.py`

Per-FOV overlay: membrane image + cell outlines + front ribbon + per-cell migration arrows. PNG output (no PDF required for QC overlays).

- [ ] **Step 1: Create `src/quantipy_polarity/viz/front_overlay.py`**

  ```python
  """Per-FOV migration-front overlay figure.

  Renders membrane channel image with:
  - Cell outlines (thin, semi-transparent)
  - Front ribbon (dilated front_mask pixels, coloured phase2/orange)
  - Per-cell migration direction arrows (green arrows toward front)

  Lifted from pipeline/debug_polarity.py display conventions:
  - Yellow → phase2 orange (lab palette)
  - Green arrows for migration direction
  """

  from __future__ import annotations

  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd
  from scipy import ndimage as ndi
  from skimage.segmentation import find_boundaries

  from quantipy_polarity.viz._style import apply_nature_style, PALETTE


  def plot_front_overlay(
      membrane: np.ndarray,
      labels: np.ndarray,
      front_mask: np.ndarray,
      fov_df: pd.DataFrame | None = None,
      *,
      vx: np.ndarray | None = None,
      vy: np.ndarray | None = None,
      pixel_size_um: float = 1.0,
      arrow_scale: float = 15.0,
      figsize: tuple[float, float] = (4.0, 4.0),
      title: str | None = None,
  ) -> plt.Figure:
      """Render a migration-front overlay figure.

      Parameters
      ----------
      membrane : (H, W) uint16 or float membrane image.
      labels : (H, W) uint16 label mask.
      front_mask : (H, W) bool front-pixel mask from detect_front.
      fov_df : optional DataFrame with cell_id, centroid_y, centroid_x columns
               for placing arrow origins.
      vx, vy : (H, W) displacement fields. If provided AND fov_df is provided,
               arrows drawn at cell centroids pointing along mean (vx, vy).
      pixel_size_um : microns per pixel (unused in px-space drawing; for label).
      arrow_scale : arrow length scaling factor.
      figsize : figure size in inches.
      title : optional title.

      Returns
      -------
      matplotlib Figure.
      """
      apply_nature_style()
      fig, ax = plt.subplots(1, 1, figsize=figsize, constrained_layout=True)

      mem = membrane.astype(float)
      vmin, vmax = np.percentile(mem[mem > 0], [2, 98]) if mem.max() > 0 else (0, 1)
      ax.imshow(mem, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")

      # Cell outlines
      outline = find_boundaries(labels, mode="outer")
      ax.contour(outline, levels=[0.5], colors=[PALETTE["composite"]],
                 linewidths=0.3, alpha=0.5)

      # Front ribbon: dilate front_mask by 2 px for visibility
      if front_mask.any():
          ribbon = ndi.binary_dilation(front_mask, iterations=2)
          rgba = np.zeros((*membrane.shape, 4), dtype=float)
          # Orange front colour
          r, g, b = tuple(
              int(PALETTE["phase2"][i: i + 2], 16) / 255.0
              for i in (1, 3, 5)
          )
          rgba[ribbon, 0] = r
          rgba[ribbon, 1] = g
          rgba[ribbon, 2] = b
          rgba[ribbon, 3] = 0.7
          ax.imshow(rgba, interpolation="nearest")

      # Per-cell migration arrows
      if fov_df is not None and vx is not None and vy is not None and len(fov_df) > 0:
          for _, row in fov_df.iterrows():
              cid = int(row["cell_id"])
              cy = float(row["centroid_y"])
              cx = float(row["centroid_x"])
              cell_mask = labels == cid
              if not cell_mask.any():
                  continue
              mean_vx = float(vx[cell_mask].mean())
              mean_vy = float(vy[cell_mask].mean())
              length = float(np.hypot(mean_vx, mean_vy))
              if length < 1e-6:
                  continue
              scale = arrow_scale / max(length, 1.0)
              ax.annotate(
                  "",
                  xy=(cx + mean_vx * scale, cy + mean_vy * scale),
                  xytext=(cx, cy),
                  arrowprops=dict(
                      arrowstyle="->",
                      color=PALETTE["phase3"],  # green
                      lw=0.6,
                  ),
              )

      ax.set_axis_off()
      if title:
          ax.set_title(title, fontsize=8, fontweight="bold")

      return fig


  def save_front_overlay(
      membrane: np.ndarray,
      labels: np.ndarray,
      front_mask: np.ndarray,
      stem: Path,
      **kwargs: object,
  ) -> Path:
      """Save front overlay as PNG only (QC overlay; raster sufficient).

      Returns path to the written PNG.
      """
      import os, tempfile
      fig = plot_front_overlay(membrane, labels, front_mask, **kwargs)
      out = Path(stem).with_suffix(".png")
      out.parent.mkdir(parents=True, exist_ok=True)
      fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=".overlay_tmp_", suffix=".png")
      os.close(fd)
      try:
          fig.savefig(tmp, dpi=600, bbox_inches="tight")
          os.replace(tmp, out)
      except Exception:
          try:
              os.unlink(tmp)
          except OSError:
              pass
          raise
      finally:
          plt.close(fig)
      return out
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity.viz.front_overlay import plot_front_overlay; print('front_overlay OK')"
  ```

  Expected: `front_overlay OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/viz/front_overlay.py
  git commit -m "feat(viz): implement front_overlay — membrane + cell outlines + front ribbon + migration arrows"
  ```

---

## Task 12: Tests for `viz/front_overlay.py`

**Files:** Create `tests/viz/test_front_overlay.py`

- [ ] **Step 1: Create `tests/viz/test_front_overlay.py`**

  ```python
  """Tests for viz/front_overlay.py."""

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd

  from tests.fixtures._build import build_synthetic_fov


  def _make_front_mask(size: int = 64) -> np.ndarray:
      mask = np.zeros((size, size), bool)
      mask[size // 2, 5 : size - 5] = True
      return mask


  def test_plot_front_overlay_returns_figure() -> None:
      from quantipy_polarity.viz.front_overlay import plot_front_overlay
      data = build_synthetic_fov(n_cells=5, image_size=64, seed=10)
      front = _make_front_mask(64)
      fig = plot_front_overlay(data["membrane"], data["label_mask"], front)
      assert hasattr(fig, "savefig")
      plt.close(fig)


  def test_plot_front_overlay_no_front() -> None:
      from quantipy_polarity.viz.front_overlay import plot_front_overlay
      data = build_synthetic_fov(n_cells=5, image_size=64, seed=11)
      empty_front = np.zeros((64, 64), bool)
      fig = plot_front_overlay(data["membrane"], data["label_mask"], empty_front)
      assert fig is not None
      plt.close(fig)


  def test_save_front_overlay_writes_png() -> None:
      from quantipy_polarity.viz.front_overlay import save_front_overlay
      data = build_synthetic_fov(n_cells=5, image_size=64, seed=12)
      front = _make_front_mask(64)
      with tempfile.TemporaryDirectory() as td:
          out = save_front_overlay(
              data["membrane"], data["label_mask"], front,
              Path(td) / "overlay_test"
          )
          assert out.exists()
          assert out.suffix == ".png"
          assert out.read_bytes()[:4] == b"\x89PNG"


  def test_plot_front_overlay_with_migration_arrows() -> None:
      from quantipy_polarity.viz.front_overlay import plot_front_overlay
      data = build_synthetic_fov(n_cells=5, image_size=64, seed=13)
      front = _make_front_mask(64)
      size = 64
      vx = np.ones((size, size), np.float32) * 3.0
      vy = np.zeros((size, size), np.float32)
      centroids = data["centroids"]
      fov_df = pd.DataFrame([
          {"cell_id": cid, "centroid_y": cy, "centroid_x": cx}
          for cid, (cy, cx) in list(centroids.items())[:3]
      ])
      fig = plot_front_overlay(
          data["membrane"], data["label_mask"], front,
          fov_df=fov_df, vx=vx, vy=vy,
      )
      assert fig is not None
      plt.close(fig)
  ```

- [ ] **Step 2: Run tests**

  ```bash
  pytest tests/viz/test_front_overlay.py -v 2>&1 | tail -8
  ```

  Expected: 4 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/viz/test_front_overlay.py
  git commit -m "test(viz): add front_overlay tests — figure objects + PNG header check"
  ```

---

## Task 13: Implement `viz/summary.py`

**Files:** Create `src/quantipy_polarity/viz/summary.py`

Population summary panel: 4-panel figure showing (A) polarity magnitude distribution, (B) polarity axis rose (all cells), (C) dist_to_front_um distribution (if available), (D) per-FOV cell count bar chart.

- [ ] **Step 1: Create `src/quantipy_polarity/viz/summary.py`**

  ```python
  """Population summary figure for across-experiment polarity data.

  Four-panel figure:
  A. Polarity magnitude distribution (histogram)
  B. Aggregate half-disk rose (all cells)
  C. Distance-to-front distribution (if dist_to_front_um populated)
  D. Per-FOV cell count bar chart
  """

  from __future__ import annotations

  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd

  from quantipy_polarity.viz._style import apply_nature_style, save_figure, PALETTE
  from quantipy_polarity.viz.rose_plot import plot_rose


  def plot_population_summary(
      per_cell: pd.DataFrame,
      *,
      n_rose_bins: int = 24,
      figsize: tuple[float, float] = (7.0, 3.5),
      suptitle: str | None = None,
  ) -> plt.Figure:
      """Generate a 4-panel population summary figure.

      Parameters
      ----------
      per_cell : experiment-wide per_cell DataFrame. Required columns:
          fov_id, magnitude, axis_deg.
          Optional: dist_to_front_um (panel C is greyed if absent/all-NaN).
      n_rose_bins : bins for the aggregate rose.
      figsize : total figure size.
      suptitle : optional super-title.

      Returns
      -------
      matplotlib Figure.
      """
      apply_nature_style()

      fig = plt.figure(figsize=figsize, constrained_layout=True)
      gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1])
      ax_mag = fig.add_subplot(gs[0])
      ax_rose = fig.add_subplot(gs[1], projection="polar")
      ax_dist = fig.add_subplot(gs[2])
      ax_count = fig.add_subplot(gs[3])

      # A. Magnitude distribution
      mags = per_cell["magnitude"].dropna().to_numpy(dtype=float)
      if len(mags) > 0:
          ax_mag.hist(mags, bins=30, color=PALETTE["phase1"], edgecolor="white",
                     linewidth=0.3, alpha=0.85)
      ax_mag.set_xlabel("Polarity magnitude", fontsize=7)
      ax_mag.set_ylabel("Cells", fontsize=7)
      ax_mag.set_title("A  Magnitude", fontsize=8, fontweight="bold", loc="left")

      # B. Aggregate rose
      angles = per_cell["axis_deg"].dropna().to_numpy(dtype=float)
      plot_rose(angles, n_bins=n_rose_bins, half_disk=True,
                color=PALETTE["phase1"], ax=ax_rose)
      ax_rose.set_title("B  Polarity axes", fontsize=8, fontweight="bold", pad=4)

      # C. Distance to front
      if "dist_to_front_um" in per_cell.columns:
          dists = per_cell["dist_to_front_um"].dropna().to_numpy(dtype=float)
      else:
          dists = np.array([])
      if len(dists) > 0:
          ax_dist.hist(dists, bins=30, color=PALETTE["phase2"], edgecolor="white",
                      linewidth=0.3, alpha=0.85)
          ax_dist.set_xlabel("Dist to front (µm)", fontsize=7)
      else:
          ax_dist.text(0.5, 0.5, "No front data", ha="center", va="center",
                      transform=ax_dist.transAxes, fontsize=7, color="gray")
          ax_dist.set_axis_off()
      ax_dist.set_title("C  Dist to front", fontsize=8, fontweight="bold", loc="left")

      # D. Per-FOV cell count
      counts = per_cell.groupby("fov_id").size().sort_index()
      if len(counts) > 0:
          fov_labels = [str(f) for f in counts.index]
          ax_count.bar(range(len(counts)), counts.values, color=PALETTE["phase3"],
                      edgecolor="white", linewidth=0.3)
          ax_count.set_xticks(range(len(counts)))
          ax_count.set_xticklabels(fov_labels, rotation=45, ha="right", fontsize=5)
          ax_count.set_ylabel("Cells", fontsize=7)
      ax_count.set_title("D  Cells per FOV", fontsize=8, fontweight="bold", loc="left")

      if suptitle:
          fig.suptitle(suptitle, fontsize=9, fontweight="bold")

      return fig


  def save_population_summary(
      per_cell: pd.DataFrame,
      stem: Path,
      **kwargs: object,
  ) -> list[Path]:
      """Generate and save the population summary; return written paths."""
      fig = plot_population_summary(per_cell, **kwargs)
      paths = save_figure(fig, stem)
      plt.close(fig)
      return paths
  ```

- [ ] **Step 2: Verify import**

  ```bash
  python -c "from quantipy_polarity.viz.summary import plot_population_summary; print('summary OK')"
  ```

  Expected: `summary OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/quantipy_polarity/viz/summary.py
  git commit -m "feat(viz): implement 4-panel population summary figure"
  ```

---

## Task 14: Tests for `viz/summary.py`

**Files:** Create `tests/viz/test_summary.py`

- [ ] **Step 1: Create `tests/viz/test_summary.py`**

  ```python
  """Tests for viz/summary.py."""

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd


  def _make_per_cell(n: int = 60) -> pd.DataFrame:
      rng = np.random.default_rng(99)
      return pd.DataFrame({
          "fov_id": [f"FOV_{i % 3 + 1:02d}" for i in range(n)],
          "cell_id": list(range(1, n + 1)),
          "axis_deg": rng.uniform(0, 180, n),
          "magnitude": rng.uniform(0.1, 1.0, n),
          "dist_to_front_um": rng.uniform(0, 100, n),
      })


  def test_plot_population_summary_returns_figure() -> None:
      from quantipy_polarity.viz.summary import plot_population_summary
      df = _make_per_cell(40)
      fig = plot_population_summary(df)
      assert hasattr(fig, "savefig")
      plt.close(fig)


  def test_plot_population_summary_no_dist_col() -> None:
      from quantipy_polarity.viz.summary import plot_population_summary
      df = _make_per_cell(20).drop(columns=["dist_to_front_um"])
      fig = plot_population_summary(df)
      assert fig is not None
      plt.close(fig)


  def test_plot_population_summary_all_dist_nan() -> None:
      from quantipy_polarity.viz.summary import plot_population_summary
      df = _make_per_cell(20)
      df["dist_to_front_um"] = np.nan
      fig = plot_population_summary(df)
      assert fig is not None
      plt.close(fig)


  def test_save_population_summary_writes_png_and_pdf() -> None:
      from quantipy_polarity.viz.summary import save_population_summary
      df = _make_per_cell(30)
      with tempfile.TemporaryDirectory() as td:
          paths = save_population_summary(df, Path(td) / "summary_test")
          assert len(paths) == 2
          for p in paths:
              assert p.exists()
          pngs = [p for p in paths if p.suffix == ".png"]
          pdfs = [p for p in paths if p.suffix == ".pdf"]
          assert pngs[0].read_bytes()[:4] == b"\x89PNG"
          assert pdfs[0].read_bytes()[:4] == b"%PDF"
  ```

- [ ] **Step 2: Run tests**

  ```bash
  pytest tests/viz/test_summary.py -v 2>&1 | tail -8
  ```

  Expected: 4 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/viz/test_summary.py
  git commit -m "test(viz): add summary figure tests — figure objects + PNG/PDF headers"
  ```

---

## Task 15: Implement `_cli_front.py` — real `quantipy front` command

**Files:** Create `src/quantipy_polarity/_cli_front.py`

Real implementation of `quantipy front`. Reads config, loads label masks from `02_segmentation/`, runs `detect_front` on each FOV, writes `front_um_per_fov.parquet`, writes per-FOV QC overlay PNGs, then calls `compute_per_cell_migration` to update `per_cell.parquet` columns.

- [ ] **Step 1: Create `src/quantipy_polarity/_cli_front.py`**

  ```python
  """Real implementation of `quantipy front`.

  Detects the migration front from label masks, writes front_um_per_fov.parquet,
  writes per-FOV QC overlay PNGs, and populates mig_dir_deg / dist_to_front_um /
  mig_alignment in per_cell.parquet.
  """

  from __future__ import annotations

  import sys
  from pathlib import Path

  import click
  import numpy as np
  import pandas as pd
  import structlog
  import tifffile

  from quantipy_polarity.cli import main
  from quantipy_polarity.config import load_config
  from quantipy_polarity.migration.front_detect import (
      _compute_migration_field_v6,
      detect_front,
  )
  from quantipy_polarity.migration.front_io import write_front_parquet, read_front_parquet
  from quantipy_polarity.migration.distance import compute_per_cell_migration

  log = structlog.get_logger()


  @main.command("front", short_help="[Advanced] Migration-front detection (auto only in v0.1.0)")
  @click.option("--config", "config_path", required=True, type=click.Path(exists=True),
                help="Path to quantipy YAML config.")
  @click.option("--input", "input_dir", required=True, type=click.Path(exists=True),
                help="Directory containing 02_segmentation/ label masks.")
  @click.option("--output", "output_dir", required=True, type=click.Path(),
                help="Results directory; 04_migration/ written here.")
  @click.option("--qc", is_flag=True, default=False,
                help="Write per-FOV QC overlay PNGs into 04_migration/qc/.")
  @click.option("--resume", is_flag=True, default=False,
                help="Skip FOVs already in front_um_per_fov.parquet.")
  def front_cmd(
      config_path: str,
      input_dir: str,
      output_dir: str,
      qc: bool,
      resume: bool,
  ) -> None:
      """Detect migration front from label masks (automated v6 algorithm).

      Writes:
          <output>/04_migration/front_um_per_fov.parquet
          <output>/04_migration/qc/<fov_id>_front_overlay.png  (if --qc)
          Updates dist_to_front_um, mig_dir_deg, mig_alignment in
          <output>/05_aggregated/per_cell.parquet (if that file exists).
      """
      cfg = load_config(Path(config_path))
      input_path = Path(input_dir)
      output_path = Path(output_dir)

      seg_dir = input_path / "02_segmentation"
      if not seg_dir.exists():
          # Fallback: input_dir itself may already be 02_segmentation
          seg_dir = input_path

      mask_files = sorted(seg_dir.glob("*_mask.tif"))
      if not mask_files:
          raise click.ClickException(
              f"No *_mask.tif files found in {seg_dir}. "
              "Run `quantipy segment` first or check --input path."
          )

      mig_dir = output_path / "04_migration"
      mig_dir.mkdir(parents=True, exist_ok=True)
      front_parquet = mig_dir / "front_um_per_fov.parquet"

      # Load existing parquet for resume
      already_done: set[str] = set()
      if resume and front_parquet.exists():
          existing = read_front_parquet(front_parquet)
          already_done = set(existing["fov_id"].tolist())
          log.info("resume: skipping FOVs already in parquet", n=len(already_done))

      pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)

      from quantipy_polarity.contracts import FrontResult
      results: list[FrontResult] = []
      vx_by_fov: dict[str, np.ndarray] = {}
      vy_by_fov: dict[str, np.ndarray] = {}
      labels_by_fov: dict[str, np.ndarray] = {}

      for mask_file in mask_files:
          fov_id = mask_file.stem.replace("_mask", "")
          if fov_id in already_done:
              log.info("skipping (resume)", fov_id=fov_id)
              continue
          log.info("detecting front", fov_id=fov_id)
          labels = tifffile.imread(str(mask_file)).astype(np.int32)
          if labels.ndim != 2:
              log.warning("label mask is not 2-D, skipping", fov_id=fov_id, shape=labels.shape)
              continue

          result = detect_front(labels, pixel_size_um=pixel_size_um, fov_id=fov_id)
          results.append(result)

          vx, vy, _front_mask = _compute_migration_field_v6(labels)
          vx_by_fov[fov_id] = vx
          vy_by_fov[fov_id] = vy
          labels_by_fov[fov_id] = labels

          if qc:
              _write_qc_overlay(
                  mask_file, labels, _front_mask, mig_dir / "qc", fov_id
              )

      if results:
          write_front_parquet(results, front_parquet)
          log.info("wrote front parquet", path=str(front_parquet), n_fovs=len(results))

      # Update per_cell.parquet if it exists
      per_cell_path = output_path / "05_aggregated" / "per_cell.parquet"
      if per_cell_path.exists() and results:
          _update_per_cell(
              per_cell_path, labels_by_fov, vx_by_fov, vy_by_fov,
              {r.fov_id: r for r in results}
          )


  def _write_qc_overlay(
      mask_file: Path,
      labels: np.ndarray,
      front_mask: np.ndarray,
      qc_dir: Path,
      fov_id: str,
  ) -> None:
      """Write a front QC overlay PNG next to the mask file."""
      from quantipy_polarity.viz.front_overlay import save_front_overlay
      qc_dir.mkdir(parents=True, exist_ok=True)
      # Membrane TIF is expected as <fov_id>_membrane.tif sibling
      mem_path = mask_file.parent / f"{fov_id}_membrane.tif"
      if mem_path.exists():
          membrane = tifffile.imread(str(mem_path)).astype(np.float32)
          if membrane.ndim == 3:
              membrane = membrane[..., 0]
      else:
          membrane = (labels > 0).astype(np.float32)

      save_front_overlay(
          membrane, labels, front_mask,
          qc_dir / f"{fov_id}_front_overlay",
          title=fov_id,
      )
      log.info("wrote QC overlay", fov_id=fov_id)


  def _update_per_cell(
      per_cell_path: Path,
      labels_by_fov: dict[str, np.ndarray],
      vx_by_fov: dict[str, np.ndarray],
      vy_by_fov: dict[str, np.ndarray],
      results_by_fov: dict,
  ) -> None:
      """Update migration columns in per_cell.parquet in-place (atomic)."""
      from quantipy_polarity.migration.distance import compute_all_fovs
      import os, tempfile

      df = pd.read_parquet(per_cell_path)
      updated = compute_all_fovs(
          df, labels_by_fov,
          {fov: (vx_by_fov[fov], vy_by_fov[fov]) for fov in vx_by_fov},
          results_by_fov,
      )
      fd, tmp = tempfile.mkstemp(
          dir=per_cell_path.parent, prefix=".per_cell_tmp_", suffix=".parquet"
      )
      os.close(fd)
      try:
          updated.to_parquet(tmp, index=False)
          os.replace(tmp, per_cell_path)
          log.info("updated per_cell.parquet with migration columns",
                   path=str(per_cell_path), n_rows=len(updated))
      except Exception:
          try:
              os.unlink(tmp)
          except OSError:
              pass
          raise
  ```

- [ ] **Step 2: Register in `cli.py`**

  Open `src/quantipy_polarity/cli.py`. After the `_cli_segment` import line, add:

  ```python
  from quantipy_polarity import _cli_front as _cli_front  # noqa: E402,F401
  ```

- [ ] **Step 3: Verify help text is real (no stub message)**

  ```bash
  python -m quantipy_polarity.cli front --help 2>&1 | head -5
  ```

  Expected: shows real help with `--config`, `--input`, `--output` options. No "Phase 4 stub" text.

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/_cli_front.py src/quantipy_polarity/cli.py
  git commit -m "feat(cli): implement real quantipy front command (v6 front detection + QC overlays)"
  ```

---

## Task 16: Tests for `_cli_front.py`

**Files:** Create `tests/cli/test_cli_front.py`

All tests use synthetic data; no real microscopy. `_compute_migration_field_v6` is called via the CLI on synthetic label masks.

- [ ] **Step 1: Create `tests/cli/test_cli_front.py`**

  ```python
  """Tests for the `quantipy front` CLI command."""

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import numpy as np
  import pandas as pd
  import pytest
  import tifffile
  from click.testing import CliRunner

  from quantipy_polarity.cli import main
  from tests.fixtures._build import build_synthetic_fov


  def _write_seg_dir(tmp: Path, n_fovs: int = 2, size: int = 64) -> Path:
      """Write synthetic mask TIFs into a 02_segmentation/ layout."""
      seg = tmp / "02_segmentation"
      seg.mkdir(parents=True)
      for i in range(1, n_fovs + 1):
          fov_id = f"FOV_{i:02d}"
          data = build_synthetic_fov(n_cells=10, image_size=size, seed=i * 7)
          tifffile.imwrite(str(seg / f"{fov_id}_mask.tif"), data["label_mask"])
          mem_u16 = (data["membrane"] * 65535).clip(0, 65535).astype(np.uint16)
          tifffile.imwrite(str(seg / f"{fov_id}_membrane.tif"), mem_u16)
      return seg


  def _write_config(tmp: Path) -> Path:
      cfg_text = (
          "project:\n  name: test\n  output_dir: ./results\n"
          "input:\n  mode: masks\n  path: ./input\n"
          "  masks_dir: ./input\n  pixel_size_um: 0.65\n"
          "  membrane_channel: 0\n"
          "polarity:\n  method: boundary_pca\n  axial: true\n"
          "  weight: magnitude\n  exclude_edge_cells: false\n"
      )
      cfg = tmp / "config.yaml"
      cfg.write_text(cfg_text)
      return cfg


  def test_front_writes_parquet() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          _write_seg_dir(tmp, n_fovs=2, size=64)
          cfg = _write_config(tmp)
          out = tmp / "results"
          result = runner.invoke(main, [
              "front",
              "--config", str(cfg),
              "--input", str(tmp),
              "--output", str(out),
          ])
          assert result.exit_code == 0, result.output
          parquet = out / "04_migration" / "front_um_per_fov.parquet"
          assert parquet.exists()
          df = pd.read_parquet(parquet)
          assert set(df["fov_id"]) == {"FOV_01", "FOV_02"}
          assert "front_y_um" in df.columns
          assert "n_front_px" in df.columns


  def test_front_qc_flag_writes_overlay_pngs() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          _write_seg_dir(tmp, n_fovs=1, size=64)
          cfg = _write_config(tmp)
          out = tmp / "results"
          result = runner.invoke(main, [
              "front", "--config", str(cfg),
              "--input", str(tmp), "--output", str(out), "--qc",
          ])
          assert result.exit_code == 0, result.output
          qc_dir = out / "04_migration" / "qc"
          pngs = list(qc_dir.glob("*.png"))
          assert len(pngs) >= 1
          assert pngs[0].read_bytes()[:4] == b"\x89PNG"


  def test_front_updates_per_cell_when_present() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          _write_seg_dir(tmp, n_fovs=1, size=64)
          cfg = _write_config(tmp)
          out = tmp / "results"
          # Pre-write a per_cell.parquet with NaN migration columns
          agg_dir = out / "05_aggregated"
          agg_dir.mkdir(parents=True)
          data = build_synthetic_fov(n_cells=10, image_size=64, seed=7)
          pc = pd.DataFrame({
              "fov_id": "FOV_01",
              "cell_id": list(range(1, 11)),
              "axis_deg": [float(v) for v in data["theta_truth"].values()],
              "magnitude": [0.5] * 10,
              "centroid_y": [float(v[0]) for v in data["centroids"].values()],
              "centroid_x": [float(v[1]) for v in data["centroids"].values()],
              "area_px": [200] * 10,
              "qc_flags": [0] * 10,
              "dist_to_front_um": [float("nan")] * 10,
              "mig_dir_deg": [float("nan")] * 10,
              "mig_alignment": [float("nan")] * 10,
          })
          pc.to_parquet(agg_dir / "per_cell.parquet", index=False)
          result = runner.invoke(main, [
              "front", "--config", str(cfg),
              "--input", str(tmp), "--output", str(out),
          ])
          assert result.exit_code == 0, result.output
          updated = pd.read_parquet(agg_dir / "per_cell.parquet")
          assert "dist_to_front_um" in updated.columns
          assert "mig_dir_deg" in updated.columns


  def test_front_no_mask_files_raises_error() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          cfg = _write_config(tmp)
          empty_in = tmp / "empty_seg"
          empty_in.mkdir()
          out = tmp / "results"
          result = runner.invoke(main, [
              "front", "--config", str(cfg),
              "--input", str(empty_in), "--output", str(out),
          ])
          assert result.exit_code != 0
  ```

- [ ] **Step 2: Run tests**

  ```bash
  pytest tests/cli/test_cli_front.py -v 2>&1 | tail -10
  ```

  Expected: 4 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/cli/test_cli_front.py
  git commit -m "test(cli): add quantipy front CLI tests — parquet output, QC PNGs, per_cell update"
  ```

---

## Task 17: Implement `_cli_figures.py` — real `quantipy plot` command

**Files:** Create `src/quantipy_polarity/_cli_figures.py`

Real implementation of `quantipy plot`. Reads `per_cell.parquet` and optional front parquet; emits per-FOV vector maps + rose plots + front overlays + population summary into `06_plots/`.

- [ ] **Step 1: Create `src/quantipy_polarity/_cli_figures.py`**

  ```python
  """Real implementation of `quantipy plot`.

  Generates polarity vector maps, rose plots, front overlays, and a
  population summary panel from a completed pipeline output directory.
  """

  from __future__ import annotations

  from pathlib import Path

  import click
  import numpy as np
  import pandas as pd
  import structlog
  import tifffile

  from quantipy_polarity.cli import main
  from quantipy_polarity.config import load_config

  log = structlog.get_logger()


  @main.command("plot", short_help="[Advanced] Regenerate plots from aggregated parquet")
  @click.option("--config", "config_path", required=True, type=click.Path(exists=True),
                help="Path to quantipy YAML config.")
  @click.option("--output", "output_dir", required=True, type=click.Path(exists=True),
                help="Results directory containing 05_aggregated/per_cell.parquet.")
  @click.option("--per-fov-maps", is_flag=True, default=True, show_default=True,
                help="Generate per-FOV polarity vector maps.")
  @click.option("--rose", is_flag=True, default=True, show_default=True,
                help="Generate per-FOV and aggregate rose plots.")
  @click.option("--summary", is_flag=True, default=True, show_default=True,
                help="Generate population summary panel.")
  @click.option("--front-overlays", is_flag=True, default=True, show_default=True,
                help="Generate front overlay PNGs (requires 04_migration/).")
  def figures_cmd(
      config_path: str,
      output_dir: str,
      per_fov_maps: bool,
      rose: bool,
      summary: bool,
      front_overlays: bool,
  ) -> None:
      """Regenerate plots from an existing pipeline output directory.

      Reads per_cell.parquet from <output>/05_aggregated/.
      Writes all figures into <output>/06_plots/.
      Does NOT re-run any pipeline stages.
      """
      cfg = load_config(Path(config_path))
      out = Path(output_dir)
      plots_dir = out / "06_plots"
      plots_dir.mkdir(parents=True, exist_ok=True)

      per_cell_path = out / "05_aggregated" / "per_cell.parquet"
      if not per_cell_path.exists():
          raise click.ClickException(
              f"per_cell.parquet not found at {per_cell_path}. "
              "Run `quantipy polarity` and `quantipy aggregate` first."
          )
      per_cell = pd.read_parquet(per_cell_path)
      log.info("loaded per_cell", n_cells=len(per_cell), n_fovs=per_cell["fov_id"].nunique())

      pixel_size_um: float = getattr(cfg.input, "pixel_size_um", 0.65)

      # Load front parquet if available
      front_parquet = out / "04_migration" / "front_um_per_fov.parquet"
      front_df: pd.DataFrame | None = None
      if front_parquet.exists():
          from quantipy_polarity.migration.front_io import read_front_parquet
          front_df = read_front_parquet(front_parquet)
          log.info("loaded front parquet", n_fovs=len(front_df))

      seg_dir = out / "02_segmentation"

      if per_fov_maps:
          _generate_vector_maps(per_cell, seg_dir, plots_dir, pixel_size_um,
                                getattr(cfg, "viz", None))

      if rose:
          _generate_rose_plots(per_cell, plots_dir,
                               getattr(cfg, "viz", None))

      if front_overlays and front_df is not None:
          _generate_front_overlays(per_cell, seg_dir, front_df, plots_dir, pixel_size_um)

      if summary:
          _generate_summary(per_cell, plots_dir)

      log.info("figures complete", plots_dir=str(plots_dir))


  def _generate_vector_maps(
      per_cell: pd.DataFrame,
      seg_dir: Path,
      plots_dir: Path,
      pixel_size_um: float,
      viz_cfg: object,
  ) -> None:
      from quantipy_polarity.viz.vector_map import save_vector_map
      vec_dir = plots_dir / "vector_maps"
      vec_dir.mkdir(parents=True, exist_ok=True)
      vector_scale = float(getattr(viz_cfg, "vector_scale", 1.0)) if viz_cfg else 1.0

      for fov_id, fov_df in per_cell.groupby("fov_id"):
          fov_id = str(fov_id)
          mask_path = seg_dir / f"{fov_id}_mask.tif"
          mem_path = seg_dir / f"{fov_id}_membrane.tif"
          if not mask_path.exists():
              log.warning("mask not found for FOV, skipping vector map", fov_id=fov_id)
              continue
          labels = tifffile.imread(str(mask_path)).astype(np.uint16)
          membrane = (
              tifffile.imread(str(mem_path)).astype(np.float32)
              if mem_path.exists()
              else (labels > 0).astype(np.float32)
          )
          if membrane.ndim == 3:
              membrane = membrane[..., 0]
          save_vector_map(
              membrane, labels, fov_df,
              vec_dir / fov_id,
              pixel_size_um=pixel_size_um,
              vector_scale=vector_scale,
              title=fov_id,
          )
          log.info("wrote vector map", fov_id=fov_id)


  def _generate_rose_plots(
      per_cell: pd.DataFrame,
      plots_dir: Path,
      viz_cfg: object,
  ) -> None:
      from quantipy_polarity.viz.rose_plot import save_rose, plot_rose_grouped
      from quantipy_polarity.viz._style import save_figure
      import matplotlib.pyplot as plt
      rose_dir = plots_dir / "roses"
      rose_dir.mkdir(parents=True, exist_ok=True)
      n_bins = int(getattr(viz_cfg, "rose_bins", 24)) if viz_cfg else 24

      # Per-FOV roses
      for fov_id, fov_df in per_cell.groupby("fov_id"):
          fov_id = str(fov_id)
          angles = fov_df["axis_deg"].dropna().to_numpy(dtype=float)
          save_rose(angles, rose_dir / f"rose_{fov_id}", n_bins=n_bins, title=fov_id)
          log.info("wrote rose", fov_id=fov_id)

      # Aggregate rose (all conditions grouped)
      fig = plot_rose_grouped(per_cell, angle_col="axis_deg", n_bins=n_bins)
      save_figure(fig, plots_dir / "rose_aggregate")
      plt.close(fig)
      log.info("wrote aggregate rose")


  def _generate_front_overlays(
      per_cell: pd.DataFrame,
      seg_dir: Path,
      front_df: pd.DataFrame,
      plots_dir: Path,
      pixel_size_um: float,
  ) -> None:
      from quantipy_polarity.viz.front_overlay import save_front_overlay
      from quantipy_polarity.migration.front_detect import _compute_migration_field_v6
      overlay_dir = plots_dir / "front_overlays"
      overlay_dir.mkdir(parents=True, exist_ok=True)

      for _, front_row in front_df.iterrows():
          fov_id = str(front_row["fov_id"])
          mask_path = seg_dir / f"{fov_id}_mask.tif"
          if not mask_path.exists():
              continue
          labels = tifffile.imread(str(mask_path)).astype(np.int32)
          mem_path = seg_dir / f"{fov_id}_membrane.tif"
          membrane = (
              tifffile.imread(str(mem_path)).astype(np.float32)
              if mem_path.exists()
              else (labels > 0).astype(np.float32)
          )
          if membrane.ndim == 3:
              membrane = membrane[..., 0]
          _vx, _vy, front_mask = _compute_migration_field_v6(labels)
          fov_df = per_cell[per_cell["fov_id"] == fov_id] if len(per_cell) else None
          save_front_overlay(
              membrane, labels, front_mask,
              overlay_dir / f"{fov_id}_front",
              fov_df=fov_df if (fov_df is not None and len(fov_df) > 0) else None,
              vx=_vx, vy=_vy, title=fov_id,
          )
          log.info("wrote front overlay", fov_id=fov_id)


  def _generate_summary(per_cell: pd.DataFrame, plots_dir: Path) -> None:
      from quantipy_polarity.viz.summary import save_population_summary
      n_fovs = per_cell["fov_id"].nunique()
      n_cells = len(per_cell)
      save_population_summary(
          per_cell,
          plots_dir / "population_summary",
          suptitle=f"Population summary — {n_fovs} FOVs, {n_cells} cells",
      )
      log.info("wrote population summary")
  ```

- [ ] **Step 2: Register in `cli.py`**

  Open `src/quantipy_polarity/cli.py`. After the `_cli_front` import line, add:

  ```python
  from quantipy_polarity import _cli_figures as _cli_figures  # noqa: E402,F401
  ```

- [ ] **Step 3: Verify help text is real**

  ```bash
  python -m quantipy_polarity.cli plot --help 2>&1 | head -5
  ```

  Expected: shows real help with `--output`, `--config` options. No "Phase 4 stub" text.

- [ ] **Step 4: Commit**

  ```bash
  git add src/quantipy_polarity/_cli_figures.py src/quantipy_polarity/cli.py
  git commit -m "feat(cli): implement real quantipy plot command — vector maps, roses, overlays, summary"
  ```

---

## Task 18: Tests for `_cli_figures.py`

**Files:** Create `tests/cli/test_cli_figures.py`

- [ ] **Step 1: Create `tests/cli/test_cli_figures.py`**

  ```python
  """Tests for the `quantipy plot` CLI command."""

  from __future__ import annotations

  import tempfile
  from pathlib import Path

  import numpy as np
  import pandas as pd
  import pytest
  import tifffile
  from click.testing import CliRunner

  from quantipy_polarity.cli import main
  from tests.fixtures._build import build_synthetic_fov


  def _write_pipeline_outputs(tmp: Path, n_fovs: int = 2, size: int = 64) -> dict:
      """Write a minimal completed-pipeline layout for quantipy plot tests."""
      seg_dir = tmp / "02_segmentation"
      seg_dir.mkdir(parents=True)
      agg_dir = tmp / "05_aggregated"
      agg_dir.mkdir(parents=True)

      rows = []
      for i in range(1, n_fovs + 1):
          fov_id = f"FOV_{i:02d}"
          data = build_synthetic_fov(n_cells=8, image_size=size, seed=i * 13)
          tifffile.imwrite(str(seg_dir / f"{fov_id}_mask.tif"), data["label_mask"])
          mem_u16 = (data["membrane"] * 65535).clip(0, 65535).astype(np.uint16)
          tifffile.imwrite(str(seg_dir / f"{fov_id}_membrane.tif"), mem_u16)
          for cid, ang in data["theta_truth"].items():
              if cid not in data["centroids"]:
                  continue
              cy, cx = data["centroids"][cid]
              rows.append({
                  "fov_id": fov_id, "cell_id": cid,
                  "centroid_y": cy, "centroid_x": cx,
                  "axis_deg": ang,
                  "magnitude": float(np.random.default_rng(cid + i).uniform(0.2, 0.9)),
                  "area_px": 200, "qc_flags": 0,
                  "dist_to_front_um": float("nan"),
                  "mig_dir_deg": float("nan"),
                  "mig_alignment": float("nan"),
              })
      df = pd.DataFrame(rows)
      df.to_parquet(agg_dir / "per_cell.parquet", index=False)
      return {"seg_dir": seg_dir, "agg_dir": agg_dir, "per_cell": df}


  def _write_config(tmp: Path) -> Path:
      cfg_text = (
          "project:\n  name: test\n  output_dir: ./results\n"
          "input:\n  mode: masks\n  path: ./input\n"
          "  masks_dir: ./input\n  pixel_size_um: 0.65\n"
          "  membrane_channel: 0\n"
          "polarity:\n  method: boundary_pca\n  axial: true\n"
          "  weight: magnitude\n  exclude_edge_cells: false\n"
          "viz:\n  rose_bins: 12\n  vector_scale: 1.0\n"
          "  per_fov_maps: true\n  overlay_dpi: 150\n"
      )
      cfg = tmp / "config.yaml"
      cfg.write_text(cfg_text)
      return cfg


  def test_plot_writes_summary_pdf() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          _write_pipeline_outputs(tmp, n_fovs=2, size=64)
          cfg = _write_config(tmp)
          result = runner.invoke(main, [
              "plot", "--config", str(cfg), "--output", str(tmp),
          ])
          assert result.exit_code == 0, result.output
          summary_pdf = tmp / "06_plots" / "population_summary.pdf"
          assert summary_pdf.exists()
          assert summary_pdf.read_bytes()[:4] == b"%PDF"


  def test_plot_writes_rose_plots() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          _write_pipeline_outputs(tmp, n_fovs=2, size=64)
          cfg = _write_config(tmp)
          result = runner.invoke(main, [
              "plot", "--config", str(cfg), "--output", str(tmp),
          ])
          assert result.exit_code == 0, result.output
          roses = list((tmp / "06_plots" / "roses").glob("*.pdf"))
          assert len(roses) >= 2  # one per FOV + aggregate


  def test_plot_writes_vector_maps() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          _write_pipeline_outputs(tmp, n_fovs=2, size=64)
          cfg = _write_config(tmp)
          result = runner.invoke(main, [
              "plot", "--config", str(cfg), "--output", str(tmp),
          ])
          assert result.exit_code == 0, result.output
          maps = list((tmp / "06_plots" / "vector_maps").glob("*.png"))
          assert len(maps) >= 2


  def test_plot_missing_per_cell_raises_error() -> None:
      runner = CliRunner()
      with tempfile.TemporaryDirectory() as td:
          tmp = Path(td)
          cfg = _write_config(tmp)
          tmp.mkdir(exist_ok=True)
          result = runner.invoke(main, [
              "plot", "--config", str(cfg), "--output", str(tmp),
          ])
          assert result.exit_code != 0
  ```

- [ ] **Step 2: Run tests**

  ```bash
  pytest tests/cli/test_cli_figures.py -v 2>&1 | tail -10
  ```

  Expected: 4 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/cli/test_cli_figures.py
  git commit -m "test(cli): add quantipy plot CLI tests — summary PDF, rose plots, vector maps"
  ```

---

## Task 19: Remove `front` and `plot` stubs; wire CLI modules

**Files:** Modify `src/quantipy_polarity/_stubs.py`

Remove the `"front"` and `"plot"` entries from `_STUBS` so the real commands registered by `_cli_front.py` and `_cli_figures.py` are not shadowed.

- [ ] **Step 1: Read `src/quantipy_polarity/_stubs.py`**

  Confirm that `"front"` maps to Phase 4 pointer, and `"plot"` maps to Phase 4 pointer.

- [ ] **Step 2: Remove `front` and `plot` from `_STUBS`**

  In `_stubs.py`, delete these two entries from the `_STUBS` dict:

  ```python
      "front": (
          "[Advanced] Migration-front detection (auto only in v0.1.0)",
          "Phase 4 (migration front)",
      ),
      "plot": (
          "[Advanced] Regenerate plots from aggregated parquet",
          "Phase 4 (visualization)",
      ),
  ```

  After removal, `_STUBS` should no longer contain `"front"` or `"plot"`.

- [ ] **Step 3: Verify `quantipy --help` shows both commands as real (no stub message)**

  ```bash
  python -m quantipy_polarity.cli --help 2>&1
  ```

  Expected output contains `front` and `plot` in the Advanced commands section, with their real short-help strings — not the stub "(Phase N stub)" text.

- [ ] **Step 4: Verify stub test still passes (stubs test should not expect `front`/`plot` as stubs)**

  ```bash
  pytest tests/test_cli_stubs.py -v 2>&1 | tail -5
  ```

  Confirm the test file checks only the remaining stubs. If `test_cli_stubs.py` has `"front"` or `"plot"` in its expected-stubs list, remove those entries from the test's expected set. Open and edit if needed.

- [ ] **Step 5: Run full test suite**

  ```bash
  pytest -q 2>&1 | tail -5
  ```

  Expected: ≥150 passed, 0 errors.

- [ ] **Step 6: Commit**

  ```bash
  git add src/quantipy_polarity/_stubs.py tests/test_cli_stubs.py
  git commit -m "feat(cli): remove front + plot stubs — real commands registered by Phase 4 modules"
  ```

---

## Task 20: Documentation updates — `migration-front.md` and `concepts.md`

**Files:** Modify `docs/migration-front.md`; modify `docs/concepts.md`

Document the v6 algorithm provenance in `migration-front.md`; add a short migration section to `concepts.md`.

- [ ] **Step 1: Read current `docs/migration-front.md`**

  Confirm whether it exists and what it contains. It may be a stub from Phase 1.

- [ ] **Step 2: Overwrite `docs/migration-front.md` with algorithm provenance**

  Replace (or create) the file with:

  ```markdown
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
  ```

- [ ] **Step 3: Append a migration note to `docs/concepts.md`**

  Find the end of `docs/concepts.md` and append:

  ```markdown

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
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add docs/migration-front.md docs/concepts.md
  git commit -m "docs: add migration-front algorithm provenance + concepts.md migration section"
  ```

---

## Task 21: README and CLAUDE.md updates

**Files:** Modify `README.md`; modify `CLAUDE.md`

- [ ] **Step 1: Read the current Phase status badge/table in `README.md`**

  Confirm there is a phase table or checklist. Locate the Phase 3 line.

- [ ] **Step 2: Update phase table in `README.md`**

  Find the existing phase status block and update it. Replace the Phase 3 complete / Phase 4 pending lines with:

  ```markdown
  | Phase | Scope | Status |
  |-------|-------|--------|
  | 1 | CLI scaffold, Pydantic config | ✅ Complete |
  | 2 | Masks → polarity pipeline | ✅ Complete |
  | 3 | TIF/ND2 ingest + Cellpose-SAM segmentation | ✅ Complete |
  | 4 | Migration front detection + visualization | ✅ Complete |
  | 5 | `quantipy run` orchestration + resume/atomic writes | 🔲 Planned |
  | 6 | Demo bundle + validation + HTML report | 🔲 Planned |
  | 7 | Interactive viewer + experimental analyses | 🔲 Planned |
  ```

- [ ] **Step 3: Update `CLAUDE.md` command map**

  Find the command table in `CLAUDE.md` and add the Phase 4 commands. Add rows for `front` and `plot`:

  ```markdown
  | `quantipy front` | Migration-front detection; writes `04_migration/front_um_per_fov.parquet` + QC PNGs |
  | `quantipy plot`  | Regenerate all figures (vector maps, roses, overlays, summary) from existing parquet |
  ```

- [ ] **Step 4: Run full test suite to confirm nothing broke**

  ```bash
  pytest -q 2>&1 | tail -5
  ```

  Expected: ≥150 passed.

- [ ] **Step 5: Commit**

  ```bash
  git add README.md CLAUDE.md
  git commit -m "docs: mark Phase 4 complete in README phase table + update CLAUDE.md command map"
  ```

---

## Task 22: Full acceptance run + tag `phase-4-complete`

**Files:** No source changes. Verify acceptance criteria and tag.

- [ ] **Step 1: Verify command stubs replaced**

  ```bash
  python -m quantipy_polarity.cli front --help 2>&1 | grep -v "stub"
  python -m quantipy_polarity.cli plot --help 2>&1 | grep -v "stub"
  ```

  Expected: both commands print real help text; neither line contains the word "stub".

- [ ] **Step 2: Run the full test suite**

  ```bash
  pytest -v 2>&1 | tail -10
  ```

  Expected: ≥150 passed, 0 failed, ≤1 skipped. Record actual count.

- [ ] **Step 3: Verify PDF/PNG headers on a live run**

  ```bash
  python -c "
  import tempfile, numpy as np, pandas as pd
  from pathlib import Path
  from tests.fixtures._build import build_synthetic_fov
  from quantipy_polarity.viz.vector_map import save_vector_map
  from quantipy_polarity.viz.rose_plot import save_rose
  from quantipy_polarity.viz.summary import save_population_summary

  data = build_synthetic_fov(n_cells=20, image_size=128, seed=42)
  fov_df = pd.DataFrame([
      {'fov_id': 'FOV_01', 'cell_id': cid, 'centroid_y': cy, 'centroid_x': cx,
       'axis_deg': ang, 'magnitude': 0.5, 'area_px': 200, 'qc_flags': 0}
      for (cid, ang), (_, (cy, cx)) in zip(data['theta_truth'].items(), data['centroids'].items())
  ])
  with tempfile.TemporaryDirectory() as td:
      stem = Path(td)
      paths = save_vector_map(data['membrane'], data['label_mask'], fov_df, stem / 'vec')
      assert paths[0].read_bytes()[:4] == b'\x89PNG', 'PNG header fail'
      assert paths[1].read_bytes()[:4] == b'%PDF', 'PDF header fail'
      paths2 = save_rose(data['theta_truth'].values(), stem / 'rose')
      assert paths2[1].read_bytes()[:4] == b'%PDF', 'rose PDF fail'
      paths3 = save_population_summary(fov_df.assign(dist_to_front_um=np.nan), stem / 'summary')
      assert paths3[1].read_bytes()[:4] == b'%PDF', 'summary PDF fail'
  print('All Phase 4 figure header checks PASSED')
  "
  ```

  Expected: `All Phase 4 figure header checks PASSED`

- [ ] **Step 4: Confirm `quantipy --help` shows no import errors**

  ```bash
  quantipy --help 2>&1
  ```

  Expected: clean help output. No `ImportError` or `ModuleNotFoundError`.

- [ ] **Step 5: Tag the release**

  ```bash
  git tag phase-4-complete
  git push origin main --tags
  ```

  Expected: tag pushed successfully. GitHub shows `phase-4-complete` tag on `main`.

- [ ] **Step 6: Record final test count in a commit message**

  ```bash
  pytest -q 2>&1 | tail -1
  ```

  Note the line e.g. `158 passed, 1 skipped in 12.34s`. Include this count in the tag annotation if desired:

  ```bash
  git tag -f phase-4-complete -m "Phase 4 complete: migration front + visualization. NNN tests passing."
  git push origin --tags --force
  ```

---

## Summary

**22 tasks**, structured as:

| Batch | Tasks | Description |
|-------|-------|-------------|
| A — Contracts | 1 | FrontResult Pydantic model in contracts.py |
| B — Migration core | 2–4 | front_detect, front_io, distance |
| C — Viz infrastructure | 5–6 | _style.py with figstyle import/fallback + tests |
| D — Viz figures | 7–14 | vector_map, rose_plot, front_overlay, summary (each with tests) |
| E — CLI | 15–19 | _cli_front, _cli_figures, remove stubs |
| F — Docs + acceptance | 20–22 | migration-front.md, README, CLAUDE.md, tag |

**Files created:** 16 new files  
**Files modified:** 6 existing files (`contracts.py`, `migration/__init__.py`, `viz/__init__.py`, `_stubs.py`, `cli.py`, `docs/concepts.md`)  
**Test count target:** 122 (Phase 3 baseline) + ≥28 new = **≥150 passed**

**Dependency batching for subagent dispatch:**

```
Batch 1 (no deps):    Task 1 (contracts)
Batch 2 (needs 1):    Tasks 2, 3, 4 (migration modules) — independent of each other, parallel OK
Batch 3 (needs none): Tasks 5, 6 (viz/_style) — independent of migration
Batch 4 (needs 5):    Tasks 7+8, 9+10, 11+12, 13+14 — 4 parallel pairs
Batch 5 (needs 2+4):  Tasks 15+16, 17+18 — CLI + tests, parallel pair
Batch 6 (needs 5):    Task 19 (remove stubs)
Batch 7 (needs all):  Tasks 20, 21, 22 (docs + acceptance)
```
