-- Migration 534: kala_paddhati_profile — native confirmation of the Agnivāsa convention
-- =============================================================================
-- ṢAḌ-DARŚANA Wave W4, lane w4-paddhati-seed.
-- Implements SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS
-- (2026-08-02 morning review), item 1 — ADJUDICATION-8 (Agnivāsa):
--
--   "CONVENTION CONTENT CONFIRMED: Pṛthvī-favourable, corpus default correct."
--   The native does yajña "when it is Pṛthvī, not Pātāla", and explicitly identified
--   his earlier elevation-session statement ("I generally do a yajna when Agni Vasa
--   is in Patala") as HIS OWN MISSTATEMENT, corrected on the record.
--
-- Consequences implemented here, verbatim from that section:
--   • Convention (A) `agnivasa_tithi_element_prithvi` is the native's LINEAGE
--     convention, not merely the corpus default. The row ships
--     `native_confirmed = TRUE`, `awaiting_native_confirmation = FALSE`, and
--     `confirmation_provenance` citing §NATIVE CONFIRMATIONS.
--   • Convention (B) `agnivasa_muhurta_chintamani_arithmetic` remains
--     `declared_not_computed` — UNCHANGED — but its `corpus_gap_ref` now points at
--     a COMMISSIONED work item (§NATIVE CONFIRMATIONS item 3: the Muhūrta-Cintāmaṇi
--     translation was commissioned 2026-08-02 as a supervised corpus-curation task,
--     outside the night runs).
--
-- WHY THIS IS AN IN-PLACE FLIP OF paddhati_v01, NOT A paddhati_v02 INSERT:
-- ADJUDICATION-8's versioned supersession ("paddhati_v02 supersedes v01 by insert")
-- is for changes to CONVENTION CONTENT. Nothing about the convention content changed
-- here — the native ATTESTED the existing row. Migration 533's own header designed for
-- exactly this: its seed uses ON CONFLICT DO NOTHING precisely so that "a re-run of
-- this migration must never reset a confirmation the native has since given" — i.e.
-- confirmation is granted by flipping the native-attested columns on the existing row.
-- Additionally, the reader (kala_sky_pattern.ts fetchPaddhatiProfile) scopes to the
-- single latest version by string sort; a v02 carrying only Row A would silently drop
-- Row B's declared divergence slot from serving, violating ADJUDICATION-8 rail 2's
-- requirement that the divergence surface stay real.
--
-- WHAT THIS MIGRATION DELIBERATELY DOES NOT DO:
--   • No `query_kala_paddhati_profile` capability (Night-4's honest gap stands — the
--     serving path degrades honest; building that capability needs a boundary
--     negotiation owned elsewhere).
--   • No change to kala_sky_pattern.ts's PADDHATI_CENSUS_STATEMENT ("the native's
--     lineage convention is not on record") — now superseded in substance by this
--     confirmation, but it is serving code asserted verbatim by the Mode-2 gate and
--     owned by a sibling lane. Flagged, not fixed, here.
--   • No asset_registry row, no count_sql, no DAG edge, no writer (533's standing
--     consequence — this is versioned config, weights-v0 precedent).
--
-- Idempotency: ALTER ... ADD COLUMN IF NOT EXISTS; INSERT ... ON CONFLICT DO UPDATE
-- (upsert on the natural key — seeds the row if 533's seed is somehow absent, flips
-- the confirmation columns if present; a plain DO NOTHING here would be a SILENT
-- NO-OP on every DB where 533 already ran, the exact §N.4 trap); deterministic
-- full-replace of Row B's corpus_gap_ref (re-run converges to the same state).
-- The confirmation flip is monotonic FALSE→TRUE: a re-run can never RESET a
-- confirmation, only re-grant it — consistent with 533's status-preserving intent.
-- A DO block at the end verifies the flip actually landed and RAISEs otherwise
-- (§N.8: a migration that can silently do nothing while the deploy reports success
-- is the defect class this campaign exists to kill).
-- =============================================================================

BEGIN;

-- ── 1. The confirmation-provenance column §NATIVE CONFIRMATIONS prescribes ────
-- (533 predates the morning review and does not carry it.)
ALTER TABLE kala_paddhati_profile
    ADD COLUMN IF NOT EXISTS confirmation_provenance TEXT;

COMMENT ON COLUMN kala_paddhati_profile.confirmation_provenance IS
  'Set iff native_confirmed=TRUE: where the native''s confirmation of this convention '
  'is recorded, so downstream consumers cite a document section rather than a chat '
  'transcript. Prescribed by SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md '
  '§NATIVE CONFIRMATIONS item 1.';

-- 533's native_confirmed comment said "FALSE on every seeded row" — true of the v01
-- SEED, but no longer of the table: the native has since confirmed convention (A).
-- Keep the comment honest.
COMMENT ON COLUMN kala_paddhati_profile.native_confirmed IS
  'FALSE on every row as SEEDED (rail 3: what was on record was the native''s practice, '
  'not his lineage''s convention content — no builder may pin invented convention '
  'content and label it "the native''s lineage"). Flipped TRUE in place by a later '
  'migration when the native confirms a convention on the record — see '
  'confirmation_provenance for where. First instance: migration 534, Agnivāsa '
  'convention (A), per SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS '
  '(2026-08-02).';

-- ── 2. Convention (A) — native_confirmed=TRUE, both canonical charts ──────────
-- Upsert, not bare UPDATE: seeds the row if absent, flips the confirmation columns
-- if present. Non-confirmation column values are identical to 533's seed.
INSERT INTO kala_paddhati_profile (
    chart_id, factor_family, convention_id, school_tag, constraint_role,
    convention_status, provenance, corpus_gap_ref,
    native_confirmed, awaiting_native_confirmation, version, confirmation_provenance
) VALUES
    -- 482012f1 (Abhisek Mohanty)
    ('482012f1-710e-4a25-994a-93821f5871aa', 'agnivasa',
     'agnivasa_tithi_element_prithvi', 'corpus_default', 'hard',
     'computed',
     'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)',
     NULL, TRUE, FALSE, 'paddhati_v01',
     'native statement 2026-08-02 (correcting the 2026-07-28 elevation-session '
     'misstatement); recorded in SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md '
     '§NATIVE CONFIRMATIONS'),
    -- 1c826d5a (Abhinandan Mohanty) — same seed shape per ADJUDICATION-8; the
    -- confirmation is of the CONVENTION CONTENT (the lineage rule), which governs
    -- both canonical charts' profiles identically.
    ('1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'agnivasa',
     'agnivasa_tithi_element_prithvi', 'corpus_default', 'hard',
     'computed',
     'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)',
     NULL, TRUE, FALSE, 'paddhati_v01',
     'native statement 2026-08-02 (correcting the 2026-07-28 elevation-session '
     'misstatement); recorded in SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md '
     '§NATIVE CONFIRMATIONS')
ON CONFLICT ON CONSTRAINT kala_paddhati_profile_natural_key DO UPDATE SET
    native_confirmed             = TRUE,
    awaiting_native_confirmation = FALSE,
    confirmation_provenance      = EXCLUDED.confirmation_provenance;

-- ── 3. Convention (B) — corpus_gap_ref now points at a COMMISSIONED work item ──
-- §NATIVE CONFIRMATIONS item 1 bullet 3 + item 3. Row B itself is UNCHANGED in
-- status: still declared_not_computed, still native_confirmed=FALSE (nothing about
-- its content was confirmed — it remains a slot, not a rule). Deterministic full
-- replace of corpus_gap_ref only, so re-runs converge.
UPDATE kala_paddhati_profile
SET corpus_gap_ref =
      'Muhurta-Chintamani translation — COMMISSIONED 2026-08-02 as a supervised '
      'corpus-curation task outside the night runs (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md '
      '§NATIVE CONFIRMATIONS item 3). Scope + provenance rules: '
      'MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md; untranslated-corpus evidence in '
      'bg_muhurta_factor_census rows. Convention (B) remains PARKED-HONEST until the '
      'translation lands, then re-opens.'
WHERE factor_family  = 'agnivasa'
  AND convention_id  = 'agnivasa_muhurta_chintamani_arithmetic'
  AND version        = 'paddhati_v01'
  AND chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa',
                   '1c826d5a-41cb-4450-b4dc-59d440e5f75a');

