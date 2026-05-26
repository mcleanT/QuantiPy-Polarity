"""Procedural synthetic-FOV builder with known per-cell polarity ground truth.

Generates a Voronoi cell field at fixed seed, places per-cell signal modulated
by cos(2(phi - theta_i)) along each cell's boundary where phi is the angle
from the cell centroid and theta_i is the seeded ground-truth axis.

The resulting (label_mask, membrane, theta_ground_truth) tuple is the canonical
test input for boundary_pca and the end-to-end Phase 2 pipeline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile


def build_synthetic_fov(
    *,
    n_cells: int = 80,
    image_size: int = 512,
    seed: int = 20260526,
    border_margin: int = 32,
    membrane_thickness: float = 1.5,
    polarity_amplitude: float = 0.7,
    noise_sigma: float = 0.03,
) -> dict:
    """Generate one synthetic FOV with known per-cell polarity axes.

    Returns a dict with keys:
        label_mask: (H, W) uint16 array; 0 = background, 1..N = cells
        membrane:   (H, W) float32 array; per-pixel membrane signal in [0, 1]
        theta_truth: dict[int, float] mapping cell_id -> ground-truth axial
                     angle in degrees, range [0, 180).
        centroids:  dict[int, tuple[float, float]] mapping cell_id ->
                    (centroid_y, centroid_x) for reference.

    The generator is fully deterministic for a given seed.
    """
    rng = np.random.default_rng(seed)

    # 1. Seed random cell centers, well-spaced via simple jittered grid
    grid_side = int(np.ceil(np.sqrt(n_cells)))
    step = (image_size - 2 * border_margin) / grid_side
    centers = []
    for r in range(grid_side):
        for c in range(grid_side):
            if len(centers) >= n_cells:
                break
            cy = border_margin + step * (r + 0.5) + rng.uniform(-step * 0.2, step * 0.2)
            cx = border_margin + step * (c + 0.5) + rng.uniform(-step * 0.2, step * 0.2)
            centers.append((cy, cx))
    centers = np.array(centers[:n_cells])

    # 2. Voronoi tessellation → label mask via nearest-neighbor assignment
    yy, xx = np.mgrid[0:image_size, 0:image_size]
    dists = (yy[..., None] - centers[:, 0]) ** 2 + (xx[..., None] - centers[:, 1]) ** 2
    label_mask = (np.argmin(dists, axis=-1) + 1).astype(np.uint16)

    # 3. Per-cell ground-truth axis (axial: [0, 180) degrees)
    theta_truth = {i + 1: float(rng.uniform(0.0, 180.0)) for i in range(n_cells)}

    # 4. Build membrane channel: signal concentrated along boundary,
    #    weighted by cos(2 * (phi - theta_i)) so signal peaks at theta and theta+180
    membrane = np.zeros((image_size, image_size), dtype=np.float32)
    # Find boundary pixels per cell (where neighbor has different label)
    pad = np.pad(label_mask, 1, mode="edge")
    is_boundary = (
        (pad[1:-1, 1:-1] != pad[:-2, 1:-1])
        | (pad[1:-1, 1:-1] != pad[2:, 1:-1])
        | (pad[1:-1, 1:-1] != pad[1:-1, :-2])
        | (pad[1:-1, 1:-1] != pad[1:-1, 2:])
    ) & (label_mask > 0)

    centroids = {}
    for cell_id in range(1, n_cells + 1):
        cell_pixels = np.argwhere(label_mask == cell_id)
        if cell_pixels.size == 0:
            continue
        cy_mean = cell_pixels[:, 0].mean()
        cx_mean = cell_pixels[:, 1].mean()
        centroids[cell_id] = (float(cy_mean), float(cx_mean))

        boundary_pixels = np.argwhere(is_boundary & (label_mask == cell_id))
        if boundary_pixels.size == 0:
            continue
        dy = boundary_pixels[:, 0] - cy_mean
        dx = boundary_pixels[:, 1] - cx_mean
        phi = np.arctan2(dy, dx)  # radians
        theta_rad = np.deg2rad(theta_truth[cell_id])
        signal = 0.5 + 0.5 * polarity_amplitude * np.cos(2.0 * (phi - theta_rad))
        # Smear signal by `membrane_thickness` via Gaussian-weighted accumulation
        for (py, px), s in zip(boundary_pixels, signal):
            y0 = max(0, int(py - 2 * membrane_thickness))
            y1 = min(image_size, int(py + 2 * membrane_thickness) + 1)
            x0 = max(0, int(px - 2 * membrane_thickness))
            x1 = min(image_size, int(px + 2 * membrane_thickness) + 1)
            yyk = np.arange(y0, y1)[:, None]
            xxk = np.arange(x0, x1)[None, :]
            kernel = np.exp(
                -((yyk - py) ** 2 + (xxk - px) ** 2) / (2 * membrane_thickness**2)
            )
            membrane[y0:y1, x0:x1] = np.maximum(membrane[y0:y1, x0:x1], kernel * s)

    # 5. Additive Gaussian noise on top
    membrane = membrane + rng.normal(0.0, noise_sigma, size=membrane.shape).astype(
        np.float32
    )
    membrane = np.clip(membrane, 0.0, 1.0)

    return {
        "label_mask": label_mask,
        "membrane": membrane,
        "theta_truth": theta_truth,
        "centroids": centroids,
    }


def save_synthetic_fov(out_path: Path, **build_kwargs) -> dict:
    """Build the fixture and save to .npz; return the same dict for reuse in tests."""
    data = build_synthetic_fov(**build_kwargs)
    np.savez_compressed(
        out_path,
        label_mask=data["label_mask"],
        membrane=data["membrane"],
        theta_truth_keys=np.array(list(data["theta_truth"].keys()), dtype=np.uint16),
        theta_truth_vals=np.array(list(data["theta_truth"].values()), dtype=np.float32),
    )
    return data


def load_synthetic_fov(npz_path: Path) -> dict:
    """Inverse of save_synthetic_fov; reconstructs the dict from .npz."""
    z = np.load(npz_path)
    keys = z["theta_truth_keys"]
    vals = z["theta_truth_vals"]
    return {
        "label_mask": z["label_mask"],
        "membrane": z["membrane"],
        "theta_truth": dict(zip(keys.tolist(), vals.tolist())),
    }


if __name__ == "__main__":
    # Allow `python tests/fixtures/_build.py tests/fixtures/synthetic_fov.npz`
    import sys

    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    save_synthetic_fov(out)
    print(f"Wrote {out}")


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
    tifffile.imwrite(out_dir / f"{fov_id}.tif", stack, photometric="minisblack")
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
    tifffile.imwrite(out_dir / f"{fov_id}_ch0.tif", membrane_u16)
    tifffile.imwrite(out_dir / f"{fov_id}_ch1.tif", nuclear_u16)
    return data
