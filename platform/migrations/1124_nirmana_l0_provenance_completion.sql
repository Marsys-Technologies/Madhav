-- Migration 1124: L0 provenance completion — derived school on the three rule
-- tables, DP §4.3 qualification_state on sutravali_rules, provenance columns on
-- the three vidhi tables, and the bg_vidhi_floors registry description made
-- truthful (migration 642 defect class).
-- Created: 2026-09-25
--
-- W-L0-5 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2, "Provenance
-- completion"). Five repairs, all measured against production on 2026-09-25:
--
-- (a) sutravali_rules: school + qualification_state. Both DERIVED, never
--     authored: school = classical_texts.school of the rule's text_id;
--     qualification_state = 'QUALIFIED_EXECUTABLE' when the text's
--     license_cleared is true AND an exact (text_id, verse_ref) chunk witness
--     exists in classical_text_chunks (the writer extracts rules from those
--     very chunks), 'UNQUALIFIED_SOURCE' when the text is known but not
--     license-cleared, 'READABLE_NOT_EXECUTABLE' (column default) when text_id
--     does not join classical_texts at all. UNSUPPORTED_SCOPE and
--     METHOD_INAPPLICABLE are application-time verdicts about a rule's USE and
--     are deliberately never stored. Production pre-flight measured: 3,002
--     rows, 0 text-join misses, 0 license-cleared misses, 0 chunk-witness
--     misses → all 3,002 backfill to QUALIFIED_EXECUTABLE; school distribution
--     parashari 2,839 / jaimini 112 / nadi 39 / hellenistic 12. Companion
--     writer change (same worktree, prerequisite): l0_rules.py seed_rules
--     derives both fields from a classical_texts load at write time.
--
-- (b) bg_transit_rules.school: derived from classical_citation via a citation
--     → text_id map joined to classical_texts (never hardcoded school). The six
--     'UNSOURCED —' Rahu/Ketu vedha rows (retained per B.10) get NULL — no
--     school is ever guessed. Production pre-flight measured: 76 rows, 70 with
--     a mappable citation (19 BPHS Ch.29, 51 Phaladipika/Phaladeepika variants
--     incl. the §double-gochara composites), 6 UNSOURCED. Companion writer
--     change (prerequisite): l0_transit.py school_for_citation() + the
--     bg_transit_rules upsert writes the derived value.
--
-- (c) bg_parihara_rules.school: derived from brahma_dosha_catalog.school via
--     dosha_canonical_id (the writer already queries that catalog; no new
--     join). Production pre-flight measured: 60 rows, 60 join, 60 parashari.
--     Companion writer change (prerequisite): bg_parihara_rules.py carries
--     school through _DOSHA_QUERY → fetch_parihara_rows → _upsert_parihara.
--
-- (d) vidhi_primitives / vidhi_intent_floors / vidhi_floor_items: two
--     provenance columns. source_authority is constant
--     'src/lib/vidhi/registry_data.ts' (the canonical TS registry both Python
--     writers mirror, parity-gated) and is filled by column DEFAULT.
--     source_ref names the classical/design authority where one exists:
--     primitives — medical_read 'BPHS Ch.18 / Aṣṭāṅga Hṛdayam',
--     sensitive_degree_check 'MC-029 (Śodhana Builder T6)', the eight
--     ṢAḌ-DARŚANA W5 kala primitives 'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'
--     (ahead/elect/explain/now/priority/ritual/story/upaya_read), all others
--     NULL; floors — wealth_deepdive 'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3',
--     career_deepdive 'CR-62 (design §12 lord-placement join)',
--     spirituality_deepdive 'VIDHI-PURNATA P-2 (brief §2 P-2 / §A)',
--     education_deepdive/progeny_deepdive 'VIDHI-PURNATA P-2 (brief §A)', the
--     three W5 routing floors 'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5', the other
--     six NULL. Floor ITEMS inherit their intent's source_ref at write time
--     (declared derivation) and in the backfill below (280 of 409 items, the
--     measured sum over the eight sourced intents: 43+39+35+34+30+33+33+33).
--     Companion writer changes (prerequisite): bg_vidhi_primitives.py /
--     bg_vidhi_floors.py _SOURCE_REFS/_FLOOR_SOURCE_REFS maps + upserts, and
--     dump_vidhi_registry.ts materializes source_ref ?? null so the parity
--     gate compares the new field on both sides.
--
-- (e) bg_vidhi_floors registry description: migration 642's composite text
--     claims "12/14 intent floors are writer-tagged [MANDATORY] (settled)".
--     The writer source (bg_vidhi_floors.py FLOORS, mirrored in
--     registry_data.ts VIDHI_INTENT_FLOORS) carries exactly 1 [MANDATORY]
--     (spirituality_deepdive), 2 [CANDIDATE] (education_deepdive,
--     progeny_deepdive), 11 untagged. This is the migration-1079 defect class
--     (registry description claims a provenance the table/writer does not
--     have); the standing detector for the class lands with this packet in
--     platform/scripts/__tests__/l0_description_truthfulness.test.ts. The
--     update below is pinned to the exact 642 text as pre-state and refuses
--     anything else. asset_registry_seed.ts (same worktree) carries the same
--     truthful text so a reseed cannot reinstall the false claim.
--
-- Guard discipline (migration 618/1075/1120/1123 pattern): this migration
-- refuses to run if (a) sutravali_rules does not satisfy the post-1123 digest
-- exactly (f1d56d0c…, the 1123 digest vector — 1124 adds columns OUTSIDE that
-- vector and never touches it), (b) the 1123 accountability column
-- unlinked_reason is absent (apply order: 1123 first), (c) any measured
-- pre-flight count deviates (3002 / 76 / 60 / 14 / 409 / 60, transit
-- UNSOURCED = 6, parihara dosha-join = 60, licensed-without-witness = 0),
-- or (d) the bg_vidhi_floors description is neither the 642 pre-state nor
-- this migration's own post-state. Re-application is a verifying no-op: DDL
-- is IF NOT EXISTS, backfills are deterministic, and the description guard
-- accepts both states.
--
-- HELD: authored 2026-09-25 against the unreconciled _migrations_applied
-- ledger (1080–1095 effects live, ledger empty). Apply only after the
-- consolidation session (madhav-65) reconciles the ledger and the strategy
-- session confirms the number. Number 1124 chosen by scanning every origin/*
-- head and every local branch across BOTH platform/migrations/ (head 1123 —
-- 1120, 1121, 1122, 1123 are this session's W-L0-1, W-L0-9, W-L0-2 and
-- W-L0-3 migrations) and platform/supabase/migrations/ (head 1090): no 1124
-- exists on any ref.
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

DO $$
DECLARE
  changed_rows integer := 0;
  has_school_col boolean;
  observed_digest text;
  rules_digest constant text :=
    'f1d56d0cebf7ce2ad270ba1145cda20cae4c10f2ec3fb1ea01bc6b999feee098';
  floors_old_description constant text :=
    'Per-intent-class acharya floor + machine band header + ordered floor items -- the compiled scope_tuple->contract input (D-2 Lane V-1). catalog_status=DRAFT is intentional, not stale: 12/14 intent floors are writer-tagged [MANDATORY] (settled), but education_deepdive and progeny_deepdive remain writer-tagged [CANDIDATE] (VIDHI-PURNATA P-2, not yet fully ratified). Re-verify against the writer source before flipping to CURRENT.';
  floors_new_description constant text :=
    'Per-intent-class acharya floor + machine band header + ordered floor items — the compiled scope_tuple->contract input (D-2 Lane V-1). catalog_status=DRAFT is intentional, not stale: per the writer source, 1/14 intent floors is writer-tagged [MANDATORY] (spirituality_deepdive), 2/14 are writer-tagged [CANDIDATE] (education_deepdive, progeny_deepdive — VIDHI-PURNATA P-2, not yet fully ratified), and 11/14 carry no writer tag. Re-verify against the writer source before flipping to CURRENT.';
BEGIN
  -- ── Pre-flight: tables, counts, apply-order dependency ─────────────────────
  IF to_regclass('public.sutravali_rules') IS NULL
     OR to_regclass('public.bg_transit_rules') IS NULL
     OR to_regclass('public.bg_parihara_rules') IS NULL
     OR to_regclass('public.vidhi_primitives') IS NULL
     OR to_regclass('public.vidhi_intent_floors') IS NULL
     OR to_regclass('public.vidhi_floor_items') IS NULL
     OR to_regclass('public.classical_texts') IS NULL
     OR to_regclass('public.classical_text_chunks') IS NULL
     OR to_regclass('public.brahma_dosha_catalog') IS NULL THEN
    RAISE EXCEPTION 'migration 1124 refuses: a required table is absent';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'sutravali_rules'
      AND column_name = 'unlinked_reason'
  ) THEN
    RAISE EXCEPTION 'migration 1124 refuses: sutravali_rules.unlinked_reason absent — apply migration 1123 first';
  END IF;

  IF (SELECT count(*) FROM sutravali_rules) <> 3002
     OR (SELECT count(*) FROM bg_transit_rules) <> 76
     OR (SELECT count(*) FROM bg_parihara_rules) <> 60
     OR (SELECT count(*) FROM vidhi_intent_floors) <> 14
     OR (SELECT count(*) FROM vidhi_floor_items) <> 409
     OR (SELECT count(*) FROM vidhi_primitives) <> 60
     OR (SELECT count(*) FROM bg_transit_rules
         WHERE classical_citation ILIKE 'UNSOURCED%') <> 6
     OR (SELECT count(*) FROM bg_parihara_rules p
         JOIN brahma_dosha_catalog d ON d.canonical_id = p.dosha_canonical_id) <> 60 THEN
    RAISE EXCEPTION 'migration 1124 refuses: a measured pre-flight count deviates from the 2026-09-25 production measurement';
  END IF;

  -- Licensed-but-witnessless is a state the five-state vocabulary cannot name
  -- honestly; refuse rather than force a label.
  IF EXISTS (
    SELECT 1 FROM sutravali_rules r
    JOIN classical_texts t ON t.text_id = r.text_id
    WHERE t.license_cleared IS TRUE
      AND NOT EXISTS (
        SELECT 1 FROM classical_text_chunks c
        WHERE c.text_id = r.text_id AND c.verse_ref = r.verse_ref
      )
  ) THEN
    RAISE EXCEPTION 'migration 1124 refuses: license-cleared rule(s) without a chunk witness exist — investigate before labeling';
  END IF;

  -- The 1123 digest vector (verified before any change, both states — 1124
  -- adds columns outside the vector and never alters it).
  EXECUTE $exec$
SELECT encode(sha256(convert_to(COALESCE(string_agg(
  jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
    prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
    yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)::text,
  E'\n' ORDER BY rule_id::text COLLATE "C"
),''),'UTF8')),'hex')
FROM sutravali_rules
$exec$ INTO observed_digest;
  IF observed_digest IS DISTINCT FROM rules_digest THEN
    RAISE EXCEPTION 'migration 1124 refuses unknown sutravali_rules state (digest %, expected the post-1123 %)',
      observed_digest, rules_digest;
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'sutravali_rules'
      AND column_name = 'school'
  ) INTO has_school_col;

  IF NOT has_school_col THEN
    -- ── DDL (state A only) ───────────────────────────────────────────────────
    ALTER TABLE public.sutravali_rules ADD COLUMN school text;
    ALTER TABLE public.sutravali_rules
      ADD COLUMN qualification_state text NOT NULL DEFAULT 'READABLE_NOT_EXECUTABLE';
    ALTER TABLE public.bg_transit_rules ADD COLUMN school text;
    ALTER TABLE public.bg_parihara_rules ADD COLUMN school text;

    ALTER TABLE public.vidhi_primitives
      ADD COLUMN source_authority text NOT NULL DEFAULT 'src/lib/vidhi/registry_data.ts',
      ADD COLUMN source_ref text;
    ALTER TABLE public.vidhi_intent_floors
      ADD COLUMN source_authority text NOT NULL DEFAULT 'src/lib/vidhi/registry_data.ts',
      ADD COLUMN source_ref text;
    ALTER TABLE public.vidhi_floor_items
      ADD COLUMN source_authority text NOT NULL DEFAULT 'src/lib/vidhi/registry_data.ts',
      ADD COLUMN source_ref text;
  END IF;

  -- ── (a) sutravali_rules backfill (deterministic; safe in both states) ──────
  UPDATE sutravali_rules r
  SET school = t.school,
      qualification_state = CASE
        WHEN t.license_cleared IS TRUE THEN 'QUALIFIED_EXECUTABLE'
        ELSE 'UNQUALIFIED_SOURCE'
      END
  FROM classical_texts t
  WHERE t.text_id = r.text_id;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 3002 THEN
    RAISE EXCEPTION 'migration 1124 expected 3002 rules joined to classical_texts, updated %', changed_rows;
  END IF;

  ALTER TABLE public.sutravali_rules
    DROP CONSTRAINT IF EXISTS sutravali_rules_qualification_state_vocab;
  ALTER TABLE public.sutravali_rules
    ADD CONSTRAINT sutravali_rules_qualification_state_vocab
    CHECK (qualification_state IN ('QUALIFIED_EXECUTABLE',
                                   'UNQUALIFIED_SOURCE',
                                   'READABLE_NOT_EXECUTABLE',
                                   'UNSUPPORTED_SCOPE',
                                   'METHOD_INAPPLICABLE'));

  -- ── (b) bg_transit_rules backfill — citation → text_id → school ───────────
  -- Pattern order is load-bearing: the §double-gochara composites name BPHS /
  -- Saravali / Jataka Parijata secondarily, so the Phaladipika|Phaladeepika
  -- pattern matches first; the UNSOURCED guard excludes the retained Rahu/Ketu
  -- rows (their citation text itself names Phaladipika — the guard must win).
  UPDATE bg_transit_rules r
  SET school = t.school
  FROM classical_texts t
  WHERE r.classical_citation NOT ILIKE 'UNSOURCED%'
    AND t.text_id = CASE
      WHEN r.classical_citation ILIKE '%phalad%' THEN 'phaladeepika'
      WHEN r.classical_citation ILIKE 'BPHS%' THEN 'bphs'
      WHEN r.classical_citation ILIKE '%Saravali%' THEN 'saravali'
      WHEN r.classical_citation ILIKE '%Jataka Parijata%' THEN 'jataka_parijata'
      WHEN r.classical_citation ILIKE '%Uttara Kalamrita%' THEN 'uttara_kalamrita'
    END;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 70 THEN
    RAISE EXCEPTION 'migration 1124 expected 70 transit rules mapped, updated %', changed_rows;
  END IF;

  -- ── (c) bg_parihara_rules backfill — dosha catalog school ─────────────────
  UPDATE bg_parihara_rules p
  SET school = d.school
  FROM brahma_dosha_catalog d
  WHERE d.canonical_id = p.dosha_canonical_id;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 60 THEN
    RAISE EXCEPTION 'migration 1124 expected 60 parihara rules joined, updated %', changed_rows;
  END IF;

  -- ── (d) vidhi provenance backfill ──────────────────────────────────────────
  UPDATE vidhi_primitives p
  SET source_ref = v.source_ref
  FROM (VALUES
    ('medical_read',           'BPHS Ch.18 / Aṣṭāṅga Hṛdayam'),
    ('sensitive_degree_check', 'MC-029 (Śodhana Builder T6)'),
    ('ahead_read',             'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('elect_read',             'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('explain_read',           'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('now_read',               'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('priority_read',          'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('ritual_read',            'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('story_read',             'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('upaya_read',             'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5')
  ) AS v(primitive_id, source_ref)
  WHERE p.primitive_id = v.primitive_id;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 10 THEN
    RAISE EXCEPTION 'migration 1124 expected 10 primitive source_refs, updated %', changed_rows;
  END IF;

  UPDATE vidhi_intent_floors f
  SET source_ref = v.source_ref
  FROM (VALUES
    ('wealth_deepdive',       'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3'),
    ('career_deepdive',       'CR-62 (design §12 lord-placement join)'),
    ('spirituality_deepdive', 'VIDHI-PURNATA P-2 (brief §2 P-2 / §A)'),
    ('education_deepdive',    'VIDHI-PURNATA P-2 (brief §A)'),
    ('progeny_deepdive',      'VIDHI-PURNATA P-2 (brief §A)'),
    ('undertaking_election',  'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('biography_narrative',   'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5'),
    ('ritual_yajna',          'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5')
  ) AS v(intent, source_ref)
  WHERE f.intent = v.intent;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 8 THEN
    RAISE EXCEPTION 'migration 1124 expected 8 floor source_refs, updated %', changed_rows;
  END IF;

  -- Floor items inherit their intent's provenance (declared derivation).
  UPDATE vidhi_floor_items i
  SET source_authority = f.source_authority,
      source_ref = f.source_ref
  FROM vidhi_intent_floors f
  WHERE f.intent = i.intent;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 409 THEN
    RAISE EXCEPTION 'migration 1124 expected 409 floor items inherited, updated %', changed_rows;
  END IF;

  -- ── (e) bg_vidhi_floors description — pinned pre-state swap ────────────────
  UPDATE asset_registry
  SET english_description = floors_new_description
  WHERE asset_id = 'bg_vidhi_floors'
    AND english_description IN (floors_old_description, floors_new_description);
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1124 refuses: bg_vidhi_floors description is neither the 642 pre-state nor this migration''s post-state — moved on by another session';
  END IF;

  -- ── Postflight (both states) ───────────────────────────────────────────────
  IF EXISTS (SELECT 1 FROM sutravali_rules WHERE school IS NULL)
     OR (SELECT count(*) FROM sutravali_rules
         WHERE qualification_state = 'QUALIFIED_EXECUTABLE') <> 3002 THEN
    RAISE EXCEPTION 'migration 1124 postflight: sutravali_rules provenance incomplete';
  END IF;
  IF (SELECT count(*) FROM bg_transit_rules WHERE school IS NOT NULL) <> 70
     OR (SELECT count(*) FROM bg_transit_rules
         WHERE school IS NULL AND classical_citation NOT ILIKE 'UNSOURCED%') <> 0 THEN
    RAISE EXCEPTION 'migration 1124 postflight: bg_transit_rules school mismatch';
  END IF;
  IF (SELECT count(*) FROM bg_parihara_rules WHERE school = 'parashari') <> 60 THEN
    RAISE EXCEPTION 'migration 1124 postflight: bg_parihara_rules school mismatch';
  END IF;
  IF (SELECT count(*) FROM vidhi_primitives WHERE source_ref IS NOT NULL) <> 10
     OR (SELECT count(*) FROM vidhi_intent_floors WHERE source_ref IS NOT NULL) <> 8
     OR (SELECT count(*) FROM vidhi_floor_items WHERE source_ref IS NOT NULL) <> 280
     OR EXISTS (SELECT 1 FROM vidhi_primitives
                WHERE source_authority <> 'src/lib/vidhi/registry_data.ts')
     OR EXISTS (SELECT 1 FROM vidhi_intent_floors
                WHERE source_authority <> 'src/lib/vidhi/registry_data.ts')
     OR EXISTS (SELECT 1 FROM vidhi_floor_items
                WHERE source_authority <> 'src/lib/vidhi/registry_data.ts') THEN
    RAISE EXCEPTION 'migration 1124 postflight: vidhi provenance mismatch';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_vidhi_floors'
      AND english_description = floors_new_description
  ) THEN
    RAISE EXCEPTION 'migration 1124 postflight registry mismatch';
  END IF;
END $$;

COMMENT ON COLUMN public.sutravali_rules.school IS
  'DERIVED (migration 1124, W-L0-5): classical_texts.school of the rule''s text_id. Never authored per rule.';
COMMENT ON COLUMN public.sutravali_rules.qualification_state IS
  'DP §4.3 rule qualification vocabulary. Stored states: QUALIFIED_EXECUTABLE (license-cleared text + chunk witness), UNQUALIFIED_SOURCE (known text, rights unresolved), READABLE_NOT_EXECUTABLE (text_id not in classical_texts; column default). UNSUPPORTED_SCOPE / METHOD_INAPPLICABLE are application-time verdicts and are never stored.';
COMMENT ON COLUMN public.bg_transit_rules.school IS
  'DERIVED (migration 1124, W-L0-5): classical_texts.school via the citation→text_id map in l0_transit.py. NULL on the six UNSOURCED Rahu/Ketu vedha rows (B.10) — never guessed.';
COMMENT ON COLUMN public.bg_parihara_rules.school IS
  'DERIVED (migration 1124, W-L0-5): brahma_dosha_catalog.school of dosha_canonical_id. Never authored per rule.';
COMMENT ON COLUMN public.vidhi_primitives.source_authority IS
  'W-L0-5: the authority the row is authored/mirrored from. Constant src/lib/vidhi/registry_data.ts for the parity-gated vidhi corpus.';
COMMENT ON COLUMN public.vidhi_primitives.source_ref IS
  'W-L0-5: pointer to the classical/design authority the primitive derives from (e.g. BPHS Ch.18 / Aṣṭāṅga Hṛdayam), NULL when no single nameable source.';
COMMENT ON COLUMN public.vidhi_intent_floors.source_authority IS
  'W-L0-5: the authority the row is authored/mirrored from. Constant src/lib/vidhi/registry_data.ts for the parity-gated vidhi corpus.';
COMMENT ON COLUMN public.vidhi_intent_floors.source_ref IS
  'W-L0-5: pointer to the design authority the floor composition derives from (e.g. DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3), NULL when no single nameable source.';
COMMENT ON COLUMN public.vidhi_floor_items.source_authority IS
  'W-L0-5: inherited from the item''s intent floor at write time (declared derivation).';
COMMENT ON COLUMN public.vidhi_floor_items.source_ref IS
  'W-L0-5: inherited from the item''s intent floor at write time (declared derivation); NULL when the intent carries none.';

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT school, count(*) FROM sutravali_rules GROUP BY 1 ORDER BY 2 DESC;
--   -- expect: parashari 2839, jaimini 112, nadi 39, hellenistic 12; no NULL.
--   SELECT qualification_state, count(*) FROM sutravali_rules GROUP BY 1;
--   -- expect: QUALIFIED_EXECUTABLE 3002 only.
--   SELECT school, count(*) FROM bg_transit_rules GROUP BY 1;
--   -- expect: parashari 70, NULL 6 (the UNSOURCED Rahu/Ketu rows).
--   SELECT school, count(*) FROM bg_parihara_rules GROUP BY 1;
--   -- expect: parashari 60.
--   SELECT intent, source_ref FROM vidhi_intent_floors WHERE source_ref IS NOT NULL
--   ORDER BY 1;  -- expect: the 8 floors listed in the header (d).
--   SELECT count(*) FROM vidhi_floor_items WHERE source_ref IS NOT NULL;
--   -- expect: 280.
--   SELECT english_description FROM asset_registry WHERE asset_id = 'bg_vidhi_floors';
--   -- expect: the floors_new_description text above (1/14 [MANDATORY] ...).
--
-- DOWN (manual rollback — restores exactly the pre-1124 state):
--   BEGIN;
--   UPDATE asset_registry
--      SET english_description = '<642 composite pre-state, verbatim from the
--          floors_old_description constant above>'
--    WHERE asset_id = 'bg_vidhi_floors';
--   ALTER TABLE public.sutravali_rules
--     DROP CONSTRAINT IF EXISTS sutravali_rules_qualification_state_vocab,
--     DROP COLUMN school, DROP COLUMN qualification_state;
--   ALTER TABLE public.bg_transit_rules DROP COLUMN school;
--   ALTER TABLE public.bg_parihara_rules DROP COLUMN school;
--   ALTER TABLE public.vidhi_primitives
--     DROP COLUMN source_authority, DROP COLUMN source_ref;
--   ALTER TABLE public.vidhi_intent_floors
--     DROP COLUMN source_authority, DROP COLUMN source_ref;
--   ALTER TABLE public.vidhi_floor_items
--     DROP COLUMN source_authority, DROP COLUMN source_ref;
--   COMMIT;
--   -- NOTE: DOWN restores schema only for the rule tables; writers from the
--   -- same worktree still emit the new columns and will error against the
--   -- rolled-back schema — roll the writers back together with this DOWN.
-- =============================================================================
