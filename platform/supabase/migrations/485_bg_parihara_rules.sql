-- Migration 485: bg_parihara_rules — parihāra graph + activity rule tables + factor
-- census registry (ṢAḌ-DARŚANA item 41: Muhūrta Factor Census + corpus-gap register
-- + parihāra rule-table extraction)
-- =============================================================================
-- Context: SHAD_DARSHANA_BRIEF_v2_0.md §2 file map ("bg_parihara_rules.py — parihāra
-- graph + activity rule tables + factor census registry (corpus-extracted,
-- citation-carrying; L0 reference data)") + KALA_SUPREME_ELEVATION_v1_0.md §9 Stage 2
-- ("Muhūrta Factor Census ... every factor carries its citation ... a factor
-- without a corpus rule table is not_computed (corpus gap) and becomes an
-- ingestion work item, never improvised") + Stage 3 ("the parihāra graph
-- (adjudication, not addition) ... doṣas_present → parihāras_applied (citations)
-- → residual_doṣas → net standing").
--
-- This migration creates ONLY the three tables + the asset_registry row. All
-- content is computed/materialized by the bg_parihara_rules writer
-- (pipeline/orchestrator/writers/bg_parihara_rules.py) at build time, by
-- REUSING/JOINING the existing ingested corpus table `brahma_dosha_catalog`
-- and the existing panchang_engine per-activity muhūrta quality tables
-- (EVENT_TABLES) — NEVER re-ingesting or duplicating corpus content.
-- (`brahma_remedy_corpus` is cited as evidence in the factor census for the
-- deity_graha_correspondence row only; the writer does not query it
-- directly — corrected 2026-07-30, Opus corpus-citation review, from an
-- earlier draft that overstated this as a direct join.) Where the
-- corpus genuinely lacks a rule (e.g. mṛtyu-yoga, dagdha-yoga as day-quality
-- combination-yogas; Śiva-vāsa; mṛtyu-bhāga; gaṇḍānta spans), the honest
-- disposition is `not_in_corpus`/`not_computed`, recorded in the census, never a
-- fabricated rule (see writer PR body for the full corpus-gap register with
-- ingestion work items named).
--
-- THREE TABLES:
--   1. bg_parihara_rules        — the doṣa-cancellation (parihāra) graph. Sourced
--      from brahma_dosha_catalog.cancellation_conditions, filtered to rows carrying
--      a REAL classical_citations text_id (excludes the 'classical_tradition'
--      placeholder — 53 of 79 brahma_dosha_catalog rows carry that placeholder and
--      are correctly excluded here). Honest scope note: this is NATAL dosha-
--      cancellation content (Manglik/Kala-Sarpa/Kemadruma/etc bhanga rules) — the
--      corpus has NO muhūrta-specific dosha-cancellation content ("Abhijit cancels
--      most doshas", dāna-parihāras) at chapter/verse grain; that gap is recorded
--      in the factor census (table 3), not fabricated here.
--   2. bg_muhurta_activity_rules — per-activity (vivah/griha_pravesh/vyapara/yatra/
--      property_purchase/mantra_initiation/upaya_ritual/sadhana_initiation) factor
--      quality rules, REUSING panchang_engine.shastra_tables.EVENT_TABLES verbatim
--      (already real, cited, tested content — MC/BS/MMP/DP per-table citations) —
--      never re-authored.
--   3. bg_muhurta_factor_census  — the census/gap registry itself (item 41's other
--      half): one row per named factor family from KALA_SUPREME_ELEVATION_v1_0.md
--      §9 Stage 2's working register, each with disposition computed/not_computed/
--      not_in_corpus + citation-or-gap-reason + evidence pointer.
--
-- Idempotency (§N.3 — L0 = global reference data, safe to upsert): all three
-- tables are DETERMINISTIC MIRRORS of live upstream tables/constants that could
-- themselves change over time (unlike bg_cohort/bg_sky_calendar's from-scratch
-- computation), so a rebuild should REFRESH content, not just skip existing rows
-- — ON CONFLICT (natural key) DO UPDATE, not DO NOTHING.
--
-- Nirmāṇa build-tracker contract (brief §2.5): one of the four new `bg_*` assets
-- that build ONLY via an explicit super-admin L0 trigger. depends_on=[] — query-
-- time-read by a future serving engine, not a per-chart DAG dependency.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_parihara_rules (
    id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dosha_canonical_id       TEXT        NOT NULL,
    dosha_name_en            TEXT        NOT NULL,
    dosha_category           TEXT        NOT NULL,
    cancellation_index       INTEGER     NOT NULL,
    cancellation_condition_text TEXT     NOT NULL,
    net_standing             TEXT        NOT NULL DEFAULT 'cancellable_by_condition'
        CHECK (net_standing IN ('cancellable_by_condition', 'cancellable_by_remedial_act')),
    scope                    TEXT        NOT NULL DEFAULT 'natal'
        CHECK (scope IN ('natal', 'muhurta')),
    source_text_id           TEXT        NOT NULL,
    source_chapter           INTEGER,
    source_citation          TEXT        NOT NULL,
    build_id                 UUID,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_parihara_rules_natural_key
        UNIQUE (dosha_canonical_id, cancellation_index)
);

CREATE INDEX IF NOT EXISTS idx_bg_parihara_rules_dosha
    ON bg_parihara_rules (dosha_canonical_id);
CREATE INDEX IF NOT EXISTS idx_bg_parihara_rules_category
    ON bg_parihara_rules (dosha_category);

COMMENT ON TABLE bg_parihara_rules IS
  'ṢAḌ-DARŚANA item 36/41: the parihāra (doṣa-cancellation) graph — a citation-'
  'filtered materialization of brahma_dosha_catalog.cancellation_conditions '
  '(excludes rows whose only citation is the classical_tradition placeholder). '
  'scope=''natal'' honestly discloses this is natal dosha-bhanga content, not '
  'muhūrta-specific dosha-cancellation (that content is not_in_corpus — see '
  'bg_muhurta_factor_census). References brahma_dosha_catalog by '
  'dosha_canonical_id rather than duplicating its full row content.';

CREATE TABLE IF NOT EXISTS bg_muhurta_activity_rules (
    id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_class           TEXT        NOT NULL
        CHECK (activity_class IN (
            'vivah', 'griha_pravesh', 'vyapara', 'yatra', 'property_purchase',
            'mantra_initiation', 'upaya_ritual', 'sadhana_initiation'
        )),
    factor_type               TEXT        NOT NULL
        CHECK (factor_type IN ('tithi', 'nakshatra', 'vara')),
    factor_id                 INTEGER     NOT NULL,
    quality_score             NUMERIC(4,3) NOT NULL CHECK (quality_score BETWEEN 0 AND 1),
    source_citation            TEXT        NOT NULL,
    build_id                   UUID,
    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_muhurta_activity_rules_natural_key
        UNIQUE (activity_class, factor_type, factor_id)
);

CREATE INDEX IF NOT EXISTS idx_bg_muhurta_activity_rules_activity
    ON bg_muhurta_activity_rules (activity_class, factor_type);

COMMENT ON TABLE bg_muhurta_activity_rules IS
  'ṢAḌ-DARŚANA item 41: per-activity muhūrta factor-quality rules, materialized '
  'verbatim from panchang_engine.shastra_tables.EVENT_TABLES (8 activity classes: '
  'vivah/griha_pravesh/vyapara/yatra/property_purchase/mantra_initiation/'
  'upaya_ritual/sadhana_initiation) — real, already-cited, already-tested content '
  '(MC/BS/MMP/DP per-table citations), reused verbatim, never re-authored.';

CREATE TABLE IF NOT EXISTS bg_muhurta_factor_census (
    id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    factor_family            TEXT        NOT NULL,
    factor_name              TEXT        NOT NULL,
    disposition              TEXT        NOT NULL
        CHECK (disposition IN ('computed', 'not_computed', 'not_in_corpus')),
    citation_or_gap_note     TEXT        NOT NULL,
    evidence_pointer         TEXT        NOT NULL,
    school_tag               TEXT,
    build_id                 UUID,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_muhurta_factor_census_natural_key
        UNIQUE (factor_family, factor_name)
);

CREATE INDEX IF NOT EXISTS idx_bg_muhurta_factor_census_disposition
    ON bg_muhurta_factor_census (disposition);

COMMENT ON TABLE bg_muhurta_factor_census IS
  'ṢAḌ-DARŚANA item 41: the Muhūrta Factor Census — one row per named classical '
  'timing-factor family (per KALA_SUPREME_ELEVATION_v1_0.md §9 Stage 2''s working '
  'register), each disposed computed/not_computed/not_in_corpus with a citation or '
  'an honest gap reason + ingestion work item. CI-trackable completeness register; '
  'a factor lacking a corpus rule table is disclosed here, never improvised '
  'elsewhere (B.10).';

-- asset_registry row (Nirmāṇa build-tracker contract, brief §2.5.1 — seed row lands
-- in the SAME PR as the writer). scope='global'; count_sql sums all three tables'
-- rows (a single asset owning three physical tables, mirroring how a single
-- writer may own multiple related tables). depends_on=[] per §2.5.3.
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'bg_parihara_rules', 'brahmagyan', 71,
    'Parihāra Jāla', 'Parihāra Rule Graph + Muhūrta Factor Census',
    'Global chart-independent parihāra (doṣa-cancellation) graph, per-activity '
    'muhūrta factor-quality rules, and the Muhūrta Factor Census + corpus-gap '
    'register. Directly queries brahma_dosha_catalog and materializes '
    'panchang_engine.shastra_tables.EVENT_TABLES — never re-ingests corpus '
    'content (brahma_remedy_corpus is referenced only as evidence in the '
    'factor census, for the deity_graha_correspondence row; this writer does '
    'not query it directly). Corpus gaps (e.g. mṛtyu-yoga, dagdha-yoga '
    'day-quality tables, Śiva-vāsa) are honestly recorded as not_in_corpus, '
    'never fabricated. ṢAḌ-DARŚANA campaign item 36-substrate/41.',
    'postgres_table', 'bg_parihara_rules',
    'SELECT (SELECT COUNT(*) FROM bg_parihara_rules) + (SELECT COUNT(*) FROM bg_muhurta_activity_rules) + (SELECT COUNT(*) FROM bg_muhurta_factor_census)',
    'SELECT pg_total_relation_size(''bg_parihara_rules'') + pg_total_relation_size(''bg_muhurta_activity_rules'') + pg_total_relation_size(''bg_muhurta_factor_census'')',
    439, NULL, NULL,
    'Live-verified 2026-07-30: 60 parihara-graph condition rows (queried directly '
    'against the REAL production brahma_dosha_catalog: 26 doshas carry a real, '
    'non-placeholder citation, flattening to 60 individual cancellation-condition '
    'rows) + 329 activity-rule rows (exact, deterministic — sum of tithi/'
    'nakshatra/vara entries across panchang_engine''s 8 EVENT_TABLES) + 50 census '
    'rows (exact — len(CENSUS_ROWS), updated from 37 by the Opus corpus-citation '
    'review''s dangling-pointer fix, which added 13 rows: panchaka, varjyam, '
    'visha_ghati, yamakantaka, krakaca, sashtighati, ghati_muhurta_30fold, and '
    '6 sandhya/vijaya/godhuli/nishita keys) = 439. The 329 + 50 = 379 portion is '
    'a hard deterministic floor; the parihara-graph portion depends on '
    'brahma_dosha_catalog''s live content and was confirmed via a direct '
    'read-only query against production, not fabricated or estimated.',
    ARRAY[]::text[], 'global', true, true,
    'Brahmagyan', 'L0', 'CURRENT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql            = EXCLUDED.count_sql,
    target_table         = EXCLUDED.target_table,
    has_writer            = EXCLUDED.has_writer,
    english_description   = EXCLUDED.english_description,
    target_floor          = EXCLUDED.target_floor,
    expected_volume_formula = EXCLUDED.expected_volume_formula,
    expected_volume_inputs  = EXCLUDED.expected_volume_inputs,
    volume_explanation      = EXCLUDED.volume_explanation;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'bg_parihara_rules';
--   DROP TABLE IF EXISTS bg_muhurta_factor_census;
--   DROP TABLE IF EXISTS bg_muhurta_activity_rules;
--   DROP TABLE IF EXISTS bg_parihara_rules;
--   COMMIT;
-- =============================================================================
