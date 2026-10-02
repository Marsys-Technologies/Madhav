#!/usr/bin/env bash
# Protected-window rehearsal — MECHANICAL PART (Codex round 8 R8-10; runbook: PROTECTED_WINDOW_REHEARSAL_PLAN_v1_0.md).
# Runs the REAL `migrate.ts --only <deploy list>` against a disposable PostgreSQL that mirrors production's ledger, ownership,
# default privileges and roles; then proves the ledger precondition, per-file failure recovery and the privilege matrix.
# It never touches production: it connects ONLY to the disposable cluster named by PGHOST/PGPORT and a database it creates.
#
#   PGPORT=54329 REPO=/path/to/integration/worktree [STRICT=1] ./run_window_rehearsal.sh
#
# Requires: psql, node/npx (REPO/platform/node_modules installed), a disposable cluster with a superuser `postgres` (trust or PGPASSWORD).
# Exit 0 = every ASSERT passed. A line starting with FINDING is an expected-today observation (STRICT=1 turns FINDINGs into failures).
set -euo pipefail
: "${PGPORT:?set PGPORT to the disposable cluster port}" ; : "${REPO:?set REPO to the integration worktree}"
PGHOST="${PGHOST:-127.0.0.1}"; DB=gochara_rehearsal; HERE="$(cd "$(dirname "$0")" && pwd)"; STRICT="${STRICT:-0}"
case "$PGHOST" in 127.0.0.1|localhost) ;; *) echo "refusing: PGHOST must be loopback (got $PGHOST)"; exit 2;; esac
SU="psql -X -h $PGHOST -p $PGPORT -U postgres -v ON_ERROR_STOP=1 -q -t -A"
AS_OWNER() { psql -X -h "$PGHOST" -p "$PGPORT" -U postgres -d $DB -v ON_ERROR_STOP=1 -q -t -A -c "SET ROLE amjis_app; $1"; }
SUDB="$SU -d $DB"
pass=0; fail=0; findings=0
ASSERT() { if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "  ok   $1"; else fail=$((fail+1)); echo "  FAIL $1 (expected '$3', got '$2')"; fi; }
FINDING() { findings=$((findings+1)); echo "  FINDING $1"; if [ "$STRICT" = 1 ]; then fail=$((fail+1)); fi; }

echo "== S0 inputs =="
M="$REPO/platform/migrations"
WINDOW=(1153_gochara_sky_event_substrate.sql 1154_gochara_rule_path_registry.sql 1155_gochara_relationship_record.sql 1156_gochara_eval_window.sql 1157_gochara_av_polarity_declaration.sql 1204_gochara_av_qualifier_object_role.sql 1206_gochara_search_inventory_completeness.sql 1232_gochara_search_moon_scope_domain.sql 1233_gochara_p1_period_anchor.sql)
echo "integration ref: $(git -C "$REPO" rev-parse HEAD)  (record this SHA in the rehearsal record)"
for f in "${WINDOW[@]}"; do printf '  %s  %s\n' "$(shasum -a 256 "$M/$f" | cut -c1-16)" "$f"; done
if [ -f "$HERE/EXPECTED_WINDOW_SHA256.txt" ]; then
  (cd "$M" && shasum -a 256 -c "$HERE/EXPECTED_WINDOW_SHA256.txt" >/dev/null) && echo "  window file hashes match EXPECTED_WINDOW_SHA256.txt" || { echo "  FAIL window file hashes differ from EXPECTED_WINDOW_SHA256.txt"; exit 1; }
fi
ONLY="$(IFS=,; echo "${WINDOW[*]}")"     # exactly the list deploy.yml builds for gochara_contracts_schema_migration=true

echo "== S1 disposable database, roles, ownership, default privileges =="
$SU -c "DROP DATABASE IF EXISTS $DB" -c "CREATE DATABASE $DB"
$SUDB <<'SQL'
DO $$ DECLARE r text; BEGIN
 FOREACH r IN ARRAY ARRAY['amjis_app','data_plane_builder','gochara_sealer','gochara_verifier','data_plane_schema_owner'] LOOP
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname=r) THEN EXECUTE format('REASSIGN OWNED BY %I TO postgres', r); EXECUTE format('DROP OWNED BY %I', r); EXECUTE format('DROP ROLE %I', r); END IF;
 END LOOP; END $$;
