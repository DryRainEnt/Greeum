#!/usr/bin/env python3
"""Simple benchmarking utility for Greeum memory operations.

Runs `greeum memory add` and/or `greeum memory search` multiple times and reports
latency statistics (avg/p95). Designed for local regression checks before and
after tuning work.
"""
from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
import time
from typing import Iterable, List, Tuple

import os

DEFAULT_ADD_TEXT = "[Bench] quick brown fox jumps over the lazy dog"
DEFAULT_SEARCH_QUERY = "quick brown fox"


class BenchmarkError(RuntimeError):
    pass


def run_command(args: List[str], env) -> float:
    start = time.perf_counter()
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
    duration = time.perf_counter() - start
    if proc.returncode != 0:
        raise BenchmarkError(
            f"Command failed ({proc.returncode}): {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return duration


def percentile(values: Iterable[float], pct: float) -> float:
    sorted_vals = sorted(values)
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def build_env(args) -> dict:
    env = dict(**os.environ)
    if args.data_dir:
        env["GREEUM_DATA_DIR"] = args.data_dir
    if args.semantic:
        env.pop("GREEUM_DISABLE_ST", None)
    else:
        env["GREEUM_DISABLE_ST"] = "1"
    if args.worker_endpoint:
        env["GREEUM_MCP_HTTP"] = args.worker_endpoint
        env["GREEUM_USE_WORKER"] = "1"
    elif args.force_worker:
        env["GREEUM_USE_WORKER"] = "1"
    if args.no_worker:
        env["GREEUM_USE_WORKER"] = "0"
        env.pop("GREEUM_MCP_HTTP", None)
    return env


def benchmark(label: str, cmd: List[str], iterations: int, env) -> Tuple[List[float], str]:
    durations: List[float] = []
    fail_note = ""
    for i in range(iterations):
        try:
            durations.append(run_command(cmd, env))
        except BenchmarkError as exc:
            fail_note = str(exc)
            break
    return durations, fail_note


def display_result(label: str, durations: List[float], note: str) -> None:
    if not durations:
        print(f"{label}: no runs (failed)\n{note}", file=sys.stderr)
        return
    avg = statistics.mean(durations)
    p95 = percentile(durations, 0.95)
    print(f"{label}: avg={avg:.3f}s p95={p95:.3f}s runs={len(durations)}")
    if note:
        print(note, file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark greeum memory add/search operations")
    parser.add_argument("--data-dir", help="Override GREEUM_DATA_DIR for benchmark runs")
    parser.add_argument("--iterations", type=int, default=5, help="Number of repetitions per command")
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Enable semantic embeddings during benchmark (default hash fallback)",
    )
    parser.add_argument(
        "--add-text",
        default=DEFAULT_ADD_TEXT,
        help="Text used for memory add benchmark",
    )
    parser.add_argument(
        "--search-query",
        default=DEFAULT_SEARCH_QUERY,
        help="Query used for memory search benchmark",
    )
    parser.add_argument(
        "--skip-add",
        action="store_true",
        help="Skip the add benchmark and only run search",
    )
    parser.add_argument(
        "--skip-search",
        action="store_true",
        help="Skip the search benchmark and only run add",
    )
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Run greeum mcp warmup for the selected mode before benchmarking",
    )
    parser.add_argument(
        "--worker-endpoint",
        help="HTTP worker endpoint (e.g., http://127.0.0.1:8800/mcp). Enables worker mode automatically.",
    )
    parser.add_argument(
        "--force-worker",
        action="store_true",
        help="Force worker usage even if the endpoint relies on environment variables.",
    )
    parser.add_argument(
        "--no-worker",
        action="store_true",
        help="Disable worker usage even if environment variables are set.",
    )

    args = parser.parse_args()

    env = build_env(args)

    if args.warmup:
        try:
            warm_cmd = [
                "greeum",
                "mcp",
                "warmup",
                "--model",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            ]
            run_command(warm_cmd, env)
            print("Warmup complete.")
        except BenchmarkError as exc:
            print(f"Warmup failed: {exc}", file=sys.stderr)

    if not args.skip_add:
        add_cmd = [
            "greeum",
            "memory",
            "add",
            args.add_text,
            "--importance",
            "0.5",
        ]
        add_times, note = benchmark("add", add_cmd, args.iterations, env)
        display_result("add", add_times, note)

    if not args.skip_search:
        search_cmd = [
            "greeum",
            "memory",
            "search",
            args.search_query,
            "--count",
            "3",
        ]
        search_times, note = benchmark("search", search_cmd, args.iterations, env)
        display_result("search", search_times, note)
