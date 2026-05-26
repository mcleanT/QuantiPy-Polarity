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
