-- Migration 473: bg_sky_events — chart-independent sky-event diary (ṢAḌ-DARŚANA item 3)
-- =============================================================================
-- Context: SHAD_DARSHANA_BRIEF_v2_0.md §2 file map ("bg_sky_calendar.py — chart-
-- independent sky-event diary (ingresses, stations, eclipses, returns, double-transit
-- geometry); per-chart contact joins live in `ka_kshetra` stage 1") + §1 item 3
-- ("Sky-event calendar: ingresses, stations, eclipse-to-natal, returns, Guru-Śani
-- double-transit"). This migration creates ONLY the table + its asset_registry row;
-- the events themselves are computed and written by the bg_sky_calendar writer
-- (pipeline/orchestrator/writers/bg_sky_calendar.py) at build time — a large
-- deterministic pyswisseph computation, not a hand-curated corpus, so it belongs in
-- the writer, not the migration (mirrors migration 472's bg_synthetic_cohort precedent).
--
-- Migration number: 473 was verified free on both `main` (HEAD at 471) and the
-- in-flight `shad-darshana/bg-cohort` branch (which claims 472 for bg_synthetic_cohort)
-- before this file was created.
--
-- SCOPE (documented in full in bg_sky_calendar.py's module docstring):
--   Four event families, all chart-independent real astronomy:
--     1. ingress        — sign-boundary crossings, 9 grahas.
--     2. station         — retro/direct stations, the 5 classical planets that
--                           station (Mars/Mercury/Jupiter/Venus/Saturn). Sun/Moon
--                           never station. Rahu/Ketu deliberately excluded — see
--                           writer docstring "Rahu/Ketu decision".
--     3. eclipse_solar / eclipse_lunar — TIMING only (max/begin/end instant +
--                           classical type), via pyswisseph's own global
--                           eclipse-finding functions. Per-location visibility/
--                           magnitude is NOT computed here (that needs an observer
--                           position, i.e. is chart-specific).
--     4. double_transit   — slow-mover conjunction geometry; Jupiter-Saturn is the
--                           brief's own paradigm case ("Guru-Śani double-transit").
--   Returns are explicitly OUT of this table (they need a natal degree, i.e. are
--   chart-specific) — see writer docstring "RETURNS SCOPE DECISION". Eclipse-to-
--   natal / any per-chart join is `ka_kshetra`'s job (brief §2), not this writer's.
--
-- Idempotency (§N.3 — L0 = global reference, safe to upsert): natural key is
-- (event_type, primary_body, secondary_body, event_jd) — but Postgres UNIQUE
-- constraints treat NULL as distinct-from-NULL, and secondary_body IS NULL for
-- ingress/station events (single-body events), which would let ON CONFLICT DO
-- NOTHING silently fail to dedupe those families. secondary_body_key is a STORED
-- generated column collapsing NULL -> '' precisely to make the natural key total
-- (matches the standard Postgres "COALESCE for uniqueness with nullable columns"
-- pattern). event_jd is rounded to 5 decimal places (~0.86s precision) by the
-- writer before insert -- the algorithm is fully deterministic (no RNG, no
-- external state), so a re-run recomputing an already-covered horizon window
-- reproduces byte-identical rounded jd values, and only the NEWLY-extended
-- forward window (per the writer's rolling horizon) produces new rows.
--
-- Nirmāṇa build-tracker contract (brief §2.5): one of the four new `bg_*` assets
-- (bg_cohort, bg_sky_calendar, bg_muhurta_lattice, bg_parihara_rules) that build
-- ONLY via an explicit super-admin L0 trigger — never auto-pulled into a per-chart
-- build. A per-chart build whose L0 upstream (this table) is dormant correctly
-- shows any future dependent as blocked, per §2.5.2. Rolling-horizon refresh
-- policy per §2.5.6: this table's forward edge ages and is refreshed via the
-- explicit L0 trigger on a cadence recorded in the campaign state ledger.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_sky_events (
    id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type            TEXT        NOT NULL
        CHECK (event_type IN ('ingress', 'station', 'eclipse_solar', 'eclipse_lunar', 'double_transit')),
    primary_body          TEXT        NOT NULL,
    secondary_body        TEXT,
    -- Generated NULL-collapsing key for the natural-key uniqueness constraint
    -- below (see idempotency note above).
    secondary_body_key    TEXT GENERATED ALWAYS AS (COALESCE(secondary_body, '')) STORED,
    event_jd              DOUBLE PRECISION NOT NULL,
    event_datetime_utc    TIMESTAMP   NOT NULL,
    sign                  TEXT,
    nakshatra             TEXT,
    longitude_deg         DOUBLE PRECISION,
    speed_dps             DOUBLE PRECISION,
    -- detail: event-family-specific fields, e.g.
    --   ingress: {"target_sign": "..."}
    --   station: {"station_type": "retrograde"|"direct"}
    --   eclipse_*: {"eclipse_type": "total"|"annular"|"partial"|"penumbral"|
    --               "annular_total", "is_central": bool, "begin_jd": float,
    --               "end_jd": float}
    --   double_transit: {"orb_deg": float, "planet_b_lon": float}
    detail                JSONB       NOT NULL DEFAULT '{}'::jsonb,
    ayanamsha_key         TEXT        NOT NULL DEFAULT 'lahiri',
    sampling_method       TEXT        NOT NULL,
    source_citation       TEXT        NOT NULL,
    build_id              UUID,
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_sky_events_natural_key
        UNIQUE (event_type, primary_body, secondary_body_key, event_jd)
);

CREATE INDEX IF NOT EXISTS idx_bg_sky_events_type_time
    ON bg_sky_events (event_type, event_datetime_utc);
CREATE INDEX IF NOT EXISTS idx_bg_sky_events_primary_body_time
    ON bg_sky_events (primary_body, event_datetime_utc);
CREATE INDEX IF NOT EXISTS idx_bg_sky_events_detail_gin
    ON bg_sky_events USING GIN (detail);

COMMENT ON TABLE bg_sky_events IS
  'ṢAḌ-DARŚANA item 3: chart-independent global sky-event diary — sign ingresses '
  '(9 grahas), planetary stations (5 classical planets), solar/lunar eclipse timing, '
  'and double-transit conjunction geometry (Jupiter-Saturn at minimum). Returns and '
  'any per-chart/natal join are explicitly OUT of scope here — see '
  'pipeline/orchestrator/writers/bg_sky_calendar.py module docstring. Populated by '
  'that writer; rolling horizon (brief §2.5.6), re-run to extend forward coverage.';

COMMENT ON COLUMN bg_sky_events.event_type IS
  'One of: ingress, station, eclipse_solar, eclipse_lunar, double_transit.';
COMMENT ON COLUMN bg_sky_events.secondary_body_key IS
  'Generated: COALESCE(secondary_body, ''''). Exists only to make the natural-key '
  'UNIQUE constraint total across NULL secondary_body (single-body events).';
COMMENT ON COLUMN bg_sky_events.event_jd IS
  'Julian day (UT) of the event, rounded to 5 decimal places by the writer '
  '(~0.86s precision) — the natural-key uniqueness grain for idempotent re-runs.';
COMMENT ON COLUMN bg_sky_events.detail IS
  'Event-family-specific fields — see table comment for the per-family shape.';

-- asset_registry row (Nirmāṇa build-tracker contract, brief §2.5.1 — seed row lands
-- in the SAME PR as the writer). scope='global' (L0, not per-chart); count_sql counts
-- ALL rows (no chart_id — this is not a chart-scoped asset). depends_on=[] — this
-- writer computes live via pyswisseph and does not read ephemeris_daily, so it has
-- no DAG edge onto bg_ephemeris (matches bg_cohort's own depends_on=[] precedent).
--
-- target_floor: per CLAUDE.md §N.4 ("floors aspirational, not gates — set target_floor
-- = achieved count after build; never fabricate rows to hit a number"), this is set to
-- 31,064 — the REAL row count from a live local verification run of this exact writer
-- against a real (throwaway) Postgres instance, horizon 1900-01-01 -> 2036-07-29
-- (today+10y at verification time): 28,760 ingress + 1,674 station + 308 eclipse_solar
-- + 312 eclipse_lunar + 10 double_transit = 31,064. Because HISTORY_START is fixed and
-- the forward edge rolls forward with every rebuild's "today" (module docstring HORIZON
-- section), a later production build will read >= this count, never less — a legal
-- floor, not a guess (mirrors bg_cohort's exactly-known COHORT_SIZE precedent; sky-event
-- density just isn't knowable ahead of a real computation the way a fixed sample size is,
-- so a live-verified count is the honest equivalent here).
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'bg_sky_calendar', 'brahmagyan', 21,
    'Ākāśa Pañjikā', 'Sky-Event Calendar',
    'Chart-independent global sky-event diary: sign ingresses (9 grahas), planetary '
    'stations (5 classical planets), solar/lunar eclipse timing, and Jupiter-Saturn '
    'double-transit conjunction geometry, over a rolling 1900 -> today+10y horizon. '
    'Returns and per-chart/natal joins are out of scope — ka_kshetra''s job. '
    'ṢAḌ-DARŚANA campaign item 3.',
    'postgres_table', 'bg_sky_events',
    'SELECT COUNT(*) FROM bg_sky_events', 'SELECT pg_total_relation_size(''bg_sky_events'')',
    31064, NULL, NULL,
    'Live-verified 2026-07-29 against a real throwaway Postgres: 28,760 ingress + '
    '1,674 station + 308 eclipse_solar + 312 eclipse_lunar + 10 double_transit = '
    '31,064, over horizon 1900-01-01 -> 2036-07-29 (today+10y at verification time). '
    'A later build reads >= this count as the forward edge rolls forward (never less).',
    ARRAY[]::text[], 'global', true, true,
    'Brahmagyan', 'L0', 'CURRENT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql            = EXCLUDED.count_sql,
    target_table         = EXCLUDED.target_table,
    has_writer            = EXCLUDED.has_writer,
    english_description   = EXCLUDED.english_description;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'bg_sky_calendar';
--   DROP TABLE IF EXISTS bg_sky_events;
--   COMMIT;
-- =============================================================================
