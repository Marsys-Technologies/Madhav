-- Gaṇita (L1) naming reconciliation — relabel asset_registry ids ganita.* → ga_*.
-- Asset IDs ONLY. No physical table renamed. Reversible via the down-block.
BEGIN;

DELETE FROM asset_registry WHERE layer='ganita' AND asset_id IN (
  'ganita.graha_sthana','ganita.varga','ganita.dasakrama','ganita.balatva',
  'ganita.suksmabindu','ganita.pancanga_janma','ganita.sade_sati','ganita.tajaka'
);

INSERT INTO asset_registry
  (asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
   storage_type, target_table, count_sql, size_sql, target_floor,
   expected_volume_formula, volume_explanation, depends_on, scope, is_active) VALUES
  ('ga_positions','ganita',1,'Graha-sthāna','Positions',
   'Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)',
   'postgres_table','ganita_positions',
   'SELECT count(*) FROM ganita_positions WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''ganita_positions'')',
   NULL,'GRAHAS * AYANAMSHAS',
   '9 grahas × ayanamsha count — one position row per graha per ayanamsha',
   ARRAY[]::text[],'per_chart',true),

  ('ga_vargas','ganita',2,'Varga','Divisional charts',
   'D1–D60 divisional chart positions per ayanamsha',
   'postgres_table','chart_divisionals',
   'SELECT count(*) FROM chart_divisionals WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''chart_divisionals'')',
   NULL,'VARGAS * GRAHAS * AYANAMSHAS',
   '60 vargas × 9 grahas × ayanamsha count — structural',
   ARRAY[]::text[],'per_chart',true),

  ('ga_dashas','ganita',3,'Daśākrama','Vimshottari dasha',
   'Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha',
   'postgres_table','ganita_dashas',
   'SELECT count(*) FROM ganita_dashas WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''ganita_dashas'')',
   NULL,'(9 + 81 + 729) * AYANAMSHAS',
   'Vimshottari tree: 9 MD + 81 AD + 729 PD = 819 rows × ayanamsha count — structural',
   ARRAY[]::text[],'per_chart',true),

  ('ga_strength','ganita',4,'Balatva','Strength tables',
   'Shadbala, ashtakavarga, and bhava bala per ayanamsha',
   'postgres_table',NULL,NULL,NULL,NULL,
   '(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS',
   'Shadbala: 6 scores × 9 grahas; ashtakavarga: 8 tables × 9 grahas × 12 signs; bhava bala: 6 scores × 12 bhavas — all × ayanamshas',
   ARRAY[]::text[],'per_chart',false),

  ('ga_sensitive','ganita',5,'Sūkṣmabindu','Sensitive points',
   'Per-chart sensitive point positions computed from the catalog × ayanamshas',
   'postgres_table',NULL,NULL,NULL,NULL,
   'ACTUAL(bg_reference) * AYANAMSHAS',
   'Derived from the reference library count × ayanamshas; awaits dedicated per-chart table',
   ARRAY['bg_reference']::text[],'per_chart',false),

  ('ga_panchanga','ganita',6,'Pañcāṅga-janma','Birth panchanga',
   'Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha',
   'postgres_table','chart_panchanga',
   'SELECT count(*) FROM chart_panchanga WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''chart_panchanga'')',
   NULL,'AYANAMSHAS',
   'One panchanga row per ayanamsha — structural',
   ARRAY[]::text[],'per_chart',true),

  ('ga_sade_sati','ganita',7,'Sāḍesātī','Sade Sati periods',
   'Saturn transit-over-natal-Moon Sade Sati + Dhaiya window calculations per ayanamsha',
   'postgres_table',NULL,NULL,NULL,NULL,'AYANAMSHAS',
   'One row per ayanamsha for the native''s Sade Sati window; awaits dedicated table',
   ARRAY[]::text[],'per_chart',false),

  ('ga_tajaka','ganita',8,'Tājaka','Tajaka Varshaphal',
   'Annual chart (Varshaphal) and Tajaka aspects per ayanamsha',
   'postgres_table',NULL,NULL,NULL,NULL,NULL,
   'Writer output — row count depends on aspect configurations found; awaits dedicated table',
   ARRAY[]::text[],'per_chart',false);

-- Also update cross-layer depends_on references in other assets that pointed at ganita.* ids
UPDATE asset_registry
  SET depends_on = array_replace(depends_on, 'ganita.dasakrama', 'ga_dashas')
  WHERE 'ganita.dasakrama' = ANY(depends_on);

UPDATE asset_registry
  SET depends_on = array_replace(depends_on, 'ganita.suksmabindu', 'ga_sensitive')
  WHERE 'ganita.suksmabindu' = ANY(depends_on);

UPDATE asset_registry
  SET depends_on = array_replace(depends_on, 'ganita.pancanga_janma', 'ga_panchanga')
  WHERE 'ganita.pancanga_janma' = ANY(depends_on);

UPDATE asset_registry
  SET expected_volume_formula = replace(expected_volume_formula, 'ganita.dasakrama', 'ga_dashas')
  WHERE expected_volume_formula LIKE '%ganita.dasakrama%';

COMMIT;

-- DOWN (manual rollback):
--   DELETE FROM asset_registry WHERE layer='ganita' AND asset_id LIKE 'ga_%';
--   UPDATE asset_registry
--     SET depends_on = array_replace(depends_on, 'ga_dashas', 'ganita.dasakrama')
--     WHERE 'ga_dashas' = ANY(depends_on);
--   UPDATE asset_registry
--     SET depends_on = array_replace(depends_on, 'ga_sensitive', 'ganita.suksmabindu')
--     WHERE 'ga_sensitive' = ANY(depends_on);
--   UPDATE asset_registry
--     SET depends_on = array_replace(depends_on, 'ga_panchanga', 'ganita.pancanga_janma')
--     WHERE 'ga_panchanga' = ANY(depends_on);
--   UPDATE asset_registry
--     SET expected_volume_formula = replace(expected_volume_formula, 'ga_dashas', 'ganita.dasakrama')
--     WHERE expected_volume_formula LIKE '%ga_dashas%';
--   Then re-run the prior asset_registry_seed.ts ganita block to restore ganita.* ids.
