# QuantiPy Polarity — Phase 7: Interactive Viewer + Experimental Analyses + Final Polish

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the "polish" phase — a portable static-HTML per-cell viewer (`quantipy debug`), two curated experimental analyses (`quantipy analyze`), final documentation, `CITATION.cff`, `CHANGELOG.md`, and a clean `v0.1.0` release tag. No changes to the core pipeline. 243 tests baseline; target ≥ 278 tests.

**Architecture overview:** The `interactive/` subpackage (currently a one-line stub) gains `build_viewer.py` and a Jinja2 template `viewer.html.j2`. `build_viewer.py` reads `per_cell.parquet` + per-FOV polarity map PNGs from the results directory, encodes everything as inline base64/JSON, and renders a single self-contained HTML file with vanilla JavaScript for click-to-inspect interactivity — no CDN, no server, no Python widgets, no X11. The `experimental/analyses/` subpackage (currently a one-line stub) gains two real analysis modules: `polarity_by_condition.py` (Mann-Whitney boxplot) and `magnitude_vs_distance.py` (robust regression scatter). A new `_cli_debug.py` replaces the `debug` stub; a new `_cli_analyze.py` replaces the `analyze` stub using Click's `@group`/`@command` subcommand pattern. Both stubs are removed from `_stubs.py`. Version is already `0.1.0` in `_version.py`; `pyproject.toml` matches — no bump needed. `CITATION.cff`, `CHANGELOG.md`, and doc pages complete the release checklist.

**Spec sources:** `docs/superpowers/specs/2026-05-26-quantipy-polarity-design.md` §4 (debug, analyze CLI), §5 (CLI surface), §8 (interactive viewer), §9 (curated analyses in experimental/), §17 (open items), §18 (acceptance criteria).

**Baseline:** 243 tests passing, tag `phase-6-complete`. Full pipeline works end-to-end.

**Interactive viewer decision — Option B (static self-contained HTML):**

Option B is chosen because:
1. It requires no additional runtime dependencies (Jinja2 is already in the `pipeline` extras from Phase 5/6).
2. It works perfectly on headless servers, over SSH, and in any OS — no X11, no TkAgg, no `DISPLAY` env var.
3. A single `.html` file is portable: users can share it alongside `per_cell.parquet`.
4. Vanilla JS (< 200 lines) handles click-to-inspect, FOV switching, cell nav — no framework, no CDN, no React.

The HTML file embeds: (a) all per-FOV polarity map PNGs as base64 `<img>` tags, (b) the full `per_cell.parquet` rows as a compact JSON array, (c) a vanilla JS controller that wires up cell-row selection to an info panel. Clicking a cell in the FOV image overlay shows the corresponding parquet row in a right-side info panel. FOV switching updates which PNG is visible and which rows are shown in the selection list.

**Version status:** `_version.py` already reads `__version__ = "0.1.0"` and `pyproject.toml` matches. No version bump needed.

**Acceptance criteria:**
1. `quantipy debug --results ./demo_results --output /tmp/viewer.html` completes without error and writes a self-contained HTML file (no external URLs, no CDN).
2. Opening `viewer.html` in a browser (or `python -m http.server`) shows per-FOV polarity maps and a cell list; clicking a row populates the info panel with parquet data.
3. `quantipy analyze polarity-by-condition --per-cell ./results/05_aggregated/per_cell.parquet --metadata <path>` emits a PDF boxplot and `polarity_by_condition_results.json`.
4. `quantipy analyze magnitude-vs-distance --per-cell ./results/05_aggregated/per_cell.parquet` emits a PDF scatter and `magnitude_vs_distance_results.json`.
5. Both `analyze` subcommands have `--help` and validate inputs; bad paths produce a clean Click error, not a Python traceback.
6. `CITATION.cff` passes `cff-validator` (`pip install cff-validator && cff-validator CITATION.cff` exits 0).
7. `quantipy --version` prints `0.1.0`.
8. Full pytest suite: 243 (Phase 6) + ≥ 35 new tests = **≥ 278 passed**. All new tests are fast-tier (no disk I/O beyond tmp fixtures).
9. Tag `phase-7-complete` + git tag `v0.1.0` pushed.

---

## File Structure (locked at planning time)

```
QuantiPy-Polarity/
├── CITATION.cff                                      # Create Task 1
├── CHANGELOG.md                                      # Create Task 2
├── src/quantipy_polarity/
│   ├── _stubs.py                                     # Modify Task 3: remove debug + analyze stubs
│   ├── cli.py                                        # Modify Task 3: import _cli_debug + _cli_analyze
│   ├── interactive/
│   │   ├── __init__.py                               # Modify Task 4: expose build_viewer public API
│   │   └── build_viewer.py                           # Create Task 4: build_viewer() function
│   ├── interactive/templates/
│   │   └── viewer.html.j2                            # Create Task 5: Jinja2 viewer template
│   ├── _cli_debug.py                                 # Create Task 6: quantipy debug command
│   ├── experimental/
│   │   ├── __init__.py                               # Modify Task 7: add experimental banner
│   │   └── analyses/
│   │       ├── __init__.py                           # Modify Task 7: analyses registry
│   │       ├── polarity_by_condition.py              # Create Task 7: Mann-Whitney boxplot
│   │       └── magnitude_vs_distance.py              # Create Task 8: robust regression scatter
│   └── _cli_analyze.py                               # Create Task 9: quantipy analyze subgroup
├── tests/
│   ├── interactive/
│   │   ├── __init__.py                               # Create Task 10
│   │   └── test_build_viewer.py                      # Create Task 10
│   ├── experimental/
│   │   ├── __init__.py                               # Create Task 11
│   │   ├── test_polarity_by_condition.py             # Create Task 11
│   │   └── test_magnitude_vs_distance.py             # Create Task 11
│   └── cli/
│       ├── test_cli_debug.py                         # Create Task 12
│       └── test_cli_analyze.py                       # Create Task 12
└── docs/
    ├── cli-reference.md                              # Create Task 13
    ├── api-reference.md                              # Create Task 13
    └── interactive-viewer.md                         # Create/finalise Task 13
README.md                                             # Modify Task 14: TOC + Phase 7 status
```

---

## Task 1: Create `CITATION.cff`

**Files:** Create `CITATION.cff` in repo root.

