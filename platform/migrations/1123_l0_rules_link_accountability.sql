-- Migration 1123: L0 link accountability — sutravali_rules.unlinked_reason,
-- replay-verified yoga link correction (17 → 7), remedy corpus source-id
-- normalization, and the tightened bg_rules integrity contract.
-- Created: 2026-09-25
--
-- W-L0-3 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2, "One identity,
-- linked rules"). Two defects repaired here:
--
-- (a) sutravali_rules.yoga_canonical_id carried 17 links, of which 11 are
--     provably false attributions: 6 parijata links extracted from work
--     citations of the form "(Jataka Parijata, ch. 8)" and 5 single-row
--     collisions (particular, raja, sunapha, neecha_bhanga, durudhura) where a
--     common word matched a yoga name. The extraction writer
--     (python-sidecar/brahmagyan/l0_rules.py, same worktree, prerequisite) now
--     suppresses candidates inside citation parentheses, truncates the
--     detection window at sentence boundaries, and always records an
--     unlinked_reason. A deterministic replay of all 36 movable rows (17
--     linked + 19 extraction_pass_log.flagged ambiguous) against the fixed
--     detector produced the backfill below, row by row:
--       - 6 links survive replay (katanidhi ×2, durudhura ×2, sunapha ×1,
--         ubhayachari ×1);
--       - 11 false links killed → no_concept_reference_in_window;
--       - of the 19 ambiguous rows, 7 stay ambiguous_reference, 9 become
--         no_concept_reference_in_window, 2 become reference_not_in_catalog
--         (candidates 'second' and 'khala', neither a catalogued yoga), and
--         1 resolves to a real link (cf36fd63… → sunapha);
--       - final state: 7 links of 3,002 rules. This is a measured coverage
--         number, not a target.
--     The two CHECK constraints make the accounting structural: a linked row
--     must not carry a reason, an unlinked row must carry one, and the reason
--     must be one of the three declared values.
--
-- (b) brahma_remedy_corpus.source_canonical_id drifted from the brahma_ontology
--     text-class identity space (production values measured 2026-09-25:
--     BPHS ×193, Phaladeepika ×11, Tajaka ×3, bphs_jaimini ×1,
--     classical_tradition ×80, of which exactly 1 row carries
--     source_citation = 'Muhurta Chintamani, classical Jyotish muhurta text').
--     Normalized by spelling normalization plus alias entries, not redesign:
--     the writer (l0_remedy_corpus.canonical_source_id) now maps the drift
--     spellings at emission, and brahma_ontology.synonyms gains the observed
--     spellings so both surfaces resolve to one identity. 'bphs_jaimini' →
--     'jaimini_sutram' is an attribution fix (the row's own citation names
--     Jaimini), not an alias. Only the single Muhurta-Chintamani-cited
--     classical_tradition row is reattributed; the other 79 stay as measured.
--     Known writer nuance (flagged, not reattributed): canonical_source_id's
--     alias map fires before the Muhurta-Chintamani citation rule, so the one
--     writer row emitted with source 'BPHS' and the MC citation stays 'bphs'
--     — contradictory provenance in the writer data, recorded for W-L0-5.
--
-- Registry contract: bg_rules.integrity_check_sql (installed by migration
-- 618) is replaced with the tightened contract: yoga link count 17 → 7, an
-- XOR filter pinning (yoga_canonical_id IS NULL) = (unlinked_reason IS NOT
-- NULL), a vocabulary filter on unlinked_reason, and the digest vector
-- extended with unlinked_reason between yoga_canonical_id and
-- dasha_system_id. The old digest is verified BEFORE any change: this
-- migration refuses an unknown starting state rather than repairing around
-- one. The new digest was computed by read-only simulation against production
-- on 2026-09-25 (3,002 rows / 7 linked / 7 ambiguous / 2
-- reference_not_in_catalog / 0 XOR violations).
--
-- Guard discipline (migration 618/1075/1120/1121/1122 pattern): this
-- migration refuses to run if (a) sutravali_rules does not satisfy the 618
-- digest exactly (state A) nor the post-migration digest exactly (state B —
-- safe re-run), (b) any of the 36 backfill rule_ids is absent, (c) the
-- measured remedy-corpus drift counts do not match, (d) the three ontology
-- text rows are absent, or (e) the bg_rules registry row carries an unknown
-- contract. State B makes re-application a verifying no-op; every other
-- deviation raises.
--
-- HELD: authored 2026-09-25 against the unreconciled _migrations_applied
-- ledger (1080–1095 effects live, ledger empty). Apply only after the
-- consolidation session (madhav-65) reconciles the ledger and the strategy
-- session confirms the number. Number 1123 chosen by scanning every origin/*
-- head across BOTH platform/migrations/ (head 1122 — 1120, 1121, 1122 are
-- this session's W-L0-1, W-L0-9 and W-L0-2 migrations) and
-- platform/supabase/migrations/ (head 1090): no 1123 exists on any ref.
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

DO $$
DECLARE
  changed_rows integer := 0;
  has_reason_col boolean;
  observed_digest text;
  old_digest constant text :=
    '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd';
  new_digest constant text :=
    'f1d56d0cebf7ce2ad270ba1145cda20cae4c10f2ec3fb1ea01bc6b999feee098';
  old_contract constant text := $check$
SELECT
  count(*) = 3002
  AND count(DISTINCT rule_id) = 3002
  AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 3002
  AND count(*) FILTER (WHERE confidence < 0.600 OR quality_score < 0.600) = 0
  AND count(*) FILTER (WHERE confidence IS DISTINCT FROM quality_score) = 0
  AND count(*) FILTER (WHERE yoga_canonical_id IS NOT NULL) = 17
  AND count(*) FILTER (WHERE dasha_system_id IS NOT NULL) = 0
  AND count(*) FILTER (WHERE transit_marker IS TRUE) = 25
  AND NOT EXISTS (
    SELECT 1 FROM sutravali_rules AS rule
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.text_id = rule.text_id
    )
       OR (rule.yoga_canonical_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_yoga_catalog AS yoga
         WHERE yoga.canonical_id = rule.yoga_canonical_id
       ))
       OR (rule.dasha_system_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_dasha_systems AS dasha
         WHERE dasha.canonical_id = rule.dasha_system_id
       ))
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,dasha_system_id,transit_marker)::text,
    E'\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') =
    '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd'
FROM sutravali_rules
$check$;
  rules_check constant text := $check$
SELECT
  count(*) = 3002
  AND count(DISTINCT rule_id) = 3002
  AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 3002
  AND count(*) FILTER (WHERE confidence < 0.600 OR quality_score < 0.600) = 0
  AND count(*) FILTER (WHERE confidence IS DISTINCT FROM quality_score) = 0
  AND count(*) FILTER (WHERE yoga_canonical_id IS NOT NULL) = 7
  AND count(*) FILTER (
    WHERE (yoga_canonical_id IS NULL) <> (unlinked_reason IS NOT NULL)) = 0
  AND count(*) FILTER (
    WHERE unlinked_reason IS NOT NULL AND unlinked_reason NOT IN
      ('no_concept_reference_in_window','ambiguous_reference',
       'reference_not_in_catalog')) = 0
  AND count(*) FILTER (WHERE dasha_system_id IS NOT NULL) = 0
  AND count(*) FILTER (WHERE transit_marker IS TRUE) = 25
  AND NOT EXISTS (
    SELECT 1 FROM sutravali_rules AS rule
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.text_id = rule.text_id
    )
       OR (rule.yoga_canonical_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_yoga_catalog AS yoga
         WHERE yoga.canonical_id = rule.yoga_canonical_id
       ))
       OR (rule.dasha_system_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_dasha_systems AS dasha
         WHERE dasha.canonical_id = rule.dasha_system_id
       ))
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)::text,
    E'\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') =
    'f1d56d0cebf7ce2ad270ba1145cda20cae4c10f2ec3fb1ea01bc6b999feee098'
FROM sutravali_rules
$check$;
BEGIN
  -- State detection: the unlinked_reason column exists iff a previous run of
  -- this migration committed. Both states are verified by digest before any
  -- change; anything else refuses.
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'sutravali_rules'
      AND column_name = 'unlinked_reason'
  ) INTO has_reason_col;

  IF NOT has_reason_col THEN
    -- State A (fresh apply): the table must satisfy the 618 pin exactly.
    EXECUTE $exec$
SELECT encode(sha256(convert_to(COALESCE(string_agg(
  jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
    prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
    yoga_canonical_id,dasha_system_id,transit_marker)::text,
  E'\n' ORDER BY rule_id::text COLLATE "C"
),''),'UTF8')),'hex')
FROM sutravali_rules
$exec$ INTO observed_digest;
    IF observed_digest IS DISTINCT FROM old_digest THEN
      RAISE EXCEPTION 'migration 1123 refuses unknown sutravali_rules starting state (digest %, expected %)',
        observed_digest, old_digest;
    END IF;

    ALTER TABLE public.sutravali_rules
      ADD COLUMN IF NOT EXISTS unlinked_reason text;

    -- Replay-verified backfill of the 36 movable rows (17 previously linked +
    -- 19 extraction_pass_log-flagged ambiguous). Each tuple is
    -- (rule_id, final yoga_canonical_id, final unlinked_reason).
    UPDATE sutravali_rules AS rule
    SET yoga_canonical_id = v.final_yoga,
        unlinked_reason = v.final_reason
    FROM (VALUES
      ('06c2785e-beb4-57a8-96de-4fffd65ed99c', NULL, 'ambiguous_reference'),
      ('0d20caf8-c33d-54a2-90d6-9790cc2d2ede', 'katanidhi', NULL),
      ('11041661-1c3e-581f-a3d8-a8954ab142c0', NULL, 'no_concept_reference_in_window'),
      ('1717de42-8638-5a63-ab85-decf304c18f1', NULL, 'no_concept_reference_in_window'),
      ('18d94b9c-ba24-535e-a15d-b3536ec11961', NULL, 'no_concept_reference_in_window'),
      ('231e2146-4355-5815-b625-49765cb2ab4d', NULL, 'no_concept_reference_in_window'),
      ('279ef8e4-c644-54bc-9184-5b38a3e00750', NULL, 'no_concept_reference_in_window'),
      ('2bdd08a1-ec92-59e8-9dd9-1fd88d0df15f', 'durudhura', NULL),
      ('323ca1f7-cc18-5c2b-9d23-8209057e8760', NULL, 'ambiguous_reference'),
      ('3e246a11-6b8a-5576-a6b2-7d993a3baed5', NULL, 'no_concept_reference_in_window'),
      ('4b88b9ce-660c-5390-b2eb-d1b89f5ce11d', NULL, 'no_concept_reference_in_window'),
      ('507743d5-d230-5437-bab0-25b2d05a4a48', NULL, 'ambiguous_reference'),
      ('5ba828bd-c255-519f-98ae-fc3dded5420e', NULL, 'ambiguous_reference'),
      ('5eef209c-5fe7-5381-b7bf-6eca70b19ba6', NULL, 'no_concept_reference_in_window'),
      ('7083157a-c410-5948-86f5-1a3ee599aa94', NULL, 'ambiguous_reference'),
      ('7905eb4d-8285-5f03-8cc1-60cd1e9e2cbb', 'katanidhi', NULL),
      ('7c864547-1a80-5b97-b791-fd2b7ece8591', NULL, 'no_concept_reference_in_window'),
      ('7ede2ed9-ceec-5fe5-910f-242b2face906', NULL, 'no_concept_reference_in_window'),
      ('896aa3e6-a7c2-5fc1-8e99-5531031c2e8c', NULL, 'reference_not_in_catalog'),
      ('8a3a3c17-088a-5b7f-8e3d-06a28a08dae5', 'ubhayachari', NULL),
      ('9b1f56eb-ff3c-581e-b7c9-ffe10b735897', NULL, 'no_concept_reference_in_window'),
      ('a051d0c0-5742-5668-a242-b93f4cdb1394', NULL, 'no_concept_reference_in_window'),
      ('a5d58ce9-5331-5db4-a803-41d9530e45fc', 'sunapha', NULL),
      ('ab652951-edf7-5df9-b4f0-7a1d2efba9f4', NULL, 'no_concept_reference_in_window'),
      ('afee174d-6de3-581d-833d-5ee0d8c37043', 'durudhura', NULL),
      ('b478cab5-b282-5fd0-a798-6c8160f5a2cd', NULL, 'ambiguous_reference'),
      ('c02a76d6-a82a-521c-8e02-a618de09824e', NULL, 'ambiguous_reference'),
      ('cb0680b1-faa2-528e-b136-4d1a4d0c70d8', NULL, 'no_concept_reference_in_window'),
      ('cd76ab0c-ea5a-533d-bc02-2bbe4117a392', NULL, 'no_concept_reference_in_window'),
      ('cf36fd63-ba97-5ead-ad17-de9054fc051f', 'sunapha', NULL),
      ('d20f3f23-fd31-58e8-9b8e-644166269982', NULL, 'no_concept_reference_in_window'),
      ('da42245d-7445-5c9b-a8f7-7cc05a573423', NULL, 'no_concept_reference_in_window'),
      ('eaf960d9-5570-5971-9203-3ec0f5e837c5', NULL, 'no_concept_reference_in_window'),
      ('eb716479-c887-5e7a-a532-1788e13e5066', NULL, 'no_concept_reference_in_window'),
      ('f18e6d6b-60b0-5687-93e4-2ee19c640055', NULL, 'reference_not_in_catalog'),
      ('faecc6eb-f6e1-5dfb-9c79-2930f6d6dae5', NULL, 'no_concept_reference_in_window')
    ) AS v(rule_id, final_yoga, final_reason)
    WHERE rule.rule_id = v.rule_id::uuid;
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 36 THEN
      RAISE EXCEPTION 'migration 1123 expected 36 replay-verified rows, updated %', changed_rows;
    END IF;

    -- Every remaining unlinked row gets its declared reason.
    UPDATE sutravali_rules
    SET unlinked_reason = 'no_concept_reference_in_window'
    WHERE unlinked_reason IS NULL AND yoga_canonical_id IS NULL;
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 2966 THEN
      RAISE EXCEPTION 'migration 1123 expected 2966 bulk-labelled rows, updated %', changed_rows;
    END IF;

    -- Ontology alias entries: the observed drift spellings resolve to the same
    -- text-class identity. Guarded append; absence of the row refuses.
    UPDATE brahma_ontology SET synonyms = synonyms || 'BPHS'::text
    WHERE entity_class = 'text' AND canonical_id = 'bphs'
      AND NOT ('BPHS' = ANY(synonyms));
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 1 THEN
      RAISE EXCEPTION 'migration 1123 expected bphs ontology row, updated %', changed_rows;
    END IF;
    UPDATE brahma_ontology SET synonyms = synonyms || 'Phaladeepika'::text
    WHERE entity_class = 'text' AND canonical_id = 'phaladeepika'
      AND NOT ('Phaladeepika' = ANY(synonyms));
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 1 THEN
      RAISE EXCEPTION 'migration 1123 expected phaladeepika ontology row, updated %', changed_rows;
    END IF;
    UPDATE brahma_ontology SET synonyms = synonyms || 'Tajaka'::text
    WHERE entity_class = 'text' AND canonical_id = 'tajaka_neelakanthi'
      AND NOT ('Tajaka' = ANY(synonyms));
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 1 THEN
      RAISE EXCEPTION 'migration 1123 expected tajaka_neelakanthi ontology row, updated %', changed_rows;
    END IF;

    -- Remedy corpus source-id normalization, measured counts asserted.
    UPDATE brahma_remedy_corpus SET source_canonical_id = 'bphs'
    WHERE source_canonical_id = 'BPHS';
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 193 THEN
      RAISE EXCEPTION 'migration 1123 expected 193 BPHS rows, updated %', changed_rows;
    END IF;
    UPDATE brahma_remedy_corpus SET source_canonical_id = 'phaladeepika'
    WHERE source_canonical_id = 'Phaladeepika';
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 11 THEN
      RAISE EXCEPTION 'migration 1123 expected 11 Phaladeepika rows, updated %', changed_rows;
    END IF;
    UPDATE brahma_remedy_corpus SET source_canonical_id = 'tajaka_neelakanthi'
    WHERE source_canonical_id = 'Tajaka';
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 3 THEN
      RAISE EXCEPTION 'migration 1123 expected 3 Tajaka rows, updated %', changed_rows;
    END IF;
    UPDATE brahma_remedy_corpus SET source_canonical_id = 'jaimini_sutram'
    WHERE source_canonical_id = 'bphs_jaimini';
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 1 THEN
      RAISE EXCEPTION 'migration 1123 expected 1 bphs_jaimini row, updated %', changed_rows;
    END IF;
    UPDATE brahma_remedy_corpus SET source_canonical_id = 'muhurta_chintamani'
    WHERE source_canonical_id = 'classical_tradition'
      AND source_citation = 'Muhurta Chintamani, classical Jyotish muhurta text';
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 1 THEN
      RAISE EXCEPTION 'migration 1123 expected 1 Muhurta Chintamani row, updated %', changed_rows;
    END IF;
  ELSE
    -- State B (re-apply): the table must already satisfy the tightened pin.
    EXECUTE $exec$
SELECT encode(sha256(convert_to(COALESCE(string_agg(
  jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
    prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
    yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)::text,
  E'\n' ORDER BY rule_id::text COLLATE "C"
),''),'UTF8')),'hex')
FROM sutravali_rules
$exec$ INTO observed_digest;
    IF observed_digest IS DISTINCT FROM new_digest THEN
      RAISE EXCEPTION 'migration 1123 refuses drifted post-migration state (digest %, expected %)',
        observed_digest, new_digest;
    END IF;
  END IF;

  -- Structural accountability constraints (idempotent: re-validated on
  -- re-apply; the table conforms in both verified states).
  ALTER TABLE public.sutravali_rules
    DROP CONSTRAINT IF EXISTS sutravali_rules_unlinked_reason_vocab;
  ALTER TABLE public.sutravali_rules
    ADD CONSTRAINT sutravali_rules_unlinked_reason_vocab
    CHECK (unlinked_reason IN ('no_concept_reference_in_window',
                               'ambiguous_reference',
                               'reference_not_in_catalog'));
  ALTER TABLE public.sutravali_rules
    DROP CONSTRAINT IF EXISTS sutravali_rules_unlinked_reason_link_xor;
  ALTER TABLE public.sutravali_rules
    ADD CONSTRAINT sutravali_rules_unlinked_reason_link_xor
    CHECK ((yoga_canonical_id IS NULL) = (unlinked_reason IS NOT NULL));

  -- Postflight, data side (runs in both states).
  EXECUTE $exec$
SELECT encode(sha256(convert_to(COALESCE(string_agg(
  jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
    prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
    yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)::text,
  E'\n' ORDER BY rule_id::text COLLATE "C"
),''),'UTF8')),'hex')
FROM sutravali_rules
$exec$ INTO observed_digest;
  IF observed_digest IS DISTINCT FROM new_digest THEN
    RAISE EXCEPTION 'migration 1123 postflight digest mismatch (%, expected %)',
      observed_digest, new_digest;
  END IF;
  IF EXISTS (
    SELECT 1 FROM brahma_remedy_corpus
    WHERE source_canonical_id IN ('BPHS','Phaladeepika','Tajaka','bphs_jaimini')
  ) THEN
    RAISE EXCEPTION 'migration 1123 postflight: remedy source drift present';
  END IF;
  IF EXISTS (
    SELECT 1 FROM brahma_remedy_corpus
    WHERE source_canonical_id = 'classical_tradition'
      AND source_citation = 'Muhurta Chintamani, classical Jyotish muhurta text'
  ) THEN
    RAISE EXCEPTION 'migration 1123 postflight: Muhurta Chintamani row not reattributed';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE entity_class = 'text' AND canonical_id = 'bphs' AND 'BPHS' = ANY(synonyms)
  ) OR NOT EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE entity_class = 'text' AND canonical_id = 'phaladeepika' AND 'Phaladeepika' = ANY(synonyms)
  ) OR NOT EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE entity_class = 'text' AND canonical_id = 'tajaka_neelakanthi' AND 'Tajaka' = ANY(synonyms)
  ) THEN
    RAISE EXCEPTION 'migration 1123 postflight: ontology alias entries missing';
  END IF;

  -- Registry contract: accept the 618 contract (state A) or this migration's
  -- own (state B); anything else refuses.
  UPDATE asset_registry
  SET integrity_check_sql = rules_check
  WHERE asset_id = 'bg_rules'
    AND target_floor = 3002
    AND integrity_check_sql IN (old_contract, rules_check);
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1123 refuses unknown bg_rules registry contract';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_rules'
      AND target_floor = 3002
      AND integrity_check_sql = rules_check
  ) THEN
    RAISE EXCEPTION 'migration 1123 postflight registry mismatch';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT (integrity_check_sql)::text FROM asset_registry WHERE asset_id = 'bg_rules';
--   -- paste the result as a query; expect: one row, true.
--   SELECT yoga_canonical_id, unlinked_reason FROM sutravali_rules
--   WHERE rule_id IN ('06c2785e-beb4-57a8-96de-4fffd65ed99c',
--     'cf36fd63-ba97-5ead-ad17-de9054fc051f','896aa3e6-a7c2-5fc1-8e99-5531031c2e8c',
--     'f18e6d6b-60b0-5687-93e4-2ee19c640055','3e246a11-6b8a-5576-a6b2-7d993a3baed5');
--   -- expect: (NULL, ambiguous_reference), (sunapha, NULL),
--   --   (NULL, reference_not_in_catalog) ×2, (NULL, no_concept_reference_in_window).
--   SELECT source_canonical_id, count(*) FROM brahma_remedy_corpus
--   GROUP BY 1 ORDER BY 2 DESC;
--   -- expect: bphs ×194 (193 + the writer's own BPHS-cited row already
--   --   normalized at write time), no BPHS/Phaladeepika/Tajaka/bphs_jaimini,
--   --   classical_tradition ×79, muhurta_chintamani ≥ 1.
--   SELECT canonical_id, synonyms FROM brahma_ontology
--   WHERE entity_class = 'text'
--     AND canonical_id IN ('bphs','phaladeepika','tajaka_neelakanthi');
--   -- expect: synonyms carry BPHS / Phaladeepika / Tajaka respectively.
--
-- DOWN (manual rollback — restores exactly the pre-1123 state):
--   BEGIN;
--   -- 1. Restore the 618 registry contract (the old_contract text above).
--   UPDATE asset_registry SET integrity_check_sql = '<618 contract verbatim>'
--   WHERE asset_id = 'bg_rules';
--   -- 2. Restore the 11 killed yoga links and remove the 1 added link.
--   UPDATE sutravali_rules SET yoga_canonical_id = 'parijata' WHERE rule_id IN
--     ('3e246a11-6b8a-5576-a6b2-7d993a3baed5','4b88b9ce-660c-5390-b2eb-d1b89f5ce11d',
--      '5eef209c-5fe7-5381-b7bf-6eca70b19ba6','7c864547-1a80-5b97-b791-fd2b7ece8591',
--      'a051d0c0-5742-5668-a242-b93f4cdb1394','cb0680b1-faa2-528e-b136-4d1a4d0c70d8');
--   UPDATE sutravali_rules SET yoga_canonical_id = 'particular'   WHERE rule_id = '231e2146-4355-5815-b625-49765cb2ab4d';
--   UPDATE sutravali_rules SET yoga_canonical_id = 'raja'         WHERE rule_id = '1717de42-8638-5a63-ab85-decf304c18f1';
--   UPDATE sutravali_rules SET yoga_canonical_id = 'sunapha'      WHERE rule_id = '7ede2ed9-ceec-5fe5-910f-242b2face906';
--   UPDATE sutravali_rules SET yoga_canonical_id = 'neecha_bhanga' WHERE rule_id = '11041661-1c3e-581f-a3d8-a8954ab142c0';
--   UPDATE sutravali_rules SET yoga_canonical_id = 'durudhura'    WHERE rule_id = 'eaf960d9-5570-5971-9203-3ec0f5e837c5';
--   UPDATE sutravali_rules SET yoga_canonical_id = NULL           WHERE rule_id = 'cf36fd63-ba97-5ead-ad17-de9054fc051f';
--   -- 3. Drop the accountability column (constraints drop with it).
--   ALTER TABLE public.sutravali_rules DROP COLUMN unlinked_reason;
--   -- 4. Revert the remedy source ids to their drift spellings.
--   UPDATE brahma_remedy_corpus SET source_canonical_id = 'BPHS'         WHERE source_canonical_id = 'bphs';
--   UPDATE brahma_remedy_corpus SET source_canonical_id = 'Phaladeepika' WHERE source_canonical_id = 'phaladeepika';
--   UPDATE brahma_remedy_corpus SET source_canonical_id = 'Tajaka'       WHERE source_canonical_id = 'tajaka_neelakanthi';
--   UPDATE brahma_remedy_corpus SET source_canonical_id = 'bphs_jaimini' WHERE source_canonical_id = 'jaimini_sutram';
--   UPDATE brahma_remedy_corpus SET source_canonical_id = 'classical_tradition'
--     WHERE source_canonical_id = 'muhurta_chintamani'
--       AND source_citation = 'Muhurta Chintamani, classical Jyotish muhurta text';
--   -- 5. Remove the three ontology alias entries.
--   UPDATE brahma_ontology SET synonyms = array_remove(synonyms, 'BPHS')
--     WHERE entity_class = 'text' AND canonical_id = 'bphs';
--   UPDATE brahma_ontology SET synonyms = array_remove(synonyms, 'Phaladeepika')
--     WHERE entity_class = 'text' AND canonical_id = 'phaladeepika';
--   UPDATE brahma_ontology SET synonyms = array_remove(synonyms, 'Tajaka')
--     WHERE entity_class = 'text' AND canonical_id = 'tajaka_neelakanthi';
--   COMMIT;
--   -- NOTE: DOWN step 4 reverts ALL 'bphs' rows including any written
--   -- post-migration by the fixed writer; run DOWN only immediately after a
--   -- rollback decision, never after new writer output has landed.
-- =============================================================================
