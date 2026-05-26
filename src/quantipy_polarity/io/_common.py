"""Shared utilities for the io/ submodules.

Functions here are private to the io package — not part of the public API.
"""

from __future__ import annotations

import re
from pathlib import Path


_FOV_ID_RE = re.compile(r"(FOV[_-]?\d+)", re.IGNORECASE)


def fov_id_from_path(path: Path | str) -> str:
    """Extract an FOV identifier from a path.

    Strategy:
      1. If filename matches a 'FOV_NNN' or 'FOV-NNN' or 'fovNNN' pattern, return the matched substring normalized to 'FOV_NNN' (zero-padded width preserved).
      2. Otherwise return the file stem (filename without extension).

    Examples:
        fov_id_from_path('/a/b/FOV_01_membrane.tif') -> 'FOV_01'
        fov_id_from_path('FOV01.tif') -> 'FOV_01'
        fov_id_from_path('sample_x.tif') -> 'sample_x'
    """
    p = Path(path)
    m = _FOV_ID_RE.search(p.name)
    if m:
        match = m.group(1).upper()
        # Normalize: strip separator, re-join with single underscore
        digits = re.search(r"\d+", match).group(0)
        return f"FOV_{digits}"
    return p.stem


def pair_masks_with_membranes(
    membrane_dir: Path,
    masks_dir: Path,
    membrane_ext: str = ".tif",
    mask_ext: str = ".tif",
) -> list[tuple[str, Path, Path]]:
    """Pair membrane TIFs with their corresponding mask TIFs by FOV ID.

    Returns a sorted list of (fov_id, membrane_path, mask_path) tuples.
    Raises FileNotFoundError if a membrane TIF has no matching mask (or vice versa).
    """
    membrane_files = sorted(Path(membrane_dir).glob(f"*{membrane_ext}"))
    mask_files = sorted(Path(masks_dir).glob(f"*{mask_ext}"))
    if not membrane_files:
        raise FileNotFoundError(f"No {membrane_ext} files found in {membrane_dir}")
    if not mask_files:
        raise FileNotFoundError(f"No {mask_ext} files found in {masks_dir}")

    mask_index = {fov_id_from_path(p): p for p in mask_files}
    paired = []
    for mp in membrane_files:
        fov = fov_id_from_path(mp)
        if fov not in mask_index:
            raise FileNotFoundError(
                f"Membrane {mp.name} (fov_id={fov}) has no matching mask in {masks_dir}"
            )
        paired.append((fov, mp, mask_index[fov]))
    return paired


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
