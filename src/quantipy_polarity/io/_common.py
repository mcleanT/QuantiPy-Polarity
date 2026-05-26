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
