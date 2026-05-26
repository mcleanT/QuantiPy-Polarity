# QuantiPy Polarity — Public Repo Design

**Date:** 2026-05-26
**Target repo:** https://github.com/mcleanT/QuantiPy-Polarity
**Source dir:** `Science/Hughes Lab/Sachin/Polarity Quantification/`
**New location:** `Science/QuantiPy-Polarity/` (sibling to `Hughes Lab/`)
**Status:** Revised post-codex-review (rev 1); awaiting user review before transition to writing-plans

**Revision history:**
- 2026-05-26 rev 0 — initial draft after brainstorming session
- 2026-05-26 rev 1 — applied codex (gpt-5.5) adversarial review (saved alongside as `*-codex-review.txt`): narrowed generality claim, added Assumptions & Validity section, restructured CLI into primary vs advanced, deferred interactive front tuner to v0.2, added resume/atomic-write semantics, moved `analyses/` to `experimental/`, added module data-contracts table, framed Claude-Code as developer workflow, tightened validation wording, added dependency upper bounds, made synthetic the default demo, gated Cellpose CI tests, and made the public package upstream for the research dir.

---

## 1. Purpose

Package the existing Python reimplementation of QuantifyPolarity (QP) — currently developed in `Hughes Lab/Sachin/Polarity Quantification/` — as a standalone public repository: **QuantiPy Polarity**.

The single-shot promise: a user feeds in raw microscopy images and receives per-FOV polarity maps, rose plots, quantitative tables, migration-front overlays, and a self-contained HTML report — without needing to install the original QP `.app` binary or understand the staged-pipeline internals.

## 2. Goals and non-goals

**Goals:**
- One CLI command (`quantipy run`) takes raw images to all outputs.
- **Channel-configurable** for membrane-associated planar-polarity markers (Vangl, Frizzled, Celsr1, Crumbs, etc.) — channel indices set via config. See "Assumptions and validity" below for what this does and does not cover.
- Three input entry points: `.nd2`, multi-page `.tif`, or pre-segmented label masks. **Pre-segmented masks + TIF is the documented quickstart path**; raw ND2 + Cellpose-SAM is the "full pipeline" path with documented environment caveats.
- Python implementation only — no vendored QP binary.
- Developer-workflow Claude-Code integration: `CLAUDE.md`, `.claude/settings.json`, and slash commands ship in-repo but are documented under a Developer Workflow section, not as headline features. Claude is not required to use the tool.
- Ship validation provenance: per-cell parquet, hashes, source-column lineage, QP version pinned, and a regeneratable QP-vs-Python figure. Users can verify they reproduce the shipped comparison analysis — not perform independent equivalence testing without QP.
- MIT license, single-author authorship.

**Non-goals (v0.1.0):**
- PyPI publishing (deferred to v0.2).
- Vendor the QP `.app` binary (cite the original tool instead).
- Generalize to non-planar-polarity quantification (e.g., apical-basal).
- Support `.lif` / `.czi` / `.lsm` input formats (deferred; can add later via `aicsimageio`).
- `quantipy front --interactive` parameter tuner with live config mutation (deferred to v0.2 — see §8).
- mkdocs documentation site (plain markdown is sufficient for v0.1.0).
- "Curated analyses" as stable API in the core namespace (lives in `experimental/` for v0.1.0; promote once external datasets validate them).

## 2a. Assumptions and validity

The pipeline is built on specific biological and image-processing assumptions. Each must hold for results to be meaningful. Documented in the README and `docs/concepts.md`; tests check the assumptions where feasible.

**Supported:**
- **Membrane-localized planar polarity markers.** Boundary-PCA reads polarity from the intensity distribution along cell perimeters; markers that decorate membrane (Celsr1, Vangl2, Frizzled, Crumbs, E-cadherin) are in-scope.
- **Confluent or near-confluent epithelial sheets** with segmentable cell boundaries.
- **Axial (head-tail-symmetric) polarity** — angles are mod π. Vector (mod 2π) polarity is configurable but not the validated default.
- **Collective migration with a definable front** — required for `quantipy front`. Random-walk or non-migrating tissue: skip migration analysis.

**Not supported / out of scope:**
- Diffuse cytoplasmic markers (no membrane signal to do boundary-PCA on).
- Puncta-only markers (e.g., Wnt receptors at vesicle hotspots; PCA does not capture punctum-by-punctum statistics).
- Apical-basal polarity (Z-direction polarity is orthogonal to this tool).
- Sparse or non-confluent cells (boundary detection fails; cell-to-cell adjacency is the implicit assumption).
- Non-front migration regimes (rotational, contractile, isolated single-cell tracks).
- 3D polarity (everything is 2D projections or single slices).

## 3. Scope decisions (resolved during brainstorming)

| Decision | Resolution |
|---|---|
| Scope | Core pipeline + curated analyses (~25 files) |
| Entry point | CLI-first (`quantipy ...`), Python API exists for free via clean package layout but is not heavily advertised |
| Input formats | `.nd2`, multi-page `.tif/.tiff`, pre-segmented label masks |
| Generality | Channel-configurable for **membrane-associated planar polarity markers**; explicit assumptions in §2a |
| Outputs | Per-FOV polarity maps + rose plots + quantitative tables + migration overlays + HTML report |
| QP binary | Python-only; drop vendored `.app`; cite original QP paper |
| License | MIT |
| Sample data | Tiny synthetic fixture in-repo + real FOV via GitHub Releases (not git-lfs) |
| Claude-Code integration | `CLAUDE.md` + `.claude/settings.json` + three custom slash commands |
| Repo home | Personal account (`mcleanT/QuantiPy-Polarity`), single-author, with `CITATION.cff` |
| Packaging | Approach A — clean `src/` Python package layout, CLI documented as primary entry |
| Validation | Dedicated `validation/` subpackage shipping the QP-vs-Python linear-relationship figure as static evidence |

