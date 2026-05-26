"""Unit tests for the stable data contracts."""
import pytest

from quantipy_polarity.contracts import (
    PER_CELL_COLUMNS,
    PerCellRow,
    QC_EDGE_CELL,
    QC_LOW_MAG,
)


def test_per_cell_columns_match_model() -> None:
    """Constant tuple must match the Pydantic model fields exactly (no drift)."""
    assert set(PER_CELL_COLUMNS) == set(PerCellRow.model_fields.keys())


def test_qc_flags_are_distinct_bits() -> None:
    flags = [QC_EDGE_CELL, QC_LOW_MAG, 1 << 1, 1 << 2, 1 << 4]
    # All distinct, all powers of two
    assert all(f & (f - 1) == 0 for f in flags)


def test_per_cell_row_minimal() -> None:
    row = PerCellRow(
        fov_id="FOV_01",
        cell_id=42,
        centroid_y=120.5,
        centroid_x=300.1,
        area_px=850,
        axis_deg=87.3,
        magnitude=0.42,
    )
    assert row.qc_flags == 0
    assert row.mig_alignment is None


def test_per_cell_row_rejects_invalid_axis() -> None:
    with pytest.raises(ValueError):
        PerCellRow(
            fov_id="FOV_01",
            cell_id=42,
            centroid_y=0.0,
            centroid_x=0.0,
            area_px=10,
            axis_deg=400.0,  # >= 360
            magnitude=0.5,
        )


def test_per_cell_row_rejects_zero_cell_id() -> None:
    with pytest.raises(ValueError):
        PerCellRow(
            fov_id="FOV_01",
            cell_id=0,  # reserved for background
            centroid_y=0.0,
            centroid_x=0.0,
            area_px=10,
            axis_deg=0.0,
            magnitude=0.0,
        )
