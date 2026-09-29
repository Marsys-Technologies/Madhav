#!/usr/bin/env bash
# nikasha-test Phase 1 extension pass 2 — extend_sandbox.sh's regex extraction picked up
# CTE names / subquery aliases as "tables" (b, c, baseline, computed...). This pass filters
# candidate names against relations that actually exist in production before copying.
set -uo pipefail
SB=/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/nikasha_test/.sandbox
PGBIN=/opt/homebrew/bin
PORT=54329
say(){ echo "[extend2] $*"; }
spsql(){ PGOPTIONS= $PGBIN/psql -h "$SB" -p $PORT -U sandbox "$@"; }
source /Users/Dev/madhav-l3/dbenv.sh
export PGPORT=5433

psql -t -A -c "SELECT count_sql FROM asset_registry WHERE count_sql IS NOT NULL" > "$SB/_sql.txt"
psql -t -A -c "SELECT integrity_check_sql FROM asset_registry WHERE integrity_check_sql IS NOT NULL" >> "$SB/_sql.txt"
grep -oE '(FROM|JOIN|UPDATE|INTO) [a-z_][a-z0-9_]*' "$SB/_sql.txt" | awk '{print $2}' | sort -u > "$SB/_refs.txt"
psql -t -A -c "SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','v')" | sort -u > "$SB/_prod.txt"
comm -12 "$SB/_refs.txt" "$SB/_prod.txt" > "$SB/_refs_real.txt"
spsql -d nikasha_sandbox -t -A -c "SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND relkind IN ('r','v')" | sort -u > "$SB/_have.txt"
comm -23 "$SB/_refs_real.txt" "$SB/_have.txt" > "$SB/_missing.txt"
say "missing (real, validated against prod): $(wc -l < "$SB/_missing.txt" | tr -d ' ') tables"
cat "$SB/_missing.txt"

TARGS=(); while IFS= read -r t; do TARGS+=(-t "$t"); done < "$SB/_missing.txt"
[ ${#TARGS[@]} -eq 0 ] && { say "nothing to add"; exit 0; }
$PGBIN/pg_dump -s --no-owner --no-privileges "${TARGS[@]}" > "$SB/schema_ext2.sql" 2>>"$SB/build.log" || { say "pg_dump FAILED"; exit 1; }
spsql -d nikasha_sandbox -v ON_ERROR_STOP=0 -f "$SB/schema_ext2.sql" > "$SB/schema_ext2_load.log" 2>&1
say "ext2 schema errors: $(grep -c ERROR "$SB/schema_ext2_load.log" || true)"

: > "$SB/copy_report_ext2.tsv"
while IFS= read -r t; do
  k=$(psql -t -A -c "SELECT relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='$t'")
  if [ "$k" = "v" ]; then
    def=$(psql -t -A -c "SELECT pg_get_viewdef('$t'::regclass)")
    spsql -d nikasha_sandbox -c "CREATE OR REPLACE VIEW \"$t\" AS $def" 2>/dev/null \
      && echo -e "$t\tview\tview\tview" >> "$SB/copy_report_ext2.tsv" \
      || { say "VIEW FAIL $t"; echo -e "$t\tview\tview\tCOPY_FAIL" >> "$SB/copy_report_ext2.tsv"; }
    continue
  fi
  n=$(psql -t -A -c "SELECT reltuples::bigint FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='$t'")
  cols=$(psql -t -A -c "SELECT string_agg(attname, ', ' ORDER BY attnum) FROM pg_attribute WHERE attrelid='public.$t'::regclass AND attnum>0 AND NOT attisdropped AND attgenerated=''")
  if [ "$n" -gt 50000 ]; then q="COPY (SELECT $cols FROM \"$t\" WHERE abs(hashtext(ctid::text)) % 20 = 0) TO STDOUT"; rule="sample5pct_ctidhash"; else q="COPY (SELECT $cols FROM \"$t\") TO STDOUT"; rule="full"; fi
  pc=$(psql -t -A -c "SELECT count(*) FROM \"$t\"")
  psql -t -A -c "$q" > "$SB/_b.copy" 2>"$SB/_b.err" || { say "COPY-OUT FAIL $t: $(head -1 "$SB/_b.err")"; echo -e "$t\t$rule\t$pc\tCOPY_FAIL" >> "$SB/copy_report_ext2.tsv"; continue; }
  spsql -d nikasha_sandbox -c "COPY \"$t\" ($cols) FROM STDIN" < "$SB/_b.copy" 2>"$SB/_b.err" || { say "COPY-IN FAIL $t: $(head -1 "$SB/_b.err")"; echo -e "$t\t$rule\t$pc\tCOPY_FAIL" >> "$SB/copy_report_ext2.tsv"; continue; }
  sc=$(spsql -d nikasha_sandbox -t -A -c "SELECT count(*) FROM \"$t\"")
  echo -e "$t\t$rule\t$pc\t$sc" >> "$SB/copy_report_ext2.tsv"
done < "$SB/_missing.txt"
rm -f "$SB/_b.copy" "$SB/_b.err" "$SB/_sql.txt"
say "extension2 done: $(awk -F'\t' '$4!="COPY_FAIL"' "$SB/copy_report_ext2.tsv" | wc -l | tr -d ' ') ok, $(grep -c COPY_FAIL "$SB/copy_report_ext2.tsv" || true) failed"