`CITATION.cff` must be valid per [citation-file-format.github.io](https://citation-file-format.github.io/) — GitHub uses it to populate "Cite this repository". It references both the QuantiPy-Polarity Python implementation **and** the original QuantifyPolarity Mathematica tool as a related work.

- [ ] **Step 1: Write `CITATION.cff`.**

  ```yaml
  cff-version: 1.2.0
  message: "If you use QuantiPy Polarity in your research, please cite it as below."
  type: software
  title: "QuantiPy Polarity"
  abstract: >
    A Python implementation of the QuantifyPolarity (QP) planar polarity
    quantification pipeline. Computes per-cell polarity axes from
    membrane-channel microscopy images using boundary PCA, detects migration
    fronts, and generates polarity maps, rose plots, and a self-contained HTML
    report.
  authors:
    - family-names: McLean
      given-names: Taggart
      orcid: ""
      email: taggartmc@pennmedicine.upenn.edu
  repository-code: "https://github.com/mcleanT/QuantiPy-Polarity"
  license: MIT
  version: "0.1.0"
  date-released: "2026-05-26"
  keywords:
    - planar-polarity
    - cell-biology
    - microscopy
    - image-analysis
    - python
  references:
    - type: software
      title: "QuantifyPolarity"
      abstract: >
        Original Mathematica implementation of the boundary-PCA polarity
        quantification algorithm that QuantiPy Polarity reimplements in Python.
      authors:
        - name: "Hughes Lab"
      notes: "QuantifyPolarity.2022.2.1.Mac — the original tool that this package re-implements."
  ```

  Critical validity rules (per CFF spec 1.2.0):
  - `cff-version`, `message`, `title`, `authors` are **required** top-level keys.
  - `orcid` must be a full URI (`https://orcid.org/...`) or omitted entirely — an empty string is invalid. **Omit `orcid` key** if it is not known.
  - `date-released` must be `YYYY-MM-DD`.
  - `references[].authors` must be a list of objects (either `{name: "..."}` for organisational authors, or `{family-names: ..., given-names: ...}` for persons).
  - `license` must be an SPDX identifier (`MIT`, not `"MIT License"`).

- [ ] **Step 2: Validate the file.**

  ```bash
  pip install cff-validator --quiet && cff-validator CITATION.cff
  ```

  If `cff-validator` is not available (network-blocked CI), fall back to:
  ```bash
  python -c "import yaml, pathlib; d = yaml.safe_load(pathlib.Path('CITATION.cff').read_text()); assert d['cff-version'] == '1.2.0'; assert 'authors' in d; assert 'title' in d; print('CITATION.cff structure OK')"
  ```

---

## Task 2: Create `CHANGELOG.md`

**Files:** Create `CHANGELOG.md` in repo root.

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format with SemVer tagging. Each phase maps to a logical feature block under `[0.1.0]`.

- [ ] **Step 1: Write `CHANGELOG.md`.**

  ```markdown
  # Changelog

  All notable changes to QuantiPy Polarity are documented in this file.

  Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
  Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

  ---

  ## [0.1.0] — 2026-05-26

  First public release of QuantiPy Polarity.

  ### Added (Phase 1 — CLI scaffold + Pydantic config)
  - `quantipy` CLI entry point with grouped help (Primary / Advanced commands)
  - Pydantic v2 config schema with YAML loader and mode discrimination (`nd2`, `tif`, `masks`)
  - `quantipy init-config --mode {nd2,tif,masks}` scaffolds a working YAML
  - Data contracts (`contracts.py`) shared across pipeline stages
  - Phase stubs for all unimplemented commands

  ### Added (Phase 2 — Masks → polarity)
  - `polarity/boundary_pca.py` — boundary-PCA polarity computation from label masks
  - `polarity/per_cell.py` — per-cell parquet assembly
  - `quantipy polarity` stage command

  ### Added (Phase 3 — TIF/ND2 ingest + Cellpose-SAM segmentation)
  - `io/tif.py`, `io/nd2.py`, `io/masks.py` — multi-format image loaders
  - `segment/cellpose.py`, `segment/postprocess.py` — Cellpose-SAM wrapper + post-processing
  - `quantipy ingest` and `quantipy segment` stage commands

  ### Added (Phase 4 — Migration front detection + visualization)
  - `migration/front.py` — automated v3 outward-side front detection
  - `migration/local.py` — per-cell local migration direction
  - `viz/style.py`, `viz/polarity_map.py`, `viz/rose.py`, `viz/overlay.py` — Nature-style figures
  - `quantipy front` and `quantipy plot` stage commands

  ### Added (Phase 5 — `quantipy run` orchestration)
  - `pipeline/` — DAG runner with `_stage_status.json` resume/atomic-write semantics
  - `report/` — Jinja2 HTML report with base64-inlined figures
  - `quantipy run` (with `--resume` and `--force`)
  - `quantipy report` stage command

  ### Added (Phase 6 — Validation + Demo + Release)
  - `validation/synthetic_data.py` — deterministic synthetic parquet generator (seed=42)
  - `validation/qp_vs_python.py` — QP-vs-Python scatter figure + R²/slope reporting
  - `quantipy validate` — regenerates validation figure, prints R²
  - `quantipy download-demo` — downloads demo bundle from GitHub Releases
  - `demo/` directory with synthetic TIFs, masks, and `config.yaml`
  - `data/validation/` — committed synthetic reference parquets
  - `docs/validation.md` — methodology, synthetic-data rationale, thresholds
  - GitHub Release `v0.1.0-demo` with demo bundle zip attached

  ### Added (Phase 7 — Interactive viewer + Experimental analyses + Polish)
  - `interactive/build_viewer.py` — generates a self-contained static HTML viewer
  - `interactive/templates/viewer.html.j2` — Jinja2 viewer template (vanilla JS, no CDN)
  - `quantipy debug` — writes `viewer.html` from a results directory (no display backend needed)
  - `experimental/analyses/polarity_by_condition.py` — Mann-Whitney boxplot, grouped by condition
  - `experimental/analyses/magnitude_vs_distance.py` — robust regression scatter vs front distance
  - `quantipy analyze polarity-by-condition` and `quantipy analyze magnitude-vs-distance`
  - `CITATION.cff` — GitHub "Cite this repository" support
  - `docs/cli-reference.md` — full CLI reference with flags and examples
  - `docs/api-reference.md` — public Python API (Config, run_pipeline)
  - `docs/interactive-viewer.md` — viewer feature guide and workflows
  - README table of contents and updated phase status table

  ---

  ## [Unreleased]

  *(No changes pending.)*
  ```

---

## Task 3: Remove stubs + wire real CLI modules

**Files:** Modify `src/quantipy_polarity/_stubs.py`, Modify `src/quantipy_polarity/cli.py`

`_stubs.py` currently registers `debug` and `analyze` as stub commands. Task 3 removes them from the stub dict; Tasks 6 and 9 supply real implementations. `cli.py` is extended to import the two new CLI modules.

- [ ] **Step 1: Remove `debug` and `analyze` from `_STUBS` in `_stubs.py`.**

  The `_STUBS` dict currently has two entries (`"debug"` and `"analyze"`). Remove **both** entries. The resulting dict will be empty. Keep the `_make_stub` helper and the `for` loop (they are harmless with an empty dict and may be reused for future stubs).

  ```python
  _STUBS: dict[str, tuple[str, str]] = {
      # All Phase 7 stubs have been replaced by real implementations.
  }
  ```

- [ ] **Step 2: Add two import lines to `cli.py`.**

  After the existing `_cli_download_demo` import, add:

  ```python
  from quantipy_polarity import _cli_debug as _cli_debug  # noqa: E402,F401
  from quantipy_polarity import _cli_analyze as _cli_analyze  # noqa: E402,F401
  ```

  These imports trigger Click command registration at module load time (the same pattern used by all other CLI modules).

- [ ] **Step 3: Verify `quantipy --help` shows `debug` and `analyze` under the correct sections.**

  `debug` must appear under **Primary commands** (it is already in `_GroupedHelp.PRIMARY`).
  `analyze` must appear under **Advanced commands** (it is not in `PRIMARY`).

  Run:
  ```bash
  python -m quantipy_polarity.cli --help 2>&1 | grep -E "debug|analyze"
  ```

---

## Task 4: Create `interactive/build_viewer.py`

**Files:** Create `src/quantipy_polarity/interactive/build_viewer.py`, Modify `src/quantipy_polarity/interactive/__init__.py`

`build_viewer.py` is the pure-Python assembly layer for the static HTML viewer. It reads the results directory, collects per-cell data and per-FOV PNGs, and renders a Jinja2 template to a single `.html` file. It has no dependency on matplotlib or any display backend.

- [ ] **Step 1: Define `build_viewer()` function signature.**

  ```python
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
  ```

- [ ] **Step 2: Implement `build_viewer()` — data collection phase.**

  ```python
  from __future__ import annotations

  import base64
  import json
  from pathlib import Path

  import pandas as pd
  from jinja2 import Environment, FileSystemLoader, select_autoescape

  _TEMPLATE_DIR = Path(__file__).parent / "templates"
  _REQUIRED_COLUMNS = {"fov_id", "cell_id", "qp_magnitude", "qp_axis_deg"}


  def build_viewer(
      results_dir: Path,
      output_path: Path,
      *,
      fov: str | None = None,
  ) -> None:
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
          c for c in df.columns
          if df[c].dtype.kind in ("f", "i", "u", "b", "O", "U")
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
      import os, tempfile  # noqa: PLC0415, E401
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
  ```

  Add a small helper at module level:
  ```python
  def _get_version() -> str:
      try:
          from importlib.metadata import version
          return version("quantipy-polarity")
      except Exception:
          return "unknown"
  ```

- [ ] **Step 3: Update `interactive/__init__.py` to expose `build_viewer`.**

  Replace the current one-line stub with:
  ```python
  """Read-only per-cell viewer (Phase 7).

  Public API:
      build_viewer(results_dir, output_path, *, fov=None) -> None
          Build a self-contained static HTML viewer from a quantipy results dir.
  """

  from quantipy_polarity.interactive.build_viewer import build_viewer

  __all__ = ["build_viewer"]
  ```

---

## Task 5: Create `interactive/templates/viewer.html.j2`

**Files:** Create `src/quantipy_polarity/interactive/templates/viewer.html.j2`

This is the Jinja2 template that produces the self-contained single-file HTML viewer. All CSS and JS are inline. No CDN, no external URLs, no `<script src="...">` tags pointing anywhere external.

- [ ] **Step 1: Create the `templates/` directory and `viewer.html.j2`.**

  The template receives these variables from `build_viewer.py`:
  - `fovs` — list of FOV ID strings
  - `fov_images` — dict of `{fov_id: base64_png_string}` (empty string = no image)
  - `cells_json` — compact JSON array string of per-cell row objects
  - `display_cols` — list of column names (drives the info panel table header)
  - `version` — package version string

  Layout:
  ```
  +--------------------------------------------------------------+
  | QuantiPy Polarity — Per-cell Viewer  [FOV dropdown] [← →]   |
  +----------------------------+---------------------------------+
  | Polarity map PNG           | Cell list (scrollable)          |
  | (scales to panel width)    | Each row: cell_id, magnitude,   |
  |                            | axis_deg                        |
  +----------------------------+---------------------------------+
  | Info panel: selected cell parquet columns as <dl> or table   |
  +--------------------------------------------------------------+
  ```

  The template structure (write this entire file exactly — no placeholders):

  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QuantiPy Polarity — Per-cell Viewer</title>
  <style>
  /* ── Reset + base ── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 13px; background: #f5f5f5; color: #222; }
  /* ── Header toolbar ── */
  #toolbar { display: flex; align-items: center; gap: 12px; padding: 8px 16px;
             background: #272727; color: #fff; }
  #toolbar h1 { font-size: 14px; font-weight: bold; }
  #toolbar select, #toolbar button { font-size: 12px; padding: 3px 8px; border-radius: 3px;
                                      border: 1px solid #888; background: #fff; cursor: pointer; }
  #toolbar button:hover { background: #e0e0e0; }
  #version-badge { margin-left: auto; font-size: 11px; color: #aaa; }
  /* ── Main layout ── */
  #main { display: flex; height: calc(100vh - 80px); }
  /* ── FOV image panel ── */
  #fov-panel { flex: 1 1 55%; padding: 12px; overflow: hidden; display: flex;
               flex-direction: column; background: #fff; border-right: 1px solid #ddd; }
  #fov-panel h2 { font-size: 12px; color: #555; margin-bottom: 6px; }
  #fov-img-container { flex: 1; overflow: hidden; }
  #fov-img { max-width: 100%; max-height: 100%; object-fit: contain; display: block; }
  #fov-placeholder { color: #aaa; font-style: italic; padding: 16px; }
  /* ── Cell list panel ── */
  #cell-panel { flex: 0 0 220px; display: flex; flex-direction: column;
                background: #fafafa; border-right: 1px solid #ddd; }
  #cell-panel h2 { font-size: 12px; color: #555; padding: 8px 10px; border-bottom: 1px solid #ddd; }
  #cell-list { flex: 1; overflow-y: auto; }
  .cell-row { padding: 5px 10px; cursor: pointer; border-bottom: 1px solid #eee;
              font-size: 12px; white-space: nowrap; }
  .cell-row:hover { background: #e8f0fe; }
  .cell-row.selected { background: #c2d4f8; font-weight: bold; }
  /* ── Info panel ── */
  #info-panel { flex: 1 1 30%; padding: 12px; overflow-y: auto; background: #fff; }
  #info-panel h2 { font-size: 12px; color: #555; margin-bottom: 8px; }
  #info-table { width: 100%; border-collapse: collapse; font-size: 12px; }
  #info-table td { padding: 3px 6px; border-bottom: 1px solid #eee; vertical-align: top; }
  #info-table td:first-child { color: #555; width: 40%; word-break: break-word; }
  #info-table td:last-child  { font-family: monospace; }
  #no-selection-msg { color: #aaa; font-style: italic; }
  /* ── Status bar ── */
  #statusbar { height: 26px; line-height: 26px; padding: 0 16px; background: #272727;
               color: #ccc; font-size: 11px; }
  </style>
  </head>
  <body>

  <!-- ── Toolbar ── -->
  <div id="toolbar">
    <h1>QuantiPy Polarity — Per-cell Viewer</h1>
    <select id="fov-select" onchange="switchFov(this.value)">
      {% for fov_id in fovs %}
      <option value="{{ fov_id }}">{{ fov_id }}</option>
      {% endfor %}
    </select>
    <button onclick="navFov(-1)">&#8592; Prev FOV</button>
    <button onclick="navFov(+1)">Next FOV &#8594;</button>
    <span id="version-badge">v{{ version }}</span>
  </div>

  <!-- ── Main panels ── -->
  <div id="main">
    <!-- FOV image -->
    <div id="fov-panel">
      <h2 id="fov-label">FOV: {{ fovs[0] if fovs else '' }}</h2>
      <div id="fov-img-container">
        {% if fovs %}
        <img id="fov-img" src="" alt="Polarity map" />
        <p id="fov-placeholder" style="display:none">No polarity map available for this FOV.</p>
        {% else %}
        <p id="fov-placeholder">No FOVs found in this results directory.</p>
        {% endif %}
      </div>
    </div>

    <!-- Cell list -->
    <div id="cell-panel">
      <h2>Cells (<span id="cell-count">0</span>)</h2>
      <div id="cell-list"></div>
    </div>

    <!-- Info panel -->
    <div id="info-panel">
      <h2>Selected cell</h2>
      <p id="no-selection-msg">Click a cell to inspect its parquet row.</p>
      <table id="info-table" style="display:none">
        <tbody id="info-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ── Status bar ── -->
  <div id="statusbar" id="statusbar">Ready. {{ fovs|length }} FOV(s) loaded.</div>

  <script>
  // ── Embedded data ──
  const ALL_CELLS = {{ cells_json }};
  const FOV_IMAGES = {{ fov_images | tojson }};
  const FOVS = {{ fovs | tojson }};

  // ── State ──
  let currentFov = FOVS.length > 0 ? FOVS[0] : null;
  let selectedIdx = null;   // index into currentCells array
  let currentCells = [];

  // ── Init ──
  document.addEventListener("DOMContentLoaded", function() {
    if (currentFov) switchFov(currentFov);
    document.addEventListener("keydown", handleKey);
  });

  function switchFov(fovId) {
    currentFov = fovId;
    selectedIdx = null;

    // Update dropdown
    const sel = document.getElementById("fov-select");
    sel.value = fovId;

    // Update label
    document.getElementById("fov-label").textContent = "FOV: " + fovId;

    // Update image
    const imgEl = document.getElementById("fov-img");
    const placeholder = document.getElementById("fov-placeholder");
    const b64 = FOV_IMAGES[fovId] || "";
    if (b64) {
      imgEl.src = "data:image/png;base64," + b64;
      imgEl.style.display = "block";
      if (placeholder) placeholder.style.display = "none";
    } else {
      if (imgEl) imgEl.style.display = "none";
      if (placeholder) placeholder.style.display = "block";
    }

    // Filter cells for this FOV
    currentCells = ALL_CELLS.filter(function(c) { return c.fov_id === fovId; });
    renderCellList();
    clearInfo();
    setStatus("FOV: " + fovId + "  |  " + currentCells.length + " cell(s)");
  }

  function renderCellList() {
    const container = document.getElementById("cell-list");
    container.innerHTML = "";
    document.getElementById("cell-count").textContent = currentCells.length;
    currentCells.forEach(function(cell, i) {
      const div = document.createElement("div");
      div.className = "cell-row";
      div.dataset.idx = i;
      const mag = cell.qp_magnitude !== undefined ? cell.qp_magnitude.toFixed(3) : "?";
      const ax  = cell.qp_axis_deg  !== undefined ? cell.qp_axis_deg.toFixed(1)  : "?";
      div.textContent = "cell " + (cell.cell_id !== undefined ? cell.cell_id : i)
                       + "  mag=" + mag + "  ax=" + ax + "°";
      div.addEventListener("click", function() { selectCell(i); });
      container.appendChild(div);
    });
  }

  function selectCell(idx) {
    // Deselect previous
    if (selectedIdx !== null) {
      const prev = document.querySelector(".cell-row.selected");
      if (prev) prev.classList.remove("selected");
    }
    selectedIdx = idx;
    const rows = document.querySelectorAll(".cell-row");
    if (rows[idx]) rows[idx].classList.add("selected");
    showInfo(currentCells[idx]);
    setStatus("Selected: cell_id=" + (currentCells[idx].cell_id ?? idx));
  }

  function showInfo(cell) {
    document.getElementById("no-selection-msg").style.display = "none";
    const table = document.getElementById("info-table");
    table.style.display = "table";
    const tbody = document.getElementById("info-tbody");
    tbody.innerHTML = "";
    Object.entries(cell).forEach(function([k, v]) {
      const tr = document.createElement("tr");
      const td1 = document.createElement("td"); td1.textContent = k;
      const td2 = document.createElement("td");
      td2.textContent = (v === null || v === undefined) ? "—" :
                         (typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(4)) : String(v));
      tr.appendChild(td1); tr.appendChild(td2);
      tbody.appendChild(tr);
    });
  }

  function clearInfo() {
    document.getElementById("no-selection-msg").style.display = "block";
    document.getElementById("info-table").style.display = "none";
    document.getElementById("info-tbody").innerHTML = "";
  }

  function navFov(delta) {
    const idx = FOVS.indexOf(currentFov);
    const next = FOVS[(idx + delta + FOVS.length) % FOVS.length];
    switchFov(next);
  }

  function handleKey(e) {
    if (e.key === "ArrowLeft")  { navFov(-1); return; }
    if (e.key === "ArrowRight") { navFov(+1); return; }
    if (e.key === "ArrowDown" && currentCells.length > 0) {
      const next = selectedIdx === null ? 0 : Math.min(selectedIdx + 1, currentCells.length - 1);
      selectCell(next); return;
    }
    if (e.key === "ArrowUp" && selectedIdx !== null) {
      selectCell(Math.max(selectedIdx - 1, 0)); return;
    }
  }

  function setStatus(msg) {
    document.getElementById("statusbar").textContent = msg;
  }
  </script>
  </body>
  </html>
  ```

  **Notes on the template:**
  - `{{ fov_images | tojson }}` uses Jinja2's built-in `tojson` filter — this is safe for large base64 strings and handles escaping correctly.
  - `{{ cells_json }}` is injected verbatim (already valid JSON serialised in `build_viewer.py`); it is placed inside a JS `const` assignment so it is parsed by the browser's JSON engine, not Jinja2.
  - The `autoescape=select_autoescape(["html"])` in `build_viewer.py` applies HTML escaping to `{{ version }}` and `{{ fovs }}` but NOT to `{{ cells_json }}` because it is rendered inside a `<script>` block. To prevent double-escaping, `cells_json` must be passed through Jinja2's `|safe` filter in the template: `const ALL_CELLS = {{ cells_json | safe }};`. Add `| safe` to all three embedded-data lines in the `<script>` block.

---

## Task 6: Create `_cli_debug.py`

**Files:** Create `src/quantipy_polarity/_cli_debug.py`

This is the real `quantipy debug` command. It writes a self-contained HTML viewer from a results directory. It never opens a browser window or spawns a display backend — it writes HTML and prints the output path.

- [ ] **Step 1: Write `_cli_debug.py`.**

  ```python
  """quantipy debug — write a self-contained per-cell HTML viewer.

  Usage:
      quantipy debug --results ./demo_results
      quantipy debug --results ./demo_results --output /tmp/viewer.html --fov fov_A
  """

  from __future__ import annotations

  from pathlib import Path

  import click

  from quantipy_polarity.cli import main
  from quantipy_polarity.interactive import build_viewer


  @main.command("debug")
  @click.option(
      "--results",
      required=True,
      type=click.Path(exists=True, file_okay=False, path_type=Path),
      help="Path to a completed quantipy run directory.",
  )
  @click.option(
      "--output",
      default=None,
      type=click.Path(path_type=Path),
      help="Output HTML path. Default: <results>/viewer.html",
  )
  @click.option(
      "--fov",
      default=None,
      type=str,
      help="Limit viewer to a single FOV ID (default: all FOVs).",
  )
  def debug_cmd(results: Path, output: Path | None, fov: str | None) -> None:
      """Write a self-contained HTML per-cell viewer for a completed run."""
      if output is None:
          output = results / "viewer.html"

      try:
          build_viewer(results, output, fov=fov)
      except FileNotFoundError as exc:
          raise click.ClickException(str(exc)) from exc
      except ValueError as exc:
          raise click.ClickException(str(exc)) from exc

      click.echo(f"Viewer written → {output}")
      click.echo("Open in any browser: no server required.")
  ```

  Key rules:
  - Command name is registered as `"debug"` (overrides the stub that `_stubs.py` previously registered — Task 3 removes the stub first, so there is no conflict).
  - `FileNotFoundError` and `ValueError` from `build_viewer` are caught and re-raised as `click.ClickException` so the user sees a clean error message rather than a Python traceback.
  - No `plt.show()`, no `webbrowser.open()`, no `subprocess.call(["open", ...])` — the command writes HTML and stops.

---

## Task 7: Create `experimental/analyses/polarity_by_condition.py`

**Files:** Create `src/quantipy_polarity/experimental/analyses/polarity_by_condition.py`, Modify `src/quantipy_polarity/experimental/__init__.py`, Modify `src/quantipy_polarity/experimental/analyses/__init__.py`

`polarity_by_condition.py` is a curated experimental analysis: given a per-cell parquet + a metadata CSV/TSV mapping `fov_id → condition`, it produces a Nature-style boxplot of polarity magnitude grouped by condition, with per-group N and a Mann-Whitney U p-value for the two-group case (skipped silently if > 2 groups — a note is added to the JSON output instead).

- [ ] **Step 1: Define the public function signature.**

  ```python
  def run_polarity_by_condition(
      per_cell_path: Path,
      metadata_path: Path,
      output_dir: Path,
      *,
      condition_col: str = "condition",
      magnitude_col: str = "qp_magnitude",
  ) -> dict:
      """Boxplot of polarity magnitude grouped by experimental condition.

      Args:
          per_cell_path: Path to per_cell.parquet (must contain ``fov_id`` + magnitude_col).
          metadata_path: Path to CSV/TSV with columns [fov_id, condition_col].
          output_dir: Directory to write ``polarity_by_condition.pdf`` and
              ``polarity_by_condition_results.json``.
          condition_col: Column name in metadata for the grouping variable.
          magnitude_col: Column name in per_cell for polarity magnitude.

      Returns:
          dict with keys: groups, n_per_group, medians, p_value (or None), test_used.

      Raises:
          FileNotFoundError: If input files do not exist.
          ValueError: If required columns are missing or fewer than 2 groups found.
      """
  ```

- [ ] **Step 2: Implement the function body.**

  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd
  from scipy import stats

  from quantipy_polarity.viz.style import apply_nature_style


  def run_polarity_by_condition(
      per_cell_path: Path,
      metadata_path: Path,
      output_dir: Path,
      *,
      condition_col: str = "condition",
      magnitude_col: str = "qp_magnitude",
  ) -> dict:
      per_cell_path, metadata_path, output_dir = (
          Path(per_cell_path), Path(metadata_path), Path(output_dir)
      )
      for p in (per_cell_path, metadata_path):
          if not p.exists():
              raise FileNotFoundError(f"File not found: {p}")

      df = pd.read_parquet(per_cell_path)
      sep = "\t" if str(metadata_path).endswith(".tsv") else ","
      meta = pd.read_csv(metadata_path, sep=sep)

      for col, src in [(magnitude_col, "per_cell"), ("fov_id", "per_cell"),
                       (condition_col, "metadata"), ("fov_id", "metadata")]:
          src_df = df if src == "per_cell" else meta
          if col not in src_df.columns:
              raise ValueError(f"Column {col!r} not found in {src} file")

      merged = df.merge(meta[["fov_id", condition_col]], on="fov_id", how="inner")
      groups = sorted(merged[condition_col].dropna().unique().tolist())
      if len(groups) < 2:
          raise ValueError(f"Fewer than 2 groups found in column {condition_col!r}: {groups}")

      group_data = [merged.loc[merged[condition_col] == g, magnitude_col].dropna().values
                    for g in groups]
      n_per_group = [int(len(d)) for d in group_data]
      medians = [float(np.median(d)) for d in group_data]

      p_value = None
      test_used = None
      note = None
      if len(groups) == 2:
          stat, p_value = stats.mannwhitneyu(group_data[0], group_data[1], alternative="two-sided")
          p_value = float(p_value)
          test_used = "Mann-Whitney U"
      else:
          note = f"Statistical test skipped: {len(groups)} groups (only performed for 2 groups)."

      # Figure
      apply_nature_style()
      fig, ax = plt.subplots(figsize=(1.6 * len(groups) + 0.8, 3.0))
      bp = ax.boxplot(group_data, patch_artist=True, widths=0.5, medianprops={"color": "#272727", "linewidth": 1.5})
      palette = ["#5B8FD6", "#E28E2C", "#7BAA5B", "#C45AD6", "#D24B40"]
      for patch, color in zip(bp["boxes"], palette):
          patch.set_facecolor(color)
          patch.set_alpha(0.7)
      ax.set_xticks(range(1, len(groups) + 1))
      ax.set_xticklabels([f"{g}\n(N={n})" for g, n in zip(groups, n_per_group)], fontsize=6)
      ax.set_ylabel("Polarity magnitude", fontsize=7)
      ax.set_xlabel(condition_col, fontsize=7)
      if p_value is not None:
          sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
          ax.set_title(f"Mann-Whitney U  p={p_value:.3g}  {sig}", fontsize=7)

      output_dir.mkdir(parents=True, exist_ok=True)
      fig_path = output_dir / "polarity_by_condition.pdf"
      fig.savefig(fig_path, bbox_inches="tight", dpi=600)
      plt.close(fig)

      results = {
          "groups": groups,
          "n_per_group": n_per_group,
          "medians": medians,
          "p_value": p_value,
          "test_used": test_used,
          "note": note,
      }
      json_path = output_dir / "polarity_by_condition_results.json"
      json_path.write_text(json.dumps(results, indent=2))
      return results
  ```

- [ ] **Step 3: Update `experimental/__init__.py`.**

  ```python
  """Experimental analyses — not part of the stable quantipy_polarity API.

  APIs in this namespace may change between minor versions. Do not build
  production workflows on them without pinning a version. Use at your own risk.

  Stable promotion happens when:
  - The analysis has been validated against ≥ 2 independent datasets.
  - The interface has not changed for ≥ 2 minor versions.
  - A corresponding docs page has been written.
  """
  ```

- [ ] **Step 4: Update `experimental/analyses/__init__.py`.**

  ```python
  """Registry of curated experimental analyses.

  Each analysis is a module in this package exposing a ``run_<name>()``
  function. The ``quantipy analyze <name>`` CLI dispatches to the registry.

  Available analyses:
      polarity-by-condition   Boxplot of polarity magnitude by condition + Mann-Whitney U
      magnitude-vs-distance   Scatter of polarity magnitude vs front distance + robust regression
  """

  REGISTRY: dict[str, str] = {
      "polarity-by-condition": "polarity_by_condition",
      "magnitude-vs-distance": "magnitude_vs_distance",
  }
  ```

---

## Task 8: Create `experimental/analyses/magnitude_vs_distance.py`

**Files:** Create `src/quantipy_polarity/experimental/analyses/magnitude_vs_distance.py`

`magnitude_vs_distance.py` produces a scatter of polarity magnitude vs distance-to-front, with a Theil-Sen robust regression line and 95% bootstrap CI band. Theil-Sen is chosen over OLS because it is robust to outliers and requires no normality assumption.

- [ ] **Step 1: Define the function signature.**

  ```python
  def run_magnitude_vs_distance(
      per_cell_path: Path,
      output_dir: Path,
      *,
      magnitude_col: str = "qp_magnitude",
      distance_col: str = "dist_to_front_px",
      max_cells: int = 5000,
  ) -> dict:
      """Scatter of polarity magnitude vs distance-to-front with robust regression.

      Args:
          per_cell_path: Path to per_cell.parquet. Must contain magnitude_col and
              distance_col. If distance_col is absent, emits a JSON noting the
              column is missing and writes no figure (exits cleanly — front detection
              may not have been run).
          output_dir: Directory to write ``magnitude_vs_distance.pdf`` and
              ``magnitude_vs_distance_results.json``.
          magnitude_col: Column name for polarity magnitude.
          distance_col: Column name for distance to migration front (pixels).
          max_cells: Subsample to this many cells for scatter legibility (random seed=42).

      Returns:
          dict with keys: n_cells, slope, intercept, r_squared, distance_col_found.

      Raises:
          FileNotFoundError: If per_cell_path does not exist.
          ValueError: If magnitude_col is absent.
      """
  ```

- [ ] **Step 2: Implement the function body.**

  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np
  import pandas as pd
  from scipy import stats

  from quantipy_polarity.viz.style import apply_nature_style


  def run_magnitude_vs_distance(
      per_cell_path: Path,
      output_dir: Path,
      *,
      magnitude_col: str = "qp_magnitude",
      distance_col: str = "dist_to_front_px",
      max_cells: int = 5000,
  ) -> dict:
      per_cell_path, output_dir = Path(per_cell_path), Path(output_dir)
      if not per_cell_path.exists():
          raise FileNotFoundError(f"File not found: {per_cell_path}")

      df = pd.read_parquet(per_cell_path)
      if magnitude_col not in df.columns:
          raise ValueError(f"Column {magnitude_col!r} not found in parquet")

      output_dir.mkdir(parents=True, exist_ok=True)

      # Handle missing distance column gracefully
      if distance_col not in df.columns:
          results = {
              "n_cells": len(df),
              "slope": None, "intercept": None, "r_squared": None,
              "distance_col_found": False,
              "note": (
                  f"Column {distance_col!r} not found. "
                  "Run `quantipy front` to compute migration distances, then re-run this analysis."
              ),
          }
          (output_dir / "magnitude_vs_distance_results.json").write_text(
              json.dumps(results, indent=2)
          )
          return results

      df_clean = df[[magnitude_col, distance_col]].dropna()
      if len(df_clean) > max_cells:
          df_clean = df_clean.sample(max_cells, random_state=42)

      x = df_clean[distance_col].values.astype(float)
      y = df_clean[magnitude_col].values.astype(float)

      # Theil-Sen robust regression
      slope, intercept, low_slope, high_slope = stats.theilslopes(y, x)
      slope, intercept = float(slope), float(intercept)

      # R² (Pearson, for reporting alongside the robust line)
      r, _ = stats.pearsonr(x, y)
      r_squared = float(r ** 2)

      # Figure
      apply_nature_style()
      fig, ax = plt.subplots(figsize=(3.5, 3.0))
      ax.scatter(x, y, s=4, alpha=0.3, color="#5B8FD6", linewidths=0, rasterized=True)
      x_line = np.linspace(x.min(), x.max(), 200)
      ax.plot(x_line, slope * x_line + intercept, color="#D24B40", linewidth=1.5,
              label=f"Theil-Sen  slope={slope:.3f}  R²={r_squared:.2f}")
      ax.set_xlabel(f"Distance to front (px)", fontsize=7)
      ax.set_ylabel("Polarity magnitude", fontsize=7)
      ax.legend(fontsize=6, frameon=False)

      fig_path = output_dir / "magnitude_vs_distance.pdf"
      fig.savefig(fig_path, bbox_inches="tight", dpi=600)
      plt.close(fig)

      results = {
          "n_cells": int(len(df_clean)),
          "slope": slope,
          "intercept": intercept,
          "r_squared": r_squared,
          "distance_col_found": True,
      }
      (output_dir / "magnitude_vs_distance_results.json").write_text(
          json.dumps(results, indent=2)
      )
      return results
  ```

---

## Task 9: Create `_cli_analyze.py`

**Files:** Create `src/quantipy_polarity/experimental/_cli_analyze.py` — **wait**: this lives at `src/quantipy_polarity/_cli_analyze.py` (top-level, consistent with all other CLI modules).

`_cli_analyze.py` implements `quantipy analyze` as a Click command group with two subcommands. Each subcommand validates its inputs and delegates to the corresponding `experimental/analyses/` function.

- [ ] **Step 1: Write `_cli_analyze.py`.**

  ```python
  """quantipy analyze <subcommand> — curated experimental analyses (experimental API).

  Subcommands:
      polarity-by-condition   Boxplot + Mann-Whitney U
      magnitude-vs-distance   Scatter + Theil-Sen robust regression
  """

  from __future__ import annotations

  from pathlib import Path

  import click

  from quantipy_polarity.cli import main


  @main.group("analyze", short_help="[Advanced] Run a curated experimental analysis")
  def analyze_group() -> None:
      """Run a curated experimental analysis (experimental API — may change).

      Use ``quantipy analyze <name> --help`` for subcommand options.
      """


  @analyze_group.command("polarity-by-condition")
  @click.option(
      "--per-cell",
      "per_cell_path",
      required=True,
      type=click.Path(exists=True, dir_okay=False, path_type=Path),
      help="Path to per_cell.parquet from a quantipy run.",
  )
  @click.option(
      "--metadata",
      "metadata_path",
      required=True,
      type=click.Path(exists=True, dir_okay=False, path_type=Path),
      help="CSV or TSV with columns [fov_id, condition] (or --condition-col).",
  )
  @click.option(
      "--output-dir",
      default="./analyze_results",
      type=click.Path(path_type=Path),
      show_default=True,
      help="Directory for output PDF + JSON.",
  )
  @click.option(
      "--condition-col",
      default="condition",
      show_default=True,
      help="Column name in metadata for the grouping variable.",
  )
  @click.option(
      "--magnitude-col",
      default="qp_magnitude",
      show_default=True,
      help="Column name in per_cell.parquet for polarity magnitude.",
  )
  def polarity_by_condition_cmd(
      per_cell_path: Path,
      metadata_path: Path,
      output_dir: Path,
      condition_col: str,
      magnitude_col: str,
  ) -> None:
      """Boxplot of polarity magnitude grouped by experimental condition."""
      from quantipy_polarity.experimental.analyses.polarity_by_condition import (
          run_polarity_by_condition,
      )
      try:
          results = run_polarity_by_condition(
              per_cell_path, metadata_path, output_dir,
              condition_col=condition_col, magnitude_col=magnitude_col,
          )
      except (FileNotFoundError, ValueError) as exc:
          raise click.ClickException(str(exc)) from exc

      p = results.get("p_value")
      p_str = f"{p:.3g}" if p is not None else "n/a"
      click.echo(f"Groups: {results['groups']}")
      click.echo(f"N per group: {results['n_per_group']}")
      click.echo(f"Medians: {[round(m, 4) for m in results['medians']]}")
      click.echo(f"p-value ({results.get('test_used', '—')}): {p_str}")
      click.echo(f"Output → {output_dir}/")


  @analyze_group.command("magnitude-vs-distance")
  @click.option(
      "--per-cell",
      "per_cell_path",
      required=True,
      type=click.Path(exists=True, dir_okay=False, path_type=Path),
      help="Path to per_cell.parquet from a quantipy run.",
  )
  @click.option(
      "--output-dir",
      default="./analyze_results",
      type=click.Path(path_type=Path),
      show_default=True,
      help="Directory for output PDF + JSON.",
  )
  @click.option(
      "--distance-col",
      default="dist_to_front_px",
      show_default=True,
      help="Column name for distance to migration front.",
  )
  @click.option(
      "--magnitude-col",
      default="qp_magnitude",
      show_default=True,
      help="Column name for polarity magnitude.",
  )
  @click.option(
      "--max-cells",
      default=5000,
      show_default=True,
      type=int,
      help="Maximum cells to plot (random subsample for legibility).",
  )
  def magnitude_vs_distance_cmd(
      per_cell_path: Path,
      output_dir: Path,
      distance_col: str,
      magnitude_col: str,
      max_cells: int,
  ) -> None:
      """Scatter of polarity magnitude vs distance-to-front with robust regression."""
      from quantipy_polarity.experimental.analyses.magnitude_vs_distance import (
          run_magnitude_vs_distance,
      )
      try:
          results = run_magnitude_vs_distance(
              per_cell_path, output_dir,
              magnitude_col=magnitude_col,
              distance_col=distance_col,
              max_cells=max_cells,
          )
      except (FileNotFoundError, ValueError) as exc:
          raise click.ClickException(str(exc)) from exc

      if not results.get("distance_col_found"):
          click.echo(f"Note: {results.get('note', '')}")
          click.echo(f"JSON written → {output_dir}/magnitude_vs_distance_results.json")
          return

      click.echo(f"N cells: {results['n_cells']}")
      click.echo(f"Theil-Sen slope: {results['slope']:.4f}")
      click.echo(f"R²: {results['r_squared']:.4f}")
      click.echo(f"Output → {output_dir}/")
  ```

---

## Task 10: Tests for `interactive/`

**Files:** Create `tests/interactive/__init__.py`, Create `tests/interactive/test_build_viewer.py`

Tests are fast-tier: they build a minimal in-memory fixture (a tiny per_cell.parquet + a 10×10 synthetic PNG) and call `build_viewer()`. No real results directory required.

- [ ] **Step 1: Write `tests/interactive/test_build_viewer.py`.**

  Tests to include (minimum 8 tests):

  1. `test_build_viewer_writes_html_file` — `build_viewer(results_dir, output_path)` creates the file at `output_path`.
  2. `test_html_is_self_contained` — output HTML does not contain any `http://` or `https://` URL outside of data URIs.
  3. `test_html_contains_fov_id` — FOV IDs from the parquet appear in the HTML.
  4. `test_html_contains_cells_json` — the string `"ALL_CELLS"` appears in the HTML (JS constant name).
  5. `test_html_contains_base64_image` — if a PNG exists in `03_polarity/maps/`, the output contains `data:image/png;base64,`.
  6. `test_html_no_image_placeholder` — if no PNG exists, the output contains `fov-placeholder` (graceful missing-image handling).
  7. `test_build_viewer_fov_filter` — `build_viewer(..., fov="fov_A")` only embeds cells with `fov_id == "fov_A"`.
  8. `test_build_viewer_missing_parquet_raises` — `build_viewer` raises `FileNotFoundError` when the parquet does not exist.
  9. `test_build_viewer_empty_parquet_raises` — `build_viewer` raises `ValueError` when parquet has no rows.
  10. `test_build_viewer_missing_required_column_raises` — raises `ValueError` when a required column is absent.
  11. `test_build_viewer_atomic_write` — if `output_path` already exists, the old content is replaced (not left partially written).
  12. `test_build_viewer_creates_parent_dir` — parent directory of `output_path` is created if it does not exist.

  **Fixture helper** (in the test file, not conftest — it is test-local):

  ```python
  import base64
  import struct
  import zlib
  from pathlib import Path

  import pandas as pd
  import numpy as np
  import pytest

  from quantipy_polarity.interactive.build_viewer import build_viewer


  def _make_minimal_png(path: Path) -> None:
      """Write a 1×1 white PNG to path (pure Python, no PIL/skimage required)."""
      def _crc(data: bytes) -> bytes:
          return struct.pack(">I", zlib.crc32(data) & 0xFFFFFFFF)
      sig = b"\x89PNG\r\n\x1a\n"
      ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
      ihdr_chunk = b"IHDR" + ihdr_data
      ihdr = struct.pack(">I", 13) + ihdr_chunk + _crc(ihdr_chunk)
      raw_row = b"\x00\xFF\xFF\xFF"  # filter byte + RGB
      idat_data = zlib.compress(raw_row)
      idat_chunk = b"IDAT" + idat_data
      idat = struct.pack(">I", len(idat_data)) + idat_chunk + _crc(idat_chunk)
      iend_chunk = b"IEND"
      iend = struct.pack(">I", 0) + iend_chunk + _crc(iend_chunk)
      path.write_bytes(sig + ihdr + idat + iend)


  @pytest.fixture()
  def results_dir(tmp_path: Path) -> Path:
      """Minimal results directory with per_cell.parquet + one polarity map PNG."""
      agg_dir = tmp_path / "05_aggregated"
      agg_dir.mkdir(parents=True)
      maps_dir = tmp_path / "03_polarity" / "maps"
      maps_dir.mkdir(parents=True)

      df = pd.DataFrame({
          "fov_id": ["fov_A", "fov_A", "fov_B"],
          "cell_id": [1, 2, 3],
          "qp_magnitude": [0.3, 0.7, 0.5],
          "qp_axis_deg": [45.0, 90.0, 120.0],
          "centroid_x": [100.0, 200.0, 150.0],
          "centroid_y": [100.0, 200.0, 150.0],
      })
      df.to_parquet(agg_dir / "per_cell.parquet", index=False)
      _make_minimal_png(maps_dir / "fov_A_polarity_map.png")
      return tmp_path
  ```

---

## Task 11: Tests for `experimental/analyses/`

**Files:** Create `tests/experimental/__init__.py`, Create `tests/experimental/test_polarity_by_condition.py`, Create `tests/experimental/test_magnitude_vs_distance.py`

Tests are fast-tier. Both analysis functions are tested with synthetic DataFrames written to `tmp_path`.

- [ ] **Step 1: Write `tests/experimental/test_polarity_by_condition.py`.**

  Tests to include (minimum 8 tests):

  1. `test_two_group_produces_pdf_and_json` — function creates both output files.
  2. `test_two_group_returns_p_value` — returned dict has `p_value` that is a float.
  3. `test_two_group_mann_whitney_test_name` — `test_used == "Mann-Whitney U"`.
  4. `test_group_n_and_medians_correct` — `n_per_group` sums match total merged cells; medians are finite floats.
  5. `test_three_group_no_p_value` — with three conditions, `p_value is None` and `note` is not None.
  6. `test_missing_per_cell_raises_fnf` — `FileNotFoundError` when parquet path does not exist.
  7. `test_missing_metadata_raises_fnf` — `FileNotFoundError` when metadata path does not exist.
  8. `test_missing_magnitude_col_raises_value_error` — `ValueError` with a custom column name that does not exist.
  9. `test_missing_condition_col_raises_value_error` — `ValueError` when `--condition-col` is absent from metadata.
  10. `test_fewer_than_two_groups_raises` — `ValueError` when only one condition value is present.
  11. `test_tsv_metadata_supported` — TSV metadata file is read correctly (tab-separated).

- [ ] **Step 2: Write `tests/experimental/test_magnitude_vs_distance.py`.**

  Tests to include (minimum 7 tests):

  1. `test_with_distance_col_produces_pdf_and_json` — both output files are created.
  2. `test_returns_slope_and_r_squared` — returned dict has `slope` and `r_squared` as floats.
  3. `test_missing_distance_col_returns_gracefully` — when `distance_col` is absent, returns dict with `distance_col_found=False` and no PDF (function does not raise).
  4. `test_missing_distance_col_writes_json` — the JSON results file is still written when distance col is absent.
  5. `test_missing_per_cell_raises_fnf` — `FileNotFoundError` when parquet does not exist.
  6. `test_missing_magnitude_col_raises_value_error` — `ValueError`.
  7. `test_max_cells_subsample` — with `max_cells=5`, a 100-row parquet results in N ≤ 5 in the returned `n_cells`.
  8. `test_r_squared_range` — `r_squared` is between 0.0 and 1.0 inclusive.

---

## Task 12: CLI tests for `debug` and `analyze`

**Files:** Create `tests/cli/test_cli_debug.py`, Create `tests/cli/test_cli_analyze.py`

- [ ] **Step 1: Write `tests/cli/test_cli_debug.py`.**

  Use `click.testing.CliRunner`.

  Tests to include (minimum 6 tests):

  1. `test_debug_writes_html` — `quantipy debug --results <results_dir>` writes `viewer.html` in the results dir.
  2. `test_debug_custom_output_path` — `--output /tmp/custom.html` writes to the specified path.
  3. `test_debug_fov_flag` — `--fov fov_A` produces HTML containing `"fov_A"`.
  4. `test_debug_missing_results_dir_exits_nonzero` — passing a non-existent path exits with code ≠ 0.
  5. `test_debug_missing_parquet_exits_nonzero` — a results dir that exists but has no parquet exits with code ≠ 0.
  6. `test_debug_no_browser_opened` — output message says "no server required" (confirms no `webbrowser.open` was called — patch `webbrowser.open` and assert it was NOT called).
  7. `test_debug_help_flag` — `quantipy debug --help` exits 0 and mentions `--results`.

- [ ] **Step 2: Write `tests/cli/test_cli_analyze.py`.**

  Tests to include (minimum 8 tests):

  1. `test_analyze_help` — `quantipy analyze --help` exits 0.
  2. `test_analyze_polarity_by_condition_help` — `quantipy analyze polarity-by-condition --help` exits 0 and mentions `--per-cell`.
  3. `test_analyze_magnitude_vs_distance_help` — `quantipy analyze magnitude-vs-distance --help` exits 0.
  4. `test_polarity_by_condition_missing_per_cell_exits_nonzero` — exits ≠ 0 with a clean error message.
  5. `test_polarity_by_condition_runs_end_to_end` — with valid synthetic parquet + metadata CSV in tmp_path, exits 0 and writes PDF + JSON.
  6. `test_magnitude_vs_distance_runs_end_to_end` — with synthetic parquet (including distance col), exits 0.
  7. `test_magnitude_vs_distance_no_distance_col_exits_zero` — exits 0 (graceful) and prints the note.
  8. `test_analyze_unknown_subcommand_shows_help` — `quantipy analyze unknown-name` exits non-zero with usage help.

---

## Task 13: Write `docs/cli-reference.md`, `docs/api-reference.md`, `docs/interactive-viewer.md`

**Files:** Create `docs/cli-reference.md`, Create `docs/api-reference.md`, Create/update `docs/interactive-viewer.md`

These are hand-written markdown files — not auto-generated from `--help`. Each cross-references others via relative links. No external URLs except the GitHub repo.

- [ ] **Step 1: Write `docs/cli-reference.md`.**

  Structure:
  ```
  # CLI Reference

  ## Primary commands
  ### quantipy init-config
  ### quantipy download-demo
  ### quantipy run
  ### quantipy debug
  ### quantipy validate

  ## Advanced commands
  ### quantipy ingest
  ### quantipy segment
  ### quantipy polarity
  ### quantipy front
  ### quantipy plot
  ### quantipy report
  ### quantipy analyze
  #### quantipy analyze polarity-by-condition
  #### quantipy analyze magnitude-vs-distance
  ```

  Each section includes: synopsis, description (1–2 sentences), options table (flag | type | default | description), example invocation.

- [ ] **Step 2: Write `docs/api-reference.md`.**

  Document the public Python API for users who want to call quantipy_polarity from a notebook or script without using the CLI. Covers:
  - `quantipy_polarity.Config` — Pydantic schema, `from_yaml()` class method
  - `quantipy_polarity.pipeline.run_pipeline(config: Config, output_dir: Path) -> None`
  - `quantipy_polarity.interactive.build_viewer(results_dir, output_path, *, fov=None) -> None`
  - `quantipy_polarity.validation.run_validation(...)` — brief mention with pointer to `docs/validation.md`
  - Note: `experimental.*` APIs are NOT covered here (they are intentionally unstable)

- [ ] **Step 3: Write `docs/interactive-viewer.md`.**

  Contents:
  - Opening a viewer: `quantipy debug --results ./demo_results` then `open viewer.html`
  - Layout: FOV image panel, cell list panel, info panel
  - Keyboard navigation: `←/→` FOV nav, `↑/↓` cell nav within FOV
  - What data is shown: all columns from `per_cell.parquet`
  - Sharing: the HTML file is fully self-contained; email or copy it anywhere
  - Headless use: works without a display (writes HTML; no `DISPLAY` required)
  - Limitations: read-only; does not rerun pipeline stages; large datasets (>50k cells) may make the page slow

---

## Task 14: Update `README.md`

**Files:** Modify `README.md`

- [ ] **Step 1: Update the status table** to show Phase 7 as complete.

  Change:
  ```
  | 7 | Interactive viewer + experimental analyses | 🔲 Planned |
  ```
  to:
  ```
  | 7 | Interactive viewer + experimental analyses | ✅ Complete |
  ```

- [ ] **Step 2: Add a table of contents** near the top of the README (after the one-liner description and before "Status").

  ```markdown
  ## Contents

  - [Quickstart](#quickstart)
  - [Documentation](#documentation)
  - [CLI reference](#cli-reference)
  - [Developer workflow](#developer-workflow)
  - [Citation](#citation)
  ```

- [ ] **Step 3: Add a Documentation section** pointing to all docs/*.md files.

  ```markdown
  ## Documentation

  | Document | Contents |
  |----------|----------|
  | [docs/concepts.md](docs/concepts.md) | Biological assumptions, PCA polarity method |
  | [docs/pipeline.md](docs/pipeline.md) | Stage-by-stage pipeline description |
  | [docs/cli-reference.md](docs/cli-reference.md) | All CLI commands, flags, examples |
  | [docs/api-reference.md](docs/api-reference.md) | Public Python API |
  | [docs/interactive-viewer.md](docs/interactive-viewer.md) | Per-cell viewer usage guide |
  | [docs/migration-front.md](docs/migration-front.md) | Front detection algorithm |
  | [docs/validation.md](docs/validation.md) | QP-vs-Python comparison methodology |
  | [docs/developer-workflow.md](docs/developer-workflow.md) | Claude-Code integration, slash commands |
  ```

- [ ] **Step 4: Add or update the Citation section.**

  ```markdown
  ## Citation

  If you use QuantiPy Polarity in your research, please cite it (see `CITATION.cff`):

  ```bibtex
  @software{mclean_quantipy_polarity_2026,
    author  = {McLean, Taggart},
    title   = {{QuantiPy Polarity}},
    year    = {2026},
    version = {0.1.0},
    url     = {https://github.com/mcleanT/QuantiPy-Polarity},
    license = {MIT}
  }
  ```

  Please also cite the original QuantifyPolarity tool from the Hughes Lab, whose boundary-PCA algorithm this package reimplements.
  ```

---

## Task 15: Final acceptance run + git tag

**Files:** No new files. Run tests, commit, tag.

- [ ] **Step 1: Run the full test suite.**

  ```bash
  cd /tmp/QuantiPy-Polarity-work
  python -m pytest tests/ -v --tb=short 2>&1 | tail -20
  ```

  Expected: ≥ 278 tests passed, 0 failed.

- [ ] **Step 2: Confirm `quantipy --version` returns `0.1.0`.**

  ```bash
  python -m quantipy_polarity.cli --version
  # Expected: quantipy, version 0.1.0
  ```

- [ ] **Step 3: Smoke-test `quantipy debug` (headless).**

  ```bash
  quantipy run --config demo/config.yaml --output /tmp/smoke_results --force
  quantipy debug --results /tmp/smoke_results --output /tmp/viewer.html
  python -c "
  content = open('/tmp/viewer.html').read()
  assert 'ALL_CELLS' in content, 'missing cells JSON'
  assert 'http' not in content.replace('https://github.com', ''), 'external URL found'
  print('viewer.html OK')
  "
  ```

- [ ] **Step 4: Smoke-test `quantipy analyze`.**

  ```bash
  python -c "
  import pandas as pd, numpy as np, tempfile, json
  from pathlib import Path
  tmp = Path(tempfile.mkdtemp())
  df = pd.DataFrame({
      'fov_id': ['f1']*50 + ['f2']*50,
      'cell_id': range(100),
      'qp_magnitude': np.random.default_rng(0).uniform(0.1, 0.9, 100),
      'qp_axis_deg': np.random.default_rng(1).uniform(0, 180, 100),
  })
  df.to_parquet(tmp / 'per_cell.parquet', index=False)
  meta = pd.DataFrame({'fov_id': ['f1','f2'], 'condition': ['ctrl','treat']})
  meta.to_csv(tmp / 'meta.csv', index=False)
  from quantipy_polarity.experimental.analyses.polarity_by_condition import run_polarity_by_condition
  r = run_polarity_by_condition(tmp / 'per_cell.parquet', tmp / 'meta.csv', tmp / 'out')
  assert r['p_value'] is not None
  print('polarity_by_condition OK  p =', r['p_value'])
  "
  ```

- [ ] **Step 5: Validate `CITATION.cff`.**

  ```bash
  pip install cff-validator --quiet 2>/dev/null && cff-validator CITATION.cff || \
  python -c "
  import yaml, pathlib
  d = yaml.safe_load(pathlib.Path('CITATION.cff').read_text())
  assert d['cff-version'] == '1.2.0'
  assert 'authors' in d
  assert 'title' in d
  for a in d['authors']:
      assert 'orcid' not in a or a['orcid'].startswith('https://orcid.org/')
  print('CITATION.cff OK')
  "
  ```

- [ ] **Step 6: Commit and tag.**

  ```bash
  git add CITATION.cff CHANGELOG.md \
          src/quantipy_polarity/_stubs.py \
          src/quantipy_polarity/cli.py \
          src/quantipy_polarity/interactive/ \
          src/quantipy_polarity/_cli_debug.py \
          src/quantipy_polarity/experimental/ \
          src/quantipy_polarity/_cli_analyze.py \
          tests/interactive/ tests/experimental/ tests/cli/test_cli_debug.py tests/cli/test_cli_analyze.py \
          docs/cli-reference.md docs/api-reference.md docs/interactive-viewer.md \
          README.md

  git commit -m "feat(phase-7): interactive viewer, experimental analyses, final polish

  - Add quantipy debug: static self-contained HTML per-cell viewer (Option B, no display backend)
  - Add quantipy analyze polarity-by-condition: Mann-Whitney boxplot
  - Add quantipy analyze magnitude-vs-distance: Theil-Sen robust regression scatter
  - Add CITATION.cff, CHANGELOG.md, docs/cli-reference.md, docs/api-reference.md
  - Remove debug + analyze stubs; wire real CLI modules
  - 278+ tests passing (243 baseline + 35 new)"

  git tag phase-7-complete
  git tag v0.1.0
  ```

---

## Task Dependency Graph

```
Task 1 (CITATION.cff)          — no deps
Task 2 (CHANGELOG.md)          — no deps
Task 3 (remove stubs)          — no deps (but must precede Task 6 + Task 9 to avoid double-registration)
Task 4 (build_viewer.py)       — no deps
Task 5 (viewer.html.j2)        — must follow Task 4 (template is loaded by build_viewer.py)
Task 6 (_cli_debug.py)         — must follow Task 3, Task 4, Task 5
Task 7 (polarity_by_condition) — no deps
Task 8 (magnitude_vs_distance) — no deps
Task 9 (_cli_analyze.py)       — must follow Task 3, Task 7, Task 8
Task 10 (tests interactive/)   — must follow Task 4, Task 5
Task 11 (tests experimental/)  — must follow Task 7, Task 8
Task 12 (tests cli/)           — must follow Task 6, Task 9, Task 10, Task 11
Task 13 (docs)                 — no deps (hand-written; can run in parallel with code tasks)
Task 14 (README.md)            — no deps
Task 15 (acceptance + tag)     — must follow ALL tasks
```

**Batch dispatch order (for subagent-driven-development):**

| Batch | Tasks | Notes |
|-------|-------|-------|
| Batch 1 | 1, 2, 3, 4, 7, 8, 13, 14 | Independent; run in parallel |
| Batch 2 | 5, 6, 9, 10, 11 | Depends on Batch 1 Task 3/4/7/8 |
| Batch 3 | 12 | Depends on Batch 2 |
| Batch 4 | 15 | Final: run tests, commit, tag |