## 4. Repository layout

```
QuantiPy-Polarity/
├── README.md                         # Install, quickstart, screenshot, citation
├── LICENSE                           # MIT
├── CITATION.cff                      # GitHub "Cite this repository" support
├── CONTRIBUTING.md
├── pyproject.toml                    # Build, deps, console_scripts entry
├── environment.yml                   # Conda alternative for users who need it
├── CLAUDE.md                         # Orientation for Claude-Code sessions
├── .claude/
│   ├── settings.json                 # Pre-approved safe Bash commands
│   └── commands/
│       ├── quantipy-run.md
│       ├── quantipy-debug-fov.md
│       └── quantipy-front-qc.md       # static QC overlay regen + diff (no GUI)
├── .github/workflows/
│   ├── ci.yml                        # pytest, Python 3.11+3.12, macOS+Ubuntu
│   └── release.yml                   # Upload demo + validation assets to Releases
├── src/
│   └── quantipy_polarity/
│       ├── __init__.py
│       ├── cli.py                    # Click root + subcommand registry
│       ├── config.py                 # Pydantic schema + YAML loader
│       ├── io/
│       │   ├── nd2.py
│       │   ├── tif.py
│       │   └── masks.py
│       ├── segment/
│       │   ├── cellpose.py
│       │   └── postprocess.py
│       ├── polarity/
│       │   ├── boundary_pca.py
│       │   └── per_cell.py
│       ├── migration/
│       │   ├── front.py              # Automated (v3 outward-side)
│       │   ├── tune.py               # Interactive parameter tuner
│       │   └── local.py              # Per-cell local migration direction
│       ├── viz/
│       │   ├── style.py              # Nature-style mpl params, palette
│       │   ├── polarity_map.py
│       │   ├── rose.py
│       │   └── overlay.py
│       ├── report/
│       │   ├── html.py               # Jinja2 + base64 inlining
│       │   └── templates/
│       ├── interactive/
│       │   └── viewer.py             # debug_polarity refactor (read-only)
│       ├── experimental/             # NOT part of stable API in v0.1.0
│       │   ├── __init__.py           # Header banner: "Experimental — APIs may change"
│       │   └── analyses/             # Registry-based; opt-in via config or CLI
│       │       ├── __init__.py       # Registry for `quantipy analyze <name>`
│       │       ├── per_fov_rose.py
│       │       ├── polarity_heatmap.py
│       │       ├── ar_stratified_rose.py
│       │       ├── axis_alignment.py
│       │       ├── magnitude_vs_distance.py
│       │       └── polarization_decline.py
│       └── validation/
│           ├── linear_relationship.py    # Regenerates QP-vs-Python scatter
│           └── README.md                 # Provenance, sample sizes, QP version
├── tests/
│   ├── fixtures/
│   │   ├── synthetic_fov.tif
│   │   └── _build.py                 # Procedural fixture generator
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_io.py
│   ├── test_segment.py
│   ├── test_polarity.py
│   ├── test_front.py
│   ├── test_viz.py
│   ├── test_cli.py
│   └── test_e2e.py                   # quantipy run on synthetic_fov
├── examples/
│   ├── quickstart.md
│   ├── notebooks/
│   │   └── exploring_polarity.ipynb
│   └── configs/
│       ├── default.yaml
│       └── celsr_optoclones.yaml
└── docs/
    ├── concepts.md
    ├── pipeline.md
    ├── cli-reference.md
    ├── config-reference.md
    ├── outputs.md
    ├── interactive-viewer.md
    ├── migration-front.md
    ├── validation.md
    └── citing.md
```

### Layout rationale

- `src/` layout (not flat) prevents accidental local-import wins during tests and is the standard for PyPI-publishable scientific packages.
- Subpackages organized by **concern** (`io/`, `segment/`, `polarity/`, ...) rather than stage number. Pipeline ordering is defined in `cli.py`, not in directory names. Python module names cannot begin with digits, so this is also a hard requirement for the Python API to exist at all.
- `experimental/analyses/` houses the curated analyses bucket but is **explicitly labeled experimental** — APIs may change, no stability guarantees, separate namespace so users see the distinction. Promotion to the stable core happens once external datasets validate the analysis.
- `validation/` is a peer of the core modules — it is the dedicated home for QP-vs-Python provenance and figure regeneration.
- `.claude/commands/` ships three slash commands. `.claude/settings.json` pre-approves read-only Bash so users avoid permission prompts on first run.

## 5. CLI surface

All commands installed via `pyproject.toml`'s `[project.scripts]` as `quantipy = "quantipy_polarity.cli:main"`. `quantipy --help` is grouped into **primary** (what biologists need) and **advanced** (stage-resume + validation tooling). The advanced commands exist but are tagged "Advanced" in CLI help and only briefly mentioned in `docs/cli-reference.md`.

**Primary commands (documented in README quickstart):**

