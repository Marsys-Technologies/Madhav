-- Migration 1157: ka_gochara_av_polarity_declaration — the §8.1 bindu
--                 polarity declaration, gated before any citation-bearing AV
--                 weight (GOCHARA_DESIGN_SPECS_v1_4 §8, T0-11). Round-3
--                 rewrite per ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 (F2 TRUNCATE,
--                 F8 signatures, F9 verified PK + CHECK definitions, F11
--                 non-empty category elements). Depends on 1153 (shared
--                 helpers + definition verifier). Never applied anywhere —
--                 in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1157 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH migration directories (2026-09-30). `npm run guard:migration-numbers`
-- green.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- (see the 1153 header). Effective ordered gate: pinned schema → preflight
-- gate (byte-identical to preflight_1157_av_polarity_declaration.sql;
-- requires 1153 recorded) → DDL → post-DDL definition verification, which
-- verifies the PRIMARY KEY and the actual CHECK definition (F9: a same-named
-- table with no PK or `CHECK (true)` fails loudly).
--
-- Spec: GOCHARA_DESIGN_SPECS_v1_4 (FROZEN 2026-09-30). §8.1 schema:
--   av_polarity_declaration(convention, benefic_mark_name, malefic_mark_name,
--   source_ref, applies_to_fact_categories[])
-- Encoded as:
--   * CONSTRAINT / COLUMN: convention text PK (non-blank); benefic_mark_name /
--     malefic_mark_name / source_ref NOT NULL non-blank, and the two mark
--     names distinct; applies_to_fact_categories text[] NOT NULL with ≥ 1
--     element and no NULL/blank element (F11 — `{NULL}` or `{''}` names no
--     fact category). Content per §8.1: pyjhora_dots = benefic_marks ↔ rekhā
--     (Santhanam BPHS, BPHS2:35666-35684; N8).
--   * TRIGGER: insert-only + TRUNCATE refused — the declaration is data that
--     evaluations join and record in lineage (§8.2 inv 2, O-BP-3); a change
--     is a new convention row, never an edit.
--   * COMMENT ONLY (evaluation-time obligations): §8.2 inv 1 (no AV-derived
--     weight exists before the declaration row exists — T0-11 gates P5) and
--     O-BP-3's write-time citation rejection are writer/evaluator gates: the
--     declaration-to-evaluation binding lands with the P5 evaluation tables,
--     not with this registry table; the empty table alone does not establish
--     the gate (explicitly deferred, as the review records).
--   * DELIBERATELY NOT ENCODED: no FK on convention. §8.1 does not say
--     whether "convention" is the §6.1 sky convention or an L1 AV-build
--     convention (the pinned G-10 extracts are build aa9602ce / single_pass
--     rows, not sky conventions); inventing a FK would assert a link the
--     frozen spec does not name.
--
-- asset_registry: deliberately NOT registered (same disposition as 1081).
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ka_gochara_av_polarity_declaration;
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1157_av_polarity_declaration.sql) ────
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
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public'
      AND c.relname IN ('ka_gochara_av_polarity_declaration',
                        'ka_gochara_av_polarity_declaration_pkey')
    UNION ALL
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public' AND NOT t.tgisinternal
      AND c.relname = 'ka_gochara_av_polarity_declaration'
      AND t.tgname IN ('ka_gochara_av_polarity_immutable', 'ka_gochara_av_polarity_no_truncate')
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_text_array_ok(text[],integer)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
       OR (SELECT format_type(p.prorettype, NULL) FROM pg_proc p
           WHERE p.oid = to_regprocedure('public.' || e.sig)) <> 'boolean'
    UNION ALL
    SELECT 'helper_function_missing', e.sig
    FROM (VALUES ('ka_gochara_refuse_truncate()'),
                 ('ka_gochara_insert_only()'),
                 ('ka_gochara_verify_definitions(text,jsonb)')) AS e(sig)
    WHERE to_regprocedure('public.' || e.sig) IS NULL
    UNION ALL
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1153_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE NOT replay AND to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1157_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1157 BLOCKED — migration 1157 must NOT be applied:% %', E'\n', failures;
  END IF;
  IF replay THEN
    RAISE NOTICE 'preflight 1157: deliberate replay — existence checks skipped; definitions are verified post-DDL';
  END IF;
  RAISE NOTICE 'preflight 1157: all checks passed';
END;
$$;

