-- 644_bg_parihara_rules_integrity_check.sql
--
-- NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md L0-W3 IMPLEMENT (L0_W2_DECIDE_v1_0.md
-- §2 NOW item 27): bg_parihara_rules was the only asset in its W1 analysis
-- batch with no integrity_check_sql, unlike its five siblings
-- (bg_kota_chakra_rings, bg_vedha_malefic_scale, bg_phaladeepika_latta,
-- bg_kp_sublord_division, bg_gochara_arcs, bg_gochara_citation_resolution),
-- all of which have a byte-identity SHA256 check. This migration adds one,
-- copying the established multi-table pattern (see e.g. bg_nakshatra,
-- bg_dignity_reference): per-table row-count pins + a content-hash pin per
-- table, all three composed with AND.
--
-- Also corrects target_floor: the writer populates 3 tables
-- (bg_parihara_rules + bg_muhurta_activity_rules + bg_muhurta_factor_census);
-- live counts are 61 + 329 + 59 = 449, not the registry's current 447 --
-- verified live before this migration (CLAUDE.md §N.4: floors track
-- achieved counts).
--
-- Hashes computed live against production 2026-09-04 and verified in a
-- rolled-back transaction before this migration was written.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
   SET target_floor = 449,
       integrity_check_sql = $check$
SELECT
  (SELECT count(*) = 61 FROM bg_parihara_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(dosha_canonical_id,dosha_name_en,dosha_category,cancellation_index,
        cancellation_condition_text,net_standing,scope,source_text_id,source_chapter,
        source_citation,extraction_context)::text,
      E'\n' ORDER BY dosha_canonical_id COLLATE "C",cancellation_index
    ),''),'UTF8')),'hex') =
      '3f2755ad5c474c027dff2fb1207b6a478f5c7ea7cfc1970103795b26b81c5175'
    FROM bg_parihara_rules)
  AND (SELECT count(*) = 329 FROM bg_muhurta_activity_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(activity_class,factor_type,factor_id,quality_score,source_citation)::text,
      E'\n' ORDER BY activity_class COLLATE "C",factor_type COLLATE "C",factor_id
    ),''),'UTF8')),'hex') =
      '5bb06a35f57b299187b8c6182b057627ea9f4406b26854c856bbdd6902fb4c71'
    FROM bg_muhurta_activity_rules)
  AND (SELECT count(*) = 59 FROM bg_muhurta_factor_census)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(factor_family,factor_name,disposition,citation_or_gap_note,
        evidence_pointer,school_tag)::text,
      E'\n' ORDER BY factor_family COLLATE "C",factor_name COLLATE "C"
    ),''),'UTF8')),'hex') =
      '5efc97659b77eae50abca427e9ba088f43096dacaee16f9f5647ce81539b5535'
    FROM bg_muhurta_factor_census)
$check$
 WHERE asset_id = 'bg_parihara_rules';

-- Forward reversal (safe at any time -- both are additive value corrections,
-- not schema changes): re-run with target_floor=447 and integrity_check_sql
-- reset to NULL.
