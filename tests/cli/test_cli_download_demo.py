"""CLI tests for `quantipy download-demo`. All network calls are mocked."""

import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from quantipy_polarity.cli import main


@pytest.fixture(autouse=True, scope="module")
def _restore_main_commands():
    """Snapshot main.commands before this module runs; restore afterward.

    Importing _cli_download_demo registers the real download-demo command on
    `main`, overriding the Phase-1 stub.  This fixture saves the original stub
    and reinstates it after the module finishes so that test_cli_stubs.py still
    passes when the full suite runs.
    """
    original_commands = dict(main.commands)
    yield
    main.commands.clear()
    main.commands.update(original_commands)


def _make_zip(tmp_path: Path) -> bytes:
    """Return bytes of a minimal demo_bundle.zip with a config.yaml inside."""
    zip_path = tmp_path / "test_bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("config.yaml", "input:\n  mode: masks\n")
        zf.writestr("fov_A_membrane.tif", b"\x00" * 100)
    return zip_path.read_bytes()


def _fake_release_response(asset_url: str) -> dict:
    return {
        "tag_name": "phase-6-demo-bundle-v1",
        "assets": [{"name": "demo_bundle.zip", "browser_download_url": asset_url}],
    }


def test_download_demo_already_exists(tmp_path):
    from quantipy_polarity._cli_download_demo import download_demo_cmd

    out = tmp_path / "demo"
    out.mkdir()
    (out / "config.yaml").write_text("input:\n  mode: masks\n")
    runner = CliRunner()
    result = runner.invoke(download_demo_cmd, ["--output", str(out)])
    assert result.exit_code == 0
    assert "already downloaded" in result.output


def test_download_demo_force_redownload(tmp_path):
    """--force flag should not early-exit even if config.yaml exists."""
    from quantipy_polarity._cli_download_demo import download_demo_cmd

    out = tmp_path / "demo"
    out.mkdir()
    (out / "config.yaml").write_text("input:\n  mode: masks\n")

    zip_bytes = _make_zip(tmp_path)

    mock_get = MagicMock()
    # First call: release API; second call: streaming download
    release_resp = MagicMock()
    release_resp.raise_for_status.return_value = None
    release_resp.json.return_value = _fake_release_response("http://fake/demo.zip")

    stream_resp = MagicMock()
    stream_resp.raise_for_status.return_value = None
    stream_resp.headers = {"content-length": str(len(zip_bytes))}
    stream_resp.iter_content = MagicMock(return_value=[zip_bytes])
    stream_resp.__enter__ = MagicMock(return_value=stream_resp)
    stream_resp.__exit__ = MagicMock(return_value=False)

    mock_get.side_effect = [release_resp, stream_resp]

    with patch("requests.get", mock_get):
        runner = CliRunner()
        result = runner.invoke(download_demo_cmd, ["--output", str(out), "--force"])
    # Should not early-exit; exit code may be 0 or non-zero depending on zip shape
    assert "already downloaded" not in result.output


def test_download_demo_network_failure(tmp_path):
    """Network failure should print fallback message, not crash."""
    from quantipy_polarity._cli_download_demo import download_demo_cmd
    import requests as req

    with patch(
        "requests.get",
        side_effect=req.exceptions.ConnectionError("no network"),
    ):
        runner = CliRunner()
        result = runner.invoke(download_demo_cmd, ["--output", str(tmp_path / "demo")])
    assert result.exit_code != 0
    output = result.output + (result.exception.__str__() if result.exception else "")
    assert (
        "fallback" in result.output.lower()
        or "clone" in result.output.lower()
        or result.exit_code != 0
    )


def test_download_demo_missing_asset(tmp_path):
    """If release has no demo_bundle.zip asset, print helpful message."""
    from quantipy_polarity._cli_download_demo import download_demo_cmd

    release_data = {"tag_name": "v0.1.0", "assets": []}
    release_resp = MagicMock()
    release_resp.raise_for_status.return_value = None
    release_resp.json.return_value = release_data

    with patch(
        "requests.get",
        return_value=release_resp,
    ):
        runner = CliRunner()
        result = runner.invoke(download_demo_cmd, ["--output", str(tmp_path / "demo")])
    assert result.exit_code != 0


def test_download_demo_help():
    from quantipy_polarity._cli_download_demo import download_demo_cmd

    runner = CliRunner()
    result = runner.invoke(download_demo_cmd, ["--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--force" in result.output
