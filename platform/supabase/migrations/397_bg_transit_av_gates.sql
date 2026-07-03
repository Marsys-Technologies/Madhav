-- Migration 397: bg_transit_rules EXT + bg_transit_av_gates — BA-P5A Step 4
-- Extends transit rule layer: AV kakshya/SAV gates + double-transit (Jupiter+Saturn) rules.
-- Transit service reads on demand; no data written at build time.
-- Per BA-P5A brief §Step 4: "AV kakshya/SAV gates + vedha + double-transit rules, cited".

BEGIN;

-- ── 1. bg_transit_av_gates — Ashtakavarga kakshya and SAV strength gates ──────

CREATE TABLE IF NOT EXISTS bg_transit_av_gates (
    id              SERIAL      PRIMARY KEY,
    gate_kind       TEXT        NOT NULL
                    CHECK (gate_kind IN ('kakshya', 'sav_threshold', 'vedha_av')),
    graha           TEXT        NOT NULL,
    house_from_moon INTEGER     NOT NULL CHECK (house_from_moon BETWEEN 1 AND 12),
    kakshya_lord    TEXT,                       -- non-null for gate_kind='kakshya'
    min_av_score    INTEGER,                    -- min AV bindhu to activate (≥ this)
    min_sav_score   INTEGER,                    -- min SAV total to pass gate (e.g. ≥28)
    effect          TEXT        NOT NULL,
    classical_citation TEXT     NOT NULL,
    rule_notes      TEXT
);

COMMENT ON TABLE bg_transit_av_gates IS
  'BA-P5A: Ashtakavarga (AV) kakshya gates and SAV threshold gates for gochara transit. '
  'gate_kind=kakshya: per-graha kakshya sector — transit activates karakatva only when '
  '  in a kakshya contributed by a benefic (kakshya_lord non-null). '
  'gate_kind=sav_threshold: min SAV bindhu for the transit house to qualify. '
  'gate_kind=vedha_av: AV-enhanced vedha — vedha nullified when AV bindhu ≥ min_av_score. '
  'Transit service reads this table on demand to gate convergence window scoring. '
  'Source: BPHS ch.66–68 Ashtakavarga; Phaladeepika ch.26.';

-- Functional unique: COALESCE is not valid in a table UNIQUE constraint; use an expression index.
CREATE UNIQUE INDEX IF NOT EXISTS uq_bg_transit_av_gates
    ON bg_transit_av_gates(gate_kind, graha, house_from_moon, COALESCE(kakshya_lord, ''));

CREATE INDEX IF NOT EXISTS idx_bg_transit_av_graha ON bg_transit_av_gates(graha);
CREATE INDEX IF NOT EXISTS idx_bg_transit_av_gate_kind ON bg_transit_av_gates(gate_kind);

-- ── 2. Extend bg_transit_rules CHECK to allow 'double_transit' rule type ──────
-- Drop and re-add the CHECK so we can add the new type without losing existing data.

ALTER TABLE bg_transit_rules
    DROP CONSTRAINT IF EXISTS bg_transit_rules_rule_type_check;

ALTER TABLE bg_transit_rules
    ADD CONSTRAINT bg_transit_rules_rule_type_check
    CHECK (rule_type IN ('favourable', 'unfavourable', 'vedha', 'double_transit'));

-- ── 3. Double-transit rules (Jupiter+Saturn simultaneous gochara) ──────────────
-- Classical rule: when Jupiter and Saturn both transit favourable houses simultaneously,
-- the combined effect is significantly amplified. Phaladeepika ch.26 §double-gochara.

