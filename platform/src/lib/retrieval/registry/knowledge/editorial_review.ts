/**
 * Purna Anvesana Wave 2 authored editorial review.
 *
 * Membership is deliberately exact and exhaustive: a descriptor is editorial only when its
 * capability name appears once in one reviewed family below. The compiler has no catch-all.
 */
import type {
  ProducerOutputAvailabilityRequirement,
  ProducerOutputClaim,
  SemanticCapabilityDeclaration,
  SemanticCapabilityKind,
} from './types'
import { JUDGMENT_READING_CHECKLIST_V2_CONTRACT } from '../layers/reading_checklist'

export interface DescriptorEditorialFamily {
  readonly family_id: string
  readonly domains: readonly string[]
  readonly concepts: readonly string[]
  readonly intents: readonly string[]
  readonly outputs: readonly string[]
  readonly horizons: readonly string[]
  readonly kind?: SemanticCapabilityKind
  readonly evidence_use: string
}

/**
 * First-slice availability decisions whose handlers are composite/source-backed
 * but have no complete, exact reviewed receipt contract yet.  Do not replace a
 * missing full contract with an adjacent producer digest: these entries keep
 * the route deliberately dark until the actual handler inputs are coverable.
 */
export interface DescriptorAvailabilityReview {
  readonly reason: string
  /** Mandatory executable legs that currently lack a complete exact contract. */
  readonly missing_binding_ids?: readonly string[]
  readonly source_refs: readonly string[]
}

/**
 * Exact receipt contracts for descriptor-derived bindings. These are separate
 * from deliberate-dark reviews: a descriptor is promotable only when its
 * handler's complete materialized output is represented by the reviewed spec.
 */
export interface DescriptorAvailabilityContractReview {
  readonly producer_output_claims: readonly ProducerOutputClaim[]
  readonly requirements: readonly ProducerOutputAvailabilityRequirement[]
}

const ASSESS_DOMAIN_MANDATORY_BINDINGS = [
  'registry:marsys://tool/L2/query_domain_reading',
  'registry:marsys://tool/L3/query_temporal_activation',
  'registry:marsys://tool/L2/query_contradictions',
] as const

const AVAILABILITY_REVIEWS: Readonly<Record<string, DescriptorAvailabilityReview>> = {
  assess_career: {
    reason: 'The composite requires domain reading, temporal activation, and contradictions. Each mandatory executable leg lacks a complete exact availability contract, so the assembled assessment cannot be promoted from adjacent receipts.',
    missing_binding_ids: ASSESS_DOMAIN_MANDATORY_BINDINGS,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts#runAssessDomain',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:679',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:791',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:804',
    ],
  },
  assess_marriage: {
    reason: 'The composite requires domain reading, temporal activation, and contradictions. Each mandatory executable leg lacks a complete exact availability contract, so the assembled assessment cannot be promoted from adjacent receipts.',
    missing_binding_ids: ASSESS_DOMAIN_MANDATORY_BINDINGS,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts#runAssessDomain',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:679',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:791',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:804',
    ],
  },
  get_strength: {
    reason: 'The handler defaults to all 21 selectable strength fact categories and, for frame-aware results, also reads graha_position facts. ga_strength attests only canonical-chart graha_shadbala_total rows, so even a fresh exact receipt covers one category rather than the full handler data and cannot promote this route.',
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_strength.ts:35-40',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_strength.ts:128-145',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_strength.ts:176-202',
      'platform/migrations/891_nirmana_l1_ga_strength_output_digest_spec.sql:3-18',
    ],
  },
}

