"""Generate a Greeum daily digest (stdout or webhook)."""

from __future__ import annotations

import os
from typing import List

import click
import requests

from greeum.core.database_manager import DatabaseManager

DEFAULT_TITLE = "Greeum Daily Digest"
DEFAULT_DB = os.environ.get("GREEUM_MEMORY_DB", os.path.join(os.getcwd(), "data", "memory.db"))


def _list_recent(limit: int) -> List[dict]:
    db = DatabaseManager(DEFAULT_DB)
    return db.get_blocks(limit=limit)


def _format_recent(limit: int) -> str:
    blocks = _list_recent(limit)
    if not blocks:
        return "(No recent memories)"

    lines = []
    for idx, block in enumerate(blocks, start=1):
        ts = block.get("timestamp", "unknown")
        slot = block.get("slot") or "?"
        context = (block.get("context") or "").replace("\n", " ")
        lines.append(f"{idx}. [{ts}] (Slot {slot}) {context}")
    return "\n".join(lines)


def _fetch_stats() -> str:
    # Reuse the workflow CLI helper via environment for simplicity.
    from .workflow import _call_mcp

    responses = _call_mcp(
        {
            "jsonrpc": "2.0",
            "id": "stats",
            "method": "tools/call",
            "params": {"name": "get_memory_stats", "arguments": {}},
        }
    )
    result = responses.get("stats", {}).get("result", {})
    for item in result.get("content", []):
        if item.get("type") == "text":
            return item["text"]
    return "(No statistics available)"


@click.command()
@click.option("--limit", default=10, show_default=True, help="Number of recent memories to include")
@click.option("--title", default=DEFAULT_TITLE, show_default=True)
@click.option("--webhook", envvar="GREEUM_SLACK_WEBHOOK", help="Slack/Discord webhook URL")
def digest(limit: int, title: str, webhook: str | None) -> None:
    """Generate a daily digest; send to webhook if provided."""
    stats = _fetch_stats()
    recent = _format_recent(limit)

    body = f"{title}\n----------------------------\n{stats}\n\nRecent entries (latest {limit}):\n{recent}\n"

    if webhook:
        try:
            response = requests.post(webhook, json={"text": body}, timeout=10)
            if response.status_code >= 400:
                click.echo(f"Webhook error: {response.status_code} {response.text}", err=True)
        except requests.RequestException as exc:
            click.echo(f"Webhook request failed: {exc}", err=True)
            raise SystemExit(1)
    else:
        click.echo(body)


if __name__ == "__main__":
    digest()
