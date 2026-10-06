#!/usr/bin/env bash
# Read-only production readback for the executor v1.1. Runs ONE SQL file inside a READ ONLY transaction through the read-only
# pgenv connection, or (with --migration) one fixed query on the applied-migrations ledger. Output: tab-separated rows.
# Never prints the connection. The SQL file must live under $KY_ROOT/run/ops/sql/ (resolved, no traversal).
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; SQL=""; MIG=""
while [ $# -gt 0 ]; do case "$1" in --sql-file|--sql_file) SQL="${2:-}"; shift 2;; --migration) MIG="${2:-}"; shift 2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; done
[ -f /Users/Dev/.config/pravaha/pgenv.sh ] || { echo "read-only connection settings are missing" >&2; exit 4; }
if [ -n "$MIG" ]; then
  [[ "$MIG" =~ ^[0-9A-Za-z_.-]{1,120}$ ]] || { echo "migration name has unsafe characters" >&2; exit 2; }
  source /Users/Dev/.config/pravaha/pgenv.sh
  exec psql -v ON_ERROR_STOP=1 -X -q -A -t -F $'\t' -c "BEGIN READ ONLY; SELECT filename, applied_at, sha256 FROM public._migrations_applied WHERE filename LIKE '${MIG}%' ORDER BY 1; COMMIT;"
fi
[ -n "$SQL" ] || { echo "sql_file (or migration) required" >&2; exit 2; }
case "$SQL" in /*) ;; *) SQL="$KY_ROOT/$SQL" ;; esac
REAL="$(cd "$(dirname "$SQL")" 2>/dev/null && pwd -P)/$(basename "$SQL")"
case "$REAL" in "$KY_ROOT"/run/ops/sql/*.sql) ;; *) echo "the SQL file must live under $KY_ROOT/run/ops/sql/" >&2; exit 2;; esac
[ -f "$REAL" ] || { echo "SQL file not found" >&2; exit 2; }
if grep -qiE '(^|[;[:space:](])(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|call|do)[[:space:]]' "$REAL"; then echo "the SQL file contains a write or procedural verb; refused" >&2; exit 3; fi
source /Users/Dev/.config/pravaha/pgenv.sh
psql -v ON_ERROR_STOP=1 -X -q -A -F $'\t' -c "BEGIN READ ONLY;" -f "$REAL" -c "COMMIT;"
