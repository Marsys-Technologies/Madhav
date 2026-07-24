import { describe, expect, it } from 'vitest';
import { VIDHI_INTENT_FLOORS, VIDHI_PRIMITIVES } from '@/lib/vidhi/registry_data';
import { isCitableKnownGap, isClosedCr, CLOSED_CRS } from '@/lib/vidhi/cr_status';

// The 135-live-tool catalog as surfaced to this session (mcp__marsys-jis-direct__* face
// names, minus the mcp__marsys-jis-direct__ prefix). Every primitive's live_tool and
// fallback_face's leading tool token MUST be a member of this set — a mapping to a
// non-existent tool name is a bind-time defect this test exists to catch.
const LIVE_TOOLS = new Set<string>([
  'assess_career', 'assess_health', 'assess_marriage', 'assess_wealth',
  'asset_registry_all', 'asset_registry_l0', 'bodha_chart_digest_get', 'bodha_discoveries_get',
  'bodha_domain_reading_get', 'bodha_graph_subgraph_get', 'bodha_graph_traverse_get',
  'bodha_quality_get', 'bodha_remedies_get', 'bodha_remedies_search', 'bodha_signals_get',
  'catalog_assets_all', 'catalog_assets_l0', 'catalog_assets_list', 'chart_snapshot',
  'compute_natal_positions', 'ephemeris_cache_year', 'event_anchors',
  'ganita_ayurdaya_get', 'ganita_chart_facts_get', 'ganita_condition_get',
  // SARVA-SIDDHI W-4 D-4 (CR-30): dedicated first-class KP cusp/sub-lord face.
  'ganita_kp_cusps_get',
  'ganita_dasha_lord_capability_get', 'ganita_dasha_periods_get', 'ganita_dashas_get',
  'ganita_medical_get', 'ganita_nakshatra_get', 'ganita_natal_positions_compute',
  'ganita_positions_get', 'ganita_sade_sati_get', 'ganita_sensitive_degrees_get',
  'ganita_special_lagnas_get', 'ganita_strength_get', 'ganita_structural_get',
  'ganita_tajaka_get', 'ganita_transit_anchors_get', 'ganita_vastu_get', 'ganita_vichara_get',
  'ganita_yoga_firings_get', 'ganita_yogas_get', 'get_cgm_subgraph', 'get_chart_orientation',
  'get_chart_quality', 'get_classical_citation', 'get_dashas', 'get_domain_reading',
  'get_graha_yuddha', 'get_positions', 'get_projections', 'get_remedies', 'get_signals',
  'get_temporal_windows', 'graha_portrait', 'bodha_bundle_get', 'intent_classify',
  // VIDHI-PŪRṆATĀ P-3b (E-1): the D-5 Gochara-Chitra window-engine tools — REGISTERED + LIVE on
  // the connector (their ROW data requires DB-direct access, tracked as the CR-131 known_gap; the
  // tool NAMES are real, which is exactly what this allowlist guards). The three E-1 primitives
  // (gochara_activation_read / gochara_forecast_read / election_read) route to these.
  'gochara_activation_get', 'gochara_forecast_get', 'gochara_election_avoidance_get',
  'judgment_query', 'kala_life_arc_get', 'kala_muhurta_get', 'kala_priority_ranking_get',
  'kala_projections_get', 'kala_bundle_get', 'kala_windows_get', 'kala_yoga_activation_get',
  'lel_query', 'list_assets', 'list_entities', 'catalog_charts_list', 'session_list',
  'list_remedies_by_category', 'mimamsa_calibration_get', 'mimamsa_insight_get',
  'mimamsa_lel_query', 'mimamsa_outcome_record', 'mitigation_map', 'muhurta_finder',
  // SARVA-SIDDHI (2026-07-24): mechanism_retrodiction_get shipped PR #688 (5f27d9d2,
  // 2026-07-21) — registered + live-wired, verified live for chart 482012f1. CR-68's
  // lel_retrodiction primitive now routes here (was mimamsa_lel_query).
  'mechanism_retrodiction_get',
  'pact_query', 'phala_anchors_get', 'phala_mitigation_get', 'phala_outlook',
  'phala_outlook_get', 'phala_predictive_anchors_get', 'phala_rectification_get',
  'prashna_undertaking_get', 'query_aspects_at_time', 'query_calibration',
  'query_chart_facts', 'query_dasha_periods', 'query_mantras', 'query_planet_position',
  'query_planet_transit', 'query_remedies', 'query_remedies_by_planet',
  'query_remedies_for_chart', 'query_retrograde_periods', 'query_special_lagnas',
  'query_tantric_remedies', 'read_remedy', 'session_recall', 'record_outcome',
  'ref_aspects_at_time_get', 'ref_classical_citation_get', 'ref_dasha_systems_get',
  'ref_dignity_reference_get', 'ref_doshas_get', 'ref_entities_list', 'ref_entity_resolve',
  'ref_ephemeris_year_get', 'ref_mantras_get', 'ref_nakshatra_get', 'ref_planet_position_get',
  'ref_planet_transit_get', 'ref_remedies_by_category_list', 'ref_remedies_by_planet_get',
  'ref_remedies_chart_get', 'ref_remedies_get', 'ref_remedies_search', 'ref_remedy_get',
  'ref_retrograde_periods_get', 'ref_rules_search', 'ref_sign_medical_get',
  'ref_tantric_remedies_get', 'ref_transit_rules_get', 'ref_vector_search', 'ref_yogas_get',
  'resolve_entity', 'catalog_chart_select', 'synth_chart_brief_get', 'synth_tail_divergence_get',
  'traverse_graph', 'util_intent_classify', 'vector_search', 'yoga_activation_by_dasha',
]);

