-- Migration 304: bg_graha_dik — Graha Directional Strength (Dig Bala) Reference Table
-- L0 Brahmagyan static reference. Chart-agnostic. 9-row canonical table.
-- Source: BPHS Ch.27 (Digbala); Saravali Ch.3; Brihat Jataka Ch.2
-- Classical rule: each graha has a 'peak house' where it gains maximum Dig Bala
-- and a corresponding cardinal direction. This is IMMUTABLE reference data.
--
-- Dig Bala peak assignments (BPHS Ch.27, universally attested):
--   Sun  → 10H (South — Agni / fame peak in zenith)
--   Moon → 4H  (North — Water / comfort peak at home)
--   Mars → 10H (South — Agni / action peak at zenith)
--   Mercury → 1H (East — clarity peak at rising)
--   Jupiter → 1H (East — wisdom peak at dawn)
--   Venus  → 4H  (North — comfort/pleasure peak)
--   Saturn → 7H  (West — separation peak at setting)
--   Rahu   → 7H  (West — shadowy, per Tajika/later tradition)
--   Ketu   → 4H  (North — inward, shadowed by controversy; noted as debated)
--
-- Note: Rahu/Ketu Dig Bala is debated; Sun+Mars share 10H, Moon+Venus share 4H,
-- Mercury+Jupiter share 1H per BPHS. The rahu/ketu assignments follow the
-- Tajika school and are flagged accordingly.

CREATE TABLE IF NOT EXISTS bg_graha_dik (
    id              SERIAL PRIMARY KEY,
    graha           TEXT NOT NULL UNIQUE,
    peak_house      SMALLINT NOT NULL CHECK (peak_house BETWEEN 1 AND 12),
    peak_direction  TEXT NOT NULL,
    debility_house  SMALLINT NOT NULL CHECK (debility_house BETWEEN 1 AND 12),
    paired_graha    TEXT,           -- graha sharing the same peak house (per BPHS)
    school_note     TEXT,           -- 'parashari' | 'tajika' | 'debated'
    classical_citation TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE bg_graha_dik IS
'Dig Bala (Directional Strength) reference: graha → peak house + cardinal direction.
 Static L0 chart-agnostic data. Source: BPHS Ch.27; Saravali Ch.3; Brihat Jataka Ch.2.
 Debility house = house opposite to peak (where Dig Bala = 0).';

COMMENT ON COLUMN bg_graha_dik.peak_house IS 'Bhava where graha gains maximum Dig Bala (1=Lagna, 4=Sukha, 7=Kalatra, 10=Karma)';
COMMENT ON COLUMN bg_graha_dik.debility_house IS 'Bhava 180 deg from peak where Dig Bala = 0';
COMMENT ON COLUMN bg_graha_dik.paired_graha IS 'Another graha sharing the same peak house per BPHS Ch.27';
COMMENT ON COLUMN bg_graha_dik.school_note IS 'parashari = canonical BPHS; tajika = Tajika tradition; debated = no consensus';

INSERT INTO bg_graha_dik (graha, peak_house, peak_direction, debility_house, paired_graha, school_note, classical_citation)
VALUES
    ('sun',      10, 'South',  4,  'mars',    'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('moon',      4, 'North',  10, 'venus',   'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('mars',     10, 'South',  4,  'sun',     'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('mercury',   1, 'East',   7,  'jupiter', 'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('jupiter',   1, 'East',   7,  'mercury', 'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('venus',     4, 'North',  10, 'moon',    'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('saturn',    7, 'West',   1,  NULL,      'parashari', 'BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2'),
    ('rahu',      7, 'West',   1,  NULL,      'tajika',    'Tajika Neelakanthi; Phaladeepika (shadowy node mirrors Saturn Dig Bala); debated'),
    ('ketu',      4, 'North',  10, NULL,      'debated',   'Ketu Dig Bala not universally attested; North per some later texts; treat as provisional')
ON CONFLICT (graha) DO NOTHING;
