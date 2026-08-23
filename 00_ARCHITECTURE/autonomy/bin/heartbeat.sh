#!/usr/bin/env bash
# heartbeat.sh <AGENT> <status> <detail...>
set -euo pipefail
S="${NIRMANA_REPO:?}/00_ARCHITECTURE/autonomy/state/HEARTBEAT.jsonl"
A="${1:?agent}"; ST="${2:?status}"; shift 2; D="${*:-}"
printf '{"ts":"%s","agent":"%s","status":"%s","detail":"%s"}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$A" "$ST" "${D//\"/\\\"}" >> "$S"
