#!/usr/bin/env bash
# nikasha-test Phase 1 — build the sandbox from read-only production extraction.
# NEVER points at the production proxy for anything but SELECTs. Local server on a unix socket only.
set -uo pipefail

SB=/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/nikasha_test/.sandbox
PGBIN=/opt/homebrew/bin
PORT=54329
mkdir -p "$SB"
LOG="$SB/build.log"; : > "$LOG"

say(){ echo "[sandbox] $*" | tee -a "$LOG"; }

# Sandbox-bound psql: PGOPTIONS from dbenv.sh (read-only) must NOT leak into local connections.
spsql(){ PGOPTIONS= psql -h "$SB" -p $PORT -U sandbox "$@"; }

# 1. initdb + start (idempotent)
if [ ! -s "$SB/pgdata/PG_VERSION" ]; then
  "$PGBIN/initdb" -D "$SB/pgdata" -U sandbox --auth=trust >>"$LOG" 2>&1 || { say "initdb FAILED"; exit 1; }
fi
if ! "$PGBIN/pg_ctl" -D "$SB/pgdata" status >/dev/null 2>&1; then
  "$PGBIN/pg_ctl" -D "$SB/pgdata" -l "$SB/server.log" \
    -o "-k $SB -p $PORT -c listen_addresses=''" -w start >>"$LOG" 2>&1 || { say "start FAILED"; exit 1; }
fi
say "server up (socket $SB, port $PORT)"
spsql -d postgres -t -A -c "SELECT version()" >/dev/null
spsql -d postgres -c "DROP DATABASE IF EXISTS nikasha_sandbox" >>"$LOG" 2>&1
spsql -d postgres -c "CREATE DATABASE nikasha_sandbox" >>"$LOG" 2>&1

# 2. table list + row estimates from production (read-only)
source /Users/Dev/madhav-l3/dbenv.sh
export PGPORT=5433
psql -t -A -F'|' > "$SB/tables.tsv" <<'SQL'
WITH t AS (
  SELECT DISTINCT target_table AS t FROM asset_registry WHERE target_table IS NOT NULL
  UNION SELECT unnest(ARRAY['asset_registry','asset_throughput','build_runs','build_run_assets',
    'build_events','brahma_ontology','classical_text_chunks','sutravali_rules','_migrations_applied'])
)
SELECT t.t, c.reltuples::bigint, c.relkind
FROM t JOIN pg_class c ON c.relname=t.t JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname='public'
ORDER BY 1;
SQL
say "tables: $(wc -l < "$SB/tables.tsv" | tr -d ' ')"

# 3. schema extraction (read-only pg_dump, includes constraints + indexes)
ALL=(); while IFS= read -r _t; do ALL+=("$_t"); done < <(cut -f1 "$SB/tables.tsv")
TARGS=(); for t in "${ALL[@]}"; do TARGS+=(-t "$t"); done
"$PGBIN/pg_dump" -s --no-owner --no-privileges "${TARGS[@]}" > "$SB/schema.sql" 2>>"$LOG" || { say "pg_dump FAILED"; exit 1; }
say "schema.sql $(wc -l < "$SB/schema.sql") lines, sha256 $(shasum -a 256 "$SB/schema.sql" | cut -c1-12)"

# 4. load schema; FK errors against non-included tables are logged, not fatal
spsql -d nikasha_sandbox -c "CREATE TABLE _w(i int); DROP TABLE _w" >/dev/null 2>&1 || { say "sandbox is READ-ONLY (PGOPTIONS leak) — aborting"; exit 1; }
spsql -d nikasha_sandbox -v ON_ERROR_STOP=0 -f "$SB/schema.sql" > "$SB/schema_load.log" 2>&1
grep -c ERROR "$SB/schema_load.log" | sed 's/^/[sandbox] schema load errors: /'

# 5. data: full copy <=50k rows, else 5% deterministic sample (hashtext(ctid::text) % 20 = 0)
: > "$SB/copy_report.tsv"
while IFS='|' read -r t n k; do
  [ "$k" = "v" ] && { echo -e "$t\tview\t0\t0" >> "$SB/copy_report.tsv"; continue; }
  if [ "$n" -gt 50000 ]; then
    q="COPY (SELECT * FROM \"$t\" WHERE abs(hashtext(ctid::text)) % 20 = 0) TO STDOUT"
    rule="sample5pct_ctidhash"
  else
    q="COPY (SELECT * FROM \"$t\") TO STDOUT"
    rule="full"
  fi
  # exact production count
  pc=$(psql -t -A -c "SELECT count(*) FROM \"$t\"")
  if ! psql -t -A -c "$q" > "$SB/_buf.copy" 2>"$SB/_buf.err"; then
    say "COPY-OUT FAIL $t: $(head -1 "$SB/_buf.err")"; echo -e "$t\t$rule\t$pc\tCOPY_FAIL" >> "$SB/copy_report.tsv"; continue
  fi
  if ! spsql -d nikasha_sandbox -c "COPY \"$t\" FROM STDIN" < "$SB/_buf.copy" 2>"$SB/_buf.err"; then
    say "COPY-IN FAIL $t: $(head -1 "$SB/_buf.err")"; echo -e "$t\t$rule\t$pc\tCOPY_FAIL" >> "$SB/copy_report.tsv"; continue
  fi
  sc=$(spsql -d nikasha_sandbox -t -A -c "SELECT count(*) FROM \"$t\"")
  echo -e "$t\t$rule\t$pc\t$sc" >> "$SB/copy_report.tsv"
done < "$SB/tables.tsv"
rm -f "$SB/_buf.copy" "$SB/_buf.err"
say "data copy done: $(awk -F'\t' '$4!="COPY_FAIL"' "$SB/copy_report.tsv" | wc -l | tr -d ' ') ok, $(grep -c COPY_FAIL "$SB/copy_report.tsv" || true) failed"