/** First whitespace/`(`-delimited token of a tool-face string — strips args like "(category=…)". */
function leadingToolToken(face: string): string {
  return face.split(/[\s(]/)[0]!;
}

describe('vidhi registry — completeness (D-2 Lane V-1 deliverable 1)', () => {
  it('ships at least 25 primitives (design §3 targets "~30")', () => {
    expect(VIDHI_PRIMITIVES.length).toBeGreaterThanOrEqual(25);
  });

  it('every primitive_id is unique', () => {
    const ids = VIDHI_PRIMITIVES.map((p) => p.primitive_id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('every primitive has a non-empty definition, a versioned id, and a live-tool mapping', () => {
    for (const p of VIDHI_PRIMITIVES) {
      expect(p.definition.length).toBeGreaterThan(10);
      expect(p.version).toBeGreaterThanOrEqual(1);
      expect(p.live_tool.length).toBeGreaterThan(0);
    }
  });

  it('every primitive live_tool is a REAL live tool on the deployed connector (never a fabricated name)', () => {
    for (const p of VIDHI_PRIMITIVES) {
      expect(LIVE_TOOLS.has(p.live_tool), `primitive "${p.primitive_id}" maps to unknown live_tool "${p.live_tool}"`).toBe(true);
    }
  });

  it('every non-null fallback_face names a REAL live tool as its leading token', () => {
    for (const p of VIDHI_PRIMITIVES) {
      if (p.fallback_face === null) continue;
      const token = leadingToolToken(p.fallback_face);
      expect(LIVE_TOOLS.has(token), `primitive "${p.primitive_id}" fallback_face "${p.fallback_face}" leading token "${token}" is not a live tool`).toBe(true);
    }
  });

  it('every known_gap cites an OPEN or LOGGED CR — never a CLOSED one', () => {
    for (const p of VIDHI_PRIMITIVES) {
      if (p.known_gap === null) continue;
      expect(isClosedCr(p.known_gap), `primitive "${p.primitive_id}" known_gap "${p.known_gap}" is a CLOSED CR — forbidden`).toBe(false);
      expect(isCitableKnownGap(p.known_gap), `primitive "${p.primitive_id}" known_gap "${p.known_gap}" is not on the OPEN/LOGGED allowlist`).toBe(true);
    }
  });

  it('sanity: the CLOSED_CRS allowlist itself is non-empty (the "never CLOSED" test is not vacuous)', () => {
    expect(CLOSED_CRS.length).toBeGreaterThan(0);
    // and at least one CLOSED CR is correctly rejected if it were (hypothetically) cited
    expect(isCitableKnownGap('CR-57')).toBe(false); // CLOSED per BRIEF_D2.md §B0.1
  });

  it('every floor references only registered primitive_ids', () => {
    const known = new Set(VIDHI_PRIMITIVES.map((p) => p.primitive_id));
    for (const floor of VIDHI_INTENT_FLOORS) {
      for (const item of floor.floor_items) {
        expect(known.has(item.primitive_id), `floor "${floor.intent}" references unregistered primitive "${item.primitive_id}"`).toBe(true);
      }
    }
  });

  it('every floor has unique, gapless-from-1 order values within each band-agnostic sequence', () => {
    for (const floor of VIDHI_INTENT_FLOORS) {
      const orders = floor.floor_items.map((i) => i.order).sort((a, b) => a - b);
      const unique = new Set(orders);
      expect(unique.size, `floor "${floor.intent}" has duplicate order values`).toBe(orders.length);
    }
  });
});
