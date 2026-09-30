-- Migration 1156: ka_gochara_eval_window — the §2.1 eval_window typed
--                 contract + §3.1 valence fields, with record membership
--                 bound to the SAME chart, generation, event class and rule
--                 version (F7), coverage applicability (F7), sealed-generation
--                 immutability (F2), sealed-rule-version references (F3) and
--                 finite numeric domains (F11). Depends on 1154 (rule_path,
--                 seal), 1155 (relationship_record, sealed-generation guard)
--                 and 1081 (kala_gochara_coverage). Round-3 rewrite per
--                 ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 under the steward rulings.
--                 Never applied anywhere — in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1156 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Effective ordered gate: pinned schema → preflight
-- gate (byte-identical to preflight_1156_eval_window.sql; requires
-- 1153–1155 recorded) → DDL → post-DDL definition verification.
--
-- ── F7 — window membership binds class and path/version, not just scope ──
-- ka_gochara_eval_window_record carries (chart_id, generation, event_class,
-- path_id, rule_version) and FKs BOTH ends on all of them: a P1/v1 marriage
-- window can hold only P1/v1 marriage records of the same chart and
-- generation (S:183–205: a window is per (path_id, rule_version) and per
-- class). ON DELETE CASCADE on both ends matches the per-(chart_id ×
-- generation) delete-then-insert rebuild ordering (§N.3) for CANDIDATE
-- generations; a sealed generation refuses the parent DELETE first (F2).
--
-- ── F7 — coverage applicability for windows ──────────────────────────────
-- Existence: composite FK to the window's own (chart, generation,
-- partition). Applicability (ka_gochara_window_coverage_guard): an
-- event_class partition's key must equal the window's class; the window's
-- interval must lie inside the partition's completed_horizon (a window
-- evaluated from records whose supports lie inside the searched horizon
-- cannot extend beyond it; a window open at the horizon end is clipped by
-- the writer to the horizon end).
--
-- ── Amendment 7 (kept) — score/interval contract ─────────────────────────
-- score ∈ [0,1] when computed (within-path product and cross-path max both
-- preserve it — S:167-170, 187-188, 209-213), NULL = explicitly unqualified
-- (NK-4); evidence finite and non-negative, no upper bound (F11: NaN/+inf
-- rejected); empty intervals rejected; a computed peak_instant lies inside
-- the window's interval (S:321-323, §7.2 inv 2); valence NOT NULL with
-- 'unqualified' as the honest state; null_states_used ⊆ {omit, unqualified}
-- with no NULL/blank element.
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK (1157 is independent; this before 1155):
--   DROP TABLE IF EXISTS ka_gochara_eval_window_record;
--   DROP TABLE IF EXISTS ka_gochara_eval_window;
--   DROP FUNCTION IF EXISTS ka_gochara_window_coverage_guard();
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1156_eval_window.sql) ────────────────
DO $$
DECLARE
  replay   boolean := COALESCE(current_setting('ka_gochara.deliberate_replay', true), '') = 'on';
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
    WHERE NOT replay AND n.nspname = 'public'
      AND c.relname IN ('ka_gochara_eval_window', 'ka_gochara_eval_window_pkey',
                        'kgew_membership_uq',
                        'ka_gochara_eval_window_record', 'ka_gochara_eval_window_record_pkey',
                        'idx_kgew_chart_gen', 'idx_kgew_path', 'idx_kgew_coverage',
                        'idx_kgewr_record')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_eval_window'
               AND t.tgname IN ('ka_gochara_ew_sealed_path_check', 'ka_gochara_ew_coverage_guard',
                                'ka_gochara_ew_sealed_generation_guard', 'ka_gochara_ew_no_truncate'))
         OR (c.relname = 'ka_gochara_eval_window_record'
               AND t.tgname IN ('ka_gochara_ewr_sealed_generation_guard', 'ka_gochara_ewr_no_truncate')) )
    UNION ALL
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES ('ka_gochara_window_coverage_guard', ARRAY[]::text[])) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE NOT replay
      AND (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('ka_gochara_rule_path'), ('ka_gochara_rule_path_seal'),
                 ('ka_gochara_relationship_record'), ('kala_gochara_coverage')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                         'id',                'uuid'),
                 ('ka_gochara_rule_path',           'path_id',           'text'),
                 ('ka_gochara_rule_path',           'rule_version',      'text'),
                 ('ka_gochara_relationship_record', 'record_id',         'uuid'),
                 ('ka_gochara_relationship_record', 'chart_id',          'uuid'),
                 ('ka_gochara_relationship_record', 'generation',        'text'),
                 ('ka_gochara_relationship_record', 'event_class',       'text'),
                 ('ka_gochara_relationship_record', 'path_id',           'text'),
                 ('ka_gochara_relationship_record', 'rule_version',      'text'),
                 ('kala_gochara_coverage',          'chart_id',          'uuid'),
                 ('kala_gochara_coverage',          'generation',        'text'),
                 ('kala_gochara_coverage',          'partition_kind',    'text'),
                 ('kala_gochara_coverage',          'partition_key',     'text'),
                 ('kala_gochara_coverage',          'completed_horizon', 'tstzrange')) AS e(t, col, typ)
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
                 ('ka_gochara_generation_is_sealed(uuid,text)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
       OR (SELECT format_type(p.prorettype, NULL) FROM pg_proc p
           WHERE p.oid = to_regprocedure('public.' || e.sig)) <> 'boolean'
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_require_sealed_rule_path()'),
                 ('ka_gochara_sealed_generation_guard()'),
                 ('ka_gochara_verify_definitions(text,jsonb)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_'), ('1155_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE NOT replay AND to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1156_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1156 BLOCKED — migration 1156 must NOT be applied:% %', E'\n', failures;
  END IF;
  IF replay THEN
    RAISE NOTICE 'preflight 1156: deliberate replay — existence checks skipped; definitions are verified post-DDL';
  END IF;
  RAISE NOTICE 'preflight 1156: all checks passed';
END;
$$;

-- ── 1. eval_window (§2.1 + §3.1) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_eval_window (
  window_id         UUID PRIMARY KEY,
  chart_id          UUID NOT NULL REFERENCES public.charts(id),
  event_class       TEXT NOT NULL,
  generation        TEXT NOT NULL,               -- '4.1'/'5.0'…; generation-scoped
  path_id           TEXT NOT NULL,               -- mandatory complete version-bound
  rule_version      TEXT NOT NULL,               --   reference (sealed version — F3)
  interval          TSTZRANGE NOT NULL,          -- the admitted window; never empty
  peak_instant      TIMESTAMPTZ,                 -- P4: argmax of min(activity_Jupiter,
                                                 --   activity_Saturn) over the overlap,
                                                 --   interior extrema (S:321-323, §7.2
                                                 --   inv 2, O-SM-4); ∈ interval when set
  score             REAL,                        -- ranks; never admits or excludes (§2);
                                                 --   NULL = explicitly unqualified (NK-4)
  evidence_for      REAL,                        -- §3.1: accumulates; never netted; finite ≥ 0
  evidence_against  REAL,                        -- §3.1: accumulates; never netted; finite ≥ 0
  outcome_valence_for_native TEXT NOT NULL,      -- §3.1: 'unqualified' is the declared
                                                 --   honest state — SQL NULL is not a valence
  severity          REAL,                        -- §3.1: interpretive, rank-only; finite
  coverage_partition_kind TEXT NOT NULL,         -- coverage partition handle (scope-bound)
  coverage_partition_key  TEXT NOT NULL,
  null_states_used  TEXT[] NOT NULL DEFAULT '{}',-- factor null_states exercised (§2.1),
                                                 --   never silent; ⊆ {omit, unqualified}
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgew_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
    -- D-SCOPE disposition: canonical chart only (S:89).
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
    -- the 27 classes of EVALUATION_PROTOCOL_v2_2 §2 — the sole enumeration
  CONSTRAINT kgew_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgew_interval_nonempty_ck CHECK (NOT isempty(interval)),
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
  CONSTRAINT kgew_coverage_kind_ck CHECK (coverage_partition_kind IN
    ('body_target','event_class','moon_on_demand','bodies_on_demand')),
  CONSTRAINT kgew_coverage_fk
    FOREIGN KEY (chart_id, generation, coverage_partition_kind, coverage_partition_key)
    REFERENCES public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key),
  CONSTRAINT kgew_null_states_ck
    CHECK (public.ka_gochara_text_array_ok(null_states_used, 0) IS TRUE
           AND null_states_used <@ ARRAY['omit','unqualified']::text[]),
  -- FK target for the scoped membership table (F7).
  CONSTRAINT kgew_membership_uq
    UNIQUE (window_id, chart_id, generation, event_class, path_id, rule_version)
);

COMMENT ON TABLE public.ka_gochara_eval_window IS
  'Evaluated window (GOCHARA_DESIGN_SPECS_v1_4 §2.1 eval_window contract + §3.1 valence '
  'fields): one evaluated interval per (chart, event_class, generation, path). Record '
  'membership is normalised into ka_gochara_eval_window_record, bound on both ends to '
  'the SAME chart, generation, event class and rule version (F7). score ∈ [0,1] when '
  'computed, NULL when unqualified; evidence finite, non-negative, never netted. Only a '
  'sealed rule version may produce a window (F3); coverage is proven applicable by '
  'trigger (F7); a sealed generation refuses UPDATE/DELETE (F2); TRUNCATE refused.';

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
  CONSTRAINT kgewr_window_fk
    FOREIGN KEY (window_id, chart_id, generation, event_class, path_id, rule_version)
    REFERENCES public.ka_gochara_eval_window (window_id, chart_id, generation, event_class, path_id, rule_version)
    ON DELETE CASCADE,
  CONSTRAINT kgewr_record_fk
    FOREIGN KEY (record_id, chart_id, generation, event_class, path_id, rule_version)
    REFERENCES public.ka_gochara_relationship_record (record_id, chart_id, generation, event_class, path_id, rule_version)
    ON DELETE CASCADE
    -- F7: membership can never cross chart, generation, event class or rule
    -- version; cascades match the §N.3 rebuild ordering for candidates
);

