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
    membrane: np.ndarray  # (H, W) float32, [0, 1]
    nuclear: np.ndarray | None  # (H, W) float32, [0, 1] or None
    pixel_size_um: float
    raw_dtype: np.dtype  # original dtype before normalization

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
            raise ValueError(f"{fov_id}: nuclear TIF must be 2D for multifile scheme")
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
        raise ValueError(
            f"Unknown TIF scheme: {scheme!r}. Expected 'stack' or 'multifile'."
        )
