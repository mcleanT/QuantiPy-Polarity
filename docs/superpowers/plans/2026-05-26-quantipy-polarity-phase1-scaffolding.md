# QuantiPy Polarity — Phase 1: Scaffolding + Config + CLI Shell

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an installable `quantipy-polarity` package whose CLI surface (`quantipy --help`, `quantipy init-config`, all primary + advanced subcommand stubs) works end-to-end on a fresh `pip install -e .[dev]`, with a fast-tier CI workflow green on push.

**Architecture:** Standard `src/` layout. Click-based CLI with two command groups (primary, advanced). Pydantic v2 discriminated-union config (`input.mode` ∈ {nd2, tif, masks}). All algorithmic modules created as empty subpackages with `NotImplementedError` placeholders so the CLI surface compiles. Tests exercise config validation, CLI parsing, and `init-config` output — algorithm tests come in later phases.

**Tech Stack:** Python 3.11+, Click 8.1+, Pydantic 2.5+, PyYAML 6.0+, pytest, hatchling (build), GitHub Actions.

**Spec source:** `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` (rev 1, post-codex-review).

**Working directory for execution:** clone of `https://github.com/mcleanT/QuantiPy-Polarity` (currently contains only README.md, LICENSE, .gitignore, and docs/superpowers/specs/). All paths below are relative to that clone root.

**Acceptance criteria for Phase 1 completion:**
1. `pip install -e .[dev]` succeeds in a clean Python 3.11 venv with no errors.
2. `quantipy --version` prints `0.1.0`.
3. `quantipy --help` lists two groups: **Primary commands** (`run`, `init-config`, `download-demo`, `debug`, `validate`) and **Advanced commands** (`ingest`, `segment`, `polarity`, `front`, `aggregate`, `plot`, `report`, `analyze`).
4. `quantipy init-config --mode masks --output /tmp/test_config.yaml` writes a Pydantic-valid YAML.
5. `pytest` passes locally and in GitHub Actions on push to `main`.
6. Loading the generated YAML via `Config.from_yaml()` returns a populated `Config` object.
7. All non-`init-config` subcommands print "Not implemented in Phase 1" with exit code 2 and a pointer to the relevant future phase.

---

## File Structure (locked at planning time)

```
QuantiPy-Polarity/
├── pyproject.toml                         # Task 1
├── environment.yml                        # Task 2
├── README.md                              # Updated in Task 22
├── CONTRIBUTING.md                        # Task 21
├── CLAUDE.md                              # Task 20
├── .claude/
│   ├── settings.json                      # Task 20
│   └── commands/                          # Task 20
│       ├── quantipy-run.md
│       ├── quantipy-debug-fov.md
│       └── quantipy-front-qc.md
├── .github/workflows/
│   ├── ci.yml                             # Task 23
│   └── ci-nightly.yml                     # Task 24 (skeleton; runs nothing real until Phase 3)
├── src/quantipy_polarity/
│   ├── __init__.py                        # Task 3
│   ├── _version.py                        # Task 3
│   ├── contracts.py                       # Task 6
│   ├── config.py                          # Tasks 4–5
│   ├── cli.py                             # Tasks 7–15
│   ├── _stubs.py                          # Task 16
│   ├── io/__init__.py                     # Task 3 (empty subpackage)
│   ├── segment/__init__.py                # Task 3
│   ├── polarity/__init__.py               # Task 3
│   ├── migration/__init__.py              # Task 3
│   ├── viz/__init__.py                    # Task 3
│   ├── report/__init__.py                 # Task 3
│   ├── interactive/__init__.py            # Task 3
│   ├── validation/__init__.py             # Task 3
│   └── experimental/
│       ├── __init__.py                    # Task 3
│       └── analyses/__init__.py           # Task 3
├── tests/
│   ├── __init__.py                        # Task 17
│   ├── conftest.py                        # Task 17
│   ├── test_config.py                     # Task 5
│   ├── test_contracts.py                  # Task 6
│   ├── test_cli_help.py                   # Task 13
│   ├── test_cli_init_config.py            # Task 15
│   └── test_cli_stubs.py                  # Task 16
└── docs/
    ├── superpowers/                       # already present (spec + this plan)
    └── developer-workflow.md              # Task 20
```

---

## Task 1: Create `pyproject.toml`

**Files:** Create `pyproject.toml`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "quantipy-polarity"
version = "0.1.0"
description = "Single-shot planar polarity quantification from raw microscopy images"
readme = "README.md"
authors = [{name = "mst36", email = "taggartmc@pennmedicine.upenn.edu"}]
license = {text = "MIT"}
requires-python = ">=3.11"
classifiers = [
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Operating System :: MacOS",
  "Operating System :: POSIX :: Linux",
  "Intended Audience :: Science/Research",
  "Topic :: Scientific/Engineering :: Image Processing",
  "Development Status :: 3 - Alpha",
]
dependencies = [
  "click>=8.1,<9",
  "pydantic>=2.5,<3",
  "pyyaml>=6.0,<7",
  "structlog>=24.1,<25",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.4,<9",
  "pytest-cov>=4.1,<7",
  "ruff>=0.3,<1",
]
# Heavy algorithm deps land in Phase 2/3 to keep Phase 1 install minimal.
pipeline = [
  "numpy>=1.26,<2.3",
  "scipy>=1.11,<1.16",
  "pandas>=2.1,<2.4",
  "pyarrow>=14,<19",
  "tifffile>=2024.1,<2026",
  "nd2reader>=3.3,<4",
  "scikit-image>=0.22,<0.25",
  "cellpose>=3.0,<4",
  "matplotlib>=3.8,<3.10",
  "jinja2>=3.1,<4",
  "tqdm>=4.66,<5",
  "requests>=2.31,<3",
]

