"""Entry points for the search → work → add workflow."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Dict, List

import click

GREEUM_BIN = os.environ.get("GREEUM_CLI_BIN", "greeum")
DEFAULT_PROTOCOL = "2024-11-10"


def _run_cli(args: List[str]) -> int:
    proc = subprocess.run([GREEUM_BIN, *args], check=False)
    return proc.returncode


def _call_mcp(payload: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    cmd = [GREEUM_BIN, "mcp", "serve", "-t", "stdio"]
    env = os.environ.copy()
    env.setdefault("GREEUM_QUIET", "true")
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    env.setdefault("GREEUM_DISABLE_ST", "1")

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    requests = [
        {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": DEFAULT_PROTOCOL,
                "clientInfo": {"name": "workflow-cli", "version": "1.0"},
                "capabilities": {},
            },
        },
        payload,
    ]

    input_blob = "\n".join(json.dumps(req) for req in requests) + "\n"

    try:
        stdout, stderr = proc.communicate(input_blob, timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise click.ClickException("MCP call timed out; ensure greeum server is reachable.")

    if proc.returncode not in (0, None):
        detail = (stderr or "").strip()
        message = f"MCP call failed (exit {proc.returncode})"
        if detail:
            message = f"{message}: {detail}"
        raise click.ClickException(message)

    responses: Dict[str, Dict[str, object]] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        responses[str(data.get("id", ""))] = data

    return responses


@click.group()
def workflow() -> None:
    """Greeum workflow helper."""


@workflow.command()
@click.argument("query")
@click.option("--limit", default=5, show_default=True, help="Number of results to display")
def search(query: str, limit: int) -> None:
    responses = _call_mcp(
        {
            "jsonrpc": "2.0",
            "id": "search",
            "method": "tools/call",
            "params": {"name": "search_memory", "arguments": {"query": query, "limit": limit}},
        }
    )
    result = responses.get("search", {}).get("result", {})
    for item in result.get("content", []):
        if item.get("type") == "text":
            click.echo(item["text"])


@workflow.command()
@click.argument("importance", type=float)
@click.argument("content", nargs=-1)
def add(importance: float, content: List[str]) -> None:
    if not content:
        click.echo("Provide memory text after the importance score.", err=True)
        sys.exit(1)
    text = " ".join(content)
    code = _run_cli(["memory", "add", "--importance", str(importance), text])
    if code != 0:
        sys.exit(code)


@workflow.command()
@click.option("--limit", default=5, show_default=True, help="Show latest memories")
def recap(limit: int) -> None:
    code = _run_cli(["memory", "search", "*", "-c", str(limit)])
    if code != 0:
        sys.exit(code)


@workflow.command()
def stats() -> None:
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
            click.echo(item["text"])


if __name__ == "__main__":
    workflow()