const PRIMARY_BINDING_DETAILS: Readonly<Record<string, NonNullable<SemanticCapabilityDeclaration['primary_binding_details']>>> = {
  query_classical_texts: {
    pagination: 'cursor',
    pagination_contract: {
      request_position_path: 'page_cursor',
      request_limit_path: 'limit',
      effective_maximum: 200,
      result_collection_path: 'content.citations',
      next_path: 'content.next_page_cursor',
      more_available_path: 'content.more_available',
      deterministic_order: [
        'hybrid:combined_score DESC', 'hybrid:text_id ASC', 'hybrid:chapter ASC NULLS LAST',
        'hybrid:verse_ref ASC NULLS LAST', 'hybrid:chunk_id ASC', 'hybrid:id ASC',
        'legacy:text_id ASC', 'legacy:chapter ASC NULLS LAST', 'legacy:verse_start ASC NULLS LAST',
        'legacy:chunk_id ASC', 'legacy:id ASC',
      ],
      material_trim_paths: [
        'budget_kb_applied', 'trim_report', 'material_trimmed', 'response_trimmed', 'truncated',
      ],
    },
    route_evidence: 'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_classical_texts.ts#queryClassicalTextsCapability.handler',
  },
  judgment_query: {
    pagination: 'none',
    non_paginated_closure: {
      closure_version: 'judgment-reading-checklist-v2',
      checklist_path: 'reading_checklist',
      checklist_contract_id: JUDGMENT_READING_CHECKLIST_V2_CONTRACT.contract_id,
      required_units: JUDGMENT_READING_CHECKLIST_V2_CONTRACT.required_units,
      material_trim_paths: [
        'budget_kb_applied', 'trim_report', 'material_trimmed', 'response_trimmed', 'truncated',
      ],
      source_ref: 'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts#reading_checklist',
    },
    route_evidence: 'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts#judgmentQueryCapability.handler',
  },
}

const AVAILABILITY_CONTRACT_REVIEWS: Readonly<Record<string, DescriptorAvailabilityContractReview>> = {
  query_classical_texts: {
    producer_output_claims: [{
      asset_id: 'bg_texts',
      component: 'classical_texts and classical_text_chunks',
      output_digest_spec_sha256: '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6',
      disposition: 'reviewed_output',
      evidence: 'platform/supabase/migrations/609_nirmana_l0_digest_spec_revision.sql:new_texts_spec',
    }],
    requirements: [{
      kind: 'producer_output',
      asset_id: 'bg_texts',
      spec_sha256: '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6',
      scope: 'global',
      source_ref: 'platform/supabase/migrations/609_nirmana_l0_digest_spec_revision.sql:new_texts_spec',
    }],
  },
  get_positions: {
    producer_output_claims: [{
      asset_id: 'ga_positions',
      component: 'chart_facts graha positions, sign attributes, bhava cusps, and house-chalit facts',
      output_digest_spec_sha256: '474b77debe7776ee7f84a1d6b225b386d7846452cbeb2cc258a98706168e3c9f',
      disposition: 'reviewed_output',
      evidence: 'platform/migrations/875_nirmana_l1_ga_positions_output_digest_spec.sql:74-77',
    }],
    requirements: [{
      kind: 'producer_output',
      asset_id: 'ga_positions',
      spec_sha256: '474b77debe7776ee7f84a1d6b225b386d7846452cbeb2cc258a98706168e3c9f',
      scope: 'chart_build',
      source_ref: 'platform/migrations/875_nirmana_l1_ga_positions_output_digest_spec.sql:74-77',
    }],
  },
  query_medical_mappings: {
    producer_output_claims: [{
      asset_id: 'bg_medical_mappings',
      component: 'medical_mappings',
      output_digest_spec_sha256: '914a5a3a22053fdc15900cadd25242b777436ea8ef471006c376d8d5932c96da',
      disposition: 'reviewed_output',
      evidence: 'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:27',
    }],
    requirements: [{
      kind: 'producer_output',
      asset_id: 'bg_medical_mappings',
      spec_sha256: '914a5a3a22053fdc15900cadd25242b777436ea8ef471006c376d8d5932c96da',
      scope: 'global',
      source_ref: 'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:27',
    }],
  },
  query_nakshatra_medical: {
    producer_output_claims: [{
      asset_id: 'bg_nakshatra_medical',
      component: 'nakshatra_medical',
      output_digest_spec_sha256: 'ae8016ab4ee18b5794d027c593dcf9662d5bfd05562f9df509985f176a1fd4b1',
      disposition: 'reviewed_output',
      evidence: 'platform/migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql:27-33',
    }],
    requirements: [{
      kind: 'producer_output',
      asset_id: 'bg_nakshatra_medical',
      spec_sha256: 'ae8016ab4ee18b5794d027c593dcf9662d5bfd05562f9df509985f176a1fd4b1',
      scope: 'global',
      source_ref: 'platform/migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql:27-33',
    }],
  },
  query_sign_medical: {
    producer_output_claims: [{
      asset_id: 'bg_sign_medical',
      component: 'sign_medical',
      output_digest_spec_sha256: '44333a746758f9a71288524273a4941071391f60ec753062d5295fafba6dcad7',
      disposition: 'reviewed_output',
      evidence: 'platform/migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql:19-25',
    }],
    requirements: [{
      kind: 'producer_output',
      asset_id: 'bg_sign_medical',
      spec_sha256: '44333a746758f9a71288524273a4941071391f60ec753062d5295fafba6dcad7',
      scope: 'global',
      source_ref: 'platform/migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql:19-25',
    }],
  },
}

