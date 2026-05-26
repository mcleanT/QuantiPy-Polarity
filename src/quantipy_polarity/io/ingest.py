"""FOV normalization: nd2/tif → per-FOV float32 membrane arrays + disk TIFs.

Provides:
    build_fov_iterator(cfg) -> Iterable[FOVData]
        Unified iterator over all input modes (nd2, tif, masks).
        Consolidates the _build_fov_iterator logic from _cli_segment.py.

    write_ingest_outputs(out_dir, fov_id, membrane_float) -> Path
        Write a normalized per-FOV membrane TIF to 01_ingest/<fov_id>_membrane.tif.
        Atomic write (tmp + os.replace). Returns the written path.

    ingest_fovs(cfg, out_dir) -> list[str]
        Iterate all FOVs, call write_ingest_outputs for each, return list of fov_ids.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import structlog
import tifffile

if TYPE_CHECKING:
    from quantipy_polarity.config import Config

log = structlog.get_logger()

_INGEST_DIR = "01_ingest"


def build_fov_iterator(cfg: "Config"):
    """Return an iterable of FOV objects for the configured input mode.

    Works for all three input modes: nd2, tif, masks.
    Each yielded object has .fov_id (str) and .membrane (float32 H×W array [0,1]).

    Args:
        cfg: Loaded Config object.

    Returns:
        Iterable of FOV data objects.
    """

    input_cfg = cfg.input

    if input_cfg.mode == "tif":
        from quantipy_polarity.io.tif import iter_tif_dataset

        return iter_tif_dataset(
            tif_dir=input_cfg.path,
            channel_membrane=input_cfg.channel_membrane,
            channel_segmentation=input_cfg.channel_segmentation,
            pixel_size_um=input_cfg.pixel_size_um,
            scheme=getattr(input_cfg, "tif_scheme", "stack"),
            channel_suffix_template=getattr(
                input_cfg, "channel_suffix_template", "_ch{ch}"
            ),
        )
    elif input_cfg.mode == "nd2":
        from quantipy_polarity.io.nd2 import iter_nd2_dataset

        nd2_files = sorted(Path(input_cfg.path).glob("*.nd2"))
        if not nd2_files:
            raise FileNotFoundError(f"No .nd2 files found in {input_cfg.path}")

        def _gen():
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

        return _gen()
    elif input_cfg.mode == "masks":
        from quantipy_polarity.io.masks import iter_mask_dataset

        return iter_mask_dataset(
            membrane_dir=input_cfg.path,
            masks_dir=input_cfg.masks_dir,
            channel_membrane=input_cfg.channel_membrane,
        )
    else:
        raise ValueError(f"Unknown input.mode: {input_cfg.mode!r}")


def write_ingest_outputs(
    out_dir: Path, fov_id: str, membrane_float: np.ndarray
) -> Path:
    """Write a normalized per-FOV membrane TIF to 01_ingest/ atomically.

    The TIF is written as uint16 (membrane_float * 65535, clipped) so it is
    consistent with the format used by segment/_writer.py for the membrane channel.

    Args:
        out_dir: Base output directory (01_ingest/ is created inside here).
        fov_id: FOV identifier string.
        membrane_float: (H, W) float32 array in [0, 1].

    Returns:
        Path to the written TIF file.
    """
    ingest_dir = Path(out_dir) / _INGEST_DIR
    ingest_dir.mkdir(parents=True, exist_ok=True)

    out_path = ingest_dir / f"{fov_id}_membrane.tif"
    membrane_u16 = (membrane_float * 65535).clip(0, 65535).astype(np.uint16)

    fd, tmp = tempfile.mkstemp(dir=ingest_dir, suffix=".tmp.tif")
    os.close(fd)
    try:
        tifffile.imwrite(tmp, membrane_u16)
        os.replace(tmp, out_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    log.info("wrote ingest TIF", fov_id=fov_id, path=str(out_path))
    return out_path


def ingest_fovs(cfg: "Config", out_dir: Path) -> list[str]:
    """Iterate all FOVs, write per-FOV membrane TIFs, return list of fov_ids.

    Args:
        cfg: Loaded Config object.
        out_dir: Base output directory.

    Returns:
        List of fov_id strings in the order processed.
    """
    fov_ids: list[str] = []
    for fov in build_fov_iterator(cfg):
        write_ingest_outputs(out_dir, fov.fov_id, fov.membrane)
        fov_ids.append(fov.fov_id)
    log.info("ingest complete", n_fovs=len(fov_ids))
    return fov_ids
