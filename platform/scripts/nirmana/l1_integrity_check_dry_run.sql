-- NIRMĀṆA L1 (Gaṇita) — integrity-check dry-run reporter (W5 prep, charter C8 priority-5)
-- L1-owned tooling (not shared/Conductor-owned like egate.sql/capsule_audit.sql). Read-only:
-- every asset_registry.integrity_check_sql is itself a bare SELECT ... AS integrity_passed
-- (verified live 2026-09-07: all 19 ga_* rows match `AS\s+integrity_passed\s*$`, none take a
-- $1 parameter). This script only writes to its own session-local TEMP scratch table.
--
--   psql "$DATABASE_URL" -f platform/scripts/nirmana/l1_integrity_check_dry_run.sql
--
-- Why it exists
-- -------------
-- W5 (per SESSION_CHARTER_V21.md) is "scripted mechanical checks + fresh-context verification
-- subagent -> verifier-identity capsule". The mechanical-check half needs no rebuild and no
-- identity-split machinery to be useful today: every one of L1's 19 assets already carries a
-- real, hand-authored integrity_check_sql contract (confirmed non-NULL for all 19, cycle 124 and
-- re-confirmed live here). This script runs all of them against the live canonical chart data
-- right now and reports PASS/FAIL, so a W5 session opens already knowing which assets are
-- mechanically clean and which need investigation -- instead of re-deriving that from scratch.
--
-- Deliberately NOT attempted here: capsule minting / evidence submission (`nrec --as verifier
-- integrity_verified ...`). That requires exact SHA256 digest computation against a strict Zod
-- schema and touches shared, identity-split-enforced campaign infrastructure with real
-- side effects (platform/src/lib/nirmana-elevation/evidence-command.ts) -- correctly a W5-time
-- action taken deliberately by a session with a real completed build to certify, not a
-- background dry-run. This script's job ends at "here is what the mechanical checks say today".
--
-- Known-expected result at time of writing (2026-09-07, chart-rebuild blocked campaign-wide by
-- adjudication #2113): FOUR assets are expected to read FAIL, live-confirmed against
-- L1_STATE.md's per-asset table before this script shipped -- all four are writer-level-fixed
-- defects whose residual only clears once the blocked rebuild actually runs, not new,
-- unaddressed problems:
--   ga_yoga        F-A16 (PR #1979,  cycle 41) -- strength_formula_version label without strength
--   ga_structural  F-A15/F-A17/F-157/F-A18/F-A24/F-A25/F-A26 -- seven tracked-red conjuncts
--   ga_condition   F-C8  (fixed at the writer level) -- conjunct (a), 135/135 rows
--   ga_vargas      F-A1  (fixed at the writer level) -- D1-authority-vs-chart_facts mismatch,
--                  precisely quantified (not newly discovered) at ga_vargas' own D9 grain
-- A FAIL here is not evidence of a new defect by itself -- always cross-check L1_STATE.md's
-- per-asset table (grep the asset's F-IDs) before treating any FAIL surfaced here as new work.
-- Any FAIL/ERROR beyond these four exact assets IS new and needs investigation.

\echo ''
\echo '════ L1 (ga_*) integrity_check_sql dry run — live data, no rebuild required ════'

CREATE TEMP TABLE IF NOT EXISTS _l1_integrity_dry_run_results (
  asset_id text, integrity_passed boolean, error_note text
);
DELETE FROM _l1_integrity_dry_run_results;

DO $l1_integrity_dry_run$
DECLARE
  r RECORD;
  passed boolean;
BEGIN
  FOR r IN
    SELECT asset_id, integrity_check_sql
    FROM asset_registry
    WHERE asset_id LIKE 'ga\_%' AND integrity_check_sql IS NOT NULL
    ORDER BY asset_id
  LOOP
    BEGIN
      EXECUTE r.integrity_check_sql INTO passed;
      INSERT INTO _l1_integrity_dry_run_results VALUES (r.asset_id, passed, NULL);
    EXCEPTION WHEN OTHERS THEN
      INSERT INTO _l1_integrity_dry_run_results VALUES (r.asset_id, NULL, SQLERRM);
    END;
  END LOOP;
END;
$l1_integrity_dry_run$;

\echo ''
\echo '-- FAIL / ERROR first, so anything needing attention is not buried below 19 PASS rows --'
SELECT asset_id,
  CASE
    WHEN error_note IS NOT NULL THEN 'ERROR'
    WHEN integrity_passed IS TRUE THEN 'PASS'
    WHEN integrity_passed IS FALSE THEN 'FAIL'
    ELSE 'NULL-RESULT'
  END AS verdict,
  error_note
FROM _l1_integrity_dry_run_results
ORDER BY (error_note IS NOT NULL) DESC, (integrity_passed IS NOT TRUE) DESC, asset_id;

\echo ''
\echo '-- summary --'
SELECT
  count(*) FILTER (WHERE error_note IS NULL AND integrity_passed IS TRUE)  AS pass_count,
  count(*) FILTER (WHERE error_note IS NULL AND integrity_passed IS FALSE) AS fail_count,
  count(*) FILTER (WHERE error_note IS NULL AND integrity_passed IS NULL)  AS null_result_count,
  count(*) FILTER (WHERE error_note IS NOT NULL)                          AS error_count,
  count(*) AS total_checked
FROM _l1_integrity_dry_run_results;