export function getDescriptorAvailabilityReview(name: string): DescriptorAvailabilityReview | undefined {
  return AVAILABILITY_REVIEWS[name]
}

export function getDescriptorAvailabilityContractReview(name: string): DescriptorAvailabilityContractReview | undefined {
  return AVAILABILITY_CONTRACT_REVIEWS[name]
}

const FAMILIES: Readonly<Record<string, DescriptorEditorialFamily>> = {
  assessment: {
    family_id: 'assessment', domains: ['cross_domain'],
    concepts: ['domain_assessment', 'evidence_reconciliation', 'judgment_support'],
    intents: ['assess', 'reconcile'],
    outputs: ['assessment_findings', 'reconciled_evidence'],
    horizons: ['natal', 'current'],
    evidence_use: 'frame and reconcile domain evidence before downstream interpretation',
  },
  strength_timing: {
    family_id: 'strength_timing', domains: ['planetary_condition', 'timing'],
    concepts: ['lunar_strength', 'nakshatra_relationship', 'timing_qualification'],
    intents: ['compare', 'time'],
    outputs: ['lunar_strength_evidence', 'timing_qualification'],
    horizons: ['current', 'candidate_time'],
    kind: 'temporal',
    evidence_use: 'qualify a time using source-backed lunar and nakshatra strength without treating it as horary judgment',
  },
  catalog: {
    family_id: 'catalog', domains: ['evidence_infrastructure'],
    concepts: ['capability_discovery', 'evidence_inventory', 'route_selection'],
    intents: ['discover', 'route'],
    outputs: ['capability_candidates', 'route_constraints'],
    horizons: ['timeless_reference'],
    evidence_use: 'discover available evidence surfaces and choose a bounded retrieval route',
  },
  chart_evidence: {
    family_id: 'chart_evidence', domains: ['chart_state'],
    concepts: ['chart_fact', 'chart_snapshot', 'coordinate_frame'],
    intents: ['establish', 'inspect'],
    outputs: ['chart_state_evidence', 'frame_safety_evidence'],
    horizons: ['natal', 'current'],
    evidence_use: 'establish concrete chart facts and coordinate-frame safety before analytical retrieval',
  },
  system_introspection: {
    family_id: 'system_introspection', domains: ['evidence_infrastructure'],
    concepts: ['channel_configuration', 'service_surface', 'system_contract'],
    intents: ['audit', 'inspect'],
    outputs: ['configuration_evidence', 'system_surface_state'],
    horizons: ['current'],
    evidence_use: 'inspect internal route, channel, schema, and orchestration contracts without treating them as chart evidence',
  },
  classical: {
    family_id: 'classical', domains: ['classical_grounding'],
    concepts: ['classical_source', 'citation_grounding', 'textual_rule'],
    intents: ['ground', 'verify'],
    outputs: ['citation_anchors', 'source_passages'],
    horizons: ['timeless_reference'],
    kind: 'citation',
    evidence_use: 'ground a claim in retrievable classical source material',
  },
  planetary_state: {
    family_id: 'planetary_state', domains: ['planetary_state'],
    concepts: ['celestial_state', 'planetary_position', 'astronomical_reference'],
    intents: ['retrieve', 'verify'],
    outputs: ['computation_provenance', 'planetary_state_evidence'],
    horizons: ['natal', 'current'],
    evidence_use: 'establish the relevant computed or stored planetary state before analysis',
  },
  planetary_condition: {
    family_id: 'planetary_condition', domains: ['planetary_condition'],
    concepts: ['condition_evidence', 'planetary_strength', 'qualification_factor'],
    intents: ['compare', 'verify'],
    outputs: ['condition_qualifiers', 'strength_evidence'],
    horizons: ['natal', 'current'],
    evidence_use: 'qualify planetary condition, strength, and exceptions without interpreting them',
  },
  relational: {
    family_id: 'relational', domains: ['planetary_relationships'],
    concepts: ['causal_structure', 'planetary_relationship', 'relational_mechanism'],
    intents: ['explain', 'trace'],
    outputs: ['mechanism_paths', 'relationship_evidence'],
    horizons: ['natal', 'current'],
    kind: 'mechanism',
    evidence_use: 'trace source-backed relationships and mechanisms without inferring missing links',
  },
  timing: {
    family_id: 'timing', domains: ['timing'],
    concepts: ['activation_timing', 'temporal_sequence', 'timing_window'],
    intents: ['sequence', 'time'],
    outputs: ['temporal_sequence_evidence', 'timing_windows'],
    horizons: ['historical', 'current', 'future', 'multi_year'],
    kind: 'temporal',
    evidence_use: 'establish dated sequence, activation, or timing evidence',
  },
  calendar: {
    family_id: 'calendar', domains: ['calendar_and_election'],
    concepts: ['calendar_factor', 'electional_constraint', 'muhurta_window'],
    intents: ['constrain', 'select'],
    outputs: ['calendar_constraints', 'candidate_windows'],
    horizons: ['current', 'future', 'candidate_time'],
    kind: 'temporal',
    evidence_use: 'retrieve calendar and electional constraints for a candidate time',
  },
  health: {
    family_id: 'health', domains: ['health'],
    concepts: ['health_indication', 'medical_mapping', 'vitality'],
    intents: ['assess', 'verify'],
    outputs: ['health_indication_evidence', 'non_diagnostic_constraints'],
    horizons: ['natal', 'current'],
    evidence_use: 'retrieve health and vitality indicators while preserving non-diagnostic boundaries',
  },
  remedial: {
    family_id: 'remedial', domains: ['remediation'],
    concepts: ['appropriateness_constraint', 'remedial_action', 'remedy_grounding'],
    intents: ['constrain', 'retrieve'],
    outputs: ['applicability_constraints', 'grounded_remedy_options'],
    horizons: ['current', 'future'],
    kind: 'intervention',
    evidence_use: 'retrieve remedial options together with their grounding and applicability constraints',
  },
  yoga_prashna: {
    family_id: 'yoga_prashna', domains: ['yoga_and_prashna'],
    concepts: ['formation_status', 'horary_factor', 'planetary_combination'],
    intents: ['assess', 'verify'],
    outputs: ['formation_evidence', 'horary_evidence'],
    horizons: ['natal', 'current'],
    evidence_use: 'distinguish configured rules from chart-specific formation or horary evidence',
  },
  evidence_quality: {
    family_id: 'evidence_quality', domains: ['evidence_quality'],
    concepts: ['calibration_evidence', 'confidence_constraint', 'falsifier'],
    intents: ['audit', 'verify'],
    outputs: ['confidence_constraints', 'quality_findings'],
    horizons: ['historical', 'current'],
    evidence_use: 'measure provenance, calibration, falsifiers, and evidence quality without overstating confidence',
  },
  signal_calibration_registry: {
    family_id: 'signal_calibration_registry', domains: ['evidence_quality'],
    concepts: ['signal_family', 'negative_control', 'calibration_evidence', 'evidence_tier'],
    intents: ['audit', 'inspect', 'verify'],
    outputs: ['signal_family_definitions', 'calibration_status', 'evidence_tiers'],
    horizons: ['historical', 'current'],
    evidence_use: 'inspect global signal-family priors, evidence tiers, negative-control classes, and calibration status without treating registry rows as chart evidence',
  },
  prospective_ledger: {
    family_id: 'prospective_ledger', domains: ['evidence_quality', 'timing'],
    concepts: ['filed_prediction', 'falsifier', 'prediction_confidence', 'prediction_lifecycle', 'source_provenance'],
    intents: ['audit', 'retrieve', 'verify'],
    outputs: ['filed_predictions', 'falsifiers', 'lifecycle_status', 'source_citations', 'temporal_windows'],
    horizons: ['current', 'future', 'multi_year'],
    kind: 'temporal',
    evidence_use: 'retrieve explicitly filed falsifiable predictions with provenance and lifecycle state through a read-only surface that never files or calibrates predictions',
  },
  vastu: {
    family_id: 'vastu', domains: ['vastu'],
    concepts: ['directional_factor', 'space_orientation', 'vastu_constraint'],
    intents: ['assess', 'retrieve'],
    outputs: ['directional_evidence', 'spatial_constraints'],
    horizons: ['current'],
    evidence_use: 'retrieve directional and spatial evidence with its bounded remedial context',
  },
  annual: {
    family_id: 'annual', domains: ['annual_timing'],
    concepts: ['solar_return', 'tajika_factor', 'varshaphal_year'],
    intents: ['inspect', 'time'],
    outputs: ['annual_chart_evidence', 'year_lord_evidence'],
    horizons: ['annual', 'current_year', 'future_years'],
    kind: 'temporal',
    evidence_use: 'retrieve Tajika Varshaphal and year-lord evidence for an explicitly selected annual horizon',
  },
}