CREATE ROLE data_plane_schema_owner NOLOGIN; CREATE ROLE amjis_app LOGIN PASSWORD 'rehearsal'; CREATE ROLE data_plane_builder NOLOGIN; CREATE ROLE gochara_sealer NOLOGIN; CREATE ROLE gochara_verifier NOLOGIN;
-- production: schema public is owned by data_plane_schema_owner; amjis_app holds USAGE only and gets CREATE for the protected window
-- (platform/scripts/jataka-schema-capability.ts grant/revoke); every object the window creates is OWNED BY amjis_app.
DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION data_plane_schema_owner;
GRANT USAGE ON SCHEMA public TO amjis_app, data_plane_builder, gochara_sealer, gochara_verifier;
ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;   -- nirmana-evidence-ownership-preflight.ts:259
SQL
OWNER_ASSERT=$($SUDB -c "SELECT nspowner::regrole FROM pg_namespace WHERE nspname='public'"); ASSERT "schema public is owned by data_plane_schema_owner (as in production)" "$OWNER_ASSERT" "data_plane_schema_owner"
CAP() { $SUDB -c "SET ROLE data_plane_schema_owner; $1 ON SCHEMA public $2 amjis_app"; }   # the window capability: GRANT CREATE ... TO / REVOKE CREATE ... FROM
echo "  PostgreSQL: $($SUDB -c 'SHOW server_version') (production is 15.18; run the rehearsal on PostgreSQL 15)"

echo "== S2 production-shaped prerequisites and LEDGER =="
CAP "GRANT CREATE" TO     # prerequisites are created with the capability, then it is revoked
$SUDB <<'SQL'
SET ROLE amjis_app;
CREATE TABLE charts (id uuid PRIMARY KEY DEFAULT gen_random_uuid());
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL, fact_category text NOT NULL, fact_subject text NOT NULL, fact_key text NOT NULL, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, unit text, citation_ref text NOT NULL DEFAULT '', citation_human text NOT NULL DEFAULT '', source_calculation text NOT NULL DEFAULT '', verification_pass_status text NOT NULL DEFAULT 'single_pass', engine_version text NOT NULL DEFAULT 'v', salience_formula_ver text, computed_at timestamptz NOT NULL DEFAULT now(), tolerance_arcsec double precision, near_sign_boundary_flag boolean DEFAULT false, near_nakshatra_boundary_flag boolean DEFAULT false, vargottama_flag_at_point boolean DEFAULT false, formula_provenance_text text, cross_ayanamsha_divergence_arcsec double precision DEFAULT 0.0, formula_id text);
CREATE TABLE chart_dashas (dasha_row_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL, system_id text NOT NULL, level_n integer NOT NULL, parent_row_id uuid, lord_graha text NOT NULL, lord_sign text, start_date date NOT NULL, end_date date NOT NULL, start_iso timestamptz NOT NULL, end_iso timestamptz NOT NULL, duration_days numeric NOT NULL, sandhi_flag boolean NOT NULL DEFAULT false, karaka_role_at_period text, verification_pass_status text NOT NULL DEFAULT 'two_pass_verified', verification_method text NOT NULL DEFAULT '', citation_ref text NOT NULL DEFAULT '', citation_human text NOT NULL DEFAULT '', computed_at timestamptz NOT NULL DEFAULT now(), engine_version text NOT NULL DEFAULT '', lord_natal_shadbala_total numeric, next_dasha_start_iso timestamptz, concurrent_system_lords_jsonb jsonb, anchored_solar_return_iso timestamptz, karakas_active_during_period text[]);
SQL
for f in 1081_nirmana_l3_gochara_ledger_coverage_publication.sql 1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql 1152_kala_gochara_contacts_t_exact_nullable_truncated.sql; do
  { echo "SET ROLE amjis_app;"; cat "$M/$f"; } | $SUDB >/dev/null
