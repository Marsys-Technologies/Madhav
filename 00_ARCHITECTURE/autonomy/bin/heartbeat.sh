#!/usr/bin/env bash
# heartbeat.sh <AGENT> <status> <detail...>
set -euo pipefail
# Default the repo root from this script's own location so a heartbeat works from any
# working directory and from a fresh profile shell that never saw the pane env (D-1).
# NIRMANA_REPO remains an override, not a requirement.
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
S="${NIRMANA_REPO:-$_here}/00_ARCHITECTURE/autonomy/state/HEARTBEAT.jsonl"
A="${1:?agent}"; ST="${2:?status}"; shift 2; D="${*:-}"
printf '{"ts":"%s","agent":"%s","status":"%s","detail":"%s"}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$A" "$ST" "${D//\"/\\\"}" >> "$S"
