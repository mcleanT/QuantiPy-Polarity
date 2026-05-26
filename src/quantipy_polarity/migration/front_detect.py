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
