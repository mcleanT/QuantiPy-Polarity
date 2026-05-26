"""Phase 1 stubs for all subcommands not yet implemented.

Each stub registers a Click command that exits with code 2 and a clear
"not implemented in Phase 1" message pointing to the future phase.
This lets `quantipy --help` show the full surface area immediately while
keeping each phase's implementation scope bounded.
"""

from __future__ import annotations

import click

from quantipy_polarity.cli import main


_STUBS: dict[str, tuple[str, str]] = {
    # All Phase 7 stubs have been replaced by real implementations.
}


def _make_stub(name: str, short_help: str, phase: str) -> click.Command:
    @click.command(name, short_help=short_help)
    def _stub(**_: object) -> None:
        raise click.ClickException(
            f"`quantipy {name}` is not implemented in v0.1.0 Phase 1. "
            f"It will land in {phase}. "
            f"See docs/superpowers/plans/ for the phased roadmap."
        )

    return _stub


for _name, (_short, _phase) in _STUBS.items():
    main.add_command(_make_stub(_name, _short, _phase))
