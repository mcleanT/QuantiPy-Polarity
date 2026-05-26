"""HTML report builder for quantipy run outputs.

Gathers all pipeline outputs from a run directory, downscales figure PNGs
to thumbnails (max 400 px longest edge), base64-encodes them, and renders
the Jinja2 template to a single self-contained HTML file.

No external URLs, no CDN dependencies. All CSS is inline in the template.
"""

from __future__ import annotations

import base64
import io
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from quantipy_polarity.config import Config

log = structlog.get_logger()

_THUMBNAIL_MAX_PX = 400  # longest edge of embedded thumbnails


def _encode_png_thumbnail(path: Path, max_px: int = _THUMBNAIL_MAX_PX) -> str:
    """Load a PNG, downscale to max_px on longest edge, return base64 data URI.

    Uses PIL (Pillow) which is a transitive dependency via matplotlib/scikit-image.

    Args:
        path: Path to PNG file.
        max_px: Maximum pixels on the longest edge.

    Returns:
        base64 data URI string: "data:image/png;base64,<data>"
    """
    from PIL import Image

    img = Image.open(path)
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{data}"


def _encode_file_b64(path: Path) -> str:
    """Base64-encode any binary file as a data URI (PDF → application/pdf)."""
    ext = path.suffix.lower()
    mime = "application/pdf" if ext == ".pdf" else "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def gather_report_inputs(results_dir: Path) -> dict:
    """Collect all inputs needed to render the HTML report template.

    Args:
        results_dir: Base run output directory.

    Returns:
        Dictionary with keys used by the Jinja2 template.
    """
    import pandas as pd
    import yaml

    data: dict = {
        "project_name": results_dir.name,
        "results_dir": str(results_dir),
        "n_fovs": 0,
        "n_cells": 0,
        "median_magnitude": None,
        "config_yaml": "",
        "fov_rows": [],
        "has_rose": False,
        "aggregate_rose_b64": None,
        "has_summary": False,
        "population_summary_b64": None,
        "stage_statuses": {},
    }

    # Load per_cell parquet for summary metrics
    per_cell_path = results_dir / "05_aggregated" / "per_cell.parquet"
    if per_cell_path.exists():
        df = pd.read_parquet(per_cell_path)
        data["n_cells"] = len(df)
        data["n_fovs"] = int(df["fov_id"].nunique())
        if "magnitude" in df.columns and len(df) > 0:
            data["median_magnitude"] = round(float(df["magnitude"].median()), 4)

    # Load config snapshot
    config_snapshot = results_dir / "config.snapshot.yaml"
    if config_snapshot.exists():
        data["config_yaml"] = config_snapshot.read_text()

    # Load stage statuses
    stage_status_dir = results_dir / "stage_status"
    if stage_status_dir.exists():
        for json_path in sorted(stage_status_dir.glob("*.json")):
            import json as _json
            try:
                rec = _json.loads(json_path.read_text())
                data["stage_statuses"][json_path.stem] = rec.get("status", "unknown")
            except Exception:
                data["stage_statuses"][json_path.stem] = "unreadable"

    # Per-FOV gallery: vector map PNG + rose PNG per FOV
    plots_dir = results_dir / "06_plots"
    fov_rows: list[dict] = []
    if plots_dir.exists():
        vec_dir = plots_dir / "vector_maps"
        rose_dir = plots_dir / "roses"
        # Collect all known FOV IDs from vector maps
        fov_ids: list[str] = []
        if vec_dir.exists():
            fov_ids = sorted(
                p.stem.replace("_vector_map", "").replace("_polarity_map", "")
                for p in vec_dir.glob("*.png")
            )
        for fov_id in fov_ids:
            row: dict = {"fov_id": fov_id, "vector_b64": None, "rose_b64": None, "n_cells": 0}
            vec_png = vec_dir / f"{fov_id}.png"
            if not vec_png.exists():
                # Try alternate naming patterns written by viz/vector_map.py
                candidates = list(vec_dir.glob(f"{fov_id}*.png"))
                vec_png = candidates[0] if candidates else vec_png
            if vec_png.exists():
                row["vector_b64"] = _encode_png_thumbnail(vec_png)
            rose_png = rose_dir / f"rose_{fov_id}.png" if rose_dir.exists() else None
            if rose_png and rose_png.exists():
                row["rose_b64"] = _encode_png_thumbnail(rose_png)
            # Cell count for this FOV
            if per_cell_path.exists():
                df = pd.read_parquet(per_cell_path)
                n = int((df["fov_id"] == fov_id).sum())
                row["n_cells"] = n
            fov_rows.append(row)
    data["fov_rows"] = fov_rows

    # Aggregate rose
    agg_rose = plots_dir / "rose_aggregate.png" if plots_dir.exists() else None
    if agg_rose and agg_rose.exists():
        data["has_rose"] = True
        data["aggregate_rose_b64"] = _encode_png_thumbnail(agg_rose, max_px=600)

    # Population summary
    summary_png = plots_dir / "population_summary.png" if plots_dir.exists() else None
    if summary_png and summary_png.exists():
        data["has_summary"] = True
        data["population_summary_b64"] = _encode_png_thumbnail(summary_png, max_px=800)

    return data


def build_report(
    results_dir: Path,
    output_html: Path,
    *,
    cfg: "Config | None" = None,
) -> None:
    """Render the self-contained HTML report and write it atomically.

    Args:
        results_dir: Base run output directory.
        output_html: Destination HTML file path.
        cfg: Optional Config object (used for project.name if available).
    """
    from importlib.resources import files as _pkg_files
    from jinja2 import Environment, BaseLoader

    template_path = Path(__file__).parent / "templates" / "report.html.j2"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Report template not found: {template_path}. "
            "This is a packaging error — template should be included with the package."
        )

    template_source = template_path.read_text(encoding="utf-8")
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(template_source)

    template_data = gather_report_inputs(results_dir)
    if cfg is not None and cfg.project.name:
        template_data["project_name"] = cfg.project.name

    html_content = template.render(**template_data)

    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=output_html.parent, suffix=".tmp.html")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html_content)
        os.replace(tmp, output_html)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    log.info("report_html_written", path=str(output_html), size_kb=output_html.stat().st_size // 1024)