| Command | Purpose |
|---|---|
| `quantipy init-config --mode {nd2,tif,masks}` | Scaffold a working config for one of the three input modes. Removes guesswork; users get a YAML with sensible defaults pre-filled for their pipeline shape. |
| `quantipy download-demo` | Pull demo bundle from latest GitHub Release (synthetic by default; `--real` flag opts into the real FOV if licensing resolved). |
| `quantipy run` | Single-shot: input → all outputs. Accepts `--resume` and `--force` (see §7). |
| `quantipy debug` | Read-only per-cell viewer (see §8). |
| `quantipy validate` | Regenerate QP-vs-Python comparison figure from the shipped validation parquet (see §9). |

**Advanced / resume commands (tagged "Advanced" in `--help`, not in README):**

| Command | Wraps | Purpose |
|---|---|---|
| `quantipy ingest` | `io/` | nd2/tif → normalized per-FOV TIFs |
| `quantipy segment` | `segment/` | Cellpose-SAM → label masks |
| `quantipy polarity` | `polarity/` | Label masks + membrane channel → per-cell axes |
| `quantipy front` | `migration/` | Migration-front detection (`--auto` only in v0.1.0; `--interactive` deferred — see §8) |
| `quantipy aggregate` | `polarity/per_cell.py` | Per-FOV parquet → experiment parquet |
| `quantipy plot` | `viz/` | Regenerate plots from existing aggregated parquet |
| `quantipy report` | `report/` | Regenerate HTML report from existing run dir |
| `quantipy analyze <name>` | `experimental/analyses/<name>` | Run a curated analysis (experimental API) |

Every subcommand accepts `--config <path>`, `--input <path>`, `--output <path>`, plus `--resume` / `--force` where stage state matters (§7).

### Input modes — explicit, not auto-magic

Three modes (`nd2`, `tif`, `masks`) are first-class. Users pick one via `quantipy init-config --mode {nd2,tif,masks}`, which writes a config pre-populated with the fields that mode actually needs (channel indices, pixel size, z-policy for nd2; FOV-naming conventions for tif; mask-membrane pairing rules for masks). The mode is then stored as `input.mode` in the YAML and validated at load time.

`input.source: auto` is **available as a convenience** for users who already understand the modes — it inspects the directory and picks `nd2` if any `.nd2` is present, else `tif` if any `.tif/.tiff` is present, else `masks` if a mask-membrane pair structure is found. Auto-detection prints the chosen mode and asks the user to confirm if `quantipy run` is interactive; in `--yes` / scripted mode it proceeds without prompting. Auto is **not** the default — `init-config` produces an explicit-mode YAML so first-time users never run into "auto picked the wrong mode."

## 6. Configuration

Single YAML, Pydantic-validated. Users generate one with `quantipy init-config --mode {nd2,tif,masks}` rather than relying on defaults — every mode has experiment-specific fields (channel semantics, pixel size, z-policy, FOV naming, mask pairing) that cannot all be inferred. The Pydantic schema discriminates on `input.mode` and only accepts the fields valid for that mode.

```yaml
project:
  name: my_experiment
  output_dir: ./results

input:
  mode: nd2                        # required: nd2 | tif | masks (NOT auto by default)
  source: explicit                 # explicit | auto (auto = best-effort directory inspection)
  path: ./raw
  z_policy: mip                    # mip | substack | none           # nd2/tif only
  substack_range: [3, 12]
  channel_membrane: 1              # 0-indexed                         # nd2/tif only
  channel_segmentation: 1
  pixel_size_um: 0.65
  masks_dir: null                  # required if mode=masks; pairing rule documented

segment:
  model: cellpose-sam              # cellpose-sam | user_supplied
  diameter_px: 60
  min_size_px: 100
  fix_undersegmented: true
  user_masks_dir: null

polarity:
  method: boundary_pca
  axial: true
  weight: magnitude                # magnitude | uniform
  exclude_edge_cells: true

migration:
  detect_front: true
  front_method: v3_outward         # v3_outward | none
  erosion_px: 10
  classify_fragments: true
  local_direction: true

viz:
  style: nature                    # nature | minimal
  rose_bins: 24
  half_disk: true
  per_fov_maps: true
  overlay_dpi: 600
  vector_scale: 1.0

report:
  html: true
  embed_thumbnails: true
  include_per_cell_parquet: true

analyses:                          # opt-in; run after core pipeline
  - per_fov_rose
  - polarity_heatmap
```

Each subcommand validates only the slice it needs (`quantipy plot` does not require `segment.diameter_px`). Config snapshot is written to `results/run_config.yaml` for reproducibility. `examples/configs/celsr_optoclones.yaml` ships as a real-world reference config (the actual one used for the optoCelsr analysis).

## 7. Output layout

```
results/
├── run_config.yaml                 # Resolved config snapshot
├── run_info.json                   # Version, timestamps, input hash, cell counts
├── 01_ingest/                      # Per-FOV normalized TIFs
├── 02_segmentation/                # Label masks + QC overlays
├── 03_polarity/
│   ├── per_fov/                    # Per-FOV polarity parquets
│   └── maps/                       # Vector overlays (PNG + PDF)
├── 04_migration/
│   ├── front_overlays/             # Front + arrows (PNG + PDF)
│   └── per_cell_migration.parquet
├── 05_aggregated/
│   └── per_cell.parquet            # Experiment-wide table
├── 06_plots/
│   ├── rose_per_fov.pdf
│   ├── rose_aggregate.pdf
│   └── polarity_heatmaps.pdf
└── report.html                     # Single-file self-contained report
```

### HTML report

Self-contained — all figures base64-inlined so the file is portable on its own:

