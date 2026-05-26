"""QuantiPy Polarity — single-shot planar polarity quantification.

Public Python API surface is intentionally small in v0.1.0; the CLI is the
documented entry point. Library callers may import from the named submodules
(quantipy_polarity.polarity, .migration, .viz, etc.) at their own risk —
API stability promised only for the per_cell.parquet schema (see contracts.py).
"""
from quantipy_polarity._version import __version__

__all__ = ["__version__"]
