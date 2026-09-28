#!/bin/sh
# Phase 0.2 — disposable Postgres for the L3 Kāla P0 safety regression tests.
#
# Builds a harness that carries production's SCHEMA **and its trigger layer**.
# THE TRAP (measured, not assumed): a table-scoped `pg_dump -t public.<table>`
# does NOT carry the trigger FUNCTIONS. Restoring such a dump produces
#     ERROR: function public.l2_data_plane_guard_active_mutation() does not exist
# once per CREATE TRIGGER (15 of them here) and leaves a harness with none of
# production's guards. So functions are dumped SEPARATELY and loaded FIRST,
# with check_function_bodies=false because their bodies reference tables the
# table dump creates in the next step.
#
# Production is READ-ONLY throughout: pg_dump and \copy ... TO only.
set -e

PGBIN=/opt/homebrew/opt/postgresql@15/bin      # prod is 15.18; this is 15.17
SOCK=/tmp/kp0                                   # short path: 103-byte socket limit
PORT=59510
OUTDIR="${1:-/tmp/kp0/dump}"

rm -rf "$SOCK"; mkdir -p "$SOCK" "$OUTDIR"
"$PGBIN/initdb" -D "$SOCK/data" -U kxuser --auth=trust >"$SOCK/initdb.log" 2>&1
"$PGBIN/pg_ctl" -D "$SOCK/data" -o "-p $PORT -k $SOCK -c fsync=off" -l "$SOCK/pg.log" start

TABLES="charts asset_freshness bg_synthetic_cohort kala_gochara_authority \
kala_gochara_windows gochara_resonance_map bodha_pratijna bodha_msr_signals \
kala_field_weight_versions kala_field_weights build_substep_progress \
kala_field_provenance kala_field_salience kala_insights kala_timeline_spec \
kala_field_windows kala_field_null kala_field kala_field_snapshots \
kala_field_primitives kala_field_boundaries kala_field_clocks kala_field_routes \
kala_field_promise_edges kala_field_promise_nodes kala_field_kinematics \
kala_bhavishya kala_darshana kala_convergence phala_anchors \
data_plane_l2_producer_generations l2_data_plane_partition_contexts \
l2_data_plane_run_intents l2_data_plane_run_rows l2_data_plane_row_snapshots \
l2_data_plane_asset_outputs l2_data_plane_input_bind_receipts build_runs \
build_run_assets asset_registry brahma_event_ontology profiles bg_transit_rules \
chart_grants"

set -- ; for t in $TABLES; do set -- "$@" -t "public.$t"; done

# READ-ONLY reads from production.
. /Users/Dev/madhav-l3/dbenv.sh >/dev/null 2>&1
"$PGBIN/pg_dump" --schema-only --no-owner --no-privileges "$@" > "$OUTDIR/schema_tables.sql"
psql -Atq -c "SELECT string_agg(def, E';\n\n' ORDER BY nm) FROM (
  SELECT p.proname AS nm, pg_get_functiondef(p.oid) AS def
  FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname='public' AND p.prokind IN ('f','p')
    AND NOT EXISTS (SELECT 1 FROM pg_depend d JOIN pg_extension e ON e.oid=d.refobjid
                    WHERE d.objid=p.oid AND d.deptype='e')) s;" \
  > "$OUTDIR/public_functions.sql"
echo ";" >> "$OUTDIR/public_functions.sql"
for t in charts kala_field_weight_versions kala_field_weights bg_synthetic_cohort \
         brahma_event_ontology; do
  psql -Atq -c "\copy (SELECT * FROM public.$t) TO '$OUTDIR/seed_$t.tsv'"
done
psql -Atq -c "\copy (SELECT * FROM public.bodha_pratijna WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa') TO '$OUTDIR/seed_bodha_pratijna.tsv'"
psql -Atq -c "\copy (SELECT * FROM public.asset_registry WHERE asset_id IN ('ka_kshetra','ka_bhavishya_lekha','ka_kala_darshana')) TO '$OUTDIR/seed_asset_registry.tsv'"

# Harness psql: clears every PG* var the production dbenv exported (notably
# PGOPTIONS=-c default_transaction_read_only=on) so nothing can reach production.
hp() {
  env -u PGHOST -u PGPORT -u PGUSER -u PGPASSWORD -u PGDATABASE -u PGOPTIONS \
      -u PGSERVICE -u DATABASE_URL \
      "$PGBIN/psql" -h "$SOCK" -p "$PORT" -U kxuser "$@"
}

hp -d postgres -Atc "CREATE DATABASE kala_harness;"
hp -d kala_harness -Atc "CREATE EXTENSION IF NOT EXISTS pgcrypto;
                         CREATE EXTENSION IF NOT EXISTS pg_trgm;
                         CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
# 1) FUNCTIONS FIRST — this is the step a table-scoped dump silently omits.
( echo "SET check_function_bodies = false;"; cat "$OUTDIR/public_functions.sql" ) \
  | hp -d kala_harness -v ON_ERROR_STOP=0 -f -
# 2) tables, constraints, TRIGGERS
hp -d kala_harness -v ON_ERROR_STOP=0 -f "$OUTDIR/schema_tables.sql"
# 3) seed
hp -d kala_harness -Atq -c "INSERT INTO profiles (id, role, status)
    VALUES ('xl2wYZRPwsVgPSAgtn9XJ80Xkub2','guest','active') ON CONFLICT DO NOTHING;"
for t in brahma_event_ontology charts kala_field_weight_versions kala_field_weights \
         bg_synthetic_cohort asset_registry; do
  hp -d kala_harness -Atq -c "\copy public.$t FROM '$OUTDIR/seed_$t.tsv'"
done
hp -d kala_harness -Atq -c "ALTER TABLE bodha_pratijna DISABLE TRIGGER USER"
hp -d kala_harness -Atq -c "\copy public.bodha_pratijna FROM '$OUTDIR/seed_bodha_pratijna.tsv'"
hp -d kala_harness -Atq -c "ALTER TABLE bodha_pratijna ENABLE TRIGGER USER"

# 4) PROVE the guard layer is present and FIRES before any test runs.
hp -d kala_harness -Atc "SELECT c.relname||' | '||t.tgname||' | '||p.proname AS r
  FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_proc p ON p.oid=t.tgfoid
  JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE NOT t.tgisinternal AND n.nspname='public' ORDER BY r;"
hp -d kala_harness -v ON_ERROR_STOP=0 -Atc \
  "INSERT INTO bodha_pratijna (chart_id) VALUES ('482012f1-710e-4a25-994a-93821f5871aa');"
# Expected: ERROR: protected L2 INSERT requires direct data_plane_builder authentication

echo "harness ready: postgresql://kxuser@/kala_harness?host=$SOCK&port=$PORT"