1. Header: project name, timestamp, config hash, link to `per_cell.parquet`
2. Summary stats: N FOVs, N cells, median polarity magnitude, mean axis-vs-migration alignment, QC flag counts
3. Per-FOV gallery: thumbnail vector overlay + thumbnail rose plot + count chip per FOV
4. Aggregate rose (full-experiment half-disk)
5. Run config (expandable YAML block)
6. Citation block: BibTeX + Zenodo DOI placeholder

`quantipy report --results ./results --output ./report.html` regenerates the report from an existing run dir without rerunning the pipeline.

### Resume, overwrite, atomicity

Stages emit and consume well-defined directories. A `_stage_status.json` file in each stage dir records `{status: pending|running|complete|failed, started_at, completed_at, config_hash}`. Behavior:

- **`quantipy run`** without flags refuses to overwrite an existing non-empty `output_dir` and exits non-zero. Error message suggests `--resume` or `--force`.
- **`--resume`** scans `_stage_status.json` files, skips stages with `status=complete` *and* matching `config_hash`, re-executes everything downstream. Stages in `running` (process killed mid-run) or `failed` state re-execute.
- **`--force`** wipes `output_dir` and starts fresh.
- **Atomic writes:** Parquet and HTML outputs write to a temp path in the same directory then `os.replace` on success. No partially-written parquet ever appears as a "real" output. PNG/PDF figures follow the same pattern.
- **Config-hash invalidation:** a `config_hash` mismatch between `_stage_status.json` and current run forces re-execution of that stage regardless of `status`. Prevents "I resumed but stage 4 used the old config" silent reproducibility breakage.

## 8. Interactive viewers

### `quantipy debug` — per-cell viewer

`quantipy debug --results ./results [--fov FOV_NN]`

Refactor of `debug_polarity.py`, generalized (drop optoCelsr-specific labels). Layout:

- **Left panel:** FOV with membrane channel + cell outlines + per-cell polarity axes (color = magnitude). Click cells to select.
- **Right panel:** Selected cell's boundary trace, PCA axes, and parquet row.
- **Top bar:** FOV dropdown, ← → nav, colormap toggle, migration-front toggle.
- **Bottom strip:** Current-FOV rose plot, selected cell highlighted as red wedge.

Keybindings preserved from current viewer: `←/→` FOV nav, `↑/↓` cell nav within FOV, `s` save figure, `r` reset zoom.

Reads from `results/05_aggregated/per_cell.parquet`. Read-only over completed runs; never re-runs pipeline stages.

### `quantipy front --interactive` — DEFERRED to v0.2

Interactive parameter mutation via matplotlib GUI is the most fragile public-facing component (Matplotlib backend behavior varies wildly across SSH, macOS, headless Linux, notebook backends) and mutating the user's config from a GUI invites silent reproducibility drift. **Deferred to v0.2.**

**v0.1.0 substitute — static QC overlays + CLI rerun loop:**

`quantipy front --auto --qc` writes per-FOV diagnostic overlays into `results/04_migration/qc/`:
- Background-foreground classification mask
- Front line + per-cell outward arrows
- Fragment classification labels (kept / killed / boundary-touched)
- Erosion-overlay showing which background fragments survived

If the user wants to tune, they edit the YAML directly (`migration.erosion_px`, `migration.classify_fragments`), re-run `quantipy front --auto --qc --resume`, and visually compare the new overlays to the old ones (kept in a sibling `qc_prev/` dir on `--resume`). This pattern is more boring but reproducible by definition — the config file is the source of truth, not GUI state.

**v0.2 design sketch (not promised):** if/when the interactive tuner returns, it will *emit* a YAML patch (`migration_patch.yaml`) for the user to apply explicitly via `cp migration_patch.yaml config.yaml` (or manually merge). It will not mutate the running config.

The debug viewer detects non-interactive matplotlib backends and prints SSH hints instead of crashing.

### Automated migration front

`quantipy front --auto` is the default path called by `quantipy run`. Lifts from `recompute_migration_v3.py` + `compute_migration_field` (v6 real-bg fragment classification, erosion to suppress thin-sliver corner artifacts). Algorithm provenance documented in `docs/migration-front.md`.

## 9. Validation evidence

The QP-vs-Python correlation is shipped as a **reproducible analysis of a frozen reference dataset**, not as independent equivalence testing — users do not have QP installed, so they cannot rederive the QP side of the comparison from raw inputs. The public claim is therefore narrowly scoped: "QuantiPy Polarity reproduces the QP-vs-Python comparison analysis published with this release."

**Shipped artifacts (GitHub Releases on the v0.1.0 tag):**

- `validation_per_cell.parquet` (~few MB, lifted from `derived_mip/07_comparison/per_cell_v2.parquet`, ~114k cells across C10+D11). Each row: `fov, cell_id, qp_axis_deg, qp_magnitude, py_axis_deg, py_magnitude, mig_*, area_px`, plus QC columns.
- `validation_provenance.json` — SHA-256 hashes of the parquet, list of source columns used, QP binary version (`QuantifyPolarity.2022.2.1.Mac`), Python implementation commit at validation time, sample counts per FOV.
- `validation_figure_reference.pdf` — the canonical linear-relationship figure (axis correlation + magnitude correlation, linear fit, R², 95% CI) as shipped. Used as the byte-comparable target for `quantipy validate`.

**Tooling:**

- `src/quantipy_polarity/validation/linear_relationship.py` regenerates the scatter from the parquet.
- `quantipy validate` downloads the parquet on first call (cached to `~/.cache/quantipy/validation/`), regenerates the figure, and reports byte / structural diffs against `validation_figure_reference.pdf`. Passing = "you reproduced the published analysis."
- `docs/validation.md` documents methodology, sample sizes, QP version, source-script lineage in the research repo, and what users *can* vs *cannot* verify (cannot: re-derive QP outputs without QP).

