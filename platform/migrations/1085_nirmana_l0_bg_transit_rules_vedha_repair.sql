-- Migration 1085: bg_transit_rules — G-9 Kṣetra L0 vedha row repair (re-cite,
--                 three Venus vedha_house corrections, missing Mercury pair,
--                 BPHS Ch.29 strike (G-8), six Rāhu/Ketu rows marked
--                 uncited_extension)
-- Created: 2026-09-24
-- Spec: KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md (PR #2725 @ 3b5821bcd), executed as
-- GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §8.4. Every before/after claim in
-- the spec was verified against OCR-independent evidence before writing:
--   * brahmagyan/l0_transit.py::BG_TRANSIT_RULES (the writer's own seed list)
--     carries, by value, the three wrong Venus pairs (3,11) (8,1) (9,2), the
--     five-row Mercury set lacking (8,1), and the six Rāhu/Ketu rows
--     (3,9) (6,12) (11,5) — matching the spec §2/§3/§5 exactly;
--   * Phaladīpikā Adh. XXVI (the passage the spec already cites,
--     phaladeepika:PG322:C1 / PG323:C1) confirms śl.6's Mercury pair (8,1) and
--     śl.8's Venus pairs (3,1) (8,5) (9,11), and gives śl.17's Mercury-8th
--     phala "Gain of wealth and birth of children".
-- Nothing is deleted (spec §2.1: UPDATE, never dedup). The UPDATEs are id- AND
-- value-guarded so they fail to match — loudly, in the verification test — on
-- any database whose rows do not equal the spec's printed before-state.
-- Applied to a disposable docker Postgres only; unapplied to any shared DB.
-- Author: nirmana l3 autonomous gochara run (remainder §8.4, sheet item G-9/G-8).
--
-- =============================================================================

BEGIN;

-- ── 0. uncited_extension flag column (bg_transit_rules has none today; the
--       six nodal rows need it per brief §8.4) ──────────────────────────────
ALTER TABLE bg_transit_rules
    ADD COLUMN IF NOT EXISTS uncited_extension BOOLEAN NOT NULL DEFAULT FALSE;

-- ── 1. §2 — the three Venus rows: UPDATE vedha_house to the text (śl. 8) ────
UPDATE bg_transit_rules
   SET vedha_house = 1
 WHERE id = 35 AND graha = 'venus' AND rule_type = 'favourable'
   AND primary_house = 3 AND vedha_house = 11;

UPDATE bg_transit_rules
   SET vedha_house = 5
 WHERE id = 44 AND graha = 'venus' AND rule_type = 'favourable'
   AND primary_house = 8 AND vedha_house = 1;

UPDATE bg_transit_rules
   SET vedha_house = 11
 WHERE id = 45 AND graha = 'venus' AND rule_type = 'favourable'
   AND primary_house = 9 AND vedha_house = 2;

-- ── 2. §1 — re-cite the 35 favourable+vedha rows of the seven classical
--       grahas to Phaladīpikā Adh. XXVI at page grain (spec §1: verse_ref in
--       this corpus is page-based; a chapter.śloka citation does not resolve).
--       śl. 3 Sun, śl. 4 Moon, śl. 5 Mars/Saturn → PG322:C1;
--       śl. 6 Mercury, śl. 7 Jupiter, śl. 8 Venus → PG323:C1. ───────────────
UPDATE bg_transit_rules
   SET classical_citation = 'Phaladīpikā Adh. XXVI śl. 3 — phaladeepika:PG322:C1'
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha = 'sun'
   AND classical_citation LIKE '%BPHS Ch.29%';

UPDATE bg_transit_rules
   SET classical_citation = 'Phaladīpikā Adh. XXVI śl. 4 — phaladeepika:PG322:C1'
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha = 'moon'
   AND classical_citation LIKE '%BPHS Ch.29%';

UPDATE bg_transit_rules
   SET classical_citation = 'Phaladīpikā Adh. XXVI śl. 5 — phaladeepika:PG322:C1'
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha IN ('mars', 'saturn')
   AND classical_citation LIKE '%BPHS Ch.29%';

UPDATE bg_transit_rules
   SET classical_citation = 'Phaladīpikā Adh. XXVI śl. 6 — phaladeepika:PG323:C1'
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha = 'mercury'
   AND classical_citation LIKE '%BPHS Ch.29%';

UPDATE bg_transit_rules
   SET classical_citation = 'Phaladīpikā Adh. XXVI śl. 7 — phaladeepika:PG323:C1'
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha = 'jupiter'
   AND classical_citation LIKE '%BPHS Ch.29%';

UPDATE bg_transit_rules
   SET classical_citation = 'Phaladīpikā Adh. XXVI śl. 8 — phaladeepika:PG323:C1'
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha = 'venus'
   AND classical_citation LIKE '%BPHS Ch.29%';

-- ── 3. §3 — the missing Mercury pair: transiting the 8th, vedha from the 1st
--       (śl. 6). phala transcribed from the same chapter's Mercury house
--       effects (śl. 17: "8th — gain of wealth and birth of children");
--       rule_notes follows the writer's own convention. ─────────────────────
INSERT INTO bg_transit_rules
    (rule_type, graha, primary_house, vedha_house,
     phala, classical_citation, rule_notes)
VALUES (
    'favourable', 'mercury', 8, 1,
    'Gain of wealth and birth of children',
    'Phaladīpikā Adh. XXVI śl. 6 — phaladeepika:PG323:C1',
    'Vedha from 1st nullifies result'
)
ON CONFLICT (graha, rule_type, primary_house) DO UPDATE SET
    vedha_house        = EXCLUDED.vedha_house,
    phala              = EXCLUDED.phala,
    classical_citation = EXCLUDED.classical_citation,
    rule_notes         = EXCLUDED.rule_notes;

-- ── 4. §5 + G-8 — the six Rāhu/Ketu rows: mark uncited_extension, note the
--       disposition (follows N-14; the L0 owner decides keep-stamped vs
--       remove per spec §5), and strike "BPHS Ch.29" from the four rows that
--       carry it. Nothing deleted. The two (11,5) rows citing "Phaladeepika
--       Ch.26" keep their string — striking it is outside this spec; their
--       unsourced state is carried by uncited_extension + rule_notes. ───────
UPDATE bg_transit_rules
   SET uncited_extension = TRUE,
       rule_notes = COALESCE(rule_notes, '') ||
         ' — uncited_extension: no served text gives house-transit vedha pairs' ||
         ' for the nodes (PG348:C1 is the sarvatobhadra mechanism, not this one);' ||
         ' disposition follows N-14 (L0 owner: keep stamped unsourced or remove).',
       classical_citation = CASE
           WHEN classical_citation LIKE '%BPHS Ch.29%'
           THEN 'unsourced — no served-text house-transit vedha pair set for the nodes (false BPHS citation struck, G-8)'
           ELSE classical_citation
       END
 WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
   AND graha IN ('rahu', 'ketu')
   AND id IN (187, 188, 189, 196, 197, 198)
   AND (primary_house, vedha_house) IN ((3, 9), (6, 12), (11, 5))
   AND uncited_extension = FALSE;

-- ── 5. G-8 sweep — no row may retain the struck "BPHS Ch.29" string after
--       this migration. Any row still carrying it at this point is outside
--       the spec's scope (spec §1 counts exactly 39 in the live database);
--       fail loudly rather than guess a replacement citation. ───────────────
DO $$
DECLARE
    leftover INTEGER;
BEGIN
    SELECT count(*) INTO leftover
      FROM bg_transit_rules
     WHERE classical_citation LIKE '%BPHS Ch.29%';
    IF leftover > 0 THEN
        RAISE EXCEPTION
            'migration 1085: % bg_transit_rules rows still cite BPHS Ch.29 — outside spec scope; resolve before applying',
            leftover;
    END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   -- §4 reverse: restore nodal rows
--   UPDATE bg_transit_rules
--      SET uncited_extension = FALSE,
--          rule_notes = NULLIF(
--              replace(rule_notes,
--                ' — uncited_extension: no served text gives house-transit vedha pairs for the nodes (PG348:C1 is the sarvatobhadra mechanism, not this one); disposition follows N-14 (L0 owner: keep stamped unsourced or remove).',
--                ''),
--              ''),
--          classical_citation = CASE
--              WHEN (primary_house, vedha_house) IN ((3, 9), (6, 12))
--              THEN 'BPHS Ch.29 (Gochara Phala — Transit Results)'
--              ELSE classical_citation
--          END
--    WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
--      AND graha IN ('rahu', 'ketu')
--      AND id IN (187, 188, 189, 196, 197, 198);
--   -- §3 reverse: remove the inserted Mercury pair
--   DELETE FROM bg_transit_rules
--    WHERE rule_type = 'favourable' AND graha = 'mercury'
--      AND primary_house = 8 AND vedha_house = 1
--      AND classical_citation = 'Phaladīpikā Adh. XXVI śl. 6 — phaladeepika:PG323:C1';
--   -- §2 reverse: restore the struck citations on the 35 re-cited rows
--   UPDATE bg_transit_rules
--      SET classical_citation = 'BPHS Ch.29 (Gochara Phala — Transit Results)'
--    WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
--      AND graha IN ('sun','moon','mars','mercury','jupiter','venus','saturn')
--      AND classical_citation LIKE 'Phaladīpikā Adh. XXVI śl. _ — phaladeepika:PG32_:C1';
--   -- §1 reverse: restore the three Venus vedha_house values
--   UPDATE bg_transit_rules SET vedha_house = 11
--    WHERE id = 35 AND graha = 'venus' AND rule_type = 'favourable'
--      AND primary_house = 3 AND vedha_house = 1;
--   UPDATE bg_transit_rules SET vedha_house = 1
--    WHERE id = 44 AND graha = 'venus' AND rule_type = 'favourable'
--      AND primary_house = 8 AND vedha_house = 5;
--   UPDATE bg_transit_rules SET vedha_house = 2
--    WHERE id = 45 AND graha = 'venus' AND rule_type = 'favourable'
--      AND primary_house = 9 AND vedha_house = 11;
--   -- §0 reverse
--   ALTER TABLE bg_transit_rules DROP COLUMN IF EXISTS uncited_extension;
--   COMMIT;
-- =============================================================================
