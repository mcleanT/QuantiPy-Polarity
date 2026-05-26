"""QP-vs-Python validation subpackage.

Public API (stable in v0.1.0):
  run_validation  — load paired parquets, match cells, compute metrics, write figures.
  ValidationResult — dataclass holding r2_magnitude, slope_magnitude,
                     r2_angle, slope_angle, n_matched.
"""

try:
    from quantipy_polarity.validation.qp_vs_python import (
        ValidationResult,
        run_validation,
    )
except ImportError:
    pass

__all__ = ["ValidationResult", "run_validation"]