**Optional escape hatch (advanced users only):** `docs/validation.md` includes a section on how to install QP independently and rerun the full comparison from raw `.nd2` images using a small `qp_validation_minicase/` bundle (subject to the demo-data licensing decision in §12). Not a v0.1.0 acceptance criterion.

## 10. Claude-Code integration (developer workflow)

**README does not mention Claude Code in the headline.** The tool is fully usable from any shell or Python session; Claude integration is an optional convenience, documented in `docs/developer-workflow.md` and a short "Developer workflow" section near the bottom of the README. The repo never implies Claude is required.

### `CLAUDE.md`

Orients Claude-Code sessions opened in the repo (for users who choose to open it that way):
- One-paragraph project description
- CLI command table (so Claude has the surface area)
- Where the config lives, demo-data invocation
- Pointer to `docs/` and the three slash commands
- "Read `docs/pipeline.md` before modifying any stage" guard

### `.claude/settings.json`

Pre-approves safe read-only commands:

```json
{
  "permissions": {
    "allow": [
      "Bash(quantipy *)",
      "Bash(pytest *)",
      "Bash(ls *)", "Bash(cat *)", "Bash(grep *)",
      "Bash(git status)", "Bash(git diff *)", "Bash(git log *)"
    ]
  }
}
```

Writes, pushes, installs still prompt.

### Slash commands

| Command | Wraps | When to use |
|---|---|---|
| `/quantipy-run` | `quantipy run` | One-shot end-to-end. Scaffolds default config via `init-config` if none found; asks before launching. |
| `/quantipy-debug-fov [FOV]` | `quantipy debug --fov $1` | Open viewer on FOV (or pick from dropdown). |
| `/quantipy-front-qc` | `quantipy front --auto --qc --resume` | Regenerate static front-detection QC overlays after editing `migration.*` config values; diff against previous overlays in `qc_prev/`. (Replaces the deferred interactive tuner.) |

Each command is a short markdown file with frontmatter; intentionally lightweight — convenience entry points, not autonomous agents.

## 11. Distribution

### `pyproject.toml`

```toml
[project]
name = "quantipy-polarity"
version = "0.1.0"
description = "Single-shot planar polarity quantification from raw microscopy images"
authors = [{name = "<full name TBD>", email = "taggartmc@pennmedicine.upenn.edu"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.26,<2.3",
  "scipy>=1.11,<1.16",
  "pandas>=2.1,<2.4",
  "pyarrow>=14,<19",
  "tifffile>=2024.1,<2026",
  "nd2reader>=3.3,<4",
  "scikit-image>=0.22,<0.25",
  "cellpose>=3.0,<4",          # SAM-line; v4 changes API
  "matplotlib>=3.8,<3.10",
  "click>=8.1,<9",
  "pydantic>=2.5,<3",
  "pyyaml>=6.0,<7",
  "jinja2>=3.1,<4",
  "structlog>=24.1,<25",
  "tqdm>=4.66,<5",
  "requests>=2.31,<3",
]

[project.optional-dependencies]
dev = ["pytest>=7.4", "pytest-cov", "ruff>=0.3", "mypy>=1.8"]
notebooks = ["jupyter", "ipywidgets"]

[project.scripts]
quantipy = "quantipy_polarity.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/quantipy_polarity"]
```

### Install paths (documented order — conda first)

1. **Conda (recommended)**: `conda env create -f environment.yml && conda activate quantipy && pip install -e .`
   Conda handles cellpose / pytorch / native image-IO libs more reliably than pip on macOS and Linux.
2. **Pip from GitHub**: `pip install git+https://github.com/mcleanT/QuantiPy-Polarity.git`
   Works for users already in a scientific Python env (e.g., an existing scanpy/scvi environment). Pin compatibility not guaranteed if their env lacks the upper bounds.
3. **Editable clone**: `git clone https://github.com/mcleanT/QuantiPy-Polarity.git && pip install -e .[dev]`
   For contributors and Claude-Code workflows.

`environment.yml` ships with tested versions for every dependency, including `cellpose`, `pytorch` (CPU-only by default; GPU via overlay), and the image-IO stack. PyPI publishing deferred to v0.2.

### Versioning

SemVer. v0.1.0 = first public release. GitHub Releases cut from tags. `release.yml` uploads demo + validation parquet assets per tagged release. `quantipy --version` reads from `importlib.metadata`.

## 12. Sample data

### Synthetic (in-repo)

`tests/fixtures/synthetic_fov.tif` (~1–3 MB):
- Procedurally generated by committed `tests/fixtures/_build.py` (Voronoi cells with known per-cell polarity ground truth).
- Doubles as regression fixture: `test_polarity.py` asserts boundary-PCA recovers seeded axis within tolerance.
- CI runs full `quantipy run` end-to-end on this fixture in <30s with no binary download.

### Default demo: synthetic only + de-identified TIF/masks (in-repo + Release)

- `quantipy download-demo` (no flags) downloads a **synthetic-cells bundle** + a **de-identified TIF + matching label-mask bundle** (~10–50 MB combined) from the v0.1.0 Release. No raw lab data. No `.nd2`. This is the default because (a) it works without resolving licensing, (b) it sidesteps Cellpose-SAM failures by including pre-segmented masks, (c) it lets first-time users hit `quantipy run` successfully within minutes.
- The de-identified bundle is produced from one optoCelsr FOV with experimental metadata stripped (clone ID, microscope serial, acquisition timestamps removed; only spatial pixel arrays + label masks retained).

