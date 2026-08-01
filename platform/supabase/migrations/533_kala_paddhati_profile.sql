-- Migration 533: kala_paddhati_profile — the per-chart convention profile (item 37's storage home)
-- =============================================================================
-- ṢAḌ-DARŚANA Wave W4, Lane R (YAJÑA-SETU), design ruling R-2
-- (KALA_W4_UPAYA_DESIGN_v1_0.md §3.2), implementing ADJUDICATION-8, which is BINDING
-- and supplies both the schema shape and the seed content.
--
-- SEEDED BY THIS MIGRATION, NOT BY A WRITER — and that is load-bearing, not a
-- convenience. This is versioned CONFIG DATA, exactly like the weights-v0 seed
-- (brief §2.5.4). ADJUDICATION-8's stated reversibility — "paddhati_v02 supersedes v01
-- by insert; no code, no schema, no rebuild" — only holds if it is config rather than
-- build output.
--   CONSEQUENCE, stated so a later session does not "helpfully" add one:
--   NO asset_registry row. NO count_sql. NO DAG edge. NO new writer.
--   (Design §8.1's table says so explicitly: kala_paddhati_profile → "New asset_registry
--   row? NO — versioned config seeded by migration, no writer, weights-v0 precedent.")
--
-- THE ZERO-PADDING IS MANDATORY. Version selection is `ORDER BY version DESC LIMIT 1`,
-- a STRING sort — `paddhati_v10` would otherwise sort below `paddhati_v2`. Same trap
-- ADJUDICATION-2 called out for `ne_v01`; repeated here because it bites per-table.
--
-- THE THREE RAILS ADJUDICATION-8 ATTACHES, restated as build requirements:
--   1. Row A is served as the OPERATIVE rule AND SIMULTANEOUSLY as an unconfirmed one.
--      The coverage census states, verbatim: "agnivāsa convention = corpus default
--      (tithi-element, pṛthvī-favourable); the native's lineage convention is not on
--      record." (Served by kala_sky_pattern.ts's PADDHATI_CENSUS_STATEMENT.)
--   2. Row B is NEVER computed and NEVER enters a candidate's grading. It exists so the
--      divergence surface is real rather than decorative. A `declared_not_computed`
--      convention that silently participates in scoring is the exact failure the status
--      exists to prevent — kala_sky_pattern.ts's `PaddhatiResolution.operative` filters
--      on `convention_status='computed'` for precisely this reason.
--   3. What is on record is the native's PRACTICE, not his lineage's CONVENTION CONTENT.
--      No builder may pin invented convention content and label it "the native's
--      lineage." Row B is therefore a SLOT with a corpus_gap_ref, not a rule.
--
-- Both canonical charts get the same seed shape; 1c826d5a's rows are seeded identically
-- (same corpus default, same native_confirmed=FALSE) — ADJUDICATION-8's own instruction.
--
-- Idempotency: CREATE TABLE IF NOT EXISTS + INSERT ... ON CONFLICT DO NOTHING on the
-- natural key. Re-running changes nothing. DO NOTHING rather than DO UPDATE is
-- deliberate: `native_confirmed` / `awaiting_native_confirmation` are NATIVE-ATTESTED
-- columns, and a re-run of this migration must never reset a confirmation the native has
-- since given (the §N.3 status-preserving discipline, applied to config).
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_paddhati_profile (
    id                          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id                    UUID        NOT NULL,
    factor_family               TEXT        NOT NULL,      -- e.g. 'agnivasa'
    convention_id               TEXT        NOT NULL,      -- e.g. 'agnivasa_tithi_element_prithvi'
    school_tag                  TEXT        NOT NULL,      -- e.g. 'corpus_default'
    constraint_role             TEXT        NOT NULL
        CHECK (constraint_role IN ('hard', 'soft', 'informational')),
    convention_status           TEXT        NOT NULL DEFAULT 'computed'
        CHECK (convention_status IN ('computed', 'declared_not_computed')),
    provenance                  TEXT        NOT NULL,
    corpus_gap_ref              TEXT,
    native_confirmed            BOOLEAN     NOT NULL DEFAULT FALSE,
    awaiting_native_confirmation BOOLEAN    NOT NULL DEFAULT TRUE,
    version                     TEXT        NOT NULL,      -- 'paddhati_v01' — ZERO-PADDED
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT kala_paddhati_profile_natural_key
        UNIQUE (chart_id, factor_family, convention_id, version)
);

CREATE INDEX IF NOT EXISTS idx_kala_paddhati_profile_chart_version
    ON kala_paddhati_profile (chart_id, version DESC);

COMMENT ON TABLE kala_paddhati_profile IS
  'ṢAḌ-DARŚANA item 37 / ADJUDICATION-8: the per-chart paddhati (convention) profile — '
  'which school convention governs each muhūrta factor family for THIS chart, whether it '
  'is computed or a declared divergence slot, and whether the native has confirmed it. '
  'Versioned CONFIG seeded by migration (weights-v0 precedent, brief §2.5.4) — NOT a '
  'built asset: no asset_registry row, no count_sql, no writer, by design. paddhati_v02 '
  'supersedes v01 by INSERT; no code, no schema, no rebuild.';

COMMENT ON COLUMN kala_paddhati_profile.convention_status IS
  'computed: this convention is live and governs grading. declared_not_computed: the '
  'convention is DECLARED so the divergence surface is real, but is NEVER computed and '
  'NEVER enters a candidate''s grading (ADJUDICATION-8 rail 2). A declared_not_computed '
  'row that silently participates in scoring is the exact failure this status exists to '
  'prevent — consumers MUST filter on convention_status=''computed''.';

COMMENT ON COLUMN kala_paddhati_profile.version IS
  'ZERO-PADDED (paddhati_v01, not paddhati_v1). Version selection is ORDER BY version '
  'DESC LIMIT 1 — a STRING sort — so paddhati_v10 would sort below paddhati_v2 without '
  'the padding. Same trap ADJUDICATION-2 called out for ne_v01.';

COMMENT ON COLUMN kala_paddhati_profile.native_confirmed IS
  'FALSE on every seeded row. What is on record is the native''s PRACTICE, not his '
  'lineage''s CONVENTION CONTENT — no builder may pin invented convention content and '
  'label it "the native''s lineage" (ADJUDICATION-8 rail 3).';

-- ── Seed: paddhati_v01, both canonical charts, verbatim from ADJUDICATION-8 (1)-(3) ──
-- Row A = the operative convention. Row B = the declared divergence slot.
INSERT INTO kala_paddhati_profile (
    chart_id, factor_family, convention_id, school_tag, constraint_role,
    convention_status, provenance, corpus_gap_ref,
    native_confirmed, awaiting_native_confirmation, version
) VALUES
    -- ── 482012f1 (Abhisek Mohanty) ──
    ('482012f1-710e-4a25-994a-93821f5871aa', 'agnivasa',
     'agnivasa_tithi_element_prithvi', 'corpus_default', 'hard',
     'computed',
     'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)',
     NULL, FALSE, TRUE, 'paddhati_v01'),
    ('482012f1-710e-4a25-994a-93821f5871aa', 'agnivasa',
     'agnivasa_muhurta_chintamani_arithmetic', 'muhurta_chintamani', 'hard',
     'declared_not_computed',
     'DECLARED SLOT ONLY — no convention content is pinned here. The Muhurta Chintamani '
     'arithmetic for Agni-vasa is not held in this codebase at verse grain: '
     'classical_text_chunks(text_id=''muhurta_chintamani'') is untranslated Devanagari OCR '
     '(content_en byte-identical to content_sa on all 274 rows; cleaned_translation_text '
     'NULL throughout). This row exists so the divergence surface is real rather than '
     'decorative, and is NEVER computed (ADJUDICATION-8 rail 2).',
     'Muhurta-Chintamani translation work item (see MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md '
     'and bg_muhurta_factor_census rows for the untranslated-corpus evidence)',
     FALSE, TRUE, 'paddhati_v01'),

    -- ── 1c826d5a (Abhinandan Mohanty) — same seed shape, per ADJUDICATION-8 ──
    ('1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'agnivasa',
     'agnivasa_tithi_element_prithvi', 'corpus_default', 'hard',
     'computed',
     'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)',
     NULL, FALSE, TRUE, 'paddhati_v01'),
    ('1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'agnivasa',
     'agnivasa_muhurta_chintamani_arithmetic', 'muhurta_chintamani', 'hard',
     'declared_not_computed',
     'DECLARED SLOT ONLY — no convention content is pinned here. See the 482012f1 row for '
     'the full untranslated-corpus evidence.',
     'Muhurta-Chintamani translation work item',
     FALSE, TRUE, 'paddhati_v01')
ON CONFLICT ON CONSTRAINT kala_paddhati_profile_natural_key DO NOTHING;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_paddhati_profile;
--   COMMIT;
-- (No asset_registry row to delete — by design, see the header.)
-- =============================================================================
