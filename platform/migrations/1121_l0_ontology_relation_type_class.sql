-- Migration 1121: brahma_ontology — relation_type vocabulary class (7 rows).
-- Created: 2026-09-25
--
-- W-L0-9 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2), executing the
-- §2.4 ruling: the sambandha relation-type vocabulary (aspect, conjunction,
-- exchange, dispositor, nakshatra-link, argalā, virodha) is L0 DATA; detection of
-- a relation in a chart stays L2 code. The class is added to the ontology as
-- seven rows under entity_class='relation_type'.
--
-- Companion code change (same worktree, prerequisite — already landed on
-- l0/nirmana-elevation-20260921): the same seven entities were added to the
-- ontology writer brahmagyan/l0_ontology.py, so the class survives the writer's
-- upsert + scoped-DELETE regime. This migration's values are byte-identical to
-- the writer's; the writer's ON CONFLICT (entity_class, canonical_id) DO UPDATE
-- ... WHERE ROW(...) IS DISTINCT FROM ... makes a later writer run a no-op.
--
-- Citation discipline: rows cite only in-repo grounded sources (BPHS Ch.26/6/32/
-- 27, Jaimini Ch.1, BPHS Ch.28). nakshatra_link has no classical citation
-- anywhere in the repo and cites the governing decision itself; standalone
-- virodha is attested only as virodhargala. See
-- L0_W_L0_9_IDENTITY_UNIQUENESS_DESIGN_PROPOSAL_v1_0.md §4.
--
-- Guard discipline (migration 1075/1120 pattern): refuses if any relation_type
-- row outside the seven declared pairs is present — another session moved on.
-- Drift on one of the seven pairs is converged (not refused) by ON CONFLICT DO
-- UPDATE, matching the writer's own upsert regime. Identical rows are a no-op
-- (safe re-run).
--
-- HELD: authored 2026-09-25 against the unreconciled _migrations_applied ledger
-- (1080–1095 effects live, ledger empty). Apply only after the consolidation
-- session (madhav-65) reconciles the ledger and the strategy session confirms
-- the number. Number 1121 chosen by scanning every origin/* head across BOTH
-- platform/migrations/ (head 1091) and platform/supabase/migrations/ (head
-- 1090): no 1092–1199 exists on any ref; 1120 is this session's W-L0-1 migration.
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

DO $$
BEGIN
  IF to_regclass('brahma_ontology') IS NULL THEN
    RAISE EXCEPTION 'migration 1121 refuses: brahma_ontology does not exist';
  END IF;

  -- Refuse on drift: any pre-existing relation_type row whose content differs
  -- from this migration's declaration means another session moved first.
  IF EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE entity_class = 'relation_type'
      AND (entity_class, canonical_id) NOT IN (
        VALUES
          ('relation_type','aspect'),
          ('relation_type','conjunction'),
          ('relation_type','exchange'),
          ('relation_type','dispositor'),
          ('relation_type','nakshatra_link'),
          ('relation_type','argala'),
          ('relation_type','virodha')
      )
  ) THEN
    RAISE EXCEPTION 'migration 1121 refuses: unexpected relation_type rows present — another session moved on';
  END IF;

  INSERT INTO brahma_ontology
    (entity_class, canonical_id, canonical_name_en, canonical_name_sa,
     synonyms, description, source_citation, created_at)
  VALUES
    ('relation_type', 'aspect', 'Aspect', 'Dṛṣṭi',
     ARRAY['aspect', 'drishti', 'gaze_relation'],
     'Graha''s influence by sight on houses/grahas at given house-distances; universal 7th plus special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10; nodes 5/7/9 per later tradition)',
     'BPHS Ch.26 (Drishti-phala-adhyaya); Jaimini Ch.1 for rashi-drishti',
     now()),
    ('relation_type', 'conjunction', 'Conjunction', 'Yuti',
     ARRAY['conjunction', 'yuti', 'co_presence'],
     'Two or more grahas in one sign; the strongest sambandha grade (orb-weighted)',
     'BPHS Ch.6',
     now()),
    ('relation_type', 'exchange', 'Exchange (Parivartana)', 'Parivartana',
     ARRAY['exchange', 'parivartana', 'mutual_exchange', 'mutual_reception'],
     'Two lords occupying each other''s signs; mutual sign exchange',
     'BPHS Ch.32',
     now()),
    ('relation_type', 'dispositor', 'Dispositor relation', 'Dispositor',
     ARRAY['dispositor', 'sign_lordship', 'dispositor_chain'],
     'A graha''s dispositor is the lord of the sign it occupies; chains terminate at a graha in own sign or a cycle',
     'BPHS Ch.27 (bhava-bala: a house is as strong as its dispositor)',
     now()),
    ('relation_type', 'nakshatra_link', 'Nakshatra link', 'Nakshatra link',
     ARRAY['nakshatra_link', 'nakshatra-link', 'nakshatra_dispositor_link'],
     'Relation through nakshatra lordship: a graha in another''s nakshatra, or exchanged nakshatras',
     'Vocabulary decision MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1 §2.4 — no in-repo classical citation; detection analogue: nakshatra_dispositor_chain (ga_structural_writer.py)',
     now()),
    ('relation_type', 'argala', 'Argala (Intervention)', 'Argalā',
     ARRAY['argala', 'intervention_relation'],
     'Jaimini intervention relation from 2/4/11 (and 5) houses on a sign/graha',
     'Jaimini Ch.1; also attributed BPHS Ch.28 (in-repo sources differ on the 5th)',
     now()),
    ('relation_type', 'virodha', 'Virodha (Obstruction)', 'Virodha',
     ARRAY['virodha', 'obstruction_relation', 'virodhargala_relation'],
     'Obstruction of an argala (virodhargala): counter-intervention from 12/10/3 (and 9)',
     'Jaimini Ch.1 (as virodhargala); BPHS Ch.28 — standalone virodha relation per vocabulary decision §2.4',
     now())
  ON CONFLICT (entity_class, canonical_id) DO UPDATE SET
    canonical_name_en = EXCLUDED.canonical_name_en,
    canonical_name_sa = EXCLUDED.canonical_name_sa,
    synonyms = EXCLUDED.synonyms,
    description = EXCLUDED.description,
    source_citation = EXCLUDED.source_citation
  WHERE ROW(
    brahma_ontology.canonical_name_en,
    brahma_ontology.canonical_name_sa,
    brahma_ontology.synonyms,
    brahma_ontology.description,
    brahma_ontology.source_citation
  ) IS DISTINCT FROM ROW(
    EXCLUDED.canonical_name_en,
    EXCLUDED.canonical_name_sa,
    EXCLUDED.synonyms,
    EXCLUDED.description,
    EXCLUDED.source_citation
  );

  IF (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'relation_type') <> 7 THEN
    RAISE EXCEPTION 'migration 1121 postflight: expected 7 relation_type rows, found %',
      (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'relation_type');
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT canonical_id FROM brahma_ontology WHERE entity_class = 'relation_type'
--   ORDER BY canonical_id;
--   -- expect: argala, aspect, conjunction, dispositor, exchange,
--   --         nakshatra_link, virodha (7 rows)
--
-- DOWN (manual rollback — removes exactly what this migration added; safe only
-- before any L2 consumer begins citing the class):
--   BEGIN;
--   DELETE FROM brahma_ontology WHERE entity_class = 'relation_type';
--   COMMIT;
-- =============================================================================