CREATE TABLE IF NOT EXISTS public.ka_gochara_av_polarity_declaration (
  convention        TEXT PRIMARY KEY,            -- §8.1 'convention' (deliberately no
                                                 --   FK; see header)
  benefic_mark_name TEXT NOT NULL,               -- §8.1: e.g. 'rekhā' (BPHS2:35666-35684)
  malefic_mark_name TEXT NOT NULL,               -- §8.1
  source_ref        TEXT NOT NULL,               -- §8.1: citation locator for the naming
  applies_to_fact_categories TEXT[] NOT NULL,    -- §8.1: the L0/L1 fact categories this
                                                 --   declaration governs (ashtakavarga_bindu*)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgav_convention_nonblank_ck CHECK (btrim(convention) <> ''),
  CONSTRAINT kgav_mark_names_ck
    CHECK (btrim(benefic_mark_name) <> '' AND btrim(malefic_mark_name) <> ''
           AND benefic_mark_name <> malefic_mark_name),
  CONSTRAINT kgav_source_ref_nonblank_ck CHECK (btrim(source_ref) <> ''),
  CONSTRAINT kgav_categories_nonempty_ck
    CHECK (public.ka_gochara_text_array_ok(applies_to_fact_categories, 1) IS TRUE)
    -- F11: ≥ 1 element, no NULL / blank element
);

COMMENT ON TABLE public.ka_gochara_av_polarity_declaration IS
  'AV bindu polarity declaration (GOCHARA_DESIGN_SPECS_v1_4 §8.1): declared before any '
  'citation-bearing AV weight exists (§8.2 inv 1 — T0-11 gates P5; writer-side gate, '
  'not SQL-checkable). The declaration is data: evaluations join it and record it in '
  'lineage (§8.2 inv 2, O-BP-3; a citation with no declaration row to join is a '
  'write-time rejection by the writer). Known-zero and unresolved are distinct states '
  'end-to-end (§8.2 inv 3, D-RQ1). Insert-only (trigger): a change is a new convention '
  'row; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_av_polarity_immutable ON public.ka_gochara_av_polarity_declaration;
CREATE TRIGGER ka_gochara_av_polarity_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_av_polarity_declaration
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§8.1/§8.2 inv 2 — a polarity change is a new convention row');
DROP TRIGGER IF EXISTS ka_gochara_av_polarity_no_truncate ON public.ka_gochara_av_polarity_declaration;
CREATE TRIGGER ka_gochara_av_polarity_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_av_polarity_declaration
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── Post-DDL definition verification (F9) — PK, CHECK bodies, triggers ────
DO $$
BEGIN
  PERFORM public.ka_gochara_verify_definitions('1157', $expected$
{
  "functions": {},
  "tables": {
    "ka_gochara_av_polarity_declaration": {
      "columns": {
        "applies_to_fact_categories": [
          "text[]",
          true
        ],
        "benefic_mark_name": [
          "text",
          true
        ],
        "convention": [
          "text",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "malefic_mark_name": [
          "text",
          true
        ],
        "source_ref": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_av_polarity_declaration_pkey": [
          "p",
          "primarykeyconvention",
          true
        ],
        "kgav_categories_nonempty_ck": [
          "c",
          "checkka_gochara_text_array_okapplies_to_fact_categories,1istrue",
          true
        ],
        "kgav_convention_nonblank_ck": [
          "c",
          "checkbtrimconvention<>''",
          true
        ],
        "kgav_mark_names_ck": [
          "c",
          "checkbtrimbenefic_mark_name<>''andbtrimmalefic_mark_name<>''andbenefic_mark_name<>malefic_mark_name",
          true
        ],
        "kgav_source_ref_nonblank_ck": [
          "c",
          "checkbtrimsource_ref<>''",
          true
        ]
      },
      "indexes": {
        "ka_gochara_av_polarity_declaration_pkey": "createuniqueindexka_gochara_av_polarity_declaration_pkeyonka_gochara_av_polarity_declarationusingbtreeconvention"
      },
      "triggers": {
        "ka_gochara_av_polarity_immutable": [
          "createtriggerka_gochara_av_polarity_immutablebeforedeleteorupdateonka_gochara_av_polarity_declarationforeachrowexecutefunctionka_gochara_insert_only'§8.1/§8.2inv2—apolaritychangeisanewconventionrow'",
          "O"
        ],
        "ka_gochara_av_polarity_no_truncate": [
          "createtriggerka_gochara_av_polarity_no_truncatebeforetruncateonka_gochara_av_polarity_declarationforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    }
  }
}
$expected$::jsonb);
END;
$$;
