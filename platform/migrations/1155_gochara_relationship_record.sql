-- Migration 1155: ka_gochara_relationship_record — the §1.1 typed contract
--                 + §3.1 valence fields + admission persistence, with
--                 ownership-bound contact references (F1/F7), coverage
--                 APPLICABILITY bound to an UNAMBIGUOUS snapshot of the
--                 coverage facts (F7/N10/N14), commit-time qualification
--                 finalisation (F5) with membership reparenting prohibited
--                 (N8), sealed-generation freezing (F2/N9), sealed-rule-version
--                 references (F3/N5) and coherent enrichment of dependent
--                 precision that survives a later coverage extension (N7/N15)
--                 — every write under the Gochara-5 chart family key, then the
--                 global family key SHARED (steward ruling B); finite AD-era
--                 horizons only (N17/N19). Depends on 1153, 1154 and
--                 1081/1087 (kala_gochara_coverage). Round-7 per
--                 ASTRA_REVIEW_A5_1_MIGRATIONS v1_5 on rounds 5–6 under the
--                 steward's corrected lock ruling. Never applied anywhere —
--                 in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1155 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Gate: pinned schema → preflight gate (byte-identical
-- to preflight_1155_relationship_record.sql; requires 1153 and 1154
-- recorded) → DDL → presence checks. Deploy route: the protected
-- public-schema window (deploy.yml `gochara_contracts_schema_migration`).
--
-- ── Lock order (steward ruling B; N12/N13) ─────────────────────────────────
-- Chart-scoped tables: a BEFORE UPDATE OR DELETE **statement-level** trigger
-- (`_0_statement_lock`, ka_gochara_chart_statement_lock) takes the chart
-- family key BEFORE PostgreSQL locks any target tuple (N13). Row triggers
-- then fire in name order: `_1_write_guard` (ka_gochara_chart_write_guard)
-- takes the chart family key (INSERT) / re-enters it, reads seal state and
-- applies the sealed-generation rules; `_2_coverage_guard` validates
-- applicability; `_3_sealed_path_check` takes the global family key SHARED
-- (chart EXCLUSIVE → global SHARED, always) and reads the rule-version seal.
-- The orchestrator's session key is never taken (N12). Isolation other than
-- READ COMMITTED is refused by the lock helpers.
--
-- ── F2/N9 — a published generation's record set is FROZEN ─────────────────
-- Once (chart_id, generation) is sealed: INSERT, UPDATE and DELETE on
-- records, prerequisite membership, windows and window membership are
-- refused (a re-evaluation is a new generation). The ONE exception is N7's
-- precision re-sync (below). Contacts keep their spec-explicit append.
--
-- ── N7/N15 — enrichment stays coherent, and survives a coverage extension ─
-- A record's `precision` restates its contact's solved precision (§1.1;
-- CLAUDE.md §N.5). When a contact is enriched in place (§6.1: the truncated
-- centre is solved — t_exact / solver_method / δλ / δt change), an AFTER
-- UPDATE trigger on ka_gochara_contact re-states the new precision into
-- every dependent record of the same (chart, generation, contact) — sealed
-- generations included: the chart guard permits, on a sealed generation,
-- exactly an UPDATE that changes `precision` alone. For that precision-only
-- UPDATE the coverage guard re-verifies ONLY that the new payload equals the
-- contact's; it does NOT re-validate the partition (N15): the row's
-- `coverage_facts` is the snapshot it was validated against at write time
-- and stays so — a horizon extended after the fact (the ledger's own
-- extend-then-enrich sequence) can no longer break the propagation. A direct
-- UPDATE that sets a precision DIFFERENT from the contact's is refused by the
-- restatement check; any other UPDATE of a sealed row is refused by the
-- chart guard.
--
-- ── N8 — membership reparenting prohibited ────────────────────────────────
-- ka_gochara_record_prerequisite may change ONLY `result` on UPDATE
-- (record_id / chart_id / generation / ordinal / predicate are immutable);
-- both the record and its membership are finalised at COMMIT by DEFERRABLE
-- constraint triggers (membership = the path version's declared list, in
-- order; admission_state = the state derived from the results).
--
-- ── F7/N10/N14 — coverage applicability bound to the facts checked ───────
-- The composite FK (chart_id, generation, partition_kind, partition_key) →
-- kala_gochara_coverage proves the partition exists in the record's own
-- scope. Applicability (ka_gochara_record_coverage_guard) additionally
-- requires, at INSERT and at every non-precision-only UPDATE:
--   * `coverage_facts` = ka_gochara_coverage_facts(convention_id,
--     completed_horizon, relations_searched) of the partition as it stands —
--     an UNAMBIGUOUS JSON encoding over the ACCEPTED DOMAIN (N14/N17/N19):
--     the Gochara-5 contract admits finite, bounded, non-empty horizons
--     whose bounds lie within 1000-01-01 ≤ t < 3000-01-01 UTC, AD only
--     (ka_gochara_horizon_finite_ok, 1153); the encoder RAISES on an empty
--     range, an omitted bound, a ±infinity bound, a BC bound or an
--     out-of-range year, so within the domain the four-digit AD ISO-8601
--     'YYYY-MM-DDTHH:MI:SS.USZ' text is a lossless bijection — no two
--     accepted horizons share an encoding and every one round-trips exactly
--     (`lower`/`upper` + inclusivity flags);
--     relations_searched is a sorted JSON array whose elements are JSON
--     strings or null, so ['conjunction'] ≠ ['conjunction', NULL] and
--     ['aspect','conjunction'] ≠ ['aspect,conjunction']. Nothing is hashed;
--     the stored facts are readable and comparable with jsonb equality.
--     The coverage guard refuses a partition whose completed_horizon is not
--     finite (N17) before encoding it; window intervals and record support
--     intervals CHECK the same predicate.
--   * THE CONSUMER CONTRACT for parent facts changed AFTER validation (N10):
--     steward ruling 1 forbids any trigger on the legacy coverage table, so a
--     later change to the partition cannot be blocked there. Instead:
--     (1) ka_gochara_coverage_drift(chart_id, generation) (1156, over records
--     AND windows) classifies every consumer against its partition's CURRENT
--     facts as `identical` | `extended` (same convention, horizon ⊇, relations
--     ⊇ — still valid) | `incompatible` | `partition_missing`;
--     (2) ka_gochara_seal_generation REFUSES to seal while any consumer is
--     `incompatible`/`partition_missing`, so nothing incompatible is ever
--     published; (3) a serve-time consumer reads the drift view and treats
--     `incompatible` as "re-validate before use" — the stored facts are the
--     evidence of what was validated, never silently refreshed.
--   * relations_searched with a NULL element is inapplicable outright, and
--     the relation-membership predicate is evaluated `IS TRUE` (N10);
--   * event_class partition ⇒ key = event_class; body_target partition ⇒ key
--     = agent || ':' || object_role EXACTLY (the full key, N10 — for governed
--     generations the writer keys body_target partitions by agent and
--     interpretive role);
--   * transit rows: agent = 'moon' ⇔ moon_on_demand; relation ∈
--     relations_searched; the partition's legacy convention is bridged to the
--     contact's sky convention; the contact's t_in lies inside
--     completed_horizon; a well-formed precision payload restates the contact
--     (a malformed one is the CHECK's finding);
--   * natal-fact rows never reference moon_on_demand coverage;
--   * every computed support interval lies inside completed_horizon.
--
-- ── F11 (kept) — fact-id resolvability is a writer-boundary obligation ───
-- source_fact_ids: typed non-empty whitespace-free string array, [] only on
-- fixture rows. RESOLVABILITY of those ids (L0/L1 chart_facts.fact_id or a
-- pinned extract row id) is a WRITER-BOUNDARY obligation stated here
-- explicitly: the spec admits extract-row ids and synthetic fixtures, so no
-- single table can be the FK target; the writer resolves every id it emits
-- (CLAUDE.md §N.5) and the A5.5 rehearsal asserts it.
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK (dependents first; 1156/1157 before this):
--   DROP TRIGGER IF EXISTS ka_gochara_contact_2_propagate_precision ON ka_gochara_contact;
--   DROP TABLE IF EXISTS ka_gochara_record_prerequisite;
--   DROP TABLE IF EXISTS ka_gochara_relationship_record;
--   DROP FUNCTION IF EXISTS ka_gochara_contact_propagate_precision();
--   DROP FUNCTION IF EXISTS ka_gochara_record_finalize_check();
--   DROP FUNCTION IF EXISTS ka_gochara_record_coverage_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_chart_write_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_facts_horizon(jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_coverage_facts(text, tstzrange, text[]);
--   DROP FUNCTION IF EXISTS ka_gochara_intervals_ok(tstzrange[]);
--   DROP FUNCTION IF EXISTS ka_gochara_precision_ok(jsonb);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1155_relationship_record.sql) ────────
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
      AND c.relname IN ('ka_gochara_relationship_record', 'ka_gochara_relationship_record_pkey',
                        'kgrr_identity_uq', 'kgrr_membership_uq',
                        'ka_gochara_record_prerequisite', 'ka_gochara_record_prerequisite_pkey',
                        'kgrpr_no_dup_uq',
                        'idx_kgrr_chart_gen', 'idx_kgrr_contact', 'idx_kgrr_object',
                        'idx_kgrr_path', 'idx_kgrr_coverage', 'idx_kgrpr_record')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_relationship_record'
               AND t.tgname IN ('ka_gochara_rr_0_statement_lock',
                                'ka_gochara_rr_1_write_guard', 'ka_gochara_rr_2_coverage_guard',
                                'ka_gochara_rr_3_sealed_path_check', 'ka_gochara_rr_finalize',
                                'ka_gochara_rr_no_truncate'))
         OR (c.relname = 'ka_gochara_record_prerequisite'
               AND t.tgname IN ('ka_gochara_rpr_0_statement_lock',
                                'ka_gochara_rpr_1_write_guard', 'ka_gochara_rpr_finalize',
                                'ka_gochara_rpr_no_truncate'))
         OR (c.relname = 'ka_gochara_contact'
               AND t.tgname = 'ka_gochara_contact_2_propagate_precision') )
    UNION ALL
    -- function collisions by EXACT ARGUMENT TYPES (F8) — this file's own helpers
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_precision_ok',                ARRAY['jsonb']),
            ('ka_gochara_intervals_ok',                ARRAY['tstzrange[]']),
            ('ka_gochara_coverage_facts',              ARRAY['text','tstzrange','text[]']),
            ('ka_gochara_facts_horizon',               ARRAY['jsonb']),
            ('ka_gochara_chart_write_guard',           ARRAY[]::text[]),
            ('ka_gochara_record_coverage_guard',       ARRAY[]::text[]),
            ('ka_gochara_record_finalize_check',       ARRAY[]::text[]),
            ('ka_gochara_contact_propagate_precision', ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- (b1) parents exist
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('kala_gochara_coverage'), ('ka_gochara_contact'),
                 ('ka_gochara_physical_object'), ('ka_gochara_rule_path'),
                 ('ka_gochara_rule_path_seal'), ('ka_gochara_predicate'),
                 ('ka_gochara_convention_bridge'), ('ka_gochara_generation_seal')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    -- (b2) parent columns with expected types (the coverage columns the
    -- applicability guard reads are included)
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                     'id',                 'uuid'),
                 ('kala_gochara_coverage',      'chart_id',           'uuid'),
                 ('kala_gochara_coverage',      'generation',         'text'),
                 ('kala_gochara_coverage',      'partition_kind',     'text'),
                 ('kala_gochara_coverage',      'partition_key',      'text'),
                 ('kala_gochara_coverage',      'convention_id',      'text'),
                 ('kala_gochara_coverage',      'completed_horizon',  'tstzrange'),
                 ('kala_gochara_coverage',      'relations_searched', 'text[]'),
                 ('ka_gochara_contact',         'chart_id',           'uuid'),
                 ('ka_gochara_contact',         'generation',         'text'),
                 ('ka_gochara_contact',         'contact_id',         'uuid'),
                 ('ka_gochara_contact',         'body',               'text'),
                 ('ka_gochara_contact',         'relation_kind',      'text'),
                 ('ka_gochara_contact',         'physical_object_id', 'uuid'),
                 ('ka_gochara_contact',         'convention_id',      'text'),
                 ('ka_gochara_contact',         't_in',               'timestamp with time zone'),
                 ('ka_gochara_contact',         'solver_method',      'text'),
                 ('ka_gochara_contact',         'delta_lambda',       'real'),
                 ('ka_gochara_contact',         'delta_t',            'real'),
                 ('ka_gochara_physical_object', 'physical_object_id', 'uuid'),
                 ('ka_gochara_rule_path',       'path_id',            'text'),
                 ('ka_gochara_rule_path',       'rule_version',       'text'),
                 ('ka_gochara_predicate',       'predicate_id',       'text'),
                 ('ka_gochara_predicate',       'rule_version',       'text'),
                 ('ka_gochara_convention_bridge','kala_convention_id', 'text'),
                 ('ka_gochara_convention_bridge','sky_convention_id',  'text')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified against pg_constraint
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                     ARRAY['id']),
                 ('kala_gochara_coverage',      ARRAY['chart_id','generation','partition_kind','partition_key']),
                 ('ka_gochara_contact',         ARRAY['chart_id','generation','contact_id','body','relation_kind','physical_object_id']),
                 ('ka_gochara_physical_object', ARRAY['physical_object_id']),
                 ('ka_gochara_rule_path',       ARRAY['path_id','rule_version']),
                 ('ka_gochara_rule_path_seal',  ARRAY['path_id','rule_version']),
                 ('ka_gochara_predicate',       ARRAY['predicate_id','rule_version']),
                 ('ka_gochara_convention_bridge', ARRAY['kala_convention_id'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    -- (b4) helper functions with exact signatures AND boolean return
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_frame_ok(text,text)'),
                 ('ka_gochara_string_array_ok(jsonb)'),
                 ('ka_gochara_finite_ok(double precision)'),
                 ('ka_gochara_finite_nonneg_ok(double precision)'),
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
                 ('ka_gochara_require_sealed_rule_path()')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    -- (c1) ordered execution gate
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_'), ('1154_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1155_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1155 BLOCKED — migration 1155 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1155: all checks passed';
END;
$$;

-- ── 0. Helpers — TOTAL booleans (F5) + the coverage facts (N10/N14) ───────

CREATE OR REPLACE FUNCTION public.ka_gochara_precision_ok(p jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT p IS NOT NULL
     AND jsonb_typeof(p) = 'object'
     AND (p - 'solver_method' - 'delta_lambda' - 'delta_t') = '{}'::jsonb
     AND jsonb_typeof(p -> 'solver_method') = 'string'
     AND (p ->> 'solver_method') IN ('arc_index_bracket','swiss_refined','clipped_truncated')
     AND p ? 'delta_lambda' AND p ? 'delta_t'
     AND CASE WHEN (p ->> 'solver_method') = 'clipped_truncated'
              THEN jsonb_typeof(p -> 'delta_lambda') = 'null'
               AND jsonb_typeof(p -> 'delta_t') = 'null'
              ELSE jsonb_typeof(p -> 'delta_lambda') = 'number'
               AND jsonb_typeof(p -> 'delta_t') = 'number'
               AND (p ->> 'delta_lambda')::numeric >= 0
               AND (p ->> 'delta_t')::numeric >= 0
         END;
$$;

-- Support intervals: every element a finite, bounded, non-empty range (N17).
CREATE OR REPLACE FUNCTION public.ka_gochara_intervals_ok(iv tstzrange[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT iv IS NOT NULL
     AND NOT EXISTS (
       SELECT 1 FROM unnest(iv) r
       WHERE public.ka_gochara_horizon_finite_ok(r) IS NOT TRUE
     );
$$;

-- The UNAMBIGUOUS coverage-facts snapshot a consumer binds to (N10/N14),
-- defined over the ACCEPTED DOMAIN only (N17/N19): the horizon must be
-- finite, bounded, non-empty, with every bound in 1000-01-01 ≤ t <
-- 3000-01-01 UTC, AD (ka_gochara_horizon_finite_ok) — anything else RAISES,
-- so the encoding never meets an omitted bound, an empty range, a ±infinity
-- timestamp, a BC year or a year outside [1000, 3000); within the domain
-- 'YYYY' is always four AD digits and the text is a lossless bijection.
-- The writer computes it with this same function from the partition row it
-- consumed; the guard recomputes it and compares with jsonb equality.
--   {"convention_id": text|null,
--    "horizon": {"lower": "YYYY-MM-DDTHH:MI:SS.USZ", "lower_inc": bool,
--                "upper": "YYYY-MM-DDTHH:MI:SS.USZ", "upper_inc": bool},
--    "relations_searched": null | [ sorted JSON strings / nulls, duplicates kept ]}
-- STABLE, not IMMUTABLE: it calls to_char/AT TIME ZONE, which PostgreSQL marks
-- STABLE; the output itself is deterministic (explicit UTC, numeric-only
-- format tokens, ISO-8601 input) and independent of DateStyle/TimeZone/lc_time.
CREATE OR REPLACE FUNCTION public.ka_gochara_coverage_facts(p_convention_id text, p_completed_horizon tstzrange, p_relations_searched text[])
RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
BEGIN
  IF public.ka_gochara_horizon_finite_ok(p_completed_horizon) IS NOT TRUE THEN
    RAISE EXCEPTION 'ka_gochara_coverage_facts: unsupported horizon % (N17/N19): the Gochara-5 coverage contract admits finite, bounded, non-empty horizons with every bound within 1000-01-01 <= t < 3000-01-01 UTC (AD) only — no omitted bound, no empty range, no ±infinity bound, no BC or out-of-range year',
      p_completed_horizon;
  END IF;
  RETURN jsonb_build_object(
    'convention_id', p_convention_id,
    'horizon', jsonb_build_object(
      'lower', to_char(lower(p_completed_horizon) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
      'lower_inc', lower_inc(p_completed_horizon),
      'upper', to_char(upper(p_completed_horizon) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
      'upper_inc', upper_inc(p_completed_horizon)),
    'relations_searched',
      CASE
        WHEN p_relations_searched IS NULL THEN NULL::jsonb
        ELSE (SELECT COALESCE(jsonb_agg(to_jsonb(x) ORDER BY x NULLS FIRST), '[]'::jsonb)
              FROM unnest(p_relations_searched) x)
      END);
END;
$$;

COMMENT ON FUNCTION public.ka_gochara_coverage_facts(text, tstzrange, text[]) IS
  'Unambiguous JSON snapshot of (convention_id, completed_horizon, relations_searched) '
  '(N10/N14/N17/N19) over the accepted domain: finite, bounded, non-empty horizons with '
  'bounds in 1000-01-01 <= t < 3000-01-01 UTC (AD) only (RAISES otherwise — the encoding '
  'never meets infinity or a BC year; within the domain it is a lossless bijection); bounds as ISO-8601 UTC '
  'microsecond text + inclusivity flags; relations as a sorted JSON array of strings/nulls '
  '(element boundaries and NULLs preserved). A record/window stores the snapshot it was '
  'validated against; the guard recomputes it from the partition and compares with jsonb '
  'equality; ka_gochara_coverage_drift classifies later parent changes.';

-- Inverse of the horizon encoding — used by the drift classifier and the
-- window membership guard (1156). Exact to the microsecond.
CREATE OR REPLACE FUNCTION public.ka_gochara_facts_horizon(f jsonb)
RETURNS tstzrange LANGUAGE sql STABLE AS $$
  SELECT CASE
    WHEN f IS NULL OR jsonb_typeof(f -> 'horizon') IS DISTINCT FROM 'object' THEN NULL::tstzrange
    ELSE tstzrange(
      (f -> 'horizon' ->> 'lower')::timestamptz,
      (f -> 'horizon' ->> 'upper')::timestamptz,
      (CASE WHEN (f -> 'horizon' ->> 'lower_inc')::boolean THEN '[' ELSE '(' END)
      || (CASE WHEN (f -> 'horizon' ->> 'upper_inc')::boolean THEN ']' ELSE ')' END))
  END;
$$;

-- Generic chart-scoped write guard (records, prerequisites, windows,
-- membership): chart family key FIRST, then the sealed-generation rules.
--   TG_ARGV[0] mode: 'plain' | 'precision_sync' | 'result_only' | 'no_update'
-- UPDATE/DELETE reach this row trigger with the chart family key already
-- taken by the table's `_0_statement_lock` trigger (N13); INSERT takes it here.
CREATE OR REPLACE FUNCTION public.ka_gochara_chart_write_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  mode   text := COALESCE(TG_ARGV[0], 'plain');
  sealed boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    PERFORM public.ka_gochara_lock_chart(OLD.chart_id);
    IF public.ka_gochara_generation_is_sealed(OLD.chart_id, OLD.generation) THEN
      RAISE EXCEPTION '% is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §10.1; F2/N9): (chart_id %, generation %) is SEALED (was published) — DELETE refused; a re-evaluation is a new generation',
        TG_TABLE_NAME, OLD.chart_id, OLD.generation;
    END IF;
    RETURN OLD;
  END IF;

  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);
  sealed := public.ka_gochara_generation_is_sealed(NEW.chart_id, NEW.generation);

  IF TG_OP = 'INSERT' THEN
    IF sealed THEN
      RAISE EXCEPTION '% is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §10.1; N9): (chart_id %, generation %) is SEALED (was published) — INSERT refused; the records, prerequisites, windows and window membership of a published generation are a FROZEN set; a re-evaluation is a new generation',
        TG_TABLE_NAME, NEW.chart_id, NEW.generation;
    END IF;
    RETURN NEW;
  END IF;

  -- UPDATE
  IF NEW.chart_id <> OLD.chart_id OR NEW.generation <> OLD.generation THEN
    RAISE EXCEPTION '% ownership scope (chart_id, generation) is immutable (N8/N9): nothing moves across scopes',
      TG_TABLE_NAME;
  END IF;
  IF mode = 'no_update' THEN
    RAISE EXCEPTION '% rows are immutable (N8/N9): UPDATE refused — membership is written once with its window',
      TG_TABLE_NAME;
  END IF;
  IF mode = 'result_only' AND (to_jsonb(NEW) - 'result') <> (to_jsonb(OLD) - 'result') THEN
    RAISE EXCEPTION '% may change only `result` (N8): membership reparenting (record_id/ordinal/predicate) is prohibited',
      TG_TABLE_NAME;
  END IF;
  IF sealed THEN
    IF mode = 'precision_sync' AND (to_jsonb(NEW) - 'precision') = (to_jsonb(OLD) - 'precision') THEN
      RETURN NEW;   -- N7: the restated precision may re-sync to its enriched contact; nothing else
    END IF;
    RAISE EXCEPTION '% is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §10.1; F2): (chart_id %, generation %) is SEALED (was published) — UPDATE refused',
      TG_TABLE_NAME, NEW.chart_id, NEW.generation;
  END IF;
  RETURN NEW;
END;
$$;

-- ── 1. relationship_record (§1.1 + §3.1 + admission persistence) ──────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_relationship_record (
  record_id         UUID PRIMARY KEY,
  -- §1.1: deterministic hash of the natural key (chart_id, generation,
  -- event_class, affected_person, frame, agent, relation, object_id,
  -- object_role, contact_id, path_id, rule_version, prerequisites,
  -- source_text). Writer-computed, not re-implemented in SQL.
  chart_id          UUID NOT NULL REFERENCES public.charts(id),
  generation        TEXT NOT NULL,               -- governed generation (major >= 5)
  contact_id        UUID,                        -- NOT NULL on transit rows (CHECK)
  event_class       TEXT NOT NULL,
  affected_person   TEXT NOT NULL,
  frame_kind        TEXT NOT NULL,
  frame_arg         TEXT,
  agent             TEXT NOT NULL,
  relation          TEXT NOT NULL,
  object_id         UUID NOT NULL REFERENCES public.ka_gochara_physical_object(physical_object_id),
  object_kind       TEXT NOT NULL,
  object_role       TEXT NOT NULL,
  path_id           TEXT NOT NULL,               -- sealed rule version (F3/N5)
  rule_version      TEXT NOT NULL,
  temporal_support_state TEXT NOT NULL,
  temporal_support_grain TEXT,
  temporal_support_intervals TSTZRANGE[] NOT NULL DEFAULT '{}',
  coverage_partition_kind TEXT NOT NULL,         -- the 1081 partition, scope-bound (FK)
  coverage_partition_key  TEXT NOT NULL,
  coverage_facts    JSONB NOT NULL,              -- N10/N14: the partition facts this row
                                                 --   was validated against (snapshot)
  precision         JSONB,                       -- {solver_method, delta_lambda, delta_t};
                                                 --   REQUIRED on transit rows; restates
                                                 --   the contact (guard; N7 propagation)
  source_text       TEXT,
  source_page       TEXT,
  source_fact_ids   JSONB NOT NULL,
  fixture           BOOLEAN NOT NULL DEFAULT false,
  provenance        TEXT NOT NULL,
  operator_role     TEXT NOT NULL,
  ruling_ref        TEXT,
  admission_state   TEXT NOT NULL,               -- finalised at COMMIT (F5)
  house_from_frame  INTEGER,                     -- §1.2 inv 5
  evidence_for_occurrence     REAL,
  evidence_against_occurrence REAL,
  outcome_valence_for_native  TEXT NOT NULL,
  severity          REAL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgrr_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgrr_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgrr_event_class_ck CHECK (event_class IN (
    'achievement_recognition','bereavement','birth_anchor',
    'business_launch','career_advancement','career_change',
    'career_entry','career_setback','childbirth',
    'chronic_onset','education_milestone','exam_outcome',
    'financial_deception','foreign_settlement','illness_acute',
    'major_gain','major_loss','marriage','parental_event',
    'property_acquisition','psychological_arc','relocation',
    'romantic_start','separation','spiritual_turn','surgery',
    'travel_event')),
  CONSTRAINT kgrr_affected_person_ck CHECK (affected_person IN
    ('native','father','mother','spouse','child','sibling')),
  CONSTRAINT kgrr_frame_ck CHECK (public.ka_gochara_frame_ok(frame_kind, frame_arg) IS TRUE),
  CONSTRAINT kgrr_relative_frame_ck
    CHECK (affected_person = 'native' OR frame_kind <> 'moon'),
  CONSTRAINT kgrr_agent_ck CHECK (agent IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgrr_relation_ck CHECK (relation IN
    ('residence','aspect','conjunction',
     'dispositorship','association','ownership','occupancy','period_running')),
  CONSTRAINT kgrr_object_kind_ck CHECK (object_kind IN
    ('degree_point','sign_span','star','derived_point',
     'varga_position','saham','house_span','house_lord')),
  CONSTRAINT kgrr_object_role_ck CHECK (object_role IN
    ('lord','occupant','karaka','dispositor','maraka_of_house',
     'period_lord','yoga_constituent','pada','signature_house')),
  CONSTRAINT kgrr_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgrr_contact_fk
    FOREIGN KEY (chart_id, generation, contact_id, agent, relation, object_id)
    REFERENCES public.ka_gochara_contact (chart_id, generation, contact_id, body, relation_kind, physical_object_id),
  CONSTRAINT kgrr_coverage_fk
    FOREIGN KEY (chart_id, generation, coverage_partition_kind, coverage_partition_key)
    REFERENCES public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key),
  CONSTRAINT kgrr_coverage_kind_ck CHECK (coverage_partition_kind IN
    ('body_target','event_class','moon_on_demand','bodies_on_demand')),
  CONSTRAINT kgrr_coverage_facts_shape_ck
    CHECK (jsonb_typeof(coverage_facts) = 'object'
           AND coverage_facts ? 'convention_id' AND coverage_facts ? 'horizon'
           AND coverage_facts ? 'relations_searched'),
  CONSTRAINT kgrr_support_state_ck CHECK (temporal_support_state IN
    ('uncomputed','computed_empty','computed')),
  CONSTRAINT kgrr_support_cardinality_ck CHECK (
    (temporal_support_state = 'uncomputed'
       AND temporal_support_grain IS NULL
       AND COALESCE(array_length(temporal_support_intervals, 1), 0) = 0)
    OR (temporal_support_state = 'computed_empty'
       AND temporal_support_grain IS NOT NULL
       AND COALESCE(array_length(temporal_support_intervals, 1), 0) = 0)
    OR (temporal_support_state = 'computed'
       AND temporal_support_grain IS NOT NULL
       AND COALESCE(array_length(temporal_support_intervals, 1), 0) >= 1)
  ),
  CONSTRAINT kgrr_support_intervals_ck
    CHECK (public.ka_gochara_intervals_ok(temporal_support_intervals) IS TRUE),
  CONSTRAINT kgrr_house_from_frame_ck
    CHECK (house_from_frame IS NULL OR house_from_frame BETWEEN 1 AND 12),
  CONSTRAINT kgrr_evaluated_has_house_ck
    CHECK (temporal_support_state = 'uncomputed' OR house_from_frame IS NOT NULL),
  CONSTRAINT kgrr_precision_typed_ck
    CHECK (precision IS NULL OR public.ka_gochara_precision_ok(precision) IS TRUE),
  CONSTRAINT kgrr_transit_natal_ck CHECK (
    (relation IN ('residence','aspect','conjunction')
       AND contact_id IS NOT NULL AND precision IS NOT NULL)
    OR
    (relation IN ('dispositorship','association','ownership','occupancy',
                  'period_running')
       AND contact_id IS NULL AND precision IS NULL)
  ),
  CONSTRAINT kgrr_source_fact_ids_ck
    CHECK (public.ka_gochara_string_array_ok(source_fact_ids) IS TRUE
           AND (jsonb_array_length(source_fact_ids) > 0 OR fixture)),
  CONSTRAINT kgrr_provenance_ck CHECK (provenance IN ('verse_cited','uncited_extension')),
  CONSTRAINT kgrr_operator_role_ck CHECK (operator_role IN ('scored','testimony')),
  CONSTRAINT kgrr_ruling_ck
    CHECK (provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL),
  CONSTRAINT kgrr_citation_ck
    CHECK (provenance <> 'verse_cited'
           OR (source_text IS NOT NULL AND source_page IS NOT NULL)),
  CONSTRAINT kgrr_admission_state_ck CHECK (admission_state IN
    ('admitted','unqualified','not_admitted')),
  CONSTRAINT kgrr_evidence_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(evidence_for_occurrence) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(evidence_against_occurrence) IS TRUE),
  CONSTRAINT kgrr_severity_finite_ck
    CHECK (public.ka_gochara_finite_ok(severity) IS TRUE),
  CONSTRAINT kgrr_valence_ck CHECK (outcome_valence_for_native IN
    ('favourable','adverse','mixed','unqualified')),
  CONSTRAINT kgrr_identity_uq UNIQUE (record_id, chart_id, generation),
  CONSTRAINT kgrr_membership_uq
    UNIQUE (record_id, chart_id, generation, event_class, path_id, rule_version)
);

COMMENT ON TABLE public.ka_gochara_relationship_record IS
  'Relationship record (GOCHARA_DESIGN_SPECS_v1_4 §1.1): one row per (event_class, '
  'affected_person, frame, agent, relation, object, role, path). Transit rows FK the '
  'OWNED contact ledger row with agent/relation/object consistency (F1/F7); coverage is an '
  'existing (chart, generation, partition) row, proven APPLICABLE and bound by an '
  'unambiguous facts snapshot (F7/N10/N14; drift classified by ka_gochara_coverage_drift). '
  'admission_state + ka_gochara_record_prerequisite.result are finalised at COMMIT (F5); '
  'membership reparenting is prohibited (N8). Only a sealed rule version may produce a row '
  '(F3/N5). A sealed generation freezes the row set (F2/N9); precision re-syncs from '
  'contact enrichment without re-validating coverage (N7/N15). Every write takes the '
  'Gochara-5 chart family key first (statement-level for UPDATE/DELETE), then the global '
  'family key SHARED. TRUNCATE refused.';

CREATE INDEX IF NOT EXISTS idx_kgrr_chart_gen ON public.ka_gochara_relationship_record
  (chart_id, generation, event_class);
CREATE INDEX IF NOT EXISTS idx_kgrr_contact ON public.ka_gochara_relationship_record
  (chart_id, generation, contact_id) WHERE contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kgrr_object ON public.ka_gochara_relationship_record
  (object_id);
CREATE INDEX IF NOT EXISTS idx_kgrr_path ON public.ka_gochara_relationship_record
  (path_id, rule_version);
CREATE INDEX IF NOT EXISTS idx_kgrr_coverage ON public.ka_gochara_relationship_record
  (chart_id, generation, coverage_partition_kind, coverage_partition_key);

-- ── 2. Prerequisite membership + evaluated results ─────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_record_prerequisite (
  record_id              UUID NOT NULL,
  chart_id               UUID NOT NULL,
  generation             TEXT NOT NULL,
  ordinal                INTEGER NOT NULL,
  predicate_id           TEXT NOT NULL,
  predicate_rule_version TEXT NOT NULL,
  result                 TEXT,                   -- NULL = not evaluated (counts as unknown)

  PRIMARY KEY (record_id, ordinal),
  CONSTRAINT kgrpr_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgrpr_ordinal_ck CHECK (ordinal >= 1),
  CONSTRAINT kgrpr_result_ck CHECK (result IS NULL OR result IN ('true','false','unknown')),
  CONSTRAINT kgrpr_record_fk FOREIGN KEY (record_id, chart_id, generation)
    REFERENCES public.ka_gochara_relationship_record (record_id, chart_id, generation)
    ON DELETE CASCADE,
  CONSTRAINT kgrpr_predicate_fk FOREIGN KEY (predicate_id, predicate_rule_version)
    REFERENCES public.ka_gochara_predicate (predicate_id, rule_version),
  CONSTRAINT kgrpr_no_dup_uq
    UNIQUE (record_id, predicate_id, predicate_rule_version)
);

COMMENT ON TABLE public.ka_gochara_record_prerequisite IS
  'Record prerequisite membership: ordered, version-bound composite references into '
  'ka_gochara_predicate, bound to the record''s own (chart_id, generation). Only `result` '
  'may ever change (N8). At COMMIT the membership must equal the path version''s declared '
  'list and admission_state must equal the state derived from the results (F5).';

CREATE INDEX IF NOT EXISTS idx_kgrpr_record ON public.ka_gochara_record_prerequisite
  (chart_id, generation, record_id);

-- ── 3. Coverage applicability (F7/N10/N14/N15) ─────────────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_record_coverage_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  cov     record;
  ct      record;
  bridged text;
  facts   jsonb;
  iv      tstzrange;
  precision_only boolean := false;
BEGIN
  IF TG_OP = 'UPDATE' THEN
    precision_only := (to_jsonb(NEW) - 'precision') = (to_jsonb(OLD) - 'precision');
  END IF;

  IF NOT precision_only THEN
    SELECT c.partition_kind, c.partition_key, c.convention_id, c.completed_horizon, c.relations_searched
      INTO cov
    FROM public.kala_gochara_coverage c
    WHERE c.chart_id = NEW.chart_id AND c.generation = NEW.generation
      AND c.partition_kind = NEW.coverage_partition_kind
      AND c.partition_key = NEW.coverage_partition_key;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage unresolvable (§1.1 coverage_ref): no kala_gochara_coverage partition (%, %) for (chart %, generation %)',
        NEW.coverage_partition_kind, NEW.coverage_partition_key, NEW.chart_id, NEW.generation;
    END IF;
    IF cov.relations_searched IS NULL OR array_position(cov.relations_searched, NULL) IS NOT NULL THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (N10): partition (%, %) carries a NULL relations_searched element — an uncertain search covers nothing',
        cov.partition_kind, cov.partition_key;
    END IF;
    IF public.ka_gochara_horizon_finite_ok(cov.completed_horizon) IS NOT TRUE THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (N17/N19): partition (%, %) completed_horizon % is not a finite, bounded, non-empty range within 1000-01-01 <= t < 3000-01-01 UTC (AD) — the Gochara-5 contract admits such horizons only',
        cov.partition_kind, cov.partition_key, cov.completed_horizon;
    END IF;
    facts := public.ka_gochara_coverage_facts(cov.convention_id, cov.completed_horizon, cov.relations_searched);
    IF NEW.coverage_facts IS DISTINCT FROM facts THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record.coverage_facts % does not equal the partition''s current facts % (N10/N14): a consumer binds to the coverage facts it was validated against — compute them with ka_gochara_coverage_facts(convention_id, completed_horizon, relations_searched)',
        NEW.coverage_facts, facts;
    END IF;

    IF cov.partition_kind = 'event_class' AND cov.partition_key <> NEW.event_class THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): event_class partition ''%'' does not cover class ''%''',
        cov.partition_key, NEW.event_class;
    END IF;
    IF cov.partition_kind = 'body_target'
       AND cov.partition_key <> NEW.agent || ':' || NEW.object_role THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7/N10): body_target partition ''%'' does not cover (agent ''%'', object_role ''%'') — the full key is agent:object_role',
        cov.partition_key, NEW.agent, NEW.object_role;
    END IF;
  END IF;

  IF NEW.contact_id IS NOT NULL THEN
    -- transit row
    SELECT k.t_in, k.convention_id, k.solver_method, k.delta_lambda, k.delta_t
      INTO ct
    FROM public.ka_gochara_contact k
    WHERE k.chart_id = NEW.chart_id AND k.generation = NEW.generation
      AND k.contact_id = NEW.contact_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record contact % is not owned by (chart %, generation %) (F1)',
        NEW.contact_id, NEW.chart_id, NEW.generation;
    END IF;
    IF NOT precision_only THEN
      IF (NEW.agent = 'moon') <> (cov.partition_kind = 'moon_on_demand') THEN
        RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7; §6.1 Moon-on-demand, O-SS-4): agent ''%'' with partition kind ''%'' — a Moon contact is covered only by a moon_on_demand partition, and vice versa',
          NEW.agent, cov.partition_kind;
      END IF;
      IF NOT COALESCE(NEW.relation = ANY (cov.relations_searched), false) THEN
        RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): relation ''%'' is not among the partition''s relations_searched %',
          NEW.relation, cov.relations_searched;
      END IF;
      SELECT b.sky_convention_id INTO bridged
      FROM public.ka_gochara_convention_bridge b
      WHERE b.kala_convention_id = cov.convention_id;
      IF bridged IS DISTINCT FROM ct.convention_id THEN
        RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): partition convention ''%'' is not bridged to the contact''s sky convention ''%'' (ka_gochara_convention_bridge)',
          cov.convention_id, ct.convention_id;
      END IF;
      IF NOT (cov.completed_horizon @> ct.t_in) THEN
        RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7; §6.1 C7): contact t_in % lies outside the partition''s completed_horizon %',
          ct.t_in, cov.completed_horizon;
      END IF;
    END IF;
    -- a malformed payload is the CHECK constraint's finding (kgrr_precision_typed_ck);
    -- a well-formed payload must restate the contact (N7 keeps it so on enrichment;
    -- this is the ONLY check a precision-only re-sync runs — N15)
    IF public.ka_gochara_precision_ok(NEW.precision) IS TRUE
       AND ((NEW.precision ->> 'solver_method') IS DISTINCT FROM ct.solver_method
            OR ((NEW.precision ->> 'delta_lambda')::real) IS DISTINCT FROM ct.delta_lambda
            OR ((NEW.precision ->> 'delta_t')::real) IS DISTINCT FROM ct.delta_t) THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record.precision % restates the contact''s solved precision (%, %, %) incorrectly (CLAUDE.md §N.5; N7: precision follows the contact, never the other way round)',
        NEW.precision, ct.solver_method, ct.delta_lambda, ct.delta_t;
    END IF;
  ELSIF NOT precision_only THEN
    -- natal-fact row
    IF cov.partition_kind = 'moon_on_demand' THEN
      RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): a natal-fact row never references a moon_on_demand partition';
    END IF;
  END IF;

  -- a non-finite support interval is the CHECK constraint's finding (kgrr_support_intervals_ck)
  IF NOT precision_only AND public.ka_gochara_intervals_ok(NEW.temporal_support_intervals) IS TRUE THEN
    FOREACH iv IN ARRAY NEW.temporal_support_intervals LOOP
      IF NOT (cov.completed_horizon @> iv) THEN
        RAISE EXCEPTION 'ka_gochara_relationship_record coverage not applicable (F7): support interval % lies outside the partition''s completed_horizon %',
          iv, cov.completed_horizon;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END;
$$;

-- ── 4. Finalisation at the atomic write boundary (F5) ─────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_record_finalize_check()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  rid       uuid;
  rec       record;
  mismatch  integer;
  n_false   integer;
  n_unknown integer;
  derived   text;
BEGIN
  rid := CASE WHEN TG_OP = 'DELETE' THEN OLD.record_id ELSE NEW.record_id END;
  SELECT r.record_id, r.path_id, r.rule_version, r.admission_state INTO rec
  FROM public.ka_gochara_relationship_record r
  WHERE r.record_id = rid;
  IF NOT FOUND THEN
    RETURN NULL;   -- the record left with this transaction; nothing to finalise
  END IF;

  SELECT count(*) INTO mismatch
  FROM (
    (SELECT p.ordinal, p.predicate_id, p.predicate_rule_version
     FROM public.ka_gochara_rule_path_prerequisite p
     WHERE p.path_id = rec.path_id AND p.rule_version = rec.rule_version
     EXCEPT
     SELECT m.ordinal, m.predicate_id, m.predicate_rule_version
     FROM public.ka_gochara_record_prerequisite m
     WHERE m.record_id = rid)
    UNION ALL
    (SELECT m.ordinal, m.predicate_id, m.predicate_rule_version
     FROM public.ka_gochara_record_prerequisite m
     WHERE m.record_id = rid
     EXCEPT
     SELECT p.ordinal, p.predicate_id, p.predicate_rule_version
     FROM public.ka_gochara_rule_path_prerequisite p
     WHERE p.path_id = rec.path_id AND p.rule_version = rec.rule_version)
  ) d;
  IF mismatch > 0 THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record % finalisation failed (F5; §1.1/§1.2 inv 7): its prerequisite membership does not equal the declared prerequisites of rule version (%, %) — a record evaluates exactly its path''s necessary predicates, in order',
      rid, rec.path_id, rec.rule_version;
  END IF;

  SELECT count(*) FILTER (WHERE m.result = 'false'),
         count(*) FILTER (WHERE m.result IS DISTINCT FROM 'true' AND m.result IS DISTINCT FROM 'false')
    INTO n_false, n_unknown
  FROM public.ka_gochara_record_prerequisite m
  WHERE m.record_id = rid;
  derived := CASE WHEN n_false > 0 THEN 'not_admitted'
                  WHEN n_unknown > 0 THEN 'unqualified'
                  ELSE 'admitted' END;
  IF rec.admission_state <> derived THEN
    RAISE EXCEPTION 'ka_gochara_relationship_record % finalisation failed (F5; §2.2 inv 2, S:103): admission_state ''%'' contradicts its prerequisite results (derived ''%'': any false ⇒ not_admitted; else any unknown/unevaluated ⇒ unqualified; else admitted)',
      rid, rec.admission_state, derived;
  END IF;
  RETURN NULL;
END;
$$;

-- ── 5. N7 — contact enrichment re-states dependent precision ──────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_contact_propagate_precision()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE restated jsonb;
BEGIN
  restated := jsonb_build_object('solver_method', NEW.solver_method,
                                 'delta_lambda',  NEW.delta_lambda,
                                 'delta_t',       NEW.delta_t);
  UPDATE public.ka_gochara_relationship_record r
     SET precision = restated
   WHERE r.chart_id = NEW.chart_id AND r.generation = NEW.generation
     AND r.contact_id = NEW.contact_id
     AND r.precision IS DISTINCT FROM restated;
  RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_2_propagate_precision ON public.ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_2_propagate_precision
  AFTER UPDATE ON public.ka_gochara_contact
  FOR EACH ROW
  WHEN (OLD.t_exact IS DISTINCT FROM NEW.t_exact
        OR OLD.solver_method IS DISTINCT FROM NEW.solver_method
        OR OLD.delta_lambda IS DISTINCT FROM NEW.delta_lambda
        OR OLD.delta_t IS DISTINCT FROM NEW.delta_t)
  EXECUTE FUNCTION public.ka_gochara_contact_propagate_precision();

-- ── 6. Triggers (statement lock → row: lock/seal → coverage → rule seal) ──

DROP TRIGGER IF EXISTS ka_gochara_rr_0_statement_lock ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_relationship_record
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_rr_1_write_guard ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_relationship_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('precision_sync');
DROP TRIGGER IF EXISTS ka_gochara_rr_2_coverage_guard ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_2_coverage_guard
  BEFORE INSERT OR UPDATE ON public.ka_gochara_relationship_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_record_coverage_guard();
DROP TRIGGER IF EXISTS ka_gochara_rr_3_sealed_path_check ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_3_sealed_path_check
  BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_relationship_record
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
DROP TRIGGER IF EXISTS ka_gochara_rr_finalize ON public.ka_gochara_relationship_record;
CREATE CONSTRAINT TRIGGER ka_gochara_rr_finalize
  AFTER INSERT OR UPDATE ON public.ka_gochara_relationship_record
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_record_finalize_check();
DROP TRIGGER IF EXISTS ka_gochara_rr_no_truncate ON public.ka_gochara_relationship_record;
CREATE TRIGGER ka_gochara_rr_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_relationship_record
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

DROP TRIGGER IF EXISTS ka_gochara_rpr_0_statement_lock ON public.ka_gochara_record_prerequisite;
CREATE TRIGGER ka_gochara_rpr_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_record_prerequisite
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_rpr_1_write_guard ON public.ka_gochara_record_prerequisite;
CREATE TRIGGER ka_gochara_rpr_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_record_prerequisite
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('result_only');
DROP TRIGGER IF EXISTS ka_gochara_rpr_finalize ON public.ka_gochara_record_prerequisite;
CREATE CONSTRAINT TRIGGER ka_gochara_rpr_finalize
  AFTER INSERT OR UPDATE OR DELETE ON public.ka_gochara_record_prerequisite
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_record_finalize_check();
DROP TRIGGER IF EXISTS ka_gochara_rpr_no_truncate ON public.ka_gochara_record_prerequisite;
CREATE TRIGGER ka_gochara_rpr_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_record_prerequisite
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 7. Post-apply PRESENCE checks (steward ruling 3) + helper self-tests ───
DO $$
DECLARE
  h  tstzrange := tstzrange('2025-01-01T00:00:00Z', '2026-01-01T00:00:00.123456Z', '[)');
  n_raised integer := 0;
  bad tstzrange;
BEGIN
  -- N17: the encoder refuses every horizon outside the accepted domain
  FOREACH bad IN ARRAY ARRAY[NULL::tstzrange, 'empty'::tstzrange, '(,)'::tstzrange,
                             tstzrange('2025-01-01T00:00Z', NULL, '[)'),
                             tstzrange('-infinity', 'infinity', '[]'),
                             tstzrange('infinity', 'infinity', '[]'),
                             tstzrange('2025-01-01T00:00Z', 'infinity', '[)'),
                             tstzrange('2025-03-01 00:00:00+00 BC', '2025-04-01 00:00:00+00 BC', '[)'),   -- N19: the reviewer's H_BC
                             tstzrange('0999-12-31 00:00:00+00', '2025-04-01 00:00:00+00', '[)'),
                             tstzrange('2025-03-01 00:00:00+00', '3000-01-01 00:00:00+00', '[)')] LOOP
    BEGIN
      PERFORM public.ka_gochara_coverage_facts('c', bad, ARRAY['a']);
    EXCEPTION WHEN raise_exception THEN
      IF SQLERRM LIKE '%unsupported horizon%' THEN n_raised := n_raised + 1; END IF;
    END;
  END LOOP;
  IF n_raised <> 10 THEN
    RAISE EXCEPTION 'migration 1155 post-apply check failed: the coverage-facts encoder accepted a non-finite horizon (N17)';
  END IF;
  IF NOT (public.ka_gochara_precision_ok(NULL) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":null,"delta_lambda":0.001,"delta_t":60}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":-0.001,"delta_t":60}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":0.001}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60,"x":1}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"clipped_truncated","delta_lambda":0.001,"delta_t":60}'::jsonb) IS FALSE
          AND public.ka_gochara_precision_ok('{"solver_method":"clipped_truncated","delta_lambda":null,"delta_t":null}'::jsonb) IS TRUE
          AND public.ka_gochara_precision_ok('{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb) IS TRUE
          AND public.ka_gochara_intervals_ok(NULL) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY['empty'::tstzrange]) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY[NULL::tstzrange]) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY[tstzrange('2025-01-01T00:00Z', 'infinity', '[)')]) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY['(,)'::tstzrange]) IS FALSE
          AND public.ka_gochara_intervals_ok(ARRAY[h]) IS TRUE
          AND public.ka_gochara_intervals_ok('{}'::tstzrange[]) IS TRUE
          -- N14: order-insensitive, element-boundary-preserving, NULL-preserving
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['b','a'])
              = public.ka_gochara_coverage_facts('c', h, ARRAY['a','b'])
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['conjunction'])
              <> public.ka_gochara_coverage_facts('c', h, ARRAY['conjunction', NULL])
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['aspect','conjunction'])
              <> public.ka_gochara_coverage_facts('c', h, ARRAY['aspect,conjunction'])
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['a'])
              <> public.ka_gochara_coverage_facts('c', h, ARRAY['a','a'])
          AND public.ka_gochara_coverage_facts('c', h, '{}'::text[])
              <> public.ka_gochara_coverage_facts('c', h, NULL)
          -- N14/N17: over the accepted domain, bounds and inclusivity are encoded exactly
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['a'])
              <> public.ka_gochara_coverage_facts('c', tstzrange(lower(h), upper(h), '[]'), ARRAY['a'])
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['a'])
              <> public.ka_gochara_coverage_facts('c', tstzrange(lower(h), upper(h) + interval '1 microsecond', '[)'), ARRAY['a'])
          AND public.ka_gochara_coverage_facts('c', h, ARRAY['a'])
              <> public.ka_gochara_coverage_facts('d', h, ARRAY['a'])
          AND (public.ka_gochara_coverage_facts('c', h, ARRAY['a']) -> 'horizon' ->> 'lower') = '2025-01-01T00:00:00.000000Z'
          AND (public.ka_gochara_coverage_facts('c', h, ARRAY['a']) -> 'horizon' ->> 'upper') = '2026-01-01T00:00:00.123456Z'
          AND (public.ka_gochara_coverage_facts('c', h, ARRAY['x', NULL]) -> 'relations_searched') = '[null, "x"]'::jsonb
          -- round trip of the horizon encoding (drift classifier + membership guard input)
          AND public.ka_gochara_facts_horizon(public.ka_gochara_coverage_facts('c', h, ARRAY['a'])) = h
          AND public.ka_gochara_facts_horizon(public.ka_gochara_coverage_facts('c', tstzrange(lower(h), upper(h), '(]'), ARRAY['a']))
              = tstzrange(lower(h), upper(h), '(]')
          -- N19: exact at the edges of the accepted era (four-digit AD years)
          AND public.ka_gochara_facts_horizon(public.ka_gochara_coverage_facts('c', tstzrange('1000-01-01 00:00:00+00', '2999-12-31 23:59:59.999999+00', '[]'), ARRAY['a']))
              = tstzrange('1000-01-01 00:00:00+00', '2999-12-31 23:59:59.999999+00', '[]')
          AND (public.ka_gochara_coverage_facts('c', tstzrange('1000-01-01 00:00:00+00', '2999-12-31 23:59:59.999999+00', '[]'), ARRAY['a']) -> 'horizon' ->> 'lower') = '1000-01-01T00:00:00.000000Z'
          AND (public.ka_gochara_coverage_facts('c', tstzrange('1000-01-01 00:00:00+00', '2999-12-31 23:59:59.999999+00', '[]'), ARRAY['a']) -> 'horizon' ->> 'upper') = '2999-12-31T23:59:59.999999Z'
          AND public.ka_gochara_facts_horizon(NULL) IS NULL) THEN
    RAISE EXCEPTION 'migration 1155 post-apply check failed: helper self-test failed';
  END IF;
END;
$$;

DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(t, ', ' ORDER BY t) INTO missing
  FROM unnest(ARRAY['ka_gochara_relationship_record','ka_gochara_record_prerequisite']) t
  WHERE to_regclass('public.' || t) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1155 post-apply check failed: missing table: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (VALUES
      ('ka_gochara_relationship_record','ka_gochara_relationship_record_pkey'),
      ('ka_gochara_relationship_record','kgrr_canonical_chart_ck'),
      ('ka_gochara_relationship_record','kgrr_generation_governed_ck'),
      ('ka_gochara_relationship_record','kgrr_event_class_ck'),
      ('ka_gochara_relationship_record','kgrr_affected_person_ck'),
      ('ka_gochara_relationship_record','kgrr_frame_ck'),
      ('ka_gochara_relationship_record','kgrr_relative_frame_ck'),
      ('ka_gochara_relationship_record','kgrr_agent_ck'),
      ('ka_gochara_relationship_record','kgrr_relation_ck'),
      ('ka_gochara_relationship_record','kgrr_object_kind_ck'),
      ('ka_gochara_relationship_record','kgrr_object_role_ck'),
      ('ka_gochara_relationship_record','kgrr_path_fk'),
      ('ka_gochara_relationship_record','kgrr_contact_fk'),
      ('ka_gochara_relationship_record','kgrr_coverage_fk'),
      ('ka_gochara_relationship_record','kgrr_coverage_kind_ck'),
      ('ka_gochara_relationship_record','kgrr_coverage_facts_shape_ck'),
      ('ka_gochara_relationship_record','kgrr_support_state_ck'),
      ('ka_gochara_relationship_record','kgrr_support_cardinality_ck'),
      ('ka_gochara_relationship_record','kgrr_support_intervals_ck'),
      ('ka_gochara_relationship_record','kgrr_house_from_frame_ck'),
      ('ka_gochara_relationship_record','kgrr_evaluated_has_house_ck'),
      ('ka_gochara_relationship_record','kgrr_precision_typed_ck'),
      ('ka_gochara_relationship_record','kgrr_transit_natal_ck'),
      ('ka_gochara_relationship_record','kgrr_source_fact_ids_ck'),
      ('ka_gochara_relationship_record','kgrr_provenance_ck'),
      ('ka_gochara_relationship_record','kgrr_operator_role_ck'),
      ('ka_gochara_relationship_record','kgrr_ruling_ck'),
      ('ka_gochara_relationship_record','kgrr_citation_ck'),
      ('ka_gochara_relationship_record','kgrr_admission_state_ck'),
      ('ka_gochara_relationship_record','kgrr_evidence_finite_ck'),
      ('ka_gochara_relationship_record','kgrr_severity_finite_ck'),
      ('ka_gochara_relationship_record','kgrr_valence_ck'),
      ('ka_gochara_relationship_record','kgrr_identity_uq'),
      ('ka_gochara_relationship_record','kgrr_membership_uq'),
      ('ka_gochara_record_prerequisite','ka_gochara_record_prerequisite_pkey'),
      ('ka_gochara_record_prerequisite','kgrpr_generation_governed_ck'),
      ('ka_gochara_record_prerequisite','kgrpr_ordinal_ck'),
      ('ka_gochara_record_prerequisite','kgrpr_result_ck'),
      ('ka_gochara_record_prerequisite','kgrpr_record_fk'),
      ('ka_gochara_record_prerequisite','kgrpr_predicate_fk'),
      ('ka_gochara_record_prerequisite','kgrpr_no_dup_uq'))
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname AND c.convalidated);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1155 post-apply check failed: missing or unvalidated constraint: %', missing;
  END IF;

  WITH expected(tgrelid, tgname) AS (VALUES
      ('ka_gochara_relationship_record','ka_gochara_rr_0_statement_lock'),
      ('ka_gochara_relationship_record','ka_gochara_rr_1_write_guard'),
      ('ka_gochara_relationship_record','ka_gochara_rr_2_coverage_guard'),
      ('ka_gochara_relationship_record','ka_gochara_rr_3_sealed_path_check'),
      ('ka_gochara_relationship_record','ka_gochara_rr_finalize'),
      ('ka_gochara_relationship_record','ka_gochara_rr_no_truncate'),
      ('ka_gochara_record_prerequisite','ka_gochara_rpr_0_statement_lock'),
      ('ka_gochara_record_prerequisite','ka_gochara_rpr_1_write_guard'),
      ('ka_gochara_record_prerequisite','ka_gochara_rpr_finalize'),
      ('ka_gochara_record_prerequisite','ka_gochara_rpr_no_truncate'),
      ('ka_gochara_contact','ka_gochara_contact_2_propagate_precision'))
  SELECT string_agg(e.tgrelid || '.' || e.tgname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.' || e.tgrelid) AND t.tgname = e.tgname
      AND NOT t.tgisinternal AND t.tgenabled = 'O');
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1155 post-apply check failed: missing trigger: %', missing;
  END IF;
  RAISE NOTICE 'migration 1155: presence checks passed';
END;
$$;
