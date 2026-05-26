"""Tests for io/nd2.py — ND2 ingest.

nd2reader tests are gated: skipped automatically when nd2reader is not installed.
Tests that don't invoke nd2reader (unit tests of helper functions) run always.
"""

from __future__ import annotations

import numpy as np
import pytest

from quantipy_polarity.io.nd2 import (
    _normalize_to_float32,
    _pixel_size_from_nd2,
    _z_project,
)


# ---------------------------------------------------------------------------
# _z_project — pure numpy, no nd2reader
# ---------------------------------------------------------------------------


def test_z_project_mip() -> None:
    stack = np.array(
        [[[1, 2], [3, 4]], [[5, 0], [0, 1]]], dtype=np.float32
    )  # (2, 2, 2)
    out = _z_project(stack, "mip", None)
    expected = np.array([[5, 2], [3, 4]], dtype=np.float32)
    np.testing.assert_array_equal(out, expected)


def test_z_project_none_picks_midplane() -> None:
    stack = np.zeros((5, 4, 4), dtype=np.float32)
    stack[2] = 1.0
    out = _z_project(stack, "none", None)
    np.testing.assert_array_equal(out, stack[2])


def test_z_project_substack() -> None:
    stack = np.zeros((10, 4, 4), dtype=np.float32)
    stack[3] = 5.0
    stack[7] = 7.0
    out = _z_project(stack, "substack", (2, 5))
    # Only planes 2-5 visible; max should be 5.0 from plane 3
    assert out.max() == pytest.approx(5.0)


def test_z_project_substack_out_of_range() -> None:
    stack = np.zeros((5, 4, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="out of range"):
        _z_project(stack, "substack", (3, 10))


def test_z_project_unknown_policy() -> None:
    stack = np.zeros((3, 4, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="Unknown z_policy"):
        _z_project(stack, "bad_policy", None)


# ---------------------------------------------------------------------------
# _pixel_size_from_nd2 — mock metadata dict
# ---------------------------------------------------------------------------


def test_pixel_size_from_nd2_uses_metadata() -> None:
    class FakeND2:
        metadata = {"pixel_microns": 0.65}

    px = _pixel_size_from_nd2(FakeND2(), 1.0)
    assert px == pytest.approx(0.65)


def test_pixel_size_from_nd2_fallback_on_missing() -> None:
    class FakeND2:
        metadata = {}

    px = _pixel_size_from_nd2(FakeND2(), 0.5)
    assert px == pytest.approx(0.5)


def test_pixel_size_from_nd2_fallback_on_invalid() -> None:
    class FakeND2:
        metadata = {"pixel_microns": "not_a_number"}

    px = _pixel_size_from_nd2(FakeND2(), 0.5)
    assert px == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# _normalize_to_float32
# ---------------------------------------------------------------------------


def test_normalize_uint16() -> None:
    arr = np.array([[32768]], dtype=np.uint16)
    out = _normalize_to_float32(arr)
    assert out.dtype == np.float32
    assert np.isclose(out[0, 0], 32768 / 65535, atol=1e-5)


def test_normalize_float_scales_by_max() -> None:
    arr = np.array([[0.0, 500.0, 1000.0]], dtype=np.float32)
    out = _normalize_to_float32(arr)
    assert np.isclose(out[0, 2], 1.0)
    assert np.isclose(out[0, 1], 0.5)


# ---------------------------------------------------------------------------
# iter_nd2_dataset — requires nd2reader; gated
# ---------------------------------------------------------------------------


def test_iter_nd2_dataset_import_error_without_nd2reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify iter_nd2_dataset raises ImportError with helpful message when nd2reader missing."""
    pytest.importorskip(
        "nd2reader", reason="nd2reader not installed; skipping ND2 integration tests"
    )
    import sys

    original = sys.modules.get("nd2reader")
    sys.modules["nd2reader"] = None  # type: ignore[assignment]
    try:
        import importlib
        import quantipy_polarity.io.nd2 as nd2_mod

        importlib.reload(nd2_mod)
        with pytest.raises((ImportError, TypeError)):
            list(nd2_mod.iter_nd2_dataset("fake.nd2", 0, None, 0.65))
    finally:
        if original is None:
            del sys.modules["nd2reader"]
        else:
            sys.modules["nd2reader"] = original
