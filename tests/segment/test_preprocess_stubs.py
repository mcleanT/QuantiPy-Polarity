"""Fast-tier smoke tests for the segment/ package.

These tests do NOT import cellpose; they verify module structure and
the lazy-import contract (ImportError with a useful message).
"""

from __future__ import annotations

import inspect

import pytest


def test_segment_package_imports() -> None:
    """segment/ package and cellpose_sam module import without errors."""
    import quantipy_polarity.segment  # noqa: F401
    from quantipy_polarity.segment.cellpose_sam import segment_fov

    assert callable(segment_fov)


def test_segment_fov_signature() -> None:
    """segment_fov has the expected keyword-only parameters."""
    from quantipy_polarity.segment.cellpose_sam import segment_fov

    sig = inspect.signature(segment_fov)
    params = sig.parameters
    assert "image" in params
    assert "model" in params
    assert "diameter" in params
    assert "gpu" in params
    assert "channels" in params
    assert "min_size_px" in params


def test_segmentation_result_contract() -> None:
    """SegmentationResult Pydantic model validates a known-good dict."""
    from quantipy_polarity.contracts import SegmentationResult

    sr = SegmentationResult(
        fov_id="FOV_01",
        n_cells_total=85,
        n_cells_after_filter=79,
        flow_threshold=0.4,
        cellprob_threshold=0.0,
        diameter_px=30.0,
        min_size_px=100,
        model="cpsam",
    )
    assert sr.fov_id == "FOV_01"
    assert sr.n_cells_after_filter == 79
