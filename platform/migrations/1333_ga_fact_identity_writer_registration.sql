-- 1333_ga_fact_identity_writer_registration.sql
--
-- Suvarna (SS-approved design; FIX1, 2026-10-08): make `ga_fact_identity` a REAL registered build asset so the Fact Identity Index
-- (public.chart_fact_identity, migration 552) can never again be silently emptied by the chart_facts FK cascade without anything
-- re-creating it. Registry + DAG + grant only; the writer is `pipeline/orchestrator/writers/ga_fact_identity.py` (same PR).
-- Three effects, ONE transaction:
--   (1) ga_fact_identity:  has_writer false -> true,  depends_on '{}' -> the 12 ga_* assets that write chart_facts,
--                          english_description rewritten (it said "NOT a built asset ... hand-run script").
--   (2) bo_pratijna:       depends_on += 'ga_fact_identity'   (ChartReaderV4 reads the index; a pratijna built while the index is
--                          empty is silently thinner: FACTID_RESTORE s.3).
--   (3) GRANT INSERT, DELETE ON public.chart_fact_identity TO data_plane_builder  (SELECT was granted by 1262).
--
-- WHY. chart_fact_identity.fact_id is `REFERENCES chart_facts(fact_id) ON DELETE CASCADE`. Every ga_* writer that replaces its
-- chart_facts rows (delete-then-insert) cascades the delete into the index. 1262 registered the asset with has_writer=false because
-- the only producer was the hand-run script G-IDX; its own header and the script header both said a later chart_facts rebuild empties
-- the index and nothing re-creates it. That is exactly what happened to the canonical chart after the forced rebuild (index 133,832
-- rows -> 0; see POST/FACTID_RESTORE.md). The FK cascade is DELIBERATELY KEPT: it is what keeps the cache honest (a row can never
-- point at a fact that no longer exists). The fix is to give the index an owner in the DAG that runs AFTER every chart_facts writer.
--
-- UPSTREAM EDGES (depends_on of ga_fact_identity, sorted): every registered ga_* writer whose code INSERTs/DELETEs chart_facts rows
-- (static scan of ga_writers/*.py and pipeline/orchestrator/writers/ga_*.py for replace_prior_chart_facts / INSERT INTO chart_facts /
-- DELETE FROM chart_facts, 2026-10-08):
--     ga_ayurdaya, ga_condition, ga_dashas, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive,
--     ga_sensitive_degree, ga_strength, ga_structural, ga_vichara                                         (12)
-- (ga_vichara writes the daridra dosha_label chart_facts row through the lazily imported helper ga_writers/ga_daridra_postpass.py,
-- called from ga_vichara_writer.py; a top-level import scan misses it, a scan following lazy imports finds it)
-- NOT edges (they read chart_facts or write other tables, they cannot cascade the index): ga_vargas (chart_divisionals), ga_yoga
-- (ga_yoga_firings), ga_medical, ga_prashna, ga_tajaka, ga_transit_anchors, ga_vastu. All 12 listed ids
-- are checked below to exist, be active, be per_chart and have a writer (a partial registry raises; the "dependency trap").
-- Acyclic by construction (ga_fact_identity has no dependents until bo_pratijna) and re-proved by a recursive CTE below.
--
-- STALING EFFECT (verified against the production trigger definition, read-only, 2026-10-08):
--     CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
--       integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table ON public.asset_registry
--       FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*) EXECUTE FUNCTION nirmana_invalidate_registry_receipts()
--   and the function body is `UPDATE asset_freshness SET freshness_state='stale', reasons += 'registry_changed', observed_at=now()
--   WHERE asset_id = NEW.asset_id`. This migration changes trigger columns of exactly TWO registry rows:
--     * ga_fact_identity (depends_on, has_writer): marks its asset_freshness row(s) stale. Production holds 0 such rows today
--       (the asset was never built), so that UPDATE is a no-op in effect.
--     * bo_pratijna (depends_on): marks its asset_freshness row STALE (production: 1 row, currently 'fresh'). bo_pratijna therefore
--       NEEDS A RE-RUN after this lands (the first ga_fact_identity run happens only when SS says, then bo_pratijna is rebuilt on top
--       of the restored index). Nothing else is staled: the trigger is per row, the function does not walk dependents, and no other
--       asset's trigger column is touched. asset_throughput (build state) is not touched by this migration.
--   count_sql, integrity_check_sql, health_probe, target_floor, scope, asset_kind/asset_type, is_active, target_table, sort_order,
--   natural_key_partition and every other registry column are UNCHANGED. english_description is not a trigger column.
--
-- OUTPUT DIGEST SPEC (a fourth, small effect, same transaction): one reviewed row in asset_output_digest_specs for ga_fact_identity, appended at the end of this
-- file (INSERT ... ON CONFLICT (asset_id, spec_sha256) DO NOTHING; the table's one-current-spec unique index means a different current spec would fail the
-- migration, and production holds none today, read 2026-10-08). WHY: an active relational producer with no reviewed spec makes the capability-estate census
-- generator refuse, and without a spec every rebuild writes an UNKNOWN output digest (fail-open: always "changed"). The spec digests the chart's index rows:
--   key columns   chart_id, fact_id  (fact_id is the primary key; a build-free sha256 of the fact's natural key since the S-L1 id change)
--   value columns fact_id, chart_id, entity_kind, graha_code, graha_code_secondary, house_num, house_num_secondary, varga_id, sign_num, parse_rule, parsed_from
--   EXCLUDED      build_id (the chart_facts generation the row was derived from; varies per rebuild) and computed_at (DB now())
--   scope         where chart_id = the canonical chart, the same pinning every other reviewed spec uses
-- spec_sha256 is the sidecar's own canonical_digest(spec) (pipeline/orchestrator/provenance.py), re-computed and re-loaded through the production
-- loader by the tests. It is NOT a trigger column of asset_registry and stales nothing. natural_key_partition (a trigger column) is deliberately NOT set.
--
-- OTHER CONSEQUENCES OF THE TWO EDGE EDITS (stated, not changed here):
--   * HARD DEPENDENCY GATE (asset_runner.deps_unsatisfied, enforce mode): every declared dep must be asset_throughput.state 'lit' AND its latest
--     asset_freshness 'fresh'. bo_pratijna now declares ga_fact_identity, which has NEVER been built (no asset_throughput row), so bo_pratijna is
--     blocked until ga_fact_identity has been built once; and while bo_pratijna is stale (above) its direct dependents ka_avadhi, ka_kshetra,
--     ka_taranga, ka_yojaka, mi_darshana (read from production 2026-10-08) are blocked by the same gate (ka_yojaka's freshness row is already
--     stale today). Correct order after apply: build ga_fact_identity (runs after the 12 chart_facts writers), then re-run bo_pratijna.
--   * NIRMANA MONITOR: ga_fact_identity becomes an ordinary denominator asset (execution obligation `build`; the N-141 writer-less exclusion is
--     REMOVED in the same PR, its end condition (a)), and bo_pratijna's dependency set changes. A definition frozen before this migration therefore
--     reads as drift (127 vs 128 assets; `plan_adaptation_required` for bo_pratijna), exactly as for migrations 1210/1253, until a successor
--     definition includes the asset. That is an SS decision, not made here.
--   * WRITER-GAP PRE-FLIGHT (runner._check_writer_registry_gaps, ORCHESTRATOR_WRITER_GAP_CHECK=enforce by default): a writer registered in code
--     whose registry row has has_writer=false fails EVERY run. The code and this migration therefore ship together: the deploy workflow runs the
--     migrate job first and every service `needs: [migrate]`. If this migration refuses (an active build run) the release is blocked, not
--     half-applied: merge ONLY when no build run is planned/running/paused (HELD, NOT armed).
--   * SEED: asset_registry_seed.ts gains a ga_fact_identity row (the writer / seed three-way guard in test_has_writer_completeness requires one for every
--     registered writer) and bo_pratijna's seed depends_on gains the edge. depends_on / has_writer / count_sql of an EXISTING registry row are
--     migration-governed (the seed upsert preserves them), so a re-seed of production changes nothing about this asset except text columns that already
--     equal the post-1333 row. The seed therefore carries the elevation denominator 128 -> 129 (pinned in asset_registry_seed_dag_parity.test.ts);
--     the E6.3 DRAFT level map deliberately does not level-map it (R.POST_DRAFT_SEED_ACTIVE; the J1 freeze re-derives from the live export).
--
-- GRANT. data_plane_builder: INSERT, DELETE on public.chart_fact_identity (SELECT is 1262's). No UPDATE (the writer is
-- delete-then-insert, N.3), no TRUNCATE/REFERENCES/TRIGGER, no column grant, no GRANT OPTION, no role membership, NOT PUBLIC, no
-- schema-wide ALL TABLES, no REVOKE. The table has a text primary key and NO sequence or identity column, so no sequence grant is
-- needed. FK-side inserts check chart_facts as the owner of chart_facts (PostgreSQL RI behaviour), so the builder needs no extra
-- privilege on chart_facts (it already holds SELECT/arwd there); the disposable-PostgreSQL test of this file proves the insert
-- works under the real role layout.
--   OWNER: pg_class.relowner of public.chart_fact_identity = amjis_app (1262's catalog finding), the role migrate.ts authenticates as,
--   so this is a ROUTINE migration (the owner issues the GRANT). A guard raises BEFORE any change if the executing role cannot act as the
--   owner, because a GRANT by a non-owner is only a WARNING in PostgreSQL and would leave the migration green with nothing granted.
--
-- GUARDS (raise, never skip): role data_plane_builder exists; asset_registry, chart_facts, build_runs, chart_fact_identity are ordinary
-- tables in public; NO build_runs row is active (planned / running / paused: a DAG change mid-run is unsafe); ga_fact_identity exists and
-- is EITHER exactly the 1262 shape (has_writer false, depends_on '{}') OR already exactly the post-1333 shape (re-run = no-op); the 12
-- upstream assets exist, are active, per_chart, has_writer; bo_pratijna, when present, is active and per_chart.
-- POST-CHECKS (P2 rule: a WARN-only GRANT counts as failure): builder holds SELECT, INSERT, DELETE and none of UPDATE / TRUNCATE /
-- REFERENCES / TRIGGER (table- or column-level); both registry rows read back in the intended shape; no other asset_registry row was
-- written by this transaction; no dependency cycle through the two edited assets.
--
-- CLEAR / INVALIDATION (companion TypeScript in this PR, not SQL): `assetClearSpec.ts` EXPLICIT_CLEAR_OPS['ga_fact_identity'] flips from
-- null to a real spec (DELETE ... WHERE chart_id = $1; the index is a rebuildable cache and a build now restores it), and the N-141
-- staged-index exclusion in nirmana-elevation/definitions.ts is removed (its END CONDITION (a): the asset gained a writer).
--
-- NOT RUN BY THIS MIGRATION: no chart row is read or written; ga_fact_identity is NOT built here. The first run happens only when SS
-- says.
--
-- LOCK TIMEOUT (pattern 1218, 1255, 1262): the first statement is `SET LOCAL lock_timeout = '5s'` so a blocked migrate job fails fast.
-- ROLLBACK NOTE: never REVOKE or DELETE. To undo for real, author a new reviewed migration against the then-current state (a revert
-- would set has_writer=false, depends_on back to '{}', remove 'ga_fact_identity' from bo_pratijna.depends_on and leave the grants,
-- which are harmless); doing so stales the same two rows again.
-- VERIFICATION AFTER APPLY is by production structure, not the deploy log (Trap 103):
--   SELECT asset_id, has_writer, depends_on FROM asset_registry WHERE asset_id IN ('ga_fact_identity','bo_pratijna');
--   SELECT has_table_privilege('data_plane_builder','public.chart_fact_identity', p) FROM unnest(ARRAY['SELECT','INSERT','DELETE','UPDATE']) p;
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $mig$
DECLARE
    v_asset          constant text   := 'ga_fact_identity';
    v_consumer       constant text   := 'bo_pratijna';
    v_deps           constant text[] := ARRAY[
        'ga_ayurdaya', 'ga_condition', 'ga_dashas', 'ga_nakshatra', 'ga_panchanga', 'ga_positions',
        'ga_sade_sati', 'ga_sensitive', 'ga_sensitive_degree', 'ga_strength', 'ga_structural', 'ga_vichara'
    ];
    v_description    constant text   :=
        'Derived index of chart_facts identity (graha / house / varga / sign / pair) parsed from fact_subject and fact_key by the single deterministic parser brahmagyan/fact_identity_parser.py (migration 552). Built per chart by the registered writer ga_fact_identity (migration 1333) AFTER every ga_* asset that writes chart_facts, because chart_fact_identity.fact_id is ON DELETE CASCADE from chart_facts: delete-then-insert for the chart, then the corrected G-IDX check (rows == parsed, parsed + identity_free + gap == total, gap == 0, coverage, reason set) is fatal. Read by the L2 Bodha identity path (ChartReaderV4 -> bo_pratijna). Rebuildable from chart_facts alone.';
    v_old_count_sql  constant text   := 'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1';
    tbl              text;
    rel              regclass;
    kind             "char";
    owner_oid        oid;
    n_active         integer;
    n_ok             integer;
    n_other          integer;
    missing          text;
    cyc              text;
    extra            text;
    p                text;
    cur_has_writer   boolean;
    cur_deps         text[];
    cur_consumer     text[];
    consumer_exists  boolean;
BEGIN
    -- ---------------------------------------------------------------- guards
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        RAISE EXCEPTION '1333: role data_plane_builder does not exist';
    END IF;
    FOREACH tbl IN ARRAY ARRAY['asset_registry', 'chart_facts', 'build_runs', 'chart_fact_identity'] LOOP
        rel := to_regclass(format('public.%I', tbl));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1333: public.% does not exist', tbl;
        END IF;
        SELECT relkind INTO kind FROM pg_class WHERE oid = rel;
        IF kind NOT IN ('r', 'p') THEN
            RAISE EXCEPTION '1333: public.% is not an ordinary table (relkind %)', tbl, kind;
        END IF;
    END LOOP;

    SELECT count(*) INTO n_active FROM public.build_runs WHERE state IN ('planned', 'running', 'paused');
    IF n_active <> 0 THEN
        RAISE EXCEPTION '1333: % build run(s) are active (planned/running/paused); apply only with no active build', n_active;
    END IF;

    rel := 'public.chart_fact_identity'::regclass;
    SELECT relowner INTO owner_oid FROM pg_class WHERE oid = rel;
    IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN
        RAISE EXCEPTION '1333: current_user % cannot act as the owner (%) of public.chart_fact_identity; a grant by a non-owner is only a WARNING, so this migration refuses. Route the grant through the owner-path package.',
            current_user, pg_get_userbyid(owner_oid);
    END IF;

    -- the registered asset must exist (1262) and be in exactly one of the two known shapes
    SELECT has_writer, COALESCE(depends_on, '{}'::text[]) INTO cur_has_writer, cur_deps
      FROM public.asset_registry WHERE asset_id = v_asset;
    IF NOT FOUND THEN
        RAISE EXCEPTION '1333: asset_registry row % does not exist (migration 1262 must have registered it)', v_asset;
    END IF;
    IF NOT (
        (cur_has_writer IS FALSE AND cur_deps = '{}'::text[])
        OR (cur_has_writer IS TRUE AND (SELECT array_agg(x ORDER BY x) FROM unnest(cur_deps) x) = (SELECT array_agg(x ORDER BY x) FROM unnest(v_deps) x))
    ) THEN
        RAISE EXCEPTION '1333: % is neither the 1262 shape (has_writer false, depends_on empty) nor the 1333 shape (has_writer true, the 12 edges): has_writer=%, depends_on=%',
            v_asset, cur_has_writer, cur_deps;
    END IF;

    -- every upstream edge target exists, is active, per_chart and a writer-bearing asset (partial-registry / dependency trap)
    SELECT string_agg(d, ', ' ORDER BY d) INTO missing
      FROM unnest(v_deps) d
     WHERE NOT EXISTS (
        SELECT 1 FROM public.asset_registry r
         WHERE r.asset_id = d AND r.is_active IS TRUE AND r.scope = 'per_chart' AND r.has_writer IS TRUE
     );
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION '1333: upstream asset(s) missing, inactive, not per_chart or without a writer in asset_registry (dependency trap): %', missing;
    END IF;

    SELECT true, COALESCE(depends_on, '{}'::text[]) INTO consumer_exists, cur_consumer
      FROM public.asset_registry WHERE asset_id = v_consumer;
    IF NOT FOUND THEN
        consumer_exists := false;
        RAISE NOTICE '1333: % is not in asset_registry; its edge is carried by the seed (nothing to update)', v_consumer;
    ELSIF NOT EXISTS (SELECT 1 FROM public.asset_registry WHERE asset_id = v_consumer AND is_active IS TRUE AND scope = 'per_chart') THEN
        RAISE EXCEPTION '1333: % is not an active per_chart asset (dependency trap)', v_consumer;
    END IF;

    -- ------------------------------------------------------- registry updates (ONE statement per row; the trigger fires once per row)
    UPDATE public.asset_registry
       SET has_writer          = true,
           depends_on          = (SELECT array_agg(x ORDER BY x) FROM unnest(v_deps) x),
           english_description = v_description
     WHERE asset_id = v_asset
       AND (has_writer IS DISTINCT FROM true
            OR depends_on IS DISTINCT FROM (SELECT array_agg(x ORDER BY x) FROM unnest(v_deps) x)
            OR english_description IS DISTINCT FROM v_description);

    IF consumer_exists THEN
        UPDATE public.asset_registry
           SET depends_on = COALESCE(depends_on, '{}'::text[]) || v_asset
         WHERE asset_id = v_consumer
           AND v_asset <> ALL (COALESCE(depends_on, '{}'::text[]));
    END IF;

    -- ------------------------------------------------------- read-back: the intended shape, and ONLY these rows written
    SELECT count(*) INTO n_ok
      FROM public.asset_registry r
     WHERE r.asset_id = v_asset
       AND r.layer = 'ganita' AND r.scope = 'per_chart' AND r.is_active IS TRUE AND r.catalog_status = 'CURRENT'
       AND r.has_writer IS TRUE AND r.has_substeps IS FALSE
       AND r.target_table = 'chart_fact_identity'
       AND r.count_sql = v_old_count_sql
       AND r.depends_on = (SELECT array_agg(x ORDER BY x) FROM unnest(v_deps) x)
       AND r.english_description = v_description;
    IF n_ok <> 1 THEN
        RAISE EXCEPTION '1333: asset_registry row % does not read back in the intended shape (matching rows: %)', v_asset, n_ok;
    END IF;
    IF consumer_exists AND NOT EXISTS (
        SELECT 1 FROM public.asset_registry WHERE asset_id = v_consumer AND v_asset = ANY (depends_on)
    ) THEN
        RAISE EXCEPTION '1333: % does not carry the % edge after the update', v_consumer, v_asset;
    END IF;
    SELECT count(*) INTO n_other
      FROM public.asset_registry
     WHERE xmin = pg_current_xact_id()::xid
       AND asset_id NOT IN (v_asset, v_consumer);
    IF n_other <> 0 THEN
        RAISE EXCEPTION '1333: % other asset_registry row(s) were modified by this migration', n_other;
    END IF;

    -- ------------------------------------------------------- acyclicity through the two edited assets (recursive reachability)
    WITH RECURSIVE edges AS (
        SELECT r.asset_id AS src, d.dep
          FROM public.asset_registry r
         CROSS JOIN LATERAL unnest(COALESCE(r.depends_on, '{}'::text[])) AS d(dep)
    ),
    reach(src, node) AS (
        SELECT e.src, e.dep FROM edges e WHERE e.src IN (v_asset, v_consumer)
        UNION
        SELECT r.src, e.dep FROM reach r JOIN edges e ON e.src = r.node
    )
    SELECT string_agg(DISTINCT src, ', ' ORDER BY src) INTO cyc FROM reach WHERE src = node;
    IF cyc IS NOT NULL THEN
        RAISE EXCEPTION '1333: dependency cycle through edited asset(s): %', cyc;
    END IF;

    -- ------------------------------------------------------------------- grant (INSERT, DELETE; each skipped where already held)
    FOREACH p IN ARRAY ARRAY['INSERT', 'DELETE'] LOOP
        IF has_table_privilege('data_plane_builder', rel, p) THEN
            RAISE NOTICE '1333: data_plane_builder already holds % on public.chart_fact_identity; no-op', p;
        ELSE
            EXECUTE format('GRANT %s ON TABLE %s TO data_plane_builder', p, rel);
        END IF;
    END LOOP;

    -- Post-check: the needed privileges took effect (never trust a WARN-only no-op) and nothing broader is held (effective privileges;
    -- column-level UPDATE/REFERENCES too; not a privilege reachable only through a NOINHERIT membership; not PG17 MAINTAIN: production is 15.18).
    FOREACH p IN ARRAY ARRAY['SELECT', 'INSERT', 'DELETE'] LOOP
        IF NOT has_table_privilege('data_plane_builder', rel, p) THEN
            RAISE EXCEPTION '1333: data_plane_builder lacks % on public.chart_fact_identity after the grant', p;
        END IF;
    END LOOP;
    SELECT string_agg(q, ', ' ORDER BY q) INTO extra
      FROM unnest(ARRAY['UPDATE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']) q
     WHERE has_table_privilege('data_plane_builder', rel, q)
        OR (q IN ('UPDATE', 'REFERENCES') AND has_any_column_privilege('data_plane_builder', rel, q));
    IF extra IS NOT NULL THEN
        RAISE EXCEPTION '1333: data_plane_builder holds more than SELECT, INSERT, DELETE on public.chart_fact_identity: %', extra;
    END IF;
END
$mig$;

-- Reviewed output-digest spec (see OUTPUT DIGEST SPEC in the header). Plain tuple form on purpose: the census generator and the spec replay read it textually.
INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_fact_identity',
  '1e3ce7d4e38ab731a4f8841b5c2624d5ec697ad703363f17fab6f4df5f18fd9d',
  '{"components":[{"key_columns":["chart_id","fact_id"],"name":"chart_fact_identity","relation":"chart_fact_identity","value_columns":["fact_id","chart_id","entity_kind","graha_code","graha_code_secondary","house_num","house_num_secondary","varga_id","sign_num","parse_rule","parsed_from"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
