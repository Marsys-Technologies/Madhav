-- Migration 1156: ka_gochara_eval_window — the §2.1 eval_window typed
--                 contract + §3.1 valence fields, with record membership bound
--                 to the SAME chart, generation, event class and rule version
--                 AND to the window's coverage (F7/N10), coverage
--                 applicability bound to an unambiguous facts snapshot
--                 (F7/N10/N14), the N10 consumer contract
--                 (ka_gochara_coverage_drift over records AND windows), a
--                 FROZEN membership set once published (F2/N9), sealed-rule-
--                 version references (F3/N5) and finite numeric domains (F11)
--                 — every write under the Gochara-5 chart family key, then
--                 the global family key SHARED (steward ruling B); the
--                 complete membership invariant re-checked at the SEAL
--                 boundary (N16); finite AD-era horizons only (N17/N19).
--                 Depends on 1154, 1155 and 1081 (kala_gochara_coverage).
--                 Round-7 per ASTRA_REVIEW_A5_1_MIGRATIONS v1_5 on rounds 5–6
--                 under the steward's corrected lock ruling. Never applied
--                 anywhere — in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1156 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Gate: pinned schema → preflight gate (byte-identical
-- to preflight_1156_eval_window.sql; requires 1153–1155 recorded) → DDL →
-- presence checks. Deploy route: the protected public-schema window.
--
-- ── Windows and their coverage (F7/N10/N14) ────────────────────────────────
-- A window is per (chart, event_class, generation, path version) — it is the
-- product of the CLASS search, so its coverage partition is the class's
-- `event_class` partition with key = event_class (P6 produces day rows, never
-- windows — §2.2). `coverage_facts` binds the window to the unambiguous
-- snapshot of the partition facts it was validated against (same helper and
-- rule as 1155). The window's interval lies inside completed_horizon.
--
-- ── Membership (F7/N9/N10) ─────────────────────────────────────────────────
-- ka_gochara_eval_window_record carries (chart_id, generation, event_class,
-- path_id, rule_version) and FKs BOTH ends on all of them. Additionally
-- (N10 — coverage applicability to window CONTRIBUTORS): a contributing
-- record must have been validated under the SAME convention as the window,
-- a transit contributor's relation must lie within the window's
-- relations_searched, and every support interval of the contributor must lie
-- inside the window's coverage horizon (ka_gochara_window_membership_guard).
-- Membership rows are written once with their window and are otherwise
-- IMMUTABLE (no UPDATE); on a sealed generation INSERT and DELETE are refused
-- too, so a published window's record list can never change (N9). ON DELETE
-- CASCADE on both ends serves the §N.3 candidate rebuild only.
-- [steward ruling] THE SEAL BOUNDARY (N16): candidate records, windows and
-- their partitions stay updateable before publication, so a membership that
-- was applicable when inserted can become inapplicable later (a class
-- partition re-searched with fewer relations, a convention change, a window
-- horizon narrowed, a contributor's support moved). Rather than revalidation
-- triggers on every parent update, ONE predicate
-- (ka_gochara_membership_violation) serves both the INSERT guard and
-- ka_gochara_membership_violations(chart, generation), which
-- ka_gochara_seal_generation (1153) runs over EVERY membership of the
-- generation and refuses the seal on any violation — the complete invariant
-- holds at publication, which is the boundary that matters.
--
-- ── The N10 consumer contract — ka_gochara_coverage_drift ─────────────────
-- Steward ruling 1 forbids any trigger on the legacy coverage table, so a
-- partition changed after a consumer was validated cannot be blocked there.
-- ka_gochara_coverage_drift(chart_id, generation) is the detector: for every
-- record and window of the generation it compares the stored coverage_facts
-- with the partition's CURRENT facts and classifies
--   identical         — unchanged;
--   extended          — same convention, current horizon ⊇ stored, current
--                       relations ⊇ stored (no NULL): still valid, more was
--                       searched afterwards (the ledger's extend-then-enrich);
--   incompatible      — anything else (convention changed, horizon shrunk or
--                       moved, relations dropped, NULL introduced);
--   partition_missing — the partition row is gone.
-- ka_gochara_seal_generation (1153) REFUSES to seal while any consumer is
-- incompatible/partition_missing; serve-time consumers read this function
-- and treat `incompatible` as "re-validate before use". The stored snapshot
-- is never silently refreshed — it is the evidence of what was validated.
-- A partition that later LEFT THE ACCEPTED DOMAIN (N17/N19: empty, unbounded,
-- a ±infinity bound, a BC bound or a year outside [1000, 3000)) is
-- `incompatible` outright — the encoder is never asked to encode it, so no
-- accepted snapshot can ever equal one (the reviewer's H_AD → H_BC
-- replacement is unsealable).
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK (1157 is independent; this before 1155):
--   DROP TABLE IF EXISTS ka_gochara_eval_window_record;
--   DROP TABLE IF EXISTS ka_gochara_eval_window;
--   DROP FUNCTION IF EXISTS ka_gochara_coverage_drift(uuid, text);
--   DROP FUNCTION IF EXISTS ka_gochara_membership_violations(uuid, text);
--   DROP FUNCTION IF EXISTS ka_gochara_window_membership_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_membership_violation(jsonb, uuid, text, jsonb, tstzrange[]);
--   DROP FUNCTION IF EXISTS ka_gochara_window_coverage_guard();
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1156_eval_window.sql) ────────────────
DO $$
DECLARE
  failures text;
BEGIN
  WITH f(failure, detail) AS (
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
    FROM (VALUES ('public.charts'), ('public.kala_gochara_coverage')) AS p(t)
    WHERE to_regclass(p.t) IS NOT NULL AND NOT has_table_privilege(p.t, 'REFERENCES')
    UNION ALL
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('ka_gochara_eval_window', 'ka_gochara_eval_window_pkey',
                        'kgew_membership_uq',
                        'ka_gochara_eval_window_record', 'ka_gochara_eval_window_record_pkey',
                        'idx_kgew_chart_gen', 'idx_kgew_path', 'idx_kgew_coverage',
                        'idx_kgewr_record', 'idx_kgewr_chart_gen')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_eval_window'
               AND t.tgname IN ('ka_gochara_ew_0_statement_lock',
                                'ka_gochara_ew_1_write_guard', 'ka_gochara_ew_2_coverage_guard',
                                'ka_gochara_ew_3_sealed_path_check', 'ka_gochara_ew_no_truncate'))
         OR (c.relname = 'ka_gochara_eval_window_record'
               AND t.tgname IN ('ka_gochara_ewr_0_statement_lock',
                                'ka_gochara_ewr_1_write_guard', 'ka_gochara_ewr_2_membership_guard',
                                'ka_gochara_ewr_no_truncate')) )
    UNION ALL
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES ('ka_gochara_window_coverage_guard',   ARRAY[]::text[]),
                 ('ka_gochara_membership_violation',    ARRAY['jsonb','uuid','text','jsonb','tstzrange[]']),
                 ('ka_gochara_window_membership_guard', ARRAY[]::text[]),
                 ('ka_gochara_membership_violations',   ARRAY['uuid','text']),
                 ('ka_gochara_coverage_drift',          ARRAY['uuid','text'])) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('ka_gochara_rule_path'), ('ka_gochara_rule_path_seal'),
                 ('ka_gochara_relationship_record'), ('kala_gochara_coverage'),
                 ('ka_gochara_generation_seal')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                         'id',                 'uuid'),
                 ('ka_gochara_rule_path',           'path_id',            'text'),
                 ('ka_gochara_rule_path',           'rule_version',       'text'),
                 ('ka_gochara_relationship_record', 'record_id',          'uuid'),
                 ('ka_gochara_relationship_record', 'chart_id',           'uuid'),
                 ('ka_gochara_relationship_record', 'generation',         'text'),
                 ('ka_gochara_relationship_record', 'event_class',        'text'),
                 ('ka_gochara_relationship_record', 'path_id',            'text'),
                 ('ka_gochara_relationship_record', 'rule_version',       'text'),
                 ('ka_gochara_relationship_record', 'contact_id',         'uuid'),
                 ('ka_gochara_relationship_record', 'relation',           'text'),
                 ('ka_gochara_relationship_record', 'coverage_facts',     'jsonb'),
                 ('ka_gochara_relationship_record', 'coverage_partition_kind', 'text'),
                 ('ka_gochara_relationship_record', 'coverage_partition_key',  'text'),
                 ('ka_gochara_relationship_record', 'temporal_support_intervals', 'tstzrange[]'),
                 ('kala_gochara_coverage',          'chart_id',           'uuid'),
                 ('kala_gochara_coverage',          'generation',         'text'),
                 ('kala_gochara_coverage',          'partition_kind',     'text'),
                 ('kala_gochara_coverage',          'partition_key',      'text'),
                 ('kala_gochara_coverage',          'convention_id',      'text'),
                 ('kala_gochara_coverage',          'completed_horizon',  'tstzrange'),
                 ('kala_gochara_coverage',          'relations_searched', 'text[]')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                         ARRAY['id']),
                 ('ka_gochara_rule_path',           ARRAY['path_id','rule_version']),
                 ('ka_gochara_rule_path_seal',      ARRAY['path_id','rule_version']),
                 ('ka_gochara_relationship_record', ARRAY['record_id','chart_id','generation','event_class','path_id','rule_version']),
                 ('kala_gochara_coverage',          ARRAY['chart_id','generation','partition_kind','partition_key'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_finite_ok(double precision)'),
                 ('ka_gochara_finite_nonneg_ok(double precision)'),
                 ('ka_gochara_text_array_ok(text[],integer)'),
                 ('ka_gochara_generation_governed(text)'),
                 ('ka_gochara_horizon_finite_ok(tstzrange)'),
                 ('ka_gochara_generation_is_sealed(uuid,text)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
       OR (SELECT format_type(p.prorettype, NULL) FROM pg_proc p
           WHERE p.oid = to_regprocedure('public.' || e.sig)) <> 'boolean'
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_lock_chart(uuid)'),
                 ('ka_gochara_lock_global_shared()'),
                 ('ka_gochara_chart_statement_lock()'),
                 ('ka_gochara_require_sealed_rule_path()'),
                 ('ka_gochara_chart_write_guard()'),
                 ('ka_gochara_coverage_facts(text,tstzrange,text[])'),
                 ('ka_gochara_facts_horizon(jsonb)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_'), ('1155_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1156_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1156 BLOCKED — migration 1156 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1156: all checks passed';
END;
$$;

-- ── 1. eval_window (§2.1 + §3.1) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_eval_window (
  window_id         UUID PRIMARY KEY,
  chart_id          UUID NOT NULL REFERENCES public.charts(id),
  event_class       TEXT NOT NULL,
  generation        TEXT NOT NULL,               -- governed generation (major >= 5)
  path_id           TEXT NOT NULL,               -- sealed rule version (F3/N5)
  rule_version      TEXT NOT NULL,
  interval          TSTZRANGE NOT NULL,          -- the admitted window; never empty
  peak_instant      TIMESTAMPTZ,                 -- ∈ interval when set (S:321-323)
  score             REAL,                        -- [0,1] when computed; NULL = unqualified
  evidence_for      REAL,                        -- finite ≥ 0; never netted
  evidence_against  REAL,                        -- finite ≥ 0; never netted
  outcome_valence_for_native TEXT NOT NULL,      -- 'unqualified' is the honest state
  severity          REAL,                        -- finite
  coverage_partition_kind TEXT NOT NULL,         -- always 'event_class' (header)
  coverage_partition_key  TEXT NOT NULL,         -- = event_class (guard)
  coverage_facts    JSONB NOT NULL,              -- N10/N14: the partition facts snapshot
  null_states_used  TEXT[] NOT NULL DEFAULT '{}',-- ⊆ {omit, unqualified}
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgew_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgew_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgew_event_class_ck CHECK (event_class IN (
    'achievement_recognition','bereavement','birth_anchor',
    'business_launch','career_advancement','career_change',
    'career_entry','career_setback','childbirth',
    'chronic_onset','education_milestone','exam_outcome',
    'financial_deception','foreign_settlement','illness_acute',
    'major_gain','major_loss','marriage','parental_event',
    'property_acquisition','psychological_arc','relocation',
    'romantic_start','separation','spiritual_turn','surgery',
    'travel_event')),
  CONSTRAINT kgew_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgew_interval_nonempty_ck CHECK (NOT isempty(interval)),
  CONSTRAINT kgew_interval_finite_ck
    CHECK (public.ka_gochara_horizon_finite_ok(interval) IS TRUE),   -- N17: finite, bounded
  CONSTRAINT kgew_peak_in_interval_ck
    CHECK (peak_instant IS NULL OR peak_instant <@ interval),
  CONSTRAINT kgew_score_unit_interval_ck
    CHECK (score IS NULL
           OR (public.ka_gochara_finite_ok(score) IS TRUE AND score >= 0 AND score <= 1)),
  CONSTRAINT kgew_evidence_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(evidence_for) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(evidence_against) IS TRUE),
  CONSTRAINT kgew_severity_finite_ck
    CHECK (public.ka_gochara_finite_ok(severity) IS TRUE),
  CONSTRAINT kgew_valence_ck CHECK (outcome_valence_for_native IN
    ('favourable','adverse','mixed','unqualified')),
  CONSTRAINT kgew_coverage_kind_ck CHECK (coverage_partition_kind = 'event_class'),
    -- a window is the product of the CLASS search (header; N10)
  CONSTRAINT kgew_coverage_fk
    FOREIGN KEY (chart_id, generation, coverage_partition_kind, coverage_partition_key)
    REFERENCES public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key),
  CONSTRAINT kgew_coverage_facts_shape_ck
    CHECK (jsonb_typeof(coverage_facts) = 'object'
           AND coverage_facts ? 'convention_id' AND coverage_facts ? 'horizon'
           AND coverage_facts ? 'relations_searched'),
  CONSTRAINT kgew_null_states_ck
    CHECK (public.ka_gochara_text_array_ok(null_states_used, 0) IS TRUE
           AND null_states_used <@ ARRAY['omit','unqualified']::text[]),
  CONSTRAINT kgew_membership_uq
    UNIQUE (window_id, chart_id, generation, event_class, path_id, rule_version)
);

COMMENT ON TABLE public.ka_gochara_eval_window IS
  'Evaluated window (GOCHARA_DESIGN_SPECS_v1_4 §2.1 eval_window contract + §3.1 valence '
  'fields): one evaluated interval per (chart, event_class, generation, path). Coverage: '
  'the class''s event_class partition, bound by an unambiguous facts snapshot (F7/N10/N14; '
  'drift classified by ka_gochara_coverage_drift). Membership is normalised into '
  'ka_gochara_eval_window_record, bound on both ends to the SAME chart, generation, class '
  'and rule version, checked against the window''s coverage, and FROZEN once the generation '
  'is sealed (N9). Only a sealed rule version may produce a window (F3/N5). Every write '
  'takes the Gochara-5 chart family key first (statement-level for UPDATE/DELETE), then '
  'the global family key SHARED. TRUNCATE refused.';

CREATE INDEX IF NOT EXISTS idx_kgew_chart_gen ON public.ka_gochara_eval_window
  (chart_id, generation, event_class, interval);
CREATE INDEX IF NOT EXISTS idx_kgew_path ON public.ka_gochara_eval_window
  (path_id, rule_version);
CREATE INDEX IF NOT EXISTS idx_kgew_coverage ON public.ka_gochara_eval_window
  (chart_id, generation, coverage_partition_kind, coverage_partition_key);

-- ── 2. Record membership — same chart/generation/class/path on both ends ──

CREATE TABLE IF NOT EXISTS public.ka_gochara_eval_window_record (
  window_id     UUID NOT NULL,
  record_id     UUID NOT NULL,
  chart_id      UUID NOT NULL,
  generation    TEXT NOT NULL,
  event_class   TEXT NOT NULL,
  path_id       TEXT NOT NULL,
  rule_version  TEXT NOT NULL,

  PRIMARY KEY (window_id, record_id),
  CONSTRAINT kgewr_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgewr_window_fk
    FOREIGN KEY (window_id, chart_id, generation, event_class, path_id, rule_version)
    REFERENCES public.ka_gochara_eval_window (window_id, chart_id, generation, event_class, path_id, rule_version)
    ON DELETE CASCADE,
  CONSTRAINT kgewr_record_fk
    FOREIGN KEY (record_id, chart_id, generation, event_class, path_id, rule_version)
    REFERENCES public.ka_gochara_relationship_record (record_id, chart_id, generation, event_class, path_id, rule_version)
    ON DELETE CASCADE
);

COMMENT ON TABLE public.ka_gochara_eval_window_record IS
  'Eval-window record membership (S:185 record_ids [FK] made structural; F7): one row per '
  '(window, contributing record), bound on both ends to the SAME (chart_id, generation, '
  'event_class, path_id, rule_version), and to the window''s coverage: same convention, '
  'transit relation within the window''s relations_searched, support intervals inside the '
  'window''s horizon (N10). Written once with its window; never updated; INSERT/DELETE '
  'refused once the generation is sealed (N9). Cascades serve the §N.3 candidate rebuild '
  'only. TRUNCATE refused.';

CREATE INDEX IF NOT EXISTS idx_kgewr_record ON public.ka_gochara_eval_window_record
  (record_id);
CREATE INDEX IF NOT EXISTS idx_kgewr_chart_gen ON public.ka_gochara_eval_window_record
  (chart_id, generation);

-- ── 3. Coverage applicability for windows (F7/N10/N14) ─────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_window_coverage_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE cov record; facts jsonb;
BEGIN
  IF NEW.coverage_partition_kind <> 'event_class' THEN
    RETURN NEW;   -- a wrong partition kind is the CHECK constraint's finding (kgew_coverage_kind_ck)
  END IF;
  SELECT c.partition_kind, c.partition_key, c.convention_id, c.completed_horizon, c.relations_searched
    INTO cov
  FROM public.kala_gochara_coverage c
  WHERE c.chart_id = NEW.chart_id AND c.generation = NEW.generation
    AND c.partition_kind = NEW.coverage_partition_kind
    AND c.partition_key = NEW.coverage_partition_key;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage unresolvable (§2.1 coverage_ref): no kala_gochara_coverage partition (%, %) for (chart %, generation %)',
      NEW.coverage_partition_kind, NEW.coverage_partition_key, NEW.chart_id, NEW.generation;
  END IF;
  IF cov.relations_searched IS NULL OR array_position(cov.relations_searched, NULL) IS NOT NULL THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage not applicable (N10): partition (%, %) carries a NULL relations_searched element',
      cov.partition_kind, cov.partition_key;
  END IF;
  IF public.ka_gochara_horizon_finite_ok(cov.completed_horizon) IS NOT TRUE THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage not applicable (N17/N19): partition (%, %) completed_horizon % is not a finite, bounded, non-empty range within 1000-01-01 <= t < 3000-01-01 UTC (AD) — the Gochara-5 contract admits such horizons only',
      cov.partition_kind, cov.partition_key, cov.completed_horizon;
  END IF;
  facts := public.ka_gochara_coverage_facts(cov.convention_id, cov.completed_horizon, cov.relations_searched);
  IF NEW.coverage_facts IS DISTINCT FROM facts THEN
    RAISE EXCEPTION 'ka_gochara_eval_window.coverage_facts % does not equal the partition''s current facts % (N10/N14)',
      NEW.coverage_facts, facts;
  END IF;
  IF cov.partition_key <> NEW.event_class THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage not applicable (F7): event_class partition ''%'' does not cover class ''%''',
      cov.partition_key, NEW.event_class;
  END IF;
  -- a non-finite window interval is the CHECK constraint's finding (kgew_interval_finite_ck)
  IF public.ka_gochara_horizon_finite_ok(NEW.interval) IS TRUE AND NOT (cov.completed_horizon @> NEW.interval) THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage not applicable (F7): window interval % lies outside the partition''s completed_horizon %',
      NEW.interval, cov.completed_horizon;
  END IF;
  RETURN NEW;
END;
$$;

-- ── 4. Coverage applicability to window CONTRIBUTORS (N10/N16) ─────────────
-- ONE predicate for both boundaries: NULL when the contributor is applicable
-- to the window's coverage, else the reason. Used by the membership INSERT
-- guard and by the seal-time set check (ka_gochara_membership_violations).
CREATE OR REPLACE FUNCTION public.ka_gochara_membership_violation(
  w_facts jsonb, r_contact_id uuid, r_relation text, r_facts jsonb, r_intervals tstzrange[])
RETURNS text LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE
  wh tstzrange;
  iv tstzrange;
BEGIN
  IF (r_facts ->> 'convention_id') IS DISTINCT FROM (w_facts ->> 'convention_id') THEN
    RETURN format('record validated under convention %L but the window was searched under convention %L',
                  r_facts ->> 'convention_id', w_facts ->> 'convention_id');
  END IF;
  IF r_contact_id IS NOT NULL
     AND NOT COALESCE((w_facts -> 'relations_searched') @> to_jsonb(ARRAY[r_relation]), false) THEN
    RETURN format('transit record relation %L was not searched by the window (relations_searched %s)',
                  r_relation, w_facts -> 'relations_searched');
  END IF;
  wh := public.ka_gochara_facts_horizon(w_facts);
  FOREACH iv IN ARRAY COALESCE(r_intervals, '{}'::tstzrange[]) LOOP
    IF NOT COALESCE(wh @> iv, false) THEN
      RETURN format('record support interval %s lies outside the window''s coverage horizon %s', iv, wh);
    END IF;
  END LOOP;
  RETURN NULL;
END;
$$;

-- Fires AFTER the chart guard took the chart family key. The FKs already
-- bind both ends to the same (chart, generation, class, path); this binds
-- the contributor to the window's COVERAGE at INSERT.
CREATE OR REPLACE FUNCTION public.ka_gochara_window_membership_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  w   record;
  r   record;
  why text;
BEGIN
  SELECT x.coverage_facts INTO w
  FROM public.ka_gochara_eval_window x
  WHERE x.window_id = NEW.window_id;
  IF NOT FOUND THEN
    RETURN NEW;   -- the FK reports a missing window
  END IF;
  SELECT y.contact_id, y.relation, y.coverage_facts, y.temporal_support_intervals INTO r
  FROM public.ka_gochara_relationship_record y
  WHERE y.record_id = NEW.record_id;
  IF NOT FOUND THEN
    RETURN NEW;   -- the FK reports a missing record
  END IF;
  why := public.ka_gochara_membership_violation(w.coverage_facts, r.contact_id, r.relation, r.coverage_facts, r.temporal_support_intervals);
  IF why IS NOT NULL THEN
    RAISE EXCEPTION 'ka_gochara_eval_window_record not applicable (N10): record % → window %: %',
      NEW.record_id, NEW.window_id, why;
  END IF;
  RETURN NEW;
END;
$$;

-- The seal-boundary set check (N16): every membership of the generation
-- that is no longer applicable to its window's coverage, with the reason.
CREATE OR REPLACE FUNCTION public.ka_gochara_membership_violations(p_chart_id uuid, p_generation text)
RETURNS TABLE (window_id uuid, record_id uuid, violation text)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT m.window_id, m.record_id, v.why
  FROM public.ka_gochara_eval_window_record m
  JOIN public.ka_gochara_eval_window w ON w.window_id = m.window_id
  JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id
  CROSS JOIN LATERAL (
    SELECT public.ka_gochara_membership_violation(w.coverage_facts, r.contact_id, r.relation, r.coverage_facts, r.temporal_support_intervals) AS why) v
  WHERE m.chart_id = p_chart_id AND m.generation = p_generation
    AND v.why IS NOT NULL;
$$;

COMMENT ON FUNCTION public.ka_gochara_membership_violations(uuid, text) IS
  'N16 seal-boundary invariant: the window memberships of (chart, generation) whose '
  'contributor is no longer applicable to the window''s coverage (relation not searched, '
  'convention mismatch, support outside the window horizon), with the reason. '
  'ka_gochara_seal_generation refuses to seal while any row exists.';

-- ── 5. The N10 consumer contract: drift classifier over records + windows ──

CREATE OR REPLACE FUNCTION public.ka_gochara_coverage_drift(p_chart_id uuid, p_generation text)
RETURNS TABLE (
  consumer        text,
  consumer_id     uuid,
  partition_kind  text,
  partition_key   text,
  drift           text,
  stored_facts    jsonb,
  current_facts   jsonb)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH consumers AS (
    SELECT 'relationship_record'::text AS consumer, r.record_id AS consumer_id,
           r.coverage_partition_kind, r.coverage_partition_key, r.coverage_facts
    FROM public.ka_gochara_relationship_record r
    WHERE r.chart_id = p_chart_id AND r.generation = p_generation
    UNION ALL
    SELECT 'eval_window'::text, w.window_id,
           w.coverage_partition_kind, w.coverage_partition_key, w.coverage_facts
    FROM public.ka_gochara_eval_window w
    WHERE w.chart_id = p_chart_id AND w.generation = p_generation
  )
  SELECT c.consumer, c.consumer_id, c.coverage_partition_kind, c.coverage_partition_key,
         CASE
           WHEN cov.chart_id IS NULL THEN 'partition_missing'
           WHEN public.ka_gochara_horizon_finite_ok(cov.completed_horizon) IS NOT TRUE THEN 'incompatible'   -- N17/N19: left the accepted domain
           WHEN cur.facts = c.coverage_facts THEN 'identical'
           WHEN cov.convention_id IS NOT DISTINCT FROM (c.coverage_facts ->> 'convention_id')
                AND cov.relations_searched IS NOT NULL
                AND array_position(cov.relations_searched, NULL) IS NULL
                AND COALESCE(cov.completed_horizon @> public.ka_gochara_facts_horizon(c.coverage_facts), false)
                AND COALESCE((SELECT bool_and(e = ANY (cov.relations_searched))
                              FROM jsonb_array_elements_text(c.coverage_facts -> 'relations_searched') e), true)
                AND jsonb_typeof(c.coverage_facts -> 'relations_searched') = 'array'
             THEN 'extended'
           ELSE 'incompatible'
         END AS drift,
         c.coverage_facts AS stored_facts,
         cur.facts AS current_facts
  FROM consumers c
  LEFT JOIN public.kala_gochara_coverage cov
    ON cov.chart_id = p_chart_id AND cov.generation = p_generation
   AND cov.partition_kind = c.coverage_partition_kind AND cov.partition_key = c.coverage_partition_key
  CROSS JOIN LATERAL (
    SELECT CASE WHEN cov.chart_id IS NULL
                  OR public.ka_gochara_horizon_finite_ok(cov.completed_horizon) IS NOT TRUE THEN NULL::jsonb
                ELSE public.ka_gochara_coverage_facts(cov.convention_id, cov.completed_horizon, cov.relations_searched)
           END AS facts) cur;
$$;

COMMENT ON FUNCTION public.ka_gochara_coverage_drift(uuid, text) IS
  'N10 consumer contract: classifies every record/window of (chart, generation) against '
  'its coverage partition''s CURRENT facts — identical | extended (same convention, horizon '
  '⊇ stored, relations ⊇ stored, no NULL: still valid) | incompatible (incl. a partition '
  'that became non-finite, N17) | partition_missing. ka_gochara_seal_generation refuses to '
  'seal while any consumer is incompatible or partition_missing; serve-time consumers treat '
  'incompatible as re-validate-before-use.';

-- ── 6. Triggers (statement lock → row: lock/seal → coverage → rule seal) ──

DROP TRIGGER IF EXISTS ka_gochara_ew_0_statement_lock ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_eval_window
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_ew_1_write_guard ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_eval_window
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('plain');
DROP TRIGGER IF EXISTS ka_gochara_ew_2_coverage_guard ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_2_coverage_guard
  BEFORE INSERT OR UPDATE ON public.ka_gochara_eval_window
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_window_coverage_guard();
DROP TRIGGER IF EXISTS ka_gochara_ew_3_sealed_path_check ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_3_sealed_path_check
  BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_eval_window
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
DROP TRIGGER IF EXISTS ka_gochara_ew_no_truncate ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_eval_window
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_ewr_0_statement_lock ON public.ka_gochara_eval_window_record;
CREATE TRIGGER ka_gochara_ewr_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_eval_window_record
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_ewr_1_write_guard ON public.ka_gochara_eval_window_record;
CREATE TRIGGER ka_gochara_ewr_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_eval_window_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('no_update');
DROP TRIGGER IF EXISTS ka_gochara_ewr_2_membership_guard ON public.ka_gochara_eval_window_record;
CREATE TRIGGER ka_gochara_ewr_2_membership_guard
  BEFORE INSERT ON public.ka_gochara_eval_window_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_window_membership_guard();
DROP TRIGGER IF EXISTS ka_gochara_ewr_no_truncate ON public.ka_gochara_eval_window_record;
CREATE TRIGGER ka_gochara_ewr_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_eval_window_record
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 7. Post-apply PRESENCE checks (steward ruling 3) ───────────────────────
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(t, ', ' ORDER BY t) INTO missing
  FROM unnest(ARRAY['ka_gochara_eval_window','ka_gochara_eval_window_record']) t
  WHERE to_regclass('public.' || t) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1156 post-apply check failed: missing table: %', missing;
  END IF;
  IF to_regprocedure('public.ka_gochara_coverage_drift(uuid,text)') IS NULL
     OR to_regprocedure('public.ka_gochara_membership_violations(uuid,text)') IS NULL
     OR to_regprocedure('public.ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[])') IS NULL THEN
    RAISE EXCEPTION 'migration 1156 post-apply check failed: drift / membership-violation functions missing';
  END IF;

  WITH expected(conrelid, conname) AS (VALUES
      ('ka_gochara_eval_window','ka_gochara_eval_window_pkey'),
      ('ka_gochara_eval_window','kgew_canonical_chart_ck'),
      ('ka_gochara_eval_window','kgew_generation_governed_ck'),
      ('ka_gochara_eval_window','kgew_event_class_ck'),
      ('ka_gochara_eval_window','kgew_path_fk'),
      ('ka_gochara_eval_window','kgew_interval_nonempty_ck'),
      ('ka_gochara_eval_window','kgew_interval_finite_ck'),
      ('ka_gochara_eval_window','kgew_peak_in_interval_ck'),
      ('ka_gochara_eval_window','kgew_score_unit_interval_ck'),
      ('ka_gochara_eval_window','kgew_evidence_finite_ck'),
      ('ka_gochara_eval_window','kgew_severity_finite_ck'),
      ('ka_gochara_eval_window','kgew_valence_ck'),
      ('ka_gochara_eval_window','kgew_coverage_kind_ck'),
      ('ka_gochara_eval_window','kgew_coverage_fk'),
      ('ka_gochara_eval_window','kgew_coverage_facts_shape_ck'),
      ('ka_gochara_eval_window','kgew_null_states_ck'),
      ('ka_gochara_eval_window','kgew_membership_uq'),
      ('ka_gochara_eval_window_record','ka_gochara_eval_window_record_pkey'),
      ('ka_gochara_eval_window_record','kgewr_generation_governed_ck'),
      ('ka_gochara_eval_window_record','kgewr_window_fk'),
      ('ka_gochara_eval_window_record','kgewr_record_fk'))
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname AND c.convalidated);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1156 post-apply check failed: missing or unvalidated constraint: %', missing;
  END IF;

  WITH expected(tgrelid, tgname) AS (VALUES
      ('ka_gochara_eval_window','ka_gochara_ew_0_statement_lock'),
      ('ka_gochara_eval_window','ka_gochara_ew_1_write_guard'),
      ('ka_gochara_eval_window','ka_gochara_ew_2_coverage_guard'),
      ('ka_gochara_eval_window','ka_gochara_ew_3_sealed_path_check'),
      ('ka_gochara_eval_window','ka_gochara_ew_no_truncate'),
      ('ka_gochara_eval_window_record','ka_gochara_ewr_0_statement_lock'),
      ('ka_gochara_eval_window_record','ka_gochara_ewr_1_write_guard'),
      ('ka_gochara_eval_window_record','ka_gochara_ewr_2_membership_guard'),
      ('ka_gochara_eval_window_record','ka_gochara_ewr_no_truncate'))
  SELECT string_agg(e.tgrelid || '.' || e.tgname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.' || e.tgrelid) AND t.tgname = e.tgname
      AND NOT t.tgisinternal AND t.tgenabled = 'O');
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1156 post-apply check failed: missing trigger: %', missing;
  END IF;
  RAISE NOTICE 'migration 1156: presence checks passed';
END;
$$;
