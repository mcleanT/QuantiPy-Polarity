"""Generate synthetic demo TIFs and demo/config.yaml.

Produces: demo/fov_A_membrane.tif, demo/fov_A_mask.tif, (same for fov_B)
and demo/config.yaml in masks mode.

Run from repo root:
    python scripts/generate_demo_bundle.py
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import tifffile
import yaml

_OUT = Path("demo")
_SIZE = 512
_SEED = 7


def _synthetic_cell(
    rng: np.random.Generator,
    cy: int, cx: int, radius: int = 28
) -> tuple[np.ndarray, np.ndarray]:
    """Return (membrane_patch, mask_patch) for a single synthetic cell."""
    H = W = radius * 2 + 4
    y, x = np.mgrid[:H, :W]
    yc, xc = H // 2, W // 2
    dist = np.sqrt((y - yc) ** 2 + (x - xc) ** 2)
    membrane = np.zeros((H, W), dtype=np.float64)
    ring = np.exp(-((dist - radius) ** 2) / 8.0)
    membrane += ring * rng.uniform(2000, 8000)
    membrane += rng.normal(0, 100, (H, W))
    membrane = np.clip(membrane, 0, 65535).astype(np.uint16)
    mask = (dist < radius - 2).astype(np.uint16)
    return membrane, mask


def generate_fov(name: str, rng: np.random.Generator, cell_count: int = 40) -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    mem_img = np.zeros((_SIZE, _SIZE), dtype=np.uint16)
    mask_img = np.zeros((_SIZE, _SIZE), dtype=np.uint16)
    # Background noise
    mem_img += rng.integers(200, 600, (_SIZE, _SIZE), dtype=np.uint16)
    # Grid layout with jitter
    cols = 7
    for i in range(cell_count):
        cell_id = i + 1
        col = i % cols
        row = i // cols
        cy = 55 + row * 70 + int(rng.integers(-8, 8))
        cx = 55 + col * 70 + int(rng.integers(-8, 8))
        radius = int(rng.integers(22, 32))
        patch_mem, patch_mask = _synthetic_cell(rng, cy, cx, radius)
        ph, pw = patch_mem.shape
        y0 = max(0, cy - ph // 2)
        x0 = max(0, cx - pw // 2)
        y1 = min(_SIZE, y0 + ph)
        x1 = min(_SIZE, x0 + pw)
        patch_h = y1 - y0
        patch_w = x1 - x0
        mem_img[y0:y1, x0:x1] = np.maximum(
            mem_img[y0:y1, x0:x1], patch_mem[:patch_h, :patch_w]
        )
        cell_region = (patch_mask[:patch_h, :patch_w] > 0)
        mask_img[y0:y1, x0:x1][cell_region] = cell_id

    tifffile.imwrite(str(_OUT / f"{name}_membrane.tif"), mem_img)
    tifffile.imwrite(str(_OUT / f"{name}_mask.tif"), mask_img)
    n_cells = int(mask_img.max())
    print(f"  {name}: {n_cells} cells, mask max label = {n_cells}")


def write_config() -> None:
    config = {
        "input": {
            "mode": "masks",
            "path": "demo",
            "masks_dir": "demo",
            "pixel_size_um": 0.1625,
            "channel_membrane": 0,
        },
        "segment": {
            "diameter_px": 28,
        },
        "polarity": {
            "method": "boundary_pca",
        },
        "migration": {
            "detect_front": False,
        },
        "viz": {
            "rose_bins": 24,
        },
    }
    with open(_OUT / "config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"  config.yaml written")


if __name__ == "__main__":
    rng = np.random.default_rng(_SEED)
    print("Generating demo bundle ...")
    generate_fov("fov_A", rng, cell_count=40)
    generate_fov("fov_B", rng, cell_count=35)
    write_config()
    print(f"Done. Files written to {_OUT}/")
