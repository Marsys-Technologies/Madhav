#!/usr/bin/env bash
# Read-only production readback for the executor v1.2. ONE SELECT/WITH statement from a file under $KY_ROOT/run/ops/sql/
# (fully resolved: a symlink that leaves the folder is refused), or — with --migration — one fixed, parameterised query on the
# applied-migrations ledger. It talks to the database through a driver, never through the psql client, so no client command
# (\!, \i, \connect, \copy, \o) exists to be abused; the extended-query protocol refuses multiple statements; the session is
# read-only. Neither privileged connection variable reaches this process. Output: tab-separated rows with a header line.
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; SQL=""; MIG=""
while [ $# -gt 0 ]; do case "$1" in --sql-file|--sql_file) SQL="${2:-}"; shift 2;; --migration) MIG="${2:-}"; shift 2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; done
[ -n "$SQL" ] || [ -n "$MIG" ] || { echo "sql_file or migration required" >&2; exit 2; }
if [ -n "$MIG" ]; then [[ "$MIG" =~ ^[0-9A-Za-z_.-]{1,120}$ ]] || { echo "migration name has unsafe characters" >&2; exit 2; }; fi
unset DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL
PGENV="${KY_READBACK_PGENV:-/Users/Dev/.config/pravaha/pgenv.sh}"     # the override exists for tests; the executor's child environment never carries it
[ -f "$PGENV" ] || { echo "read-only connection settings are missing" >&2; exit 4; }
source "$PGENV"
exec "$KY_ROOT/venv/bin/python" - "$KY_ROOT" "$SQL" "$MIG" <<'KYPY'
import csv, pathlib, re, sys
import psycopg

root = pathlib.Path(sys.argv[1]).resolve(); sql_arg, mig = sys.argv[2], sys.argv[3]
params = None
if mig:
    sql = "SELECT filename, applied_at, sha256 FROM public._migrations_applied WHERE filename LIKE %s ORDER BY 1"; params = (mig + "%",)
else:
    base = (root / "run/ops/sql").resolve(strict=True)
    path = pathlib.Path(sql_arg)
    if not path.is_absolute(): path = root / path
    try: path = path.resolve(strict=True)
    except FileNotFoundError: raise SystemExit("SQL file not found")
    if not path.is_relative_to(base) or path.suffix != ".sql": raise SystemExit("the SQL file must resolve beneath run/ops/sql and end in .sql")
    sql = path.read_text()
    if "\\" in sql: raise SystemExit("backslash is not allowed in a readback file")
    if not re.match(r"\s*(SELECT|WITH)\b", sql, re.I): raise SystemExit("one SELECT/WITH statement required")
with psycopg.connect("") as conn:          # connection settings come from the read-only environment file only
    conn.read_only = True
    with conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '14min'")
        cur.execute(sql, params, prepare=True)          # a prepared statement cannot hold more than one command
        if cur.description is None: raise SystemExit("the query did not return rows")
        out = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        out.writerow([c.name for c in cur.description])
        for row in cur: out.writerow(row)
KYPY
