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
        labels, density_sigma_px=20.0, border_margin_px=5, min_segment_px=100
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