[project.scripts]
quantipy = "quantipy_polarity.cli:main"

[project.urls]
Repository = "https://github.com/mcleanT/QuantiPy-Polarity"
Issues = "https://github.com/mcleanT/QuantiPy-Polarity/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/quantipy_polarity"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
filterwarnings = ["ignore::DeprecationWarning"]
```

- [ ] **Step 2: Verify TOML parses**

Run: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "build: pyproject.toml with quantipy CLI entry + tiered deps"
```

---

## Task 2: Create `environment.yml`

**Files:** Create `environment.yml`

- [ ] **Step 1: Write `environment.yml`**

```yaml
name: quantipy
channels:
  - conda-forge
  - nodefaults
dependencies:
  - python=3.11
  - pip
  # Scientific stack pinned to ranges matched by pyproject.toml [project.optional-dependencies.pipeline]
  - numpy=1.26.*
  - scipy=1.11.*
  - pandas=2.1.*
  - pyarrow=14.*
  - tifffile=2024.*
  - scikit-image=0.22.*
  - matplotlib=3.8.*
  - jinja2=3.1.*
  - tqdm=4.66.*
  - requests=2.31.*
  # Phase 1 deps (core CLI)
  - click=8.1.*
  - pydantic=2.5.*
  - pyyaml=6.0.*
  - structlog=24.1.*
  # Dev
  - pytest=7.4.*
  - pytest-cov=4.1.*
  - ruff=0.3.*
  # pip-only
  - pip:
      - nd2reader>=3.3,<4
      - cellpose>=3.0,<4
      - -e .
```

- [ ] **Step 2: Commit**

```bash
git add environment.yml
git commit -m "build: environment.yml conda recipe with editable install"
```

---

## Task 3: Create source package skeleton

**Files:**
- Create `src/quantipy_polarity/__init__.py`
- Create `src/quantipy_polarity/_version.py`
- Create `src/quantipy_polarity/{io,segment,polarity,migration,viz,report,interactive,validation,experimental,experimental/analyses}/__init__.py`

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p src/quantipy_polarity/{io,segment,polarity,migration,viz,report,interactive,validation,experimental/analyses}
```

- [ ] **Step 2: Write `src/quantipy_polarity/_version.py`**

```python
"""Single source of truth for the package version. Read by __init__ and pyproject build."""
__version__ = "0.1.0"
```

- [ ] **Step 3: Write `src/quantipy_polarity/__init__.py`**

```python
"""QuantiPy Polarity — single-shot planar polarity quantification.

Public Python API surface is intentionally small in v0.1.0; the CLI is the
documented entry point. Library callers may import from the named submodules
(quantipy_polarity.polarity, .migration, .viz, etc.) at their own risk —
API stability promised only for the per_cell.parquet schema (see contracts.py).
"""
from quantipy_polarity._version import __version__

__all__ = ["__version__"]
```

- [ ] **Step 4: Write empty `__init__.py` for each subpackage**

```python
# src/quantipy_polarity/io/__init__.py
"""I/O for ND2, TIF, and label-mask inputs. Implemented in Phase 2 (masks) and Phase 3 (TIF, ND2)."""
```

Repeat the same one-line-docstring `__init__.py` for `segment/`, `polarity/`, `migration/`, `viz/`, `report/`, `interactive/`, `validation/`, `experimental/`, `experimental/analyses/`, each with a phase-pointer docstring:
- `segment/__init__.py`: `"""Cellpose-SAM wrapper + postprocess. Implemented in Phase 3."""`
- `polarity/__init__.py`: `"""Boundary-PCA polarity quantification. Implemented in Phase 2."""`
- `migration/__init__.py`: `"""Migration-front detection. Implemented in Phase 4."""`
- `viz/__init__.py`: `"""Polarity maps, rose plots, overlays. Implemented in Phase 4."""`
- `report/__init__.py`: `"""Self-contained HTML report. Implemented in Phase 5."""`
- `interactive/__init__.py`: `"""Read-only per-cell viewer. Implemented in Phase 7."""`
- `validation/__init__.py`: `"""QP-vs-Python comparison provenance + figure. Implemented in Phase 6."""`
- `experimental/__init__.py`: `"""Experimental APIs — not stable. Use at your own risk."""`
- `experimental/analyses/__init__.py`: `"""Curated analyses registry. Implemented in Phase 7."""`

- [ ] **Step 5: Verify the package imports**

```bash
pip install -e .
python -c "import quantipy_polarity; print(quantipy_polarity.__version__)"
```
Expected: `0.1.0`

- [ ] **Step 6: Commit**

```bash
git add src/
git commit -m "feat(pkg): src/ layout skeleton with versioned __init__ and phase-tagged subpackages"
```

---

## Task 4: Implement `config.py` — Pydantic schema

**Files:** Create `src/quantipy_polarity/config.py`

- [ ] **Step 1: Write `src/quantipy_polarity/config.py`**

```python
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
                raise ValueError(f"substack_range[0] must be < substack_range[1]; got {self.substack_range}")
        return self


class InputTIF(_InputCommon):
    mode: Literal["tif"]
    z_policy: Literal["mip", "substack", "none"] = "none"
    substack_range: tuple[int, int] | None = None
    channel_membrane: int = Field(ge=0)
    channel_segmentation: int = Field(ge=0)
    pixel_size_um: float = Field(gt=0)


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
```

- [ ] **Step 2: Verify the module imports**

Run: `python -c "from quantipy_polarity.config import Config; print(Config.model_json_schema()['title'])"`
Expected: `Config`

- [ ] **Step 3: Commit**

```bash
git add src/quantipy_polarity/config.py
git commit -m "feat(config): Pydantic schema with input.mode discriminator + validators"
```

---

## Task 5: Tests for `config.py`

**Files:** Create `tests/test_config.py`

- [ ] **Step 1: Write `tests/test_config.py`**

```python
"""Unit tests for the Pydantic configuration schema."""
from pathlib import Path

