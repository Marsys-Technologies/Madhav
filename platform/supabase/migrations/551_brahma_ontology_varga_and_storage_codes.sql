-- Migration 551: brahma_ontology registry completion
-- ADHIṢṬHĀNA Campaign A, Lane A3 (2026-08-08)
--
-- Adds entity_class='varga' (30 rows: l0_reference.py's 19-varga BPHS set
-- fully contained within the L1 writer's 30-varga computational set
-- ga_vargas_writer.py ALL_30_VARGAS; delta = 11 new) and appends the
-- storage-format codes actually used in chart_facts.fact_subject (e.g.
-- 'MAR', 'RAH_MEAN', 'HOUSE_07', 'D9') as synonyms on the existing
-- planet/house rows. ADDITIVE ONLY: no existing row's existing content
-- is altered or removed — new rows via INSERT ... ON CONFLICT DO NOTHING,
-- new synonym elements via synonyms = synonyms || (EXCEPT-deduped array).
-- Safe to run twice (idempotent both ways).
--
-- Source of truth: platform/python-sidecar/brahmagyan/l0_ontology.py
-- (this file is generated FROM that module so the two cannot drift;
-- see gen_migration.py in the PR's scratchpad history / commit message).
--
-- Companion fix (same PR, not this migration): resolve_entity.ts gains a
-- deterministic ORDER BY tie-break preferring entity_class='varga', because
-- 14 of the 30 varga codes (D3/D4/D7/D9/D10/D12/D16/D20/D24/D27/D30/D40/
-- D45/D60) already collide with a pre-existing entity_class='concept' row's
-- bare 'D<n>' synonym (added under CONCEPT_EXTRA before this lane) — additive
-- -only forbids removing that legacy synonym, so the ORDER BY makes the
-- resolution deterministic instead of leaving it to accidental row order.

BEGIN;

-- Part 1: entity_class='varga' — 30 new rows (new entity_class; brand-new
-- canonical_ids d1..d2700 cannot collide with anything -> ON CONFLICT DO
-- NOTHING is belt-and-braces idempotency, not expected to ever fire).
INSERT INTO brahma_ontology (entity_class, canonical_id, canonical_name_en, canonical_name_sa, synonyms, description, source_citation)
VALUES
  ('varga', 'd1', 'Rashi', 'Rashi', ARRAY['D1', 'rashi_chart', 'd1_chart']::text[], 'Overall chart; physical body; all life matters (the birth/natal chart itself)', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd2', 'Hora', 'Hora', ARRAY['D2', 'hora_chart']::text[], 'Wealth; finances; material possessions', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd3', 'Drekkana', 'Drekkana', ARRAY['D3', 'drekkana_chart']::text[], 'Siblings; courage; communication (3 formula variants: Parashari/Jagannatha/Somanatha)', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd4', 'Chaturthamsha', 'Chaturthamsha', ARRAY['D4', 'chaturthamsa']::text[], 'Property; fixed assets; home; fortune', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd5', 'Panchamsha', 'Panchamsha', ARRAY['D5', 'panchamsa']::text[], 'Spiritual merit; past-life credit; children', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd6', 'Shashthamsha', 'Shashthamsha', ARRAY['D6', 'shashthamsa']::text[], 'Health; enemies; debts; service', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd7', 'Saptamsha', 'Saptamsha', ARRAY['D7', 'saptamsa']::text[], 'Children; progeny; creativity', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd8', 'Ashtamsha', 'Ashtamsha', ARRAY['D8', 'ashtamsa']::text[], 'Longevity; obstacles; sudden events; inheritance', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd9', 'Navamsha', 'Navamsha', ARRAY['D9', 'navamsha_chart']::text[], 'Marriage; dharma; spiritual development; inner nature — most important divisional', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd10', 'Dashamsha', 'Dashamsha', ARRAY['D10', 'dasamsa']::text[], 'Career; professional achievement; public life', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd11', 'Rudramsha', 'Rudramsha', ARRAY['D11', 'ekadashamsha', 'ekadasamsa']::text[], 'Gains; elder siblings; fulfillment of desires (11H significations)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd12', 'Dvadashamsha', 'Dvadashamsha', ARRAY['D12', 'dwadasamsa']::text[], 'Parents; ancestors; karmic inheritance', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd14', 'Chaturdashamsha', 'Chaturdashamsha', ARRAY['D14']::text[], 'Father, paternal matters (secondary emphasis)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd15', 'Panchadashamsha', 'Panchadashamsha', ARRAY['D15']::text[], 'Children, progeny (tertiary emphasis)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd16', 'Shodashamsha', 'Shodashamsha', ARRAY['D16', 'shodasamsa']::text[], 'Vehicles; conveyances; happiness', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd20', 'Vimshamsha', 'Vimshamsha', ARRAY['D20', 'vimsamsa']::text[], 'Spiritual practice; upasana; religious activities', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd21', 'Ekavimshamsha', 'Ekavimshamsha', ARRAY['D21']::text[], 'Mother, maternal matters (secondary emphasis)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd24', 'Chaturvimshamsha', 'Chaturvimshamsha', ARRAY['D24', 'chaturvimsamsa']::text[], 'Education; learning; academic achievements', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd27', 'Nakshatramsha', 'Nakshatramsha', ARRAY['D27', 'bhamsa', 'saptavimshamsha']::text[], 'Strength; stamina; vitality', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd30', 'Trimshamsha', 'Trimshamsha', ARRAY['D30', 'trimsamsa']::text[], 'Miseries; evils; health issues', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd32', 'Dvatrimshamsha', 'Dvatrimshamsha', ARRAY['D32']::text[], 'Secondary navamsha-linked harmonics', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd33', 'Trayastrimshamsha', 'Trayastrimshamsha', ARRAY['D33']::text[], 'Secondary ashtamsha-linked harmonics (longevity/obstacles)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd40', 'Khavedamsha', 'Khavedamsha', ARRAY['D40', 'khavedamsa']::text[], 'Maternal ancestry; auspicious effects', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd45', 'Akshavedamsha', 'Akshavedamsha', ARRAY['D45', 'akshavedamsa']::text[], 'Paternal ancestry; general indications', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd50', 'Panchashamsha', 'Panchashamsha', ARRAY['D50']::text[], 'Higher/subtle significations (secondary emphasis)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd54', 'Chatuhpanchashamsha', 'Chatuhpanchashamsha', ARRAY['D54']::text[], 'Higher/subtle significations (tertiary emphasis)', 'Not in l0_reference.py''s 19-varga BPHS-cited set. Sanskrit ordinal-numeral + "aṃśa" divisional-chart naming convention (same pattern as the 19 BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the L1 writer''s supplementary Parashari varga set (ga_vargas_writer.py SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per ga_vargas_writer.py VARGA_KARYA.'),
  ('varga', 'd60', 'Shastiamsha', 'Shastiamsha', ARRAY['D60', 'shashtiamsa', 'shashtyamsha']::text[], 'Past-life karma; most subtle influences', 'BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); name + signification per brahmagyan/l0_reference.py VARGAS (reference_vargas seed, BPHS_SHODASHA citation)'),
  ('varga', 'd108', 'Ashtottaramsha', 'Ashtottaramsha', ARRAY['D108', 'ashtottaramsa']::text[], 'Karma-type attribution; finest Nadi-tradition subdivision', 'Not in l0_reference.py''s 19-varga BPHS-cited set. "Nadiamsa" terminology and rishi/karma-type attribution per ga_vargas_writer.py inline documentation (D150_RISHIS/D2700_SUB_RISHIS) and A6_VARGAS_SPEC_v1_0.md §Q5/Q6 (K.N. Rao Nadi-jyotish tradition, 27-rishi cycle); D108/D2700 named by the same ordinal-numeral convention as the core set.'),
  ('varga', 'd150', 'Nadiamsha', 'Nadiamsha', ARRAY['D150', 'nadiamsa']::text[], 'Nadi rishi attribution; 27-rishi cycle; finest Nadi-tradition subdivision', 'Not in l0_reference.py''s 19-varga BPHS-cited set. "Nadiamsa" terminology and rishi/karma-type attribution per ga_vargas_writer.py inline documentation (D150_RISHIS/D2700_SUB_RISHIS) and A6_VARGAS_SPEC_v1_0.md §Q5/Q6 (K.N. Rao Nadi-jyotish tradition, 27-rishi cycle); D108/D2700 named by the same ordinal-numeral convention as the core set.'),
  ('varga', 'd2700', 'Sukshma Nadiamsha', 'Sukshma-Nadiamsha', ARRAY['D2700', 'sub_nadiamsa', 'atinadiamsa']::text[], 'Sub-Nadi (sub-rishi) attribution; finest Nadi-tradition sub-subdivision', 'Not in l0_reference.py''s 19-varga BPHS-cited set. "Nadiamsa" terminology and rishi/karma-type attribution per ga_vargas_writer.py inline documentation (D150_RISHIS/D2700_SUB_RISHIS) and A6_VARGAS_SPEC_v1_0.md §Q5/Q6 (K.N. Rao Nadi-jyotish tradition, 27-rishi cycle); D108/D2700 named by the same ordinal-numeral convention as the core set.')
ON CONFLICT (entity_class, canonical_id) DO NOTHING;

-- Part 2: planet storage-code synonyms (additive append, EXCEPT-deduped so
-- re-running this migration is a no-op the second time).
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['SUN']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'sun';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['MOON']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'moon';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['MAR', 'MARS']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'mars';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['MER', 'MERCURY']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'mercury';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['JUP', 'JUPITER']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'jupiter';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['VEN', 'VENUS']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'venus';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['SAT', 'SATURN']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'saturn';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['RAH_MEAN', 'RAHU']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'rahu';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['KET_MEAN', 'KETU']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'ketu';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['LAGNA']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'ascendant';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['MC']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'planet' AND canonical_id = 'midheaven';

-- Part 3: house storage-code synonyms (additive append, EXCEPT-deduped).
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_01', 'HOUSE_1', 'H1']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_01';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_02', 'HOUSE_2', 'H2']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_02';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_03', 'HOUSE_3', 'H3']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_03';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_04', 'HOUSE_4', 'H4']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_04';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_05', 'HOUSE_5', 'H5']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_05';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_06', 'HOUSE_6', 'H6']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_06';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_07', 'HOUSE_7', 'H7']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_07';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_08', 'HOUSE_8', 'H8']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_08';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_09', 'HOUSE_9', 'H9']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_09';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_10', 'H10']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_10';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_11', 'H11']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_11';
UPDATE brahma_ontology SET synonyms = synonyms || (SELECT COALESCE(array_agg(x), ARRAY[]::text[]) FROM unnest(ARRAY['HOUSE_12', 'H12']::text[]) AS x WHERE x <> ALL(synonyms)) WHERE entity_class = 'house' AND canonical_id = 'house_12';

COMMIT;

-- DOWN (rollback): additive-only migration; rollback removes exactly what
-- Part 1-3 added, nothing else. Not expected to be needed.
--
--   BEGIN;
--   DELETE FROM brahma_ontology WHERE entity_class = 'varga';
--   -- (synonym removals omitted — additive appends are safe to leave in
--   -- place; a full precise reversal would need per-row array surgery)
--   COMMIT;
