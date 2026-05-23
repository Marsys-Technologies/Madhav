-- data_source_expected_seed.sql — Initial expected row counts for data coverage reporting.
-- MCPT v3.1.0-S4
-- Status: Ready to load. Migrations 073-076 applied 2026-05-22. MCPT v3.3 backfill complete.

-- chart_facts categories
INSERT INTO data_source_expected (tool_name, category, expected_rows, backfill_phase, notes)
VALUES
  ('query_chart_facts', 'house',                  12,    'v3.1.0-S1',               'D1 house cusps — 12 houses'),
  ('query_chart_facts', 'planet',                  9,    'v3.1.0-S1',               '9 grahas + 2 nodes (Sun through Ketu)'),
  ('query_chart_facts', 'dasha_vimshottari',        9,    'v3.1.0-S1',               'Vimshottari dasha periods — 9 maha dashas'),
  ('query_chart_facts', 'dasha_chara',             12,    'v3.1.0-S1',               'Jaimini Chara Dasha — 12 sign-based periods'),
  ('query_chart_facts', 'saham',                   30,    'v3.1.0-S1',               'Arabian Parts / Saham points'),
  ('query_chart_facts', 'sensitive_point',         10,    'v3.1.0-S1',               'Sensitive points: Lagna, AL, UL, etc.'),
  ('query_chart_facts', 'birth_metadata',           5,    'v3.1.0-S1',               'Birth date, time, place, ayanamsha, house system'),
  ('query_chart_facts', 'strength_extra',          15,    'v3.1.0-S1',               'Jaimini karaka extra strength rows'),
  ('query_chart_facts', 'yoga',                    50,    'v3.1.0-S1',               'Yoga catalog (Raj, Dhana, etc.)'),
  ('query_chart_facts', 'shadbala',                 9,    'v3.3',                    'Shadbala per planet — 6-factor strength system'),
  ('query_chart_facts', 'ashtakavarga_sav',         9,    'v3.3',                    'Ashtakavarga Sarvashtakavarga per planet'),
  ('query_chart_facts', 'ashtakavarga_bav',        12,    'v3.3',                    'Ashtakavarga Bhinnashtakavarga per house per planet'),
  ('query_chart_facts', 'kp_cusp',                12,    'v3.3',                    'KP Cusp sub-lord table — 12 cusps'),
  ('query_chart_facts', 'kp_planet',               9,    'v3.3',                    'KP planet sub-lord positions'),
  ('query_chart_facts', 'kp_significator',         12,    'v3.3',                    'KP significators per house'),
  ('query_chart_facts', 'varshphal',               10,    'v3.3',                    'Tajaka Varshaphal annual chart positions (2024-2026)'),
  ('query_chart_facts', 'bhava_bala',              12,    'v3.3',                    'Bhava Bala — house strength per house'),
  ('query_chart_facts', 'upagraha',                 5,    'v3.3',                    'Upagraha positions (Gulika, Mandi, etc.)'),
  ('query_chart_facts', 'arudha',                  12,    'v3.1.0-S1',               'Arudha positions per house'),
  ('query_chart_facts', 'navatara',                 9,    'v3.1.0-S1',               'Navatara nakshatra groupings'),
  ('query_chart_facts', 'aspect',                  20,    'v3.1.0-S1',               'Graha drishti + rashi aspect rows'),
  ('query_chart_facts', 'chalit_shift',             9,    'v3.1.0-S1',               'Bhava Chalit house shift per planet'),
  ('query_chart_facts', 'special_lagna',            5,    'v3.1.0-S1',               'Special lagnas: AL, UL, HL, GL, VL')
ON CONFLICT (tool_name, category) DO NOTHING;

-- MSR signals
INSERT INTO data_source_expected (tool_name, category, expected_rows, backfill_phase, notes)
VALUES
  ('query_signals', 'msr_corpus', 573, 'v3.1.0-S1', 'MSR v5.0: 573 signals across all domains')
ON CONFLICT (tool_name, category) DO NOTHING;

-- Panchanga
INSERT INTO data_source_expected (tool_name, category, expected_rows, backfill_phase, notes)
VALUES
  ('query_panchanga', 'panchanga_daily', 73414, 'phase-4c-enrich-20260521-r2', 'Full enrichment: 1900-01-01 to 2100-12-31')
ON CONFLICT (tool_name, category) DO NOTHING;

-- LEL
INSERT INTO data_source_expected (tool_name, category, expected_rows, backfill_phase, notes)
VALUES
  ('lel_query', 'life_events', 36, 'v3.1.0-S1', 'LEL v1.6: 36 events + 5 period summaries + 6 chronic patterns')
ON CONFLICT (tool_name, category) DO NOTHING;

-- Tool caveats (v3.3 backfill complete 2026-05-22 — rows now populated)
INSERT INTO tool_caveats (tool_name, caveat_text, caveat_class, severity)
VALUES
  ('query_chart_facts', 'KP categories (kp_cusp, kp_planet, kp_significator): v3.3 backfill complete 2026-05-22.', 'data_gap', 'info'),
  ('query_chart_facts', 'Tajaka category (varshphal): v3.3 backfill complete 2026-05-22.', 'data_gap', 'info'),
  ('query_chart_facts', 'Strength categories (shadbala, ashtakavarga_sav, ashtakavarga_bav, bhava_bala): v3.3 backfill complete 2026-05-22.', 'data_gap', 'info'),
  ('query_chart_facts', 'Upagraha positions: v3.3 backfill complete 2026-05-22.', 'data_gap', 'info')
ON CONFLICT DO NOTHING;
