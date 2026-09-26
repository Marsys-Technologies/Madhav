-- Migration 1125: brahma_polysemy_registry — declared cross-class polysemy for
-- brahma_ontology canonical_ids, with the corrected W-L0-9 identity detector.
-- Created: 2026-09-26
--
-- W-L0-9 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2), executing the
-- RATIFIED design Option A + Option C of
-- L0_W_L0_9_IDENTITY_UNIQUENESS_DESIGN_PROPOSAL_v1_0.md §3:
--   A — the identity key STAYS composite (entity_class, canonical_id), already
--       enforced by brahma_ontology_canonical_unique (ws2_l0_ontology.sql:26);
--       a consumer resolving on canonical_id alone is the defect.
--   C — the multiply-registered ids are DECLARED here and resolution is
--       fail-closed: "class-qualified citation required; bare resolution of a
--       registered id refuses" (enforced in resolve_entity.ts and
--       brahmagyan/l0_ontology.py resolve() via AmbiguousEntityError).
-- Ratification: standing mandate Ruling 2; native Decision 16 (2026-09-26,
-- NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8 @ l3, commit 090bd9aaa); ADHIKARIN
-- register ADK-0003.
--
-- Seed rows: the 11 measured cross-class pairs (verified live 2026-09-26:
-- 741 rows, 730 distinct canonical_ids) + argala (relation_type x aspect_type,
-- introduced by held migration 1121). family: 'reflection' = one phenomenon
-- registered under two framings (concept/vocabulary vs catalog class);
-- 'true_polysemy' = two real entities sharing a name (kp the dasha system vs
-- the school; phaladeepika the school vs the text; vyatipata the upagraha vs
-- the panchanga yoga).
--
-- Detector correction (Decision 16): the plan's bare-id detector
-- (count(*) - count(DISTINCT canonical_id) = 0) measures bare-id uniqueness,
-- which A+C deliberately does not impose — it would sit at 11 forever. It is
-- replaced here, in bg_ontology's registered integrity contract, by the
-- undeclared-duplicates detector:
--   SELECT canonical_id FROM brahma_ontology GROUP BY canonical_id
--   HAVING count(*) > 1 EXCEPT SELECT canonical_id FROM brahma_polysemy_registry
--   -- must be empty
-- Verified live (read-only, 2026-09-26): the 11 live duplicates are exactly the
-- 11 non-argala seed ids, so the detector passes by construction once applied.
--
-- Guard discipline (migration 606/620/630 pattern): refuses if the registry
-- already holds rows outside the 12 declared ids (another session moved on);
-- drift on a declared row is converged by ON CONFLICT DO UPDATE; the
-- bg_ontology registry row is pinned by the sha256 of its current (migration
-- 606) integrity_check_sql, verified live 2026-09-26.
--
-- HELD: production application is a Part 5 hard stop belonging to the native —
-- authored only, NOT applied (same regime as held 1120–1124). Number 1125
-- chosen by scanning every origin/* head across BOTH platform/migrations/ and
-- platform/supabase/migrations/ plus this branch's held 1120–1124:
--   git log --all --diff-filter=A --name-only --format='' --
--     'platform/migrations/*.sql' 'platform/supabase/migrations/*.sql'
-- highest number on any ref is 1124 (this branch, held); next free is 1125.
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

CREATE TABLE IF NOT EXISTS brahma_polysemy_registry (
  canonical_id     text   PRIMARY KEY,
  entity_classes   text[] NOT NULL,
  family           text   NOT NULL CHECK (family IN ('reflection', 'true_polysemy')),
  resolution_rule  text   NOT NULL,
  registered_on    date   NOT NULL,
  decision_ref     text   NOT NULL
);

COMMENT ON TABLE brahma_polysemy_registry IS
  'Declared cross-class polysemy of brahma_ontology canonical_ids (W-L0-9, Option A+C; '
  'native Decision 16 / mandate Ruling 2 / ADK-0003, 2026-09-26). brahma_ontology identity '
  'is the composite (entity_class, canonical_id); a canonical_id listed here is legally '
  'carried by more than one class. Resolution rule: class-qualified citation required; '
  'bare resolution of a registered id refuses (AmbiguousEntityError in resolve_entity.ts '
  'and brahmagyan/l0_ontology.py resolve()). The identity detector is undeclared '
  'duplicates = 0: ids with rows in more than one class that are NOT registered here.';

DO $$
BEGIN
  -- Refuse on outside drift: a registry row beyond the 12 declared ids means
  -- another session moved first.
  IF EXISTS (
    SELECT 1 FROM brahma_polysemy_registry
    WHERE canonical_id NOT IN (
      'ashtakavarga', 'balarishta', 'daridra', 'dhaiya', 'kemadruma', 'kp',
      'neecha_bhanga_raja_yoga', 'phaladeepika', 'sade_sati', 'sthira_dasha',
      'vyatipata', 'argala'
    )
  ) THEN
    RAISE EXCEPTION 'migration 1125 refuses: unexpected brahma_polysemy_registry rows present — another session moved on';
  END IF;

  INSERT INTO brahma_polysemy_registry
    (canonical_id, entity_classes, family, resolution_rule, registered_on, decision_ref)
  VALUES
    ('ashtakavarga', ARRAY['concept','school'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('balarishta', ARRAY['concept','dosha'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('daridra', ARRAY['dosha','yoga'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('dhaiya', ARRAY['concept','dosha'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('kemadruma', ARRAY['dosha','yoga'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('kp', ARRAY['dasha_system','school'], 'true_polysemy',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('neecha_bhanga_raja_yoga', ARRAY['concept','yoga'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('phaladeepika', ARRAY['school','text'], 'true_polysemy',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('sade_sati', ARRAY['concept','dosha'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('sthira_dasha', ARRAY['concept','dasha_system'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('vyatipata', ARRAY['upagraha','yoga'], 'true_polysemy',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3'),
    ('argala', ARRAY['aspect_type','relation_type'], 'reflection',
     'class-qualified citation required; bare resolution of a registered id refuses',
     DATE '2026-09-26',
     'Native Decision 16 (2026-09-26, NATIVE_DECISIONS_2026-09-25_v1_0.md v1.8, commit 090bd9aaa); mandate Ruling 2; ADK-0003; L0_W_L0_9 design proposal §3 — pair introduced by held migration 1121')
  ON CONFLICT (canonical_id) DO UPDATE SET
    entity_classes = EXCLUDED.entity_classes,
    family = EXCLUDED.family,
    resolution_rule = EXCLUDED.resolution_rule,
    decision_ref = EXCLUDED.decision_ref
  WHERE ROW(
    brahma_polysemy_registry.entity_classes,
    brahma_polysemy_registry.family,
    brahma_polysemy_registry.resolution_rule,
    brahma_polysemy_registry.decision_ref
  ) IS DISTINCT FROM ROW(
    EXCLUDED.entity_classes,
    EXCLUDED.family,
    EXCLUDED.resolution_rule,
    EXCLUDED.decision_ref
  );

  IF (SELECT count(*) FROM brahma_polysemy_registry) <> 12 THEN
    RAISE EXCEPTION 'migration 1125 postflight: expected 12 brahma_polysemy_registry rows, found %',
      (SELECT count(*) FROM brahma_polysemy_registry);
  END IF;
END $$;

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  integrity_sha TEXT;
  ontology_description_old CONSTANT TEXT :=
    'Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms';
  ontology_description_new CONSTANT TEXT :=
    'Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms. '
    'Identity IS the composite (entity_class, canonical_id) — bare canonical_id is NOT unique '
    '(730 distinct over 741 rows, 11 declared cross-class pairs + argala via held 1121, verified '
    'live 2026-09-26; registry: brahma_polysemy_registry). Resolve class-qualified; bare '
    'resolution of a registered id refuses (Decision 16 / mandate Ruling 2 / ADK-0003).';
  ontology_check_v2 CONSTANT TEXT := $check$
SELECT
  (SELECT COUNT(*) >= 737 FROM brahma_ontology)
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'nak_01_ashwini','nak_02_bharani','nak_03_krittika','nak_04_rohini','nak_05_mrigasira',
    'nak_06_ardra','nak_07_punarvasu','nak_08_pushya','nak_09_ashlesha','nak_10_magha',
    'nak_11_purva_phalguni','nak_12_uttara_phalguni','nak_13_hasta','nak_14_chitra',
    'nak_15_swati','nak_16_vishakha','nak_17_anuradha','nak_18_jyeshtha','nak_19_moola',
    'nak_20_purva_ashadha','nak_21_uttara_ashadha','nak_22_shravana','nak_23_dhanishtha',
    'nak_24_shatabhisha','nak_25_purva_bhadrapada','nak_26_uttara_bhadrapada','nak_27_revati'
  ]::text[] FROM brahma_ontology WHERE entity_class='nakshatra')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'aquarius','aries','cancer','capricorn','gemini','leo','libra','pisces','sagittarius','scorpio','taurus','virgo'
  ]::text[] FROM brahma_ontology WHERE entity_class='sign')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'house_01','house_02','house_03','house_04','house_05','house_06',
    'house_07','house_08','house_09','house_10','house_11','house_12'
  ]::text[] FROM brahma_ontology WHERE entity_class='house')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'ascendant','jupiter','ketu','mars','mercury','midheaven','moon','rahu','saturn','sun','venus'
  ]::text[] FROM brahma_ontology WHERE entity_class='planet')
  AND NOT EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE canonical_id IS NULL OR canonical_name_en IS NULL OR entity_class IS NULL OR source_citation IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM brahma_ontology GROUP BY entity_class, canonical_id HAVING COUNT(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT canonical_id FROM brahma_ontology
      GROUP BY canonical_id HAVING COUNT(*) > 1
      EXCEPT
      SELECT canonical_id FROM brahma_polysemy_registry
    ) undeclared_polysemy
  )
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_ontology' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'migration 1125 requires bg_ontology registry row'; END IF;
  integrity_sha := encode(sha256(convert_to(
    COALESCE(registry_row.integrity_check_sql, ''), 'UTF8')), 'hex');
  -- Precondition: the migration-606 contract text (digest verified live
  -- 2026-09-26) with the migration-174 description — or the already-applied
  -- post-state of this migration (idempotent re-run).
  IF (integrity_sha = 'cffc280635242e8eeb5690f92d4ba7b2e2a534abcb585dbedea6625f096982b7'
        AND registry_row.english_description = ontology_description_old) IS NOT TRUE
     AND (registry_row.integrity_check_sql = ontology_check_v2
        AND registry_row.english_description = ontology_description_new) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 1125 refuses unknown bg_ontology registry contract';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = ontology_check_v2,
      english_description = ontology_description_new
  WHERE asset_id = 'bg_ontology';

  IF (SELECT COUNT(*) FROM asset_registry
      WHERE asset_id = 'bg_ontology'
        AND integrity_check_sql = ontology_check_v2
        AND english_description = ontology_description_new) <> 1 THEN
    RAISE EXCEPTION 'migration 1125 failed bg_ontology registry postflight';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT canonical_id, entity_classes, family FROM brahma_polysemy_registry
--   ORDER BY canonical_id;  -- expect: 12 rows (argala … vyatipata)
--   SELECT canonical_id FROM brahma_ontology GROUP BY canonical_id
--   HAVING count(*) > 1 EXCEPT SELECT canonical_id FROM brahma_polysemy_registry;
--   -- expect: empty (the W-L0-9 detector, Decision-16-corrected)
--
-- DOWN (manual rollback — safe only before consumers rely on fail-closed
-- resolution or the corrected contract):
--   BEGIN;
--   -- restore bg_ontology registry row (integrity_check_sql prior text is the
--   -- ontology_check block of migration 606 verbatim, sha256
--   -- cffc280635242e8eeb5690f92d4ba7b2e2a534abcb585dbedea6625f096982b7):
--   UPDATE asset_registry
--   SET english_description = 'Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms',
--       integrity_check_sql = <migration 606 ontology_check text>
--   WHERE asset_id = 'bg_ontology';
--   DROP TABLE brahma_polysemy_registry;
--   COMMIT;
-- =============================================================================
