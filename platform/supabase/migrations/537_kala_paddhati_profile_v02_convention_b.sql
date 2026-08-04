-- Migration 537: kala_paddhati_profile paddhati_v02 -- flips Agnivasa Convention (B)
-- (agnivasa_muhurta_chintamani_arithmetic) from declared_not_computed to computed.
-- =============================================================================
-- ADJUDICATION-16 (SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md) extracted a
-- real, cited, computable arithmetic from the translated Muhurta-Cintamani corpus (MC 1.36,
-- chunk_id=muhurta_chintamani_pg0048_c01): remainder = (tithi_id + 1 + vara_id) mod 4, where
-- {0,3} -> Prthvi (favourable), 1 -> Akasha, 2 -> Patala.
--
-- ADJUDICATION-17 (SHAD_DARSHANA_ADJUDICATION_17_AGNIVASA_MULTI_CONVENTION_GRADING_v1_0.md)
-- ruled how this can flip live without silently overriding Convention (A), the
-- native-confirmed convention: Convention (B) becomes a SECOND, SEPARATELY SERVED
-- concurrence/dissent voice (see platform-mcp/src/lib/agnivasa_convention_b_voice.ts) --
-- it does NOT enter the `residence` constraint's hard-gate matching path in
-- kala_sky_pattern.ts, which is structurally bound to Convention (A)'s bg_muhurta_lattice
-- atoms and cannot represent a second, vara-dependent classification.
--
-- Per ADJUDICATION-8's own designed reversibility ("paddhati_v02 supersedes v01 by INSERT;
-- no code, no schema, no rebuild") and migration 533's own header (NEVER edit an applied
-- migration): this is a pure INSERT of new version='paddhati_v02' rows. Nothing about
-- version='paddhati_v01' changes.
--
-- native_confirmed STAYS FALSE. Nothing here attests Convention (B) as the native's own
-- lineage practice -- only that its arithmetic is now computed and citeable (ADJUDICATION-8
-- rail 3: what is on record is the native's PRACTICE, not invented convention content; the
-- native's practice attestation belongs to Convention A alone, migration 534).
--
-- Idempotency: same pattern as 533 -- INSERT ... ON CONFLICT ON CONSTRAINT
-- kala_paddhati_profile_natural_key DO NOTHING. A re-run changes nothing.
-- =============================================================================

BEGIN;

INSERT INTO kala_paddhati_profile (
    chart_id, factor_family, convention_id, school_tag, constraint_role,
    convention_status, provenance, corpus_gap_ref,
    native_confirmed, awaiting_native_confirmation, version
) VALUES
    -- ── 482012f1 (Abhisek Mohanty) ──
    ('482012f1-710e-4a25-994a-93821f5871aa', 'agnivasa',
     'agnivasa_muhurta_chintamani_arithmetic', 'muhurta_chintamani', 'hard',
     'computed',
     'MC 1.36 (chunk_id=muhurta_chintamani_pg0048_c01), translated 2026-08-03 '
     '(MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md); extraction ruled in '
     'SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md. Arithmetic: '
     'remainder = (tithi_id + 1 + vara_id) mod 4; {0,3}=Prthvi(fav), 1=Akasha, 2=Patala. '
     'Served as a second, informational concurrence/dissent voice ONLY (ADJUDICATION-17) -- '
     'NEVER enters the residence hard-gate Convention A alone governs.',
     NULL, FALSE, TRUE, 'paddhati_v02'),

    -- ── 1c826d5a (Abhinandan Mohanty) -- same seed shape ──
    ('1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'agnivasa',
     'agnivasa_muhurta_chintamani_arithmetic', 'muhurta_chintamani', 'hard',
     'computed',
     'MC 1.36 (chunk_id=muhurta_chintamani_pg0048_c01) -- see the 482012f1 row for full '
     'provenance. Same arithmetic, same disposition (ADJUDICATION-16/17).',
     NULL, FALSE, TRUE, 'paddhati_v02')
ON CONFLICT ON CONSTRAINT kala_paddhati_profile_natural_key DO NOTHING;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM kala_paddhati_profile
--     WHERE version = 'paddhati_v02'
--       AND factor_family = 'agnivasa'
--       AND convention_id = 'agnivasa_muhurta_chintamani_arithmetic';
--   COMMIT;
-- (Reverts to paddhati_v01 being the latest version again -- version selection is
-- ORDER BY version DESC LIMIT 1, so removing v02 rows alone is sufficient.)
-- =============================================================================