-- ── 4. Verify the flip landed (loud failure beats a silent no-op — §N.4/§N.8) ──
DO $$
DECLARE
    confirmed_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO confirmed_count
    FROM kala_paddhati_profile
    WHERE factor_family = 'agnivasa'
      AND convention_id = 'agnivasa_tithi_element_prithvi'
      AND version       = 'paddhati_v01'
      AND native_confirmed = TRUE
      AND awaiting_native_confirmation = FALSE
      AND confirmation_provenance LIKE '%§NATIVE CONFIRMATIONS%'
      AND chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa',
                       '1c826d5a-41cb-4450-b4dc-59d440e5f75a');
    IF confirmed_count <> 2 THEN
        RAISE EXCEPTION
          'migration 534: expected 2 native-confirmed agnivasa_tithi_element_prithvi '
          'rows (one per canonical chart), found % — the confirmation flip did not land',
          confirmed_count;
    END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   UPDATE kala_paddhati_profile
--   SET native_confirmed = FALSE,
--       awaiting_native_confirmation = TRUE,
--       confirmation_provenance = NULL
--   WHERE factor_family = 'agnivasa'
--     AND convention_id = 'agnivasa_tithi_element_prithvi'
--     AND version = 'paddhati_v01';
--   ALTER TABLE kala_paddhati_profile DROP COLUMN IF EXISTS confirmation_provenance;
--   COMMIT;
-- (Rolling back erases a native attestation from the DB but not from the record —
--  it remains in SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS.)
-- =============================================================================