done
{ echo "SET ROLE amjis_app;"; echo "CREATE TABLE IF NOT EXISTS _migrations_applied (id SERIAL PRIMARY KEY, filename TEXT UNIQUE NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), sha256 TEXT NOT NULL); ALTER TABLE _migrations_applied ADD COLUMN IF NOT EXISTS sql_identity TEXT;"; } | $SUDB
# the production ledger as of 2026-10-02 (read-only snapshot of _migrations_applied.filename): every repo file named there is recorded as applied,
# EXCEPT the window files themselves (1153-1157 are applied in production but are re-applied here through the real runner).
APPLIED_SQL="SET ROLE amjis_app;"
while read -r fn; do
  [ -z "$fn" ] && continue
  case " ${WINDOW[*]} " in *" $fn "*) continue;; esac
  for d in "$M" "$REPO/platform/supabase/migrations"; do
    if [ -f "$d/$fn" ]; then h=$(shasum -a 256 "$d/$fn" | cut -d' ' -f1); APPLIED_SQL+=" INSERT INTO _migrations_applied (filename, sha256) VALUES ('$fn','$h') ON CONFLICT DO NOTHING;"; break; fi
  done
done < "$HERE/prod_ledger_2026-10-02.txt"
echo "$APPLIED_SQL" | $SUDB
# prod ALSO applied the contract helper grants before the window (1216, 1220): apply their SQL (their ledger rows came from the snapshot above)
for f in 1216_gochara_contract_builder_grants.sql; do { echo "SET ROLE amjis_app;"; cat "$M/$f"; } | $SUDB >/dev/null 2>&1 || true; done
echo "  ledger rows: $($SUDB -c 'SELECT count(*) FROM _migrations_applied')"
CAP "REVOKE CREATE" FROM
ASSERT "amjis_app has NO CREATE on schema public outside the window" "$($SUDB -c "SELECT has_schema_privilege('amjis_app','public','CREATE')")" "f"
# the pending routine migration that blocks the window: remove its row if the snapshot had it, to reproduce today's ledger exactly
$SUDB -c "DELETE FROM _migrations_applied WHERE filename IN ('1230_ka_gochara_registry_revert_1091_pin.sql')"
URL="postgresql://amjis_app:rehearsal@$PGHOST:$PGPORT/$DB"
RUN() { CAP "GRANT CREATE" TO >/dev/null; (cd "$REPO/platform" && DATABASE_URL="$URL" npx tsx scripts/migrate.ts --only "$ONLY" 2>&1); local rc=$?; CAP "REVOKE CREATE" FROM >/dev/null; return $rc; }

echo "== S3a ledger precondition: the real invocation against today's ledger =="
set +e; OUT=$(RUN); RC=$?; set -e
echo "$OUT" | tail -3 | sed 's/^/    /'
ASSERT "migrate.ts --only <window list> is REFUSED while an unselected predecessor is unapplied" "$([ $RC -ne 0 ] && echo refused || echo ran)" "refused"
ASSERT "the refusal names the unapplied predecessor 1230" "$(echo "$OUT" | grep -c '1230_ka_gochara_registry_revert_1091_pin.sql')" "1"
ASSERT "nothing from the window was applied by the refused run" "$($SUDB -c "SELECT count(*) FROM _migrations_applied WHERE filename = ANY (ARRAY['1204_gochara_av_qualifier_object_role.sql','1206_gochara_search_inventory_completeness.sql','1232_gochara_search_moon_scope_domain.sql','1233_gochara_p1_period_anchor.sql'])")" "0"

echo "== S3b the routine deploy applies 1230 first (represented by its ledger row) =="
H1230=$(shasum -a 256 "$M/1230_ka_gochara_registry_revert_1091_pin.sql" | cut -d' ' -f1)
$SUDB -c "INSERT INTO _migrations_applied (filename, sha256) VALUES ('1230_ka_gochara_registry_revert_1091_pin.sql','$H1230')"

