-- Migration 388: brahma_event_ontology + brahma_activity_ontology (bg_ghatana) — BA-P3A Step 1
-- Source authority: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §5 (22 event classes) + §6 (12 activity classes).
-- Event ontology: life-event classes keyed to LEL categories.
-- Activity ontology: electional (muhurta) activity classes.
-- Both: global scope; L0 = ON CONFLICT DO UPDATE idempotency.

BEGIN;

-- ── DDL: brahma_event_ontology ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahma_event_ontology (
    event_class_id      TEXT        PRIMARY KEY,
    name_en             TEXT        NOT NULL,
    domain              TEXT        NOT NULL CHECK (domain IN (
                            'career','wealth','relationship','progeny','health','education',
                            'family','residence','travel','spirituality','character','transition','general')),
    lel_category        TEXT        NOT NULL,
    signature_model     JSONB       NOT NULL,
    magnitude_floor     TEXT        NOT NULL CHECK (magnitude_floor IN ('trivial','moderate','significant','major','life_altering')),
    adjacency           JSONB,
    base_rate_by_age    JSONB       NOT NULL,
    matching_rules      JSONB,
    citations           TEXT[],
    version             TEXT        NOT NULL DEFAULT '1.0',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE brahma_event_ontology IS
  'BA-P3A: Life-event ontology — 22 event classes keyed to LEL categories. '
  'Seeded from W1 seed package §5. Governs L4 prediction anchors + L5 adjudication. '
  'signature_model: {houses, lords, karakas, vargas, dasha_rules, transit_triggers}. '
  'base_rate_by_age: {band_0_12, band_13_25, band_26_40, band_41_60, band_60_plus}.';

-- ── SEED: brahma_event_ontology (22 classes) ──────────────────────────────────

INSERT INTO brahma_event_ontology
  (event_class_id, name_en, domain, lel_category, signature_model, magnitude_floor, adjacency, base_rate_by_age, citations, version)
VALUES
  ('career_entry', 'Career Entry', 'career', 'career',
    '{"houses":["10","6","1"],"lords":["10L","6L"],"karakas":["Sun","Saturn"],"vargas":["D10"],"dasha_rules":"MD/AD of 10th-related","transit_triggers":"Jupiter/Saturn transit to 10th"}',
    'moderate',
    '["career_change"]',
    '{"band_0_12":0.00,"band_13_25":0.55,"band_26_40":0.20,"band_41_60":0.05,"band_60_plus":0.01}',
    ARRAY['BPHS ch.10 (karma-bhava)','Phaladeepika ch.10'],
    '1.0'),

  ('career_advancement', 'Career Advancement', 'career', 'career',
    '{"houses":["10","11"],"lords":["10L","11L"],"karakas":["Sun"],"vargas":["D10"],"dasha_rules":"benefic transit to 10th","transit_triggers":"Jupiter to 10th/11th"}',
    'moderate',
    '["career_entry"]',
    '{"band_0_12":0.00,"band_13_25":0.15,"band_26_40":0.45,"band_41_60":0.35,"band_60_plus":0.05}',
    ARRAY['BPHS ch.10','Phaladeepika ch.10'],
    '1.0'),

  ('career_change', 'Career Change', 'career', 'career',
    '{"houses":["10","3","9"],"lords":["10L"],"karakas":["Rahu"],"vargas":["D10"],"dasha_rules":"dasha-sandhi; parivartana periods","transit_triggers":"Rahu transit to 10th"}',
    'moderate',
    '["career_entry","transition"]',
    '{"band_0_12":0.00,"band_13_25":0.20,"band_26_40":0.45,"band_41_60":0.30,"band_60_plus":0.05}',
    ARRAY['BPHS ch.10','standard Rahu transit rules'],
    '1.0'),

  ('career_setback', 'Career Setback', 'career', 'career',
    '{"houses":["10","6","8","12"],"lords":["10L afflicted"],"karakas":["Saturn","Rahu"],"vargas":["D10"],"dasha_rules":"adverse 6/8/12 dasha","transit_triggers":"adverse Saturn transit to 10th"}',
    'significant',
    '["career_change"]',
    '{"band_0_12":0.00,"band_13_25":0.10,"band_26_40":0.35,"band_41_60":0.35,"band_60_plus":0.15}',
    ARRAY['BPHS dusthana chapter'],
    '1.0'),

  ('business_launch', 'Business Launch', 'career', 'career',
    '{"houses":["7","10","11"],"lords":["7L","10L","11L"],"karakas":["Mercury","Jupiter"],"vargas":["D10"],"dasha_rules":"strong 7/10/11 dasha","transit_triggers":"Jupiter to 10th or 11th"}',
    'significant',
    '["career_entry"]',
    '{"band_0_12":0.00,"band_13_25":0.15,"band_26_40":0.50,"band_41_60":0.30,"band_60_plus":0.05}',
    ARRAY['BPHS ch.7,10,11'],
    '1.0'),

  ('education_milestone', 'Education Milestone', 'education', 'education',
    '{"houses":["4","5","9"],"lords":["4L","5L","9L"],"karakas":["Mercury","Jupiter"],"vargas":["D24"],"dasha_rules":"benefic 4/5/9 dasha","transit_triggers":"Jupiter transit to 5th or 9th"}',
    'moderate',
    '[]',
    '{"band_0_12":0.10,"band_13_25":0.70,"band_26_40":0.25,"band_41_60":0.05,"band_60_plus":0.01}',
    ARRAY['BPHS ch.4,5,9','Jaimini Sutram (vidya-karaka)'],
    '1.0'),

  ('exam_outcome', 'Exam Outcome', 'education', 'education',
    '{"houses":["5","9"],"lords":["5L"],"karakas":["Mercury"],"vargas":["D24"],"dasha_rules":"5th lord period","transit_triggers":"transit to 5th"}',
    'trivial',
    '["education_milestone"]',
    '{"band_0_12":0.15,"band_13_25":0.75,"band_26_40":0.20,"band_41_60":0.03,"band_60_plus":0.01}',
    ARRAY['BPHS ch.5'],
    '1.0'),

  ('marriage', 'Marriage', 'relationship', 'relationship',
    '{"houses":["7","2"],"lords":["7L"],"karakas":["Venus"],"vargas":["D9"],"dasha_rules":"7th-lord or Venus dasha/antardasha","transit_triggers":"Jupiter/Saturn transit to 7th; Jaimini DK activation"}',
    'significant',
    '["partnership_formed"]',
    '{"band_0_12":0.00,"band_13_25":0.45,"band_26_40":0.45,"band_41_60":0.10,"band_60_plus":0.02}',
    ARRAY['BPHS ch.7 (vivaha)','Phaladeepika kalatra-bhava','Jaimini Sutram DK'],
    '1.0'),

  ('romantic_start', 'Romantic Relationship Start', 'relationship', 'relationship',
    '{"houses":["5","7"],"lords":["5L","7L"],"karakas":["Venus"],"vargas":["D9"],"dasha_rules":"Venus/5th-lord period","transit_triggers":"benefic transit to 5th or 7th"}',
    'moderate',
    '["marriage"]',
    '{"band_0_12":0.05,"band_13_25":0.55,"band_26_40":0.35,"band_41_60":0.10,"band_60_plus":0.02}',
    ARRAY['BPHS ch.5,7'],
    '1.0'),

  ('separation', 'Separation', 'relationship', 'relationship',
    '{"houses":["6","8","12"],"lords":["7L afflicted"],"karakas":["Rahu","Saturn","Mars"],"vargas":["D9"],"dasha_rules":"adverse dasha for 7th","transit_triggers":"adverse Saturn/Rahu transit to 7th"}',
    'significant',
    '["marriage"]',
    '{"band_0_12":0.00,"band_13_25":0.15,"band_26_40":0.40,"band_41_60":0.30,"band_60_plus":0.10}',
    ARRAY['BPHS ch.7 (vivaha-vighna)'],
    '1.0'),

  ('childbirth', 'Childbirth', 'progeny', 'family',
    '{"houses":["5","1"],"lords":["5L"],"karakas":["Jupiter"],"vargas":["D7"],"dasha_rules":"5th-lord or Jupiter dasha","transit_triggers":"Jupiter transit to 5th"}',
    'significant',
    '[]',
    '{"band_0_12":0.00,"band_13_25":0.30,"band_26_40":0.60,"band_41_60":0.08,"band_60_plus":0.00}',
    ARRAY['BPHS ch.5 (putra-bhava)','Jaimini Sutram putra-karaka'],
    '1.0'),

  ('parental_event', 'Parental Event', 'family', 'family',
    '{"houses":["4","9"],"lords":["4L","9L"],"karakas":["Moon","Sun"],"vargas":["D12"],"dasha_rules":"4th/9th lord dasha","transit_triggers":"Saturn/Ketu transit to 4th or 9th"}',
    'moderate',
    '["bereavement"]',
    '{"band_0_12":0.05,"band_13_25":0.20,"band_26_40":0.35,"band_41_60":0.35,"band_60_plus":0.20}',
    ARRAY['BPHS ch.4 (matru-bhava), ch.9 (pitru-bhava)'],
    '1.0'),

  ('bereavement', 'Bereavement', 'transition', 'loss',
    '{"houses":["8","12","2"],"lords":["8L","maraka lords (2L/7L)"],"karakas":["Saturn","Ketu"],"vargas":["D8"],"dasha_rules":"maraka dasha","transit_triggers":"adverse Saturn/Ketu transit to 1st or 8th"}',
    'significant',
    '["parental_event"]',
    '{"band_0_12":0.05,"band_13_25":0.15,"band_26_40":0.30,"band_41_60":0.30,"band_60_plus":0.30}',
    ARRAY['BPHS ch.8,2 (maraka/nidhan)'],
    '1.0'),

  ('major_gain', 'Major Financial Gain', 'wealth', 'finance',
    '{"houses":["2","11"],"lords":["2L","11L"],"karakas":["Jupiter","Mercury"],"vargas":["D2"],"dasha_rules":"dhana-yoga dasha","transit_triggers":"Jupiter transit to 2nd or 11th"}',
    'moderate',
    '["property_acquisition"]',
    '{"band_0_12":0.00,"band_13_25":0.20,"band_26_40":0.40,"band_41_60":0.30,"band_60_plus":0.10}',
    ARRAY['BPHS ch.2,11 (dhana-bhava)'],
    '1.0'),

  ('major_loss', 'Major Financial Loss', 'wealth', 'loss',
    '{"houses":["2","11","12"],"lords":["2L/11L afflicted","12L active"],"karakas":["Saturn","Rahu"],"vargas":["D2"],"dasha_rules":"adverse dasha for 2nd","transit_triggers":"adverse Saturn/Rahu transit to 2nd"}',
    'significant',
    '["career_setback"]',
    '{"band_0_12":0.00,"band_13_25":0.15,"band_26_40":0.40,"band_41_60":0.30,"band_60_plus":0.15}',
    ARRAY['BPHS ch.12 (vyaya)'],
    '1.0'),

  ('property_acquisition', 'Property Acquisition', 'residence', 'finance',
    '{"houses":["4"],"lords":["4L"],"karakas":["Mars"],"vargas":["D4"],"dasha_rules":"4th-lord dasha","transit_triggers":"benefic transit to 4th"}',
    'moderate',
    '["major_gain","relocation"]',
    '{"band_0_12":0.00,"band_13_25":0.15,"band_26_40":0.50,"band_41_60":0.30,"band_60_plus":0.05}',
    ARRAY['BPHS ch.4 (bhumi-bhava)'],
    '1.0'),

  ('relocation', 'Relocation', 'residence', 'residential',
    '{"houses":["4","3","12"],"lords":["4L","3L"],"karakas":["Moon","Rahu"],"vargas":["D4"],"dasha_rules":"dasha-change or 4L in transit to dusthana","transit_triggers":"Rahu transit to 4th or 12th"}',
    'moderate',
    '["property_acquisition","foreign_settlement"]',
    '{"band_0_12":0.05,"band_13_25":0.30,"band_26_40":0.40,"band_41_60":0.20,"band_60_plus":0.05}',
    ARRAY['BPHS ch.4,12'],
    '1.0'),

  ('foreign_settlement', 'Foreign Settlement', 'travel', 'travel',
    '{"houses":["12","9","7"],"lords":["12L","9L"],"karakas":["Rahu"],"vargas":["D9","D12"],"dasha_rules":"Rahu dasha; 12L period","transit_triggers":"Rahu transit to 9th or 12th"}',
    'significant',
    '["relocation"]',
    '{"band_0_12":0.00,"band_13_25":0.35,"band_26_40":0.45,"band_41_60":0.15,"band_60_plus":0.02}',
    ARRAY['BPHS ch.12 (videsh)'],
    '1.0'),

  ('illness_acute', 'Acute Illness', 'health', 'health',
    '{"houses":["6","8"],"lords":["6L","8L"],"karakas":["Mars","Saturn"],"vargas":["D30"],"dasha_rules":"adverse transit to lagna or 6th","transit_triggers":"Mars/Saturn adverse transit to 6th or 1st"}',
    'moderate',
    '["surgery","chronic_onset"]',
    '{"band_0_12":0.15,"band_13_25":0.20,"band_26_40":0.25,"band_41_60":0.30,"band_60_plus":0.40}',
    ARRAY['BPHS ch.6 (roga-bhava)','Phaladeepika ch.6'],
    '1.0'),

  ('chronic_onset', 'Chronic Illness Onset', 'health', 'health',
    '{"houses":["6","8"],"lords":["6L","8L"],"karakas":["Saturn"],"vargas":["D30"],"dasha_rules":"Sade-Sati; Saturn dasha","transit_triggers":"Saturn transit to 1st, 4th, or 8th"}',
    'significant',
    '["illness_acute"]',
    '{"band_0_12":0.02,"band_13_25":0.08,"band_26_40":0.20,"band_41_60":0.35,"band_60_plus":0.45}',
    ARRAY['BPHS ch.6,8; Sade-Sati rules'],
    '1.0'),

  ('surgery', 'Surgery', 'health', 'health',
    '{"houses":["6","8"],"lords":["6L","8L"],"karakas":["Mars"],"vargas":["D30"],"dasha_rules":"Mars/Ketu dasha-transit","transit_triggers":"Mars transit to 6th or 8th with simultaneous Ketu aspect"}',
    'significant',
    '["illness_acute"]',
    '{"band_0_12":0.05,"band_13_25":0.10,"band_26_40":0.20,"band_41_60":0.30,"band_60_plus":0.35}',
    ARRAY['BPHS ch.6 (shastra-vrana)','Phaladeepika on Mars aspects'],
    '1.0'),

  ('spiritual_turn', 'Spiritual Turn', 'spirituality', 'spiritual',
    '{"houses":["9","12","5"],"lords":["9L","12L"],"karakas":["Jupiter","Ketu"],"vargas":["D20"],"dasha_rules":"Ketu or Jupiter dasha","transit_triggers":"Jupiter transit to 9th or 12th"}',
    'moderate',
    '["transition"]',
    '{"band_0_12":0.00,"band_13_25":0.15,"band_26_40":0.25,"band_41_60":0.35,"band_60_plus":0.45}',
    ARRAY['BPHS ch.9 (dharma), ch.12 (moksha)','Jaimini Sutram moksha-karaka'],
    '1.0')

ON CONFLICT (event_class_id)
DO UPDATE SET
    signature_model  = EXCLUDED.signature_model,
    magnitude_floor  = EXCLUDED.magnitude_floor,
    adjacency        = EXCLUDED.adjacency,
    base_rate_by_age = EXCLUDED.base_rate_by_age,
    citations        = EXCLUDED.citations;

-- ── DDL: brahma_activity_ontology ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahma_activity_ontology (
    activity_class_id   TEXT        PRIMARY KEY,
    name_en             TEXT        NOT NULL,
    significators       JSONB       NOT NULL,
    fructification_rules JSONB      NOT NULL,
    related_event_class TEXT        REFERENCES brahma_event_ontology(event_class_id),
    citations           TEXT[],
    version             TEXT        NOT NULL DEFAULT '1.0',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE brahma_activity_ontology IS
  'BA-P3A: Electional (muhurta) activity ontology — 12 activity classes. '
  'Seeded from W1 seed package §6. Governs L4 ph_muhurta generator. '
  'significators: {strengthen_grahas, strengthen_houses, strengthen_varga, avoid}. '
  'fructification_rules: {timing_anchor, panchanga_rules, classical_source}.';

-- ── SEED: brahma_activity_ontology (12 classes) ───────────────────────────────

INSERT INTO brahma_activity_ontology
  (activity_class_id, name_en, significators, fructification_rules, related_event_class, citations, version)
VALUES
  ('marriage', 'Marriage',
    '{"strengthen_grahas":["Venus","Jupiter"],"strengthen_houses":["7"],"strengthen_varga":"D9","avoid":["6th/8th/12th afflicting 7th","Bhadra tithi","Venus/Jupiter combust"]}',
    '{"timing_anchor":"tara+candra-bala","panchanga_rules":"Venus and Jupiter dignified; avoid Ritu-sandhya","classical_source":"Muhurta-Chintamani ch.4"}',
    'marriage',
    ARRAY['Muhurta-Chintamani ch.4','BPHS muhurta chapter'],
    '1.0'),

  ('business_start', 'Business Start',
    '{"strengthen_grahas":["Mercury","Jupiter","Sun"],"strengthen_houses":["10","11"],"strengthen_varga":"D10","avoid":["8th lord hora","Rahu-kala","weak 10L"]}',
    '{"timing_anchor":"strong lagna+10th at election","panchanga_rules":"waxing Moon; avoid Krishna-paksha","classical_source":"Muhurta-Chintamani ch.7"}',
    'business_launch',
    ARRAY['Muhurta-Chintamani ch.7'],
    '1.0'),

  ('contract_signing', 'Contract Signing',
    '{"strengthen_grahas":["Mercury"],"strengthen_houses":["3","11"],"strengthen_varga":"D1","avoid":["Mercury combust/retrograde","void Moon"]}',
    '{"timing_anchor":"Mercury dignified; waxing Moon","panchanga_rules":"avoid Panchami/Saptami (vyatipata)","classical_source":"standard Jyotish muhurta texts"}',
    NULL,
    ARRAY['Standard muhurta texts'],
    '1.0'),

  ('travel_journey', 'Travel Journey',
    '{"strengthen_grahas":["Moon","Mercury"],"strengthen_houses":["3","9","12"],"strengthen_varga":"D1","avoid":["durmuhurta","Moon in 8th from janma-rashi"]}',
    '{"timing_anchor":"favorable candra-bala; disha-shul clear","panchanga_rules":"Moon in 3/6/10/11 from birth Moon; avoid Bharani/Krittika/Ashlesha on travel day","classical_source":"Muhurta-Chintamani ch.8"}',
    'relocation',
    ARRAY['Muhurta-Chintamani ch.8'],
    '1.0'),

  ('property_purchase', 'Property Purchase',
    '{"strengthen_grahas":["Mars","Saturn"],"strengthen_houses":["4"],"strengthen_varga":"D4","avoid":["4L weak","adverse Saturn transit","Mangal in 4th from lagna"]}',
    '{"timing_anchor":"4th lord strong; Mars dignified","panchanga_rules":"avoid Shraddha-paksha; avoid Krishna-8th","classical_source":"Muhurta-Chintamani ch.10"}',
    'property_acquisition',
    ARRAY['Muhurta-Chintamani ch.10'],
    '1.0'),

  ('medical_procedure', 'Medical Procedure',
    '{"strengthen_grahas":["controlled Mars"],"strengthen_houses":["6","8"],"strengthen_varga":"D30","avoid":["Krishna-chaturdashi","afflicted lagna","Moon in surgery-site rashi"]}',
    '{"timing_anchor":"benefic lagna; Moon away from affected body part","panchanga_rules":"avoid Bharani/Krittika/Moola nakshatra for elective surgery","classical_source":"BPHS muhurta + surgical nakshatra rules"}',
    'surgery',
    ARRAY['BPHS muhurta','surgical nakshatra rules'],
    '1.0'),

  ('education_start', 'Education Start',
    '{"strengthen_grahas":["Mercury","Jupiter"],"strengthen_houses":["4","5"],"strengthen_varga":"D24","avoid":["Mercury combust","weak 5L"]}',
    '{"timing_anchor":"Vasanta-panchami-type windows; dignified Mercury/Jupiter","panchanga_rules":"Pushya/Hasta/Ashwini nakshatra favored","classical_source":"standard Vidyarambha muhurta"}',
    'education_milestone',
    ARRAY['Vidyarambha muhurta tradition'],
    '1.0'),

  ('spiritual_initiation', 'Spiritual Initiation',
    '{"strengthen_grahas":["Jupiter","Ketu"],"strengthen_houses":["9","12"],"strengthen_varga":"D20","avoid":["broadly permissive"]}',
    '{"timing_anchor":"Jupiter/Moon strong; auspicious tithi/nakshatra","panchanga_rules":"Ekadashi/Purnima/auspicious solar ingress","classical_source":"Diksha-vidhi tradition"}',
    'spiritual_turn',
    ARRAY['Diksha-vidhi tradition','BPHS ch.9'],
    '1.0'),

  ('vehicle_purchase', 'Vehicle Purchase',
    '{"strengthen_grahas":["Venus"],"strengthen_houses":["4"],"strengthen_varga":"D4","avoid":["Venus combust","4L weak"]}',
    '{"timing_anchor":"Venus dignified; benefic Moon","panchanga_rules":"avoid Rahu-kala; Rohini/Mrigashira favored","classical_source":"Muhurta-Chintamani ch.10"}',
    NULL,
    ARRAY['Muhurta-Chintamani ch.10'],
    '1.0'),

  ('financial_investment', 'Financial Investment',
    '{"strengthen_grahas":["Jupiter","Mercury"],"strengthen_houses":["2","11"],"strengthen_varga":"D2","avoid":["8th lord periods","void Moon"]}',
    '{"timing_anchor":"dhana-yoga active; waxing Moon","panchanga_rules":"avoid Panchami/Chaturdashi; Pushya favored","classical_source":"standard dhana muhurta"}',
    'major_gain',
    ARRAY['Standard dhana muhurta tradition'],
    '1.0'),

  ('griha_pravesh', 'Griha Pravesh (Home Entry)',
    '{"strengthen_grahas":["Moon","Jupiter"],"strengthen_houses":["4"],"strengthen_varga":"D4","avoid":["Chaturmasya prohibitions","weak Moon"]}',
    '{"timing_anchor":"classical griha-pravesha nakshatras (Rohini/Hasta/Pushya/Anuradha)","panchanga_rules":"Shukla-paksha; avoid Shunya tithi; benefic lagna","classical_source":"Griha-pravesha-paddhati"}',
    'property_acquisition',
    ARRAY['Griha-pravesha-paddhati','BPHS muhurta'],
    '1.0'),

  ('ceremony_naming', 'Naming Ceremony',
    '{"strengthen_grahas":["Jupiter","Moon"],"strengthen_houses":["5"],"strengthen_varga":"D1","avoid":["durmuhurta","Rikta tithi (4/9/14)"]}',
    '{"timing_anchor":"benefic Moon-nakshatra; Shukla-paksha","panchanga_rules":"Namakarana muhurta: day 10-12 after birth; Pushya/Hasta/Shravana favored","classical_source":"Namakarana-paddhati"}',
    'childbirth',
    ARRAY['Namakarana-paddhati'],
    '1.0')

ON CONFLICT (activity_class_id)
DO UPDATE SET
    significators        = EXCLUDED.significators,
    fructification_rules = EXCLUDED.fructification_rules,
    citations            = EXCLUDED.citations;

-- ── asset_registry row for bg_ghatana ────────────────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active,
    layer_name, layer_index, catalog_status
)
VALUES (
    'bg_ghatana',
    'brahmagyan',
    17,
    'Ghaṭanā-darśanam',
    'Event + Activity Ontology',
    'Life-event ontology (22 classes keyed to LEL categories) + '
    'electional activity ontology (12 muhurta activity classes). '
    'Seeded from W1 seed package §5-§6. Governs L4 ph_nimitta and ph_muhurta.',
    'postgres_table',
    'brahma_event_ontology',
    'SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count',
    'SELECT pg_total_relation_size(''brahma_event_ontology'')',
    NULL,
    'global',
    true,
    'Brahmagyan',
    'L0',
    'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    count_sql           = EXCLUDED.count_sql,
    layer_name          = EXCLUDED.layer_name,
    layer_index         = EXCLUDED.layer_index,
    catalog_status      = EXCLUDED.catalog_status;

UPDATE asset_registry SET has_writer = true WHERE asset_id = 'bg_ghatana';

COMMIT;
