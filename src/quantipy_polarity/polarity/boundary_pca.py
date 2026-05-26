"""Per-cell intensity-weighted Fourier-k=2 polarity on skeleton-adjacent pixels.

Algorithm (skeleton-aware mode)
--------------------------------
For each cell:
1. Expand the cell bounding box by ``_CROP_PAD`` pixels on every side.
2. Binary-dilate the cell mask by one pixel (3×3 structuring element).
3. Skeleton-adjacent pixels = dilated mask ∩ skeleton mask ∩ ~cell mask.
4. For each skeleton-adjacent pixel *i* at position (r_i, c_i) carrying signal I_i:
   - phi_i  = arctan2(r_i − c̄_r, c_i − c̄_c)   (angle from cell interior centroid)
   - dI_i   = I_i − mean(I)                        (mean-subtracted signal)
   - S_w    = sum(I)                               (total skel-adj signal)
   - z2     = sum(dI_i · exp(2j · phi_i)) / S_w   (Fourier k=2 coefficient)
5. PCA Magnitude = |z2|                            (∈ [0, 1])
6. PCA Angle (°)  = arctan2(−Im z2, Re z2) / 2   → wrapped axially to [−90, 90]

Angle convention (skeleton mode)
----------------------------------
- Horizontal polarity (signal concentrated left+right): angle ≈ 0°.
- Vertical polarity (signal concentrated top+bottom):   angle ≈ ±90°.

Fallback (no skeleton provided)
---------------------------------
Original intensity-weighted PCA on ``find_boundaries`` pixels, preserved exactly
as written (including the 1-pixel padding fix for cells touching crop edges).

Angle convention (fallback)
-----------------------------
- Row-component is v_dom[0], col-component is v_dom[1].
- ``theta_rad = arctan2(v_dom[0], v_dom[1])`` — standard image frame.
- Wrapped to axial [-90, 90]: ``((deg + 90) % 180) - 90``.
"""

# ---------------------------------------------------------------------------
# QP vs Python calibration (validated 2026-05-13)
# ---------------------------------------------------------------------------
# QP_CALIBRATION_SLOPE = 0.669
#
# Magnitude calibration
#   Python skeleton-mode magnitudes are consistently ~0.669× QP values
#   (OLS slope across two replicates: 0.6620, 0.6762; |Δslope| = 0.014).
#   To convert Python output to QP-equivalent scale:
#       py_mag_calibrated = py_mag / 0.669
#   Apply ONLY when comparing to absolute QP magnitudes.
#   NOT needed for within-experiment comparisons — the bias cancels.
#   Cause: boundary-pixel attribution differs slightly between QP's and
#   Python's flood-fill even when cell positions and boundary counts match
#   (median centroid distance 0.25 px); the normalization formula is
#   algebraically identical.
#
# Elongated-cell angle bias (AR > 2.0)
#   Skeleton-pixel sampling is non-uniform around elongated cells (denser
#   at cell ends, sparser at sides), biasing the Fourier k=2 angle toward
#   the morphological long axis relative to QP (median shift 9.5°,
#   Spearman ρ(AR, |Δangle|) = +0.28, Wilcoxon p < 0.0001).
#   Recommendation: flag cells with AR > 2.0 as `is_elongated` for
#   downstream filtering — do NOT exclude by default.
#
# Full forensics: reports/qp_python_forensics.md
# ---------------------------------------------------------------------------

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.ndimage import binary_dilation, find_objects
from skimage.segmentation import find_boundaries

# How many pixels to expand the bounding box before looking for skeleton-adjacent pixels.
# Must be at least dilation_radius + 1 to avoid missing skel pixels near the bbox edge.
_CROP_PAD: int = 2


# ---------------------------------------------------------------------------
# Skeleton-aware (Fourier k=2) path
# ---------------------------------------------------------------------------

