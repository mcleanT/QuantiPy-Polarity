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
