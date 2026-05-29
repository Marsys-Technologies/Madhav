-- Migration 141: Supplementary Jyotish Chakra Reference Tables
-- Stream C [BUILD-ORCH-STREAM-C-A17-S2]
-- Idempotent: CREATE TABLE IF NOT EXISTS with ON CONFLICT DO NOTHING seeding
-- Covers: Sapta-Shalaka, Kalanala, Kota, and Chandra Kala Nadi (CKN) chakras

-- ---------------------------------------------------------------------------
-- Table 1: l1_sapta_shalaka — 7-spoked wheel for transit muhurta assessment
-- 27 nakshatras (no Abhijit) distributed across 7 shalas (Tara-based)
-- Source: Muhurta Chintamani, Tara Bala chapter
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS l1_sapta_shalaka (
    nakshatra_id       INT  NOT NULL,
    nakshatra_name     TEXT NOT NULL,
    shalaka_number     INT  NOT NULL
                           CHECK (shalaka_number BETWEEN 1 AND 7),
    shalaka_type       TEXT NOT NULL,
    classical_citation TEXT,
    PRIMARY KEY (nakshatra_id)
);

COMMENT ON TABLE l1_sapta_shalaka IS
    'A17-S2 Sapta-Shalaka Chakra: 27 nakshatras distributed across 7 shalas (Tara-based '
    'cycling). Shalaka types: Janma, Sampat, Vipat, Ksheema, Pratyak, Sadhana, Naidhana. '
    'Source: Muhurta Chintamani, Tara Bala. [BUILD-ORCH-STREAM-C-A17-S2]';

-- ---------------------------------------------------------------------------
-- Table 2: l1_kalanala_chakra — timing chakra grouping nakshatras by fire intensity
-- 27 nakshatras (no Abhijit) in 3 groups: auspicious / inauspicious / mixed
-- Source: Jyotish Sara Sangraha, Muhurta Kalanala chapter
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS l1_kalanala_chakra (
    nakshatra_id       INT  NOT NULL,
    nakshatra_name     TEXT NOT NULL,
    kalanala_group     INT  NOT NULL CHECK (kalanala_group BETWEEN 1 AND 3),
    group_effect       TEXT NOT NULL,
    fire_intensity     TEXT NOT NULL
                           CHECK (fire_intensity IN ('mild','moderate','intense')),
    classical_citation TEXT,
    PRIMARY KEY (nakshatra_id)
);

COMMENT ON TABLE l1_kalanala_chakra IS
    'A17-S2 Kalanala Chakra: 27 nakshatras in 3 groups by fire intensity. '
    'Group 1=auspicious/mild, Group 2=inauspicious/intense, Group 3=mixed/moderate. '
    'Source: Jyotish Sara Sangraha, Muhurta Kalanala. [BUILD-ORCH-STREAM-C-A17-S2]';

-- ---------------------------------------------------------------------------
-- Table 3: l1_kota_chakra — fortification chakra for transit protection analysis
-- 28 nakshatras (27 standard + Abhijit id=28) in 3 concentric rings, 4 quadrants
-- Source: Brihat Samhita, Kota Chakra
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS l1_kota_chakra (
    nakshatra_id       INT  NOT NULL,
    nakshatra_name     TEXT NOT NULL,
    ring               TEXT NOT NULL
                           CHECK (ring IN ('swami','madhya','bahya')),
    quadrant           TEXT NOT NULL
                           CHECK (quadrant IN ('north','south','east','west')),
    protection_level   INT  NOT NULL CHECK (protection_level BETWEEN 1 AND 3),
    classical_citation TEXT,
    PRIMARY KEY (nakshatra_id)
);

COMMENT ON TABLE l1_kota_chakra IS
    'A17-S2 Kota Chakra: 28 nakshatras (27 + Abhijit id=28) in 3 concentric rings. '
    'swami=inner/most protected (3), madhya=middle (2), bahya=outer/exposed (1). '
    'Source: Brihat Samhita, Kota Chakra. [BUILD-ORCH-STREAM-C-A17-S2]';

-- ---------------------------------------------------------------------------
-- Table 4: l1_ckn_chakra — Chandra Kala Nadi nakshatra attributes
-- 27 nakshatras (no Abhijit): rishi lord, domain, soul-contract theme, D150 amsa group
-- Source: Chandra Kala Nadi, Saptarishi Nadi tradition
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS l1_ckn_chakra (
    nakshatra_id       INT  NOT NULL,
    nakshatra_name     TEXT NOT NULL,
    rishi_lord         TEXT NOT NULL,
    primary_domain     TEXT NOT NULL,
    soul_theme         TEXT NOT NULL,
    d150_amsa_group    INT,
    classical_citation TEXT,
    PRIMARY KEY (nakshatra_id)
);

COMMENT ON TABLE l1_ckn_chakra IS
    'A17-S2 Chandra Kala Nadi Chakra: 27 nakshatras with rishi lord, primary domain, '
    'soul-contract theme, and D150 Saptarishi amsa group (1-7, cycling Marichi→Kratu→Vasishtha). '
    'Source: Chandra Kala Nadi, Saptarishi Nadi tradition. [BUILD-ORCH-STREAM-C-A17-S2]';
