-- Migration 524: bg_parihara_rules — muhūrta-scope net_standing value +
-- extraction_context provenance column (ṢAḌ-DARŚANA ADJUDICATION-10 Part 1:
-- Abhijit sarva-doṣaghna one-row in-corpus extraction)
-- =============================================================================
-- Context: SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md ADJUDICATION-10. The
-- W3 lattice-engine gate criterion ("the Abhijit-override case demonstrably
-- rescues a candidate") is MET by extracting the ONE muhūrta-scope
-- cancellation rule already present in the corpus (bphs_jaimini PG213, chunk
-- bphs_jaimini_pg0213_c01: "...Abhijit Sarva Doshaghnam or that noon time
-- which cuts and cures all evil influences.") — verified read-only against
-- production `classical_text_chunks` before writing this migration (see PR
-- body for the verification query + returned content_en).
--
-- Migration 485 (bg_parihara_rules) already supports scope='muhurta' on the
-- CHECK constraint, but its net_standing CHECK only allows
-- ('cancellable_by_condition', 'cancellable_by_remedial_act') — the
-- adjudication's ruled value 'cancelled' has no home. And no column exists
-- to honestly mark this one row as a TRANSLATOR'S DOCTRINAL GLOSS (Rao's
-- 1949 narrative aside at PG213) rather than a mūla-sūtra verse — seeding it
-- as an unmarked sūtra citation would be citation inflation (ADJUDICATION-10
-- Part 1: "labelled honestly it is stronger evidence than the Kota ring
-- table's tier-(iii) source, and genuinely in-corpus").
--
-- TWO MINIMAL, ADDITIVE CHANGES (no data loss, no existing row touched):
--   1. Widen the net_standing CHECK to also allow 'cancelled' (the ADJUDICATION's
--      ruled value for a rule the corpus states unconditionally, with no
--      cancellation CONDITION to satisfy — contrast 'cancellable_by_condition',
--      which implies a condition the candidate must independently meet).
--   2. Add nullable `extraction_context` TEXT, CHECK-constrained to the two
--      provenance tiers this campaign has needed language for so far
--      ('mula_sutra_citation' | 'translator_gloss_in_narrative'). NULL is the
--      honest default for every pre-existing row: this migration does NOT
--      retroactively classify the 485 natal rows (that classification work
--      was not done and would be a fabricated assertion, not a migration's
--      job — §N.7 item 6, honest null beats an invented judgment).
--
-- Migration-number claim (per ADJUDICATION-10 dispatch note: several 52x
-- numbers were being claimed concurrently tonight across sibling ṢAḌ-DARŚANA
-- worktrees/branches). Checked immediately before writing this file:
-- shad-darshana/integration (+ everything already merged into it) tops out
-- at 521; two OTHER in-flight lanes had uncommitted local claims on 522
-- (l0-ne-priors: 522_brahma_class_lifetime_counts.sql) and 522/523
-- (w3-moorti-vedha: 522_kala_moorti_nirnaya.sql,
-- 523_kala_vedha_gochara.sql) as of this check; w3-kota-rings and
-- w2g-validations had not yet created a migration file locally. Claiming
-- **524** as the next free number after those two observed claims — see PR
-- body for the full claim statement.
-- =============================================================================

BEGIN;

ALTER TABLE bg_parihara_rules
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_net_standing_check;

ALTER TABLE bg_parihara_rules
  ADD CONSTRAINT bg_parihara_rules_net_standing_check
    CHECK (net_standing IN (
      'cancellable_by_condition', 'cancellable_by_remedial_act', 'cancelled'
    ));

ALTER TABLE bg_parihara_rules
  ADD COLUMN IF NOT EXISTS extraction_context TEXT
    CHECK (extraction_context IS NULL OR extraction_context IN (
      'mula_sutra_citation', 'translator_gloss_in_narrative'
    ));

COMMENT ON COLUMN bg_parihara_rules.net_standing IS
  'cancellable_by_condition: the candidate must independently satisfy a stated '
  'condition. cancellable_by_remedial_act: cancelled by performing a named act. '
  'cancelled: the corpus states the cancellation unconditionally for the scope '
  'given (e.g. ADJUDICATION-10''s Abhijit sarva-doṣaghna row — the source names '
  'no condition beyond the muhūrta itself occurring).';

COMMENT ON COLUMN bg_parihara_rules.extraction_context IS
  'Provenance tier of this row''s classical_citations entry, honestly '
  'disclosed so a mūla-sūtra verse is never confused with a translator''s '
  'narrative aside. NULL on every row seeded before this migration (2026-08-01) '
  '-- not retroactively classified, not assumed. mula_sutra_citation: the cited '
  'chunk IS verse/sūtra text. translator_gloss_in_narrative: the cited chunk is '
  'a translator''s own doctrinal remark embedded in narrative/commentary prose '
  '(ADJUDICATION-10''s Abhijit row: B. Suryanarain Rao''s 1949 aside at Jaimini '
  'Sutras PG213 -- stronger than a bare classical_tradition placeholder, but '
  'weaker than a mūla-sūtra, and must be labelled as such rather than upgraded.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE bg_parihara_rules DROP COLUMN IF EXISTS extraction_context;
--   ALTER TABLE bg_parihara_rules DROP CONSTRAINT IF EXISTS bg_parihara_rules_net_standing_check;
--   ALTER TABLE bg_parihara_rules ADD CONSTRAINT bg_parihara_rules_net_standing_check
--     CHECK (net_standing IN ('cancellable_by_condition', 'cancellable_by_remedial_act'));
--   COMMIT;
-- =============================================================================
