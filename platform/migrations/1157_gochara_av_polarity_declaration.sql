-- Migration 1157: ka_gochara_av_polarity_declaration — the §8.1 bindu
--                 polarity declaration, gated before any citation-bearing AV
--                 weight (GOCHARA_DESIGN_SPECS_v1_4 §8, T0-11).
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1157 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1157 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Spec: GOCHARA_DESIGN_SPECS_v1_4 (FROZEN 2026-09-30). §8.1 schema:
--   av_polarity_declaration(convention, benefic_mark_name, malefic_mark_name,
--   source_ref, applies_to_fact_categories[])
-- Encoded as:
--   * CONSTRAINT / COLUMN: convention text PK; benefic_mark_name /
--     malefic_mark_name / source_ref NOT NULL; applies_to_fact_categories
--     text[] NOT NULL. Content per §8.1 (unchanged from v1.0): L1's
--     ashtakavarga_bindu* stores PyJHora benefic "dots"; Santhanam BPHS
--     names the benefic mark rekhā (BPHS2:35666-35684); the declaration pins
--     pyjhora_dots = benefic_marks ↔ rekhā for citation (N8).
--   * TRIGGER: insert-only — the declaration is data that evaluations join
--     and record in lineage (§8.2 inv 2, O-BP-3); a change is a new
--     convention row, never an edit.
--   * COMMENT ONLY: §8.2 inv 1 (no AV-derived weight exists before the
--     declaration row exists — T0-11 gates P5) is a writer/evaluator gate,
--     not SQL-checkable; §8 evaluation semantics (known-zero adverse, no
--     sign-mean comparator, SAV bands >30/25–30/<25, unresolved operand ⇒
--     unqualified) are P5 evaluator behaviour.
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
-- Operational properties: pure CREATE TABLE / FUNCTION / TRIGGER; no
-- existing object or data touched; no production data writes; ONE
-- TRANSACTION (BEGIN/COMMIT, 1081 style); replay-idempotent by construction
-- (IF NOT EXISTS / CREATE OR REPLACE / DROP TRIGGER IF EXISTS everywhere),
-- though migrate.ts never replays; SET LOCAL bounds stated honestly.
--
-- ROLLBACK:
--   DROP TRIGGER IF EXISTS ka_gochara_av_polarity_immutable ON ka_gochara_av_polarity_declaration;
--   DROP FUNCTION IF EXISTS ka_gochara_av_polarity_no_mutation();
--   DROP TABLE IF EXISTS ka_gochara_av_polarity_declaration;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

CREATE TABLE IF NOT EXISTS ka_gochara_av_polarity_declaration (
  convention        TEXT PRIMARY KEY,            -- §8.1 'convention' — the AV fact
                    -- convention this declaration pins (deliberately no FK; see header)
  benefic_mark_name TEXT NOT NULL,               -- §8.1: e.g. 'rekhā' (Santhanam BPHS,
                    -- BPHS2:35666-35684); pins pyjhora_dots = benefic_marks ↔ rekhā (N8)
  malefic_mark_name TEXT NOT NULL,               -- §8.1
  source_ref        TEXT NOT NULL,               -- §8.1: citation locator for the naming
  applies_to_fact_categories TEXT[] NOT NULL,    -- §8.1: the L0/L1 fact categories this
                    -- declaration governs (ashtakavarga_bindu* rows)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ka_gochara_av_polarity_declaration IS
  'AV bindu polarity declaration (GOCHARA_DESIGN_SPECS_v1_4 §8.1): declared before any '
  'citation-bearing AV weight exists (§8.2 inv 1 — T0-11 gates P5; evaluator-side, not '
  'SQL-checkable). The declaration is data: evaluations join it and record it in '
  'lineage (§8.2 inv 2, O-BP-3). Known-zero and unresolved are distinct states '
  'end-to-end (§8.2 inv 3, D-RQ1); an unresolved operand yields unqualified, and each '
  'P5 operand gates exactly its own form (§8.2 inv 4). min_sav_score-style config is '
  'never read as measured SAV (§8.2 inv 5, #26). Insert-only (trigger): a change is a '
  'new convention row.';

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

COMMIT;