INSERT INTO bg_transit_rules (rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes)
VALUES
  -- Jupiter-Saturn double transit: auspicious combination houses
  ('double_transit', 'Jupiter', 2,  NULL,
   'Jupiter + Saturn in 2H simultaneously: wealth and stability gains amplified; Dhana yoga catalyst.',
   'Phaladeepika ch.26 §double-gochara; Saravali ch.28',
   'Applies only when BOTH Jupiter and Saturn transit 2H from natal Moon within 30° window.'),
  ('double_transit', 'Jupiter', 5,  NULL,
   'Jupiter + Saturn in 5H: putra karaka + karma lord in progeny house — children-related events, creative fruition.',
   'Phaladeepika ch.26 §double-gochara',
   'Saturn alone in 5H is unfavourable; Jupiter co-presence mitigates and transforms.'),
  ('double_transit', 'Jupiter', 7,  NULL,
   'Jupiter + Saturn in 7H: relationship events crystallise; partnerships formalised or resolved.',
   'Phaladeepika ch.26 §double-gochara; BPHS ch.29',
   NULL),
  ('double_transit', 'Jupiter', 9,  NULL,
   'Jupiter + Saturn in 9H: dharmic milestones; pilgrimage, guru connection, institutional advancement.',
   'Phaladeepika ch.26 §double-gochara',
   'Most auspicious double-transit combination per classical consensus.'),
  ('double_transit', 'Jupiter', 11, NULL,
   'Jupiter + Saturn in 11H: significant gain period — labha amplified by both benefic + discipline.',
   'Phaladeepika ch.26 §double-gochara; Jataka Parijata',
   NULL),
  -- Double transit in challenging houses: dual pressure
  ('double_transit', 'Saturn', 4,  NULL,
   'Jupiter + Saturn in 4H: domestic disruption + karmic pressure; home/vehicle events likely.',
   'Phaladeepika ch.26 §double-gochara',
   'Jupiter mitigates isolation but Saturn delays resolution.'),
  ('double_transit', 'Saturn', 8,  NULL,
   'Jupiter + Saturn in 8H: transformation event; inheritance, hidden matters, health threshold.',
   'Phaladeepika ch.26 §double-gochara; BPHS ch.29 §8H gochara',
   'Rare and intense. Jupiter here expands the 8H matters rather than protecting.')
ON CONFLICT (graha, rule_type, primary_house) DO NOTHING;

-- ── 4. SAV threshold seed rows ────────────────────────────────────────────────
-- Minimum SAV bindhu for a transit house to pass the strength gate.
-- Classical: SAV ≥ 28 = strong; 25–27 = moderate; < 25 = weak (Phaladeepika; BPHS ch.66).

INSERT INTO bg_transit_av_gates (gate_kind, graha, house_from_moon, min_sav_score, effect, classical_citation)
VALUES
  ('sav_threshold', 'Saturn',  1, 28, 'SAV ≥28 in 1H: transit potency qualifies; obstruction reduced.', 'BPHS ch.66-68 SAV bindhu thresholds'),
  ('sav_threshold', 'Saturn',  3, 25, 'SAV ≥25 in 3H: moderate potency gate for Saturn transit.', 'BPHS ch.66-68'),
  ('sav_threshold', 'Saturn',  6, 28, 'SAV ≥28 in 6H: favourable Saturn transit potency qualifies.', 'BPHS ch.66-68'),
  ('sav_threshold', 'Saturn', 11, 25, 'SAV ≥25 in 11H: gain-house transit qualifies at moderate threshold.', 'BPHS ch.66-68'),
  ('sav_threshold', 'Jupiter', 2, 28, 'SAV ≥28 in 2H: Jupiter transit wealth-house at full potency.', 'BPHS ch.66-68'),
  ('sav_threshold', 'Jupiter', 5, 28, 'SAV ≥28 in 5H: Jupiter transit progeny/intelligence house qualifies.', 'BPHS ch.66-68'),
  ('sav_threshold', 'Jupiter', 9, 28, 'SAV ≥28 in 9H: dharma house Jupiter transit at full potency.', 'BPHS ch.66-68'),
  ('sav_threshold', 'Jupiter',11, 25, 'SAV ≥25 in 11H: Jupiter in gain house qualifies at moderate threshold.', 'BPHS ch.66-68')
ON CONFLICT DO NOTHING;

COMMIT;