echo "== S3c per-file failure recovery: make 1233 fail AFTER 1204/1206/1232 =="
# pre-seed a P1 row's blocker the cheap way: a column of the same name makes 1233's gate refuse (migration_1233_already_applied)
# (the gate only runs once 1155 exists; 1153-1157 apply first in the same invocation, so add the column AFTER them via a first partial run)
CAP "GRANT CREATE" TO >/dev/null; set +e; OUT=$(cd "$REPO/platform" && DATABASE_URL="$URL" npx tsx scripts/migrate.ts --only "${ONLY%%,1204*}" 2>&1); RC=$?; set -e; CAP "REVOKE CREATE" FROM >/dev/null
ASSERT "1153-1157 apply through the real runner" "$RC" "0"
$SUDB -c "SET ROLE amjis_app; ALTER TABLE ka_gochara_relationship_record ADD COLUMN period_anchor_lord text"
set +e; OUT=$(RUN); RC=$?; set -e
echo "$OUT" | tail -4 | sed 's/^/    /'
ASSERT "the full window run FAILS at 1233" "$([ $RC -ne 0 ] && echo failed || echo ok)" "failed"
ASSERT "1204, 1206 and 1232 stay committed (separate file transactions)" "$($SUDB -c "SELECT count(*) FROM _migrations_applied WHERE filename = ANY (ARRAY['1204_gochara_av_qualifier_object_role.sql','1206_gochara_search_inventory_completeness.sql','1232_gochara_search_moon_scope_domain.sql'])")" "3"
ASSERT "1233 is NOT recorded and its columns are not half-applied" "$($SUDB -c "SELECT count(*) FROM _migrations_applied WHERE filename='1233_gochara_p1_period_anchor.sql'")" "0"
$SUDB -c "SET ROLE amjis_app; ALTER TABLE ka_gochara_relationship_record DROP COLUMN period_anchor_lord"
set +e; OUT=$(RUN); RC=$?; set -e
echo "$OUT" | tail -3 | sed 's/^/    /'
ASSERT "after the cause is removed, the SAME invocation applies only 1233" "$RC" "0"
ASSERT "all four window files are now recorded exactly once" "$($SUDB -c "SELECT count(*) FROM _migrations_applied WHERE filename = ANY (ARRAY['1204_gochara_av_qualifier_object_role.sql','1206_gochara_search_inventory_completeness.sql','1232_gochara_search_moon_scope_domain.sql','1233_gochara_p1_period_anchor.sql'])")" "4"

echo "== S4 ownership and privilege matrix (deployment-faithful) =="
ASSERT "amjis_app holds no CREATE on schema public after the window (capability revoked)" "$($SUDB -c "SELECT has_schema_privilege('amjis_app','public','CREATE')")" "f"
ASSERT "every ka_gochara_* function is owned by amjis_app" "$($SUDB -c "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname LIKE 'ka\\_gochara\\_%' AND p.proowner::regrole::text <> 'amjis_app'")" "0"
ASSERT "every ka_gochara_* table is owned by amjis_app" "$($SUDB -c "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'ka\\_gochara\\_%' AND c.relkind='r' AND c.relowner::regrole::text <> 'amjis_app'")" "0"
ASSERT "PUBLIC holds EXECUTE on NO ka_gochara_* function created by the window" "$($SUDB -c "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname LIKE 'ka\\_gochara\\_%' AND EXISTS (SELECT 1 FROM aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a WHERE a.grantee = 0 AND a.privilege_type='EXECUTE')")" "0"
HAS_F() { $SUDB -c "SELECT has_function_privilege('$1','public.$2','EXECUTE')"; }
HAS_T() { $SUDB -c "SELECT has_table_privilege('$1','public.$2','$3')"; }
echo "  -- builder (data_plane_builder): grants come from 1216 / 1206 §7 / 1220 only"
$SUDB <<'SQL' >/dev/null
GRANT SELECT, INSERT ON ka_gochara_relationship_record, ka_gochara_record_prerequisite, ka_gochara_contact TO data_plane_builder;
SQL
ASSERT "builder may INSERT inventory obligations (construct path)" "$(HAS_T data_plane_builder ka_gochara_search_obligation INSERT)" "t"
ASSERT "builder may NOT run the seal function" "$(HAS_F data_plane_builder 'ka_gochara_seal_generation(uuid,text)')" "f"
ASSERT "builder may NOT run the completeness / replay checks (seal-side)" "$(HAS_F data_plane_builder 'ka_gochara_search_completeness_violations(uuid,text)')$(HAS_F data_plane_builder 'ka_gochara_search_replay_violations(uuid,text)')" "ff"
ASSERT "builder may NOT run 1232's two new seal-side functions" "$(HAS_F data_plane_builder 'ka_gochara_search_moon_scope_violations(uuid,text)')$(HAS_F data_plane_builder 'ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)')" "ff"
ASSERT "builder may NOT INSERT a generation seal" "$(HAS_T data_plane_builder ka_gochara_generation_seal INSERT)" "f"
if [ "$(HAS_T data_plane_builder ka_gochara_search_inventory_verification INSERT)" = "t" ]; then
  FINDING "PC-4: 1206 §7 grants the BUILDER INSERT/DELETE on ka_gochara_search_inventory_verification — the builder can write the independent verification row. Required end state: only the verifier principal (proposed grants-only migration)."
