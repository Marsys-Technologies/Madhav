-- Migration 1078: reseal bg_transit_rules's frozen integrity contract after
-- L0 repair items 1/2/3's row corrections and one genuine row addition.
--
-- Migration 613 pinned bg_transit_rules (alongside bg_transit_engine and
-- bg_transit_moorti) as a closed, governed-rebuild composite contract at 75
-- rows (42 favourable + 26 unfavourable + 7 migration-owned double_transit).
-- L0 repair items 1-3 (this same repair session, KALA_DELEGATED_DECISIONS_
-- v1_0.md D-E / KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md) made three governed
-- changes: (1) re-cited 35 rows off the refuted "BPHS Ch.29" to page-anchored
-- Phaladipika citations; (2) corrected three Venus vedha_house values
-- (UPDATE only, ids 35/44/45) and INSERTED the one genuinely missing Mercury
-- 8->1 pair the text specifies; (3) marked six Rahu/Ketu rows honestly
-- UNSOURCED. Item (2)'s INSERT is the only shape change: the table now holds
-- 76 rows (43 favourable + 26 unfavourable + 7 double_transit, +1 favourable
-- over migration 613's 42). This migration is the required governed reseal
-- for both the shape (target_floor, breakdown counts, description text) and
-- the content hash — bg_transit_engine's own sub-check is verified
-- byte-identical to migration 613's pinned hash below (this repair touched
-- bg_transit_rules only, never bg_transit_engine) and carries over unchanged.
--
-- New hash and counts independently computed and verified against
-- production (amjis-postgres) after items 1-3's writer ran, via the exact
-- same query migration 613 uses.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  prior_rules_description constant text :=
    '75 classical transit rules: 42 favourable, 26 unfavourable, and 7 double-transit rules from BPHS Ch.29, Phaladeepika Ch.26, Saravali, and Jataka Parijata.';
  new_rules_description constant text :=
    '76 classical transit rules: 43 favourable, 26 unfavourable, and 7 double-transit rules from Phaladeepika Adh. XXVI (page-anchored) and Saravali/Jataka Parijata (double-transit). L0 repair 2026-09: re-cited off the refuted "BPHS Ch.29", corrected 3 Venus vedha pairs, inserted the missing Mercury 8th-house pair, marked 6 Rahu/Ketu rows honestly unsourced.';
  prior_rules_explanation constant text :=
    '75 rows = 68 writer-owned Gochara rules (42 favourable + 26 unfavourable) plus 7 preserved migration-owned Jupiter–Saturn double-transit rules.';
  new_rules_explanation constant text :=
    '76 rows = 69 writer-owned Gochara rules (43 favourable + 26 unfavourable) plus 7 preserved migration-owned Jupiter–Saturn double-transit rules. The 69th writer-owned row is the Mercury 8th-house-transit/1st-house-vedha pair L0 repair item 2 inserted (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.3) — present in the text, absent from every prior build.';
  -- Unchanged from migration 613 — bg_transit_engine was never touched by
  -- this repair; carried forward verbatim as the guard precondition.
  engine_check constant text := $check$
SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
$check$;
  prior_rules_check constant text := $check$
SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
  AND (SELECT count(*) = 75 FROM bg_transit_rules)
  AND (SELECT count(*) FILTER (WHERE rule_type = 'favourable') = 42
       AND count(*) FILTER (WHERE rule_type = 'unfavourable') = 26
       AND count(*) FILTER (WHERE rule_type = 'double_transit') = 7
       FROM bg_transit_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY graha COLLATE "C",rule_type COLLATE "C",primary_house
  ),''),'UTF8')),'hex') =
    '13616890d782a47cf667a4b1d3c52d2be08408a80f647d0e4aed4fc38cae3e54'
  FROM bg_transit_rules)
  AND (SELECT count(*) = 27 FROM bg_transit_moorti)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_offset,moorti_name,quality_tier,phala_brief,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY nakshatra_offset
  ),''),'UTF8')),'hex') =
    'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450'
  FROM bg_transit_moorti)
$check$;
  new_rules_check constant text := $check$
SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
  AND (SELECT count(*) = 76 FROM bg_transit_rules)
  AND (SELECT count(*) FILTER (WHERE rule_type = 'favourable') = 43
       AND count(*) FILTER (WHERE rule_type = 'unfavourable') = 26
       AND count(*) FILTER (WHERE rule_type = 'double_transit') = 7
       FROM bg_transit_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY graha COLLATE "C",rule_type COLLATE "C",primary_house
  ),''),'UTF8')),'hex') =
    '1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d'
  FROM bg_transit_rules)
  AND (SELECT count(*) = 27 FROM bg_transit_moorti)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_offset,moorti_name,quality_tier,phala_brief,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY nakshatra_offset
  ),''),'UTF8')),'hex') =
    'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450'
  FROM bg_transit_moorti)
$check$;
BEGIN
  -- bg_transit_engine: unchanged guard, sanity-confirms this repair never
  -- touched it before proceeding to reseal bg_transit_rules.
  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_transit_engine' FOR UPDATE;
  IF NOT FOUND OR (registry_row.integrity_check_sql = engine_check) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 1078 refuses: bg_transit_engine integrity_check_sql has drifted from migration 613''s contract';
  END IF;

  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.target_floor = 75
    AND registry_row.english_description = prior_rules_description
    AND registry_row.volume_explanation = prior_rules_explanation
    AND registry_row.integrity_check_sql = prior_rules_check
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 1078 refuses: bg_transit_rules registry contract does not match migration 613''s applied state (already resealed, or 613 never applied)';
  END IF;

  UPDATE asset_registry
  SET target_floor = 76,
      english_description = new_rules_description,
      volume_explanation = new_rules_explanation,
      integrity_check_sql = new_rules_check
  WHERE asset_id = 'bg_transit_rules';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1078 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_transit_rules'
      AND target_floor = 76
      AND english_description = new_rules_description
      AND volume_explanation = new_rules_explanation
      AND integrity_check_sql = new_rules_check
  ) THEN
    RAISE EXCEPTION 'migration 1078 postflight registry mismatch';
  END IF;
END $$;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT target_floor, english_description FROM asset_registry
--     WHERE asset_id = 'bg_transit_rules';
--   -- expect: target_floor = 76
--   -- execute the stored integrity_check_sql itself:
--   SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules' \gexec
--   -- expect: t
--
-- DOWN (manual rollback — restores migration 613's original contract):
--   BEGIN;
--   UPDATE asset_registry
--      SET target_floor = 75,
--          english_description = $$<prior_rules_description from migration 613>$$,
--          volume_explanation = $$<prior_rules_explanation from migration 613>$$,
--          integrity_check_sql = $$<prior_rules_check from migration 613>$$
--    WHERE asset_id = 'bg_transit_rules';
--   COMMIT;
-- =============================================================================
