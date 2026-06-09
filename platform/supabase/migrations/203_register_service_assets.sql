-- Migration 203: Register bg_panchanga + bg_ephemeris_engine as L0 Brahmagyan service assets.
--
-- Two new rows in asset_registry (scope='global', layer='brahmagyan', asset_type='service').
-- Service assets have no count_sql (no rows). Completeness = health probe GREEN/degraded/down.
-- catalog_status='CURRENT' because L0 spec is finalized (panchang_engine is production-live).
--
-- Depends on migration 202 (asset_type, layer_name, layer_index, provides_apis,
-- health_probe, catalog_status columns; storage_type='service' CHECK).
--
-- FORENSIC invariant baked into probe spec:
--   panchanga_instant(1984-02-05T10:43, 20.27, 85.84, +330)
--   → Shukla Tritiya / Purva Bhadrapada / Shiva / Garaja / Ravivara
--
-- Down block: DELETE both rows from asset_registry.

-- ── UP ────────────────────────────────────────────────────────────────────────

INSERT INTO asset_registry (
  asset_id,
  layer,
  sort_order,
  sanskrit_name,
  english_name,
  english_description,
  storage_type,
  asset_type,
  layer_name,
  layer_index,
  scope,
  is_active,
  catalog_status,
  target_table,
  count_sql,
  size_sql,
  target_floor,
  depends_on,
  provides_apis,
  health_probe
) VALUES
(
  'bg_panchanga',
  'brahmagyan',
  13,  -- L0 sort order after existing 12 data assets
  'पञ्चाङ्ग गणना',
  'Panchanga Engine',
  'Deterministic panchang computation service (swisseph DE441, Lahiri ayanamsha, Drik-parity). '
  'Exposes panchanga_instant(instant,lat,lon,tz_offset) and panchanga_day(date,lat,lon,tz_offset). '
  'Zero LLM. Floor: 5 angas + timing windows + 9 graha states.',
  'service',
  'service',
  'Brahmagyan',
  'L0',
  'global',
  true,
  'CURRENT',
  NULL,   -- service assets have no target_table
  NULL,   -- service assets have no count_sql
  NULL,
  NULL,   -- no target_floor (row count not applicable)
  '{}',   -- no data-asset dependencies
  '[
    {
      "api": "panchanga_instant",
      "signature": "panchanga_instant(instant: datetime, lat: float, lon: float, tz_offset: int) -> PanchangaInstant",
      "description": "Anga state at exact moment — birth chart / event instant"
    },
    {
      "api": "panchanga_day",
      "signature": "panchanga_day(date: date, lat: float, lon: float, tz_offset: int) -> Panchang",
      "description": "Full sunrise-based daily panchang including timings and graha states"
    }
  ]'::jsonb,
  '{
    "probe_type": "panchanga_engine",
    "forensic_instant": "1984-02-05T10:43:00",
    "forensic_lat": 20.27,
    "forensic_lon": 85.84,
    "forensic_tz_offset": 330,
    "forensic_expected": {
      "tithi": "Shukla Tritiya",
      "nakshatra": "Purva Bhadrapada",
      "yoga": "Shiva",
      "karana": "Garaja",
      "vara": "Ravivara"
    }
  }'::jsonb
),
(
  'bg_ephemeris_engine',
  'brahmagyan',
  14,  -- L0 sort order after bg_panchanga
  'दृक् एफिमेरिस',
  'Ephemeris Engine',
  'Swiss Ephemeris (pyswisseph) with DE441 JPL file providing sidereal planetary positions '
  'from 9999 BCE to 9999 CE. Foundation for all computational Jyotish in MARSYS-JIS. '
  'Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).',
  'service',
  'service',
  'Brahmagyan',
  'L0',
  'global',
  true,
  'CURRENT',
  NULL,
  NULL,
  NULL,
  NULL,
  '{}',
  '[
    {
      "api": "swisseph.calc_ut",
      "description": "Planetary longitude at Julian Day (UT) — wraps pyswisseph swe.calc_ut"
    },
    {
      "api": "swisseph.houses_ex",
      "description": "House cusps + Lagna at JD with geographic coordinates"
    }
  ]'::jsonb,
  '{
    "probe_type": "ephemeris_engine",
    "forensic_jd": 2445701.948264,
    "expected_sun_approximate_sign": 10,
    "note": "JD = 1984-02-05 10:43 IST → UTC = 2445701.948264. Sun in Makara (sign 10) sidereal Lahiri."
  }'::jsonb
)
ON CONFLICT (asset_id) DO UPDATE SET
  english_description = EXCLUDED.english_description,
  asset_type          = EXCLUDED.asset_type,
  layer_name          = EXCLUDED.layer_name,
  layer_index         = EXCLUDED.layer_index,
  catalog_status      = EXCLUDED.catalog_status,
  provides_apis       = EXCLUDED.provides_apis,
  health_probe        = EXCLUDED.health_probe,
  is_active           = EXCLUDED.is_active;

-- Verify insertion
DO $$
DECLARE
  cnt INTEGER;
BEGIN
  SELECT COUNT(*) INTO cnt
  FROM asset_registry
  WHERE asset_id IN ('bg_panchanga', 'bg_ephemeris_engine')
    AND asset_type = 'service'
    AND catalog_status = 'CURRENT';
  IF cnt != 2 THEN
    RAISE EXCEPTION 'Migration 203 verification failed: expected 2 service assets, got %', cnt;
  END IF;
END $$;

-- ── DOWN ──────────────────────────────────────────────────────────────────────
-- To reverse: DELETE FROM asset_registry WHERE asset_id IN ('bg_panchanga', 'bg_ephemeris_engine');
