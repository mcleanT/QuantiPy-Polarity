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
    membrane: np.ndarray  # (H, W) float32, [0, 1]
    nuclear: np.ndarray | None  # (H, W) float32, [0, 1] or None
    pixel_size_um: float  # from ND2 metadata or config fallback
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


def _z_project(
    stack: np.ndarray, policy: str, substack_range: tuple[int, int] | None
) -> np.ndarray:
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
    raise ValueError(
        f"Unknown z_policy: {policy!r}. Expected 'mip', 'substack', or 'none'."
    )


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
