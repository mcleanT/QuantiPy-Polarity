"""Load paired (label_mask, membrane) FOVs from disk.

This is the entry point for the `masks` input mode in v0.1.0 — user provides
a directory of label-mask TIFs paired with a directory of membrane TIFs, and
this module yields (fov_id, label_mask, membrane) tuples ready for boundary-PCA.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import tifffile

from quantipy_polarity.io._common import pair_masks_with_membranes


@dataclass(frozen=True)
class MaskFOV:
    """One paired FOV: label mask + membrane channel + identifier."""

    fov_id: str
    label_mask: np.ndarray  # (H, W) uint16
    membrane: np.ndarray  # (H, W) float32 or float64

    def __post_init__(self) -> None:
        if self.label_mask.shape != self.membrane.shape:
            raise ValueError(
                f"{self.fov_id}: mask shape {self.label_mask.shape} != "
                f"membrane shape {self.membrane.shape}"
            )
        if self.label_mask.ndim != 2:
            raise ValueError(f"{self.fov_id}: label_mask must be 2D, got ndim={self.label_mask.ndim}")
        if self.label_mask.dtype not in (np.uint8, np.uint16, np.uint32):
            raise ValueError(
                f"{self.fov_id}: label_mask dtype must be unsigned int, got {self.label_mask.dtype}"
            )


def load_mask_fov(
    membrane_path: Path,
    mask_path: Path,
    fov_id: str,
    channel_membrane: int = 0,
) -> MaskFOV:
    """Read one (membrane, mask) pair from disk and return a validated MaskFOV.

    Membrane TIF may be single-channel (2D) or multi-channel (3D); `channel_membrane`
    selects the channel index. Mask TIF must be 2D unsigned-int.
    """
    membrane = tifffile.imread(membrane_path)
    if membrane.ndim == 3:
        # Assume last axis is channels
        if membrane.shape[-1] <= channel_membrane:
            raise IndexError(
                f"{fov_id}: requested channel {channel_membrane} but membrane has only "
                f"{membrane.shape[-1]} channels"
            )
        membrane = membrane[..., channel_membrane]
    elif membrane.ndim != 2:
        raise ValueError(f"{fov_id}: membrane TIF must be 2D or 3D (H,W,C); got ndim={membrane.ndim}")

    label_mask = tifffile.imread(mask_path)
    if label_mask.ndim != 2:
        raise ValueError(f"{fov_id}: mask TIF must be 2D; got ndim={label_mask.ndim}")
    if label_mask.dtype.kind != "u":
        # Some QP outputs are float — cast safely
        label_mask = label_mask.astype(np.uint16)

    # Normalize membrane to float32 [0, 1] if it looks integer-typed
    if membrane.dtype.kind in ("u", "i"):
        max_val = float(np.iinfo(membrane.dtype).max)
        membrane = (membrane.astype(np.float32) / max_val).clip(0.0, 1.0)
    else:
        membrane = membrane.astype(np.float32)

    return MaskFOV(fov_id=fov_id, label_mask=label_mask, membrane=membrane)


def iter_mask_dataset(
    membrane_dir: Path,
    masks_dir: Path,
    channel_membrane: int = 0,
) -> Iterator[MaskFOV]:
    """Yield validated MaskFOV objects for every paired FOV in the directory.

    Pairing is by fov_id_from_path (see io/_common.py).
    """
    for fov_id, mp, mskp in pair_masks_with_membranes(membrane_dir, masks_dir):
        yield load_mask_fov(mp, mskp, fov_id, channel_membrane=channel_membrane)
