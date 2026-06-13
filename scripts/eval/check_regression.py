#!/usr/bin/env python3
"""Compare an eval result JSON against a baseline JSON via policy.yml.

Exit codes:
  0  all metrics within tolerance
  1  hard_fail violation (one or more)
  2  invalid arguments
  3  policy.yml or baseline missing

Usage:
  python scripts/eval/check_regression.py \
      --result docs/eval/results/internal_<run>.json \
      --baseline docs/eval/baseline_internal_2026-06-14.json \
      --policy scripts/eval/policy.yml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Lightweight YAML parser sufficient for our policy.yml shape; avoids needing
# pyyaml in CI base envs.
import re


def _parse_policy_yaml(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, out)]
    current_list_key = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        # Pop deeper frames
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- "):
            item_body = stripped[2:].strip()
            # List items are dicts: '- name: "x"'
            d: Dict[str, Any] = {}
            if isinstance(parent, list):
                parent.append(d)
            elif current_list_key is not None and isinstance(parent, dict):
                lst = parent.setdefault(current_list_key, [])
                lst.append(d)
            # parse the first key on same line
            if ":" in item_body:
                k, v = item_body.split(":", 1)
                d[k.strip()] = _coerce(v.strip())
            stack.append((indent + 2, d))
            continue
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v == "":
                # Nested block — could be dict or list
                child: Dict[str, Any] = {}
                if isinstance(parent, dict):
                    parent[k] = child
                stack.append((indent, child))
                current_list_key = k
            else:
                val = _coerce(v)
                if isinstance(parent, dict):
                    parent[k] = val
    return out


def _coerce(v: str) -> Any:
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1]
    if v in ("true", "True"): return True
    if v in ("false", "False"): return False
    if re.match(r"^-?\d+$", v):
        return int(v)
    if re.match(r"^-?\d+\.\d+([eE][-+]?\d+)?$", v):
        return float(v)
    return v


# ---------------------------------------------------------------------------
# Metric lookup against the JSON shape produced by internal_bench.py

_METRIC_PATHS = {
    "internal.embedding.recall@5":      ("quality", "embedding_only", "recall@5"),
    "internal.embedding.recall@10":     ("quality", "embedding_only", "recall@10"),
    "internal.embedding.mrr":           ("quality", "embedding_only", "mrr"),
    "internal.embedding.pair_auc":      ("quality", "embedding_only", "pair_auc"),
    "internal.hybrid.recall@5":         ("quality", "hybrid_production", "recall@5"),
    "internal.hybrid.recall@10":        ("quality", "hybrid_production", "recall@10"),
    "internal.hybrid.mrr":              ("quality", "hybrid_production", "mrr"),
    "search.latency.p50_ms":            ("latency", "search_latency_ms", "p50"),
    "search.latency.p95_ms":            ("latency", "search_latency_ms", "p95"),
    "ingest.latency.p95_ms":            ("latency", "ingest_latency_ms", "p95"),
}


def _get(d: Dict[str, Any], path) -> Any:
    for k in path:
        if d is None: return None
        d = d.get(k) if isinstance(d, dict) else None
    return d


def _format_violations(rows):
    if not rows:
        return ""
    out = "\n"
    for r in rows:
        out += f"  {r['level']:5} {r['metric']:35} "
        out += f"baseline={r['baseline']} current={r['current']} "
        out += f"({r['direction']}, margin={r['margin']})\n"
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--policy", default="scripts/eval/policy.yml")
    args = p.parse_args()

    for path in (args.result, args.baseline, args.policy):
        if not Path(path).exists():
            print(f"missing: {path}", file=sys.stderr)
            return 3

    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    policy = _parse_policy_yaml(Path(args.policy).read_text(encoding="utf-8"))

    violations: List[Dict[str, Any]] = []

    for group, entries in (policy.get("metrics") or {}).items():
        if not isinstance(entries, list):
            continue
        for spec in entries:
            name = spec.get("name", "")
            path = _METRIC_PATHS.get(name)
            if path is None:
                continue
            direction = spec.get("direction", "max")
            b = _get(baseline, path)
            c = _get(result, path)
            if b is None or c is None:
                continue
            try:
                b_f = float(b); c_f = float(c)
            except (TypeError, ValueError):
                continue

            hf_margin = spec.get("hard_fail_margin")
            warn_margin = spec.get("warn_margin")

            if direction == "max":
                if hf_margin is not None and c_f < b_f * (1.0 - hf_margin):
                    violations.append({"level": "FAIL", "metric": name, "baseline": b, "current": c,
                                       "direction": direction, "margin": hf_margin})
                elif warn_margin is not None and c_f < b_f * (1.0 - warn_margin):
                    violations.append({"level": "WARN", "metric": name, "baseline": b, "current": c,
                                       "direction": direction, "margin": warn_margin})
            elif direction == "min":
                if hf_margin is not None and c_f > b_f * (1.0 + hf_margin):
                    violations.append({"level": "FAIL", "metric": name, "baseline": b, "current": c,
                                       "direction": direction, "margin": hf_margin})
                elif warn_margin is not None and c_f > b_f * (1.0 + warn_margin):
                    violations.append({"level": "WARN", "metric": name, "baseline": b, "current": c,
                                       "direction": direction, "margin": warn_margin})

    fails = [v for v in violations if v["level"] == "FAIL"]
    warns = [v for v in violations if v["level"] == "WARN"]

    if fails:
        print(f"REGRESSION: {len(fails)} hard-fail metrics:{_format_violations(fails)}")
    if warns:
        print(f"WARNING: {len(warns)} metrics in warn band:{_format_violations(warns)}")
    if not fails and not warns:
        print("OK — no regression detected.")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
