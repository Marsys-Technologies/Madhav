-- migration 554: G9 (SAMPURTI L0e) — brahma_event_ontology signature_model reconciliation
-- ============================================================================
-- Reconciles the 5 DR-13 provisional event classes' signature_model with the
-- ratified KaryatvaMap entries (R21+R22, bo_pratijna_karyatva.py G8).
--
-- Changes per class:
--   1. Remove `provisional: true` and `inherited_from` keys from signature_model.
--   2. Update `citations` array to reflect the ratified classical sources
--      (BPHS + Phaladeepika per B.3; no "inherited — provisional pending" language).
--   3. Houses / karakas / vargas are UNCHANGED — they were already aligned
--      with the ratified KaryatvaMap (no genuine dispute; see G9 conductor note
--      in bo_pratijna_karyatva.py).
--
-- R13: no signature_model change traces to any native's known outcomes.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.
-- Idempotency: signature_model column is JSONB; we replace it via jsonb_set
-- chains; the WHERE clause limits to only the 5 affected rows.

-- ── achievement_recognition ─────────────────────────────────────────────────
UPDATE brahma_event_ontology
SET signature_model = (
    -- Remove provisional/inherited_from; update citations; keep all other keys
    (signature_model
     - 'provisional'
     - 'inherited_from')
    || jsonb_build_object(
        'citations', jsonb_build_array(
            'BPHS ch.16 (putra-bhava: vidya-buddhi-chitta; 5th as the seat of intellect whose public recognition is kirti — fame accrued from works)',
            'BPHS ch.10 (karma-bhava: rajya, pratigya — the public career stage on which recognition lands) + ch.11 (labha-bhava: the fruit of public deeds including title, honour, and prize)',
            'BPHS ch.3 (graha-karakatva: Budha/Mercury = vidya, kala, vakya — the planet whose dasha confers recognition for intellectual and communicative achievement)',
            'BPHS ch.28 (karaka-adhyaya: Ravi/Sun = rajya, mana, kirti — natural significator of public honour, prestige, and recognition by authority)',
            'BPHS ch.6 (varga-prakarana: dashamsha — all karma/career/public-domain events, including their fruits such as award and title, manifest through D10)'
        )
    )
)
WHERE event_class_id = 'achievement_recognition';

-- ── financial_deception ──────────────────────────────────────────────────────
UPDATE brahma_event_ontology
SET signature_model = (
    (signature_model
     - 'provisional'
     - 'inherited_from')
    || jsonb_build_object(
        'citations', jsonb_build_array(
            'BPHS ch.3 (dhana-bhava: the 2nd holds sanchita-dhana — accumulated savings; its affliction by the 12L/8L chain is the classical mechanism for involuntary wealth-destruction through hidden agency)',
            'BPHS ch.11 (labha-bhava: income and anticipated gains; Rahu in or aspecting 11th produces earnings that fail to materialise or are misdirected — labha-nasha through vyajakarana)',
            'BPHS ch.12 (vyaya-bhava: the 12th represents loss through cheating (chhala), hidden enemies, and clandestine activity — dhrohana distinguishes this from ordinary market loss)',
            'BPHS ch.28 (karaka-adhyaya: Rahu = maya, chala, apasavya — the planet of illusion and deception; its involvement converts a financial-loss event from market-driven to fraud-driven)',
            'BPHS ch.12 (dusthana-viveka: the 12th and 8th must be active structural connectors — a deception without 12th/8th involvement is mere market loss, not a classified fraud event)'
        )
    )
)
WHERE event_class_id = 'financial_deception';

-- ── psychological_arc ────────────────────────────────────────────────────────
UPDATE brahma_event_ontology
SET signature_model = (
    (signature_model
     - 'provisional'
     - 'inherited_from')
    || jsonb_build_object(
        'citations', jsonb_build_array(
            'BPHS ch.1 (lagna-bhava: the 1st is the svarupa — temperament, constitution, and manas-shakti; psychological arcs are lagna-centred because they modify the subject''s fundamental self-expression)',
            'BPHS ch.6 (ari-bhava/roga-bhava: the 6th governs roga in all forms including unmada (mental disorder) and vakya-dosha (speech defect); a psychological arc begins when 6L activates against lagna or Moon)',
            'BPHS ch.12 (vyaya-bhava: the 12th governs sayana, bandha, and sukha-nasha — classical descriptors of a psychological crisis period)',
            'BPHS ch.28 (karaka-adhyaya: Chandra/Moon = manas, chitta, manasika-roga — the natural karaka of the mind; its affliction is the primary classical trigger for psychological disturbance)',
            'BPHS ch.28 (karaka-adhyaya: Budha/Mercury = buddhi, vakya, smriti — karaka of cognitive function and speech; distinguishes speech-pattern/cognitive dimension from purely emotional Moon-affliction)',
            'BPHS ch.28 (karaka-adhyaya: Shani/Saturn = ayus, roga-sthiti — governs chronic disease; its involvement converts an acute episode into a long-duration psychological arc)',
            'BPHS ch.6 (varga-prakarana: D1/rashi chart — the fundamental chart is the appropriate varga for psychological arcs; manasika conditions read from D1 Moon/lagna configurations)'
        )
    )
)
WHERE event_class_id = 'psychological_arc';

-- ── birth_anchor ──────────────────────────────────────────────────────────────
UPDATE brahma_event_ontology
SET signature_model = (
    (signature_model
     - 'provisional'
     - 'inherited_from')
    || jsonb_build_object(
        'citations', jsonb_build_array(
            'BPHS ch.1 (lagna-bhava: the 1st bhava IS the birth moment — the rising sign at the first breath is the definitional anchor of the natal chart; this class marks that epoch, not a predicted event)',
            'BPHS ch.28 (karaka-adhyaya: Ravi/Sun = atma, jiva, bala — natural significator of the self, life-force, and vitality; the Sun''s placement at birth defines the chart''s fundamental strength axis)',
            'BPHS ch.1 (lagna-pida: Saturn and Rahu in the 12th and 2nd from lagna form papakartari yoga — the condition axis assesses lagna affliction quality, not the prediction of birth itself)'
        )
    )
)
WHERE event_class_id = 'birth_anchor';

-- ── travel_event ─────────────────────────────────────────────────────────────
UPDATE brahma_event_ontology
SET signature_model = (
    (signature_model
     - 'provisional'
     - 'inherited_from')
    || jsonb_build_object(
        'citations', jsonb_build_array(
            'BPHS ch.3 (parakrama-bhava: the 3rd governs parakrama and yatra to nearby/domestic destinations; primary bhava for a discrete short or medium trip as distinct from durable residence change)',
            'BPHS ch.9 (dharma/bhagya-bhava: the 9th governs tirthayyatra, desha-antara, and pravasa; Jupiter-activated 9th confers auspicious foreign travel; Rahu-activated 9th produces sudden overseas journeys)',
            'BPHS ch.12 (vyaya-bhava: the 12th is the bhava of expenditure in distant lands and sayanasthana — activated during any non-local journey involving lodging away from home)',
            'BPHS ch.28 (karaka-adhyaya: Chandra/Moon = chara (movable), natural significator of journeys and change of place; the Moon alone governs discrete trips; Rahu governs foreign-residency-specific uprooting)',
            'BPHS ch.6 (varga-prakarana: D1/rashi chart — a discrete trip is a D1 event; unlike foreign_settlement which involves D9/D12 soul-level relocation, travel_event manifests in the rashi chart)'
        )
    )
)
WHERE event_class_id = 'travel_event';
