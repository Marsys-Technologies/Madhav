#!/usr/bin/env bash
# Local rehearsal databases v1.1 (charter §7). Production is never written by this script; the seed is a READ-ONLY dump.
#   local_db.sh up              start (or reuse, after validating image+label) pgvector/pgvector:pg16 on 127.0.0.1:${KY_PG_PORT:-55433}
#   local_db.sh seed            READ-ONLY schema dump of production + the applied-migrations ledger → run/schema/. An OPERATOR or
#                               EXECUTOR action (executor kind `local_schema_seed`): it reads the production connection settings,
#                               so it refuses to run inside a lane (KY_LANE set).
#   local_db.sh db <lane>       create ky_<lane> if absent (seed + migrate.ts for pending) or RE-VALIDATE it if present; either way the
#                               answer is READY (assertions passed in THIS invocation, receipt written) or FAILED — never just 'exists'
#   local_db.sh reset <lane>    drop and recreate ky_<lane> (explicit; a worker notes it in the tracker first)
#   local_db.sh url <lane>      print the connection URL (read-only operation)
#   local_db.sh down            stop the container
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; REPO="${KY_REPO:-$KY_ROOT/wt/campaign}"
CONT=ky-pg; IMAGE=pgvector/pgvector:pg16; PORT="${KY_PG_PORT:-55433}"; PW=postgres; LABEL=campaign=kalayantra
PSQL=(psql -h 127.0.0.1 -p "$PORT" -U postgres); export PGPASSWORD="$PW"
LANES="sutradhara adhikarin v1 v2 v3 k1 k2 k3 k4 k5 k6 k7 k8"
valid_lane() { case " $LANES " in *" $1 "*) return 0;; *) echo "invalid lane $1"; return 2;; esac; }
up() {
  if docker ps -a --format '{{.Names}}' | grep -qx "$CONT"; then
    img="$(docker inspect -f '{{.Config.Image}}' "$CONT")"; lbl="$(docker inspect -f '{{index .Config.Labels "campaign"}}' "$CONT")"
    [ "$img" = "$IMAGE" ] && [ "$lbl" = "kalayantra" ] || { echo "container $CONT exists but is not ours ($img, campaign=$lbl) — refusing to reuse or remove"; exit 1; }
    docker ps --format '{{.Names}}' | grep -qx "$CONT" || docker start "$CONT" >/dev/null
  else docker run -d --name "$CONT" --label "$LABEL" -e POSTGRES_PASSWORD="$PW" -p "127.0.0.1:$PORT:5432" "$IMAGE" >/dev/null; fi
  for i in $(seq 1 30); do "${PSQL[@]}" -c 'select 1' >/dev/null 2>&1 && break; sleep 1; done
  "${PSQL[@]}" -tAc 'select version()' | cut -c1-60
}
seed() {
  [ -z "${KY_LANE:-}" ] || { echo "seed reads the production connection settings: it is the operator's or the executor's action, never a lane's (request executor kind local_schema_seed)"; return 1; }
  local D="$KY_ROOT/run/schema"; mkdir -p "$D"
  [ -f /Users/Dev/.config/pravaha/pgenv.sh ] || { echo "pgenv missing"; exit 1; }
  ( source /Users/Dev/.config/pravaha/pgenv.sh; local -a EXCL=(); local i t
    for i in $(seq 1 40); do local -a args=(); for t in ${EXCL[@]+"${EXCL[@]}"}; do args+=(-T "$t"); done
      if pg_dump --schema-only --no-owner --no-privileges --no-comments -n public ${args[@]+"${args[@]}"} -f "$D/prod_schema.sql" 2>"$D/pg_dump.err"; then break; fi
      t="$(grep -oE 'permission denied for (table|sequence|view|materialized view) [a-zA-Z0-9_]+' "$D/pg_dump.err" | head -1 | awk '{print $NF}')"
      [ -n "$t" ] || { echo "schema dump failed:"; head -3 "$D/pg_dump.err"; exit 1; }; EXCL+=("public.$t"); done
    printf '%s\n' ${EXCL[@]+"${EXCL[@]}"} > "$D/excluded_tables.txt"
    pg_dump --data-only --no-owner --no-privileges -t public._migrations_applied -f "$D/migrations_applied_data.sql" 2>"$D/pg_dump_applied.err"
    date -u +%Y-%m-%dT%H:%M:%SZ > "$D/SEEDED_AT"
    echo "seed ready: $(grep -c 'CREATE TABLE' "$D/prod_schema.sql") tables; excluded $(wc -l < "$D/excluded_tables.txt" | tr -d ' ') (run/schema/excluded_tables.txt)" )
}
mkdb() {
  local lane="$1"; valid_lane "$lane" || return 2; local db="ky_$lane"; local url="postgresql://postgres:$PW@127.0.0.1:$PORT/$db"; local D="$KY_ROOT/run/schema"
  [ -s "$D/prod_schema.sql" ] && [ -s "$D/migrations_applied_data.sql" ] || { echo "ky_$lane FAILED: the schema seed is missing under run/schema/ — an operator/executor prerequisite (local_schema_seed); a lane never reads production settings"; return 1; }
  rm -f "$KY_ROOT/run/local_db/$lane.json"          # a restore in progress has no receipt; only a proven one writes it
  "${PSQL[@]}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE $db;" || return 1
  "${PSQL[@]}" -d "$db" -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS vector;' -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto;' -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;' -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' -c 'CREATE EXTENSION IF NOT EXISTS btree_gist;' >/dev/null
  for r in role_sidecar role_jobs data_plane_builder role_orchestrator role_mcp_reader role_portal_reader role_pipeline_reader verifier_principal gochara_sealer role_web_serve role_ledger_write amjis_app anon authenticated service_role; do
    "${PSQL[@]}" -d "$db" -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$r') THEN CREATE ROLE $r NOLOGIN; END IF; END \$\$;" >/dev/null 2>&1 || true
  done
  # psql exits 0 on statement errors (they are judged exactly, below) and non-zero on a connection or process failure (fatal here)
  "${PSQL[@]}" -d "$db" -q -f "$D/prod_schema.sql" > "$KY_ROOT/run/local_db_${lane}_schema.log" 2>&1 || return 1
  "${PSQL[@]}" -d "$db" -q -f "$D/migrations_applied_data.sql" >> "$KY_ROOT/run/local_db_${lane}_schema.log" 2>&1 || return 1
  validate "$lane" restored
}
# The restore of the read-only dump produces EXACTLY nine statement errors — the pre-existing public schema (1) and the two types of
# the planner tables the dump could not include (6 + 2). The check is an exact multiset: any other message, or any other count,
# means an incomplete or different fixture and fails the lane database.
restore_errors_unexpected() {   # prints 0 when the log holds exactly the nine expected errors, 1 otherwise
  /opt/homebrew/bin/python3 - "$1" <<'KYPY'
import collections, pathlib, re, sys
try: text = pathlib.Path(sys.argv[1]).read_text()
except OSError: print(1); sys.exit(0)
actual = collections.Counter(f"{m.group(1)}: {' '.join(m.group(2).split())}" for m in (re.search(r"\b(ERROR|FATAL|PANIC):\s*(.*)$", line) for line in text.splitlines()) if m)
expected = collections.Counter({'ERROR: schema "public" already exists': 1,
                                'ERROR: type "public.planner_managed_prashna_jobs" does not exist': 6,
                                'ERROR: type "public.planner_inquiry_lifecycles" does not exist': 2})
print(0 if actual == expected else 1)
KYPY
}
# MIGRATE_APPLY_PROTECTED=1: lane databases are loopback superuser rehearsal DBs, so the runner also applies the Kāla
# protected-window files (platform/scripts/kala_protected_migrations.txt) that production applies only via kala_schema_migration=true.
validate() {   # validate <lane> [restored] — assertions run in THIS invocation; pending migrations applied by the project's runner; a receipt
  local lane="$1" db="ky_$1"; local url="postgresql://postgres:$PW@127.0.0.1:$PORT/$db"; local D="$KY_ROOT/run/schema" rc=0
  local tables kala applied unexpected=1 seed_sha
  seed_sha="$(shasum -a 256 "$D/prod_schema.sql" "$D/migrations_applied_data.sql" | shasum -a 256 | cut -d' ' -f1)" || return 1
  if [ "${2:-}" != restored ]; then      # an existing database is trusted only with a READY receipt bound to this very seed
    /opt/homebrew/bin/python3 -c 'import json, sys
try:
    r = json.load(open(sys.argv[1])); ok = r.get("result") == "READY" and r.get("lane") == sys.argv[2] and r.get("seed_sha256") == sys.argv[3]
except (OSError, ValueError): ok = False
sys.exit(0 if ok else 1)' "$KY_ROOT/run/local_db/$lane.json" "$lane" "$seed_sha" || { echo "ky_$lane FAILED: restore provenance missing or changed (no READY receipt for this seed) — run: local_db.sh reset $lane"; return 1; }
  fi
  ( cd "$REPO/platform" && DATABASE_URL="$url" MIGRATE_APPLY_PROTECTED=1 npx tsx scripts/migrate.ts ) > "$KY_ROOT/run/local_db_${lane}_runner.log" 2>&1 || rc=$?
  tables="$("${PSQL[@]}" -d "$db" -tAc "select count(*) from pg_tables where schemaname='public'" 2>/dev/null || echo 0)"
  kala="$("${PSQL[@]}" -d "$db" -tAc "select count(*) from pg_tables where schemaname='public' and (tablename like 'kala_%' or tablename like 'ka_gochara%')" 2>/dev/null || echo 0)"
  applied="$("${PSQL[@]}" -d "$db" -tAc 'select count(*) from _migrations_applied' 2>/dev/null || echo 0)"
  unexpected="$(restore_errors_unexpected "$KY_ROOT/run/local_db_${lane}_schema.log")" || return 1
  mkdir -p "$KY_ROOT/run/local_db"
  local result=FAILED
  if [ "$rc" -eq 0 ] && [ "${tables:-0}" -ge 400 ] && [ "${kala:-0}" -ge 70 ] && [ "${applied:-0}" -ge 900 ] && [ "${unexpected:-0}" -eq 0 ]; then result=READY; fi
  printf '{"lane":"%s","result":"%s","tables":%s,"kala_tables":%s,"ledger":%s,"unexpected_restore_errors":%s,"runner_rc":%s,"seed_sha256":"%s","ts":"%s"}\n' \
    "$lane" "$result" "${tables:-0}" "${kala:-0}" "${applied:-0}" "${unexpected:-0}" "$rc" "$seed_sha" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$KY_ROOT/run/local_db/$lane.json"
  echo "ky_$lane $result: tables=${tables:-0} kala_tables=${kala:-0} ledger=${applied:-0} unexpected_restore_errors=${unexpected:-0} runner_rc=$rc (receipt run/local_db/$lane.json)"
  [ "$result" = READY ]
}
case "${1:-}" in
  up) up ;;
  seed) seed ;;
  db) valid_lane "${2:?lane}" || exit 2; up >/dev/null; if "${PSQL[@]}" -tAc "select 1 from pg_database where datname='ky_$2'" | grep -q 1; then validate "$2"; else mkdb "$2"; fi ;;
  reset) valid_lane "${2:?lane}" || exit 2; up >/dev/null; "${PSQL[@]}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ky_$2;"; mkdb "$2" ;;
  url) valid_lane "${2:?lane}" || exit 2; echo "postgresql://postgres:$PW@127.0.0.1:$PORT/ky_$2" ;;
  down) docker stop "$CONT" >/dev/null 2>&1 || true; echo "stopped (container kept)" ;;
  *) echo "usage: $0 up|seed|db <lane>|reset <lane>|url <lane>|down"; exit 2 ;;
esac
