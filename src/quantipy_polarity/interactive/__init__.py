"""Read-only per-cell viewer (Phase 7).

Public API:
    build_viewer(results_dir, output_path, *, fov=None) -> None
        Build a self-contained static HTML viewer from a quantipy results dir.
"""

from quantipy_polarity.interactive.build_viewer import build_viewer

__all__ = ["build_viewer"]
