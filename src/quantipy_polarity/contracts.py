"""Stable data contracts crossed at module boundaries.

The per_cell parquet schema below is the **public stable API** of v0.1.0.
Schema changes follow SemVer:
  - additive (new column): minor bump
  - destructive (rename/remove): major bump

Coordinate conventions:
  - All image arrays are (H, W) or (H, W, C); origin (0, 0) top-left (numpy).
  - All coordinates are (y, x) pixels; never (x, y).
  - Angles in degrees: axial = [0, 180), vector = [0, 360).
  - Cell IDs: uint16, 0 reserved for background, FOV-unique not global.
  - FOV IDs: strings preserved from input filenames.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PerCellRow(BaseModel):
    """One row of the per_cell.parquet output. SemVer-stable in v0.1.0."""

    fov_id: str
    cell_id: int = Field(ge=1, le=65535)
    centroid_y: float
    centroid_x: float
    area_px: int = Field(ge=1)
    axis_deg: float = Field(ge=0.0, lt=360.0)
    magnitude: float = Field(ge=0.0)
    qc_flags: int = Field(default=0, ge=0)
    condition: str | None = None
    # Migration columns populated by migration/local.py (Phase 4)
    mig_dir_deg: float | None = None
    mig_alignment: float | None = None
    dist_to_front_um: float | None = None


# Parquet column names exposed as constants so downstream code references
# them through a single source of truth (no stringly-typed columns).
PER_CELL_COLUMNS: tuple[str, ...] = (
    "fov_id",
    "cell_id",
    "centroid_y",
    "centroid_x",
    "area_px",
    "axis_deg",
    "magnitude",
    "qc_flags",
    "condition",
    "mig_dir_deg",
    "mig_alignment",
    "dist_to_front_um",
)


# QC flag bits — populated by polarity/per_cell.py (Phase 2)
QC_EDGE_CELL: int = 1 << 0
QC_TOO_SMALL: int = 1 << 1
QC_TOO_LARGE: int = 1 << 2
QC_LOW_MAG: int = 1 << 3
QC_UNDERSEGMENTED: int = 1 << 4


class FOVManifestEntry(BaseModel):
    """One entry in the FOV manifest emitted by io/* stages."""

    fov_id: str
    path: str  # absolute path to normalized per-FOV TIF
    shape: tuple[int, int, int]  # (H, W, C)
    pixel_size_um: float
    condition: str | None = None
