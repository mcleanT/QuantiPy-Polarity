"""Pydantic-validated configuration schema for QuantiPy Polarity.

Single YAML drives every command. The `input.mode` field is a discriminator
controlling which subset of input.* fields are required (nd2 / tif / masks).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, Field, model_validator


class ProjectConfig(BaseModel):
    name: str = "my_experiment"
    output_dir: Path = Path("./results")


class _InputCommon(BaseModel):
    path: Path
    source: Literal["explicit", "auto"] = "explicit"


class InputND2(_InputCommon):
    mode: Literal["nd2"]
    z_policy: Literal["mip", "substack", "none"] = "mip"
    substack_range: tuple[int, int] | None = None
    channel_membrane: int = Field(ge=0)
    channel_segmentation: int = Field(ge=0)
    pixel_size_um: float = Field(gt=0)

    @model_validator(mode="after")
    def _validate_substack_range(self) -> "InputND2":
        if self.z_policy == "substack" and self.substack_range is None:
            raise ValueError("substack_range required when z_policy='substack'")
        if self.substack_range is not None:
            lo, hi = self.substack_range
            if lo >= hi:
                raise ValueError(
                    f"substack_range[0] must be < substack_range[1]; got {self.substack_range}"
                )
        return self


class InputTIF(_InputCommon):
    mode: Literal["tif"]
    z_policy: Literal["mip", "substack", "none"] = "none"
    substack_range: tuple[int, int] | None = None
    channel_membrane: int = Field(ge=0)
    channel_segmentation: int = Field(ge=0)
    pixel_size_um: float = Field(gt=0)
    tif_scheme: Literal["stack", "multifile"] = "stack"
    channel_suffix_template: str = "_ch{ch}"


class InputMasks(_InputCommon):
    mode: Literal["masks"]
    masks_dir: Path
    pixel_size_um: float = Field(gt=0)
    channel_membrane: int = Field(default=0, ge=0)


Input = Union[InputND2, InputTIF, InputMasks]


class SegmentConfig(BaseModel):
    model: Literal["cellpose-sam", "user_supplied"] = "cellpose-sam"
    diameter_px: int = Field(default=60, gt=0)
    min_size_px: int = Field(default=100, gt=0)
    fix_undersegmented: bool = True
    user_masks_dir: Path | None = None


class PolarityConfig(BaseModel):
    method: Literal["boundary_pca"] = "boundary_pca"
    axial: bool = True
    weight: Literal["magnitude", "uniform"] = "magnitude"
    exclude_edge_cells: bool = True


class MigrationConfig(BaseModel):
    detect_front: bool = True
    front_method: Literal["v3_outward", "none"] = "v3_outward"
    erosion_px: int = Field(default=10, ge=0)
    classify_fragments: bool = True
    local_direction: bool = True
    min_fragment_area_px: int = Field(default=500, ge=0)


class VizConfig(BaseModel):
    style: Literal["nature", "minimal"] = "nature"
    rose_bins: int = Field(default=24, gt=0)
    half_disk: bool = True
    per_fov_maps: bool = True
    overlay_dpi: int = Field(default=600, gt=0)
    vector_scale: float = Field(default=1.0, gt=0)


class ReportConfig(BaseModel):
    html: bool = True
    embed_thumbnails: bool = True
    include_per_cell_parquet: bool = True


class Config(BaseModel):
    project: ProjectConfig = ProjectConfig()
    input: Input = Field(discriminator="mode")
    segment: SegmentConfig = SegmentConfig()
    polarity: PolarityConfig = PolarityConfig()
    migration: MigrationConfig = MigrationConfig()
    viz: VizConfig = VizConfig()
    report: ReportConfig = ReportConfig()
    analyses: list[str] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Config":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    def to_yaml(self, path: Path | str) -> None:
        data = self.model_dump(mode="json", exclude_defaults=False)
        with open(path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
