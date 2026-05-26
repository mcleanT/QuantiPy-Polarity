"""Tests for `quantipy init-config`."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity.config import Config, InputMasks, InputND2, InputTIF


@pytest.mark.parametrize(
    "mode,expected_cls",
    [("masks", InputMasks), ("nd2", InputND2), ("tif", InputTIF)],
)
def test_init_config_writes_valid_yaml(
    tmp_path: Path, mode: str, expected_cls: type
) -> None:
    runner = CliRunner()
    out = tmp_path / f"cfg_{mode}.yaml"
    result = runner.invoke(main, ["init-config", "--mode", mode, "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    cfg = Config.from_yaml(out)
    assert isinstance(cfg.input, expected_cls)


def test_init_config_refuses_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "cfg.yaml"
    out.write_text("placeholder")
    result = runner.invoke(
        main, ["init-config", "--mode", "masks", "--output", str(out)]
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_init_config_force_overwrites(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "cfg.yaml"
    out.write_text("placeholder")
    result = runner.invoke(
        main, ["init-config", "--mode", "masks", "--output", str(out), "--force"]
    )
    assert result.exit_code == 0
    cfg = Config.from_yaml(out)
    assert isinstance(cfg.input, InputMasks)


def test_init_config_rejects_invalid_mode() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["init-config", "--mode", "garbage", "--output", "x.yaml"]
    )
    assert result.exit_code != 0


def test_init_config_tif_includes_tif_scheme(tmp_path: Path) -> None:
    """TIF template must include tif_scheme and channel_suffix_template fields."""
    runner = CliRunner()
    out = tmp_path / "cfg_tif.yaml"
    result = runner.invoke(main, ["init-config", "--mode", "tif", "--output", str(out)])
    assert result.exit_code == 0, result.output
    yaml_text = out.read_text()
    assert "tif_scheme: stack" in yaml_text
    assert "channel_suffix_template:" in yaml_text
    # Ensure the config is still Pydantic-parseable
    cfg = Config.from_yaml(out)
    assert isinstance(cfg.input, InputTIF)
    assert cfg.input.tif_scheme == "stack"
    assert cfg.input.channel_suffix_template == "_ch{ch}"
