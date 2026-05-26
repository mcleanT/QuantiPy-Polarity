"""Tests for the Phase 1 stub subcommands."""
import pytest
from click.testing import CliRunner

from quantipy_polarity.cli import main
from quantipy_polarity._stubs import _STUBS


@pytest.mark.parametrize("cmd_name", list(_STUBS.keys()))
def test_stub_exits_nonzero_with_phase_message(cmd_name: str) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [cmd_name])
    assert result.exit_code != 0, f"{cmd_name} should exit non-zero in Phase 1"
    assert "not implemented in v0.1.0 Phase 1" in result.output


@pytest.mark.parametrize("cmd_name", list(_STUBS.keys()))
def test_stub_help_works(cmd_name: str) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [cmd_name, "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_all_stubs_have_phase_pointers() -> None:
    for cmd_name, (_short, phase) in _STUBS.items():
        assert "Phase" in phase, f"{cmd_name} stub missing phase pointer"