def _fourier2_one_cell(
    signal: np.ndarray,
    labels: np.ndarray,
    skeleton: np.ndarray,
    label_val: int,
    sl: tuple,
    min_skel_pixels: int,
    dilation_iterations: int = 1,
) -> dict | None:
    """Compute Fourier k=2 nematic polarity on skeleton-adjacent pixels.

    Parameters
    ----------
    signal:
        Full (H, W) signal image.
    labels:
        Full (H, W) integer label image (0 = background).
    skeleton:
        Full (H, W) boolean mask (True = skeleton / cell-wall pixel).
    label_val:
        Cell label value (>0) to process.
    sl:
        Bounding-box slice tuple from ``scipy.ndimage.find_objects``.
    min_skel_pixels:
        Minimum skeleton-adjacent pixels required; fewer → return None.

    Returns
    -------
    dict or None
    """
    r_off = sl[0].start
    c_off = sl[1].start

    # Widen crop pad to accommodate multi-iteration dilation
    crop_pad = max(_CROP_PAD, dilation_iterations + 1)

    # Expand bounding box to catch skeleton pixels just outside the tight bbox
    r_start = max(0, r_off - crop_pad)
    c_start = max(0, c_off - crop_pad)
    r_end   = min(labels.shape[0], sl[0].stop + crop_pad)
    c_end   = min(labels.shape[1], sl[1].stop + crop_pad)

    cell_mask_exp = (labels[r_start:r_end, c_start:c_end] == label_val)
    skel_crop     = skeleton[r_start:r_end, c_start:c_end]

    # Dilation of cell mask → intersect with skeleton
    struct   = np.ones((3, 3), dtype=bool)
    dilated  = binary_dilation(cell_mask_exp, structure=struct, iterations=dilation_iterations)
    skel_adj = dilated & skel_crop & ~cell_mask_exp   # strictly outside cell

    rows_s, cols_s = np.nonzero(skel_adj)
    n_skel = len(rows_s)

    if n_skel < min_skel_pixels:
        return None

    # Full-image coordinates of skeleton-adjacent pixels
    rows_full = rows_s + r_start
    cols_full = cols_s + c_start

    # Local coordinates relative to the original (tight) bbox
    rows_local = rows_s + r_start - r_off
    cols_local = cols_s + c_start - c_off

    I   = signal[rows_full, cols_full].astype(np.float64)
    S_w = I.sum()

    if S_w <= 0.0:
        return {
            "Cell Identity": label_val,
            "PCA Magnitude": float("nan"),
            "PCA Angle (°)": float("nan"),
            "n_boundary_px": n_skel,
            "intensity_sum":  float(S_w),
        }

    # Geometric centroid of cell interior (tight bbox)
    cell_mask_orig = (labels[sl] == label_val)
    rows_int, cols_int = np.nonzero(cell_mask_orig)
    c_r = float(rows_int.mean())   # row centroid (in bbox coords)
    c_c = float(cols_int.mean())   # col centroid (in bbox coords)

    # Angles from centroid to each skeleton-adjacent pixel
    phi = np.arctan2(rows_local.astype(np.float64) - c_r,
                     cols_local.astype(np.float64) - c_c)

    # Fourier k=2 coefficient
    dI = I - I.mean()
    z2  = np.sum(dI * np.exp(2j * phi)) / S_w

    magnitude = float(np.abs(z2))

    # Axial angle: convert complex phase to direction, halve, wrap to [−90, 90]
    theta_deg   = np.degrees(np.arctan2(-z2.imag, z2.real)) / 2.0
    theta_axial = ((theta_deg + 90.0) % 180.0) - 90.0

    return {
        "Cell Identity": label_val,
        "PCA Magnitude": magnitude,
        "PCA Angle (°)": float(theta_axial),
        "n_boundary_px": n_skel,
        "intensity_sum":  float(S_w),
    }


# ---------------------------------------------------------------------------
# Fallback PCA path (no skeleton)
# ---------------------------------------------------------------------------

