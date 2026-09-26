#!/usr/bin/env bash
# nikasha-test Phase 1 repair — pgvector extension, FK-replica mode, re-copy failed tables.
set -uo pipefail
SB=/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/nikasha_test/.sandbox
PORT=54329
say(){ echo "[repair] $*"; }
spsql(){ PGOPTIONS= /opt/homebrew/bin/psql -h "$SB" -p $PORT -U sandbox "$@"; }

spsql -d nikasha_sandbox -c "CREATE EXTENSION IF NOT EXISTS vector" || { say "CREATE EXTENSION vector FAILED"; exit 1; }
say "pgvector extension created"
spsql -d nikasha_sandbox -v ON_ERROR_STOP=0 -f "$SB/schema.sql" > "$SB/schema_load2.log" 2>&1
say "schema replay errors: $(grep -c ERROR "$SB/schema_load2.log")"
spsql -d postgres -c "ALTER DATABASE nikasha_sandbox SET session_replication_role = replica" || exit 1
say "session_replication_role=replica persisted on nikasha_sandbox"

source /Users/Dev/madhav-l3/dbenv.sh
export PGPORT=5433
: > "$SB/copy_report_repair.tsv"
awk -F'\t' '$4=="COPY_FAIL"{print $1"\t"$2}' "$SB/copy_report.tsv" | while IFS=$'\t' read -r t rule; do
  [ "$rule" = "view" ] && continue
  if [ "$rule" = "sample5pct_ctidhash" ]; then
    q="COPY (SELECT * FROM \"$t\" WHERE abs(hashtext(ctid::text)) % 20 = 0) TO STDOUT"
  else
    q="COPY (SELECT * FROM \"$t\") TO STDOUT"
  fi
  psql -t -A -c "$q" > "$SB/_buf.copy" 2>"$SB/_buf.err" || { say "COPY-OUT FAIL $t: $(head -1 "$SB/_buf.err")"; echo -e "$t\t$rule\tCOPY_FAIL\tCOPY_FAIL" >> "$SB/copy_report_repair.tsv"; continue; }
  spsql -d nikasha_sandbox -c "COPY \"$t\" FROM STDIN" < "$SB/_buf.copy" 2>"$SB/_buf.err" || { say "COPY-IN FAIL $t: $(head -1 "$SB/_buf.err")"; echo -e "$t\t$rule\t?\tCOPY_FAIL" >> "$SB/copy_report_repair.tsv"; continue; }
  pc=$(psql -t -A -c "SELECT count(*) FROM \"$t\"")
  sc=$(spsql -d nikasha_sandbox -t -A -c "SELECT count(*) FROM \"$t\"")
  echo -e "$t\t$rule\t$pc\t$sc" >> "$SB/copy_report_repair.tsv"
  say "ok $t prod=$pc sandbox=$sc"
done
rm -f "$SB/_buf.copy" "$SB/_buf.err"
say "repair done: $(wc -l < "$SB/copy_report_repair.tsv" | tr -d ' ') tables retried, $(grep -c COPY_FAIL "$SB/copy_report_repair.tsv" || true) still failing"
