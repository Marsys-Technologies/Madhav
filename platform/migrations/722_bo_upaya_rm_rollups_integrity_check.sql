-- 722_bo_upaya_rm_rollups_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Extends bo_upaya's
-- integrity_check_sql (migration 721) to the four sibling rollup tables
-- explicitly deferred there: bodha_rm_chart_summary,
-- bodha_rm_dosha_remedy_bundles, bodha_rm_pattern_remedies, and
-- bodha_rm_dasha_windowed_prescriptions. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Thirteenth migration of L2's 710-729 range.
--
-- asset_registry carries ONE integrity_check_sql per asset_id, so this
-- REPLACES 721's value -- all sixteen of 721's invariants (on
-- bodha_rm_resonances / bodha_rm_remedy_prescriptions) are carried forward
-- verbatim below, not dropped. Twenty new invariants added, all
-- independently verified live against the canonical chart (482012f1)
-- before landing (C12).
--
-- Two DB-enforced natural keys (bodha_rm_chart_summary
-- (chart_id,ayanamsha_id,build_id,snapshot_type) and
-- bodha_rm_dosha_remedy_bundles (chart_id,ayanamsha_id,build_id,dosha_class),
-- both real UNIQUE constraints) are deliberately NOT re-asserted here --
-- a redundant check with zero detection power beyond what Postgres itself
-- already guarantees at insert time adds no C12 value.
--
-- Caught and corrected before shipping:
--   - theme_strength (bodha_rm_pattern_remedies) is NOT bounded [0,1]: it
--     is round(resonance_score, 6), and resonance_score_v1 (formulas.py)
--     is a weighted sum (max 1.0) times several (1 + burden*weight)
--     multipliers plus yoga_karaka_amp (up to 1.20) and chara_amp (up to
--     1.30) -- theoretical ceiling ~2.37, same unbounded-above shape as
--     721's resonance_match_score trap. Checked >= 0 only (every term in
--     the formula is non-negative by construction).
--   - window_intensity_multiplier (bodha_rm_dasha_windowed_prescriptions)
--     is NOT bounded [0,1] either -- it is leverage_index_value (L1,
--     unbounded positive) x sadhana_history_factor ([1.0,1.75]) x
--     dasha_runway_weight -- live values run 8.5-9.3 on the canonical
--     chart. Checked > 0 only (leverage_index_value is filtered > 0 at
--     the SQL fetch, sadhana factor is always >= 1.0).
--   - cross_tradition_unanimity_score is currently a near-constant 0.25
--     on every row: the ONE tradition literal this writer ever emits is
--     'parashari' (bo_upaya.py:1818, hardcoded), so
--     len({tradition})/4.0 always evaluates to 1/4.0. This is an honest
--     computation over a currently single-tradition corpus, not a
--     fabricated/hardcoded value (same disclosure class as L2_STATE.md's
--     S6 finding on system_convergence_count) -- checked bounded [0,1]
--     only, not asserted non-constant, since asserting variety would be a
--     C12-illegitimate invariant this writer cannot currently satisfy.
--
-- bodha_rm_resonances (9 invariants, carried forward from 721):
--   1-9. see 721_bo_upaya_integrity_check.sql for the full accounting.
--
-- bodha_rm_remedy_prescriptions (7 invariants, carried forward from 721):
--   10-16. see 721_bo_upaya_integrity_check.sql for the full accounting.
--
-- bodha_rm_chart_summary (7 new invariants):
--   17. snapshot_type always 'static_natal' (SNAPSHOT_TYPE constant).
--   18. verification_pass_status always UNVERIFIED_DEFAULT ('single') --
--       distinct from the primary tables' 'documented_approximation'.
--   19. recommended_intensity_class in the 4-value vocabulary the
--       priority_class->intensity map produces, or NULL (no resonances).
--   20. remedy_chart_typology in the 5-value _ELEMENT_MAP vocabulary
--       (_fetch_chart_typology's own literal outputs).
--   21. top_3_resonance_targets_jsonb has at most 3 elements.
--   22. top_10_priority_prescriptions_jsonb has at most 10 elements.
--   23. total_active_dosha_count cross-table TRUTH re-derivation: must
--       equal the live distinct-dosha-class bundle count for the same
--       (chart_id, ayanamsha_id, build_id) in bodha_rm_dosha_remedy_bundles
--       (both written together, same run).
--   24. acharya_review_required_count cross-table TRUTH re-derivation:
--       must equal the live count of requires_acharya_review_flag=true
--       rows in bodha_rm_remedy_prescriptions for the same group.
--   25. primary_dosha_class, when not NULL, must be one of that group's
--       actual bundle dosha_class values (cross-table).
--
-- bodha_rm_dosha_remedy_bundles (4 new invariants):
--   26. active_flag always TRUE (writer sets it unconditionally; no
--       deactivation path exists yet).
--   27. verification_pass_status always UNVERIFIED_DEFAULT ('single').
--   28. intensity_score bounded [0, 1] (min(count/3.0, 1.0) by
--       construction).
--   29. cancellation_count always 0 -- the writer hardcodes this (no
--       cancellation-detection logic wired yet); an honest "not yet
--       computed" placeholder per §N.4's honest-tier-over-fabrication
--       doctrine, not a claim that no cancellations exist.
--   30. prescription_ids_in_bundle_array cross-table TRUTH re-derivation:
--       every id resolves to a bodha_rm_remedy_prescriptions row in the
--       same (chart_id, ayanamsha_id, build_id) group whose
--       targets_dosha_class matches the bundle's own dosha_class.
--
-- bodha_rm_pattern_remedies (5 new invariants):
--   31. source_kind always 'resonance' (the only source_kind this writer
--       emits).
--   32. verification_pass_status always UNVERIFIED_DEFAULT ('single').
--   33. theme_strength never negative (see note above).
--   34. cross_tradition_unanimity_score bounded [0, 1] (see note above).
--   35. remedy_theme always matches 'strengthen_<Graha>'.
--   36. prescription_ids_array cross-table TRUTH re-derivation: every id
--       resolves to a bodha_rm_remedy_prescriptions row in the same
--       (chart_id, ayanamsha_id, build_id) group whose
--       target_resonance_id matches the pattern row's own source_id.
--
-- bodha_rm_dasha_windowed_prescriptions (7 new invariants):
--   37. dasha_system always 'vimshottari' (the only system this B-4 join
--       reads).
--   38. dasha_level always 'maha' (Mahadasha-level window only, per the
--       B-4 design note).
--   39. phase_within_window in the 2-value vocabulary the runway branch
--       produces.
--   40. verification_pass_status always 'documented_approximation' --
--       matches the primary tables' literal, NOT UNVERIFIED_DEFAULT.
--   41. window_intensity_multiplier always positive (see note above).
--   42. window_start_iso <= window_end_iso.
--   43. base_prescription_id cross-table TRUTH re-derivation: resolves to
--       a bodha_rm_remedy_prescriptions row in the same (chart_id,
--       ayanamsha_id, build_id) group.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances WHERE weakest_rank_in_chart < 1 OR weakest_rank_in_chart > 9
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_resonances WHERE resonance_score < 0)
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances
    WHERE graha NOT IN ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances WHERE remedy_priority_class NOT IN ('critical','high','medium','low')
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_resonances WHERE verification_pass_status != 'documented_approximation')
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_resonances WHERE resonance_score_formula_version != 'v1.0')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances
    WHERE ayanamsha_id NOT IN ('lahiri_chitrapaksha','raman','krishnamurti','surya_siddhanta_classical','true_chitra')
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, graha FROM bodha_rm_resonances GROUP BY 1, 2, 3 HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, weakest_rank_in_chart FROM bodha_rm_resonances GROUP BY 1, 2, 3 HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE verification_pass_status != 'documented_approximation'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions
    WHERE target_graha NOT IN ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE resonance_match_score < 0)
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE match_score_formula_version != 'v1.0')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE remedy_label_human IS NULL OR remedy_label_human = ''
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions p
    WHERE NOT EXISTS (SELECT 1 FROM bodha_rm_resonances r WHERE r.resonance_id = p.target_resonance_id)
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, target_resonance_id
    FROM bodha_rm_remedy_prescriptions
    GROUP BY 1, 2, 3 HAVING count(*) > 3
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_chart_summary WHERE snapshot_type != 'static_natal')
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_chart_summary WHERE verification_pass_status != 'single')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary
    WHERE recommended_intensity_class IS NOT NULL
      AND recommended_intensity_class NOT IN ('intensive','sustained','moderate','light')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary
    WHERE remedy_chart_typology NOT IN ('pitta','kapha_stable','vata','kapha_fluid','balanced')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary WHERE jsonb_array_length(top_3_resonance_targets_jsonb) > 3
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary WHERE jsonb_array_length(top_10_priority_prescriptions_jsonb) > 10
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary s
    WHERE s.total_active_dosha_count != (
      SELECT count(DISTINCT b.dosha_class) FROM bodha_rm_dosha_remedy_bundles b
      WHERE b.chart_id = s.chart_id AND b.ayanamsha_id = s.ayanamsha_id AND b.build_id = s.build_id
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary s
    WHERE s.acharya_review_required_count != (
      SELECT count(*) FROM bodha_rm_remedy_prescriptions p
      WHERE p.chart_id = s.chart_id AND p.ayanamsha_id = s.ayanamsha_id AND p.build_id = s.build_id
        AND p.requires_acharya_review_flag
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_chart_summary s
    WHERE s.primary_dosha_class IS NOT NULL
      AND s.primary_dosha_class NOT IN (
        SELECT b.dosha_class FROM bodha_rm_dosha_remedy_bundles b
        WHERE b.chart_id = s.chart_id AND b.ayanamsha_id = s.ayanamsha_id AND b.build_id = s.build_id
      )
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_dosha_remedy_bundles WHERE active_flag IS NOT TRUE)
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_dosha_remedy_bundles WHERE verification_pass_status != 'single')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dosha_remedy_bundles WHERE intensity_score < 0 OR intensity_score > 1
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_dosha_remedy_bundles WHERE cancellation_count != 0)
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dosha_remedy_bundles b
    CROSS JOIN LATERAL unnest(b.prescription_ids_in_bundle_array) AS pid
    LEFT JOIN bodha_rm_remedy_prescriptions p
      ON p.prescription_id = pid AND p.chart_id = b.chart_id
     AND p.ayanamsha_id = b.ayanamsha_id AND p.build_id = b.build_id
    WHERE p.prescription_id IS NULL OR p.targets_dosha_class IS DISTINCT FROM b.dosha_class
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_pattern_remedies WHERE source_kind != 'resonance')
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_pattern_remedies WHERE verification_pass_status != 'single')
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_pattern_remedies WHERE theme_strength < 0)
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_pattern_remedies
    WHERE cross_tradition_unanimity_score < 0 OR cross_tradition_unanimity_score > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_pattern_remedies WHERE remedy_theme !~ '^strengthen_[A-Za-z]+$'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_pattern_remedies pr
    CROSS JOIN LATERAL unnest(pr.prescription_ids_array) AS pid
    LEFT JOIN bodha_rm_remedy_prescriptions p
      ON p.prescription_id = pid AND p.chart_id = pr.chart_id
     AND p.ayanamsha_id = pr.ayanamsha_id AND p.build_id = pr.build_id
    WHERE p.prescription_id IS NULL OR p.target_resonance_id IS DISTINCT FROM pr.source_id
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions WHERE dasha_system != 'vimshottari')
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions WHERE dasha_level != 'maha')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions
    WHERE phase_within_window NOT IN ('active_md_direct_intervention','pre_md_preparation_window')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions WHERE verification_pass_status != 'documented_approximation'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions WHERE window_intensity_multiplier <= 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions WHERE window_start_iso > window_end_iso
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_dasha_windowed_prescriptions w
    LEFT JOIN bodha_rm_remedy_prescriptions p
      ON p.prescription_id = w.base_prescription_id AND p.chart_id = w.chart_id
     AND p.ayanamsha_id = w.ayanamsha_id AND p.build_id = w.build_id
    WHERE p.prescription_id IS NULL
  )
$ic$
 WHERE asset_id = 'bo_upaya';
