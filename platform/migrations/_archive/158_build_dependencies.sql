-- 158_build_dependencies.sql
-- Build asset dependency graph for cascade invalidation and resume logic.
-- NOTE: Tables already created via 158_build_dependencies.sql; this file is
-- idempotent and safe to apply on a DB that already has these objects.
CREATE TABLE IF NOT EXISTS build_dependencies (
  asset_id      text PRIMARY KEY,
  depends_on    text[] NOT NULL DEFAULT '{}',
  layer         text NOT NULL,
  sort_order    int NOT NULL,
  display_name  text,
  category_prefix text
);
INSERT INTO build_dependencies (asset_id, depends_on, layer, sort_order, display_name, category_prefix) VALUES
  ('A1',  '{}',                                  'L1',   1,  'Pratyaksha',        'a1_'),
  ('A2',  '{A1}',                                'L1',   2,  'Janma-Patra',       'a2_'),
  ('A3',  '{A2}',                                'L1',   3,  'Mula-Lakshana',     'a3_'),
  ('A4',  '{A2}',                                'L1',   4,  'Panchanga',         'a4_'),
  ('A5',  '{A2}',                                'L1',   5,  'Marma-Bindu',       'a5_'),
  ('A6',  '{A2}',                                'L1',   6,  'Shodashvarga',      'a6_'),
  ('A7',  '{A2}',                                'L1',   7,  'Dasha-Kala',        'a7_'),
  ('A8',  '{A2,A3,A6,A7}',                       'L25',  8,  'Bala-Yoga',         'a8_'),
  ('A9',  '{A2,A7}',                             'L25',  9,  'Sade-Sati',         'a9_'),
  ('A10', '{A3,A4,A5,A6,A7,A8,A9}',              'L25', 10,  'Lakshana-Sangraha', 'a10_'),
  ('A11', '{A10}',                               'L25', 11,  'Bhava-Sambandha',   'a11_'),
  ('A12', '{A10,A11}',                           'L25', 12,  'Chakra-Jala',       'a12_'),
  ('A13', '{A10,A11,A12}',                       'L25', 13,  'Aushadhi',          'a13_'),
  ('A15', '{A7,A8,A10}',                         'L3',  15,  'Sangat-Kala',       'a15_'),
  ('A16', '{A15}',                               'L3',  16,  'Sankalpa-Phala',    'a16_'),
  ('A17', '{A10,A12}',                           'L3',  17,  'Yantra',            'a17_'),
  ('A18', '{A7,A15}',                            'L3',  18,  'Vedha',             'a18_'),
  ('A19', '{A2,A7,A15}',                         'L3',  19,  'Bhrigu-Bindu',      'a19_'),
  ('A20', '{A7,A8}',                             'L3',  20,  'Varshesha',         'a20_'),
  ('A21', '{A3,A15}',                            'L3',  21,  'Drishti-Patrika',   'a21_'),
  ('A22', '{A15,A16,A18,A20,A21}',               'L3',  22,  'Varsha-Darshan',    'a22_'),
  ('META_ALPHA', '{A10,A11,A12,A15,A16,A22}',    'L3',  23,  'Trikala-Darshan',   'meta_alpha_'),
  ('META_BETA',  '{A10,A11,A12,A13}',            'L3',  24,  'Yantra-Sangraha',   'meta_beta_'),
  ('META_GAMMA', '{A10,A11,A12}',                'L3',  25,  'Sampradaya',        'meta_gamma_'),
  ('META_DELTA', '{A10,A11,A12,A13}',            'L3',  26,  'Shunya',            'meta_delta_'),
  ('META_EPSILON','{A10,A11,A12,A13,A15,A16}',   'L3',  27,  'Pramana',           'meta_epsilon_'),
  ('META_ZETA',  '{A15,A16,A18,A19,A20,A21,A22}','L3',  28,  'Kala-Darpana',      'meta_zeta_')
ON CONFLICT (asset_id) DO UPDATE SET
  depends_on=EXCLUDED.depends_on, layer=EXCLUDED.layer, sort_order=EXCLUDED.sort_order,
  display_name=EXCLUDED.display_name, category_prefix=EXCLUDED.category_prefix;
