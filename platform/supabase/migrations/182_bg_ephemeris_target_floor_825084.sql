-- bg_ephemeris floor reconciliation: 1980–2060 (29,200) → 1900–2150 (825,084) per PR #228.
-- 91,676 days × 9 grahas = 825,084. Engine VOLUME_FLOOR + prod data already at this value;
-- migration 174 registered 29,200 (original 1980-2060 floor); this aligns the registry.
BEGIN;
UPDATE asset_registry SET
  target_floor = 825084,
  expected_volume_formula = 'GRAHAS * DATE_RANGE_DAYS',
  expected_volume_inputs = '{"GRAHAS": 9, "DATE_RANGE_DAYS": 91676, "start_date": "1900-01-01", "end_date": "2150-12-31"}'::jsonb,
  volume_explanation = '825,084 rows = 91,676 days (1900-01-01 to 2150-12-31) × 9 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu). Raw tropical stored; 5 ayanamshas (Lahiri, Raman, KP, Yukteshwar, Surya-Siddhanta) derived at read time. Source: pyswisseph DE441 (==2.10.3.2).'
WHERE asset_id = 'bg_ephemeris';
COMMIT;
