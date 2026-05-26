# Interactive Viewer

The interactive viewer is a self-contained HTML file that lets you inspect
individual cells from a completed QuantiPy Polarity run — no server, no Python
environment required after the file has been generated.

---

## Opening the viewer

### Via the CLI (quickest)

```bash
quantipy debug --results ./demo_results
open ./demo_results/viewer.html      # macOS
xdg-open ./demo_results/viewer.html  # Linux
```

`quantipy debug` calls `build_viewer` internally and writes
`viewer.html` into the run directory.  Pass `--output <path>` to write
elsewhere, or `--fov FOV_01` to limit the viewer to a single FOV.

### Via the Python API

```python
from pathlib import Path
from quantipy_polarity.interactive import build_viewer

build_viewer(
    results_dir=Path("./demo_results"),
    output_path=Path("./demo_results/viewer.html"),
)
```

See [docs/api-reference.md](api-reference.md) for the full `build_viewer`
signature.

---

## Layout

The viewer is divided into three panels rendered side-by-side:

| Panel | Contents |
|-------|----------|
| **FOV image** | The polarity vector-map PNG for the currently selected FOV.  Cells are overlaid with their polarity arrows. |
| **Cell list** | A scrollable table of all cells in the current FOV.  Clicking a row highlights the corresponding cell in the FOV image panel. |
| **Info** | All columns from `per_cell.parquet` for the selected cell (cell ID, polarity magnitude, polarity angle, distance to front, condition, …). |

---

## Keyboard navigation

| Key | Action |
|-----|--------|
| `←` / `→` | Navigate to the previous / next FOV. |
| `↑` / `↓` | Move the selection up / down within the cell list of the current FOV. |

---

## What data is shown

The viewer embeds **all columns** present in `05_aggregated/per_cell.parquet`
for the selected run.  Typical columns include:

| Column | Description |
|--------|-------------|
| `fov_id` | Field-of-view identifier. |
| `cell_id` | Integer label from the segmentation mask. |
| `qp_magnitude` | Polarity magnitude (0–1; higher = more polarised). |
| `qp_angle_deg` | Polarity angle in degrees (0–360). |
| `centroid_x`, `centroid_y` | Cell centroid in pixels. |
| `dist_to_front_px` | Distance to migration front (present if `front` stage ran). |
| `condition` | Experimental condition label (if provided at ingest). |

Additional columns written by experimental analyses are also displayed if
present.

---

## Sharing

The HTML file is **fully self-contained**: all images are embedded as base64
data URIs and all JavaScript is inlined.  You can email the file, copy it to a
shared drive, or attach it to a Slack message and the recipient can open it in
any modern browser without installing anything.

---

## Headless use

`build_viewer` (and therefore `quantipy debug`) works without a display.
It writes the HTML file and exits; it does not open a browser window.  The
`DISPLAY` environment variable is not consulted.  This makes it safe to call
from HPC batch scripts or CI pipelines.

```bash
# Works on a headless compute node
quantipy debug --results ./results --output /scratch/viewer.html
```

---

## Limitations

- **Read-only.** The viewer displays results; it does not rerun or modify any
  pipeline stage.
- **Large datasets.** The viewer embeds all cell data as inline JSON.  Runs
  with more than ~50 000 cells may make the page slow to load or scroll.  Use
  the `--fov` flag to limit to a single FOV if performance is an issue.
- **Static images.** The FOV panel shows the pre-rendered PNG from
  `03_polarity/maps/`.  Re-segmenting or changing polarity parameters requires
  re-running the relevant pipeline stages and regenerating the viewer.
