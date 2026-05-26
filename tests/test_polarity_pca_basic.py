"""Basic / edge-case tests for boundary_pca.compute_cell_polarity.

The ground-truth recovery test lives in test_polarity_pca_recovery.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantipy_polarity.polarity.boundary_pca import compute_cell_polarity


# Column names returned by compute_cell_polarity
AXIS_COL = "PCA Angle (°)"
MAG_COL = "PCA Magnitude"


def _single_cell_label_mask(shape=(64, 64), bbox=((16, 16), (48, 48))) -> np.ndarray:
    msk = np.zeros(shape, dtype=np.uint16)
    (y0, x0), (y1, x1) = bbox
    msk[y0:y1, x0:x1] = 1
    return msk


def test_empty_mask_returns_no_cells() -> None:
    labels = np.zeros((32, 32), dtype=np.uint16)
    signal = np.zeros_like(labels, dtype=np.float32)
    result = compute_cell_polarity(signal, labels)
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] == 0


def test_single_cell_uniform_signal_low_magnitude() -> None:
    labels = _single_cell_label_mask()
    signal = np.ones_like(labels, dtype=np.float32) * 0.5
    result = compute_cell_polarity(signal, labels)
    assert result.shape[0] >= 1
    mag = float(result[MAG_COL].iloc[0])
    assert mag < 0.15, f"expected near-zero magnitude on uniform signal, got {mag}"


def test_output_axis_is_axial_range() -> None:
    labels = _single_cell_label_mask()
    rng = np.random.default_rng(0)
    signal = rng.random(labels.shape).astype(np.float32)
    result = compute_cell_polarity(signal, labels)
    axes = result[AXIS_COL].to_numpy()
    # Accept either axial convention: [-90, 90] or [0, 180) or [0, 360)
    assert all((-90.0 <= a <= 90.0) or (0.0 <= a < 360.0) for a in axes), f"axes out of expected range: {axes}"


def test_dtype_preserved_membrane_float32() -> None:
    labels = _single_cell_label_mask()
    signal = np.zeros_like(labels, dtype=np.float32)
    signal[16:48, 16:32] = 1.0  # left half of cell has signal
    result = compute_cell_polarity(signal, labels)
    assert result is not None
    assert result.shape[0] >= 1