import pytest
import yaml

from quantipy_polarity.config import (
    Config,
    InputMasks,
    InputND2,
    InputTIF,
)


def _minimal_masks_dict() -> dict:
    return {
        "input": {
            "mode": "masks",
            "path": "./raw",
            "masks_dir": "./masks",
            "pixel_size_um": 0.65,
        }
    }


def _minimal_nd2_dict() -> dict:
    return {
        "input": {
            "mode": "nd2",
            "path": "./raw",
            "channel_membrane": 1,
            "channel_segmentation": 1,
            "pixel_size_um": 0.65,
        }
    }


def test_masks_minimal_config_parses() -> None:
    cfg = Config.model_validate(_minimal_masks_dict())
    assert isinstance(cfg.input, InputMasks)
    assert cfg.input.mode == "masks"
    assert cfg.input.pixel_size_um == 0.65
    assert cfg.project.name == "my_experiment"  # default


def test_nd2_minimal_config_parses() -> None:
    cfg = Config.model_validate(_minimal_nd2_dict())
    assert isinstance(cfg.input, InputND2)
    assert cfg.input.z_policy == "mip"  # default


def test_tif_mode_parses() -> None:
    data = {
        "input": {
            "mode": "tif",
            "path": "./tifs",
            "channel_membrane": 0,
            "channel_segmentation": 0,
            "pixel_size_um": 0.5,
        }
    }
    cfg = Config.model_validate(data)
    assert isinstance(cfg.input, InputTIF)


def test_substack_requires_range() -> None:
    data = _minimal_nd2_dict()
    data["input"]["z_policy"] = "substack"
    with pytest.raises(ValueError, match="substack_range required"):
        Config.model_validate(data)


def test_substack_range_must_be_ordered() -> None:
    data = _minimal_nd2_dict()
    data["input"]["z_policy"] = "substack"
    data["input"]["substack_range"] = [10, 3]
    with pytest.raises(ValueError, match="must be <"):
        Config.model_validate(data)


def test_negative_channel_rejected() -> None:
    data = _minimal_nd2_dict()
    data["input"]["channel_membrane"] = -1
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_pixel_size_must_be_positive() -> None:
    data = _minimal_masks_dict()
    data["input"]["pixel_size_um"] = 0.0
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_round_trip_yaml(tmp_path: Path) -> None:
    cfg = Config.model_validate(_minimal_masks_dict())
    yaml_path = tmp_path / "c.yaml"
    cfg.to_yaml(yaml_path)
    loaded = Config.from_yaml(yaml_path)
    assert loaded.input.mode == "masks"
    assert loaded.input.pixel_size_um == 0.65


def test_unknown_mode_rejected() -> None:
    data = {"input": {"mode": "xyz", "path": "./raw", "pixel_size_um": 0.5}}
    with pytest.raises(ValueError):
        Config.model_validate(data)
```

- [ ] **Step 2: Run tests, expect them to pass**

Run: `pytest tests/test_config.py -v`
Expected: 9 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_config.py
git commit -m "test(config): cover discriminator, validators, yaml round-trip"
```

---

## Task 6: Implement `contracts.py` (per_cell schema for downstream phases)

**Files:** Create `src/quantipy_polarity/contracts.py`, `tests/test_contracts.py`

- [ ] **Step 1: Write `src/quantipy_polarity/contracts.py`**

```python
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
```

- [ ] **Step 2: Write `tests/test_contracts.py`**

```python
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
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_contracts.py -v`
Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/contracts.py tests/test_contracts.py
git commit -m "feat(contracts): PerCellRow + QC bit flags + column constants"
```

---

## Task 7: Implement `cli.py` root with Click groups

**Files:** Create `src/quantipy_polarity/cli.py`

- [ ] **Step 1: Write `src/quantipy_polarity/cli.py`**

```python
"""quantipy CLI root.

Two command groups visible in --help:
  Primary commands (documented in README quickstart): init-config, download-demo,
    run, debug, validate
  Advanced commands (for stage-resume / debugging): ingest, segment, polarity,
    front, aggregate, plot, report, analyze
"""
from __future__ import annotations

import click

from quantipy_polarity import __version__


class _GroupedHelp(click.Group):
    """Click Group subclass that prints commands under Primary / Advanced headers."""

    PRIMARY: tuple[str, ...] = (
        "init-config",
        "download-demo",
        "run",
        "debug",
        "validate",
    )

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        commands = []
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            commands.append((name, cmd))
        primary = [(n, c) for n, c in commands if n in self.PRIMARY]
        advanced = [(n, c) for n, c in commands if n not in self.PRIMARY]
        for label, rows in (("Primary commands", primary), ("Advanced commands", advanced)):
            if not rows:
                continue
            with formatter.section(label):
                formatter.write_dl(
                    [(n, (c.get_short_help_str(limit=80) or "")) for n, c in rows]
                )


@click.group(cls=_GroupedHelp, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="quantipy")
def main() -> None:
    """QuantiPy Polarity — planar polarity quantification from microscopy images."""


