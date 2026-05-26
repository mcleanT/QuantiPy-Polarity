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