def _pca_one_cell(
    signal: np.ndarray,
    labels: np.ndarray,
    label_val: int,
    sl: tuple,
    min_boundary_pixels: int,
) -> dict | None:
    """Compute intensity-weighted PCA polarity for a single cell (fallback).

    Parameters
    ----------
    signal:
        Full (H, W) signal image.
    labels:
        Full (H, W) integer label image.
    label_val:
        The cell label value (>0) to process.
    sl:
        Slice tuple from ``scipy.ndimage.find_objects`` (already offset-trimmed).
    min_boundary_pixels:
        Minimum number of boundary pixels required; fewer → skip (return None).

    Returns
    -------
    dict with keys: Cell Identity, PCA Magnitude, PCA Angle (°), n_boundary_px,
    intensity_sum — or None if cell should be skipped.
    """
    label_crop = labels[sl]
    cell_mask = label_crop == label_val

    # Boundary detection via find_boundaries(mode='inner') requires background pixels
    # adjacent to the cell to be visible in the crop.  find_objects gives a tight
    # bounding box, so cells touching the crop edge have no background neighbour and
    # find_boundaries returns zero pixels.  Pad the crop by 1 pixel on all sides with
    # zeros (background) so border-touching cells are handled correctly.
    cell_mask_padded = np.pad(cell_mask, pad_width=1, mode="constant", constant_values=False)
    bnd_padded = find_boundaries(cell_mask_padded, mode="inner")
    # Unpad to restore crop coordinates
    bnd_crop = bnd_padded[1:-1, 1:-1]

    # get coords in crop frame
    rows_crop, cols_crop = np.nonzero(bnd_crop)
    n_bnd = len(rows_crop)

    if n_bnd < min_boundary_pixels:
        return None

    # convert to full-image coords
    r_offset = sl[0].start
    c_offset = sl[1].start
    rows = rows_crop.astype(np.float64) + r_offset
    cols = cols_crop.astype(np.float64) + c_offset

    I = signal[rows_crop + r_offset, cols_crop + c_offset].astype(np.float64)
    Sw = I.sum()

    if Sw <= 0.0:
        return {
            "Cell Identity": label_val,
            "PCA Magnitude": float("nan"),
            "PCA Angle (°)": float("nan"),
            "n_boundary_px": n_bnd,
            "intensity_sum": Sw,
        }

    # weighted centroid
    c_r = np.dot(I, rows) / Sw
    c_c = np.dot(I, cols) / Sw

    dr = rows - c_r
    dc = cols - c_c

    # weighted covariance (2x2)
    M = np.empty((2, 2), dtype=np.float64)
    M[0, 0] = np.dot(I, dr * dr) / Sw
    M[1, 1] = np.dot(I, dc * dc) / Sw
    M[0, 1] = np.dot(I, dr * dc) / Sw
    M[1, 0] = M[0, 1]

    # eigendecompose — eigh returns ascending eigenvalues
    evals, evecs = np.linalg.eigh(M)
    l_min, l_max = evals[0], evals[1]
    v_dom = evecs[:, 1]  # dominant eigenvector (largest eigenvalue)

    # magnitude
    denom = l_max + l_min
    if denom <= 0.0:
        magnitude = 0.0
    else:
        magnitude = float((l_max - l_min) / denom)

    # angle: arctan2(row_component, col_component) → image frame
    theta_rad = np.arctan2(v_dom[0], v_dom[1])
    theta_deg = np.degrees(theta_rad)
    # wrap to axial [-90, 90]
    theta_axial = ((theta_deg + 90.0) % 180.0) - 90.0

    return {
        "Cell Identity": label_val,
        "PCA Magnitude": magnitude,
        "PCA Angle (°)": theta_axial,
        "n_boundary_px": n_bnd,
        "intensity_sum": float(Sw),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cell_polarity(
    signal: np.ndarray,
    labels: np.ndarray,
    min_boundary_pixels: int = 4,
    skeleton: np.ndarray | None = None,
    dilation_iterations: int = 1,
) -> pd.DataFrame:
    """Compute per-cell polarity.

    When *skeleton* is provided (recommended), the Fourier k=2 nematic polarity
    is computed on skeleton-adjacent pixels — the best available approximation of
    QP's ``PCA_Cell-by-Cell_Polarity`` metric (Pearson r ≈ 0.89 vs QP ground truth
    on FOV_02, Spearman r ≈ 0.88).

    When *skeleton* is ``None``, falls back to intensity-weighted PCA on
    ``find_boundaries`` pixels (original algorithm; lower agreement with QP).

    Parameters
    ----------
    signal:
        (H, W) float-castable array — the polarity marker / membrane channel.
    labels:
        (H, W) integer array — Cellpose / QP labels (0 = background).
    min_boundary_pixels:
        Minimum boundary/skeleton-adjacent pixels required to process a cell.
        Default 4 (skeleton mode) or 8 (PCA fallback legacy default).
    skeleton:
        Optional (H, W) uint8 or bool array.  Non-zero pixels mark cell-wall /
        skeleton pixels (e.g. the ``handCorrection.png`` image from QP, where
        255 = skeleton).  When supplied, activates the Fourier k=2 path.
    dilation_iterations:
        Number of binary dilation iterations used to expand the cell mask when
        searching for skeleton-adjacent pixels.  Default 1 (original behaviour).
        Increase to 2–4 for higher-resolution images where 1 px is too narrow
        a physical band (e.g., 0.325 µm/px vs. 0.648 µm/px at 25h).

    Returns
    -------
    pd.DataFrame with columns:
        Cell Identity   — 1-indexed int matching label value
        PCA Magnitude   — float ≥ 0 (Fourier k=2 mode: bounded roughly [0, 0.25];
                          PCA fallback mode: ∈ [0, 1])
        PCA Angle (°)   — float in [−90, 90] (axial)
        n_boundary_px   — int (number of pixels used; for QC)
        intensity_sum   — float (total signal used; for QC)
    """
    signal = np.asarray(signal, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int32)

    # Prepare skeleton mask (bool) if provided
    skel_mask: np.ndarray | None = None
    if skeleton is not None:
        skel_arr = np.asarray(skeleton)
        skel_mask = skel_arr > 0  # any non-zero pixel = skeleton

    slices = find_objects(labels)  # list of (slice_row, slice_col) or None per label

    records: list[dict] = []
    for idx, sl in enumerate(slices):
        if sl is None:
            continue
        label_val = idx + 1  # find_objects is 0-indexed; label 1 → index 0

        if skel_mask is not None:
            result = _fourier2_one_cell(
                signal, labels, skel_mask, label_val, sl, min_boundary_pixels,
                dilation_iterations=dilation_iterations,
            )
        else:
            result = _pca_one_cell(
                signal, labels, label_val, sl, min_boundary_pixels
            )

        if result is not None:
            records.append(result)

    if not records:
        return pd.DataFrame(
            columns=["Cell Identity", "PCA Magnitude", "PCA Angle (°)", "n_boundary_px", "intensity_sum"]
        )

    df = pd.DataFrame(records)
    df["Cell Identity"] = df["Cell Identity"].astype(int)
    return df