### Optional real-FOV demo — `download-demo --real` (gated on licensing decision)

- One real `.nd2` from the optoCelsr dataset, uploaded as a Release asset only if redistribution rights are confirmed (see decision item below).
- If rights are confirmed: `quantipy download-demo --real` fetches `demo_real_FOV.zip` from the v0.1.0 Release.
- If rights are unclear or under embargo: the `--real` flag prints a polite "real demo not yet redistributable; using synthetic fallback" and downloads the default bundle instead.

**Decision required before v0.1.0 push** (now a §17 open item): redistribution rights for the optoCelsr FOV. Confirm with Hughes Lab PI before any real image leaves the local machine.

### README quickstart (synthetic-default path)

```bash
# Conda recommended (handles cellpose/torch reliably)
conda env create -f environment.yml && conda activate quantipy && pip install -e .
# Or pip if you already have a scientific Python env
# pip install git+https://github.com/mcleanT/QuantiPy-Polarity.git

quantipy download-demo
quantipy init-config --mode masks --output config.yaml
quantipy run --config config.yaml --output ./results
open ./results/report.html
```

## 13. Testing + CI

Two tiers — fast tier runs on every push; slow tier runs nightly.

**Fast tier (`ci.yml`, every push/PR):**
- Per-module tests: `test_io.py`, `test_polarity.py`, `test_front.py`, `test_viz.py`, `test_cli.py`, `test_config.py`, `test_report.py`.
- Integration test `test_e2e.py` runs `quantipy run` on the **pre-segmented synthetic mask + membrane fixture** (no Cellpose invocation). Verifies all output classes (maps, rose plots, parquet, migration overlays, HTML) and parses the report.
- Python 3.11 + 3.12, Ubuntu + macOS. Runs in <5 min.
- Cellpose / torch are installed but not exercised in this tier.

**Slow tier (`ci-nightly.yml`, cron + manual trigger):**
- `test_segment.py` runs Cellpose-SAM on the small synthetic fixture. Allowed to fail with `continue-on-error: true` and reported as a warning, not a blocking failure. Cellpose-SAM weights cached between runs.
- Full e2e with `quantipy run` starting from raw TIF (segment + polarity + plot + report).
- Tags failures in a GitHub issue rather than blocking releases.

**Rationale:** segmentation is the most fragile, slowest, and most environment-dependent part of the pipeline. Gating mainline CI on it is a recipe for green-when-the-tool-works / red-when-pytorch-rebased-or-cellpose-changed. The fast tier verifies *the QuantiPy pipeline's own correctness* on inputs it controls. The slow tier verifies *the segmentation integration* on a schedule where flake doesn't block work.

No GPU in CI. Local users with GPUs see expected behavior documented in `docs/concepts.md`.

## 14. Documentation

| File | Audience | Length target |
|---|---|---|
| `README.md` | First-time visitor | One scroll: install, quickstart, screenshot, citation |
| `docs/concepts.md` | New-to-QP biologist | Planar polarity primer; what boundary-PCA measures |
| `docs/pipeline.md` | Anyone running the tool | Stage diagram + data flow + per-stage rationale |
| `docs/cli-reference.md` | Power user | Every command, every flag (auto-generated from Click) |
| `docs/config-reference.md` | Anyone writing a config | Field-by-field reference, defaults, examples |
| `docs/outputs.md` | Anyone reading results | What every file means + parquet schema |
| `docs/interactive-viewer.md` | Debug viewer user | Screenshots, keybindings, workflows |
| `docs/migration-front.md` | Migration analyst | Algorithm provenance, tuning guide |
| `docs/validation.md` | Reviewer / sceptic | QP-vs-Python methodology, scatter, sample sizes, QP version |
| `docs/citing.md` | Citing user | BibTeX, CITATION.cff pointer, original QP paper link |

No mkdocs site for v0.1.0 — plain markdown on GitHub is sufficient. Revisit at v0.2.

## 15. Carve-out plan from `Hughes Lab/Sachin/Polarity Quantification/`

The existing dir is research-active. Plan must not break it.

1. **New repo lives at `Science/QuantiPy-Polarity/`** — sibling to `Hughes Lab/`, independent git repo.
2. **Copy + refactor, do not move.** Source dir stays intact. If something breaks during refactor, the original still runs.
3. **Refactor in batches via subagents** (per global CLAUDE.md mandate). Each subpackage = one subagent task: `io/`, `segment/`, `polarity/`, `migration/`, `viz/`, `report/`, `interactive/`, `analyses/`, `validation/`, plus CLI batch and tests batch.
4. **Strip optoCelsr-specific naming** as files move. Concretely: hard-coded `C10`/`D11` clone identifiers become user-supplied condition labels (read from config or directory names); `FOV_NN` stays as generic numbering; `Celsr1`/`optoCelsr` references in docstrings and variable names become "polarity marker" / "membrane channel"; magic channel indices (e.g., `img[..., 1]`) read from `input.channel_membrane` / `input.channel_segmentation`. Search for and remove every occurrence of `C10`, `D11`, `optoCelsr`, `Celsr1`, `Sachin`, `hPGK`, `pGK` outside of `examples/configs/celsr_optoclones.yaml` (which intentionally documents the original analysis).
5. **Tests must pass on new repo before pushing to GitHub.** Cut v0.1.0 tag once green. Upload demo + validation parquet to the Release.
6. **Original Hughes-Lab dir untouched.** Optionally later: one-line `README.md` there pointing to QuantiPy-Polarity. Not part of this plan.

