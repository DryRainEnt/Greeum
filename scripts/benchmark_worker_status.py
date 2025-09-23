#!/usr/bin/env python3
"""Benchmark readiness check for MCP worker and memory latency."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

DEFAULT_ENDPOINT = "http://127.0.0.1:8800/mcp"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8800


def call_worker(payload: Dict[str, Any], endpoint: str, timeout: float) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        if resp.status == 204:
            return {}
    message = json.loads(body)
    if "error" in message:
        raise RuntimeError(f"Worker error: {message['error']}")
    return message.get("result") or {}


def percentile(vals: List[float], pct: float) -> float:
    if not vals:
        return 0.0
    sorted_vals = sorted(vals)
    k = (len(sorted_vals) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def bench(endpoint: str, iterations: int, query: str, content: str, timeout: float) -> None:
    add_times: List[float] = []
    search_times: List[float] = []

    add_payload = {
        "jsonrpc": "2.0",
        "id": "add-1",
        "method": "tools/call",
        "params": {
            "name": "add_memory",
            "arguments": {"content": content, "importance": 0.5},
        },
    }
    search_payload = {
        "jsonrpc": "2.0",
        "id": "search-1",
        "method": "tools/call",
        "params": {
            "name": "search_memory",
            "arguments": {"query": query, "limit": 3},
        },
    }

    for i in range(iterations):
        start = time.perf_counter()
        call_worker(add_payload, endpoint, timeout)
        add_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        call_worker(search_payload, endpoint, timeout)
        search_times.append(time.perf_counter() - start)

    def report(label: str, times: List[float]) -> None:
        if not times:
            print(f"{label}: no data")
            return
        avg = statistics.mean(times)
        p95 = percentile(times, 0.95)
        print(f"{label}: avg={avg:.3f}s p95={p95:.3f}s runs={len(times)}")

    report("add", add_times)
    report("search", search_times)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark MCP worker add/search latency")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="HTTP MCP endpoint")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--query", default="Bench latency")
    parser.add_argument("--content", default="[Bench] worker latency test")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    try:
        bench(args.endpoint, args.iterations, args.query, args.content, args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        sys.exit(1)
