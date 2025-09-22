#!/usr/bin/env bash
LOG_FILE=${GREEUM_CODEX_LOG:-/tmp/greeum_codex_stdio.log}
{
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "===================="
  echo "[$ts] launching greeum $@"
  export PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}
  export GREEUM_QUIET=${GREEUM_QUIET:-true}
  /Users/dryrain/.local/pipx/venvs/greeum/bin/greeum "$@"
  status=$?
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] exited with $status"
  exit $status
} >> "$LOG_FILE" 2>&1
