-- Migration 1157: ka_gochara_av_polarity_declaration — the §8.1 bindu
--                 polarity declaration, gated before any citation-bearing AV
--                 weight (GOCHARA_DESIGN_SPECS_v1_4 §8, T0-11).
--                 Rewritten at A5.1 round 2 per ASTRA_REVIEW_A5_1_MIGRATIONS
--                 v1_0 amendment 2 (transaction ownership) and amendment 8
--                 (post-DDL verification). Never applied anywhere — in-place
--                 rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1157 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1157 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Amendment 2 (P1 #2): NO BEGIN/COMMIT — migrate.ts owns ONE transaction
-- around DDL + ledger insert (see the 1153 header). SET LOCAL is scoped to
-- the runner's transaction.
--
-- Spec: GOCHARA_DESIGN_SPECS_v1_4 (FROZEN 2026-09-30). §8.1 schema:
--   av_polarity_declaration(convention, benefic_mark_name, malefic_mark_name,
--   source_ref, applies_to_fact_categories[])
-- Encoded as:
--   * CONSTRAINT / COLUMN: convention text PK; benefic_mark_name /
--     malefic_mark_name / source_ref NOT NULL; applies_to_fact_categories
--     text[] NOT NULL (and non-empty — a declaration governing no category
--     is not a declaration). Content per §8.1: pyjhora_dots = benefic_marks
--     ↔ rekhā (Santhanam BPHS, BPHS2:35666-35684; N8).
--   * TRIGGER: insert-only — the declaration is data that evaluations join
--     and record in lineage (§8.2 inv 2, O-BP-3); a change is a new
--     convention row, never an edit.
--   * COMMENT ONLY (evaluation-time obligations, unchanged from round 1):
--     §8.2 inv 1 (no AV-derived weight exists before the declaration row
--     exists — T0-11 gates P5) and O-BP-3's write-time citation rejection
--     (a citation emitted with no declaration row to join is rejected by the
--     WRITER at write time) are writer/evaluator gates: the declaration-to-
--     evaluation binding lands with the P5 evaluation tables, not with this
--     registry table; the empty table alone does not establish the gate.
--   * DELIBERATELY NOT ENCODED: no FK on convention. §8.1 does not say
--     whether "convention" is the §6.1 sky convention or an L1 AV-build
--     convention (the pinned G-10 extracts are build aa9602ce / single_pass
--     rows, not sky conventions); inventing a FK to ka_gochara_sky_convention
--     would assert a link the spec does not name. Flagged in the A5.1
--     report, not silently resolved.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- has no 'L2' value; contract table of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- Operational properties: pure CREATE TABLE / FUNCTION / TRIGGER + post-DDL
-- verification; no existing object or data touched; no business-data writes.
-- Execution outcomes (amendment 8): fresh apply = create + verify; repeat
-- execution = verified no-op; drifted same-named object = loud RAISE.
--
-- ROLLBACK:
--   DROP TRIGGER IF EXISTS ka_gochara_av_polarity_immutable ON ka_gochara_av_polarity_declaration;
--   DROP FUNCTION IF EXISTS ka_gochara_av_polarity_no_mutation();
--   DROP TABLE IF EXISTS ka_gochara_av_polarity_declaration;
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

CREATE TABLE IF NOT EXISTS ka_gochara_av_polarity_declaration (
  convention        TEXT PRIMARY KEY,            -- §8.1 'convention' (deliberately no
                                                 --   FK; see header)
  benefic_mark_name TEXT NOT NULL,               -- §8.1: e.g. 'rekhā' (BPHS2:35666-35684)
  malefic_mark_name TEXT NOT NULL,               -- §8.1
  source_ref        TEXT NOT NULL,               -- §8.1: citation locator for the naming
  applies_to_fact_categories TEXT[] NOT NULL,    -- §8.1: the L0/L1 fact categories this
                                                 --   declaration governs (ashtakavarga_bindu*)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgav_categories_nonempty_ck
    CHECK (COALESCE(array_length(applies_to_fact_categories, 1), 0) >= 1)
);

COMMENT ON TABLE ka_gochara_av_polarity_declaration IS
  'AV bindu polarity declaration (GOCHARA_DESIGN_SPECS_v1_4 §8.1): declared before any '
  'citation-bearing AV weight exists (§8.2 inv 1 — T0-11 gates P5; writer-side gate, '
  'not SQL-checkable). The declaration is data: evaluations join it and record it in '
  'lineage (§8.2 inv 2, O-BP-3; a citation with no declaration row to join is a '
  'write-time rejection). Known-zero and unresolved are distinct states end-to-end '
  '(§8.2 inv 3, D-RQ1). Insert-only (trigger): a change is a new convention row.';

CREATE OR REPLACE FUNCTION ka_gochara_av_polarity_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_av_polarity_declaration is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §8.1/§8.2 inv 2): % not permitted; a polarity change is a new convention row', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_av_polarity_immutable ON ka_gochara_av_polarity_declaration;
CREATE TRIGGER ka_gochara_av_polarity_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_av_polarity_declaration
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_av_polarity_no_mutation();

-- ── Post-DDL definition verification (amendment 8) ────────────────────────

DO $$
DECLARE missing text;
BEGIN
  WITH expected(tbl, col, typ, nn) AS (
    VALUES
      ('ka_gochara_av_polarity_declaration','convention','text',true),
      ('ka_gochara_av_polarity_declaration','benefic_mark_name','text',true),
      ('ka_gochara_av_polarity_declaration','malefic_mark_name','text',true),
      ('ka_gochara_av_polarity_declaration','source_ref','text',true),
      ('ka_gochara_av_polarity_declaration','applies_to_fact_categories','text[]',true)
  )
  SELECT string_agg(e.tbl || '.' || e.col, ', ' ORDER BY e.tbl, e.col) INTO missing
  FROM expected e
  LEFT JOIN pg_attribute a
    ON a.attrelid = to_regclass('public.' || e.tbl)
   AND a.attname = e.col AND NOT a.attisdropped
  WHERE a.attname IS NULL
     OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
     OR a.attnotnull IS DISTINCT FROM e.nn;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1157 post-DDL verification failed (amendment 8): column drift: %', missing;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.ka_gochara_av_polarity_declaration')
      AND c.conname = 'kgav_categories_nonempty_ck'
  ) THEN
    RAISE EXCEPTION 'migration 1157 post-DDL verification failed (amendment 8): missing constraint: kgav_categories_nonempty_ck';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.ka_gochara_av_polarity_declaration')
      AND t.tgname = 'ka_gochara_av_polarity_immutable' AND NOT t.tgisinternal
  ) THEN
    RAISE EXCEPTION 'migration 1157 post-DDL verification failed (amendment 8): missing trigger: ka_gochara_av_polarity_immutable';
  END IF;
END;
$$;