# Subcommand modules register themselves on import.
from quantipy_polarity import _stubs as _stubs  # noqa: E402,F401
from quantipy_polarity import _cli_init_config as _cli_init_config  # noqa: E402,F401
```

- [ ] **Step 2: Verify a smoke import**

Run: `python -c "from quantipy_polarity.cli import main; print(type(main).__name__)"`
Expected: `Group` (or subclass — actually `_GroupedHelp`). The exact print result is `_GroupedHelp`.

Note: this step will fail until Tasks 8 and 16 land because `_cli_init_config` and `_stubs` don't exist yet. That's expected — proceed to next task and re-verify after Task 16.

- [ ] **Step 3: Commit**

```bash
git add src/quantipy_polarity/cli.py
git commit -m "feat(cli): Click root group with primary/advanced --help split"
```

---

## Task 8: Implement `init-config` subcommand module

**Files:** Create `src/quantipy_polarity/_cli_init_config.py`

- [ ] **Step 1: Write `src/quantipy_polarity/_cli_init_config.py`**

```python
"""`quantipy init-config` — write a mode-specific YAML scaffold.

Registers itself on import (see cli.py footer).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import click

from quantipy_polarity.cli import main
from quantipy_polarity.config import (
    Config,
    InputMasks,
    InputND2,
    InputTIF,
    ProjectConfig,
)


def _build_config(mode: Literal["nd2", "tif", "masks"]) -> Config:
    project = ProjectConfig(name="my_experiment", output_dir=Path("./results"))
    if mode == "nd2":
        return Config(
            project=project,
            input=InputND2(
                mode="nd2",
                path=Path("./raw"),
                z_policy="mip",
                channel_membrane=1,
                channel_segmentation=1,
                pixel_size_um=0.65,
            ),
        )
    if mode == "tif":
        return Config(
            project=project,
            input=InputTIF(
                mode="tif",
                path=Path("./raw"),
                z_policy="none",
                channel_membrane=0,
                channel_segmentation=0,
                pixel_size_um=0.65,
            ),
        )
    return Config(
        project=project,
        input=InputMasks(
            mode="masks",
            path=Path("./membrane_tifs"),
            masks_dir=Path("./label_masks"),
            pixel_size_um=0.65,
        ),
    )


@main.command("init-config", short_help="Scaffold a config YAML for a given input mode")
@click.option(
    "--mode",
    type=click.Choice(["nd2", "tif", "masks"], case_sensitive=False),
    required=True,
    help="Which input mode the config should be wired for.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("config.yaml"),
    show_default=True,
    help="Path to write the YAML.",
)
@click.option("--force", is_flag=True, help="Overwrite if --output already exists.")
def init_config_cmd(mode: str, output: Path, force: bool) -> None:
    """Write a Pydantic-valid YAML scaffold for the chosen input mode.

    Example: quantipy init-config --mode masks --output config.yaml
    """
    if output.exists() and not force:
        raise click.ClickException(
            f"{output} already exists. Pass --force to overwrite."
        )
    cfg = _build_config(mode.lower())  # type: ignore[arg-type]
    cfg.to_yaml(output)
    click.echo(f"Wrote {output} (mode={mode})")
```

- [ ] **Step 2: Smoke-test from shell**

Run:
```bash
quantipy init-config --mode masks --output /tmp/_qp_test_config.yaml
cat /tmp/_qp_test_config.yaml
rm /tmp/_qp_test_config.yaml
```

Expected: `Wrote /tmp/_qp_test_config.yaml (mode=masks)` followed by a YAML document containing `mode: masks` and `pixel_size_um: 0.65`.

- [ ] **Step 3: Commit**

```bash
git add src/quantipy_polarity/_cli_init_config.py
git commit -m "feat(cli): init-config subcommand for nd2/tif/masks modes"
```

---

## Task 9: Implement stub subcommands (`_stubs.py`)

**Files:** Create `src/quantipy_polarity/_stubs.py`

- [ ] **Step 1: Write `src/quantipy_polarity/_stubs.py`**

```python
"""Phase 1 stubs for all subcommands not yet implemented.