### Public package becomes upstream for reusable algorithms

To prevent silent divergence between research-dir and public package on core algorithms (boundary-PCA, migration-front detection, axial statistics, rose rendering):

- Once v0.1.0 is cut, the research dir (`Hughes Lab/Sachin/Polarity Quantification/`) installs the public package as a dependency (`pip install -e ../../../QuantiPy-Polarity`) instead of evolving parallel copies of those algorithms.
- The research dir keeps its experiment-specific orchestration, paper-figure builders, and one-off analyses, but imports from `quantipy_polarity` for the validated core.
- Bug fixes to core algorithms land in QuantiPy-Polarity first, get a patch version (`v0.1.1`, `v0.2.0`), and the research dir bumps its dependency pin.
- This relationship is described in `docs/maintenance.md` in the public repo and in the research dir's CLAUDE.md.
- The fast tier of public CI is the gate for any algorithmic change that affects research output. No more "fixed in research dir but forgot to port to public" drift.

This is a discipline change, not v0.1.0 code work — it locks in at the moment v0.1.0 is tagged and the research dir bumps to import from it. Adding it to §17 as an open item to actually execute as part of the v0.1.0 release.

## 16. Module-level lift table

| New module | Lifted from | Notes |
|---|---|---|
| `io/nd2.py` | `01_nd2_to_tif.py` | Strip optoCelsr naming; channel indices from config |
| `io/tif.py` | new | Multi-page TIF ingest via `tifffile`; normalize to per-FOV TIFs |
| `io/masks.py` | new | User-supplied label masks (uint16); validate against membrane TIFs |
| `segment/cellpose.py` | `02_segment.py` | Wrap cellpose-SAM; pass model+diameter via config |
| `segment/postprocess.py` | `03b_fix_undersegmented.py` | Skeleton-based merged-cell splitter |
| `polarity/boundary_pca.py` | `04b_polarity_python.py` + `lib/qp/*` | Python QP reimplementation, generalized |
| `polarity/per_cell.py` | `05_aggregate.py` | Per-FOV → experiment parquet |
| `migration/front.py` | `recompute_migration_v3.py` + `compute_migration_field` | v6 real-bg classification, configurable erosion |
| `migration/tune.py` | new (informed by `audit_front_detection.py`) | Interactive front-param tuner |
| `migration/local.py` | `compute_48h_local_migration.py` | Per-cell local migration direction |
| `viz/style.py` | `Science/styles/figstyle.py` + lab figure-standards | Nature palette baked in; no external dep on Science/styles |
| `viz/polarity_map.py` | `plot_fov_polarity_panel.py` | Per-FOV vector overlay |
| `viz/rose.py` | `plot_rose_per_fov.py` + `plot_rose_pair_halfdisk.py` | Rose / half-disk plots |
| `viz/overlay.py` | `plot_fov_with_rose_localmig.py` | Combined FOV + rose + migration overlay |
| `report/html.py` | new (Jinja2) | Self-contained HTML; base64-inlined figures |
| `interactive/viewer.py` | `debug_polarity.py` | Matplotlib viewer; FOV dropdown, nav, click-cell inspection |
| `analyses/per_fov_rose.py` | `plot_rose_per_fov.py` | Rose plot grid |
| `analyses/polarity_heatmap.py` | `plot_continuous_polarity_heatmaps.py` | Continuous polarity heatmap |
| `analyses/ar_stratified_rose.py` | `plot_ar_stratified_rose.py` | AR-stratified rose plots |
| `analyses/axis_alignment.py` | `compare_axis_polarity_alignment.py` | Cell-axis vs polarity-axis alignment |
| `analyses/magnitude_vs_distance.py` | `plot_magnitude_vs_distance.py` | Magnitude vs distance to front |
| `analyses/polarization_decline.py` | `plot_polarization_decline.py` | Polarization vs depth band |
| `validation/linear_relationship.py` | `compute_core_values_py_vs_qp.py` + `compute_correlation_v2.py` | QP-vs-Python scatter, linear fit, R², 95% CI |

### Data contracts (per module)

Every module's inputs and outputs are fixed before refactor begins; downstream modules program against the contracts, not against upstream internals. Contracts live in `src/quantipy_polarity/contracts.py` (Pydantic models + typed dict aliases) and are imported wherever a module boundary is crossed.

**Coordinate / unit conventions (apply everywhere):**
- **Image arrays:** `numpy.ndarray`, shape `(H, W)` for single-channel or `(H, W, C)` for multi-channel; dtype `uint16` for raw, `uint8` for visualization. Origin `(0, 0)` at top-left (numpy convention).
- **Coordinates:** `(y, x)` pixels everywhere (numpy/scikit-image convention). Never `(x, y)`. Documented in `docs/concepts.md` as a known foot-gun for matplotlib mixing.
- **Scale:** `pixel_size_um` from config converts pixels → microns where physical units matter (vector length, area).
- **Angles:** **degrees**, range `[0, 180)` for axial polarity, `[0, 360)` for vector. Documented per-column in the parquet schema.
- **Cell IDs:** `uint16` label values matching the segmentation mask. `0` reserved for background. FOV-unique, not globally unique; the per_cell parquet keys on `(fov_id, cell_id)`.
- **FOV IDs:** strings (e.g., `"FOV_01"`); preserved from input filenames or generated by `io/` if not present.

