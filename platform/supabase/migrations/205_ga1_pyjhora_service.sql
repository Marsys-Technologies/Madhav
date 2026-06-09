-- Migration 205: Register GA1 (PyJHora chart engine) as L1 service asset
-- GA1 is the deterministic compute engine that produces all L1 Gaṇita facts.
-- GA2 (forensic_render) is intentionally NOT registered — it is a 0-row stub
-- superseded by the L2 retrieval layer + panchang service (per campaign §C.3).
-- Per: L1_GANITA_BUILD_CAMPAIGN_v1_0.md §C.3 · UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md §B-D

BEGIN;

INSERT INTO asset_registry (
  asset_id,
  layer,
  layer_name,
  layer_index,
  asset_type,
  storage_type,
  sanskrit_name,
  english_name,
  english_description,
  scope,
  sort_order,
  depends_on,
  is_active,
  catalog_status,
  health_probe,
  provides_apis,
  target_floor,
  target_table,
  count_sql
)
VALUES (
  'ga_pyjhora_engine',
  'ganita',
  'Gaṇita',
  'L1',
  'service',
  'service',
  'Gaṇita-yantra',
  'PyJHora Chart Engine',
  'PyJHora 4.8.6 — deterministic Jyotish computation engine. Produces all L1 Gaṇita facts: positions, vargas, dashas, strength, sensitive points, panchanga, Sade Sati. FORENSIC-grounded: Sun=Capricorn, Moon nak=Purva Bhadrapada, Lagna=Aries.',
  'global',
  9,
  ARRAY[]::text[],
  true,
  'CURRENT',
  '{"probe_type": "pyjhora_engine", "forensic_lat": 20.27, "forensic_lon": 85.84, "forensic_jd": 2445701.948264, "forensic_expected": {"sun_sign": "Makara", "moon_nakshatra": "Purva Bhadrapada", "lagna": "Mesha"}, "forensic_datetime": "1984-02-05T10:43:00+05:30"}'::jsonb,
  '[{"api": "compute_chart", "description": "Full L1 chart computation from birth data — positions, houses, dashas, vargas, strength via PyJHora 4.8.6"}, {"api": "pyjhora.Chart", "description": "PyJHora Chart class: Chart(jd, lat, lon, tz_offset, ayanamsha) — wraps Swiss Ephemeris via pyswisseph"}]'::jsonb,
  NULL,
  NULL,
  NULL
)
ON CONFLICT (asset_id) DO UPDATE SET
  asset_type      = EXCLUDED.asset_type,
  storage_type    = EXCLUDED.storage_type,
  layer_name      = EXCLUDED.layer_name,
  layer_index     = EXCLUDED.layer_index,
  catalog_status  = EXCLUDED.catalog_status,
  health_probe    = EXCLUDED.health_probe,
  provides_apis   = EXCLUDED.provides_apis,
  english_description = EXCLUDED.english_description,
  is_active       = EXCLUDED.is_active;

COMMIT;