Each stub registers a Click command that exits with code 2 and a clear
"not implemented in Phase 1" message pointing to the future phase.
This lets `quantipy --help` show the full surface area immediately while
keeping each phase's implementation scope bounded.
"""
from __future__ import annotations

import click

from quantipy_polarity.cli import main


_STUBS: dict[str, tuple[str, str]] = {
    # name: (short_help, phase_pointer)
    "run": (
        "Single-shot: input → all outputs",
        "Phase 5 (run orchestration + resume/atomic-writes)",
    ),
    "download-demo": (
        "Pull demo bundle from latest GitHub Release",
        "Phase 6 (demo bundle + Release workflow)",
    ),
    "debug": (
        "Open the read-only per-cell viewer",
        "Phase 7 (interactive viewer)",
    ),
    "validate": (
        "Regenerate QP-vs-Python comparison figure",
        "Phase 6 (validation + provenance)",
    ),
    "ingest": (
        "[Advanced] nd2/tif → normalized per-FOV TIFs",
        "Phase 2 (masks) / Phase 3 (tif/nd2)",
    ),
    "segment": (
        "[Advanced] Cellpose-SAM → label masks",
        "Phase 3 (segmentation)",
    ),
    "polarity": (
        "[Advanced] Label masks + membrane → per-cell axes",
        "Phase 2 (boundary-PCA)",
    ),
    "front": (
        "[Advanced] Migration-front detection (auto only in v0.1.0)",
        "Phase 4 (migration front)",
    ),
    "aggregate": (
        "[Advanced] Per-FOV parquets → experiment parquet",
        "Phase 2 (aggregation)",
    ),
    "plot": (
        "[Advanced] Regenerate plots from aggregated parquet",
        "Phase 4 (visualization)",
    ),
    "report": (
        "[Advanced] Regenerate HTML report from a run dir",
        "Phase 5 (HTML report)",
    ),
    "analyze": (
        "[Advanced] Run a curated experimental analysis by name",
        "Phase 7 (experimental analyses)",
    ),
}


def _make_stub(name: str, short_help: str, phase: str) -> click.Command:
    @click.command(name, short_help=short_help)
    def _stub(**_: object) -> None:
        raise click.ClickException(
            f"`quantipy {name}` is not implemented in v0.1.0 Phase 1. "
            f"It will land in {phase}. "
            f"See docs/superpowers/plans/ for the phased roadmap."
        )

    return _stub


for _name, (_short, _phase) in _STUBS.items():
    main.add_command(_make_stub(_name, _short, _phase))
```

- [ ] **Step 2: Smoke-test from shell**

Run: `quantipy --help`

Expected output (abbreviated, exact wording may vary):
```
Usage: quantipy [OPTIONS] COMMAND [ARGS]...

  QuantiPy Polarity — planar polarity quantification from microscopy images.

Options:
  --version
  -h, --help  Show this message and exit.

Primary commands:
  init-config       Scaffold a config YAML for a given input mode
  download-demo     Pull demo bundle from latest GitHub Release
  run               Single-shot: input → all outputs
  debug             Open the read-only per-cell viewer
  validate          Regenerate QP-vs-Python comparison figure

Advanced commands:
  ingest, segment, polarity, front, aggregate, plot, report, analyze
```

- [ ] **Step 3: Verify a stub call fails clearly**

Run: `quantipy run --help`
Expected: exit 0, help text including the short help and Click's standard usage block.

Run: `quantipy run; echo "exit=$?"`
Expected: error message containing `not implemented in v0.1.0 Phase 1` and `exit=1` (Click's `ClickException` default exit code).

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/_stubs.py
git commit -m "feat(cli): stub all non-init-config subcommands with phase pointers"
```

---

## Task 10: Add `tests/__init__.py` and `tests/conftest.py`

**Files:** Create `tests/__init__.py`, `tests/conftest.py`

- [ ] **Step 1: Write `tests/__init__.py`**

```python
# Tests package marker; lets pytest discover the package and avoids namespace warnings.
```

- [ ] **Step 2: Write `tests/conftest.py`**

```python
"""Shared pytest fixtures and configuration."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Absolute path to the repo root (the directory containing pyproject.toml)."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("pyproject.toml not found above tests/")
```

- [ ] **Step 3: Verify pytest still passes**

Run: `pytest -v`
Expected: All Tasks-5/6 tests still pass.

- [ ] **Step 4: Commit**

```bash
git add tests/__init__.py tests/conftest.py
git commit -m "test: package marker + repo_root fixture"
```

---

## Task 11: CLI help tests

**Files:** Create `tests/test_cli_help.py`

- [ ] **Step 1: Write `tests/test_cli_help.py`**

```python
"""Tests for the top-level `quantipy --help` and `--version`."""
from click.testing import CliRunner

from quantipy_polarity import __version__
from quantipy_polarity.cli import main


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_both_groups() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Primary commands" in result.output
    assert "Advanced commands" in result.output


def test_help_lists_primary_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    for cmd in ("init-config", "download-demo", "run", "debug", "validate"):
        assert cmd in result.output


def test_help_lists_advanced_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    for cmd in ("ingest", "segment", "polarity", "front", "aggregate", "plot", "report", "analyze"):
        assert cmd in result.output


def test_short_help_flag_works() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["-h"])
    assert result.exit_code == 0
    assert "QuantiPy Polarity" in result.output
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_cli_help.py -v`
Expected: 5 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli_help.py
git commit -m "test(cli): cover --version, --help, command group split"
```

---

## Task 12: `init-config` tests

**Files:** Create `tests/test_cli_init_config.py`

- [ ] **Step 1: Write `tests/test_cli_init_config.py`**

```python
"""Tests for `quantipy init-config`."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config, InputMasks, InputND2, InputTIF


@pytest.mark.parametrize(
    "mode,expected_cls",
    [("masks", InputMasks), ("nd2", InputND2), ("tif", InputTIF)],
)
def test_init_config_writes_valid_yaml(tmp_path: Path, mode: str, expected_cls: type) -> None:
    runner = CliRunner()
    out = tmp_path / f"cfg_{mode}.yaml"
    result = runner.invoke(main, ["init-config", "--mode", mode, "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    cfg = Config.from_yaml(out)
    assert isinstance(cfg.input, expected_cls)


def test_init_config_refuses_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "cfg.yaml"
    out.write_text("placeholder")
    result = runner.invoke(main, ["init-config", "--mode", "masks", "--output", str(out)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_init_config_force_overwrites(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "cfg.yaml"
    out.write_text("placeholder")
    result = runner.invoke(main, ["init-config", "--mode", "masks", "--output", str(out), "--force"])
    assert result.exit_code == 0
    cfg = Config.from_yaml(out)
    assert isinstance(cfg.input, InputMasks)


def test_init_config_rejects_invalid_mode() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["init-config", "--mode", "garbage", "--output", "x.yaml"])
    assert result.exit_code != 0
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_cli_init_config.py -v`
Expected: 6 passed (3 parametrized + 3 explicit).

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli_init_config.py
git commit -m "test(cli): init-config writes valid yaml + overwrite behavior"
```

---

## Task 13: Stub subcommand tests

**Files:** Create `tests/test_cli_stubs.py`

- [ ] **Step 1: Write `tests/test_cli_stubs.py`**

```python
"""Tests for the Phase 1 stub subcommands."""
import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity._stubs import _STUBS


@pytest.mark.parametrize("cmd_name", list(_STUBS.keys()))
def test_stub_exits_nonzero_with_phase_message(cmd_name: str) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [cmd_name])
    assert result.exit_code != 0, f"{cmd_name} should exit non-zero in Phase 1"
    assert "not implemented in v0.1.0 Phase 1" in result.output