const MEMBERS: Readonly<Record<keyof typeof FAMILIES, readonly string[]>> = {
  assessment: [
    'assess_career', 'assess_health', 'assess_marriage', 'compose_large_n', 'judgment_query',
    'pact_query', 'query_cdlm_summary', 'query_chart_gestalt', 'query_contradictions',
    'query_domain_reading', 'query_domain_result', 'query_pratijna', 'query_question_lenses',
    'query_spillover_cascades', 'query_triangulation', 'query_ucd', 'synergy_cross_layer',
    'synergy_pipeline', 'get_vichara',
  ],
  strength_timing: ['get_tara_chandra_bala'],
  catalog: [
    'asset_registry_all', 'asset_registry_l0', 'concept_locate', 'intent_classify',
    'list_entities', 'resolve_entity', 'route', 'tool_search',
  ],
  chart_evidence: ['chart_facts_query', 'chart_snapshot', 'get_chart_header'],
  system_introspection: [
    'channel_chat_dispatch', 'channel_mcp_wiring', 'get_database_schema', 'maro_mcp_surface',
    'maro_orchestrate', 'maro_profiles',
  ],
  classical: [
    'classical_attribution_lookup', 'find_verses_about', 'list_classical_texts',
    'list_sutravali_rules_by_text', 'query_classical_texts', 'query_compendium_index',
    'query_formula_constants', 'query_prashna_fructification_rules', 'query_sutravali_rules',
    'query_sutravali_rules_for_planet', 'query_vichara_constants', 'read_chapter',
    'read_sutravali_rule',
  ],
  planetary_state: [
    'call_ephemeris_at_t', 'ephemeris_cache_native_lifetime', 'ephemeris_cache_year',
    'get_eclipse_flags', 'get_kp_cusps', 'get_nakshatra', 'get_positions',
    'get_sensitive_degrees', 'get_sensitive_points', 'graha_portrait',
    'query_aspects_at_time', 'query_combustion_orbs', 'query_graha_dik',
    'query_motion_state_thresholds', 'query_planet', 'query_planet_position',
    'query_shashtiamsha_deities', 'ref_graha_reference_get',
  ],
  planetary_condition: [
    'get_ashtakavarga', 'get_av_transit_gating', 'get_avasthas', 'get_bhava_bala',
    'get_condition_composite', 'get_dasha_lord_capability', 'get_dignity',
    'get_graha_yuddha', 'get_karakas', 'get_strength', 'query_avastha_schemes',
    'query_class_priors', 'query_graha_naisargika_friendship', 'query_transit_av_gates',
  ],
  relational: [
    'get_argala', 'get_aspects', 'get_dispositors', 'get_structural', 'query_cgm_motifs',
    'query_cgm_paths', 'query_signals', 'query_spine_bundle',
    'traverse_chart_graph',
  ],
  timing: [
    'call_dasha_eligibility', 'call_priority_ranking', 'call_transit_search', 'get_dashas',
    'get_sade_sati', 'get_transit_anchors', 'prediction_lifecycle_sweep',
    'query_activation_waveform', 'query_active_dashas', 'query_cleansed_anchors',
    'query_convergence_windows', 'query_dasha_dossier', 'query_dasha_systems',
    'query_kala_paddhati_profile', 'query_kota_chakra', 'query_life_arc',
    'query_current_transit_snapshot', 'query_moorti_nirnaya', 'query_obstruction_periods', 'query_planet_transit',
    'query_predictive_anchors', 'query_projections',
    'query_retrograde_periods', 'query_sky_calendar', 'query_sudarshana_varsha',
    'query_temporal_view', 'query_tithi_pravesha', 'query_transit_engine',
    'query_transit_moorti', 'query_transit_vedha', 'query_vedha_gochara',
    'yoga_activation_by_dasha',
  ],
  calendar: [
    'call_muhurta_score', 'call_panchanga_service', 'get_panchanga', 'query_auspicious_windows',
    'query_muhurat', 'query_muhurta_lattice',
  ],
  health: [
    'get_ayurdaya', 'get_medical_indications', 'query_medical_mappings',
    'query_nakshatra_medical', 'query_sign_medical',
  ],
  remedial: [
    'list_remedies_by_category', 'query_mantras', 'query_parihara_graph', 'query_remedies',
    'query_remedies_by_planet', 'query_remedies_for_chart', 'query_remedy_corpus',
    'query_remedy_program', 'query_rm_chart_summary', 'query_rm_dasha_windowed_prescriptions',
    'query_rm_dosha_remedy_bundles', 'query_rm_pattern_remedies', 'query_rm_prescriptions',
    'query_rm_resonances', 'query_tantric_remedies', 'read_remedy',
  ],
  yoga_prashna: [
    'get_prashna_lagna',
    'get_yoga_dosha', 'query_dosha_catalog', 'query_prashna_lagna_methods',
    'query_prashna_significators', 'query_prashna_special_techniques',
    'query_prashna_tajik_yogas', 'query_yoga_catalog',
  ],
  evidence_quality: [
    'lel_intake_checklist', 'query_anomaly_flags', 'query_attribution', 'query_calibration',
    'query_discoveries', 'query_falsifiers', 'query_insight_embeddings', 'query_insights',
    'query_journal', 'query_load_bearing', 'query_manifestation_grammar',
    'query_manifestation_sets', 'query_mimamsa_discoveries', 'query_quality_scorecard',
    'query_rectification',
  ],
  signal_calibration_registry: ['query_signal_families'],
  prospective_ledger: ['query_prospective_ledger'],
  vastu: ['get_vastu_directions', 'query_vastu_direction_remedials', 'query_vastu_directions'],
  annual: ['get_tajik'],
}

const REVIEW_BY_NAME = new Map<string, DescriptorEditorialFamily>()
for (const [familyId, names] of Object.entries(MEMBERS)) {
  const family = FAMILIES[familyId]
  if (!family) throw new Error(`UNKNOWN_EDITORIAL_FAMILY:${familyId}`)
  for (const name of names) {
    if (REVIEW_BY_NAME.has(name)) throw new Error(`DUPLICATE_EDITORIAL_REVIEW:${name}`)
    REVIEW_BY_NAME.set(name, family)
  }
}

export function getDescriptorEditorialReview(name: string): DescriptorEditorialFamily | null {
  return REVIEW_BY_NAME.get(name) ?? null
}

export function getDescriptorPrimaryBindingDetails(
  name: string,
): SemanticCapabilityDeclaration['primary_binding_details'] | undefined {
  return PRIMARY_BINDING_DETAILS[name]
}

export function getReviewedDescriptorNames(): readonly string[] {
  return [...REVIEW_BY_NAME.keys()].sort()
}
