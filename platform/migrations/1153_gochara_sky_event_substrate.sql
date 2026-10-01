-- Migration 1153: ka_gochara sky-event substrate — convention, physical
--                 object, boundary sky events, the §6.1 CONTACT identity and
--                 its per-(chart × generation) ledger, the explicit publication
--                 seal, and the legacy-convention bridge
--                 (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§7/§10, FROZEN 2026-09-30).
--                 Round-7 per ASTRA_REVIEW_A5_1_MIGRATIONS v1_5 (N18 one chart
--                 per transaction, N19 timestamp era) on round 6 (v1_4:
--                 substrate order, seal-boundary membership invariant, finite
--                 horizons) and round 5 (v1_3: N12–N15, P2) under the
--                 steward's CORRECTED lock ruling of 2026-09-30. 1153–1157
--                 were never applied anywhere, so this is an in-place rewrite.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1153 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH platform/migrations/ and platform/supabase/migrations/ (2026-09-30:
-- the only 1153–1157 files on any head are this PR's own).
-- `npm run guard:migration-numbers` green.
--
-- ── STEWARD RULING (binding; corrected item 2 supersedes the round-4 text) ─
-- 1. NO NEW TRIGGER ON ANY EXISTING TABLE (N1, kept). The seal is written
--    EXPLICITLY by ka_gochara_seal_generation(chart, generation) from the
--    governed publication path (A5.x/A6.1) in the SAME transaction as the
--    manifest flip; it refuses 'v1'/'3.0'/'4.0'/'4.1' and anything below
--    major 5 (ka_gochara_generation_governed — numeric-major regex, never a
--    lexical comparison). Every chart-scoped table CHECKs it. See
--    "Operational assertions" below for what this family DOES add to
--    existing tables (foreign keys) — the round-4 claim of "nothing on any
--    existing table" was overstated and is withdrawn (P2).
-- 2. [steward ruling — corrected] THE GOCHARA-5 FAMILY KEYS (N12). The frozen
--    orchestrator holds its per-chart SESSION advisory lock
--    (pg_advisory_lock(hashtext(chart_id)), pipeline/orchestrator/locks.py)
--    on its MAIN connection for the whole run (runner.py ~1092–1212) while
--    every writer executes on its own WORKER connection (runner.py ~682,
--    ~753). Advisory-lock re-entrancy does not cross connections, so a
--    trigger taking the orchestrator's key on a worker would wait on the
--    scheduler forever. Triggers therefore NEVER take the orchestrator's
--    keys. They take a dedicated, transaction-scoped family key:
--      chart  : pg_advisory_xact_lock(hashtext('gochara5:chart:' || chart_id))
--      global : hashtext('gochara5:global')  (EXCLUSIVE or SHARED)
--    The orchestrator's session lock stays as it is and still prevents
--    concurrent builds of one chart; the family keys serialise worker
--    transactions, the seal function and out-of-band writers against each
--    other. READ COMMITTED only (the state read after the lock must see
--    concurrently committed rows).
-- 3. [steward ruling] DEADLOCK-FREE ORDER, FIXED AND ENFORCED (N13):
--      * chart-scoped mutating triggers take the chart family key EXCLUSIVE
--        first; if they need rule-path seal state they then take the global
--        family key SHARED (pg_advisory_xact_lock_shared);
--      * rule-path registry, seal and membership mutations take the global
--        family key EXCLUSIVE and never take a chart key;
--      * ka_gochara_seal_generation takes the chart family key EXCLUSIVE.
--    Rule mutators never wait for a chart key, so no cycle exists — and the
--    order is ENFORCED, not assumed: transaction-local markers
--    (set_config('gochara5.*', …, true)) make ka_gochara_lock_chart RAISE
--    inside a transaction that already holds the global key EXCLUSIVE, and
--    make ka_gochara_lock_global (EXCLUSIVE) RAISE inside a transaction that
--    already holds a chart key or the global key SHARED. A registry mutation
--    and a chart-scoped mutation never share a transaction.
--    TUPLE LOCKS (N13): PostgreSQL locks the target tuple BEFORE it calls a
--    BEFORE ROW trigger, so a row-level advisory lock cannot precede the
--    tuple lock. Every chart-scoped table therefore carries a BEFORE
--    UPDATE OR DELETE **statement-level** trigger
--    (ka_gochara_chart_statement_lock) that takes the chart family key for
--    every chart present in the table (ascending) before any tuple is
--    touched; refusals (insert-only tables, sealed seals, legacy
--    generations) RAISE before acquiring any FAMILY advisory lock (a
--    row-level refusal may still have waited for its tuple — that tuple
--    lock dies with the refused statement's abort/savepoint rollback and
--    can never be held INTO a family-key wait).
--    SUBSTRATE ORDER (residual N13, v1_4) [steward ruling]: the tables that
--    carry no family key of their own (sky convention, physical object, sky
--    event, contact identity, bridge — and, for a total invariant, the AV
--    declaration) are written by chart-serving transactions beside chart
--    rows, and a unique-index or tuple wait on them could otherwise be held
--    while waiting for a chart key (A holds C → waits on B's uncommitted
--    identity; B waits for C). The mixed order is therefore STRUCTURALLY
--    PROHIBITED: a BEFORE INSERT (and, on the enrichable sky-event table,
--    UPDATE) statement-level trigger (ka_gochara_substrate_chart_lock) first
--    takes the chart family key of the chart the transaction serves — the
--    key already held (gochara5.chart_locked), else the declared context
--    (set_config('gochara5.chart', <chart_id>, true)) — and REFUSES the
--    statement when the transaction has no chart context. The chart key
--    thus always precedes any substrate tuple or unique lock; the
--    registry/chart markers stay as they are (a registry transaction cannot
--    write substrate rows either — it would need a chart key).
--    ONE CHART PER TRANSACTION (N18, v1_5) [steward ruling]: a transaction
--    is BOUND to the first chart it locks (gochara5.bound_chart, written
--    only by ka_gochara_lock_chart) at the context/lock boundary, before any
--    substrate acquisition; a request for a DIFFERENT chart in the same
--    transaction is refused BEFORE another family key is requested, and a
--    substrate write whose declared context disagrees with the binding is
--    refused too. The existing canonical-only scope (D-SCOPE: every
--    chart-scoped table CHECKs chart_id = 482012f1-…) is enforced at that
--    same boundary: a non-canonical chart_id is refused before any key. So
--    no transaction can hold substrate unique/tuple locks under one chart
--    and then wait for another chart's key.
-- 3b. [steward ruling] THE SEAL BOUNDARY CARRIES THE COMPLETE MEMBERSHIP
--    INVARIANT (N16/N10): candidate records, windows and their coverage
--    partitions stay updateable before publication, and no trigger sits on
--    the legacy coverage table, so an existing window membership can become
--    inapplicable after it was validated. ka_gochara_seal_generation
--    therefore re-checks EVERY window membership of the generation
--    (contributor relation ∈ window relations_searched, same convention,
--    support intervals ⊆ window horizon — ka_gochara_membership_violations,
--    1156) and refuses the seal on any violation, exactly as it refuses
--    incompatible coverage drift.
-- 3c. [steward ruling] FINITE, AD-ERA HORIZONS ONLY (N17/N19/N14): the
--    Gochara-5 contract admits finite, bounded, non-empty horizons whose
--    every bound lies within 1000-01-01 ≤ t < 3000-01-01 UTC (AD only; our
--    horizons are 1998–2084) — never an omitted bound, never a ±infinity
--    bound, never an empty range, never a BC or out-of-range year.
--    ka_gochara_horizon_finite_ok is CHECKed on window intervals and record
--    support intervals, the coverage guards refuse a partition whose
--    completed_horizon is outside that domain, ka_gochara_coverage_facts
--    RAISES on any other input, and the drift classifier reports a partition
--    that later left the domain as `incompatible`. Within the domain the
--    ISO-8601 'YYYY-MM-DDTHH:MI:SS.USZ' encoding is a lossless bijection
--    (four-digit AD years, microsecond exact), so serialisation is exact and
--    unambiguous over the whole accepted domain.
-- 4. NO CUSTOM DEFINITION VERIFIER, NO REPLAY GUC (N4, kept): migrate.ts
--    tracks applied files by hash; a re-run is an untracked collision and
--    the gate BLOCKS it; post-apply checks are presence checks.
-- 5. DEPLOY ROUTE (N3, kept): the protected public-schema window
--    (deploy.yml `gochara_contracts_schema_migration`, exact files 1153–1157
--    in order); the general runner REFUSES them
--    (migrate.ts PROTECTED_PUBLIC_SCHEMA_MIGRATIONS).
--
-- ── Operational assertions (P2 — corrected, no overclaims) ────────────────
-- * EXISTING-TABLE EFFECTS. This family adds NO trigger, function or CHECK
--   to any existing table, but it DOES add foreign keys that reference
--   existing tables: charts(id) (seal, ledger, records, windows),
--   kala_gochara_convention(convention_id) (bridge) and
--   kala_gochara_coverage(chart_id, generation, partition_kind,
--   partition_key) (records, windows). Each FK installs PostgreSQL's
--   internal RI triggers on the referenced table and takes SHARE ROW
--   EXCLUSIVE on it while the migration transaction runs (bounded by the
--   SET LOCAL timeouts below, not eliminated). After apply, a referenced
--   charts / convention / coverage row cannot be deleted while a governed
--   row references it; kala_gochara_publication and kala_gochara_contacts
--   receive no dependency of any kind.
-- * ROUTINE REFUSAL is loud but not write-free: migrate.ts creates/backfills
--   the tracker (TRACKER DDL, sql_identity backfill) and applies every
--   pending migration numbered BEFORE 1153 before it reaches and refuses
--   1153; none of 1153–1157 is applied by that invocation.
-- * THE PROTECTED WINDOW IS PER-FILE ATOMIC, NOT FAMILY-ATOMIC: each file
--   and its ledger row commit together; a failure in, say, 1156 leaves
--   1153–1155 committed, rolls 1156 back and never attempts 1157. Recovery
--   is to re-dispatch the window: applied files are skipped by hash, the
--   failed file re-runs from its gate. `--only` refuses to jump an unapplied
--   predecessor, so the window must be dispatched with every earlier pending
--   migration already applied.
-- * The migration files are immutable once applied (CLAUDE.md §N.4); any
--   later correction is a new forward migration.
--
-- ── Transaction ownership (round-1 amendment 2, kept closed) ───────────────
-- No BEGIN/COMMIT/ROLLBACK here. platform/scripts/migrate.ts owns ONE
-- transaction around (this file + the _migrations_applied ledger insert).
--
-- ── Effective ordered gate (F8/F9, kept) ───────────────────────────────────
-- (1) pinned schema + timeouts, (2) the PREFLIGHT GATE — a DO block
-- byte-identical to preflight_1153_sky_event_substrate.sql checking real
-- preconditions only, (3) DDL, (4) presence checks.
--
-- ── The contact model (F1/F2/F4/N6, kept) ──────────────────────────────────
-- * ka_gochara_contact_identity — contact_id = hash(physical_object_id,
--   occurrence_ordinal) exactly as frozen; UNIQUE (physical_object_id,
--   occurrence_ordinal); insert-only; never deleted.
-- * ka_gochara_contact — per-(chart_id, generation) LEDGER row (PK
--   (chart_id, generation, contact_id)). N6: the solved reading (t_exact, δλ,
--   δt, precision_regime, non-placeholder solver_method) of one identity is
--   consistent across every ledger row sharing it (checked under the chart
--   family key; sufficient under the D-SCOPE single-chart CHECK).
-- * Corrections supersede a DIFFERENT identity of the SAME (body,
--   relation_kind); enrichment fills NULL/truncated fields only; sealed
--   generation: DELETE refused, INSERT (append) and enrichment permitted;
--   TRUNCATE refused everywhere.
-- * Legacy kala_gochara_contacts rows are NOT migrated (steward ruling).
-- * ka_gochara_convention_bridge maps the legacy 1081 convention vector to
--   the §6.1 sky convention for 1155's applicability guard.
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK (down-migration, dependents first; 1154–1157 before this):
--   DROP TABLE IF EXISTS ka_gochara_contact;
--   DROP TABLE IF EXISTS ka_gochara_convention_bridge;
--   DROP TABLE IF EXISTS ka_gochara_generation_seal;
--   DROP TABLE IF EXISTS ka_gochara_contact_identity;
--   DROP TABLE IF EXISTS ka_gochara_sky_event;
--   DROP TABLE IF EXISTS ka_gochara_physical_object;
--   DROP TABLE IF EXISTS ka_gochara_sky_convention;
--   DROP FUNCTION IF EXISTS ka_gochara_contact_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_contact_identity_supersede_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_supersede_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_generation_seal_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_seal_generation(uuid, text);
--   DROP FUNCTION IF EXISTS ka_gochara_generation_is_sealed(uuid, text);
--   DROP FUNCTION IF EXISTS ka_gochara_chart_statement_lock();
--   DROP FUNCTION IF EXISTS ka_gochara_substrate_chart_lock();
--   DROP FUNCTION IF EXISTS ka_gochara_global_write_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_insert_only();
--   DROP FUNCTION IF EXISTS ka_gochara_lock_global_shared();
--   DROP FUNCTION IF EXISTS ka_gochara_lock_global();
--   DROP FUNCTION IF EXISTS ka_gochara_lock_chart(uuid);
--   DROP FUNCTION IF EXISTS ka_gochara_generation_governed(text);
--   DROP FUNCTION IF EXISTS ka_gochara_horizon_finite_ok(tstzrange);
--   DROP FUNCTION IF EXISTS ka_gochara_refuse_truncate();
--   DROP FUNCTION IF EXISTS ka_gochara_finite_nonneg_ok(double precision);
--   DROP FUNCTION IF EXISTS ka_gochara_finite_ok(double precision);
--   DROP FUNCTION IF EXISTS ka_gochara_text_array_ok(text[], integer);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1153_sky_event_substrate.sql) ────────
DO $$
DECLARE
  failures text;
