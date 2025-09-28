"""Compatibility shim for the modern CLI defined in greeum.cli.__init__."""

import sys

import click

from .cli.__init__ import main as _cli_main


def main() -> None:
    try:
        _cli_main.main(args=sys.argv[1:], prog_name="greeum", standalone_mode=False)
    except SystemExit as exc:  # pragma: no cover - delegate to CLI exit handling
        ctx_exc = getattr(exc, "__context__", None)
        if (
            exc.code == 2
            and isinstance(ctx_exc, click.exceptions.MissingParameter)
            and getattr(getattr(ctx_exc, "param", None), "name", None) == "content"
        ):
            sys.exit(0)
        raise


if __name__ == "__main__":
    main()
