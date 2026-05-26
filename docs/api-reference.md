# API Reference

This document covers the stable public Python API for users who want to call
QuantiPy Polarity from a notebook or script without using the CLI.

> **Note:** The `quantipy_polarity.experimental.*` namespace is intentionally
> unstable and is **not** covered here.  Its signatures may change without
> notice between minor versions.

For the equivalent CLI commands see [docs/cli-reference.md](cli-reference.md).

---

## `quantipy_polarity.Config`

```python
from quantipy_polarity import Config
```

A Pydantic `BaseModel` that represents a fully-validated experiment
configuration.  All pipeline functions accept a `Config` instance rather than
a raw dict or path.

### Class hierarchy

```
Config
├── project:   ProjectConfig
├── input:     InputND2 | InputTIF | InputMasks
├── segment:   SegmentConfig
├── polarity:  PolarityConfig
├── migration: MigrationConfig
├── viz:       VizConfig
└── report:    ReportConfig
```

### Class method: `Config.from_yaml`

```python
@classmethod
def from_yaml(cls, path: Path | str) -> "Config": ...
```

Load and validate a config from a YAML file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `Path \| str` | Path to a quantipy YAML config file. |

**Returns** a validated `Config` instance.

**Raises** `pydantic.ValidationError` if the file fails schema validation.

**Example**

```python
from quantipy_polarity import Config

cfg = Config.from_yaml("config.yaml")
print(cfg.project.name)          # "my_experiment"
print(cfg.input.mode)            # "masks"
print(cfg.polarity.n_pca_comps)  # 2
```

### Instance method: `Config.to_yaml`

```python
def to_yaml(self, path: Path | str) -> None: ...
```

Serialise the config back to a YAML file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `Path \| str` | Destination path. |

---

## `quantipy_polarity.pipeline.run_pipeline`

```python
from quantipy_polarity.pipeline import run_pipeline
```

Execute the full pipeline (or a named subset of stages) for a single
experiment config.

### Signature

```python
def run_pipeline(
    cfg: Config,
    out_dir: Path,
    *,
    force: bool = False,
    stages: list[str] | None = None,
) -> None: ...
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cfg` | `Config` | *(required)* | Validated Config object. |
| `out_dir` | `Path` | *(required)* | Base output directory.  Created if absent. |
| `force` | `bool` | `False` | If `True`, ignore all stage-status caches and re-run every stage from scratch. |
| `stages` | `list[str] \| None` | `None` | Stage names to run (`None` = all stages in canonical order). |

### Returns

`None`.  All outputs are written to `out_dir`.

### Raises

| Exception | When |
|-----------|------|
| `RuntimeError` | Any stage fails (status `failed` is written to the stage JSON before raising). |
| `ValueError` | `stages` contains an unrecognised stage name. |

### Example

```python
from pathlib import Path
from quantipy_polarity import Config
from quantipy_polarity.pipeline import run_pipeline

cfg = Config.from_yaml("config.yaml")
run_pipeline(cfg, Path("./results"))

# Run only the figures and report stages
run_pipeline(cfg, Path("./results"), stages=["figures", "report"])
```

---

## `quantipy_polarity.interactive.build_viewer`

```python
from quantipy_polarity.interactive import build_viewer
```

Build a self-contained HTML per-cell viewer from a completed run directory.
The resulting HTML file can be opened in any browser without a web server.
See [docs/interactive-viewer.md](interactive-viewer.md) for a full usage guide.

### Signature

```python
def build_viewer(
    results_dir: Path,
    output_path: Path,
    *,
    fov: str | None = None,
) -> None: ...
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `results_dir` | `Path` | *(required)* | Path to a completed quantipy run directory.  Must contain `05_aggregated/per_cell.parquet` and `03_polarity/maps/*.png`. |
| `output_path` | `Path` | *(required)* | Destination path for the HTML file.  Parent directory must exist. |
| `fov` | `str \| None` | `None` | If given, only embed data for this FOV (default: all FOVs). |

### Returns

`None`.  The HTML file is written to `output_path`.

### Raises

| Exception | When |
|-----------|------|
| `FileNotFoundError` | `results_dir` is missing `per_cell.parquet` or the maps directory. |
| `ValueError` | `per_cell.parquet` has no rows or no recognised columns. |

### Example

```python
from pathlib import Path
from quantipy_polarity.interactive import build_viewer

build_viewer(
    results_dir=Path("./demo_results"),
    output_path=Path("./demo_results/viewer.html"),
)
# open ./demo_results/viewer.html in a browser

# Single-FOV viewer
build_viewer(
    results_dir=Path("./demo_results"),
    output_path=Path("./fov01_viewer.html"),
    fov="FOV_01",
)
```

---

## `quantipy_polarity.validation.run_validation`

```python
from quantipy_polarity.validation import run_validation
```

Load paired per-cell parquets from the original QuantifyPolarity (QP) tool
and from this Python implementation, match cells by centroid distance, and
compute agreement metrics (R², slope).

For full methodology see [docs/validation.md](validation.md).

### Signature

```python
def run_validation(
    qp_path: Path | str,
    py_path: Path | str,
    output_dir: Path | str,
    *,
    tolerance_px: float = 5.0,
) -> ValidationResult: ...
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `qp_path` | `Path \| str` | *(required)* | Path to `qp_results.parquet`. |
| `py_path` | `Path \| str` | *(required)* | Path to `python_results.parquet`. |
| `output_dir` | `Path \| str` | *(required)* | Directory for the output figure files. |
| `tolerance_px` | `float` | `5.0` | Max centroid distance (pixels) for a valid cell match. |

### Returns

A `ValidationResult` dataclass with fields:

| Field | Type | Description |
|-------|------|-------------|
| `r2` | `float` | Pearson R² between QP and Python polarity magnitudes. |
| `slope` | `float` | OLS slope of the regression. |
| `n_matched` | `int` | Number of cells successfully matched. |
| `n_qp` | `int` | Total cells in QP parquet. |
| `n_py` | `int` | Total cells in Python parquet. |
