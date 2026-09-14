/**
 * Purna Anvesana Wave 2 producer-to-semantics editorial review.
 *
 * These are authored relationships, not name-derived joins. Every active W1 producer
 * must occur exactly once. The compiler validates this table against the generated W1
 * producer census and fails closed on omissions, duplicates, or stale SCU targets.
 */
export interface ProducerSemanticReviewGroup {
  readonly target_scu_id: string
  readonly rationale: string
  readonly asset_ids: readonly string[]
}

export const PRODUCER_SEMANTIC_REVIEW: readonly ProducerSemanticReviewGroup[] = [
  {
    target_scu_id: 'scu.catalog.query_class_priors',
    rationale: 'Supplies cohort and lifetime-count priors used to contextualize class-level evidence.',
    asset_ids: ['bg_class_lifetime_counts', 'bg_class_priors', 'bg_cohort'],
  },
  {
    target_scu_id: 'scu.catalog.query_compendium_index',
    rationale: 'Supplies the compendium inventory used to discover bounded classical material.',
    asset_ids: ['bg_compendium_index'],
  },
  {
    target_scu_id: 'scu.catalog.query_classical_texts',
    rationale: 'Supplies indexed texts, rules, concordance, reference entries, and resolvable citations for classical grounding.',
    asset_ids: ['bg_concordance', 'bg_gochara_citation_resolution', 'bg_reference', 'bg_rules', 'bg_text_index', 'bg_texts'],
  },
  {
    target_scu_id: 'scu.catalog.query_dasha_systems',
    rationale: 'Supplies the governed system definitions needed to select and interpret a dasha sequence.',
    asset_ids: ['bg_dasha_systems'],
  },
  {
    target_scu_id: 'scu.catalog.get_dignity',
    rationale: 'Supplies the reference tables required to qualify planetary dignity.',
    asset_ids: ['bg_dignity_reference'],
  },
  {
    target_scu_id: 'scu.catalog.query_dosha_catalog',
    rationale: 'Supplies configured dosha definitions that distinguish rules from chart-specific findings.',
    asset_ids: ['bg_doshas'],
  },
  {
    target_scu_id: 'scu.catalog.query_planet_position',
    rationale: 'Supplies governed ephemeris material and computation support for planetary positions.',
    asset_ids: ['bg_ephemeris', 'bg_ephemeris_engine'],
  },
  {
    target_scu_id: 'scu.catalog.query_formula_constants',
    rationale: 'Supplies versioned formula constants used by source-grounded computations.',
    asset_ids: ['bg_formula_constants'],
  },
  {
    target_scu_id: 'scu.catalog.query_convergence_windows',
    rationale: 'Supplies event-convergence configuration used to identify candidate timing windows.',
    asset_ids: ['bg_ghatana', 'ka_sangam'],
  },
  {
    target_scu_id: 'scu.catalog.query_planet_transit',
    rationale: 'Supplies transit arcs, engine output, rules, and materialized century-scale transit evidence.',
    asset_ids: ['bg_gochara_arcs', 'bg_transit_engine', 'bg_transit_rules', 'ka_gochara', 'ka_gochara_v3_century_materialize', 'ka_graha_sancara', 'ph_sankrama'],
  },
  {
    target_scu_id: 'scu.catalog.query_vedha_gochara',
    rationale: 'Supplies obstruction, latta, sarvatobhadra, and malefic-scale evidence for transit qualification.',
    asset_ids: ['bg_phaladeepika_latta', 'bg_sarvatobhadra_grid', 'bg_vedha_malefic_scale', 'ka_vedha_gochara'],
  },
  {
    target_scu_id: 'scu.catalog.query_kota_chakra',
    rationale: 'Supplies ring definitions and evaluated Kota Chakra timing evidence.',
    asset_ids: ['bg_kota_chakra_rings', 'ka_kota_chakra'],
  },
  {
    target_scu_id: 'scu.catalog.get_kp_cusps',
    rationale: 'Supplies KP sub-lord division evidence required for cusp-level retrieval.',
    asset_ids: ['bg_kp_sublord_division'],
  },
  {
    target_scu_id: 'scu.catalog.query_medical_mappings',
    rationale: 'Supplies governed medical correspondence data while retaining the non-diagnostic boundary.',
    asset_ids: ['bg_medical_mappings'],
  },
  {
    target_scu_id: 'scu.catalog.query_nakshatra_medical',
    rationale: 'Supplies nakshatra-specific health correspondence evidence.',
    asset_ids: ['bg_nakshatra_medical'],
  },
  {
    target_scu_id: 'scu.catalog.query_sign_medical',
    rationale: 'Supplies sign-specific health correspondence evidence.',
    asset_ids: ['bg_sign_medical'],
  },
  {
    target_scu_id: 'scu.catalog.query_muhurta_lattice',
    rationale: 'Supplies the electional lattice used to constrain candidate times.',
    asset_ids: ['bg_muhurta_lattice'],
  },
  {
    target_scu_id: 'scu.catalog.get_nakshatra',
    rationale: 'Supplies nakshatra reference and semantic evidence for the retrieved lunar mansion.',
    asset_ids: ['bg_nakshatra', 'bo_nakshatra_semantic', 'ga_nakshatra'],
  },
  {
    target_scu_id: 'scu.catalog.concept_locate',
    rationale: 'Supplies the governed ontology used to resolve domain concepts to evidence surfaces.',
    asset_ids: ['bg_ontology'],
  },
  {
    target_scu_id: 'scu.catalog.get_panchanga',
    rationale: 'Supplies the calendar factors required for a Panchanga result.',
    asset_ids: ['bg_panchanga', 'ga_panchanga'],
  },
  {
    target_scu_id: 'scu.catalog.query_remedies',
    rationale: 'Supplies grounded remedy and parihara rules for bounded remedial retrieval.',
    asset_ids: ['bg_parihara_rules', 'bg_remedies'],
  },
  {
    target_scu_id: 'scu.catalog.query_prashna_special_techniques',
    rationale: 'Supplies configured Prashna rules and evaluated special-technique evidence.',
    asset_ids: ['bg_prashna_rules', 'ph_nimitta'],
  },
  {
    target_scu_id: 'scu.catalog.query_sky_calendar',
    rationale: 'Supplies dated sky-calendar evidence for temporal retrieval.',
    asset_ids: ['bg_sky_calendar'],
  },
  {
    target_scu_id: 'scu.catalog.query_vastu_directions',
    rationale: 'Supplies directional reference and evaluated Vastu evidence.',
    asset_ids: ['bg_vastu_directions', 'ga_vastu'],
  },
  {
    target_scu_id: 'scu.catalog.query_question_lenses',
    rationale: 'Supplies governed Vidhi floors and primitives used to frame an inquiry without synthesizing its answer.',
    asset_ids: ['bg_vidhi_floors', 'bg_vidhi_primitives'],
  },
  {
    target_scu_id: 'scu.catalog.query_yoga_catalog',
    rationale: 'Supplies configured yoga definitions used to distinguish a rule from a chart firing.',
    asset_ids: ['bg_yogas'],
  },
  {
    target_scu_id: 'scu.catalog.query_discoveries',
    rationale: 'Supplies reviewed discovery records for bounded exploratory inquiry.',
    asset_ids: ['bo_anveshana'],
  },
  {
    target_scu_id: 'scu.catalog.query_chart_gestalt',
    rationale: 'Supplies whole-chart and Arudha structural summaries for gestalt assessment.',
    asset_ids: ['bo_arudha', 'bo_chart_gestalt'],
  },
  {
    target_scu_id: 'scu.catalog.graha_portrait',
    rationale: 'Supplies the Bimba portrait evidence used to inspect a planet in context.',
    asset_ids: ['bo_bimba'],
  },
  {
    target_scu_id: 'scu.catalog.query_cdlm_summary',
    rationale: 'Supplies the CDLM summary used for cross-domain assessment.',
    asset_ids: ['bo_cdlm_summary'],
  },
  {
    target_scu_id: 'scu.catalog.query_cgm_motifs',
    rationale: 'Supplies detected causal-graph motifs for relationship inspection.',
    asset_ids: ['bo_cgm_motifs'],
  },
  {
    target_scu_id: 'scu.catalog.query_cgm_paths',
    rationale: 'Supplies source-backed causal-graph paths for mechanism tracing.',
    asset_ids: ['bo_cgm_paths'],
  },
  {
    target_scu_id: 'scu.catalog.get_aspects',
    rationale: 'Supplies evaluated Drishti relationships for aspect retrieval.',
    asset_ids: ['bo_drishti'],
  },
  {
    target_scu_id: 'scu.catalog.query_attribution',
    rationale: 'Supplies grounding and attribution records for claim provenance.',
    asset_ids: ['bo_grounding', 'mi_adhilepa', 'ph_pramana'],
  },
  {
    target_scu_id: 'scu.catalog.query_spine_bundle',
    rationale: 'Supplies the Karanajala causal spine used to trace mechanism evidence.',
    asset_ids: ['bo_karanajala'],
  },
  {
    target_scu_id: 'scu.catalog.query_signals',
    rationale: 'Supplies extracted Laksana signals for evidence retrieval.',
    asset_ids: ['bo_laksana'],
  },
  {
    target_scu_id: 'scu.catalog.query_signal_families',
    rationale: 'Supplies ranked signal families and Mimamsa family evidence.',
    asset_ids: ['bo_laksana_rerank', 'mi_kula'],
  },
  {
    target_scu_id: 'scu.catalog.query_quality_scorecard',
    rationale: 'Supplies Pramana and Sodhana quality evidence for confidence constraints.',
    asset_ids: ['bo_pramana_mapa', 'mi_pariksha', 'mi_pramana', 'ph_suddha_sodhana'],
  },
  {
    target_scu_id: 'scu.catalog.query_pratijna',
    rationale: 'Supplies proposition records used to inspect an explicit claim contract.',
    asset_ids: ['bo_pratijna'],
  },
  {
    target_scu_id: 'scu.catalog.query_manifestation_grammar',
    rationale: 'Supplies Samskara and Sankalpa pattern evidence for manifestation grammar retrieval.',
    asset_ids: ['bo_samskara', 'mi_sankalpa'],
  },
  {
    target_scu_id: 'scu.catalog.query_contradictions',
    rationale: 'Supplies Samvada and Mimamsa contradiction evidence for explicit tension handling.',
    asset_ids: ['bo_samvada', 'mi_sambandha'],
  },
  {
    target_scu_id: 'scu.catalog.query_triangulation',
    rationale: 'Supplies Sangati agreement evidence for cross-source triangulation.',
    asset_ids: ['bo_sangati'],
  },
  {
    target_scu_id: 'scu.catalog.get_structural',
    rationale: 'Supplies special-lagna and structural chart evidence.',
    asset_ids: ['bo_special_lagna', 'ga_structural'],
  },
  {
    target_scu_id: 'scu.catalog.query_sudarshana_varsha',
    rationale: 'Supplies Sudarshana and annual-cycle evidence for time-bounded retrieval.',
    asset_ids: ['bo_sudarshana', 'ka_sudarshana_varsha'],
  },
  {
    target_scu_id: 'scu.catalog.query_remedies_for_chart',
    rationale: 'Supplies chart-specific Upaya evidence with applicability constraints.',
    asset_ids: ['bo_upaya'],
  },
  {
    target_scu_id: 'scu.finance.prosperity_assessment',
    rationale: 'Supplies Vargottama-Dhana evidence for the authored prosperity assessment.',
    asset_ids: ['bo_vargottama_dhana'],
  },
  {
    target_scu_id: 'scu.bodha.mechanism.network',
    rationale: 'Supplies the authored Yantra mechanism network used for causal inspection.',
    asset_ids: ['bo_yantra_mechanism'],
  },
  {
    target_scu_id: 'scu.catalog.get_ayurdaya',
    rationale: 'Supplies computed Ayurdaya evidence while preserving its bounded interpretive role.',
    asset_ids: ['ga_ayurdaya'],
  },
  {
    target_scu_id: 'scu.catalog.get_condition_composite',
    rationale: 'Supplies the composite planetary-condition output.',
    asset_ids: ['ga_condition'],
  },
  {
    target_scu_id: 'scu.catalog.get_dashas',
    rationale: 'Supplies computed dasha sequences for temporal analysis.',
    asset_ids: ['ga_dashas'],
  },
  {
    target_scu_id: 'scu.catalog.get_medical_indications',
    rationale: 'Supplies computed health indications while retaining the non-diagnostic boundary.',
    asset_ids: ['ga_medical'],
  },
  {
    target_scu_id: 'scu.catalog.get_positions',
    rationale: 'Supplies computed chart positions for downstream retrieval.',
    asset_ids: ['ga_positions'],
  },
  {
    target_scu_id: 'scu.catalog.get_prashna_lagna',
    rationale: 'Supplies computed Prashna-lagna evidence for horary inspection.',
    asset_ids: ['ga_prashna'],
  },
  {
    target_scu_id: 'scu.catalog.get_sade_sati',
    rationale: 'Supplies computed Sade-Sati interval evidence.',
    asset_ids: ['ga_sade_sati'],
  },
  {
    target_scu_id: 'scu.catalog.get_sensitive_points',
    rationale: 'Supplies computed sensitive-point evidence.',
    asset_ids: ['ga_sensitive'],
  },
  {
    target_scu_id: 'scu.catalog.get_sensitive_degrees',
    rationale: 'Supplies computed sensitive-degree evidence.',
    asset_ids: ['ga_sensitive_degree'],
  },
  {
    target_scu_id: 'scu.catalog.get_strength',
    rationale: 'Supplies computed planetary-strength evidence.',
    asset_ids: ['ga_strength'],
  },
  {
    target_scu_id: 'scu.catalog.get_tajik',
    rationale: 'Supplies computed Tajaka evidence for annual and horary analysis.',
    asset_ids: ['ga_tajaka'],
  },
  {
    target_scu_id: 'scu.catalog.get_transit_anchors',
    rationale: 'Supplies evaluated transit anchors and resonance evidence.',
    asset_ids: ['ga_transit_anchors', 'ka_gochara_resonance'],
  },
  {
    target_scu_id: 'scu.catalog.get_divisionals',
    rationale: 'Supplies computed divisional-chart evidence for authored varga retrieval.',
    asset_ids: ['ga_vargas'],
  },
  {
    target_scu_id: 'scu.catalog.get_vichara',
    rationale: 'Supplies a judged cross-domain Vichara structure for synthesis support.',
    asset_ids: ['ga_vichara'],
  },
  {
    target_scu_id: 'scu.yoga.firing_and_cancellation',
    rationale: 'Supplies chart-specific yoga firing and cancellation evidence.',
    asset_ids: ['ga_yoga'],
  },
  {
    target_scu_id: 'scu.catalog.query_life_arc',
    rationale: 'Supplies duration and life-stage evidence for temporal sequencing.',
    asset_ids: ['ka_avadhi', 'ka_jivana_parva'],
  },
  {
    target_scu_id: 'scu.catalog.query_prospective_ledger',
    rationale: 'Supplies prospective timing records for future-facing inquiry.',
    asset_ids: ['ka_bhavishya_lekha', 'mi_bhavisya'],
  },
  {
    target_scu_id: 'scu.catalog.query_active_dashas',
    rationale: 'Supplies active dasha-period evidence for current temporal activation.',
    asset_ids: ['ka_dasha_kala'],
  },
  {
    target_scu_id: 'scu.catalog.query_temporal_view',
    rationale: 'Supplies the Kala Darshana temporal view for ordered event inspection.',
    asset_ids: ['ka_kala_darshana'],
  },
  {
    target_scu_id: 'scu.kala.temporal_activation',
    rationale: 'Supplies Kalasutra and Yojaka evidence for the authored temporal-activation capability.',
    asset_ids: ['ka_kalasutra', 'ka_yojaka'],
  },
  {
    target_scu_id: 'scu.catalog.query_predictive_anchors',
    rationale: 'Supplies domain-field anchors used to constrain predictive retrieval.',
    asset_ids: ['ka_kshetra'],
  },
  {
    target_scu_id: 'scu.catalog.query_moorti_nirnaya',
    rationale: 'Supplies evaluated Moorti Nirnaya evidence.',
    asset_ids: ['ka_moorti_nirnaya'],
  },
  {
    target_scu_id: 'scu.catalog.query_muhurat',
    rationale: 'Supplies Muhurta service evidence for electional selection.',
    asset_ids: ['ka_muhurta_seva', 'ph_muhurta'],
  },
  {
    target_scu_id: 'scu.catalog.query_activation_waveform',
    rationale: 'Supplies temporal-wave evidence for activation sequencing.',
    asset_ids: ['ka_taranga'],
  },
  {
    target_scu_id: 'scu.catalog.query_tithi_pravesha',
    rationale: 'Supplies evaluated Tithi Pravesha evidence.',
    asset_ids: ['ka_tithi_pravesha'],
  },
  {
    target_scu_id: 'scu.catalog.call_priority_ranking',
    rationale: 'Supplies comparative timing evidence used to rank candidate activations.',
    asset_ids: ['ka_tulana'],
  },
  {
    target_scu_id: 'scu.catalog.query_obstruction_periods',
    rationale: 'Supplies Vighnakara obstruction-period evidence.',
    asset_ids: ['ka_vighnakara'],
  },
  {
    target_scu_id: 'scu.catalog.query_journal',
    rationale: 'Supplies recorded life events and Jivanaghatana evidence for audit and calibration.',
    asset_ids: ['lel_events', 'mi_jivanaghatana'],
  },
  {
    target_scu_id: 'scu.catalog.prediction_lifecycle_sweep',
    rationale: 'Supplies Abhilekha lifecycle records used to inspect prediction outcomes.',
    asset_ids: ['mi_abhilekha'],
  },
  {
    target_scu_id: 'scu.catalog.query_load_bearing',
    rationale: 'Supplies load-bearing evidence used to identify claims sensitive to weak support.',
    asset_ids: ['mi_bhara'],
  },
  {
    target_scu_id: 'scu.catalog.query_insights',
    rationale: 'Supplies reviewed Darshana insights for bounded discovery.',
    asset_ids: ['mi_darshana'],
  },
  {
    target_scu_id: 'scu.catalog.query_calibration',
    rationale: 'Supplies Gunanaka and Seva calibration evidence for confidence control.',
    asset_ids: ['mi_gunanaka', 'mi_seva'],
  },
  {
    target_scu_id: 'scu.catalog.query_insight_embeddings',
    rationale: 'Supplies indexed Vistara insight representations for discovery, not conclusion generation.',
    asset_ids: ['mi_vistara'],
  },
  {
    target_scu_id: 'scu.catalog.query_domain_result',
    rationale: 'Supplies Phaladesa domain results for bounded assessment.',
    asset_ids: ['ph_phaladesa'],
  },
  {
    target_scu_id: 'scu.catalog.query_remedy_program',
    rationale: 'Supplies Pratikara remedy-program evidence with its constraints.',
    asset_ids: ['ph_pratikara'],
  },
  {
    target_scu_id: 'scu.catalog.query_rectification',
    rationale: 'Supplies rectification evidence for explicit uncertainty handling.',
    asset_ids: ['ph_rectification'],
  },
  {
    target_scu_id: 'scu.catalog.query_cleansed_anchors',
    rationale: 'Supplies Sodhana-cleansed anchors for timing retrieval.',
    asset_ids: ['ph_sodhana'],
  },
] as const

export function getProducerSemanticReview(): readonly ProducerSemanticReviewGroup[] {
  return PRODUCER_SEMANTIC_REVIEW
}
