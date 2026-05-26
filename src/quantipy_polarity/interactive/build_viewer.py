"""Build a self-contained HTML per-cell viewer from a quantipy run directory."""

from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_REQUIRED_COLUMNS = {"fov_id", "cell_id", "qp_magnitude", "qp_axis_deg"}


def _get_version() -> str:
    try:
        from importlib.metadata import version

        return version("quantipy-polarity")
    except Exception:
        return "unknown"


def build_viewer(
    results_dir: Path,
    output_path: Path,
    *,
    fov: str | None = None,
) -> None:
    """Build a self-contained HTML per-cell viewer from a quantipy run directory.

    Args:
        results_dir: Path to a completed quantipy run directory (must contain
            ``05_aggregated/per_cell.parquet`` and ``03_polarity/maps/*.png``).
        output_path: Destination path for the HTML file. Parent must exist.
        fov: If given, only embed data for this FOV (default: all FOVs).

    Raises:
        FileNotFoundError: If ``results_dir`` is missing required files.
        ValueError: If ``per_cell.parquet`` has no rows or no recognised columns.
    """
    results_dir = Path(results_dir)
    parquet_path = results_dir / "05_aggregated" / "per_cell.parquet"
    maps_dir = results_dir / "03_polarity" / "maps"

    if not parquet_path.exists():
        raise FileNotFoundError(f"per_cell.parquet not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    if df.empty:
        raise ValueError("per_cell.parquet contains no rows")

    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"per_cell.parquet missing required columns: {missing}")

    if fov is not None:
        df = df[df["fov_id"] == fov]
        if df.empty:
            raise ValueError(f"No rows found for fov_id={fov!r}")

    # Collect FOV list (preserving insertion order)
    fovs: list[str] = list(dict.fromkeys(df["fov_id"].tolist()))

    # Encode per-FOV polarity map PNGs as base64 strings
    fov_images: dict[str, str] = {}
    for fov_id in fovs:
        candidates = sorted(maps_dir.glob(f"{fov_id}*.png")) if maps_dir.exists() else []
        if candidates:
            img_bytes = candidates[0].read_bytes()
            fov_images[fov_id] = base64.b64encode(img_bytes).decode("ascii")
        else:
            fov_images[fov_id] = ""  # viewer shows placeholder text if empty

    # Serialise per-cell rows as a compact JSON array
    # Only include columns that are JSON-serialisable; cast numpy types
    display_cols = [
        c for c in df.columns if df[c].dtype.kind in ("f", "i", "u", "b", "O", "U")
    ]
    records = df[display_cols].to_dict(orient="records")

    # Ensure all values are plain Python types (pandas may return np.float64)
    def _coerce(v: object) -> object:
        import numpy as np  # noqa: PLC0415

        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, float) and (v != v):  # NaN
            return None
        return v

    clean_records = [{k: _coerce(v) for k, v in row.items()} for row in records]
    cells_json = json.dumps(clean_records, separators=(",", ":"))

    # Render template
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("viewer.html.j2")
    html_content = template.render(
        fovs=fovs,
        fov_images=fov_images,
        cells_json=cells_json,
        display_cols=display_cols,
        version=_get_version(),
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: temp file → os.replace
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", dir=output_path.parent, delete=False
    )
    try:
        tmp.write(html_content)
        tmp.flush()
        tmp.close()
        os.replace(tmp.name, output_path)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise
