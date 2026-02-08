"""CLI entry point for the Greeum Consolidator.

Usage:
    greeum-consolidator once [--max-pairs N] [--min-sim F]
    greeum-consolidator daemon [--interval S] [--batch-size N]
    greeum-consolidator status
    greeum-consolidator --db /path/to/memory.db once
    greeum-consolidator -v once
"""

from __future__ import annotations

import logging
import sys

import click

from .config import ConsolidatorConfig
from .loop import ConsolidationLoop
from .state import StateManager
from .db import ConsolidatorDB


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.option("--db", default=None, help="Path to memory.db")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, db: str | None, verbose: bool) -> None:
    """Greeum Consolidator — LLM-based judicial deliberation for memory associations."""
    _setup_logging(verbose)
    ctx.ensure_object(dict)

    config = ConsolidatorConfig.from_env()
    if db:
        config.db_path = db
    ctx.obj["config"] = config


@cli.command()
@click.option("--max-pairs", default=50, show_default=True, help="Maximum pairs to process")
@click.option("--min-sim", default=None, type=float, help="Minimum cosine similarity threshold")
@click.pass_context
def once(ctx: click.Context, max_pairs: int, min_sim: float | None) -> None:
    """Run a single consolidation batch."""
    config: ConsolidatorConfig = ctx.obj["config"]
    if min_sim is not None:
        config.min_cosine_similarity = min_sim

    loop = ConsolidationLoop(config)
    try:
        report = loop.run_once(max_pairs=max_pairs)
        click.echo(report.summary())
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    finally:
        loop.close()


@cli.command()
@click.option("--interval", default=None, type=int, help="Seconds between batches")
@click.option("--batch-size", default=None, type=int, help="Pairs per batch")
@click.pass_context
def daemon(ctx: click.Context, interval: int | None, batch_size: int | None) -> None:
    """Run as a daemon, processing batches at regular intervals."""
    config: ConsolidatorConfig = ctx.obj["config"]
    loop = ConsolidationLoop(config)
    try:
        loop.run_daemon(interval=interval, batch_size=batch_size)
    except KeyboardInterrupt:
        click.echo("\nShutdown requested")
    finally:
        loop.close()


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show consolidation statistics."""
    config: ConsolidatorConfig = ctx.obj["config"]
    db = ConsolidatorDB(config.db_path, config.busy_timeout_ms)
    state = StateManager(db)

    try:
        stats = state.get_stats()
        type_dist = state.get_type_distribution()
        avg_latency = state.get_average_latency()
        deferred = state.get_deferred_pairs()

        click.echo("=== Greeum Consolidator Status ===")
        click.echo(f"Database: {config.db_path}")
        click.echo(f"Model:    {config.model}")
        click.echo()
        click.echo("Verdicts:")
        click.echo(f"  Total:     {stats['total']}")
        click.echo(f"  Connected: {stats['connected']}")
        click.echo(f"  Rejected:  {stats['rejected']}")
        click.echo(f"  Deferred:  {stats['deferred']}")
        click.echo(f"  Errors:    {stats['error']}")

        if type_dist:
            click.echo()
            click.echo("Connection types:")
            for ctype, count in sorted(type_dist.items(), key=lambda x: -x[1]):
                click.echo(f"  {ctype}: {count}")

        if avg_latency is not None:
            click.echo()
            click.echo(f"Avg LLM latency: {avg_latency:.0f}ms")

        if deferred:
            click.echo()
            click.echo(f"Deferred pairs awaiting retry: {len(deferred)}")
    finally:
        db.close()


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