else ASSERT "builder may NOT write verification rows" "f" "f"; fi
echo "  -- sealer (gochara_sealer): granted by the authorising operator, not by any migration — grant exactly what the live suites grant"
SEALER_FUNCS="ka_gochara_lock_chart ka_gochara_seal_generation ka_gochara_generation_governed ka_gochara_coverage_drift ka_gochara_horizon_finite_ok ka_gochara_coverage_facts ka_gochara_facts_horizon ka_gochara_membership_violations ka_gochara_membership_violation ka_gochara_lock_global_shared ka_gochara_search_completeness_violations ka_gochara_search_l1_facts_digest ka_gochara_sha256_hex ka_gochara_canonical_json ka_gochara_search_dasha_digest ka_gochara_search_av_entry ka_gochara_search_inventory_digest ka_gochara_search_ledger_digest ka_gochara_search_inventory_preimage ka_gochara_utc_ts ka_gochara_search_replay_violations ka_gochara_search_inventories_digest ka_gochara_search_moon_scope_violations ka_gochara_search_moon_resolved_domain"
GRANT_LIST=$(for f in $SEALER_FUNCS; do printf 'public.%s, ' "$f"; done | sed 's/, $//')
$SUDB -c "SET ROLE amjis_app; GRANT EXECUTE ON FUNCTION $GRANT_LIST TO gochara_sealer; GRANT SELECT, INSERT ON ka_gochara_generation_seal TO gochara_sealer"
ASSERT "sealer may run the seal function" "$(HAS_F gochara_sealer 'ka_gochara_seal_generation(uuid,text)')" "t"
ASSERT "sealer has EXECUTE on 1232's two new helpers" "$(HAS_F gochara_sealer 'ka_gochara_search_moon_scope_violations(uuid,text)')$(HAS_F gochara_sealer 'ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)')" "tt"
ASSERT "sealer may NOT write inventory content" "$(HAS_T gochara_sealer ka_gochara_search_obligation INSERT)" "f"
echo "  -- verifier (gochara_verifier): NOT provisioned in production today; the proposed least-privilege set is tested here"
$SUDB -c "SET ROLE amjis_app; GRANT SELECT ON ka_gochara_search_input_snapshot, ka_gochara_search_inventory, ka_gochara_search_path_pin, ka_gochara_search_obligation, ka_gochara_search_interval, ka_gochara_search_inventory_verification, ka_gochara_relationship_record, ka_gochara_eval_window, ka_gochara_eval_window_record, kala_gochara_coverage TO gochara_verifier; GRANT INSERT ON ka_gochara_search_inventory_verification TO gochara_verifier; GRANT SELECT ON chart_facts, chart_dashas TO gochara_verifier"
ASSERT "verifier may write verification rows" "$(HAS_T gochara_verifier ka_gochara_search_inventory_verification INSERT)" "t"
ASSERT "verifier may NOT write obligations, intervals, records or windows" "$(HAS_T gochara_verifier ka_gochara_search_obligation INSERT)$(HAS_T gochara_verifier ka_gochara_search_interval INSERT)$(HAS_T gochara_verifier ka_gochara_relationship_record INSERT)$(HAS_T gochara_verifier ka_gochara_eval_window INSERT)" "ffff"
ASSERT "verifier may NOT seal" "$(HAS_F gochara_verifier 'ka_gochara_seal_generation(uuid,text)')" "f"
echo "  -- 1233: the anchor columns ride the builder's table-level grant"
ASSERT "builder INSERT covers period_anchor_lord / period_anchor_level" "$($SUDB -c "SELECT has_column_privilege('data_plane_builder','public.ka_gochara_relationship_record','period_anchor_lord','INSERT')::text || has_column_privilege('data_plane_builder','public.ka_gochara_relationship_record','period_anchor_level','INSERT')::text")" "truetrue"

echo
echo "REHEARSAL (mechanical part): $pass passed, $fail failed, $findings finding(s)."
[ "$fail" = 0 ]