BEGIN
  WITH f(failure, detail) AS (
    -- (d) pinned schema + effective privileges
    SELECT 'schema_missing', 'public'
    WHERE to_regnamespace('public') IS NULL
    UNION ALL
    SELECT 'no_usage_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'USAGE')
    UNION ALL
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'CREATE')
    UNION ALL
    SELECT 'no_references_privilege', p.t
    FROM (VALUES ('public.charts'), ('public.kala_gochara_convention')) AS p(t)
    WHERE to_regclass(p.t) IS NOT NULL AND NOT has_table_privilege(p.t, 'REFERENCES')
    UNION ALL
    SELECT 'no_select_privilege', 'public.kala_gochara_publication'
    WHERE to_regclass('public.kala_gochara_publication') IS NOT NULL
      AND NOT has_table_privilege('public.kala_gochara_publication', 'SELECT')
    UNION ALL
    -- (a1) relation-namespace collisions (tables, indexes, sequences share pg_class)
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_sky_convention', 'ka_gochara_sky_convention_pkey',
                        'ka_gochara_physical_object', 'ka_gochara_physical_object_pkey',
                        'ka_gochara_physical_object_natural_uq', 'kgpo_identity_uq',
                        'ka_gochara_sky_event', 'ka_gochara_sky_event_pkey',
                        'ka_gochara_sky_event_ordinal_uq', 'kgse_supersedes_uq',
                        'ka_gochara_contact_identity', 'ka_gochara_contact_identity_pkey',
                        'ka_gochara_contact_identity_ordinal_uq', 'kgci_supersedes_uq',
                        'kgci_tuple_uq',
                        'ka_gochara_generation_seal', 'ka_gochara_generation_seal_pkey',
                        'ka_gochara_convention_bridge', 'ka_gochara_convention_bridge_pkey',
                        'ka_gochara_contact', 'ka_gochara_contact_pkey', 'kgc_reference_uq',
                        'idx_kgse_convention_time', 'idx_kgc_chart_gen', 'idx_kgc_object',
                        'idx_kgc_identity')
    UNION ALL
    -- (a2) trigger collisions, scoped to the intended table in public
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_sky_convention'
               AND t.tgname IN ('ka_gochara_sky_convention_0_chart_context',
                                'ka_gochara_sky_convention_immutable',
                                'ka_gochara_sky_convention_no_truncate'))
         OR (c.relname = 'ka_gochara_physical_object'
               AND t.tgname IN ('ka_gochara_physical_object_0_chart_context',
                                'ka_gochara_physical_object_immutable',
                                'ka_gochara_physical_object_no_truncate'))
         OR (c.relname = 'ka_gochara_sky_event'
               AND t.tgname IN ('ka_gochara_sky_event_0_chart_context',
                                'ka_gochara_sky_event_supersede_check',
                                'ka_gochara_sky_event_mutation_guard',
                                'ka_gochara_sky_event_no_truncate'))
         OR (c.relname = 'ka_gochara_contact_identity'
               AND t.tgname IN ('ka_gochara_contact_identity_0_chart_context',
                                'ka_gochara_contact_identity_supersede_check',
                                'ka_gochara_contact_identity_immutable',
                                'ka_gochara_contact_identity_no_truncate'))
         OR (c.relname = 'ka_gochara_generation_seal'
               AND t.tgname IN ('ka_gochara_generation_seal_write_guard',
                                'ka_gochara_generation_seal_no_truncate'))
         OR (c.relname = 'ka_gochara_convention_bridge'
               AND t.tgname IN ('ka_gochara_convention_bridge_0_chart_context',
                                'ka_gochara_convention_bridge_immutable',
                                'ka_gochara_convention_bridge_no_truncate'))
         OR (c.relname = 'ka_gochara_contact'
               AND t.tgname IN ('ka_gochara_contact_0_statement_lock',
                                'ka_gochara_contact_1_write_guard',
                                'ka_gochara_contact_no_truncate')) )
    UNION ALL
    -- (a3) function collisions by EXACT ARGUMENT TYPES (F8)
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_refuse_truncate',                  ARRAY[]::text[]),
            ('ka_gochara_text_array_ok',                    ARRAY['text[]','integer']),
            ('ka_gochara_finite_ok',                        ARRAY['double precision']),
            ('ka_gochara_finite_nonneg_ok',                 ARRAY['double precision']),
            ('ka_gochara_generation_governed',              ARRAY['text']),
            ('ka_gochara_horizon_finite_ok',                ARRAY['tstzrange']),
            ('ka_gochara_lock_chart',                       ARRAY['uuid']),
            ('ka_gochara_lock_global',                      ARRAY[]::text[]),
            ('ka_gochara_lock_global_shared',               ARRAY[]::text[]),
            ('ka_gochara_insert_only',                      ARRAY[]::text[]),
            ('ka_gochara_global_write_guard',               ARRAY[]::text[]),
            ('ka_gochara_chart_statement_lock',             ARRAY[]::text[]),
            ('ka_gochara_substrate_chart_lock',             ARRAY[]::text[]),
            ('ka_gochara_generation_is_sealed',             ARRAY['uuid','text']),
            ('ka_gochara_seal_generation',                  ARRAY['uuid','text']),
            ('ka_gochara_generation_seal_guard',            ARRAY[]::text[]),
            ('ka_gochara_sky_event_supersede_guard',        ARRAY[]::text[]),
            ('ka_gochara_sky_event_guard',                  ARRAY[]::text[]),
            ('ka_gochara_contact_identity_supersede_guard', ARRAY[]::text[]),
            ('ka_gochara_contact_guard',                    ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- (b1) in-database parents exist (publication is READ by the seal path only)
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('kala_gochara_publication'), ('kala_gochara_convention')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    -- (b2) parent columns exist with the expected types (expected side named)
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                   'id',           'uuid'),
                 ('kala_gochara_publication', 'manifest_id',  'uuid'),
                 ('kala_gochara_publication', 'chart_id',     'uuid'),
                 ('kala_gochara_publication', 'generation',   'text'),
                 ('kala_gochara_publication', 'status',       'text'),
                 ('kala_gochara_convention',  'convention_id','text')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified against pg_constraint
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                   ARRAY['id']),
                 ('kala_gochara_publication', ARRAY['manifest_id']),
                 ('kala_gochara_publication', ARRAY['chart_id','generation']),
                 ('kala_gochara_convention',  ARRAY['convention_id'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    -- (c) ledger lookup, wildcard-safe (starts_with, not LIKE)
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1153_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1153 BLOCKED — migration 1153 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1153: all checks passed';
END;
$$;

-- ── 0. Shared helpers (this family; reused by 1154–1157) ──────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_refuse_truncate()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION 'TRUNCATE refused on % (GOCHARA_DESIGN_SPECS_v1_4 §6.1 publication immutability; CLAUDE.md §N.3): TRUNCATE is generation-blind and bypasses the row guards — rebuild a CANDIDATE generation with a scoped DELETE', TG_TABLE_NAME;
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_text_array_ok(a text[], p_min integer)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT a IS NOT NULL
     AND COALESCE(cardinality(a), 0) >= p_min
     AND NOT EXISTS (SELECT 1 FROM unnest(a) e WHERE e IS NULL OR btrim(e) = '');
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_finite_ok(x double precision)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT x IS NULL
      OR (NOT (x = 'NaN'::double precision)
          AND x > '-infinity'::double precision
          AND x < 'infinity'::double precision);
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_finite_nonneg_ok(x double precision)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT x IS NULL
      OR (NOT (x = 'NaN'::double precision)
          AND x >= 0
          AND x < 'infinity'::double precision);
$$;

-- The generation contract boundary (ruling 1 / N1): governed iff major >= 5.
-- 'v1', '3.0', '4.0' and the candidate-only '4.1' (D-41) are never governed.
CREATE OR REPLACE FUNCTION public.ka_gochara_generation_governed(g text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT g IS NOT NULL AND g ~ '^([5-9]|[1-9][0-9]+)\.[0-9]+$';
$$;

-- The accepted horizon domain (ruling 3c / N17 / N19): finite, bounded,
-- non-empty, every bound within 1000-01-01 ≤ t < 3000-01-01 UTC (AD only).
-- Refuses NULL, 'empty', an omitted bound, a ±infinity bound (implied by the
-- era bounds), a BC bound and any year outside [1000, 3000).
CREATE OR REPLACE FUNCTION public.ka_gochara_horizon_finite_ok(h tstzrange)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT h IS NOT NULL
     AND NOT isempty(h)
     AND NOT lower_inf(h) AND NOT upper_inf(h)
     AND lower(h) >= '1000-01-01 00:00:00+00'::timestamptz
     AND upper(h) <  '3000-01-01 00:00:00+00'::timestamptz;
$$;

-- ── 0b. The Gochara-5 family keys and the ENFORCED order (rulings 2–3) ────
-- Transaction-local markers (set_config(..., true)) record which class of
-- key this transaction holds so the fixed order is enforced, not assumed.

CREATE OR REPLACE FUNCTION public.ka_gochara_lock_chart(p_chart_id uuid)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF current_setting('transaction_isolation') <> 'read committed' THEN
    RAISE EXCEPTION 'ka_gochara writes require READ COMMITTED (transaction_isolation is %): the seal/membership state read after the family lock must see concurrently committed transactions (N2)',
      current_setting('transaction_isolation');
  END IF;
  IF p_chart_id IS NULL THEN
    RAISE EXCEPTION 'ka_gochara_lock_chart: chart_id is NULL';
  END IF;
  -- ONE CHART PER TRANSACTION (N18): refuse a different chart BEFORE requesting another key
  IF COALESCE(current_setting('gochara5.bound_chart', true), '') NOT IN ('', p_chart_id::text) THEN
    RAISE EXCEPTION 'ka_gochara lock-order violation (steward ruling B / N18): this transaction is bound to chart % and may not take the family key of chart % — a transaction serves ONE chart (substrate unique/tuple locks taken under one chart can never be held into another chart''s key wait)',
      current_setting('gochara5.bound_chart', true), p_chart_id;
  END IF;
  -- canonical-only scope (D-SCOPE), enforced at the lock boundary before any key
  IF p_chart_id <> '482012f1-710e-4a25-994a-93821f5871aa'::uuid THEN
    RAISE EXCEPTION 'ka_gochara_lock_chart refused: chart % is not governed by the Gochara-5 contract (D-SCOPE: the canonical chart 482012f1-710e-4a25-994a-93821f5871aa only — every chart-scoped table CHECKs it, and no family key is issued for any other chart)',
      p_chart_id;
  END IF;
  IF COALESCE(current_setting('gochara5.global_exclusive', true), '') = 'on' THEN
    RAISE EXCEPTION 'ka_gochara lock-order violation (steward ruling B / N13): this transaction already holds the gochara5 GLOBAL family key EXCLUSIVE (a rule-path registry/seal/membership mutation) and may not take a chart family key — registry mutations and chart-scoped mutations never share a transaction';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext('gochara5:chart:' || p_chart_id::text)::bigint);
  PERFORM set_config('gochara5.chart_locked', 'on', true);
  PERFORM set_config('gochara5.chart', p_chart_id::text, true);         -- the declared context
  PERFORM set_config('gochara5.bound_chart', p_chart_id::text, true);   -- the binding (N18): written here only
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_lock_global()
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF current_setting('transaction_isolation') <> 'read committed' THEN
    RAISE EXCEPTION 'ka_gochara writes require READ COMMITTED (transaction_isolation is %): the seal/membership state read after the family lock must see concurrently committed transactions (N2/N5)',
      current_setting('transaction_isolation');
  END IF;
  IF COALESCE(current_setting('gochara5.chart_locked', true), '') = 'on'
     OR COALESCE(current_setting('gochara5.global_shared', true), '') = 'on' THEN
    RAISE EXCEPTION 'ka_gochara lock-order violation (steward ruling B / N13): this transaction already holds a chart family key (a chart-scoped mutation) and may not take the GLOBAL family key EXCLUSIVE — rule-path registry/seal/membership mutations never share a transaction with chart-scoped mutations';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext('gochara5:global')::bigint);
  PERFORM set_config('gochara5.global_exclusive', 'on', true);
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_lock_global_shared()
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF current_setting('transaction_isolation') <> 'read committed' THEN
    RAISE EXCEPTION 'ka_gochara writes require READ COMMITTED (transaction_isolation is %)',
      current_setting('transaction_isolation');
  END IF;
  PERFORM pg_advisory_xact_lock_shared(hashtext('gochara5:global')::bigint);
  PERFORM set_config('gochara5.global_shared', 'on', true);
END;
$$;

COMMENT ON FUNCTION public.ka_gochara_lock_chart(uuid) IS
  'Takes the Gochara-5 per-chart FAMILY key (hashtext(''gochara5:chart:''||chart_id), '
  'transaction-scoped, EXCLUSIVE) — never the orchestrator''s session key, which lives on '
  'the scheduler''s main connection while writers run on worker connections (N12). Binds the '
  'transaction to ONE chart (N18): a different chart is refused before any other key is '
  'requested; only the canonical chart is governed (D-SCOPE). Refuses a transaction that '
  'already holds the global family key EXCLUSIVE (enforced order, N13). READ COMMITTED only.';
COMMENT ON FUNCTION public.ka_gochara_lock_global() IS
  'Takes the Gochara-5 GLOBAL family key (hashtext(''gochara5:global''), transaction-scoped) '
  'EXCLUSIVE — rule-path registry, seal and membership mutations only. Refuses a '
  'transaction that already holds a chart family key or the global key SHARED (enforced '
  'order, N13). READ COMMITTED only.';
COMMENT ON FUNCTION public.ka_gochara_lock_global_shared() IS
  'Takes the Gochara-5 GLOBAL family key SHARED — chart-scoped writers reading rule-path '
  'seal state, always AFTER their chart family key. Blocks only behind a registry mutation.';

-- Insert-only guard for chart-independent, constraint-guarded tables (NO
-- family key — UNIQUE/FK constraints serialise what needs serialising).
CREATE OR REPLACE FUNCTION public.ka_gochara_insert_only()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION '% is insert-only (GOCHARA_DESIGN_SPECS_v1_4 %): % not permitted; a change is a NEW row (new id / new version / new convention), never an edit',
    TG_TABLE_NAME, COALESCE(TG_ARGV[0], '§6.1'), TG_OP;
END;
$$;

-- Registry-class guard (rule-path registry, seal, membership UPDATE/DELETE):
-- a refusal RAISES before any FAMILY advisory lock is acquired (N13); an
-- INSERT takes the global family key EXCLUSIVE.
CREATE OR REPLACE FUNCTION public.ka_gochara_global_write_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION '% is insert-only (GOCHARA_DESIGN_SPECS_v1_4 %): % not permitted; a change is a NEW row (new version), never an edit',
      TG_TABLE_NAME, COALESCE(TG_ARGV[0], '§2.1'), TG_OP;
  END IF;
  PERFORM public.ka_gochara_lock_global();
  RETURN NEW;
END;
$$;

-- BEFORE UPDATE OR DELETE, FOR EACH STATEMENT, on every chart-scoped table:
-- runs before PostgreSQL locks any target tuple (ExecBRUpdateTriggers /
-- ExecBRDeleteTriggers lock the tuple before ROW triggers — N13), so the
-- family key always precedes the tuple lock. Every chart present in the
-- table is locked in ascending order (one chart under the D-SCOPE CHECK).
CREATE OR REPLACE FUNCTION public.ka_gochara_chart_statement_lock()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE c uuid;
BEGIN
  -- distinct chart_ids via a loose index walk (every chart-scoped table has a
  -- chart_id-leading index), ascending — no full scan per statement
  FOR c IN EXECUTE format(
    'WITH RECURSIVE w AS (
       (SELECT chart_id FROM public.%1$I ORDER BY chart_id LIMIT 1)
       UNION ALL
       SELECT (SELECT t.chart_id FROM public.%1$I t WHERE t.chart_id > w.chart_id ORDER BY t.chart_id LIMIT 1)
       FROM w WHERE w.chart_id IS NOT NULL)
     SELECT chart_id FROM w WHERE chart_id IS NOT NULL ORDER BY chart_id', TG_TABLE_NAME) LOOP
    PERFORM public.ka_gochara_lock_chart(c);
  END LOOP;
  RETURN NULL;
END;
$$;

-- BEFORE INSERT (and UPDATE where enrichment is permitted), FOR EACH
-- STATEMENT, on every table that carries no family key of its own (ruling
-- 3, SUBSTRATE ORDER): the chart family key of the chart this transaction
-- serves is taken BEFORE any substrate unique-index or tuple lock. The chart
-- is the one already locked (gochara5.chart_locked → nothing to do), else
-- the declared context gochara5.chart; a transaction with neither is
-- refused — the mixed order cannot occur.
CREATE OR REPLACE FUNCTION public.ka_gochara_substrate_chart_lock()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE ctx text; bound text;
BEGIN
  ctx := current_setting('gochara5.chart', true);
  IF COALESCE(current_setting('gochara5.chart_locked', true), '') = 'on' THEN
    bound := current_setting('gochara5.bound_chart', true);
    IF ctx IS NOT NULL AND ctx <> '' AND ctx IS DISTINCT FROM bound THEN
      RAISE EXCEPTION '% write refused (steward ruling B / N18): this transaction is bound to chart % but declares context % — a transaction serves ONE chart; the substrate write would otherwise run under another chart''s key',
        TG_TABLE_NAME, bound, ctx;
    END IF;
    RETURN NULL;   -- the bound chart's key already precedes this statement
  END IF;
  IF ctx IS NULL OR ctx = '' THEN
    RAISE EXCEPTION '% write refused (steward ruling B / N13 substrate order): no chart context — a transaction that writes substrate, identity, bridge or declaration rows must first take the chart family key of the chart it serves (SELECT ka_gochara_lock_chart(chart_id)) or declare it (set_config(''gochara5.chart'', chart_id, true)), so the chart key always precedes any substrate tuple or unique-index lock',
      TG_TABLE_NAME;
  END IF;
  PERFORM public.ka_gochara_lock_chart(ctx::uuid);
  RETURN NULL;
END;
$$;

-- ── 1. Convention (§6.1) — constraint-guarded, insert-only, no family key ─

CREATE TABLE IF NOT EXISTS public.ka_gochara_sky_convention (
  convention_id        TEXT PRIMARY KEY,
  ephemeris_generation TEXT NOT NULL,
  ayanamsha            TEXT NOT NULL,
  node_convention      TEXT NOT NULL,
  grid                 TEXT NOT NULL,
  method_version       TEXT NOT NULL,
  domain_start         TIMESTAMPTZ NOT NULL,
  domain_end           TIMESTAMPTZ NOT NULL,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgsc_domain_ordered_ck CHECK (domain_start < domain_end)
);

COMMENT ON TABLE public.ka_gochara_sky_convention IS
  'Sky-event substrate convention (GOCHARA_DESIGN_SPECS_v1_4 §6.1): one substrate per '
  '(ephemeris/convention generation, ayanāṃśa, node convention, grid, method version) '
  'plus the ordinal domain (domain_start/domain_end). A backward partition is a new '
  'convention_id. Insert-only; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_sky_convention_0_chart_context ON public.ka_gochara_sky_convention;
CREATE TRIGGER ka_gochara_sky_convention_0_chart_context
  BEFORE INSERT ON public.ka_gochara_sky_convention
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_substrate_chart_lock();
DROP TRIGGER IF EXISTS ka_gochara_sky_convention_immutable ON public.ka_gochara_sky_convention;
CREATE TRIGGER ka_gochara_sky_convention_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_sky_convention
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1/§7.2 inv 4');
DROP TRIGGER IF EXISTS ka_gochara_sky_convention_no_truncate ON public.ka_gochara_sky_convention;
CREATE TRIGGER ka_gochara_sky_convention_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_sky_convention
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 2. Physical object (§6.1) ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_physical_object (
  physical_object_id  UUID PRIMARY KEY,
  body                TEXT NOT NULL,
  relation_kind       TEXT NOT NULL,
  canonical_target    TEXT NOT NULL,
  convention_id       TEXT NOT NULL REFERENCES public.ka_gochara_sky_convention(convention_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgpo_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgpo_relation_kind_ck CHECK (relation_kind IN
    ('residence','aspect','conjunction',
     'sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant')),
  CONSTRAINT kgpo_target_form_ck CHECK (
    canonical_target ~ '^point:([0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9])(\.[0-9]+)?$'
    OR canonical_target ~ '^span:[a-z0-9_]+$'
    OR canonical_target ~ '^star:([1-9]|1[0-9]|2[0-7])$'),
  CONSTRAINT ka_gochara_physical_object_natural_uq
    UNIQUE (body, relation_kind, canonical_target, convention_id),
  CONSTRAINT kgpo_identity_uq
    UNIQUE (physical_object_id, body, relation_kind, convention_id)
);

COMMENT ON TABLE public.ka_gochara_physical_object IS
  'Canonical physical object (GOCHARA_DESIGN_SPECS_v1_4 §6.1): label-independent physical '
  'identity; one object per (body, relation_kind, canonical_target, convention_id). '
  'Insert-only; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_physical_object_0_chart_context ON public.ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_0_chart_context
  BEFORE INSERT ON public.ka_gochara_physical_object
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_substrate_chart_lock();
DROP TRIGGER IF EXISTS ka_gochara_physical_object_immutable ON public.ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_physical_object
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1 publication immutability');
DROP TRIGGER IF EXISTS ka_gochara_physical_object_no_truncate ON public.ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_physical_object
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 3. Sky event — BOUNDARY EVENTS ONLY (§6.1 + §7.1) ─────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_sky_event (
  event_id            UUID PRIMARY KEY,
  physical_object_id  UUID NOT NULL,
  convention_id       TEXT NOT NULL,
  body                TEXT NOT NULL,
  event_kind          TEXT NOT NULL,
  occurrence_ordinal  INTEGER NOT NULL,
  t_exact             TIMESTAMPTZ,
  longitude           DOUBLE PRECISION,
  solver_method       TEXT NOT NULL,
  delta_lambda        REAL,
  delta_t             REAL,
  precision_regime    TEXT,
  coverage            JSONB NOT NULL,
  supersedes_event_id UUID REFERENCES public.ka_gochara_sky_event(event_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_gochara_sky_event_object_fk
    FOREIGN KEY (physical_object_id, body, event_kind, convention_id)
    REFERENCES public.ka_gochara_physical_object (physical_object_id, body, relation_kind, convention_id),
  CONSTRAINT kgse_event_kind_ck CHECK (event_kind IN
    ('sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant')),
  CONSTRAINT kgse_body_domain_ck CHECK (body IN
    ('sun','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgse_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT ka_gochara_sky_event_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal),
  CONSTRAINT kgse_solver_method_ck CHECK (solver_method IN
    ('arc_index_bracket','swiss_refined','clipped_truncated')),
  CONSTRAINT kgse_coverage_shape_ck
    CHECK (jsonb_typeof(coverage) = 'object'
           AND coverage ? 'truncated'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
  CONSTRAINT kgse_t_exact_iff_truncated_ck
    CHECK ((t_exact IS NULL) = (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgse_truncated_method_ck
    CHECK ((coverage ->> 'truncated')::boolean = (solver_method = 'clipped_truncated')),
  CONSTRAINT kgse_exact_precision_ck
    CHECK (t_exact IS NULL
           OR (longitude IS NOT NULL AND delta_lambda IS NOT NULL
               AND delta_t IS NOT NULL AND precision_regime IS NOT NULL)),
  CONSTRAINT kgse_longitude_range_ck
    CHECK (longitude IS NULL OR (longitude >= 0 AND longitude < 360)),
  CONSTRAINT kgse_uncertainty_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(delta_lambda) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(delta_t) IS TRUE),
  CONSTRAINT kgse_station_refined_ck
    CHECK (event_kind <> 'station' OR solver_method = 'swiss_refined'),
  CONSTRAINT kgse_no_self_supersede_ck
    CHECK (supersedes_event_id IS NULL OR supersedes_event_id <> event_id),
  CONSTRAINT kgse_supersedes_uq UNIQUE (supersedes_event_id)
);

COMMENT ON TABLE public.ka_gochara_sky_event IS
  'Boundary-event substrate (GOCHARA_DESIGN_SPECS_v1_4 §6.1, §7.1): the five boundary '
  'kinds ONLY. event_id = hash(physical_object_id, occurrence_ordinal). Correction: a NEW '
  'event of the same (body, kind) under a corrected target or a new convention, linked by '
  'supersedes_event_id (chain; never self). DELETE forbidden; UPDATE may only fill NULL '
  'fields (truncated→exact flip); TRUNCATE refused. Constraint-guarded (UNIQUE/FK); a '
  'write first takes the chart family key of the chart the transaction serves (substrate '
  'order).';

CREATE OR REPLACE FUNCTION public.ka_gochara_sky_event_supersede_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  pred_body text; pred_kind text;
BEGIN
  IF NEW.supersedes_event_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT p.body, p.event_kind INTO pred_body, pred_kind
  FROM public.ka_gochara_sky_event p
  WHERE p.event_id = NEW.supersedes_event_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_sky_event supersede edge invalid (§6.1): predecessor % does not exist',
      NEW.supersedes_event_id;
  END IF;
  IF pred_body <> NEW.body OR pred_kind <> NEW.event_kind THEN
    RAISE EXCEPTION 'ka_gochara_sky_event supersede edge invalid (§6.1 correction): predecessor % is (%, %) but the correction is (%, %) — a correction re-solves the SAME body and kind under a corrected target or a new convention (§7.2 inv 4)',
      NEW.supersedes_event_id, pred_body, pred_kind, NEW.body, NEW.event_kind;
  END IF;
  -- "superseded at most once": the named message for the common case; the
  -- race-safe guarantee is kgse_supersedes_uq (no family key on this table)
  IF EXISTS (SELECT 1 FROM public.ka_gochara_sky_event s
             WHERE s.supersedes_event_id = NEW.supersedes_event_id) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event % is already superseded (§6.1): supersession history is a chain, never a tree',
      NEW.supersedes_event_id;
  END IF;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_sky_event_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE flip boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'ka_gochara_sky_event is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1): DELETE forbidden; a correction retires an event via a superseding row, never by deletion';
  END IF;
  flip := OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
      AND (OLD.coverage ->> 'truncated')::boolean
      AND NOT (NEW.coverage ->> 'truncated')::boolean
      AND OLD.solver_method = 'clipped_truncated'
      AND NEW.solver_method <> 'clipped_truncated'
      AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated');
  IF NEW.event_id            <> OLD.event_id
     OR NEW.physical_object_id <> OLD.physical_object_id
     OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
     OR NEW.convention_id      <> OLD.convention_id
     OR NEW.body               <> OLD.body
     OR NEW.event_kind         <> OLD.event_kind THEN
    RAISE EXCEPTION 'ka_gochara_sky_event identity fields are immutable (§6.1): a change to id/ordinal/target/convention is a correction — mint a new id with a supersedes edge, never UPDATE';
  END IF;
  IF (OLD.t_exact IS NOT NULL AND NEW.t_exact IS DISTINCT FROM OLD.t_exact)
     OR (OLD.longitude IS NOT NULL AND NEW.longitude IS DISTINCT FROM OLD.longitude)
     OR (OLD.delta_lambda IS NOT NULL AND NEW.delta_lambda IS DISTINCT FROM OLD.delta_lambda)
     OR (OLD.delta_t IS NOT NULL AND NEW.delta_t IS DISTINCT FROM OLD.delta_t)
     OR (OLD.precision_regime IS NOT NULL AND NEW.precision_regime IS DISTINCT FROM OLD.precision_regime)
     OR (OLD.supersedes_event_id IS NOT NULL AND NEW.supersedes_event_id IS DISTINCT FROM OLD.supersedes_event_id)
     OR (OLD.supersedes_event_id IS NULL AND NEW.supersedes_event_id IS NOT NULL) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event published non-NULL values are immutable (§6.1 enrichment-vs-correction): changing one is a correction (new id + supersedes edge), not an UPDATE';
  END IF;
  IF NEW.solver_method <> OLD.solver_method AND NOT flip THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.solver_method may only leave the clipped_truncated placeholder as part of the truncated→exact enrichment flip (§6.1, §7.2 inv 4): any other method change is a new convention';
  END IF;
  IF NEW.coverage IS DISTINCT FROM OLD.coverage AND NOT flip THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.coverage is immutable except the truncated→exact enrichment flip (§6.1)';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_event_0_chart_context ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_0_chart_context
  BEFORE INSERT OR UPDATE ON public.ka_gochara_sky_event
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_substrate_chart_lock();
DROP TRIGGER IF EXISTS ka_gochara_sky_event_supersede_check ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_supersede_check
  BEFORE INSERT ON public.ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sky_event_supersede_guard();
DROP TRIGGER IF EXISTS ka_gochara_sky_event_mutation_guard ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_mutation_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sky_event_guard();
DROP TRIGGER IF EXISTS ka_gochara_sky_event_no_truncate ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_sky_event
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 4. Contact IDENTITY — stable, global, never renumbered (§6.1; F1/F4) ───

CREATE TABLE IF NOT EXISTS public.ka_gochara_contact_identity (
  contact_id            UUID PRIMARY KEY,
  physical_object_id    UUID NOT NULL REFERENCES public.ka_gochara_physical_object(physical_object_id),
  occurrence_ordinal    INTEGER NOT NULL,
  supersedes_contact_id UUID REFERENCES public.ka_gochara_contact_identity(contact_id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgci_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT ka_gochara_contact_identity_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal),
  CONSTRAINT kgci_no_self_supersede_ck
    CHECK (supersedes_contact_id IS NULL OR supersedes_contact_id <> contact_id),
  CONSTRAINT kgci_supersedes_uq UNIQUE (supersedes_contact_id),
  CONSTRAINT kgci_tuple_uq UNIQUE (contact_id, physical_object_id, occurrence_ordinal)
);

COMMENT ON TABLE public.ka_gochara_contact_identity IS
  'Contact identity (GOCHARA_DESIGN_SPECS_v1_4 §6.1 NK-2; F1/F4): contact_id = '
  'hash(physical_object_id, occurrence_ordinal), one row per identity, GLOBAL — the stable '
  'physical identity that generation-scoped ledger rows reference and share. Never '
  'renumbered, reused or deleted (insert-only; TRUNCATE refused). Correction: a new '
  'identity of the same (body, relation_kind) under a corrected target or a new '
  'convention, linked by supersedes_contact_id (chain — kgci_supersedes_uq; never self). '
  'Constraint-guarded; a chart writer inserts it beside its ledger row, and the write '
  'first takes the chart family key of the chart the transaction serves (substrate order).';

CREATE OR REPLACE FUNCTION public.ka_gochara_contact_identity_supersede_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  pred_body text; pred_rel text; new_body text; new_rel text;
BEGIN
  IF NEW.supersedes_contact_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT o.body, o.relation_kind INTO pred_body, pred_rel
  FROM public.ka_gochara_contact_identity i
  JOIN public.ka_gochara_physical_object o ON o.physical_object_id = i.physical_object_id
  WHERE i.contact_id = NEW.supersedes_contact_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_contact_identity supersede edge invalid (§6.1): predecessor % does not exist',
      NEW.supersedes_contact_id;
  END IF;
  SELECT o.body, o.relation_kind INTO new_body, new_rel
  FROM public.ka_gochara_physical_object o
  WHERE o.physical_object_id = NEW.physical_object_id;
  IF pred_body IS DISTINCT FROM new_body OR pred_rel IS DISTINCT FROM new_rel THEN
    RAISE EXCEPTION 'ka_gochara_contact_identity supersede edge invalid (§6.1 correction): predecessor % is (%, %) but the correction is (%, %) — a correction re-solves the SAME body and relation under a corrected target or a new convention (§7.2 inv 4)',
      NEW.supersedes_contact_id, pred_body, pred_rel, new_body, new_rel;
  END IF;
  -- "superseded at most once": the named message for the common case; the
  -- race-safe guarantee is kgci_supersedes_uq (no family key on this table)
  IF EXISTS (SELECT 1 FROM public.ka_gochara_contact_identity s
             WHERE s.supersedes_contact_id = NEW.supersedes_contact_id) THEN
    RAISE EXCEPTION 'ka_gochara_contact_identity % is already superseded (§6.1): supersession history is a chain, never a tree',
      NEW.supersedes_contact_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_identity_0_chart_context ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_0_chart_context
  BEFORE INSERT ON public.ka_gochara_contact_identity
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_substrate_chart_lock();
DROP TRIGGER IF EXISTS ka_gochara_contact_identity_supersede_check ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_supersede_check
  BEFORE INSERT ON public.ka_gochara_contact_identity
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_contact_identity_supersede_guard();
DROP TRIGGER IF EXISTS ka_gochara_contact_identity_immutable ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_contact_identity
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1 publication immutability — an id is never renumbered or reused');
DROP TRIGGER IF EXISTS ka_gochara_contact_identity_no_truncate ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_contact_identity
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 5. Explicit publication seal (ruling 1; F2) ───────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_generation_seal (
  chart_id    UUID NOT NULL REFERENCES public.charts(id),
  generation  TEXT NOT NULL,
  manifest_id UUID NOT NULL,                     -- the published manifest, recorded (no FK
                                                 --   into the legacy table — ruling 1)
  sealed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation),
  CONSTRAINT kgseal_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE)
);

COMMENT ON TABLE public.ka_gochara_generation_seal IS
  'Permanent publication history for GOVERNED generations (major >= 5): one row per '
  '(chart_id, generation) that was ever published, written explicitly by '
  'ka_gochara_seal_generation() from the governed publication path in the same '
  'transaction as the status flip (ruling 1 — no trigger on the legacy manifest table). '
  'Never updated, deleted or truncated. Sealing refuses a generation whose records/windows '
  'carry coverage facts incompatible with the current coverage partitions '
  '(ka_gochara_coverage_drift, 1156) or whose window memberships are no longer applicable '
  '(ka_gochara_membership_violations, 1156). Read under the chart family key.';

-- INSERT: refuse legacy, take the chart family key, require a published
-- manifest, refuse incompatible coverage drift (1156's detector, once it
-- exists — the window applies 1153–1157 together). UPDATE/DELETE: refuse
-- before any lock.
CREATE OR REPLACE FUNCTION public.ka_gochara_generation_seal_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE n_bad integer := 0;
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal is permanent (§6.1/§10.1): % not permitted', TG_OP;
  END IF;
  IF NOT public.ka_gochara_generation_governed(NEW.generation) THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal refused: generation % is not governed by the A5.1 contract — legacy v1/3.0/4.0/4.1 (and any generation below major 5) are never sealed here (steward ruling 1)',
      NEW.generation;
  END IF;
  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);
  IF NOT EXISTS (
    SELECT 1 FROM public.kala_gochara_publication p
    WHERE p.manifest_id = NEW.manifest_id
      AND p.chart_id = NEW.chart_id AND p.generation = NEW.generation
      AND p.status = 'published'
  ) THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal refused: manifest % is not a published manifest of (chart %, generation %) — seal in the SAME transaction that sets status = published (CLAUDE.md §N.8: a seal records a real publication)',
      NEW.manifest_id, NEW.chart_id, NEW.generation;
  END IF;
  IF to_regprocedure('public.ka_gochara_coverage_drift(uuid,text)') IS NOT NULL THEN
    EXECUTE 'SELECT count(*) FROM public.ka_gochara_coverage_drift($1, $2) d WHERE d.drift IN (''incompatible'', ''partition_missing'')'
      INTO n_bad USING NEW.chart_id, NEW.generation;
    IF n_bad > 0 THEN
      RAISE EXCEPTION 'ka_gochara_generation_seal refused (N10 consumer contract): % record/window row(s) of (chart %, generation %) carry coverage facts that are INCOMPATIBLE with their partition''s current facts (or the partition is missing) — re-validate the candidate before publishing; see ka_gochara_coverage_drift(chart_id, generation)',
        n_bad, NEW.chart_id, NEW.generation;
    END IF;
  END IF;
  -- the complete membership invariant at the seal boundary (ruling 3b / N16)
  IF to_regprocedure('public.ka_gochara_membership_violations(uuid,text)') IS NOT NULL THEN
    EXECUTE 'SELECT count(*) FROM public.ka_gochara_membership_violations($1, $2)'
      INTO n_bad USING NEW.chart_id, NEW.generation;
    IF n_bad > 0 THEN
      RAISE EXCEPTION 'ka_gochara_generation_seal refused (N16 membership invariant): % window membership row(s) of (chart %, generation %) are NO LONGER APPLICABLE to their window''s coverage (contributor relation not searched, convention mismatch, or support outside the window horizon) — re-evaluate the candidate before publishing; see ka_gochara_membership_violations(chart_id, generation)',
        n_bad, NEW.chart_id, NEW.generation;
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_generation_seal_write_guard ON public.ka_gochara_generation_seal;
CREATE TRIGGER ka_gochara_generation_seal_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_generation_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_generation_seal_guard();
DROP TRIGGER IF EXISTS ka_gochara_generation_seal_no_truncate ON public.ka_gochara_generation_seal;
CREATE TRIGGER ka_gochara_generation_seal_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_generation_seal
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- The function the governed publication path calls (A5.x/A6.1). Protocol:
--   SELECT ka_gochara_lock_chart(chart);      -- FIRST, before any content read
--   ... compute digest/counts, UPDATE kala_gochara_publication SET status='published' ...
--   SELECT ka_gochara_seal_generation(chart, generation);
--   COMMIT;
CREATE OR REPLACE FUNCTION public.ka_gochara_seal_generation(p_chart_id uuid, p_generation text)
RETURNS uuid LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE m uuid;
BEGIN
  IF NOT public.ka_gochara_generation_governed(p_generation) THEN
    RAISE EXCEPTION 'ka_gochara_seal_generation refused: generation % is not governed by the A5.1 contract — legacy v1/3.0/4.0/4.1 (and any generation below major 5) are never sealed here (steward ruling 1)',
      p_generation;
  END IF;
  PERFORM public.ka_gochara_lock_chart(p_chart_id);
  SELECT p.manifest_id INTO m
  FROM public.kala_gochara_publication p
  WHERE p.chart_id = p_chart_id AND p.generation = p_generation AND p.status = 'published';
  IF m IS NULL THEN
    RAISE EXCEPTION 'ka_gochara_seal_generation refused: no published manifest for (chart %, generation %) — call it in the SAME transaction that sets kala_gochara_publication.status = published',
      p_chart_id, p_generation;
  END IF;
  INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)
  VALUES (p_chart_id, p_generation, m)
  ON CONFLICT (chart_id, generation) DO NOTHING;
  RETURN m;
END;
$$;

COMMENT ON FUNCTION public.ka_gochara_seal_generation(uuid, text) IS
  'Governed publication path entry point (ruling 1): call in the SAME transaction that '
  'sets kala_gochara_publication.status = ''published'' for a generation of major >= 5, '
  'AFTER ka_gochara_lock_chart(chart) was taken first (one lock order, N13). Refuses '
  'legacy generations, incompatible coverage drift and inapplicable window memberships; '
  'idempotent; returns the manifest id.';

CREATE OR REPLACE FUNCTION public.ka_gochara_generation_is_sealed(p_chart_id uuid, p_generation text)
RETURNS boolean LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  PERFORM public.ka_gochara_lock_chart(p_chart_id);
  RETURN EXISTS (
    SELECT 1 FROM public.ka_gochara_generation_seal s
    WHERE s.chart_id = p_chart_id AND s.generation = p_generation);
END;
$$;

-- ── 6. Legacy-convention bridge (F7) ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_convention_bridge (
  kala_convention_id TEXT PRIMARY KEY REFERENCES public.kala_gochara_convention(convention_id),
  sky_convention_id  TEXT NOT NULL REFERENCES public.ka_gochara_sky_convention(convention_id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.ka_gochara_convention_bridge IS
  'Explicit bridge (F7) from the LEGACY 1081 convention vector carried by '
  'kala_gochara_coverage.convention_id to the §6.1 sky convention carried by contacts. '
  'Insert-only; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_convention_bridge_0_chart_context ON public.ka_gochara_convention_bridge;
CREATE TRIGGER ka_gochara_convention_bridge_0_chart_context
  BEFORE INSERT ON public.ka_gochara_convention_bridge
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_substrate_chart_lock();
DROP TRIGGER IF EXISTS ka_gochara_convention_bridge_immutable ON public.ka_gochara_convention_bridge;
CREATE TRIGGER ka_gochara_convention_bridge_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_convention_bridge
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§7.2 inv 4 — a convention change is a new convention');
DROP TRIGGER IF EXISTS ka_gochara_convention_bridge_no_truncate ON public.ka_gochara_convention_bridge;
CREATE TRIGGER ka_gochara_convention_bridge_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_convention_bridge
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 7. Contact LEDGER — per-(chart × generation) ownership (§6.1/§10; F1) ─

CREATE TABLE IF NOT EXISTS public.ka_gochara_contact (
  chart_id            UUID NOT NULL REFERENCES public.charts(id),
  generation          TEXT NOT NULL,
  contact_id          UUID NOT NULL REFERENCES public.ka_gochara_contact_identity(contact_id),
  physical_object_id  UUID NOT NULL,
  occurrence_ordinal  INTEGER NOT NULL,
  convention_id       TEXT NOT NULL,
  body                TEXT NOT NULL,
  relation_kind       TEXT NOT NULL,
  t_in                TIMESTAMPTZ NOT NULL,
  t_out               TIMESTAMPTZ,
  t_exact             TIMESTAMPTZ,
  solver_method       TEXT NOT NULL,
  delta_lambda        REAL,
  delta_t             REAL,
  precision_regime    TEXT,
  coverage            JSONB NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, contact_id),
  CONSTRAINT ka_gochara_contact_identity_fk
    FOREIGN KEY (contact_id, physical_object_id, occurrence_ordinal)
    REFERENCES public.ka_gochara_contact_identity (contact_id, physical_object_id, occurrence_ordinal),
  CONSTRAINT ka_gochara_contact_object_fk
    FOREIGN KEY (physical_object_id, body, relation_kind, convention_id)
    REFERENCES public.ka_gochara_physical_object (physical_object_id, body, relation_kind, convention_id),
  CONSTRAINT kgc_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgc_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgc_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgc_relation_kind_ck CHECK (relation_kind IN
    ('residence','aspect','conjunction')),
  CONSTRAINT kgc_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT kgc_reference_uq
    UNIQUE (chart_id, generation, contact_id, body, relation_kind, physical_object_id),
  CONSTRAINT kgc_solver_method_ck CHECK (solver_method IN
    ('arc_index_bracket','swiss_refined','clipped_truncated')),
  CONSTRAINT kgc_coverage_shape_ck
    CHECK (jsonb_typeof(coverage) = 'object'
           AND coverage ? 'truncated'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
  CONSTRAINT kgc_t_exact_iff_truncated_ck
    CHECK ((t_exact IS NULL) = (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgc_truncated_method_ck
    CHECK ((coverage ->> 'truncated')::boolean = (solver_method = 'clipped_truncated')),
  CONSTRAINT kgc_t_out_unless_truncated_ck
    CHECK (t_out IS NOT NULL OR (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgc_exact_precision_ck
    CHECK (t_exact IS NULL
           OR (delta_lambda IS NOT NULL AND delta_t IS NOT NULL
               AND precision_regime IS NOT NULL)),
  CONSTRAINT kgc_uncertainty_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(delta_lambda) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(delta_t) IS TRUE),
  CONSTRAINT kgc_time_order_ck
    CHECK (t_exact IS NULL
           OR (t_in <= t_exact AND (t_out IS NULL OR t_exact <= t_out))),
  CONSTRAINT kgc_span_order_ck
    CHECK (t_out IS NULL OR t_in < t_out)
);

COMMENT ON TABLE public.ka_gochara_contact IS
  'Transit-contact LEDGER (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§10; F1): the per-(chart_id × '
  'generation) OWNERSHIP row of a stable contact identity carrying the solved values. PK '
  '(chart_id, generation, contact_id). N6: one identity, one solved reading across '
  'generations. Writer: per-(chart_id × generation) delete-then-insert of CANDIDATE '
  'generations (CLAUDE.md §N.3); a sealed generation refuses DELETE; UPDATE is '
  'enrichment-only; TRUNCATE refused. Every write takes the Gochara-5 chart family key '
  'first (statement-level for UPDATE/DELETE — N13). Legacy kala_gochara_contacts rows are '
  'NOT migrated.';

CREATE OR REPLACE FUNCTION public.ka_gochara_contact_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE flip boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    PERFORM public.ka_gochara_lock_chart(OLD.chart_id);
    IF public.ka_gochara_generation_is_sealed(OLD.chart_id, OLD.generation) THEN
      RAISE EXCEPTION 'ka_gochara_contact is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§10.1): (chart_id %, generation %) is SEALED (was published) — DELETE refused; a correction mints a new identity with a supersedes edge and a rebuild is a new generation',
        OLD.chart_id, OLD.generation;
    END IF;
    RETURN OLD;
  END IF;

  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);

  IF TG_OP = 'UPDATE' THEN
    flip := OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
        AND (OLD.coverage ->> 'truncated')::boolean
        AND NOT (NEW.coverage ->> 'truncated')::boolean
        AND OLD.solver_method = 'clipped_truncated'
        AND NEW.solver_method <> 'clipped_truncated'
        AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated');
    IF NEW.chart_id            <> OLD.chart_id
       OR NEW.generation         <> OLD.generation
       OR NEW.contact_id         <> OLD.contact_id
       OR NEW.physical_object_id <> OLD.physical_object_id
       OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
       OR NEW.convention_id      <> OLD.convention_id
       OR NEW.body               <> OLD.body
       OR NEW.relation_kind      <> OLD.relation_kind THEN
      RAISE EXCEPTION 'ka_gochara_contact identity fields are immutable (§6.1): a change to chart/generation/id/ordinal/target/relation is a correction — mint a new identity with a supersedes edge, never UPDATE';
    END IF;
    IF NEW.t_in IS DISTINCT FROM OLD.t_in
       OR (OLD.t_out IS NOT NULL AND NEW.t_out IS DISTINCT FROM OLD.t_out)
       OR (OLD.t_exact IS NOT NULL AND NEW.t_exact IS DISTINCT FROM OLD.t_exact)
       OR (OLD.delta_lambda IS NOT NULL AND NEW.delta_lambda IS DISTINCT FROM OLD.delta_lambda)
       OR (OLD.delta_t IS NOT NULL AND NEW.delta_t IS DISTINCT FROM OLD.delta_t)
       OR (OLD.precision_regime IS NOT NULL AND NEW.precision_regime IS DISTINCT FROM OLD.precision_regime) THEN
      RAISE EXCEPTION 'ka_gochara_contact published non-NULL values are immutable (§6.1 enrichment-vs-correction): changing one is a correction (new identity + supersedes edge, under a corrected target or a new convention), not an UPDATE';
    END IF;
    IF NEW.solver_method <> OLD.solver_method AND NOT flip THEN
      RAISE EXCEPTION 'ka_gochara_contact.solver_method may only leave the clipped_truncated placeholder as part of the truncated→exact enrichment flip (§6.1, §7.2 inv 4): any other method change is a new convention';
    END IF;
    IF NEW.coverage IS DISTINCT FROM OLD.coverage AND NOT flip THEN
      RAISE EXCEPTION 'ka_gochara_contact.coverage is immutable except the truncated→exact enrichment flip (§6.1)';
    END IF;
  END IF;

  -- N6 (INSERT and enrichment UPDATE): one identity, one solved reading.
  IF EXISTS (
    SELECT 1 FROM public.ka_gochara_contact o
    WHERE o.contact_id = NEW.contact_id
      AND (o.chart_id, o.generation) <> (NEW.chart_id, NEW.generation)
      AND ( (o.t_exact IS NOT NULL AND NEW.t_exact IS NOT NULL AND o.t_exact <> NEW.t_exact)
         OR (o.delta_lambda IS NOT NULL AND NEW.delta_lambda IS NOT NULL AND o.delta_lambda <> NEW.delta_lambda)
         OR (o.delta_t IS NOT NULL AND NEW.delta_t IS NOT NULL AND o.delta_t <> NEW.delta_t)
         OR (o.precision_regime IS NOT NULL AND NEW.precision_regime IS NOT NULL AND o.precision_regime <> NEW.precision_regime)
         OR (o.solver_method <> 'clipped_truncated' AND NEW.solver_method <> 'clipped_truncated'
             AND o.solver_method <> NEW.solver_method) )
  ) THEN
    RAISE EXCEPTION 'ka_gochara_contact refused (N6 / §6.1): contact % already carries a different solved reading in another generation — a changed published reading is a CORRECTION (new identity under a corrected target or a new convention), never the same id with a new value',
      NEW.contact_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_0_statement_lock ON public.ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_contact
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_contact_1_write_guard ON public.ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_contact
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_contact_guard();
DROP TRIGGER IF EXISTS ka_gochara_contact_no_truncate ON public.ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_contact
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 8. Serving/read shapes ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_kgse_convention_time ON public.ka_gochara_sky_event
  (convention_id, body, event_kind, t_exact);
CREATE INDEX IF NOT EXISTS idx_kgc_chart_gen ON public.ka_gochara_contact
  (chart_id, generation, relation_kind, t_exact);
CREATE INDEX IF NOT EXISTS idx_kgc_object ON public.ka_gochara_contact
  (physical_object_id, occurrence_ordinal);
CREATE INDEX IF NOT EXISTS idx_kgc_identity ON public.ka_gochara_contact
  (contact_id);

-- ── 9. Post-apply PRESENCE checks (ruling 4) + helper self-tests ──────────
DO $$
BEGIN
  IF NOT (public.ka_gochara_finite_nonneg_ok('NaN'::double precision) IS FALSE
          AND public.ka_gochara_finite_nonneg_ok('infinity'::double precision) IS FALSE
          AND public.ka_gochara_finite_nonneg_ok(-0.5) IS FALSE
          AND public.ka_gochara_finite_nonneg_ok(0) IS TRUE
          AND public.ka_gochara_finite_nonneg_ok(NULL) IS TRUE
          AND public.ka_gochara_finite_ok('-infinity'::double precision) IS FALSE
          AND public.ka_gochara_finite_ok(-1) IS TRUE
          AND public.ka_gochara_text_array_ok(ARRAY[NULL]::text[], 1) IS FALSE
          AND public.ka_gochara_text_array_ok(ARRAY[' ']::text[], 1) IS FALSE
          AND public.ka_gochara_text_array_ok('{}'::text[], 1) IS FALSE
          AND public.ka_gochara_text_array_ok('{}'::text[], 0) IS TRUE
          AND public.ka_gochara_text_array_ok(NULL::text[], 0) IS FALSE
          AND public.ka_gochara_text_array_ok(ARRAY['a']::text[], 1) IS TRUE
          AND public.ka_gochara_generation_governed('5.0') IS TRUE
          AND public.ka_gochara_generation_governed('12.3') IS TRUE
          AND public.ka_gochara_generation_governed('4.1') IS FALSE
          AND public.ka_gochara_generation_governed('4.0') IS FALSE
          AND public.ka_gochara_generation_governed('3.0') IS FALSE
          AND public.ka_gochara_generation_governed('v1') IS FALSE
          AND public.ka_gochara_generation_governed('5') IS FALSE
          AND public.ka_gochara_generation_governed('05.0') IS FALSE
          AND public.ka_gochara_generation_governed(NULL) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('2025-01-01T00:00Z','2026-01-01T00:00Z','[)')) IS TRUE
          AND public.ka_gochara_horizon_finite_ok(NULL) IS FALSE
          AND public.ka_gochara_horizon_finite_ok('empty'::tstzrange) IS FALSE
          AND public.ka_gochara_horizon_finite_ok('(,)'::tstzrange) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('2025-01-01T00:00Z', NULL, '[)')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('-infinity', 'infinity', '[]')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('infinity', 'infinity', '[]')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('2025-01-01T00:00Z', 'infinity', '[)')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('-infinity', '2026-01-01T00:00Z', '(]')) IS FALSE
          -- N19: AD era, years [1000, 3000) only
          AND public.ka_gochara_horizon_finite_ok(tstzrange('2025-03-01 00:00:00+00 BC', '2025-04-01 00:00:00+00 BC', '[)')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('0999-12-31 23:59:59.999999+00', '2025-04-01 00:00:00+00', '[)')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('2025-03-01 00:00:00+00', '3000-01-01 00:00:00+00', '[)')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('2025-03-01 00:00:00+00', '3000-01-01 00:00:00+00', '[]')) IS FALSE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('1000-01-01 00:00:00+00', '2999-12-31 23:59:59.999999+00', '[]')) IS TRUE
          AND public.ka_gochara_horizon_finite_ok(tstzrange('1998-01-01 00:00:00+00', '2085-01-01 00:00:00+00', '[)')) IS TRUE) THEN
    RAISE EXCEPTION 'migration 1153 post-apply check failed: helper self-test failed';
  END IF;
END;
$$;

DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(t, ', ' ORDER BY t) INTO missing
  FROM unnest(ARRAY['ka_gochara_sky_convention','ka_gochara_physical_object','ka_gochara_sky_event',
                    'ka_gochara_contact_identity','ka_gochara_generation_seal',
                    'ka_gochara_convention_bridge','ka_gochara_contact']) t
  WHERE to_regclass('public.' || t) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1153 post-apply check failed: missing table: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (VALUES
      ('ka_gochara_sky_convention','ka_gochara_sky_convention_pkey'),
      ('ka_gochara_sky_convention','kgsc_domain_ordered_ck'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_pkey'),
      ('ka_gochara_physical_object','kgpo_body_domain_ck'),
      ('ka_gochara_physical_object','kgpo_relation_kind_ck'),
      ('ka_gochara_physical_object','kgpo_target_form_ck'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_natural_uq'),
      ('ka_gochara_physical_object','kgpo_identity_uq'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_pkey'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_object_fk'),
      ('ka_gochara_sky_event','kgse_event_kind_ck'),
      ('ka_gochara_sky_event','kgse_body_domain_ck'),
      ('ka_gochara_sky_event','kgse_ordinal_ck'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_ordinal_uq'),
      ('ka_gochara_sky_event','kgse_solver_method_ck'),
      ('ka_gochara_sky_event','kgse_coverage_shape_ck'),
      ('ka_gochara_sky_event','kgse_t_exact_iff_truncated_ck'),
      ('ka_gochara_sky_event','kgse_truncated_method_ck'),
      ('ka_gochara_sky_event','kgse_exact_precision_ck'),
      ('ka_gochara_sky_event','kgse_longitude_range_ck'),
      ('ka_gochara_sky_event','kgse_uncertainty_finite_ck'),
      ('ka_gochara_sky_event','kgse_station_refined_ck'),
      ('ka_gochara_sky_event','kgse_no_self_supersede_ck'),
      ('ka_gochara_sky_event','kgse_supersedes_uq'),
      ('ka_gochara_contact_identity','ka_gochara_contact_identity_pkey'),
      ('ka_gochara_contact_identity','kgci_ordinal_ck'),
      ('ka_gochara_contact_identity','ka_gochara_contact_identity_ordinal_uq'),
      ('ka_gochara_contact_identity','kgci_no_self_supersede_ck'),
      ('ka_gochara_contact_identity','kgci_supersedes_uq'),
      ('ka_gochara_contact_identity','kgci_tuple_uq'),
      ('ka_gochara_generation_seal','ka_gochara_generation_seal_pkey'),
      ('ka_gochara_generation_seal','kgseal_generation_governed_ck'),
      ('ka_gochara_convention_bridge','ka_gochara_convention_bridge_pkey'),
      ('ka_gochara_contact','ka_gochara_contact_pkey'),
      ('ka_gochara_contact','ka_gochara_contact_identity_fk'),
      ('ka_gochara_contact','ka_gochara_contact_object_fk'),
      ('ka_gochara_contact','kgc_canonical_chart_ck'),
      ('ka_gochara_contact','kgc_generation_governed_ck'),
      ('ka_gochara_contact','kgc_body_domain_ck'),
      ('ka_gochara_contact','kgc_relation_kind_ck'),
      ('ka_gochara_contact','kgc_ordinal_ck'),
      ('ka_gochara_contact','kgc_reference_uq'),
      ('ka_gochara_contact','kgc_solver_method_ck'),
      ('ka_gochara_contact','kgc_coverage_shape_ck'),
      ('ka_gochara_contact','kgc_t_exact_iff_truncated_ck'),
      ('ka_gochara_contact','kgc_truncated_method_ck'),
      ('ka_gochara_contact','kgc_t_out_unless_truncated_ck'),
      ('ka_gochara_contact','kgc_exact_precision_ck'),
      ('ka_gochara_contact','kgc_uncertainty_finite_ck'),
      ('ka_gochara_contact','kgc_time_order_ck'),
      ('ka_gochara_contact','kgc_span_order_ck'))
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname AND c.convalidated);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1153 post-apply check failed: missing or unvalidated constraint: %', missing;
  END IF;

  WITH expected(tgrelid, tgname) AS (VALUES
      ('ka_gochara_sky_convention','ka_gochara_sky_convention_0_chart_context'),
      ('ka_gochara_sky_convention','ka_gochara_sky_convention_immutable'),
      ('ka_gochara_sky_convention','ka_gochara_sky_convention_no_truncate'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_0_chart_context'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_immutable'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_no_truncate'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_0_chart_context'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_supersede_check'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_mutation_guard'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_no_truncate'),
      ('ka_gochara_contact_identity','ka_gochara_contact_identity_0_chart_context'),
      ('ka_gochara_contact_identity','ka_gochara_contact_identity_supersede_check'),
      ('ka_gochara_contact_identity','ka_gochara_contact_identity_immutable'),
      ('ka_gochara_contact_identity','ka_gochara_contact_identity_no_truncate'),
      ('ka_gochara_generation_seal','ka_gochara_generation_seal_write_guard'),
      ('ka_gochara_generation_seal','ka_gochara_generation_seal_no_truncate'),
      ('ka_gochara_convention_bridge','ka_gochara_convention_bridge_0_chart_context'),
      ('ka_gochara_convention_bridge','ka_gochara_convention_bridge_immutable'),
      ('ka_gochara_convention_bridge','ka_gochara_convention_bridge_no_truncate'),
      ('ka_gochara_contact','ka_gochara_contact_0_statement_lock'),
      ('ka_gochara_contact','ka_gochara_contact_1_write_guard'),
      ('ka_gochara_contact','ka_gochara_contact_no_truncate'))
  SELECT string_agg(e.tgrelid || '.' || e.tgname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.' || e.tgrelid) AND t.tgname = e.tgname
      AND NOT t.tgisinternal AND t.tgenabled = 'O');
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1153 post-apply check failed: missing trigger: %', missing;
  END IF;

  -- ruling 1: none of OUR (user) triggers may sit on a table this family does
  -- not own. (Foreign keys to charts / kala_gochara_convention /
  -- kala_gochara_coverage install PostgreSQL's internal RI triggers there —
  -- disclosed in the header, not hidden by this check.)
  IF EXISTS (
    SELECT 1 FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    WHERE NOT t.tgisinternal AND t.tgname LIKE 'ka\_gochara\_%'
      AND c.relname NOT LIKE 'ka\_gochara\_%') THEN
    RAISE EXCEPTION 'migration 1153 post-apply check failed: a ka_gochara user trigger exists on a table this family does not own (steward ruling 1)';
  END IF;
  RAISE NOTICE 'migration 1153: presence checks passed';
END;
$$;
