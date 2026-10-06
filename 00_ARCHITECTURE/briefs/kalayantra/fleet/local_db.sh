#!/usr/bin/env bash
# Local rehearsal databases for the KĀLA-YANTRA lanes (charter §7). Production is never touched by this script.
#   local_db.sh up                 start (or reuse) the pgvector/pgvector:pg16 container on 127.0.0.1:${KY_PG_PORT:-55433} (55432 is taken on this machine)
#   local_db.sh db <lane>          create ky_<lane> from the baseline schema + migrations (drops and recreates if it exists)
#   local_db.sh url <lane>         print the connection URL for ky_<lane>
#   local_db.sh down               stop the container (data discarded — these are throwaway databases)
#
# B-3 HARDENING (SŪTRADHĀRA): the migration replay below mirrors ci.yml's P3-C job (baseline via psql -f, then
# migrations). Migrations that need a production-only role/extension are listed in local_db.skip (one filename per
# line, with the reason) after the first replay surfaces them; the replay reports every skipped or failed file.
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
REPO="${KY_REPO:-$KY_ROOT/wt/campaign}"
MIG="$REPO/platform/supabase/migrations"
SKIP="$(dirname "$0")/local_db.skip"
CONT=ky-pg; PORT="${KY_PG_PORT:-55433}"; PW=postgres
PSQL=(psql -h 127.0.0.1 -p "$PORT" -U postgres)
export PGPASSWORD="$PW"

up() {
  if docker ps --format '{{.Names}}' | grep -qx "$CONT"; then echo "$CONT already running"; return; fi
  if docker ps -a --format '{{.Names}}' | grep -qx "$CONT"; then docker start "$CONT" >/dev/null; else
    docker run -d --name "$CONT" -e POSTGRES_PASSWORD="$PW" -p "127.0.0.1:$PORT:5432" pgvector/pgvector:pg16 >/dev/null
  fi
  for i in $(seq 1 30); do "${PSQL[@]}" -c 'select 1' >/dev/null 2>&1 && break; sleep 1; done
  "${PSQL[@]}" -c 'select version()' | head -3
}

mkdb() {
  local lane="$1" db="ky_$1" f n failures=0 skipped=0
  "${PSQL[@]}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $db;" -c "CREATE DATABASE $db;"
  "${PSQL[@]}" -d "$db" -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS vector;' -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto;' >/dev/null
  echo "baseline…"; "${PSQL[@]}" -d "$db" -q -f "$MIG/0001_brahma_baseline.sql" > "$KY_ROOT/run/local_db_${lane}_baseline.log" 2>&1 || true
  echo "migrations…"
  for f in $(ls "$MIG"/*.sql | sort -V); do
    n="$(basename "$f")"; [ "$n" = 0001_brahma_baseline.sql ] && continue
    if [ -f "$SKIP" ] && grep -q "^$n" "$SKIP"; then skipped=$((skipped+1)); continue; fi
    if ! "${PSQL[@]}" -d "$db" -q -v ON_ERROR_STOP=1 -f "$f" >> "$KY_ROOT/run/local_db_${lane}_migrations.log" 2>&1; then
      failures=$((failures+1)); echo "$n" >> "$KY_ROOT/run/local_db_${lane}.failures"
    fi
  done
  echo "ky_$lane ready: skipped=$skipped failed=$failures (failures listed in run/local_db_${lane}.failures; B-3 decides skip vs fix)"
}

case "${1:-}" in
  up) up ;;
  db) [ -n "${2:-}" ] || { echo "lane required"; exit 2; }; up >/dev/null; mkdb "$2" ;;
  url) echo "postgresql://postgres:$PW@127.0.0.1:$PORT/ky_${2:?lane}" ;;
  down) docker rm -f "$CONT" >/dev/null 2>&1 || true; echo "stopped" ;;
  *) echo "usage: $0 up|db <lane>|url <lane>|down"; exit 2 ;;
esac
