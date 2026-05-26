"""Stub command registry for quantipy subcommands not yet implemented.

``_STUBS`` is intentionally empty as of v0.1.0 — all Phase 1–7 subcommands
have been replaced by real implementations.  The module is retained because
``cli.py`` imports it as a side-effect import to register any future stubs;
the ``_make_stub`` helper and the registration loop remain in place so that
new stubs can be added here without touching ``cli.py``.
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
