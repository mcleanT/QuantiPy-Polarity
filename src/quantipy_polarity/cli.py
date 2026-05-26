"""quantipy CLI root.

Two command groups visible in --help:
  Primary commands (documented in README quickstart): init-config, download-demo,
    run, debug, validate
  Advanced commands (for stage-resume / debugging): ingest, segment, polarity,
    front, aggregate, plot, report, analyze
"""

from __future__ import annotations

import click

from quantipy_polarity import __version__


class _GroupedHelp(click.Group):
    """Click Group subclass that prints commands under Primary / Advanced headers."""

    PRIMARY: tuple[str, ...] = (
        "init-config",
        "download-demo",
        "run",
        "debug",
        "validate",
    )

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        commands = []
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            commands.append((name, cmd))
        primary = [(n, c) for n, c in commands if n in self.PRIMARY]
        advanced = [(n, c) for n, c in commands if n not in self.PRIMARY]
        for label, rows in (
            ("Primary commands", primary),
            ("Advanced commands", advanced),
        ):
            if not rows:
                continue
            with formatter.section(label):
                formatter.write_dl(
                    [(n, (c.get_short_help_str(limit=80) or "")) for n, c in rows]
                )


@click.group(cls=_GroupedHelp, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="quantipy")
def main() -> None:
    """QuantiPy Polarity — planar polarity quantification from microscopy images."""


# Subcommand modules register themselves on import.
from quantipy_polarity import _stubs as _stubs  # noqa: E402,F401
from quantipy_polarity import _cli_init_config as _cli_init_config  # noqa: E402,F401
from quantipy_polarity import _cli_polarity as _cli_polarity  # noqa: E402,F401
from quantipy_polarity import _cli_segment as _cli_segment  # noqa: E402,F401
from quantipy_polarity import _cli_front as _cli_front  # noqa: E402,F401
from quantipy_polarity import _cli_figures as _cli_figures  # noqa: E402,F401
from quantipy_polarity import _cli_ingest as _cli_ingest  # noqa: E402,F401
from quantipy_polarity import _cli_run as _cli_run  # noqa: E402,F401
from quantipy_polarity import _cli_report as _cli_report  # noqa: E402,F401
from quantipy_polarity import _cli_validate as _cli_validate          # noqa: E402,F401
from quantipy_polarity import _cli_download_demo as _cli_download_demo  # noqa: E402,F401