COMMENT ON TABLE public.ka_gochara_eval_window_record IS
  'Eval-window record membership (S:185 record_ids [FK] made structural; F7): one row '
  'per (window, contributing record), bound on both ends to the SAME (chart_id, '
  'generation, event_class, path_id, rule_version). ON DELETE CASCADE on both ends '
  'matches the per-(chart × generation) rebuild ordering for candidates; a sealed '
  'generation refuses the parent DELETE. TRUNCATE refused.';

CREATE INDEX IF NOT EXISTS idx_kgewr_record ON public.ka_gochara_eval_window_record
  (record_id);

-- ── 3. Coverage applicability for windows (F7) ─────────────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_window_coverage_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE cov record;
BEGIN
  SELECT c.partition_kind, c.partition_key, c.completed_horizon INTO cov
  FROM public.kala_gochara_coverage c
  WHERE c.chart_id = NEW.chart_id AND c.generation = NEW.generation
    AND c.partition_kind = NEW.coverage_partition_kind
    AND c.partition_key = NEW.coverage_partition_key;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage unresolvable (§2.1 coverage_ref): no kala_gochara_coverage partition (%, %) for (chart %, generation %)',
      NEW.coverage_partition_kind, NEW.coverage_partition_key, NEW.chart_id, NEW.generation;
  END IF;
  IF cov.partition_kind = 'event_class' AND cov.partition_key <> NEW.event_class THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage not applicable (F7): event_class partition ''%'' does not cover class ''%''',
      cov.partition_key, NEW.event_class;
  END IF;
  IF NOT (cov.completed_horizon @> NEW.interval) THEN
    RAISE EXCEPTION 'ka_gochara_eval_window coverage not applicable (F7): window interval % lies outside the partition''s completed_horizon %',
      NEW.interval, cov.completed_horizon;
  END IF;
  RETURN NEW;
END;
$$;

-- ── 4. Triggers ────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS ka_gochara_ew_sealed_path_check ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_sealed_path_check
  BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_eval_window
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
DROP TRIGGER IF EXISTS ka_gochara_ew_coverage_guard ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_coverage_guard
  BEFORE INSERT OR UPDATE ON public.ka_gochara_eval_window
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_window_coverage_guard();
DROP TRIGGER IF EXISTS ka_gochara_ew_sealed_generation_guard ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_sealed_generation_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_eval_window
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sealed_generation_guard();
DROP TRIGGER IF EXISTS ka_gochara_ew_no_truncate ON public.ka_gochara_eval_window;
CREATE TRIGGER ka_gochara_ew_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_eval_window
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_ewr_sealed_generation_guard ON public.ka_gochara_eval_window_record;
CREATE TRIGGER ka_gochara_ewr_sealed_generation_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_eval_window_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sealed_generation_guard();
DROP TRIGGER IF EXISTS ka_gochara_ewr_no_truncate ON public.ka_gochara_eval_window_record;
CREATE TRIGGER ka_gochara_ewr_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_eval_window_record
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 5. Post-DDL definition verification (F9) ───────────────────────────────
DO $$
BEGIN
  PERFORM public.ka_gochara_verify_definitions('1156', $expected$
{
  "functions": {
    "ka_gochara_window_coverage_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ]
  },
  "tables": {
    "ka_gochara_eval_window": {
      "columns": {
        "chart_id": [
          "uuid",
          true
        ],
        "coverage_partition_key": [
          "text",
          true
        ],
        "coverage_partition_kind": [
          "text",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "event_class": [
          "text",
          true
        ],
        "evidence_against": [
          "real",
          false
        ],
        "evidence_for": [
          "real",
          false
        ],
        "generation": [
          "text",
          true
        ],
        "interval": [
          "tstzrange",
          true
        ],
        "null_states_used": [
          "text[]",
          true
        ],
        "outcome_valence_for_native": [
          "text",
          true
        ],
        "path_id": [
          "text",
          true
        ],
        "peak_instant": [
          "timestamp with time zone",
          false
        ],
        "rule_version": [
          "text",
          true
        ],
        "score": [
          "real",
          false
        ],
        "severity": [
          "real",
          false
        ],
        "window_id": [
          "uuid",
          true
        ]
      },
      "constraints": {
        "ka_gochara_eval_window_chart_id_fkey": [
          "f",
          "foreignkeychart_idreferenceschartsid",
          true
        ],
        "ka_gochara_eval_window_pkey": [
          "p",
          "primarykeywindow_id",
          true
        ],
        "kgew_canonical_chart_ck": [
          "c",
          "checkchart_id='482012f1-710e-4a25-994a-93821f5871aa'",
          true
        ],
        "kgew_coverage_fk": [
          "f",
          "foreignkeychart_id,generation,coverage_partition_kind,coverage_partition_keyreferenceskala_gochara_coveragechart_id,generation,partition_kind,partition_key",
          true
        ],
        "kgew_coverage_kind_ck": [
          "c",
          "checkcoverage_partition_kind=anyarray['body_target','event_class','moon_on_demand','bodies_on_demand']",
          true
        ],
        "kgew_event_class_ck": [
          "c",
          "checkevent_class=anyarray['achievement_recognition','bereavement','birth_anchor','business_launch','career_advancement','career_change','career_entry','career_setback','childbirth','chronic_onset','education_milestone','exam_outcome','financial_deception','foreign_settlement','illness_acute','major_gain','major_loss','marriage','parental_event','property_acquisition','psychological_arc','relocation','romantic_start','separation','spiritual_turn','surgery','travel_event']",
          true
        ],
        "kgew_evidence_finite_ck": [
          "c",
          "checkka_gochara_finite_nonneg_okevidence_foristrueandka_gochara_finite_nonneg_okevidence_againstistrue",
          true
        ],
        "kgew_interval_nonempty_ck": [
          "c",
          "checknotisempty\"interval\"",
          true
        ],
        "kgew_membership_uq": [
          "u",
          "uniquewindow_id,chart_id,generation,event_class,path_id,rule_version",
          true
        ],
        "kgew_null_states_ck": [
          "c",
          "checkka_gochara_text_array_oknull_states_used,0istrueandnull_states_used<@array['omit','unqualified']",
          true
        ],
        "kgew_path_fk": [
          "f",
          "foreignkeypath_id,rule_versionreferenceska_gochara_rule_pathpath_id,rule_version",
          true
        ],
        "kgew_peak_in_interval_ck": [
          "c",
          "checkpeak_instantisnullorpeak_instant<@\"interval\"",
          true
        ],
        "kgew_score_unit_interval_ck": [
          "c",
          "checkscoreisnullorka_gochara_finite_okscoreistrueandscore>=0andscore<=1",
          true
        ],
        "kgew_severity_finite_ck": [
          "c",
          "checkka_gochara_finite_okseverityistrue",
          true
        ],
        "kgew_valence_ck": [
          "c",
          "checkoutcome_valence_for_native=anyarray['favourable','adverse','mixed','unqualified']",
          true
        ]
      },
      "indexes": {
        "idx_kgew_chart_gen": "createindexidx_kgew_chart_genonka_gochara_eval_windowusingbtreechart_id,generation,event_class,\"interval\"",
        "idx_kgew_coverage": "createindexidx_kgew_coverageonka_gochara_eval_windowusingbtreechart_id,generation,coverage_partition_kind,coverage_partition_key",
        "idx_kgew_path": "createindexidx_kgew_pathonka_gochara_eval_windowusingbtreepath_id,rule_version",
        "ka_gochara_eval_window_pkey": "createuniqueindexka_gochara_eval_window_pkeyonka_gochara_eval_windowusingbtreewindow_id",
        "kgew_membership_uq": "createuniqueindexkgew_membership_uqonka_gochara_eval_windowusingbtreewindow_id,chart_id,generation,event_class,path_id,rule_version"
      },
      "triggers": {
        "ka_gochara_ew_coverage_guard": [
          "createtriggerka_gochara_ew_coverage_guardbeforeinsertorupdateonka_gochara_eval_windowforeachrowexecutefunctionka_gochara_window_coverage_guard",
          "O"
        ],
        "ka_gochara_ew_no_truncate": [
          "createtriggerka_gochara_ew_no_truncatebeforetruncateonka_gochara_eval_windowforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_ew_sealed_generation_guard": [
          "createtriggerka_gochara_ew_sealed_generation_guardbeforedeleteorupdateonka_gochara_eval_windowforeachrowexecutefunctionka_gochara_sealed_generation_guard",
          "O"
        ],
        "ka_gochara_ew_sealed_path_check": [
          "createtriggerka_gochara_ew_sealed_path_checkbeforeinsertorupdateofpath_id,rule_versiononka_gochara_eval_windowforeachrowexecutefunctionka_gochara_require_sealed_rule_path",
          "O"
        ]
      }
    },
    "ka_gochara_eval_window_record": {
      "columns": {
        "chart_id": [
          "uuid",
          true
        ],
        "event_class": [
          "text",
          true
        ],
        "generation": [
          "text",
          true
        ],
        "path_id": [
          "text",
          true
        ],
        "record_id": [
          "uuid",
          true
        ],
        "rule_version": [
          "text",
          true
        ],
        "window_id": [
          "uuid",
          true
        ]
      },
      "constraints": {
        "ka_gochara_eval_window_record_pkey": [
          "p",
          "primarykeywindow_id,record_id",
          true
        ],
        "kgewr_record_fk": [
          "f",
          "foreignkeyrecord_id,chart_id,generation,event_class,path_id,rule_versionreferenceska_gochara_relationship_recordrecord_id,chart_id,generation,event_class,path_id,rule_versionondeletecascade",
          true
        ],
        "kgewr_window_fk": [
          "f",
          "foreignkeywindow_id,chart_id,generation,event_class,path_id,rule_versionreferenceska_gochara_eval_windowwindow_id,chart_id,generation,event_class,path_id,rule_versionondeletecascade",
          true
        ]
      },
      "indexes": {
        "idx_kgewr_record": "createindexidx_kgewr_recordonka_gochara_eval_window_recordusingbtreerecord_id",
        "ka_gochara_eval_window_record_pkey": "createuniqueindexka_gochara_eval_window_record_pkeyonka_gochara_eval_window_recordusingbtreewindow_id,record_id"
      },
      "triggers": {
        "ka_gochara_ewr_no_truncate": [
          "createtriggerka_gochara_ewr_no_truncatebeforetruncateonka_gochara_eval_window_recordforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_ewr_sealed_generation_guard": [
          "createtriggerka_gochara_ewr_sealed_generation_guardbeforedeleteorupdateonka_gochara_eval_window_recordforeachrowexecutefunctionka_gochara_sealed_generation_guard",
          "O"
        ]
      }
    }
  }
}
$expected$::jsonb);
END;
$$;
