"""Tests for the Jinja2 HTML report template."""

from pathlib import Path
from types import SimpleNamespace

import jinja2


TEMPLATE_PATH = Path("src/quantipy_polarity/report/templates/report.html.j2")


def _default_ctx(**overrides):
    """Return a minimal valid template context, merged with *overrides*."""
    ctx = dict(
        project_name="",
        results_dir="",
        now="2026-01-01",
        n_fovs=0,
        n_cells=0,
        median_magnitude=None,
        stage_statuses={},
        fov_rows=[],
        has_rose=False,
        aggregate_rose_b64=None,
        has_summary=False,
        population_summary_b64=None,
        config_yaml="",
        thumbnail_max_px=256,
    )
    ctx.update(overrides)
    return ctx


def _render(**overrides) -> str:
    """Load the template from disk and render with the given context."""
    loader = jinja2.FileSystemLoader(str(TEMPLATE_PATH.parent))
    env = jinja2.Environment(loader=loader, autoescape=False)
    template = env.get_template(TEMPLATE_PATH.name)
    return template.render(**_default_ctx(**overrides))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_template_renders_project_name():
    """Rendered HTML should contain the project name."""
    html = _render(project_name="My Exp")
    assert "My Exp" in html


def test_template_renders_stage_statuses():
    """Stage names and badge CSS classes should both appear in the output."""
    html = _render(stage_statuses={"ingest": "done", "segment": "failed"})
    assert "ingest" in html
    assert "segment" in html
    assert "badge-done" in html
    assert "badge-failed" in html


def test_template_renders_fov_row():
    """An fov_rows entry with vector_b64 should produce an <img src= tag."""
    fov = SimpleNamespace(
        fov_id="FOV_01",
        vector_b64="data:image/png;base64,abc",
        rose_b64=None,
        n_cells=10,
    )
    html = _render(fov_rows=[fov])
    assert '<img src="data:image/png;base64,abc"' in html


def test_template_no_http_refs():
    """Rendered output with empty data must not reference any external URLs."""
    html = _render()
    assert "http://" not in html
    assert "https://" not in html


def test_template_config_yaml_in_details():
    """config_yaml value should appear inside a <pre> block."""
    html = _render(config_yaml="k: v")
    assert "k: v" in html
    # Confirm it lands inside a <pre> element
    pre_start = html.index("<pre>")
    pre_end = html.index("</pre>")
    pre_content = html[pre_start:pre_end]
    assert "k: v" in pre_content
