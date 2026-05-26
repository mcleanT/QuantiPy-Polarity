"""Self-contained HTML report generation.

Public API:
    build_report(results_dir, output_html, *, cfg=None) -> None
"""

from quantipy_polarity.report.build import build_report

__all__ = ["build_report"]
