-- Migration 410: JL-015 (BA Phase 2.5 J2) — ga_structural category-ownership
-- single source of truth, retiring the hand-maintained count_sql allow-list
-- that has already silently drifted twice (migrations 364, 368).
--
-- Creates fact_category_ownership(fact_category, owning_asset_id) and seeds it
-- with the 58 concrete fact_category values ga_structural's hand-maintained
-- LIKE/IN/NOT-IN count_sql currently resolves to (verified live against the
-- canonical chart 482012f1 chart_facts rows, 2026-07-05). Updates
-- asset_registry.count_sql for ga_structural to a JOIN against this table
-- instead of the fragile hand-maintained pattern-list.

BEGIN;

CREATE TABLE IF NOT EXISTS fact_category_ownership (
    fact_category   TEXT NOT NULL,
    owning_asset_id TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (fact_category, owning_asset_id)
);

COMMENT ON TABLE fact_category_ownership IS
  'JL-015 (BA Phase 2.5 J2): single source of truth for which asset owns which '
  'chart_facts.fact_category, for count_sql derivation. Replaces hand-maintained '
  'LIKE/IN/NOT-IN allow-lists that have silently drifted twice (migrations 364, 368).';

CREATE INDEX IF NOT EXISTS idx_fact_category_ownership_asset
  ON fact_category_ownership (owning_asset_id);

INSERT INTO fact_category_ownership (fact_category, owning_asset_id) VALUES
    ('argala_natal_matrix', 'ga_structural'),
    ('aspect_jaimini', 'ga_structural'),
    ('aspect_jaimini_per_varga', 'ga_structural'),
    ('aspect_matrix_summary', 'ga_structural'),
    ('aspect_parashari_given', 'ga_structural'),
    ('aspect_parashari_per_varga', 'ga_structural'),
    ('aspect_parashari_received', 'ga_structural'),
    ('aspect_received_by_special_point', 'ga_structural'),
    ('aspect_tajik', 'ga_structural'),
    ('bhadra_flag', 'ga_structural'),
    ('bhava_significance_link', 'ga_structural'),
    ('chandra_bala_natal_baseline', 'ga_structural'),
    ('chart_center_of_gravity', 'ga_structural'),
    ('chart_cluster', 'ga_structural'),
    ('combustion_per_varga', 'ga_structural'),
    ('composite_dispositor_strength', 'ga_structural'),
    ('conjunction_per_varga', 'ga_structural'),
    ('conjunction_within_orb', 'ga_structural'),
    ('contradiction_pair', 'ga_structural'),
    ('convergence_count', 'ga_structural'),
    ('dispositor_chain_per_varga', 'ga_structural'),
    ('dispositor_tree', 'ga_structural'),
    ('eclipse_proximity_natal', 'ga_structural'),
    ('graha_avastha_baladi', 'ga_structural'),
    ('graha_avastha_deepta', 'ga_structural'),
    ('graha_avastha_jagrad', 'ga_structural'),
    ('graha_avastha_lajjitadi', 'ga_structural'),
    ('graha_avastha_lifetime_exposure_summary', 'ga_structural'),
    ('graha_avastha_sayanadi', 'ga_structural'),
    ('graha_centrality', 'ga_structural'),
    ('graha_composite_state_classification', 'ga_structural'),
    ('graha_dignity_per_varga', 'ga_structural'),
    ('graha_dispositor_chain', 'ga_structural'),
    ('graha_effective_dignity_modified_by_aspects', 'ga_structural'),
    ('graha_functional_class_per_ascendant', 'ga_structural'),
    ('graha_in_house_composite_strength', 'ga_structural'),
    ('graha_special_state_rollup', 'ga_structural'),
    ('graha_tri_deva_role_strength', 'ga_structural'),
    ('graha_vargottama_amplification_factor', 'ga_structural'),
    ('graha_yoga_karaka_flag', 'ga_structural'),
    ('graha_yuddha_per_varga', 'ga_structural'),
    ('house_strength_classification_rollup', 'ga_structural'),
    ('jaimini_tri_deva_role_per_graha', 'ga_structural'),
    ('kala_sarpa_per_varga', 'ga_structural'),
    ('karaka_bhava_concordance', 'ga_structural'),
    ('karaka_house_lord_overlap_flag', 'ga_structural'),
    ('karakatva_strength_per_significance', 'ga_structural'),
    ('lord_aspects_lord_per_varga', 'ga_structural'),
    ('lord_in_house_per_varga', 'ga_structural'),
    ('nakshatra_dispositor_chain', 'ga_structural'),
    ('net_argala_per_varga', 'ga_structural'),
    ('nway_config_per_varga', 'ga_structural'),
    ('panchaka_flag', 'ga_structural'),
    ('parivartana_per_varga', 'ga_structural'),
    ('pranic_strength_per_graha', 'ga_structural'),
    ('sambandha_grade', 'ga_structural'),
    ('tara_bala_natal_baseline', 'ga_structural'),
    ('vargottama_per_varga', 'ga_structural'),
    ('virodha_argala_natal_matrix', 'ga_structural')
ON CONFLICT (fact_category, owning_asset_id) DO NOTHING;

DO $$
BEGIN
    UPDATE asset_registry
    SET count_sql = $sql$SELECT count(*) AS count FROM chart_facts cf
JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category
WHERE cf.chart_id = $1 AND fco.owning_asset_id = 'ga_structural'$sql$
    WHERE asset_id = 'ga_structural';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 410: ga_structural row not found in asset_registry';
    END IF;
END $$;

COMMIT;
