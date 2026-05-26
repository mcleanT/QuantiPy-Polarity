# QuantiPy Polarity — Phase 3: TIF/ND2 Ingest + Cellpose-SAM Segmentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TIF and ND2 ingest paths upstream of segmentation, plus a Cellpose-SAM segmentation stage, so `quantipy segment` can take raw microscopy images (TIF or ND2) and produce Phase-2-compatible label masks + membrane TIFs on disk — without requiring the user to pre-segment.

**Architecture:** Three new modules work in concert. `io/tif.py` and `io/nd2.py` yield typed FOV objects (same shape pattern as Phase 2's `MaskFOV`). `segment/cellpose_sam.py` wraps the Cellpose-SAM API lifted from `pipeline/lib/segmentation.py` and returns validated `uint16` label arrays. A new `_cli_segment.py` wires these into `quantipy segment`. The `segment` stub in `_stubs.py` is removed. `quantipy ingest` remains a stub (it is only needed for the `run` orchestration, which lands in Phase 5).

**Tech Stack:** Python 3.11+, numpy 1.26+, scipy 1.11+, scikit-image 0.22+, tifffile 2024+, nd2reader 3.3+, cellpose 3.0+, Click 8.1+, Pydantic 2.5+, structlog 24+, tqdm 4.66+.

**Spec source:** `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` (rev 1), §§3 (layout), 4 (CLI), 5 (config), 6 (stage contracts), 7 (outputs), 13 (CI), 16 (module lift table).

**Working directory:** clone of `https://github.com/mcleanT/QuantiPy-Polarity`. Phase 2 already landed (tag `phase-2-complete`). Working tree should be clean on `main`. 82 tests passing.

**Lift sources** (research repo, read-only references):
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/lib/segmentation.py` — real Cellpose-SAM wrapper (`segment()` → `(masks, meta)`)
- `Hughes Lab/Sachin/Polarity Quantification/pipeline/01_nd2_to_tif.py` — ND2 ingest orchestrator: `_extract_fov()` (returns `(C, Z, H, W)`), `_z_project()` (mip / fixed_plane / substack_mip)

**Acceptance criteria for Phase 3 completion:**
1. `quantipy segment --config config.yaml --input <tif_dir> --output <out_dir>` produces `<out_dir>/02_segmentation/<fov_id>_mask.tif` (uint16) + `<fov_id>_membrane.tif` (uint16) for every FOV.
2. `quantipy segment` with `input.mode = nd2` does the same starting from `.nd2` files.
3. `quantipy segment` output dirs can be passed directly as `--input` to `quantipy polarity` (Phase 2 contract honored).
4. `quantipy segment --help` no longer shows "(Phase 3 stub)" message — it is a real subcommand.
5. Nightly CI installs `.[dev,pipeline]`, runs cellpose import check, and runs `tests/segment/test_cellpose_sam.py` with `continue-on-error: true`.
6. Fast-tier CI stays green (all new segment/io tests are either gated or use synthetic data with no cellpose import).
7. Full pytest suite: 82 (Phase 2) + 22 new fast-tier tests = **104 passed** in fast tier; nightly adds ~8 more cellpose-gated tests.
8. README updated to reflect Phase 3 completion; tag `phase-3-complete` pushed.

---

## File Structure (locked at planning time)

```
QuantiPy-Polarity/
├── pyproject.toml                                 # Task 1: promote nd2reader + tqdm to pipeline extra (already there); add scipy upper-bound check
├── src/quantipy_polarity/
│   ├── io/
│   │   ├── _common.py                             # Modify Task 3: add pair_tifs_by_channel()
│   │   ├── tif.py                                 # Create Task 4
│   │   └── nd2.py                                 # Create Task 7
│   ├── segment/
│   │   ├── __init__.py                            # Create Task 10
│   │   └── cellpose_sam.py                        # Create Task 10
│   ├── _cli_segment.py                            # Create Task 14
│   └── _stubs.py                                  # Modify Task 15: remove "segment" stub
├── tests/
│   ├── fixtures/
│   │   ├── _build.py                              # Modify Task 2: add write_synthetic_tif_stack(), write_synthetic_tif_multifile()
│   │   └── synthetic_fov.npz                      # Already committed; unchanged
│   ├── io/
│   │   ├── __init__.py                            # Create Task 5
│   │   ├── test_tif.py                            # Create Task 5
│   │   └── test_nd2.py                            # Create Task 8
│   ├── segment/
│   │   ├── __init__.py                            # Create Task 11
│   │   ├── test_cellpose_sam.py                   # Create Task 11 (nightly-gated)
│   │   └── test_preprocess_stubs.py               # Create Task 12 (import-only; no cellpose needed)
│   └── cli/
│       ├── __init__.py                            # Create Task 16
│       └── test_cli_segment.py                    # Create Task 16 (nightly-gated for cellpose smoke)
├── .github/workflows/
│   └── ci-nightly.yml                             # Modify Task 17: replace placeholder with real cellpose tests
├── docs/
│   ├── concepts.md                                # Modify Task 19: TIF/ND2 ingest notes
│   └── superpowers/plans/                         # this file
├── README.md                                      # Modify Task 20: ✅ Phase 3 badge + [pipeline] install note
└── CLAUDE.md                                      # Modify Task 20: update command map table
```

---

## Task 1: Confirm `pyproject.toml` pipeline extras are correct for Phase 3

**Files:** Modify `pyproject.toml`

Phase 3 introduces hard imports of `nd2reader`, `cellpose`, and `tqdm` inside `io/nd2.py` and `segment/cellpose_sam.py`. These are already in `[pipeline]` extras. This task verifies that is still the case after Phase 2 edits, and confirms `.[dev,pipeline]` installs cleanly.

- [ ] **Step 1: Read current `pyproject.toml`**

Confirm `pipeline` extra contains: `nd2reader>=3.3,<4`, `cellpose>=3.0,<4`, `tqdm>=4.66,<5`. If any are missing, add them. Expected current state (already correct after Phase 2):

```toml
pipeline = [
  "nd2reader>=3.3,<4",
  "cellpose>=3.0,<4",
  "matplotlib>=3.8,<3.10",
  "jinja2>=3.1,<4",
  "tqdm>=4.66,<5",
  "requests>=2.31,<3",
]
```

- [ ] **Step 2: Verify TOML parses**

```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('TOML OK')"
```
Expected: `TOML OK`

- [ ] **Step 3: Verify existing tests still pass**

```bash
pytest -v 2>&1 | tail -3
```
Expected: `82 passed`

- [ ] **Step 4: Commit if any changes were made; skip if file was already correct**

```bash
git add pyproject.toml
git commit -m "build: confirm pipeline extras include nd2reader + cellpose + tqdm for Phase 3"
```

---

## Task 2: Extend fixture builder for TIF ingest tests

**Files:** Modify `tests/fixtures/_build.py`

Add two helpers that write synthetic FOV data to disk as TIF files, covering both supported TIF schemes: (a) multi-page TIF with channels as pages, (b) per-channel multi-file TIFs.

- [ ] **Step 1: Read current `tests/fixtures/_build.py`**

Confirm existing imports (`numpy`, `scipy.spatial.Voronoi`, `tifffile` not yet imported). The two new helpers need `tifffile` and `pathlib.Path`.

- [ ] **Step 2: Append two helpers to `tests/fixtures/_build.py`**

After the existing `if __name__ == "__main__":` block, append:

```python
import tifffile as _tifffile


def write_synthetic_tif_stack(
    out_dir: Path,
    fov_id: str = "FOV_01",
    *,
    n_cells: int = 20,
    image_size: int = 128,
    seed: int = 20260526,
) -> dict:
    """Write a 2-channel multi-page TIF (C, H, W) to out_dir/<fov_id>.tif.

    Channel 0 = membrane signal (float32 scaled to uint16).
    Channel 1 = nuclear placeholder (uniform random uint16).
    Returns the build dict from build_synthetic_fov (includes theta_truth).
    """
    import numpy as _np

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = build_synthetic_fov(n_cells=n_cells, image_size=image_size, seed=seed)
    membrane_u16 = (data["membrane"] * 65535).clip(0, 65535).astype(_np.uint16)
    rng = _np.random.default_rng(seed + 1)
    nuclear_u16 = rng.integers(0, 1000, size=(image_size, image_size), dtype=_np.uint16)
    stack = _np.stack([membrane_u16, nuclear_u16], axis=0)  # (C=2, H, W)
    _tifffile.imwrite(out_dir / f"{fov_id}.tif", stack, photometric="minisblack")
    return data


def write_synthetic_tif_multifile(
    out_dir: Path,
    fov_id: str = "FOV_01",
    *,
    n_cells: int = 20,
    image_size: int = 128,
    seed: int = 20260526,
) -> dict:
    """Write per-channel TIFs to out_dir/<fov_id>_ch0.tif and <fov_id>_ch1.tif.

    Channel 0 = membrane, Channel 1 = nuclear placeholder.
    Returns the same build dict.
    """
    import numpy as _np

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = build_synthetic_fov(n_cells=n_cells, image_size=image_size, seed=seed)
    membrane_u16 = (data["membrane"] * 65535).clip(0, 65535).astype(_np.uint16)
    rng = _np.random.default_rng(seed + 1)
    nuclear_u16 = rng.integers(0, 1000, size=(image_size, image_size), dtype=_np.uint16)
    _tifffile.imwrite(out_dir / f"{fov_id}_ch0.tif", membrane_u16)
    _tifffile.imwrite(out_dir / f"{fov_id}_ch1.tif", nuclear_u16)
    return data
```

- [ ] **Step 3: Smoke-test both helpers**

```bash
python -c "
import tempfile
from pathlib import Path
from tests.fixtures._build import write_synthetic_tif_stack, write_synthetic_tif_multifile
with tempfile.TemporaryDirectory() as td:
    d = write_synthetic_tif_stack(Path(td), 'FOV_01', n_cells=10, image_size=64)
    import tifffile, numpy as np
    arr = tifffile.imread(str(Path(td) / 'FOV_01.tif'))
    assert arr.shape == (2, 64, 64), f'stack shape wrong: {arr.shape}'
    assert arr.dtype == np.uint16
    print('stack: OK', arr.shape)
with tempfile.TemporaryDirectory() as td:
    d = write_synthetic_tif_multifile(Path(td), 'FOV_01', n_cells=10, image_size=64)
    f0 = tifffile.imread(str(Path(td) / 'FOV_01_ch0.tif'))
    f1 = tifffile.imread(str(Path(td) / 'FOV_01_ch1.tif'))
    assert f0.shape == (64, 64)
    print('multifile: OK', f0.shape, f1.shape)
"
```
Expected: both `OK` lines printed.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/_build.py
git commit -m "test(fixtures): add write_synthetic_tif_stack + write_synthetic_tif_multifile helpers"
```

---

## Task 3: Extend `io/_common.py` with `pair_tifs_by_channel`

**Files:** Modify `src/quantipy_polarity/io/_common.py`

Add a helper that pairs per-channel multi-file TIFs by FOV ID and channel suffix pattern, e.g. `FOV_01_ch0.tif` + `FOV_01_ch1.tif`.

- [ ] **Step 1: Read current `src/quantipy_polarity/io/_common.py`**

Confirm existing content: `fov_id_from_path`, `pair_masks_with_membranes`.

- [ ] **Step 2: Append `pair_tifs_by_channel` to `io/_common.py`**

```python
def pair_tifs_by_channel(
    tif_dir: Path,
    channel_membrane: int,
    channel_segmentation: int | None = None,
    *,
    channel_suffix_template: str = "_ch{ch}",
    ext: str = ".tif",
) -> list[tuple[str, Path, Path | None]]:
    """Pair per-channel TIF files by FOV ID.

    Expects files named like `<fov_id>_ch0.tif`, `<fov_id>_ch1.tif` (or
    whatever `channel_suffix_template` produces for the given channel indices).

    Returns a sorted list of (fov_id, membrane_path, seg_path_or_None).
    `seg_path_or_None` is None when channel_segmentation is None.

    Raises FileNotFoundError if no membrane-channel files exist or if any
    membrane file's segmentation-channel counterpart is missing.
    """
    membrane_suffix = channel_suffix_template.format(ch=channel_membrane)
    mem_files = sorted(Path(tif_dir).glob(f"*{membrane_suffix}{ext}"))
    if not mem_files:
        raise FileNotFoundError(
            f"No files matching '*{membrane_suffix}{ext}' in {tif_dir}"
        )

    result = []
    for mp in mem_files:
        # Derive fov_id: strip channel suffix from stem
        stem = mp.stem  # e.g. "FOV_01_ch0"
        if not stem.endswith(membrane_suffix.lstrip("_") if membrane_suffix.startswith("_") else membrane_suffix):
            fov_id = fov_id_from_path(mp)
        else:
            fov_id = stem[: -len(membrane_suffix)]
        if not fov_id:
            fov_id = fov_id_from_path(mp)

        seg_path: Path | None = None
        if channel_segmentation is not None:
            seg_suffix = channel_suffix_template.format(ch=channel_segmentation)
            seg_path = mp.parent / f"{fov_id}{seg_suffix}{ext}"
            if not seg_path.exists():
                raise FileNotFoundError(
                    f"Membrane file {mp.name} has no matching segmentation channel file {seg_path.name}"
                )
        result.append((fov_id, mp, seg_path))
    return result
```

- [ ] **Step 3: Verify imports are clean**

```bash
python -c "from quantipy_polarity.io._common import pair_tifs_by_channel; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/io/_common.py
git commit -m "feat(io): add pair_tifs_by_channel helper for multi-file TIF scheme"
```

---

## Task 4: Implement `io/tif.py` — multi-channel TIF ingest

**Files:** Create `src/quantipy_polarity/io/tif.py`

Supports two TIF schemes controlled by `input.tif_scheme` (new config field added in Task 4 Step 1):
- `"stack"`: single TIF per FOV with channels as pages, shape `(C, H, W)` or `(H, W, C)` (auto-detected)
- `"multifile"`: one TIF per channel per FOV, named `<fov_id>_ch{N}.tif`

- [ ] **Step 1: Add `tif_scheme` field to `InputTIF` in `config.py`**

Open `src/quantipy_polarity/config.py`. After the `pixel_size_um` field in `InputTIF`, add:

```python
    tif_scheme: Literal["stack", "multifile"] = "stack"
    channel_suffix_template: str = "_ch{ch}"
```

This adds two new optional fields to `InputTIF` with safe defaults. Run `pytest -v 2>&1 | tail -3` to confirm 82 still pass after the change.

- [ ] **Step 2: Create `src/quantipy_polarity/io/tif.py`**

```python
"""Load multi-channel TIF stacks from disk.

Supports two schemes:
  stack:     single multi-page TIF per FOV; channels as first axis (C, H, W)
             or last axis (H, W, C). Auto-detected: if ndim==3 and shape[0]<=8
             treat as (C, H, W), else (H, W, C).
  multifile: one TIF per channel per FOV, named <fov_id>_ch{N}.tif (or the
             configured channel_suffix_template).

Both schemes yield TIFFOV objects with the same shape contract as MaskFOV.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import structlog
import tifffile

from quantipy_polarity.io._common import fov_id_from_path, pair_tifs_by_channel

log = structlog.get_logger()


@dataclass(frozen=True)
class TIFFOV:
    """One FOV loaded from TIF: membrane channel + optional nuclear channel."""

    fov_id: str
    membrane: np.ndarray     # (H, W) float32, [0, 1]
    nuclear: np.ndarray | None  # (H, W) float32, [0, 1] or None
    pixel_size_um: float
    raw_dtype: np.dtype      # original dtype before normalization

    def __post_init__(self) -> None:
        if self.membrane.ndim != 2:
            raise ValueError(
                f"{self.fov_id}: membrane must be 2D, got ndim={self.membrane.ndim}"
            )
        if self.nuclear is not None and self.nuclear.shape != self.membrane.shape:
            raise ValueError(
                f"{self.fov_id}: nuclear shape {self.nuclear.shape} != "
                f"membrane shape {self.membrane.shape}"
            )
        if self.pixel_size_um <= 0:
            raise ValueError(f"{self.fov_id}: pixel_size_um must be > 0")


def _normalize_channel(arr: np.ndarray) -> np.ndarray:
    """Normalize an integer or float channel to float32 [0, 1]."""
    if arr.dtype.kind in ("u", "i"):
        max_val = float(np.iinfo(arr.dtype).max)
        return (arr.astype(np.float32) / max_val).clip(0.0, 1.0)
    return arr.astype(np.float32)


def _extract_channels_stack(
    arr: np.ndarray,
    channel_membrane: int,
    channel_segmentation: int | None,
    fov_id: str,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Extract membrane and optional nuclear channels from a stack array.

    Handles both (C, H, W) and (H, W, C) layouts.
    """
    if arr.ndim == 2:
        # Single-channel TIF
        if channel_membrane != 0:
            raise IndexError(
                f"{fov_id}: single-channel TIF but channel_membrane={channel_membrane}"
            )
        return arr, None

    if arr.ndim != 3:
        raise ValueError(
            f"{fov_id}: expected 2D or 3D TIF array, got shape {arr.shape}"
        )

    # Heuristic: (C, H, W) if first dim <= 8; else (H, W, C)
    if arr.shape[0] <= 8:
        n_channels = arr.shape[0]
        if channel_membrane >= n_channels:
            raise IndexError(
                f"{fov_id}: channel_membrane={channel_membrane} out of range "
                f"for {n_channels}-channel stack"
            )
        membrane = arr[channel_membrane]
        nuclear = (
            arr[channel_segmentation]
            if channel_segmentation is not None and channel_segmentation < n_channels
            else None
        )
    else:
        n_channels = arr.shape[2]
        if channel_membrane >= n_channels:
            raise IndexError(
                f"{fov_id}: channel_membrane={channel_membrane} out of range "
                f"for {n_channels}-channel stack"
            )
        membrane = arr[..., channel_membrane]
        nuclear = (
            arr[..., channel_segmentation]
            if channel_segmentation is not None and channel_segmentation < n_channels
            else None
        )
    return membrane, nuclear


def load_tif_fov_stack(
    path: Path,
    fov_id: str,
    channel_membrane: int,
    channel_segmentation: int | None,
    pixel_size_um: float,
) -> TIFFOV:
    """Load a single multi-page TIF and return a TIFFOV."""
    arr = tifffile.imread(path)
    raw_dtype = arr.dtype
    membrane_raw, nuclear_raw = _extract_channels_stack(
        arr, channel_membrane, channel_segmentation, fov_id
    )
    return TIFFOV(
        fov_id=fov_id,
        membrane=_normalize_channel(membrane_raw),
        nuclear=_normalize_channel(nuclear_raw) if nuclear_raw is not None else None,
        pixel_size_um=pixel_size_um,
        raw_dtype=raw_dtype,
    )


def load_tif_fov_multifile(
    membrane_path: Path,
    nuclear_path: Path | None,
    fov_id: str,
    pixel_size_um: float,
) -> TIFFOV:
    """Load per-channel TIF files and return a TIFFOV."""
    membrane_raw = tifffile.imread(membrane_path)
    if membrane_raw.ndim != 2:
        raise ValueError(
            f"{fov_id}: membrane TIF must be 2D for multifile scheme, "
            f"got shape {membrane_raw.shape}"
        )
    raw_dtype = membrane_raw.dtype
    nuclear_raw = None
    if nuclear_path is not None:
        nuclear_raw = tifffile.imread(nuclear_path)
        if nuclear_raw.ndim != 2:
            raise ValueError(
                f"{fov_id}: nuclear TIF must be 2D for multifile scheme"
            )
    return TIFFOV(
        fov_id=fov_id,
        membrane=_normalize_channel(membrane_raw),
        nuclear=_normalize_channel(nuclear_raw) if nuclear_raw is not None else None,
        pixel_size_um=pixel_size_um,
        raw_dtype=raw_dtype,
    )


def iter_tif_dataset(
    tif_dir: Path,
    channel_membrane: int,
    channel_segmentation: int | None,
    pixel_size_um: float,
    *,
    scheme: str = "stack",
    channel_suffix_template: str = "_ch{ch}",
) -> Iterator[TIFFOV]:
    """Yield TIFFOV objects for every FOV in tif_dir.

    Args:
        tif_dir: Directory containing TIF files.
        channel_membrane: 0-indexed membrane channel.
        channel_segmentation: 0-indexed nuclear/segmentation channel, or None.
        pixel_size_um: Physical pixel size in microns (from config).
        scheme: "stack" (multi-page TIF) or "multifile" (per-channel TIFs).
        channel_suffix_template: Template for per-channel filenames; default "_ch{ch}".
    """
    tif_dir = Path(tif_dir)
    if scheme == "stack":
        tif_files = sorted(tif_dir.glob("*.tif")) + sorted(tif_dir.glob("*.tiff"))
        if not tif_files:
            raise FileNotFoundError(f"No .tif/.tiff files found in {tif_dir}")
        for tf in tif_files:
            fov_id = fov_id_from_path(tf)
            log.debug("loading_tif_stack", fov_id=fov_id, path=str(tf))
            yield load_tif_fov_stack(
                tf, fov_id, channel_membrane, channel_segmentation, pixel_size_um
            )
    elif scheme == "multifile":
        pairs = pair_tifs_by_channel(
            tif_dir,
            channel_membrane,
            channel_segmentation,
            channel_suffix_template=channel_suffix_template,
        )
        for fov_id, mem_path, nuc_path in pairs:
            log.debug("loading_tif_multifile", fov_id=fov_id, membrane=str(mem_path))
            yield load_tif_fov_multifile(mem_path, nuc_path, fov_id, pixel_size_um)
    else:
        raise ValueError(f"Unknown TIF scheme: {scheme!r}. Expected 'stack' or 'multifile'.")
```

- [ ] **Step 3: Verify module imports cleanly**

```bash
python -c "
from quantipy_polarity.io.tif import TIFFOV, iter_tif_dataset, load_tif_fov_stack
print('tif module OK')
"
```
Expected: `tif module OK`

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/io/tif.py src/quantipy_polarity/config.py
git commit -m "feat(io): add io/tif.py (stack + multifile TIF ingest) + tif_scheme config field"
```

---

## Task 5: Tests for `io/tif.py`

**Files:** Create `tests/io/__init__.py`, `tests/io/test_tif.py`

- [ ] **Step 1: Create `tests/io/__init__.py`**

Empty file: `"""IO module tests."""`

- [ ] **Step 2: Write `tests/io/test_tif.py`**

```python
"""Tests for io/tif.py — TIF ingest with stack and multifile schemes."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import tifffile

from quantipy_polarity.io.tif import (
    TIFFOV,
    _extract_channels_stack,
    _normalize_channel,
    iter_tif_dataset,
    load_tif_fov_multifile,
    load_tif_fov_stack,
)
from tests.fixtures._build import write_synthetic_tif_stack, write_synthetic_tif_multifile


# ---------------------------------------------------------------------------
# _normalize_channel
# ---------------------------------------------------------------------------

def test_normalize_uint16_max() -> None:
    arr = np.array([[65535]], dtype=np.uint16)
    out = _normalize_channel(arr)
    assert out.dtype == np.float32
    assert np.isclose(out[0, 0], 1.0)


def test_normalize_uint16_zero() -> None:
    arr = np.zeros((4, 4), dtype=np.uint16)
    out = _normalize_channel(arr)
    assert out.min() == 0.0 and out.max() == 0.0


def test_normalize_float32_passthrough() -> None:
    arr = np.array([[0.5]], dtype=np.float32)
    out = _normalize_channel(arr)
    assert out.dtype == np.float32
    assert np.isclose(out[0, 0], 0.5)


# ---------------------------------------------------------------------------
# _extract_channels_stack
# ---------------------------------------------------------------------------

def test_extract_channels_stack_chw() -> None:
    """(C, H, W) layout: first axis is channels."""
    arr = np.zeros((3, 64, 64), dtype=np.uint16)
    arr[1] = 1000  # channel 1 = membrane
    mem, nuc = _extract_channels_stack(arr, channel_membrane=1, channel_segmentation=0, fov_id="T")
    assert mem.shape == (64, 64)
    assert mem[0, 0] == 1000
    assert nuc is not None and nuc.shape == (64, 64)


def test_extract_channels_stack_hwc() -> None:
    """(H, W, C) layout: last axis is channels when first axis > 8."""
    arr = np.zeros((64, 64, 3), dtype=np.uint16)
    arr[..., 2] = 2000  # channel 2 = membrane
    mem, nuc = _extract_channels_stack(arr, channel_membrane=2, channel_segmentation=None, fov_id="T")
    assert mem.shape == (64, 64)
    assert mem[0, 0] == 2000
    assert nuc is None


def test_extract_channels_stack_out_of_range() -> None:
    arr = np.zeros((2, 64, 64), dtype=np.uint16)
    with pytest.raises(IndexError, match="channel_membrane=5"):
        _extract_channels_stack(arr, 5, None, "T")


# ---------------------------------------------------------------------------
# load_tif_fov_stack
# ---------------------------------------------------------------------------

def test_load_tif_fov_stack_roundtrip(tmp_path: Path) -> None:
    data = write_synthetic_tif_stack(tmp_path, "FOV_01", n_cells=10, image_size=64)
    fov = load_tif_fov_stack(
        tmp_path / "FOV_01.tif",
        fov_id="FOV_01",
        channel_membrane=0,
        channel_segmentation=1,
        pixel_size_um=0.65,
    )
    assert isinstance(fov, TIFFOV)
    assert fov.fov_id == "FOV_01"
    assert fov.membrane.shape == (64, 64)
    assert fov.membrane.dtype == np.float32
    assert 0.0 <= fov.membrane.min() and fov.membrane.max() <= 1.0
    assert fov.nuclear is not None
    assert fov.nuclear.shape == (64, 64)
    assert fov.pixel_size_um == 0.65


def test_load_tif_fov_stack_no_nuclear(tmp_path: Path) -> None:
    data = write_synthetic_tif_stack(tmp_path, "FOV_01", n_cells=10, image_size=64)
    fov = load_tif_fov_stack(
        tmp_path / "FOV_01.tif",
        fov_id="FOV_01",
        channel_membrane=0,
        channel_segmentation=None,
        pixel_size_um=0.65,
    )
    assert fov.nuclear is None


# ---------------------------------------------------------------------------
# load_tif_fov_multifile
# ---------------------------------------------------------------------------

def test_load_tif_fov_multifile_roundtrip(tmp_path: Path) -> None:
    write_synthetic_tif_multifile(tmp_path, "FOV_01", n_cells=10, image_size=64)
    fov = load_tif_fov_multifile(
        membrane_path=tmp_path / "FOV_01_ch0.tif",
        nuclear_path=tmp_path / "FOV_01_ch1.tif",
        fov_id="FOV_01",
        pixel_size_um=0.65,
    )
    assert fov.fov_id == "FOV_01"
    assert fov.membrane.shape == (64, 64)
    assert fov.nuclear is not None


# ---------------------------------------------------------------------------
# iter_tif_dataset — stack scheme
# ---------------------------------------------------------------------------

def test_iter_tif_dataset_stack(tmp_path: Path) -> None:
    for fov_name in ("FOV_01", "FOV_02", "FOV_03"):
        write_synthetic_tif_stack(tmp_path, fov_name, n_cells=10, image_size=64)
    fovs = list(iter_tif_dataset(tmp_path, 0, None, 0.65, scheme="stack"))
    assert len(fovs) == 3
    assert [f.fov_id for f in fovs] == ["FOV_01", "FOV_02", "FOV_03"]
    assert all(isinstance(f, TIFFOV) for f in fovs)


def test_iter_tif_dataset_stack_empty_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        list(iter_tif_dataset(tmp_path, 0, None, 0.65, scheme="stack"))


# ---------------------------------------------------------------------------
# iter_tif_dataset — multifile scheme
# ---------------------------------------------------------------------------

def test_iter_tif_dataset_multifile(tmp_path: Path) -> None:
    for fov_name in ("FOV_01", "FOV_02"):
        write_synthetic_tif_multifile(tmp_path, fov_name, n_cells=10, image_size=64)
    fovs = list(iter_tif_dataset(tmp_path, 0, 1, 0.65, scheme="multifile"))
    assert len(fovs) == 2
    assert all(f.nuclear is not None for f in fovs)


def test_iter_tif_dataset_unknown_scheme(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown TIF scheme"):
        list(iter_tif_dataset(tmp_path, 0, None, 0.65, scheme="bad_scheme"))
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/io/test_tif.py -v 2>&1 | tail -5
```
Expected: **17 passed** (3 normalize + 3 extract + 2 stack load + 1 multifile load + 2 stack iter + 1 empty + 2 multifile iter + 1 unknown scheme).

- [ ] **Step 4: Run full suite**

```bash
pytest -v 2>&1 | tail -3
```
Expected: 82 + 17 = **99 passed**.

- [ ] **Step 5: Commit**

```bash
git add tests/io/__init__.py tests/io/test_tif.py
git commit -m "test(io): cover TIFFOV normalization, stack/multifile TIF roundtrip, iter_tif_dataset"
```

---

## Task 6: Tests for `io/_common.py` `pair_tifs_by_channel`

**Files:** Modify `tests/test_io_common.py`

- [ ] **Step 1: Append three tests to `tests/test_io_common.py`**

```python
from quantipy_polarity.io._common import pair_tifs_by_channel


def test_pair_tifs_by_channel_finds_pairs(tmp_path: Path) -> None:
    for fov in ("FOV_01", "FOV_02"):
        (tmp_path / f"{fov}_ch0.tif").write_bytes(b"")
        (tmp_path / f"{fov}_ch1.tif").write_bytes(b"")
    pairs = pair_tifs_by_channel(tmp_path, channel_membrane=0, channel_segmentation=1)
    assert len(pairs) == 2
    fov_ids = [p[0] for p in pairs]
    assert "FOV_01" in fov_ids and "FOV_02" in fov_ids
    assert all(p[2] is not None for p in pairs)


def test_pair_tifs_by_channel_no_seg(tmp_path: Path) -> None:
    (tmp_path / "FOV_01_ch0.tif").write_bytes(b"")
    pairs = pair_tifs_by_channel(tmp_path, channel_membrane=0, channel_segmentation=None)
    assert len(pairs) == 1
    assert pairs[0][2] is None


def test_pair_tifs_by_channel_missing_seg_file(tmp_path: Path) -> None:
    (tmp_path / "FOV_01_ch0.tif").write_bytes(b"")
    # ch1 file is absent
    with pytest.raises(FileNotFoundError, match="ch1"):
        pair_tifs_by_channel(tmp_path, channel_membrane=0, channel_segmentation=1)
```

- [ ] **Step 2: Run new tests**

```bash
pytest tests/test_io_common.py -v 2>&1 | tail -5
```
Expected: The 10 original tests + 3 new tests = **13 passed**.

- [ ] **Step 3: Commit**

```bash
git add tests/test_io_common.py
git commit -m "test(io): cover pair_tifs_by_channel helper"
```

---

## Task 7: Implement `io/nd2.py` — ND2 ingest

**Files:** Create `src/quantipy_polarity/io/nd2.py`

Lift `_extract_fov` and `_z_project` logic from `Hughes Lab/.../pipeline/01_nd2_to_tif.py`, generalized to config-driven channel/z parameters and yielding `ND2FOV` objects. `nd2reader` is a lazy import (inside the function) so the module imports cleanly without the `[pipeline]` extra installed.

- [ ] **Step 1: Create `src/quantipy_polarity/io/nd2.py`**

```python
"""Load microscopy data from .nd2 files via nd2reader.

nd2reader is a lazy import — this module can be imported without the [pipeline]
extra installed, but calling any public function without nd2reader raises
ImportError with a clear install hint.

ND2FOV has the same shape contract as TIFFOV: membrane (H, W) float32 [0, 1],
optional nuclear channel, pixel_size_um from ND2 metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import structlog

log = structlog.get_logger()

_ND2READER_IMPORT_HINT = (
    "nd2reader is required for ND2 ingest. "
    "Install with: pip install 'quantipy-polarity[pipeline]'"
)


@dataclass(frozen=True)
class ND2FOV:
    """One FOV loaded from an ND2 file."""

    fov_id: str
    membrane: np.ndarray       # (H, W) float32, [0, 1]
    nuclear: np.ndarray | None  # (H, W) float32, [0, 1] or None
    pixel_size_um: float        # from ND2 metadata or config fallback
    raw_dtype: np.dtype

    def __post_init__(self) -> None:
        if self.membrane.ndim != 2:
            raise ValueError(
                f"{self.fov_id}: membrane must be 2D, got ndim={self.membrane.ndim}"
            )
        if self.nuclear is not None and self.nuclear.shape != self.membrane.shape:
            raise ValueError(
                f"{self.fov_id}: nuclear shape {self.nuclear.shape} != "
                f"membrane shape {self.membrane.shape}"
            )


def _z_project(stack: np.ndarray, policy: str, substack_range: tuple[int, int] | None) -> np.ndarray:
    """Project a (Z, H, W) stack to (H, W) according to policy.

    Args:
        stack: (Z, H, W) array.
        policy: "mip" | "substack" | "none".
        substack_range: (z_min, z_max) inclusive range for "substack" policy.
    """
    if policy == "mip":
        return stack.max(axis=0)
    if policy == "none":
        # Use the middle z-plane
        mid = stack.shape[0] // 2
        return stack[mid]
    if policy == "substack":
        if substack_range is None:
            raise ValueError("substack_range required when z_policy='substack'")
        z_min, z_max = substack_range
        if not (0 <= z_min <= z_max < stack.shape[0]):
            raise ValueError(
                f"substack_range=({z_min}, {z_max}) out of range for Z={stack.shape[0]}"
            )
        return stack[z_min : z_max + 1].max(axis=0)
    raise ValueError(f"Unknown z_policy: {policy!r}. Expected 'mip', 'substack', or 'none'.")


def _extract_fov_from_nd2(nd2: object, v: int) -> np.ndarray:
    """Pull one FOV (all channels, all z-planes) from an open ND2Reader.

    Returns (C, Z, H, W) uint16 array. Promotes (Z, H, W) single-channel
    arrays to (1, Z, H, W).

    Args:
        nd2: Open ND2Reader instance.
        v: FOV index (v-axis).
    """
    nd2.iter_axes = ""
    nd2.bundle_axes = "czyx" if "c" in nd2.axes else "zyx"
    if "v" in nd2.axes:
        nd2.default_coords["v"] = v
    if "t" in nd2.axes:
        nd2.default_coords["t"] = 0

    img = nd2[0]
    arr = np.asarray(img, dtype=np.float32)

    if arr.ndim == 3:
        arr = arr[np.newaxis, ...]  # (Z, H, W) -> (1, Z, H, W)
    if arr.ndim != 4:
        raise ValueError(
            f"Unexpected FOV shape {arr.shape} from ND2; expected (C, Z, H, W)"
        )
    return arr


def _pixel_size_from_nd2(nd2: object, config_fallback: float) -> float:
    """Extract pixel size in microns from ND2 metadata, falling back to config.

    nd2reader exposes metadata via nd2.metadata. The key varies:
    'pixel_microns' is the most common; fall back gracefully.
    """
    meta = getattr(nd2, "metadata", {}) or {}
    px = meta.get("pixel_microns") or meta.get("pixel_size") or config_fallback
    try:
        px = float(px)
    except (TypeError, ValueError):
        px = config_fallback
    if px <= 0:
        log.warning("nd2_pixel_size_invalid", raw=px, fallback=config_fallback)
        px = config_fallback
    return px


def _normalize_to_float32(arr: np.ndarray) -> np.ndarray:
    """Normalize array to float32 [0, 1]; handles float and int dtypes."""
    if arr.dtype.kind in ("u", "i"):
        max_val = float(np.iinfo(arr.dtype).max)
        return (arr.astype(np.float32) / max_val).clip(0.0, 1.0)
    arr = arr.astype(np.float32)
    # nd2reader returns float arrays already in raw ADU; normalize by max to [0, 1]
    max_val = arr.max()
    if max_val > 0:
        arr = arr / max_val
    return arr.clip(0.0, 1.0)


def iter_nd2_dataset(
    nd2_path: Path,
    channel_membrane: int,
    channel_segmentation: int | None,
    pixel_size_um_fallback: float,
    z_policy: str = "mip",
    substack_range: tuple[int, int] | None = None,
    fov_id_prefix: str = "FOV",
) -> Iterator[ND2FOV]:
    """Yield ND2FOV objects for every FOV in an ND2 file.

    Args:
        nd2_path: Path to .nd2 file.
        channel_membrane: 0-indexed membrane channel.
        channel_segmentation: 0-indexed nuclear/segmentation channel or None.
        pixel_size_um_fallback: Used when ND2 metadata does not contain pixel size.
        z_policy: "mip" | "substack" | "none".
        substack_range: (z_min, z_max) inclusive range for "substack" policy.
        fov_id_prefix: Prefix for generated FOV IDs (e.g. "FOV" -> "FOV_01").
    """
    try:
        from nd2reader import ND2Reader
    except ImportError as exc:
        raise ImportError(_ND2READER_IMPORT_HINT) from exc

    nd2_path = Path(nd2_path)
    with ND2Reader(str(nd2_path)) as nd2:
        n_fovs = nd2.sizes.get("v", 1)
        n_channels = nd2.sizes.get("c", 1)
        pixel_size_um = _pixel_size_from_nd2(nd2, pixel_size_um_fallback)

        log.info(
            "nd2_opened",
            path=str(nd2_path),
            n_fovs=n_fovs,
            n_channels=n_channels,
            pixel_size_um=pixel_size_um,
        )

        for v in range(n_fovs):
            fov_id = f"{fov_id_prefix}_{v + 1:02d}"
            arr = _extract_fov_from_nd2(nd2, v)  # (C, Z, H, W) float32

            if channel_membrane >= arr.shape[0]:
                raise IndexError(
                    f"{fov_id}: channel_membrane={channel_membrane} out of range "
                    f"for ND2 with {arr.shape[0]} channels"
                )

            mem_stack = arr[channel_membrane].astype(np.float32)  # (Z, H, W)
            raw_dtype = np.dtype("uint16")  # ND2s are always 16-bit camera data
            membrane_2d = _z_project(mem_stack, z_policy, substack_range)
            membrane_norm = _normalize_to_float32(membrane_2d)

            nuclear_norm = None
            if channel_segmentation is not None:
                if channel_segmentation < arr.shape[0]:
                    nuc_stack = arr[channel_segmentation].astype(np.float32)
                    nuclear_2d = _z_project(nuc_stack, z_policy, substack_range)
                    nuclear_norm = _normalize_to_float32(nuclear_2d)
                else:
                    log.warning(
                        "nd2_nuclear_channel_missing",
                        fov_id=fov_id,
                        requested=channel_segmentation,
                        available=arr.shape[0],
                    )

            yield ND2FOV(
                fov_id=fov_id,
                membrane=membrane_norm,
                nuclear=nuclear_norm,
                pixel_size_um=pixel_size_um,
                raw_dtype=raw_dtype,
            )
```

- [ ] **Step 2: Verify module imports cleanly without nd2reader installed**

```bash
python -c "from quantipy_polarity.io.nd2 import ND2FOV, iter_nd2_dataset; print('nd2 module imports OK')"
```
Expected: `nd2 module imports OK` (no ImportError because nd2reader is lazily imported)

- [ ] **Step 3: Commit**

```bash
git add src/quantipy_polarity/io/nd2.py
git commit -m "feat(io): add io/nd2.py — ND2FOV, z-project, iter_nd2_dataset (lazy nd2reader import)"
```

---

## Task 8: Tests for `io/nd2.py`

**Files:** Create `tests/io/test_nd2.py`

All nd2reader tests are gated with `pytest.importorskip("nd2reader")` so the fast CI tier (which may not have nd2reader installed in the dev-only environment) can skip them cleanly.

- [ ] **Step 1: Write `tests/io/test_nd2.py`**

```python
"""Tests for io/nd2.py — ND2 ingest.

nd2reader tests are gated: skipped automatically when nd2reader is not installed.
Tests that don't invoke nd2reader (unit tests of helper functions) run always.
"""
from __future__ import annotations

import numpy as np
import pytest

from quantipy_polarity.io.nd2 import (
    ND2FOV,
    _normalize_to_float32,
    _pixel_size_from_nd2,
    _z_project,
)


# ---------------------------------------------------------------------------
# _z_project — pure numpy, no nd2reader
# ---------------------------------------------------------------------------

def test_z_project_mip() -> None:
    stack = np.array([[[1, 2], [3, 4]], [[5, 0], [0, 1]]], dtype=np.float32)  # (2, 2, 2)
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

    px = _pixel_size_from_nd2(FakeND2(), fallback=1.0)
    assert px == pytest.approx(0.65)


def test_pixel_size_from_nd2_fallback_on_missing() -> None:
    class FakeND2:
        metadata = {}

    px = _pixel_size_from_nd2(FakeND2(), fallback=0.5)
    assert px == pytest.approx(0.5)


def test_pixel_size_from_nd2_fallback_on_invalid() -> None:
    class FakeND2:
        metadata = {"pixel_microns": "not_a_number"}

    px = _pixel_size_from_nd2(FakeND2(), fallback=0.5)
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

nd2reader = pytest.importorskip("nd2reader", reason="nd2reader not installed; skipping ND2 integration tests")


def test_iter_nd2_dataset_import_error_without_nd2reader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify iter_nd2_dataset raises ImportError with helpful message when nd2reader missing."""
    import sys
    original = sys.modules.get("nd2reader")
    sys.modules["nd2reader"] = None  # type: ignore[assignment]
    try:
        from quantipy_polarity.io.nd2 import iter_nd2_dataset
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
```

- [ ] **Step 2: Run tests (gated nd2reader tests will skip if not installed)**

```bash
pytest tests/io/test_nd2.py -v 2>&1 | tail -8
```
Expected: 11 fast-tier tests pass; nd2reader test either passes or is skipped (1 skipped if nd2reader absent, 1 passed if present).

- [ ] **Step 3: Run full fast suite**

```bash
pytest -v --ignore=tests/segment --ignore=tests/cli 2>&1 | tail -3
```
Expected: 99 (previous) + 12 new = **111 passed** (±1 for nd2reader skip).

- [ ] **Step 4: Commit**

```bash
git add tests/io/test_nd2.py
git commit -m "test(io): cover _z_project, _pixel_size_from_nd2, _normalize_to_float32; gate nd2reader tests"
```

---

## Task 9: Add `segment/` package skeleton and `contracts.py` update

**Files:** Create `src/quantipy_polarity/segment/__init__.py`; Modify `src/quantipy_polarity/contracts.py`

- [ ] **Step 1: Create `src/quantipy_polarity/segment/__init__.py`**

```python
"""Segmentation subpackage for QuantiPy Polarity.

Public entry point: segment_fov() in cellpose_sam.py.
"""
```

- [ ] **Step 2: Add `SegmentationResult` to `contracts.py`**

Open `src/quantipy_polarity/contracts.py`. After the `FOVManifestEntry` class, append:

```python

class SegmentationResult(BaseModel):
    """Metadata emitted alongside each label mask by segment/cellpose_sam.py."""

    fov_id: str
    n_cells_total: int = Field(ge=0)
    n_cells_after_filter: int = Field(ge=0)
    flow_threshold: float
    cellprob_threshold: float
    diameter_px: float | None
    min_size_px: int
    model: str
```

- [ ] **Step 3: Verify contracts.py imports cleanly**

```bash
python -c "from quantipy_polarity.contracts import SegmentationResult; print('SegmentationResult OK')"
```
Expected: `SegmentationResult OK`

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/segment/__init__.py src/quantipy_polarity/contracts.py
git commit -m "feat(segment): segment/ package + SegmentationResult contract"
```

---

## Task 10: Implement `segment/cellpose_sam.py`

**Files:** Create `src/quantipy_polarity/segment/cellpose_sam.py`

Lift logic from `pipeline/lib/segmentation.py` (real Cellpose-SAM wrapper). Generalize: model name from config, channels param, validate output label mask (contiguous IDs, no zero-area cells).

- [ ] **Step 1: Create `src/quantipy_polarity/segment/cellpose_sam.py`**

```python
"""Cellpose-SAM segmentation wrapper.

Lifted from Hughes Lab research repo pipeline/lib/segmentation.py and
generalized: model name and channels are config-driven rather than hard-coded.

cellpose is a lazy import — this module can be imported without the [pipeline]
extra installed, but calling segment_fov() without cellpose raises ImportError.
"""

from __future__ import annotations

import numpy as np
import structlog

log = structlog.get_logger()

_CELLPOSE_IMPORT_HINT = (
    "cellpose is required for segmentation. "
    "Install with: pip install 'quantipy-polarity[pipeline]'"
)


def segment_fov(
    image: np.ndarray,
    *,
    model: str = "cpsam",
    diameter: float | None = None,
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_size_px: int = 100,
    gpu: bool = False,
    channels: tuple[int, int] = (0, 0),
) -> tuple[np.ndarray, dict]:
    """Run Cellpose-SAM on a 2D image and return a validated uint16 label mask.

    Args:
        image: (H, W) or (H, W, C) float32 or uint16 array. For single-channel
               input pass a 2D array; Cellpose interprets channels=(0,0) as grayscale.
        model: Cellpose pretrained model name. Default "cpsam" is Cellpose-SAM.
               Use "cyto3" for the previous generation model.
        diameter: Expected cell diameter in pixels. None = auto-estimate.
        flow_threshold: Cellpose flow threshold (0.4 is the Cellpose default).
        cellprob_threshold: Cell probability threshold (0.0 is Cellpose default).
        min_size_px: Minimum cell area in pixels; smaller cells removed post-eval.
        gpu: Use GPU if available.
        channels: Cellpose channels argument: (cytoplasm_channel, nucleus_channel).
                  (0, 0) = grayscale. (1, 2) = membrane ch1, nuclear ch2.

    Returns:
        (label_mask, meta):
            label_mask: (H, W) uint16 array. Background = 0; cells = 1..N.
            meta: dict with keys matching SegmentationResult fields:
                  n_cells_total, n_cells_after_filter, flow_threshold,
                  cellprob_threshold, diameter_px, min_size_px, model.

    Raises:
        ImportError: If cellpose is not installed.
        ValueError: If the input image has an unsupported shape.
    """
    try:
        from cellpose import models, utils
    except ImportError as exc:
        raise ImportError(_CELLPOSE_IMPORT_HINT) from exc

    if image.ndim not in (2, 3):
        raise ValueError(
            f"segment_fov expects 2D or 3D image, got shape {image.shape}"
        )

    cp_model = models.CellposeModel(gpu=gpu, pretrained_model=model)
    masks, flows, styles = cp_model.eval(
        image,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        channels=list(channels),
    )

    n_before = int(masks.max())
    masks = utils.fill_holes_and_remove_small_masks(masks, min_size=min_size_px)
    masks = masks.astype(np.uint16)
    n_after = int(masks.max())

    # Validate: cell IDs should be contiguous starting at 1
    if n_after > 0:
        unique_ids = np.unique(masks[masks > 0])
        expected = np.arange(1, n_after + 1, dtype=np.uint16)
        if not np.array_equal(unique_ids, expected):
            # Re-label to ensure contiguous IDs (skimage relabel)
            from skimage.segmentation import relabel_sequential
            masks, _, _ = relabel_sequential(masks)
            masks = masks.astype(np.uint16)
            n_after = int(masks.max())
            log.debug("segment_fov_relabeled", n_after=n_after)

    # Validate: no zero-area cells (paranoia check after relabeling)
    if n_after > 0:
        areas = np.bincount(masks.ravel())[1:]  # skip background
        zero_area_ids = np.where(areas == 0)[0] + 1
        if zero_area_ids.size > 0:
            log.warning("segment_fov_zero_area_cells", ids=zero_area_ids.tolist())

    meta = {
        "n_cells_total": n_before,
        "n_cells_after_filter": n_after,
        "flow_threshold": flow_threshold,
        "cellprob_threshold": cellprob_threshold,
        "diameter_px": diameter,
        "min_size_px": min_size_px,
        "model": model,
    }
    log.info("segment_fov_done", n_before=n_before, n_after=n_after, model=model)
    return masks, meta
```

- [ ] **Step 2: Verify module imports cleanly without cellpose**

```bash
python -c "from quantipy_polarity.segment.cellpose_sam import segment_fov; print('segment module imports OK')"
```
Expected: `segment module imports OK`

- [ ] **Step 3: Commit**

```bash
git add src/quantipy_polarity/segment/cellpose_sam.py
git commit -m "feat(segment): cellpose_sam.py — segment_fov() wrapper with validation + lazy cellpose import"
```

---

## Task 11: Tests for `segment/cellpose_sam.py`

**Files:** Create `tests/segment/__init__.py`, `tests/segment/test_cellpose_sam.py`

All cellpose tests are gated on `pytest.importorskip("cellpose")`. These run only in the nightly tier.

- [ ] **Step 1: Create `tests/segment/__init__.py`**

```python
"""Segmentation tests."""
```

- [ ] **Step 2: Write `tests/segment/test_cellpose_sam.py`**

```python
"""Tests for segment/cellpose_sam.py.

All tests in this module are gated on cellpose availability:
    pytest.importorskip("cellpose")
These run in the nightly CI tier only (not fast tier).
Expected cell count for the 512x512 n=80-cell fixture: 72-88 cells (±10%).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

# Gate entire module — skip all tests if cellpose not installed
pytest.importorskip("cellpose", reason="cellpose not installed; nightly-tier tests only")

from quantipy_polarity.segment.cellpose_sam import segment_fov


FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "synthetic_fov.npz"
_EXPECTED_CELLS = 80
_TOLERANCE = 0.10  # ±10%


@pytest.fixture(scope="module")
def synthetic_membrane() -> np.ndarray:
    """Load the committed synthetic fixture membrane channel."""
    z = np.load(FIXTURE_PATH)
    membrane = z["membrane"]  # float32 (512, 512), [0, 1]
    # Scale to uint16 for Cellpose (more realistic input)
    return (membrane * 65535).clip(0, 65535).astype(np.uint16)


def test_segment_fov_returns_uint16_mask(synthetic_membrane: np.ndarray) -> None:
    masks, meta = segment_fov(synthetic_membrane, model="cpsam", diameter=30.0, gpu=False)
    assert masks.dtype == np.uint16
    assert masks.shape == synthetic_membrane.shape


def test_segment_fov_cell_count_within_tolerance(synthetic_membrane: np.ndarray) -> None:
    """Cellpose should find approximately the right number of cells."""
    masks, meta = segment_fov(synthetic_membrane, model="cpsam", diameter=30.0, gpu=False)
    n_cells = int(masks.max())
    lo = int(_EXPECTED_CELLS * (1 - _TOLERANCE))
    hi = int(_EXPECTED_CELLS * (1 + _TOLERANCE))
    assert lo <= n_cells <= hi, (
        f"Expected {lo}–{hi} cells (±{_TOLERANCE*100:.0f}% of {_EXPECTED_CELLS}), "
        f"got {n_cells}"
    )


def test_segment_fov_label_ids_contiguous(synthetic_membrane: np.ndarray) -> None:
    """All label IDs must be contiguous 1..N (no gaps)."""
    masks, _ = segment_fov(synthetic_membrane, model="cpsam", diameter=30.0, gpu=False)
    n = int(masks.max())
    if n > 0:
        unique = np.unique(masks[masks > 0])
        np.testing.assert_array_equal(unique, np.arange(1, n + 1, dtype=np.uint16))


def test_segment_fov_background_is_zero(synthetic_membrane: np.ndarray) -> None:
    masks, _ = segment_fov(synthetic_membrane, model="cpsam", diameter=30.0, gpu=False)
    # Background pixels should exist (synthetic FOV has borders)
    assert (masks == 0).any()


def test_segment_fov_meta_keys(synthetic_membrane: np.ndarray) -> None:
    _, meta = segment_fov(synthetic_membrane, model="cpsam", diameter=30.0, gpu=False)
    required_keys = {
        "n_cells_total", "n_cells_after_filter", "flow_threshold",
        "cellprob_threshold", "diameter_px", "min_size_px", "model",
    }
    assert required_keys <= meta.keys()
    assert meta["model"] == "cpsam"
    assert meta["min_size_px"] == 100


def test_segment_fov_import_error_without_cellpose(monkeypatch: pytest.MonkeyPatch) -> None:
    """segment_fov raises ImportError with install hint when cellpose absent."""
    import sys
    original = sys.modules.get("cellpose")
    sys.modules["cellpose"] = None  # type: ignore[assignment]
    sys.modules["cellpose.models"] = None  # type: ignore[assignment]
    sys.modules["cellpose.utils"] = None  # type: ignore[assignment]
    try:
        import importlib
        import quantipy_polarity.segment.cellpose_sam as csam
        importlib.reload(csam)
        import numpy as np
        with pytest.raises((ImportError, TypeError)):
            csam.segment_fov(np.zeros((64, 64), dtype=np.uint16))
    finally:
        for k in ("cellpose", "cellpose.models", "cellpose.utils"):
            if original is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = original


def test_segment_fov_invalid_shape() -> None:
    """segment_fov rejects non-2D/3D input."""
    import importlib, sys
    # Only run this sub-test if cellpose is actually importable
    pytest.importorskip("cellpose")
    from quantipy_polarity.segment.cellpose_sam import segment_fov as sfov
    bad_input = np.zeros((4, 4, 4, 4), dtype=np.uint16)
    with pytest.raises(ValueError, match="2D or 3D"):
        sfov(bad_input)
```

- [ ] **Step 3: Verify module and tests are syntactically valid**

```bash
python -m py_compile tests/segment/test_cellpose_sam.py && echo "compile OK"
```
Expected: `compile OK`

- [ ] **Step 4: Run fast tier (cellpose tests should be skipped)**

```bash
pytest tests/segment/ -v 2>&1 | tail -5
```
Expected: all cellpose tests show `SKIPPED (cellpose not installed)` — zero failures.

- [ ] **Step 5: Commit**

```bash
git add tests/segment/__init__.py tests/segment/test_cellpose_sam.py
git commit -m "test(segment): cellpose_sam tests gated on cellpose availability (nightly tier)"
```

---

## Task 12: Verify `segment/cellpose_sam.py` import-only smoke

**Files:** Create `tests/segment/test_preprocess_stubs.py`

A minimal non-cellpose test that confirms the segment package imports cleanly and `segment_fov`'s signature matches expectations. Runs in fast tier.

- [ ] **Step 1: Write `tests/segment/test_preprocess_stubs.py`**

```python
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
```

- [ ] **Step 2: Run fast-tier suite including new test**

```bash
pytest tests/segment/test_preprocess_stubs.py -v
```
Expected: **3 passed**.

- [ ] **Step 3: Run full fast suite to date**

```bash
pytest -v --ignore=tests/segment/test_cellpose_sam.py 2>&1 | tail -3
```
Expected: approximately **114 passed** (111 previous + 3 new).

- [ ] **Step 4: Commit**

```bash
git add tests/segment/test_preprocess_stubs.py
git commit -m "test(segment): fast-tier smoke for segment/ package, signature, SegmentationResult contract"
```

---

## Task 13: Implement segment output writer

**Files:** Create `src/quantipy_polarity/segment/_writer.py`

A small module that writes label masks and extracted membrane TIFs to the `02_segmentation/` output dir, matching the Phase 2 input contract (so `quantipy polarity` can consume `quantipy segment` outputs directly).

- [ ] **Step 1: Create `src/quantipy_polarity/segment/_writer.py`**

```python
"""Write segmentation outputs to disk.

Output layout under <out_dir>/02_segmentation/:
    <fov_id>_mask.tif       uint16 label mask (H, W)
    <fov_id>_membrane.tif   uint16 membrane channel (H, W), camera-native scale
    <fov_id>_seg_meta.json  SegmentationResult fields as JSON
    _stage_status.json      Stage status record (pending → running → complete)

The membrane TIF is written as uint16 (scaled from the normalized float32 [0,1]
by multiplying by 65535) so it is compatible with masks.load_mask_fov's
uint16 normalization path.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import tifffile

from quantipy_polarity.contracts import SegmentationResult


def write_fov_outputs(
    out_dir: Path,
    fov_id: str,
    label_mask: np.ndarray,
    membrane_float: np.ndarray,
    meta: dict,
) -> None:
    """Atomically write mask + membrane TIF + metadata JSON for one FOV.

    Args:
        out_dir: Base output directory (02_segmentation/ parent).
        fov_id: FOV identifier string.
        label_mask: (H, W) uint16 label mask.
        membrane_float: (H, W) float32 membrane, [0, 1].
        meta: Dict matching SegmentationResult fields (from segment_fov).
    """
    seg_dir = Path(out_dir) / "02_segmentation"
    seg_dir.mkdir(parents=True, exist_ok=True)

    # Validate meta with Pydantic contract before writing
    sr = SegmentationResult(fov_id=fov_id, **meta)

    mask_path = seg_dir / f"{fov_id}_mask.tif"
    mem_path = seg_dir / f"{fov_id}_membrane.tif"
    json_path = seg_dir / f"{fov_id}_seg_meta.json"

    # Atomic writes via tempfile + os.replace in same dir
    def _atomic_write_tif(path: Path, arr: np.ndarray) -> None:
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.tif")
        os.close(fd)
        try:
            tifffile.imwrite(tmp, arr)
            os.replace(tmp, path)
        except Exception:
            os.unlink(tmp)
            raise

    membrane_u16 = (membrane_float * 65535).clip(0, 65535).astype(np.uint16)
    _atomic_write_tif(mask_path, label_mask.astype(np.uint16))
    _atomic_write_tif(mem_path, membrane_u16)

    # JSON metadata (atomic)
    json_data = sr.model_dump()
    fd, tmp_json = tempfile.mkstemp(dir=seg_dir, suffix=".tmp.json")
    os.close(fd)
    try:
        with open(tmp_json, "w") as f:
            json.dump(json_data, f, indent=2)
        os.replace(tmp_json, json_path)
    except Exception:
        os.unlink(tmp_json)
        raise


def write_stage_status(
    out_dir: Path,
    status: str,
    config_hash: str | None = None,
) -> None:
    """Write or update the _stage_status.json for 02_segmentation/.

    Args:
        out_dir: Base output directory.
        status: "pending" | "running" | "complete" | "failed".
        config_hash: SHA-256 of the canonical config dump.
    """
    seg_dir = Path(out_dir) / "02_segmentation"
    seg_dir.mkdir(parents=True, exist_ok=True)
    status_path = seg_dir / "_stage_status.json"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record: dict = {"status": status, "config_hash": config_hash}
    if status == "running":
        record["started_at"] = now
    elif status in ("complete", "failed"):
        record["completed_at"] = now
    status_path.write_text(json.dumps(record, indent=2))
```

- [ ] **Step 2: Smoke-test the writer**

```bash
python -c "
import tempfile, numpy as np
from pathlib import Path
from quantipy_polarity.segment._writer import write_fov_outputs, write_stage_status
with tempfile.TemporaryDirectory() as td:
    label_mask = np.ones((32, 32), dtype=np.uint16)
    membrane = np.full((32, 32), 0.5, dtype=np.float32)
    meta = dict(n_cells_total=5, n_cells_after_filter=4, flow_threshold=0.4,
                cellprob_threshold=0.0, diameter_px=30.0, min_size_px=100, model='cpsam')
    write_fov_outputs(Path(td), 'FOV_01', label_mask, membrane, meta)
    import tifffile
    mask = tifffile.imread(str(Path(td) / '02_segmentation' / 'FOV_01_mask.tif'))
    assert mask.dtype == np.uint16, f'wrong dtype: {mask.dtype}'
    assert mask.shape == (32, 32)
    print('writer OK')
"
```
Expected: `writer OK`

- [ ] **Step 3: Commit**

```bash
git add src/quantipy_polarity/segment/_writer.py
git commit -m "feat(segment): _writer.py — atomic mask+membrane TIF + JSON output with stage status"
```

---

## Task 14: Implement `_cli_segment.py` — the real `quantipy segment` command

**Files:** Create `src/quantipy_polarity/_cli_segment.py`

Wires `io/tif.py` or `io/nd2.py` (based on `input.mode`) → `segment/cellpose_sam.py` → `segment/_writer.py`. Removes the need to pre-segment.

- [ ] **Step 1: Create `src/quantipy_polarity/_cli_segment.py`**

```python
"""CLI command: quantipy segment.

Loads FOVs from TIF or ND2 (based on input.mode in config), runs Cellpose-SAM,
and writes label masks + membrane TIFs to 02_segmentation/ in the output dir.
The outputs are Phase-2-compatible: quantipy polarity can consume them directly.

Usage:
    quantipy segment --config config.yaml --input ./raw --output ./results
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import click
import structlog

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config, InputMasks

log = structlog.get_logger()


def _config_hash(cfg: Config) -> str:
    """SHA-256 of the canonical JSON config dump."""
    canonical = cfg.model_dump_json(exclude_defaults=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@main.command("segment", short_help="[Advanced] Cellpose-SAM → label masks")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to quantipy config YAML.",
)
@click.option(
    "--input",
    "input_path",
    required=False,
    type=click.Path(path_type=Path),
    default=None,
    help="Input directory (overrides config input.path).",
)
@click.option(
    "--output",
    "output_path",
    required=False,
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (overrides config project.output_dir).",
)
@click.option("--gpu/--no-gpu", default=False, show_default=True, help="Use GPU for Cellpose.")
def segment_cmd(
    config_path: Path,
    input_path: Path | None,
    output_path: Path | None,
    gpu: bool,
) -> None:
    """Run Cellpose-SAM segmentation: TIF/ND2 input → uint16 label masks.

    \b
    Output (in <output>/02_segmentation/):
        <fov_id>_mask.tif      uint16 label mask, Phase-2-compatible
        <fov_id>_membrane.tif  uint16 membrane channel
        <fov_id>_seg_meta.json segmentation metadata per FOV
        _stage_status.json     stage completion record
    """
    cfg = Config.from_yaml(config_path)

    if input_path is not None:
        # Override config input path without mutating the Pydantic model
        # (Pydantic v2: use model_copy with update)
        cfg = cfg.model_copy(
            update={"input": cfg.input.model_copy(update={"path": input_path})}
        )
    out_dir = output_path or cfg.project.output_dir
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_cfg = cfg.input
    if isinstance(input_cfg, InputMasks):
        raise click.ClickException(
            "quantipy segment requires input.mode = 'nd2' or 'tif'. "
            "Mode 'masks' means you already have segmented masks — "
            "use `quantipy polarity` directly."
        )

    seg_cfg = cfg.segment
    if seg_cfg.model == "user_supplied":
        raise click.ClickException(
            "segment.model = 'user_supplied' bypasses Cellpose — "
            "copy your masks to 02_segmentation/ and use `quantipy polarity` directly."
        )

    chash = _config_hash(cfg)
    from quantipy_polarity.segment._writer import write_stage_status
    write_stage_status(out_dir, "running", config_hash=chash)

    try:
        _run_segment(cfg, out_dir, gpu=gpu)
    except Exception:
        write_stage_status(out_dir, "failed", config_hash=chash)
        raise

    write_stage_status(out_dir, "complete", config_hash=chash)
    log.info("segment_complete", output_dir=str(out_dir))
    click.echo(f"Segmentation complete. Masks written to {out_dir / '02_segmentation'}")


def _run_segment(cfg: Config, out_dir: Path, *, gpu: bool) -> None:
    """Internal: iterate FOVs and segment each one."""
    from quantipy_polarity.segment.cellpose_sam import segment_fov
    from quantipy_polarity.segment._writer import write_fov_outputs

    input_cfg = cfg.input
    seg_cfg = cfg.segment

    try:
        from tqdm import tqdm as _tqdm
        progress = _tqdm
    except ImportError:
        def progress(x, **_):  # type: ignore[misc]
            return x

    fov_iter = _build_fov_iterator(cfg)
    fov_list = list(fov_iter)
    log.info("segment_start", n_fovs=len(fov_list), model=seg_cfg.model)

    for fov in progress(fov_list, desc="Segmenting FOVs"):
        log.info("segmenting_fov", fov_id=fov.fov_id)

        # Convert normalized float32 [0,1] membrane to uint16 for Cellpose
        import numpy as np
        image_u16 = (fov.membrane * 65535).clip(0, 65535).astype(np.uint16)

        masks, meta = segment_fov(
            image_u16,
            model=seg_cfg.model,
            diameter=float(seg_cfg.diameter_px) if seg_cfg.diameter_px else None,
            min_size_px=seg_cfg.min_size_px,
            gpu=gpu,
        )

        write_fov_outputs(
            out_dir,
            fov_id=fov.fov_id,
            label_mask=masks,
            membrane_float=fov.membrane,
            meta=meta,
        )


def _build_fov_iterator(cfg: Config):
    """Return an iterable of TIFFOV or ND2FOV objects based on input.mode."""
    from quantipy_polarity import config as _config_mod

    input_cfg = cfg.input

    if input_cfg.mode == "tif":
        from quantipy_polarity.io.tif import iter_tif_dataset
        return iter_tif_dataset(
            tif_dir=input_cfg.path,
            channel_membrane=input_cfg.channel_membrane,
            channel_segmentation=input_cfg.channel_segmentation,
            pixel_size_um=input_cfg.pixel_size_um,
            scheme=getattr(input_cfg, "tif_scheme", "stack"),
            channel_suffix_template=getattr(input_cfg, "channel_suffix_template", "_ch{ch}"),
        )
    elif input_cfg.mode == "nd2":
        from quantipy_polarity.io.nd2 import iter_nd2_dataset
        # nd2 mode: iterate all .nd2 files in path
        nd2_files = sorted(Path(input_cfg.path).glob("*.nd2"))
        if not nd2_files:
            raise click.ClickException(f"No .nd2 files found in {input_cfg.path}")

        def _nd2_gen():
            for nd2_path in nd2_files:
                yield from iter_nd2_dataset(
                    nd2_path=nd2_path,
                    channel_membrane=input_cfg.channel_membrane,
                    channel_segmentation=input_cfg.channel_segmentation,
                    pixel_size_um_fallback=input_cfg.pixel_size_um,
                    z_policy=input_cfg.z_policy,
                    substack_range=input_cfg.substack_range,
                    fov_id_prefix="FOV",
                )

        return _nd2_gen()
    else:
        raise ValueError(f"Unexpected input.mode: {input_cfg.mode!r}")
```

- [ ] **Step 2: Register `_cli_segment` in `cli.py`**

Open `src/quantipy_polarity/cli.py`. After the last import line:
```python
from quantipy_polarity import _cli_polarity as _cli_polarity  # noqa: E402,F401
```
Add:
```python
from quantipy_polarity import _cli_segment as _cli_segment  # noqa: E402,F401
```

- [ ] **Step 3: Verify `quantipy segment --help` works**

```bash
quantipy segment --help
```
Expected output includes `Run Cellpose-SAM segmentation`, `--config`, `--input`, `--output`, `--gpu/--no-gpu`. Must NOT show stub "not implemented" error.

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/_cli_segment.py src/quantipy_polarity/cli.py
git commit -m "feat(segment): _cli_segment.py — real quantipy segment command (TIF/ND2 → masks)"
```

---

## Task 15: Remove `segment` stub from `_stubs.py`

**Files:** Modify `src/quantipy_polarity/_stubs.py`

- [ ] **Step 1: Open `_stubs.py` and remove the `segment` entry from `_STUBS`**

In `_stubs.py`, find the `_STUBS` dict entry:
```python
    "segment": (
        "[Advanced] Cellpose-SAM → label masks",
        "Phase 3 (segmentation)",
    ),
```
Remove this entry (the whole 3-line block including trailing comma). Do not touch any other entries.

- [ ] **Step 2: Verify no duplicate `segment` command**

```bash
quantipy --help 2>&1 | grep -c "segment"
```
Expected: `1` (the real command, not a stub duplicate).

- [ ] **Step 3: Run full fast-tier suite**

```bash
pytest -v --ignore=tests/segment/test_cellpose_sam.py 2>&1 | tail -3
```
Expected: approximately **117 passed** (114 + 3 preprocess stubs).

- [ ] **Step 4: Commit**

```bash
git add src/quantipy_polarity/_stubs.py
git commit -m "feat(segment): remove segment stub — real command now registered via _cli_segment"
```

---

## Task 16: CLI end-to-end smoke test for `quantipy segment`

**Files:** Create `tests/cli/__init__.py`, `tests/cli/test_cli_segment.py`

The full cellpose invocation is nightly-gated. A fast-tier sub-test verifies the CLI rejects `mode=masks` input without calling cellpose.

- [ ] **Step 1: Create `tests/cli/__init__.py`**

```python
"""CLI integration tests."""
```

- [ ] **Step 2: Write `tests/cli/test_cli_segment.py`**

```python
"""CLI tests for quantipy segment.

Fast-tier tests: reject masks-mode input; help text presence; config parsing.
Nightly-gated tests: real TIF → Cellpose → on-disk masks roundtrip.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import tifffile
from click.testing import CliRunner

from quantipy_polarity.cli import main
from tests.fixtures._build import write_synthetic_tif_stack


# ---------------------------------------------------------------------------
# Fast-tier tests (no cellpose invocation)
# ---------------------------------------------------------------------------

def _write_masks_config(tmp_path: Path) -> Path:
    cfg_text = f"""
project:
  name: test
  output_dir: {tmp_path / 'results'}
input:
  mode: masks
  path: {tmp_path / 'masks'}
  masks_dir: {tmp_path / 'masks_dir'}
  pixel_size_um: 0.65
"""
    p = tmp_path / "config.yaml"
    p.write_text(cfg_text.strip())
    return p


def _write_tif_config(tmp_path: Path, input_path: Path) -> Path:
    cfg_text = f"""
project:
  name: test
  output_dir: {tmp_path / 'results'}
input:
  mode: tif
  path: {input_path}
  channel_membrane: 0
  channel_segmentation: 1
  pixel_size_um: 0.65
  tif_scheme: stack
"""
    p = tmp_path / "config.yaml"
    p.write_text(cfg_text.strip())
    return p


def test_segment_cmd_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["segment", "--help"])
    assert result.exit_code == 0
    assert "Cellpose-SAM" in result.output or "segment" in result.output.lower()


def test_segment_cmd_rejects_masks_mode(tmp_path: Path) -> None:
    """quantipy segment should fail cleanly when mode=masks."""
    cfg_path = _write_masks_config(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["segment", "--config", str(cfg_path)])
    assert result.exit_code != 0
    assert "masks" in result.output.lower() or "polarity" in result.output.lower()


def test_segment_cmd_config_missing_file() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["segment", "--config", "/nonexistent/config.yaml"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Nightly-gated test: full TIF → Cellpose → on-disk masks
# ---------------------------------------------------------------------------

cellpose = pytest.importorskip("cellpose", reason="cellpose not installed; nightly-tier test only")


def test_segment_cmd_tif_to_masks_e2e(tmp_path: Path) -> None:
    """Full smoke: synthetic TIF → quantipy segment → validates mask output files."""
    input_dir = tmp_path / "input"
    for fov_name in ("FOV_01", "FOV_02"):
        write_synthetic_tif_stack(input_dir, fov_name, n_cells=20, image_size=128)

    cfg_path = _write_tif_config(tmp_path, input_dir)
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["segment", "--config", str(cfg_path), "--output", str(tmp_path / "results")],
    )
    assert result.exit_code == 0, f"CLI failed:\n{result.output}"

    seg_dir = tmp_path / "results" / "02_segmentation"
    assert seg_dir.exists(), "02_segmentation/ was not created"

    for fov_name in ("FOV_01", "FOV_02"):
        mask_path = seg_dir / f"{fov_name}_mask.tif"
        mem_path = seg_dir / f"{fov_name}_membrane.tif"
        assert mask_path.exists(), f"Missing mask: {mask_path}"
        assert mem_path.exists(), f"Missing membrane: {mem_path}"

        mask = tifffile.imread(str(mask_path))
        assert mask.dtype == np.uint16, f"Mask not uint16: {mask.dtype}"
        assert mask.shape == (128, 128), f"Mask shape wrong: {mask.shape}"
        n_cells = int(mask.max())
        assert n_cells >= 5, f"Suspiciously few cells ({n_cells}) for FOV {fov_name}"

    status_path = seg_dir / "_stage_status.json"
    assert status_path.exists()
    import json
    status = json.loads(status_path.read_text())
    assert status["status"] == "complete"
```

- [ ] **Step 3: Run fast-tier portion**

```bash
pytest tests/cli/test_cli_segment.py -v -k "not e2e" 2>&1 | tail -5
```
Expected: `3 passed` (help + masks-mode rejection + missing-config). The e2e test skips if cellpose absent.

- [ ] **Step 4: Run full fast suite to verify no regressions**

```bash
pytest -v --ignore=tests/segment/test_cellpose_sam.py -k "not e2e" 2>&1 | tail -3
```
Expected: approximately **120 passed**.

- [ ] **Step 5: Commit**

```bash
git add tests/cli/__init__.py tests/cli/test_cli_segment.py
git commit -m "test(cli): segment CLI smoke — masks-mode rejection + nightly e2e (gated on cellpose)"
```

---

## Task 17: Update nightly CI workflow

**Files:** Modify `.github/workflows/ci-nightly.yml`

Replace the Phase 2 placeholder nightly job with real cellpose segmentation tests.

- [ ] **Step 1: Read the current `ci-nightly.yml`**

Confirm current content: placeholder job named "nightly stub (no slow tests until Phase 3)".

- [ ] **Step 2: Replace the nightly workflow content**

Edit `.github/workflows/ci-nightly.yml` to replace the entire file content with:

```yaml
name: CI (nightly — segmentation)

on:
  schedule:
    - cron: "17 7 * * *"  # 07:17 UTC daily
  workflow_dispatch: {}

jobs:
  nightly:
    name: Cellpose-SAM segmentation tests (Python ${{ matrix.python-version }}, ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11"]
        os: [ubuntu-latest]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install with pipeline extras
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,pipeline]"

      - name: Verify cellpose importable
        run: python -c "import cellpose; print('cellpose', cellpose.__version__)"
        continue-on-error: true

      - name: Run fast suite (should be 100% pass)
        run: pytest -v --ignore=tests/segment/test_cellpose_sam.py -k "not e2e"

      - name: Run cellpose segmentation tests
        run: pytest tests/segment/test_cellpose_sam.py tests/cli/test_cli_segment.py -v
        continue-on-error: true

      - name: Report cellpose test outcome
        if: always()
        run: |
          echo "Nightly segmentation tests complete."
          echo "Failures here do NOT block releases per design spec §13."
          echo "File a GitHub issue if tests fail consistently."
```

- [ ] **Step 3: Verify YAML is valid**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci-nightly.yml')); print('YAML OK')"
```
Expected: `YAML OK`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci-nightly.yml
git commit -m "ci: update nightly workflow — real Cellpose-SAM segmentation tests (continue-on-error)"
```

---

## Task 18: Update `init-config` for TIF and ND2 modes

**Files:** Modify `src/quantipy_polarity/_cli_init_config.py`

The `init-config` command was scaffolded in Phase 1. Phase 3 makes the TIF and ND2 templates output the new `tif_scheme` field and document channel/z options accurately.

- [ ] **Step 1: Read current `src/quantipy_polarity/_cli_init_config.py`**

Locate the TIF and ND2 mode template strings. Identify where `channel_membrane`, `channel_segmentation`, `pixel_size_um` are scaffolded.

- [ ] **Step 2: Ensure the TIF template includes `tif_scheme`**

Find the section that generates the `tif` mode YAML template. After the `pixel_size_um` line, add (if not already present):
```
  tif_scheme: stack   # stack = multi-page TIF (C,H,W); multifile = per-channel TIFs named <fov_id>_ch{N}.tif
  channel_suffix_template: "_ch{ch}"  # only used for tif_scheme: multifile
```

- [ ] **Step 3: Run existing `init-config` tests**

```bash
pytest -v -k "init_config or config" 2>&1 | tail -5
```
Expected: all config tests pass (no regressions).

- [ ] **Step 4: Manually verify TIF template output**

```bash
quantipy init-config --mode tif --output /tmp/test_tif_config.yaml
cat /tmp/test_tif_config.yaml | grep tif_scheme
```
Expected: `tif_scheme: stack` appears in the output.

- [ ] **Step 5: Commit**

```bash
git add src/quantipy_polarity/_cli_init_config.py
git commit -m "feat(cli): init-config TIF template includes tif_scheme + channel_suffix_template fields"
```

---

## Task 19: Documentation updates

**Files:** Modify `docs/concepts.md`, `README.md`, `CLAUDE.md`

- [ ] **Step 1: Add TIF/ND2 ingest section to `docs/concepts.md`**

Open `docs/concepts.md`. At the end of the file, append the following section:

```markdown
## Input Modes: TIF and ND2 Ingest (Phase 3+)

QuantiPy Polarity supports three input modes. The `masks` mode (Phase 2) requires
pre-segmented label masks. The `tif` and `nd2` modes (Phase 3) accept raw
microscopy images and segment them using Cellpose-SAM.

### TIF ingest

Two schemes are supported:

**Stack scheme** (`tif_scheme: stack`): A single multi-page TIF per FOV with
channels as the first axis `(C, H, W)`. This is the default.

**Multifile scheme** (`tif_scheme: multifile`): One TIF per channel per FOV,
named `<fov_id>_ch{N}.tif` (controlled by `channel_suffix_template`).

Both schemes normalize the membrane channel to float32 [0, 1] before
segmentation. The `channel_membrane` config field selects which channel
to use (0-indexed).

### ND2 ingest

`.nd2` files are loaded via `nd2reader` (included in `[pipeline]` extras).
Pixel size is read from ND2 metadata and falls back to `pixel_size_um` from
config if metadata is missing or invalid.

Z-projection policy is controlled by `z_policy`:
- `mip`: maximum intensity projection (recommended for thick samples)
- `substack`: MIP over a specific z-range (`substack_range: [z_min, z_max]`)
- `none`: use the middle z-plane

### Cellpose-SAM segmentation

After ingest, the membrane channel (uint16) is passed to Cellpose-SAM
(`pretrained_model="cpsam"`, Cellpose ≥3.0). The `segment.diameter_px` config
field sets the expected cell diameter in pixels. Label masks are validated
for contiguous IDs (1..N, background=0) and written as uint16 TIFs.

Label masks and membrane TIFs written by `quantipy segment` are fully
compatible with `quantipy polarity` (Phase 2 masks-mode contract).

### Coordinate conventions reminder

All operations use `(y, x)` pixel coordinates (numpy/scikit-image convention).
Angles are in degrees: `[0, 180)` for axial polarity. See the contract table
in `src/quantipy_polarity/contracts.py` for the full schema.
```

- [ ] **Step 2: Update README.md Phase status and install instructions**

Open `README.md`. Find the Phase completion summary section (or the Phase roadmap table). Update Phase 3 entry to show ✅:

Change any line resembling:
```
| Phase 3 | TIF / ND2 ingest + Cellpose-SAM segmentation | 🔲 planned |
```
To:
```
| Phase 3 | TIF / ND2 ingest + Cellpose-SAM segmentation | ✅ complete |
```

Also find the Install section. Ensure it includes a note about the `[pipeline]` extra:

```markdown
### Full pipeline install (TIF/ND2 ingest + Cellpose segmentation)

```bash
pip install -e ".[dev,pipeline]"
```

The `[pipeline]` extra installs `nd2reader`, `cellpose`, `matplotlib`, `tqdm`,
and other dependencies required for raw-image processing. The base install
(`pip install -e .`) is sufficient for the `masks` mode (Phase 2 quickstart).
```

- [ ] **Step 3: Update CLAUDE.md command map table**

Open `CLAUDE.md`. In the CLI command map table, change the `segment` row:

Change:
```
| `quantipy ingest` / `segment` / `front` / `plot` / `report` | stubbed (Phases 3–5) | Stage-resume commands |
```
To:
```
| `quantipy segment` | implemented (Phase 3) | TIF/ND2 → Cellpose-SAM → label masks |
| `quantipy ingest` / `front` / `plot` / `report` | stubbed (Phases 3–5) | Stage-resume commands |
```

Also update the "Where things live" section to include:
```
- `src/quantipy_polarity/io/tif.py` — TIF ingest (stack + multifile schemes)
- `src/quantipy_polarity/io/nd2.py` — ND2 ingest via nd2reader
- `src/quantipy_polarity/segment/cellpose_sam.py` — Cellpose-SAM wrapper
- `src/quantipy_polarity/_cli_segment.py` — quantipy segment command
```

- [ ] **Step 4: Commit**

```bash
git add docs/concepts.md README.md CLAUDE.md
git commit -m "docs: Phase 3 — TIF/ND2 ingest notes in concepts.md, README status, CLAUDE.md command map"
```

---

## Task 20: Acceptance + tag

**Files:** No new files. Verify everything end-to-end on a fresh clone.

- [ ] **Step 1: Fresh clone and install**

```bash
cd /tmp
git clone https://github.com/mcleanT/QuantiPy-Polarity QuantiPy-phase3-acceptance
cd QuantiPy-phase3-acceptance
pip install -e ".[dev,pipeline]"
```
Expected: install completes without errors.

- [ ] **Step 2: Run fast-tier suite (must be 100% pass)**

```bash
pytest -v --ignore=tests/segment/test_cellpose_sam.py -k "not e2e" 2>&1 | tail -5
```
Expected: all tests pass; no skips other than gated nd2reader/cellpose tests. Target: **≥ 104 passed**.

- [ ] **Step 3: Verify `quantipy segment --help` is real (not stub)**

```bash
quantipy segment --help | head -10
```
Expected: shows the real docstring ("Run Cellpose-SAM segmentation...") — not the stub "not implemented" message.

- [ ] **Step 4: Verify `quantipy segment` rejects `masks` mode gracefully**

```bash
python -c "
import tempfile, pathlib, textwrap
from click.testing import CliRunner
from quantipy_polarity.cli import main
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    cfg = td / 'cfg.yaml'
    cfg.write_text(textwrap.dedent('''
        project:
          name: test
          output_dir: ./results
        input:
          mode: masks
          path: ./masks
          masks_dir: ./masks_dir
          pixel_size_um: 0.65
    ''').strip())
    r = CliRunner().invoke(main, ['segment', '--config', str(cfg)])
    assert r.exit_code != 0
    print('masks-mode rejection OK')
"
```
Expected: `masks-mode rejection OK`.

- [ ] **Step 5: Verify `io/nd2.py` imports cleanly without nd2reader (lazy import)**

```bash
python -c "
from quantipy_polarity.io.nd2 import ND2FOV, iter_nd2_dataset
print('nd2 module lazy import OK')
"
```
Expected: `nd2 module lazy import OK`

- [ ] **Step 6: Verify fast-tier CI passes (push to `main`)**

```bash
git push origin main
```
Wait for GitHub Actions CI (`ci.yml`) to show green on `main`.

- [ ] **Step 7: Tag `phase-3-complete`**

```bash
git tag -a phase-3-complete -m "Phase 3 complete: TIF/ND2 ingest + Cellpose-SAM segmentation"
git push origin phase-3-complete
```

- [ ] **Step 8: Confirm nightly workflow triggers on the tag**

Check `.github/workflows/ci-nightly.yml` is present and syntactically valid. The nightly run will execute Cellpose-SAM tests; `continue-on-error: true` ensures tag is valid even if Cellpose model weights are unavailable in CI.

---

*End of Phase 3 Plan.*
