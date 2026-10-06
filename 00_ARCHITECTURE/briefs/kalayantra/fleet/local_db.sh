#!/usr/bin/env bash
# Local rehearsal databases for the KĀLA-YANTRA lanes (charter §7). Production is never touched by this script.
#   local_db.sh up                 start (or reuse) the pgvector/pgvector:pg16 container on 127.0.0.1:${KY_PG_PORT:-55433} (55432 is taken on this machine)
#   local_db.sh seed               READ-ONLY schema dump of production + applied-migrations ledger → run/schema/ (re-run when main gains migrations)
#   local_db.sh db <lane>          create ky_<lane> = production schema (seed) + pending migrations via the project's runner (drops/recreates)
#   local_db.sh url <lane>         print the connection URL for ky_<lane>
#   local_db.sh down               stop the container (data discarded — these are throwaway databases)
#
# B-3b HARDENING (SŪTRADHĀRA): the replay uses platform/scripts/migrate.ts (the deploy's runner). If it stops, the
# runner log names the migration and the missing role/extension; add the role to the list in mkdb() or record a skip
# reason in local_db.skip (a file the runner does not read — it is the campaign's own record of why).
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

seed() {
  # READ-ONLY: a schema-only dump of production (tables the read-only role cannot lock are excluded and listed) plus the
  # data of _migrations_applied, so a throwaway database starts at production's schema and the runner applies only what is
  # pending. Needs ~/.config/pravaha/pgenv.sh (never printed). Re-run whenever main gains migrations.
  local D="$KY_ROOT/run/schema"; mkdir -p "$D"
  ( source /Users/Dev/.config/pravaha/pgenv.sh 2>/dev/null || { echo "pgenv missing"; exit 1; }
    local -a EXCL=(); local i t
    for i in $(seq 1 40); do
      local -a args=(); for t in "${EXCL[@]}"; do args+=(-T "$t"); done
      if pg_dump --schema-only --no-owner --no-privileges --no-comments -n public "${args[@]}" -f "$D/prod_schema.sql" 2>"$D/pg_dump.err"; then break; fi
      t="$(grep -oE 'permission denied for (table|sequence|view|materialized view) [a-zA-Z0-9_]+' "$D/pg_dump.err" | head -1 | awk '{print $NF}')"
      [ -n "$t" ] || { echo "schema dump failed for a non-permission reason:"; head -3 "$D/pg_dump.err"; exit 1; }
      EXCL+=("public.$t")
    done
    printf '%s\n' "${EXCL[@]}" > "$D/excluded_tables.txt"
    pg_dump --data-only --no-owner --no-privileges -t public._migrations_applied -f "$D/migrations_applied_data.sql" 2>"$D/pg_dump_applied.err"
    date -u +%Y-%m-%dT%H:%M:%SZ > "$D/SEEDED_AT"
    echo "seed ready: $(grep -c 'CREATE TABLE' "$D/prod_schema.sql") tables; excluded $(wc -l < "$D/excluded_tables.txt" | tr -d ' ') (see excluded_tables.txt); ledger rows dumped" )
}

mkdb() {
  # A throwaway database = production's schema (seed) + the project's own runner for pending migrations
  # (platform/scripts/migrate.ts — the deploy pipeline's code path). Never a hand-rolled file loop.
  local lane="$1"; local db="ky_$1"; local url="postgresql://postgres:$PW@127.0.0.1:$PORT/$db"; local D="$KY_ROOT/run/schema"
  [ -f "$D/prod_schema.sql" ] || seed || return 1
  "${PSQL[@]}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $db;" -c "CREATE DATABASE $db;"
  "${PSQL[@]}" -d "$db" -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS vector;' -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto;' -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;' -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' -c 'CREATE EXTENSION IF NOT EXISTS btree_gist;' >/dev/null
  for r in data_plane_builder role_orchestrator role_mcp_reader role_portal_reader role_pipeline_reader verifier_principal gochara_sealer role_web_serve role_ledger_write amjis_app anon authenticated service_role; do
    "${PSQL[@]}" -d "$db" -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$r') THEN CREATE ROLE $r NOLOGIN; END IF; END \$\$;" >/dev/null 2>&1 || true
  done
  echo "schema…"; "${PSQL[@]}" -d "$db" -q -f "$D/prod_schema.sql" > "$KY_ROOT/run/local_db_${lane}_schema.log" 2>&1 || true
  echo "applied ledger…"; "${PSQL[@]}" -d "$db" -q -f "$D/migrations_applied_data.sql" >> "$KY_ROOT/run/local_db_${lane}_schema.log" 2>&1 || true
  echo "runner (pending only)…"
  ( cd "$REPO/platform" && DATABASE_URL="$url" npx tsx scripts/migrate.ts ) > "$KY_ROOT/run/local_db_${lane}_runner.log" 2>&1; local rc=$?
  local tables applied
  tables="$("${PSQL[@]}" -d "$db" -tAc "select count(*) from pg_tables where schemaname='public'" 2>/dev/null)"
  applied="$("${PSQL[@]}" -d "$db" -tAc 'select count(*) from _migrations_applied' 2>/dev/null)"
  local errs; errs="$(grep -c 'ERROR' "$KY_ROOT/run/local_db_${lane}_schema.log" 2>/dev/null || true)"
  echo "ky_$lane: tables=$tables applied_ledger=$applied schema_errors=${errs:-0} runner_rc=$rc (logs: run/local_db_${lane}_{schema,runner}.log; excluded tables: run/schema/excluded_tables.txt)"
  return $rc
}

case "${1:-}" in
  up) up ;;
  seed) seed ;;
  db) [ -n "${2:-}" ] || { echo "lane required"; exit 2; }; up >/dev/null; mkdb "$2" ;;
  url) echo "postgresql://postgres:$PW@127.0.0.1:$PORT/ky_${2:?lane}" ;;
  down) docker rm -f "$CONT" >/dev/null 2>&1 || true; echo "stopped" ;;
  *) echo "usage: $0 up|seed|db <lane>|url <lane>|down"; exit 2 ;;
esac
