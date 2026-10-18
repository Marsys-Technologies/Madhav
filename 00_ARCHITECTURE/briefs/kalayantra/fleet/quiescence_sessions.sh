#!/usr/bin/env bash
# Read-only session measurement for the executor's `quiescence_check` kind (A7 D-44). It MEASURES; it judges nothing.
# One fixed, parameterised query on pg_stat_activity: the live sessions whose application_name is the marker the executor gave
# the operation's child process (PGAPPNAME=ky-op-<sha256(operation_id)[:16]>; libpq applies it to every connection the child opens
# that does not name its own application_name). Same connection discipline as readback_sql.sh: driver (no psql client), read-only
# session, connection settings from the read-only environment file only; neither privileged connection variable reaches this process.
# Output: ONE line, a `ky.session_readback/1` JSON record (measured_at is this host's UTC clock, the one the receipts use). `sees_all_sessions` is measured, not assumed: without pg_read_all_stats
# (or superuser) PostgreSQL hides other roles' sessions, and an empty list would then prove nothing.
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; OPERATION=""
while [ $# -gt 0 ]; do case "$1" in --operation) OPERATION="${2:-}"; shift 2;; --execution_readback|--execution-readback) shift 2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; done
[[ "$OPERATION" =~ ^[A-Za-z0-9_.-]{1,80}$ ]] || { echo "operation (a safe operation id) required" >&2; exit 2; }
unset DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL
PGENV="${KY_READBACK_PGENV:-/Users/Dev/.config/pravaha/pgenv.sh}"     # the override exists for tests; the executor's child environment never carries it
[ -f "$PGENV" ] || { echo "read-only connection settings are missing" >&2; exit 4; }
source "$PGENV"
unset PGAPPNAME                                                       # this process's own session must never carry an operation marker
exec "$KY_ROOT/venv/bin/python" - "$OPERATION" <<'KYPY'
import datetime as dt, hashlib, json, sys
import psycopg

operation = sys.argv[1]
marker = "ky-op-" + hashlib.sha256(operation.encode()).hexdigest()[:16]
with psycopg.connect("", application_name="ky-quiescence-readback") as conn:       # connection settings come from the read-only environment file only
    conn.read_only = True
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), pg_has_role(current_user, 'pg_read_all_stats', 'USAGE') "
                    "OR COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname = current_user), false)")
        database, sees_all = cur.fetchone()
        cur.execute("SELECT pid, state, backend_start::text FROM pg_stat_activity "
                    "WHERE application_name = %s AND pid <> pg_backend_pid() ORDER BY pid", (marker,), prepare=True)
        sessions = [{"pid": pid, "state": state, "backend_start": started} for pid, state, started in cur]
print(json.dumps({"schema": "ky.session_readback/1", "status": "MEASURED", "marker": marker, "database": database,
                  "sees_all_sessions": bool(sees_all), "sessions": sessions,
                  "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}, sort_keys=True, separators=(",", ":")), flush=True)
KYPY
