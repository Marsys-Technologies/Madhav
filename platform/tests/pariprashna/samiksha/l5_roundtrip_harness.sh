#!/usr/bin/env bash
# SAMĪKṢĀ L-5 throwaway-DB round-trip harness — PB-3 lane L-5.
#
# Applies migration 470 (the L-1 ledger) to a throwaway Postgres, points
# SAMIKSHA_TEST_DATABASE_URL at it, and runs the L-5 pure + integration tests. Real code path,
# real DB — no mocks.
#
# Two ways to supply the DB (in priority order):
#   1. Export SAMIKSHA_ADMIN_DSN pointing at a reachable Postgres you may create a DB on, e.g.
#        SAMIKSHA_ADMIN_DSN="postgresql://postgres@127.0.0.1:54329/postgres"
#      (the path used to PROVE this lane — a reachable local throwaway cluster).
#   2. Otherwise the script tries `initdb` to spin up its own cluster. NOTE: `initdb` fails in
#      a sandbox whose euid has no passwd entry ("could not look up effective user ID"); use
#      option 1 there.
#
# Usage:  bash platform/tests/pariprashna/samiksha/l5_roundtrip_harness.sh
set -euo pipefail

PLATFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MIGRATION="$PLATFORM_DIR/supabase/migrations/470_pariprashna_samiksha_prediction_ledger.sql"
DBNAME="samiksha_l5"

apply_and_run() {
  local admin_dsn="$1" run_dsn="$2"
  echo "== reset db $DBNAME =="
  psql "$admin_dsn" -q -c "DROP DATABASE IF EXISTS $DBNAME;" -c "CREATE DATABASE $DBNAME;"
  echo "== FK stub: minimal message_parts(id uuid pk) so migration 470's FK resolves =="
  psql "$run_dsn" -v ON_ERROR_STOP=1 -q -c "CREATE TABLE message_parts (id uuid PRIMARY KEY DEFAULT gen_random_uuid());"
  echo "== apply migration 470 (the real L-1 ledger DDL) =="
  psql "$run_dsn" -v ON_ERROR_STOP=1 -q -f "$MIGRATION"
  psql "$run_dsn" -q -c "SELECT to_regclass('public.brahma_mimamsa_prediction_ledger') AS ledger;"
  export SAMIKSHA_TEST_DATABASE_URL="$run_dsn"
  echo "== run L-5 tests (pure + real-DB integration) =="
  cd "$PLATFORM_DIR"
  node_modules/.bin/vitest run \
    tests/pariprashna/samiksha/outcome_calibration.test.ts \
    tests/pariprashna/samiksha/outcome_recorder_db.integration.test.ts
}

if [[ -n "${SAMIKSHA_ADMIN_DSN:-}" ]]; then
  # Derive the run DSN by swapping the db name onto the admin DSN's host/port/user.
  base="${SAMIKSHA_ADMIN_DSN%/*}"
  apply_and_run "$SAMIKSHA_ADMIN_DSN" "$base/$DBNAME"
  exit 0
fi

# Fallback: self-hosted throwaway cluster via initdb (fails under a passwd-less sandbox euid).
WORK="$(mktemp -d "${TMPDIR:-/tmp}/samiksha_l5_pg.XXXXXX")"
PGDATA="$WORK/data"; PGSOCK="$WORK/sock"; PGPORT="${SAMIKSHA_L5_PGPORT:-55470}"; mkdir -p "$PGSOCK"
cleanup() { pg_ctl -D "$PGDATA" -m immediate stop >/dev/null 2>&1 || true; rm -rf "$WORK"; }
trap cleanup EXIT
initdb -D "$PGDATA" -U postgres --auth=trust >/dev/null
pg_ctl -D "$PGDATA" -o "-p $PGPORT -k $PGSOCK -c listen_addresses=''" -w start >/dev/null
apply_and_run "postgresql://postgres@/postgres?host=$PGSOCK&port=$PGPORT" \
              "postgresql://postgres@/$DBNAME?host=$PGSOCK&port=$PGPORT"
