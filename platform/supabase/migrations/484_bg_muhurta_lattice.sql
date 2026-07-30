-- Migration 484: bg_muhurta_lattice — global boundary/factor lattice (ṢAḌ-DARŚANA item 36-substrate)
-- =============================================================================
-- Context: SHAD_DARSHANA_BRIEF_v2_0.md §2 file map ("bg_muhurta_lattice.py — global
-- boundary/factor lattice tables, rolling horizon (~5y), incl. Agnivāsa states,
-- combination-yoga spans, kālams, ghaṭīs (chart-independent parts only; per-chart
-- contact joins live in ka_kshetra stage 1)") + KALA_SUPREME_ELEVATION_v1_0.md §9
-- (item 36 core: "Stage 1 — The temporal lattice ... boundary event ... Agnivāsa state
-- changes (tithi×vara function) ... amṛta/viṣa ghaṭīs").
--
-- This migration creates ONLY the table + its asset_registry row. The lattice rows
-- themselves are computed and written by the bg_muhurta_lattice writer
-- (pipeline/orchestrator/writers/bg_muhurta_lattice.py) at build time — a large
-- deterministic panchang_engine computation, not a hand-curated corpus, so it
-- belongs in the writer (mirrors migrations 472/473's precedent).
--
-- WHAT THIS TABLE HOLDS (four chart-independent factor families; see writer module
-- docstring for full methodology):
--   1. agnivasa          — Agni's tithi-keyed elemental residence (Pṛthvī/Jala/Vāyu/
--                           Ākāśa), one row per calendar day.
--   2. combination_yoga   — muhūrta combination-yoga spans (Sarvārtha-siddhi, Amṛta-
--                           siddhi, Ravi/Guru-Puṣya, Tripuṣkara/Dvipuṣkara, Siddha-
--                           yoga, Bhadra/Vishti, Pañchaka) via panchang_engine's
--                           already-cited detectors (MC/BS/DP).
--   3. kalam              — day-part inauspicious/auspicious windows (rāhu-kālam,
--                           yamagaṇḍa, gulika-kālam, durmuhūrta, brāhma-muhūrta,
--                           abhijit, amṛta-kālam, varjyam, etc.).
--   4. ghati_muhurta      — the 30 named ghaṭī-grained day+night muhūrtas.
--
-- REFERENCE LOCATION (explicit scope decision, documented in full in the writer's
-- module docstring): these factor families are chart-INDEPENDENT (no native's birth
-- data), but kālam/ghaṭī/sunrise-anchored windows are NOT location-independent —
-- they need a sunrise/sunset. This table computes them at ONE fixed reference
-- location — Bhubaneswar/IST (lat=20.27, lon=85.84, tz_offset=+330 min), the same
-- (lat, lon, tz_offset) triple `platform/python-sidecar/routers/panchang.py`'s
-- `_PANCHANGA_KNOWN_LOCATIONS['bhubaneswar']` already uses as its FORENSIC-matching
-- fallback — never a per-querent location. Adjusting to a specific querent's
-- location is explicitly OUT of scope here (a future per-location join), exactly
-- parallel to how bg_sky_calendar deferred per-chart joins to `ka_kshetra`.
--
-- Idempotency (§N.3 — L0 = global reference, safe to upsert): natural key is
-- (factor_family, factor_key, start_utc) — deterministic recomputation of an
-- already-covered window reproduces byte-identical rows (panchang_engine has no
-- RNG/external state), so ON CONFLICT DO NOTHING is correct; a re-run only WIDENS
-- coverage as the rolling forward horizon advances (see writer docstring).
--
-- Nirmāṇa build-tracker contract (brief §2.5): one of the four new `bg_*` assets
-- (bg_cohort, bg_sky_calendar, bg_muhurta_lattice, bg_parihara_rules) that build
-- ONLY via an explicit super-admin L0 trigger — never auto-pulled into a per-chart
-- build. depends_on=[] — election substrate is query-time-read by a future serving
-- engine (`lib/kala_lattice_query.ts`, W3), not a per-chart DAG dependency (brief
-- §2.5.3: "Election substrate ... appears as L0 assets with their own rows, not as
-- ka_kshetra edges").
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_muhurta_lattice (
    id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    factor_family            TEXT        NOT NULL
        CHECK (factor_family IN ('agnivasa', 'combination_yoga', 'kalam', 'ghati_muhurta')),
    factor_key               TEXT        NOT NULL,
    start_utc                TIMESTAMP   NOT NULL,
    end_utc                  TIMESTAMP   NOT NULL,
    -- detail: factor-family-specific fields, e.g.
    --   agnivasa: {"tithi_id": int, "tithi_name": str, "element": "Prithvi"|"Jala"|
    --              "Vayu"|"Akasha", "chandra_vasa": str, "rahu_vasa": str,
    --              "disha_vasa": str, "nakshatra_vasa": str, "bhadra_vasa": str}
    --   combination_yoga: {"strength": "auspicious"|"inauspicious", "stars": int}
    --   kalam: {"category": "inauspicious"|"auspicious"}
    --   ghati_muhurta: {"number": int, "period": "day"|"night", "quality": str}
    detail                   JSONB       NOT NULL DEFAULT '{}'::jsonb,
    reference_lat            NUMERIC(7,4) NOT NULL,
    reference_lon            NUMERIC(7,4) NOT NULL,
    reference_tz_offset_minutes INTEGER  NOT NULL,
    reference_location_key   TEXT        NOT NULL DEFAULT 'bhubaneswar',
    ayanamsha_key            TEXT        NOT NULL DEFAULT 'lahiri',
    sampling_method          TEXT        NOT NULL,
    source_citation          TEXT        NOT NULL,
    corpus_status            TEXT        NOT NULL DEFAULT 'computed_cited'
        CHECK (corpus_status IN ('computed_cited', 'computed_uncited_convention')),
    build_id                 UUID,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_muhurta_lattice_natural_key
        UNIQUE (factor_family, factor_key, start_utc)
);

CREATE INDEX IF NOT EXISTS idx_bg_muhurta_lattice_family_time
    ON bg_muhurta_lattice (factor_family, start_utc);
CREATE INDEX IF NOT EXISTS idx_bg_muhurta_lattice_time_range
    ON bg_muhurta_lattice (start_utc, end_utc);
CREATE INDEX IF NOT EXISTS idx_bg_muhurta_lattice_detail_gin
    ON bg_muhurta_lattice USING GIN (detail);

COMMENT ON TABLE bg_muhurta_lattice IS
  'ṢAḌ-DARŚANA item 36-substrate: global chart-independent muhūrta boundary/factor '
  'lattice — Agnivāsa states, combination-yoga spans, kālam periods, ghaṭī-muhūrta '
  'boundaries — computed at a fixed Bhubaneswar/IST reference location over a rolling '
  '~5y forward horizon. Per-chart/per-querent-location joins are explicitly OUT of '
  'scope — see pipeline/orchestrator/writers/bg_muhurta_lattice.py module docstring. '
  'Query-time-read by a future serving engine (kala_lattice_query.ts, W3) — not a '
  'per-chart DAG dependency.';

COMMENT ON COLUMN bg_muhurta_lattice.factor_family IS
  'One of: agnivasa, combination_yoga, kalam, ghati_muhurta.';
COMMENT ON COLUMN bg_muhurta_lattice.factor_key IS
  'Family-specific sub-type key, e.g. "agni_vasa" (agnivasa family); '
  '"sarvartha_siddhi"/"amrit_siddhi"/"bhadra"/etc (combination_yoga); '
  '"rahu_kalam"/"abhijit"/etc (kalam); "1:Rudra"/"16:Girisha"/etc (ghati_muhurta).';
COMMENT ON COLUMN bg_muhurta_lattice.corpus_status IS
  'computed_cited: table carries an inline classical-source citation in '
  'panchang_engine (MC/BS/DP). computed_uncited_convention: value is a live, '
  'already-shipped deterministic convention (used elsewhere in production, e.g. '
  'ga_panchanga_writer.py AGNI_VASA_BIRTH) but its source table in panchang_engine '
  'carries no explicit per-row classical citation comment — disclosed honestly '
  'rather than inventing one; see bg_parihara_rules factor census for the full gap '
  'register.';

-- asset_registry row (Nirmāṇa build-tracker contract, brief §2.5.1 — seed row lands
-- in the SAME PR as the writer). scope='global' (L0, not per-chart); count_sql counts
-- ALL rows (no chart_id). depends_on=[] per §2.5.3 (query-time-read, not a DAG edge).
--
-- target_floor: per CLAUDE.md §N.4, set to the REAL row count from a live local
-- verification run of this exact writer against a real (throwaway) Postgres
-- instance — see the writer's PR body for the exact live-verified count and horizon
-- window used (horizon rolls forward on every rebuild, so a later build reads >=
-- this count, never less).
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'bg_muhurta_lattice', 'brahmagyan', 22,
    'Muhūrta Jālaka', 'Muhūrta Boundary/Factor Lattice',
    'Global chart-independent muhūrta factor lattice — Agnivāsa states, combination-'
    'yoga spans (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-Puṣya, Tripuṣkara/'
    'Dvipuṣkara, Siddha-yoga, Bhadra, Pañchaka), kālam periods (rāhu/gulika/'
    'yamagaṇḍa/durmuhūrta/brāhma-muhūrta/abhijit/amṛta-kālam/varjyam), and 30-fold '
    'ghaṭī-muhūrta day+night boundaries, over a rolling ~5y forward horizon at a '
    'fixed Bhubaneswar/IST reference location. Per-chart contact joins are '
    'ka_kshetra''s job (W3). ṢAḌ-DARŚANA campaign item 36-substrate.',
    'postgres_table', 'bg_muhurta_lattice',
    'SELECT COUNT(*) FROM bg_muhurta_lattice', 'SELECT pg_total_relation_size(''bg_muhurta_lattice'')',
    91737, NULL, NULL,
    'Live-verified 2026-07-30 against a real throwaway Postgres (pg17 + pgvector): '
    '1,826 agnivasa + 1,481 combination_yoga + 33,650 kalam + 54,780 ghati_muhurta '
    '= 91,737, over horizon 2026-07-30 -> 2031-07-30 (today+5y at verification '
    'time), computed at the fixed Bhubaneswar/IST reference location. Because the '
    'horizon rolls FORWARD from "today" every rebuild and old rows are never '
    'deleted (ON CONFLICT DO NOTHING only), a later build reads >= this count, '
    'never less — a legal floor, not a guess (mirrors bg_sky_calendar''s '
    'live-verified-count precedent).',
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
--   DELETE FROM asset_registry WHERE asset_id = 'bg_muhurta_lattice';
--   DROP TABLE IF EXISTS bg_muhurta_lattice;
--   COMMIT;
-- =============================================================================