**Per-module contracts (summary; full Pydantic schemas in `contracts.py`):**

| Module | Consumes | Emits |
|---|---|---|
| `io/nd2` / `io/tif` | path to raw input dir + `input.*` config | per-FOV normalized TIF `(H, W, C)` uint16 + FOV manifest JSON `[{fov_id, path, shape, channels}]` |
| `io/masks` | mask dir + membrane TIF dir + pairing rule | per-FOV `{fov_id, membrane_tif_path, mask_tif_path}`; validates mask `uint16` and dim-match |
| `segment/cellpose` | normalized TIFs + `segment.*` config | per-FOV label-mask TIF `(H, W)` uint16 + QC overlay PNG |
| `segment/postprocess` | label-mask TIFs | corrected label-mask TIFs + change-log JSON `{n_split, n_merged, n_filtered}` |
| `polarity/boundary_pca` | label masks + membrane channel | per-FOV parquet: `[fov_id, cell_id, centroid_y, centroid_x, area_px, axis_deg, magnitude, qc_flags]` |
| `polarity/per_cell` | per-FOV parquets | experiment parquet: same schema + `condition` (from config) |
| `migration/front` | label masks + FOV manifest + `migration.*` config | per-FOV: front_line geometry (GeoJSON), background-classification mask (uint8) |
| `migration/local` | per_cell parquet + front geometries | adds columns `[mig_dir_deg, mig_alignment, dist_to_front_um]` to per_cell parquet |
| `viz/polarity_map` | per_cell parquet + normalized TIFs | per-FOV PNG + PDF overlay |
| `viz/rose` | per_cell parquet (subset by FOV or aggregated) | rose / half-disk PDF |
| `viz/overlay` | per_cell parquet + front geometries + normalized TIFs | combined PNG + PDF |
| `report/html` | results dir | self-contained HTML (base64-inlined assets) |
| `interactive/viewer` | results dir (read-only) | (no outputs; UI only) |

**Stability promise:** the `per_cell.parquet` schema is the public stable API. Adding columns: minor version. Removing or renaming columns: major version. Other module boundaries may shift before v1.0.

## 17. Open items deferred to the implementation plan

These are intentionally not resolved here; the writing-plans pass will decide:

**Pre-push blockers (must resolve before v0.1.0 tag):**
- **Author name string** in `pyproject.toml` and `CITATION.cff` — currently `<full name TBD>`; needs user input.
- **Real-FOV redistribution rights** (§12) — confirm with Hughes Lab PI before any real `.nd2` is uploaded to a public Release. If unclear/embargoed, synthetic-only ships as v0.1.0.
- **Confirm tested upper bounds** in `pyproject.toml` (§11) — actually test the upper-bound values in CI before committing to them.

**v0.1.0 deferrals — confirmed (not blockers):**
- `quantipy front --interactive` parameter tuner — deferred to v0.2 (§8); v0.1.0 uses static QC overlays.
- PyPI publishing — deferred to v0.2.
- mkdocs documentation site — deferred to v0.2.
- Promotion of `experimental/analyses/` to stable API — gated on validation against ≥2 external datasets.

**Detail decisions for writing-plans:**
- Specific tolerance thresholds for `test_polarity.py`'s synthetic-recovery assertion.
- Whether `experimental/analyses/` exposes a Python plugin entry-point group, or stays internal-only.
- Whether `release.yml` is a manual trigger or fires on tag push.
- Exact contents of the de-identified TIF + mask demo bundle (which FOV, what stripping rules).
- Concrete `config_hash` algorithm for §7 resume semantics (canonical-YAML dump → SHA-256, or Pydantic-model JSON dump → SHA-256).
- Whether the research-dir → public-dir upstream migration (§15) happens as part of the v0.1.0 release or as a follow-up.

## 18. Acceptance criteria for v0.1.0 release

**Quickstart success (the headline promise):**
- Default README quickstart (conda env, `download-demo`, `init-config --mode masks`, `run`) completes successfully on a clean macOS or Ubuntu machine with conda installed — no GPU, no Cellpose execution required, no raw `.nd2`. Verified by a fresh-VM test before tagging.
- Resulting `results/report.html` opens in a browser and shows all four output classes: per-FOV polarity maps, rose plots, per-cell table summary, migration overlays.

**Optional install paths:**
- `pip install git+https://github.com/mcleanT/QuantiPy-Polarity.git` succeeds in a clean Python 3.11 environment that already has scientific Python deps. Documented as a secondary path.
- ND2 + Cellpose-SAM "full pipeline" demo (`download-demo --real`, `init-config --mode nd2`, `run`) succeeds on macOS or Ubuntu with the recommended conda env, **gated on real-FOV redistribution rights** (§17).

**Quality gates:**
- Fast-tier CI green on Python 3.11 + 3.12, Ubuntu + macOS (§13).
- Slow-tier CI (Cellpose) runs to completion on the nightly schedule; failures filed as issues but do not block tagging.
- `quantipy validate` produces a figure that matches `validation_figure_reference.pdf` within documented structural tolerance.
- `quantipy run --resume` correctly skips completed stages and re-executes interrupted ones (§7).

**Repo hygiene:**
- README does not require Claude Code; Developer Workflow section is below the fold.
- `docs/concepts.md` and `docs/validation.md` describe assumptions, limits, and what users can vs cannot verify.
- `CITATION.cff` includes author name (filled from §17 open item).
- `.claude/commands/quantipy-run.md` invocable as `/quantipy-run` from a Claude-Code session, but only documented under Developer Workflow.