@pytest.mark.parametrize("cmd_name", list(_STUBS.keys()))
def test_stub_help_works(cmd_name: str) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [cmd_name, "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_all_stubs_have_phase_pointers() -> None:
    for cmd_name, (_short, phase) in _STUBS.items():
        assert "Phase" in phase, f"{cmd_name} stub missing phase pointer"
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_cli_stubs.py -v`
Expected: 25 passed (12 stubs × 2 + 1 metadata test).

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli_stubs.py
git commit -m "test(cli): every stub exits clearly + has phase pointer"
```

---

## Task 14: Full test suite verification

**Files:** none

- [ ] **Step 1: Run the full suite**

Run: `pytest -v`
Expected: All tests from Tasks 5, 6, 11, 12, 13 pass. Total ~44 tests passing.

- [ ] **Step 2: Run with coverage**

Run: `pytest --cov=quantipy_polarity --cov-report=term-missing`
Expected: Coverage for `config.py`, `contracts.py`, `_cli_init_config.py`, `_stubs.py`, `cli.py` ≥ 85% each.

If any file is < 85%, stop and add tests covering the uncovered lines before proceeding.

- [ ] **Step 3: No commit yet — proceeds to Task 15.**

---

## Task 15: CLAUDE.md + .claude/ scaffolding

**Files:** Create `CLAUDE.md`, `.claude/settings.json`, `.claude/commands/quantipy-run.md`, `.claude/commands/quantipy-debug-fov.md`, `.claude/commands/quantipy-front-qc.md`

- [ ] **Step 1: Write `CLAUDE.md`**

```markdown
# QuantiPy Polarity — Claude Code Orientation

This file orients Claude Code sessions opened in this repo. The tool does NOT
require Claude Code — see README.md for the standard CLI workflow.

## What this is

QuantiPy Polarity is a Python CLI tool for planar-polarity quantification from
microscopy images. The `quantipy` command is installed by
`pip install -e .` (or via the conda recipe in `environment.yml`).

## CLI command map

| Command | Status (Phase 1) | Purpose |
|---|---|---|
| `quantipy init-config --mode {nd2,tif,masks}` | implemented | Scaffold a config YAML |
| `quantipy --version` / `--help` | implemented | CLI introspection |
| `quantipy run` | stubbed (Phase 5) | Single-shot pipeline |
| `quantipy ingest` / `segment` / `polarity` / `front` / `aggregate` / `plot` / `report` | stubbed (Phases 2–5) | Stage-resume commands |
| `quantipy debug` | stubbed (Phase 7) | Read-only per-cell viewer |
| `quantipy validate` | stubbed (Phase 6) | QP-vs-Python figure regeneration |
| `quantipy download-demo` | stubbed (Phase 6) | Pull demo bundle from Release |
| `quantipy analyze <name>` | stubbed (Phase 7) | Experimental analyses |

## Where things live

- `src/quantipy_polarity/cli.py` — Click root, `_GroupedHelp` class
- `src/quantipy_polarity/config.py` — Pydantic schema (input mode discriminator)
- `src/quantipy_polarity/contracts.py` — `PerCellRow` schema, QC bit flags, coord conventions
- `docs/superpowers/specs/` — design spec + codex review
- `docs/superpowers/plans/` — phased implementation plans
- `tests/` — pytest suite

## Guard

Read `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` (rev 1)
before modifying any module — the spec defines stable contracts (per_cell
schema, coord conventions, axial angle range) that downstream phases depend on.

## Slash commands available

`/quantipy-run`, `/quantipy-debug-fov`, `/quantipy-front-qc` — see `.claude/commands/`.
```

- [ ] **Step 2: Write `.claude/settings.json`**

```json
{
  "permissions": {
    "allow": [
      "Bash(quantipy *)",
      "Bash(pytest *)",
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(grep *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)"
    ]
  }
}
```

- [ ] **Step 3: Write the three slash command files**

`.claude/commands/quantipy-run.md`:

```markdown
---
description: Run the QuantiPy Polarity single-shot pipeline on a folder of images
---

Run `quantipy run --config ./config.yaml` if a config.yaml is present in the
current working directory. If not found, run `quantipy init-config --mode masks`
(or the user-specified mode) first, then ask the user to confirm before
running `quantipy run`. Note: `quantipy run` is stubbed in Phase 1 — it will
exit non-zero with a "not yet implemented" message until Phase 5 lands.
```

`.claude/commands/quantipy-debug-fov.md`:

```markdown
---
description: Open the read-only per-cell viewer on a specific FOV
---

Run `quantipy debug --results ./results --fov $1` if a FOV identifier is
provided as $1; otherwise run `quantipy debug --results ./results` and let
the viewer's dropdown pick the FOV. Note: `quantipy debug` is stubbed in
Phase 1; will land in Phase 7.
```

`.claude/commands/quantipy-front-qc.md`:

```markdown
---
description: Regenerate static migration-front QC overlays
---

Run `quantipy front --auto --qc --resume --config ./config.yaml`. This
regenerates per-FOV QC overlays into results/04_migration/qc/ and keeps the
previous overlays in qc_prev/ for visual diffing after editing
migration.* config values. Note: `quantipy front` is stubbed in Phase 1;
will land in Phase 4.
```

- [ ] **Step 4: Write `docs/developer-workflow.md`**

```markdown
# Developer Workflow

This page describes optional integrations for development workflows. **None
are required to use the tool** — `quantipy` is a standard Python CLI.

## Claude Code integration

If you use Claude Code, the repo ships:
- `CLAUDE.md` — orients a session opened in this directory
- `.claude/settings.json` — pre-approves safe read-only commands so you avoid
  permission prompts on first run; writes/pushes/installs still prompt
- `.claude/commands/quantipy-run.md` — `/quantipy-run` slash command
- `.claude/commands/quantipy-debug-fov.md` — `/quantipy-debug-fov [FOV]`
- `.claude/commands/quantipy-front-qc.md` — `/quantipy-front-qc`

## Running tests

```bash
pip install -e .[dev]
pytest -v
```

## Running the fast-tier CI locally

```bash
pytest tests/
```

The fast tier deliberately excludes Cellpose-SAM (which lands in Phase 3 and
is gated on the nightly CI tier).
```

- [ ] **Step 5: Verify all files exist**

Run: `ls CLAUDE.md .claude/settings.json .claude/commands/ docs/developer-workflow.md`
Expected: every path printed without errors.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md .claude/ docs/developer-workflow.md
git commit -m "docs(cc): CLAUDE.md + slash commands + developer-workflow page"
```

---

## Task 16: CONTRIBUTING.md

**Files:** Create `CONTRIBUTING.md`

- [ ] **Step 1: Write `CONTRIBUTING.md`**

```markdown
# Contributing to QuantiPy Polarity

Thanks for your interest. The project is in early development (v0.1.0,
phased rollout — see `docs/superpowers/plans/`).

## Development setup

```bash
git clone https://github.com/mcleanT/QuantiPy-Polarity.git
cd QuantiPy-Polarity
# Option A: conda (recommended for the full algorithm stack)
conda env create -f environment.yml
conda activate quantipy
# Option B: venv + pip
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,pipeline]
```

## Running tests

```bash
pytest -v
```

The fast tier (CI default) excludes Cellpose-SAM. The slow tier runs nightly
and is allowed to flake without blocking releases.

## Pull requests

- Open against `main`.
- Reference the spec section your change affects:
  `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md`.
- New code requires tests. Coverage must stay ≥ 85% for modules you touch.
- The `per_cell.parquet` schema in `src/quantipy_polarity/contracts.py` is
  a SemVer-stable public API; column rename/removal is a major version bump.

## Reporting bugs

GitHub issues. Include:
- `quantipy --version`
- A minimal config + input bundle (synthetic is fine)
- The full traceback
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: CONTRIBUTING.md with setup, tests, PR guidance"
```

---

## Task 17: Update README.md (post-Phase-1 status)

**Files:** Modify `README.md`

- [ ] **Step 1: Replace the existing `README.md` contents**

```markdown
# QuantiPy Polarity

Single-shot planar polarity quantification from raw microscopy images — a
Python implementation and packaging of the QuantifyPolarity (QP) PCA
cell-by-cell polarity pipeline, plus migration-front detection, rose plots,
polarity vector maps, and a self-contained HTML report.

## Status: v0.1.0 Phase 1 (scaffolding) complete

This repository now installs and exposes the full CLI surface, with most
subcommands stubbed for later phases. See `docs/superpowers/plans/` for the
phased roadmap.

- ✅ Phase 1 — CLI shell, config schema, init-config, fast-tier CI
- ⏳ Phase 2 — Masks → polarity (smallest viable pipeline)
- ⏳ Phase 3 — TIF / ND2 ingest + Cellpose segmentation
- ⏳ Phase 4 — Migration front + visualization
- ⏳ Phase 5 — Run orchestration + HTML report + resume/atomic-writes
- ⏳ Phase 6 — Validation + demo bundle + GitHub Release
- ⏳ Phase 7 — Interactive viewer + experimental analyses + docs
- ⏳ Phase 8 — Research-dir upstream migration

## Install (Phase 1 — CLI only)

```bash
git clone https://github.com/mcleanT/QuantiPy-Polarity.git
cd QuantiPy-Polarity
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

## Verify

```bash
quantipy --version          # 0.1.0
quantipy --help             # primary + advanced command groups
quantipy init-config --mode masks --output config.yaml
cat config.yaml             # mode: masks, valid Pydantic schema
quantipy run                # stubbed: "not implemented in v0.1.0 Phase 1"
```

## Planned full quickstart (lands at Phase 6)

```bash
conda env create -f environment.yml && conda activate quantipy && pip install -e .
quantipy download-demo
quantipy init-config --mode masks --output config.yaml
quantipy run --config config.yaml --output ./results
open ./results/report.html
```

## Design + reviews

- Design spec (rev 1): `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md`
- Adversarial review (codex / gpt-5.5): `docs/superpowers/specs/2026-05-26-quantipy-polarity-design-codex-review.txt`
- Phase 1 plan: `docs/superpowers/plans/2026-05-26-quantipy-polarity-phase1-scaffolding.md`

## License

MIT — see [`LICENSE`](LICENSE).

## Citation

A `CITATION.cff` will be added before the v0.1.0 tag. The original
QuantifyPolarity tool this project reimplements is cited there.

## Developer workflow

See [`docs/developer-workflow.md`](docs/developer-workflow.md) for optional
Claude Code integrations and test/CI setup.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): post-Phase-1 status, install, verify, planned quickstart"
```

---

## Task 18: GitHub Actions — fast-tier CI

**Files:** Create `.github/workflows/ci.yml`

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: CI (fast)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: pytest (Python ${{ matrix.python-version }}, ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]

      - name: Lint
        run: ruff check src tests

      - name: Format check
        run: ruff format --check src tests

      - name: Test
        run: pytest -v --cov=quantipy_polarity --cov-report=term-missing
```

- [ ] **Step 2: Format-check locally before committing**

Run: `ruff format src tests && ruff check src tests`
Expected: no errors.

If ruff reports issues, fix them and rerun before committing.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: fast-tier workflow (pytest + ruff, 3.11+3.12, ubuntu+macos)"
```

---

## Task 19: GitHub Actions — nightly skeleton

**Files:** Create `.github/workflows/ci-nightly.yml`

- [ ] **Step 1: Write `.github/workflows/ci-nightly.yml`**

```yaml
name: CI (nightly slow tier)

on:
  schedule:
    - cron: "17 7 * * *"  # 07:17 UTC daily
  workflow_dispatch: {}

jobs:
  nightly:
    name: nightly stub (no slow tests until Phase 3)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install
        run: pip install -e .[dev]

      - name: Run fast suite (placeholder; Phase 3 adds segmentation tests here)
        run: pytest -v
        continue-on-error: true

      - name: Notice
        run: echo "Phase 3 will add Cellpose-SAM segmentation tests to this job."
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci-nightly.yml
git commit -m "ci: nightly workflow skeleton (Phase 3 will populate Cellpose tests)"
```

---

## Task 20: Push and verify CI

**Files:** none

- [ ] **Step 1: Push to remote**

```bash
git push origin main
```

- [ ] **Step 2: Verify CI on GitHub**

Open `https://github.com/mcleanT/QuantiPy-Polarity/actions` in a browser. Wait for the `CI (fast)` workflow to complete.

Expected: all 4 jobs (Python 3.11 + 3.12 × Ubuntu + macOS) green.

If any job fails:
- Read the failing job's log.
- Reproduce locally (e.g., `pytest -v` if a test broke; `ruff check src tests` if a lint broke).
- Fix in a new commit referencing the failure mode (`ci: fix ruff E501 in cli.py`).
- Push and re-verify.

- [ ] **Step 3: No additional commit unless a fix was needed.**

---

## Task 21: Phase 1 acceptance verification

**Files:** none

- [ ] **Step 1: Run the Phase 1 acceptance script**

Verify each acceptance criterion from the plan header against a fresh clone:

```bash
# In a fresh shell, no quantipy env active
cd /tmp && rm -rf qp_accept && git clone https://github.com/mcleanT/QuantiPy-Polarity.git qp_accept
cd qp_accept
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]                                                    # criterion 1
quantipy --version                                                       # criterion 2: 0.1.0
quantipy --help                                                          # criterion 3: both groups
quantipy init-config --mode masks --output /tmp/_a.yaml && cat /tmp/_a.yaml  # criterion 4
pytest -v                                                                # criterion 5
python -c "from quantipy_polarity.config import Config; print(Config.from_yaml('/tmp/_a.yaml').input.mode)"  # criterion 6: masks
quantipy run 2>&1 | grep "not implemented"                               # criterion 7
```

Expected: every command succeeds (returns exit 0 except the final `quantipy run` which exits non-zero with the expected message).

If any criterion fails, **do not declare Phase 1 complete**. Fix the failure in a new commit and re-run.

- [ ] **Step 2: Tag a Phase 1 milestone**

```bash
git tag -a phase-1-complete -m "Phase 1: scaffolding + config + CLI shell complete"
git push origin phase-1-complete
```

- [ ] **Step 3: Final commit (no code change, just marker)** — skipped; tag is the marker.

---

## Self-review

**Spec coverage (against the rev 1 design spec):**

| Spec section | Phase-1 coverage |
|---|---|
| §1 Purpose | Out of scope for Phase 1; full purpose realized across phases. |
| §2 Goals — installable | Task 1 (pyproject.toml), Task 20 (CI verifies install). |
| §2 Goals — three input entry points | Config supports all three modes (Task 4); functionality stubbed (Task 9). |
| §2 Goals — claude-code dev workflow | Task 15. |
| §2a Assumptions and validity | Documented as a docs item in Phase 7; not Phase 1. |
| §3 Decisions table | All decisions baked into Phase 1 scaffolding (license, layout, modes). |
| §4 Repository layout | Tasks 1–3, 15, 16, 17, 18, 19. |
| §5 CLI surface | Tasks 7–9. Primary/advanced grouping in Task 7. init-config in Task 8. Stubs in Task 9. |
| §6 Configuration schema | Tasks 4–5. |
| §7 Output layout + resume semantics | Phase 5 (stubs in Phase 1). |
| §8 Interactive viewers | Phase 7 (stubs in Phase 1). |
| §9 Validation evidence | Phase 6 (stubs in Phase 1). |
| §10 Claude-Code dev workflow | Task 15. |
| §11 Distribution / pyproject / env | Tasks 1, 2, 18. |
| §12 Sample data | Phase 6 (stub for `download-demo` in Phase 1). |
| §13 Testing + CI | Fast tier in Tasks 18, 20; nightly skeleton in Task 19. |
| §14 Documentation | README updated (Task 17); CONTRIBUTING (Task 16); developer-workflow (Task 15); other docs in Phase 7. |
| §15 Carve-out | Phase 8. |
| §16 Module-level lift table | Subpackage skeletons in Task 3; implementations in Phases 2–7. |
| §17 Open items | Author name now resolved in pyproject.toml (Task 1); other items resolved in later phases. |
| §18 Acceptance criteria | Task 21 verifies Phase 1's subset. |

No spec sections lack coverage for Phase 1. Sections deferred to later phases are explicitly noted.

**Placeholder scan:** every step has full, exact code. No "TBD", "fill in later", or "similar to Task N" patterns.

**Type consistency:**
- `Config`, `InputND2`, `InputTIF`, `InputMasks` defined in Task 4, used in Tasks 5, 8, 12. Field names match (`channel_membrane`, `pixel_size_um`, `mode`, `path`, etc.).
- `_STUBS` dict in Task 9, iterated in Task 13's tests. Key set matches.
- `main` group from `cli.py` (Task 7) referenced by `_cli_init_config.py` (Task 8) and `_stubs.py` (Task 9). All three modules side-effect-register subcommands on the same `main` object.
- `_GroupedHelp.PRIMARY` (Task 7) names exactly the 5 commands implemented or stubbed under that label (Task 9's stub names + `init-config`).
- `PerCellRow` (Task 6) fields match the per_cell parquet schema documented in spec §16 data contracts.

No drift detected. Phase 1 plan is internally consistent and aligns with the spec.
