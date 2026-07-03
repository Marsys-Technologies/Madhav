-- Migration 401: bg_transit_moorti — BA-P7A AV-transit moorti determinations
-- Adds nakshatra-offset → moorti quality table consumed by ka_gochara transit scoring.
-- Source: Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28 §nakshatra-gochara.
-- 27 rows: count transit nakshatra from natal janma nakshatra (offset 1..27).
-- Moorti cycle: Swarna(1,5,9,13,17,21,25) · Rajata(2,6,10,14,18,22,26)
--              Tamra(3,7,11,15,19,23,27) · Loha(4,8,12,16,20,24).

BEGIN;

CREATE TABLE IF NOT EXISTS bg_transit_moorti (
    nakshatra_offset    INTEGER     PRIMARY KEY
                        CHECK (nakshatra_offset BETWEEN 1 AND 27),
    moorti_name         TEXT        NOT NULL
                        CHECK (moorti_name IN ('swarna', 'rajata', 'tamra', 'loha')),
    quality_tier        INTEGER     NOT NULL
                        CHECK (quality_tier BETWEEN 1 AND 4),
    phala_brief         TEXT        NOT NULL,
    classical_citation  TEXT        NOT NULL,
    rule_notes          TEXT
);

COMMENT ON TABLE bg_transit_moorti IS
  'BA-P7A: Moorti Nirnaya — transit nakshatra moorti quality lookup. '
  'Count the transit nakshatra from natal janma nakshatra (offset 1–27). '
  'ka_gochara reads this table to add moorti_tier to convergence window scoring. '
  'Source: Phaladeepika Ch.26 moorti-nirnaya; BPHS Ch.28 nakshatra gochara phala.';

CREATE INDEX IF NOT EXISTS idx_bg_transit_moorti_tier ON bg_transit_moorti(quality_tier);

INSERT INTO bg_transit_moorti
    (nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation, rule_notes)
VALUES
-- ── Swarna (gold) moorti — most auspicious ─────────────────────────────────
(1,  'swarna', 1, 'Janma nakshatra itself — full Swarna moorti; all endeavours prosper.',
     'Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28',
     'Offset 1 = transit in birth nakshatra; strongest Swarna position.'),
(5,  'swarna', 1, 'Fifth nakshatra from janma — Swarna moorti; gains and good health.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(9,  'swarna', 1, 'Ninth nakshatra from janma — Swarna moorti; dharma and fortune favoured.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(13, 'swarna', 1, 'Thirteenth nakshatra from janma — Swarna moorti; auspicious outcomes.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(17, 'swarna', 1, 'Seventeenth nakshatra from janma — Swarna moorti; prosperity and recognition.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(21, 'swarna', 1, 'Twenty-first nakshatra from janma — Swarna moorti; success in enterprises.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(25, 'swarna', 1, 'Twenty-fifth nakshatra from janma — Swarna moorti; gains and blessings.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
-- ── Rajata (silver) moorti — auspicious ───────────────────────────────────
(2,  'rajata', 2, 'Second nakshatra from janma — Rajata moorti; moderate gains and comfort.',
     'Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28',
     NULL),
(6,  'rajata', 2, 'Sixth nakshatra from janma — Rajata moorti; enemies manageable, health fair.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(10, 'rajata', 2, 'Tenth nakshatra from janma — Rajata moorti; career matters advance moderately.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(14, 'rajata', 2, 'Fourteenth nakshatra from janma — Rajata moorti; positive outcomes with effort.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(18, 'rajata', 2, 'Eighteenth nakshatra from janma — Rajata moorti; moderate auspiciousness.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(22, 'rajata', 2, 'Twenty-second nakshatra from janma — Rajata moorti; partial success likely.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(26, 'rajata', 2, 'Twenty-sixth nakshatra from janma — Rajata moorti; gains with moderate delay.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
-- ── Tamra (copper) moorti — mixed/unfavourable ────────────────────────────
(3,  'tamra', 3, 'Third nakshatra from janma — Tamra moorti; mixed results; caution advised.',
     'Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28',
     NULL),
(7,  'tamra', 3, 'Seventh nakshatra from janma — Tamra moorti; relationship and travel caution.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(11, 'tamra', 3, 'Eleventh nakshatra from janma — Tamra moorti; gains delayed or obstructed.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(15, 'tamra', 3, 'Fifteenth nakshatra from janma — Tamra moorti; mixed; health attention needed.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(19, 'tamra', 3, 'Nineteenth nakshatra from janma — Tamra moorti; efforts yield partial results.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(23, 'tamra', 3, 'Twenty-third nakshatra from janma — Tamra moorti; undertakings face friction.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(27, 'tamra', 3, 'Twenty-seventh nakshatra from janma — Tamra moorti; cycle near end; caution.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     'Offset 27 = one full nakshatra cycle before renewal; Tamra quality per classical consensus.'),
-- ── Loha (iron) moorti — inauspicious ────────────────────────────────────
(4,  'loha', 4, 'Fourth nakshatra from janma — Loha moorti; hardship, obstacles, health risk.',
     'Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28',
     NULL),
(8,  'loha', 4, 'Eighth nakshatra from janma — Loha moorti; severe obstruction; avoid new ventures.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(12, 'loha', 4, 'Twelfth nakshatra from janma — Loha moorti; losses and expenditure likely.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(16, 'loha', 4, 'Sixteenth nakshatra from janma — Loha moorti; disputes and health affliction.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(20, 'loha', 4, 'Twentieth nakshatra from janma — Loha moorti; career and domestic troubles.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL),
(24, 'loha', 4, 'Twenty-fourth nakshatra from janma — Loha moorti; inauspicious; delays and loss.',
     'Phaladeepika Ch.26 §moorti-nirnaya',
     NULL)
ON CONFLICT (nakshatra_offset) DO UPDATE SET
    moorti_name        = EXCLUDED.moorti_name,
    quality_tier       = EXCLUDED.quality_tier,
    phala_brief        = EXCLUDED.phala_brief,
    classical_citation = EXCLUDED.classical_citation,
    rule_notes         = EXCLUDED.rule_notes;

COMMIT;
