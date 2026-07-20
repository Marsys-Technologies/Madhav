/**
 * Chart-Agnostic Gate — Registry Integration Tests
 * ==================================================
 * Runs the gate against the actual registered capabilities
 * to confirm the retrofitted registry is clean.
 *
 * These tests load the real capability objects from the registry
 * layer files and pass them through the gate, verifying that:
 * - All L0 (global) capabilities pass the gate
 * - All L1 (per_chart) capabilities pass the gate
 * - All L2, L5 (per_chart) capabilities pass the gate
 * - The known native-id leak in get_positions is scrubbed
 */

import { describe, it, expect } from 'vitest'
import { checkCapability, checkAllCapabilities, NATIVE_CHART_ID } from './chart_agnostic_gate'
import type { CapabilityDescriptor } from './types'

// Import retrofitted capabilities directly
import { getPositionsCapability }       from './layers/L1_ganita/get_positions'
import { getDignityCapability }         from './layers/L1_ganita/get_dignity'
import { getStrengthCapability }        from './layers/L1_ganita/get_strength'
import { getAspectsCapability }         from './layers/L1_ganita/get_aspects'
import { getYogaDoshaCapability }       from './layers/L1_ganita/get_yoga_dosha'
import { getDivisionalsCapability }     from './layers/L1_ganita/get_divisionals'
import { getAshtakavargaCapability }    from './layers/L1_ganita/get_ashtakavarga'
import { getDashasCapability }          from './layers/L1_ganita/get_dashas'
import { getPanchangaCapability }       from './layers/L1_ganita/get_panchanga'
import { getArgalaCapability }          from './layers/L1_ganita/get_argala'
import { getKarakasCapability }         from './layers/L1_ganita/get_karakas'
import { getSensitivePointsCapability } from './layers/L1_ganita/get_sensitive_points'
import { getSadeSatiCapability }        from './layers/L1_ganita/get_sade_sati'
import { getEclipseFlagsCapability }    from './layers/L1_ganita/get_eclipse_flags'
import { getTajikCapability }           from './layers/L1_ganita/get_tajik'
import { getTaraChanndraBalaCapability }from './layers/L1_ganita/get_tara_chandra_bala'
import { getBhavaBalaCapability }       from './layers/L1_ganita/get_bhava_bala'
import { getDispositorsCapability }     from './layers/L1_ganita/get_dispositors'
import { getAvasthsCapability }         from './layers/L1_ganita/get_avasthas'

import { queryYogaCatalogCapability }   from './layers/L0_brahmagyan/query_yoga_catalog'
import { queryDoshaCatalogCapability }  from './layers/L0_brahmagyan/query_dosha_catalog'
import { queryRemedyCorpusCapability }  from './layers/L0_brahmagyan/query_remedy_corpus'
import { queryClassicalTextsCapability }from './layers/L0_brahmagyan/query_classical_texts'
import { listEntitiesCapability }       from './layers/L0_brahmagyan/list_entities'
import { resolveEntityCapability }      from './layers/L0_brahmagyan/resolve_entity'
import { intentClassifyCapability }     from './layers/L0_brahmagyan/intent_classify'
import { queryPlanetPositionCapability }from './layers/L0_brahmagyan/query_planet_position'
import { queryPlanetTransitCapability } from './layers/L0_brahmagyan/query_planet_transit'
import { queryAspectsAtTimeCapability } from './layers/L0_brahmagyan/query_aspects_at_time'
import { queryRetrogradePeriodsCapability } from './layers/L0_brahmagyan/query_retrograde_periods'

import { queryUcdCapability }           from './layers/L2_bodha/query_ucd'
import { queryInsightsCapability }      from './layers/L5_mimamsa/query_insights'
import { queryCalibrationCapability }   from './layers/L5_mimamsa/query_calibration'

// ── Registry capability collections ─────────────────────────────────────────

const L1_CAPABILITIES: CapabilityDescriptor[] = [
  getPositionsCapability,
  getDignityCapability,
  getStrengthCapability,
  getAspectsCapability,
  getYogaDoshaCapability,
  getDivisionalsCapability,
  getAshtakavargaCapability,
  getDashasCapability,
  getPanchangaCapability,
  getArgalaCapability,
  getKarakasCapability,
  getSensitivePointsCapability,
  getSadeSatiCapability,
  getEclipseFlagsCapability,
  getTajikCapability,
  getTaraChanndraBalaCapability as unknown as CapabilityDescriptor,
  getBhavaBalaCapability,
  getDispositorsCapability,
  getAvasthsCapability as unknown as CapabilityDescriptor,
]

const L0_CAPABILITIES: CapabilityDescriptor[] = [
  queryYogaCatalogCapability,
  queryDoshaCatalogCapability,
  queryRemedyCorpusCapability,
  queryClassicalTextsCapability,
  listEntitiesCapability,
  resolveEntityCapability,
  intentClassifyCapability,
  queryPlanetPositionCapability as unknown as CapabilityDescriptor,
  queryPlanetTransitCapability as unknown as CapabilityDescriptor,
  queryAspectsAtTimeCapability as unknown as CapabilityDescriptor,
  queryRetrogradePeriodsCapability as unknown as CapabilityDescriptor,
]

const L2_L5_CAPABILITIES: CapabilityDescriptor[] = [
  queryUcdCapability,
  queryInsightsCapability,
  queryCalibrationCapability,
]

const ALL_CAPABILITIES = [...L0_CAPABILITIES, ...L1_CAPABILITIES, ...L2_L5_CAPABILITIES]

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('chart_agnostic_gate — registry integration', () => {

  it('get_positions: native uuid is scrubbed from chart_id field description', () => {
    const chartIdDesc = getPositionsCapability.input_schema?.['chart_id']?.description ?? ''
    expect(chartIdDesc).not.toContain(NATIVE_CHART_ID)
    expect(chartIdDesc).toContain('<chart_uuid>')
  })

  it('All L1 capabilities are per_chart scope', () => {
    for (const cap of L1_CAPABILITIES) {
      expect(cap.scope).toBe('per_chart')
    }
  })

  it('All L1 capabilities require chart_id', () => {
    for (const cap of L1_CAPABILITIES) {
      expect(cap.required_inputs).toContain('chart_id')
    }
  })

  it('All L1 capabilities have D1 contract fields', () => {
    for (const cap of L1_CAPABILITIES) {
      expect(cap.archetype, `${cap.uri} missing archetype`).toBeDefined()
      expect(cap.traversal_level, `${cap.uri} missing traversal_level`).toBeDefined()
      expect(cap.tool_role, `${cap.uri} missing tool_role`).toBeDefined()
      expect(cap.emits_references, `${cap.uri} missing emits_references`).toBeDefined()
      expect(cap.lel_capable, `${cap.uri} missing lel_capable`).toBeDefined()
    }
  })

  it('All L0 capabilities are global scope', () => {
    for (const cap of L0_CAPABILITIES) {
      expect(cap.scope).toBe('global')
    }
  })

  it('All L0 capabilities have D1 contract fields', () => {
    for (const cap of L0_CAPABILITIES) {
      expect(cap.archetype, `${cap.uri} missing archetype`).toBeDefined()
      expect(cap.traversal_level, `${cap.uri} missing traversal_level`).toBeDefined()
      expect(cap.tool_role, `${cap.uri} missing tool_role`).toBeDefined()
    }
  })

  it('L2 query_ucd is per_chart orientation_digest umbrella', () => {
    expect(queryUcdCapability.scope).toBe('per_chart')
    expect(queryUcdCapability.archetype).toBe('orientation_digest')
    expect(queryUcdCapability.tool_role).toBe('umbrella')
    expect(queryUcdCapability.traversal_level).toBe('L-ORIENT')
    expect(queryUcdCapability.lel_capable).toBe(true)
  })

  it('L5 query_insights is per_chart calibration quality tool', () => {
    expect(queryInsightsCapability.scope).toBe('per_chart')
    expect(queryInsightsCapability.archetype).toBe('calibration')
    expect(queryInsightsCapability.tool_role).toBe('quality')
    expect(queryInsightsCapability.lel_capable).toBe(true)
  })

  it('Gate passes GREEN on all L1 capabilities (0 violations)', () => {
    const violations = checkAllCapabilities(L1_CAPABILITIES)
    if (violations.length > 0) {
      // Print violations for easier debugging
      for (const v of violations) {
        console.error(`VIOLATION: ${v.uri} — ${v.rule}: ${v.detail}`)
      }
    }
    expect(violations).toHaveLength(0)
  })

  it('Gate passes GREEN on all L0 capabilities (0 violations)', () => {
    const violations = checkAllCapabilities(L0_CAPABILITIES)
    if (violations.length > 0) {
      for (const v of violations) {
        console.error(`VIOLATION: ${v.uri} — ${v.rule}: ${v.detail}`)
      }
    }
    expect(violations).toHaveLength(0)
  })

  it('Gate passes GREEN on all L2+L5 capabilities (0 violations)', () => {
    const violations = checkAllCapabilities(L2_L5_CAPABILITIES)
    if (violations.length > 0) {
      for (const v of violations) {
        console.error(`VIOLATION: ${v.uri} — ${v.rule}: ${v.detail}`)
      }
    }
    expect(violations).toHaveLength(0)
  })

  it('Gate passes GREEN on the entire registry (0 violations)', () => {
    const violations = checkAllCapabilities(ALL_CAPABILITIES)
    if (violations.length > 0) {
      for (const v of violations) {
        console.error(`VIOLATION: ${v.uri} — ${v.rule}: ${v.detail}`)
      }
    }
    expect(violations).toHaveLength(0)
  })

  it('Total registry has the expected capability count (L0=11 + L1=19 + L2=1 + L5=2 = 33)', () => {
    expect(ALL_CAPABILITIES).toHaveLength(33)
  })
})

// ── Full-catalog end-to-end proof (GT-32/GT-43/GT-54 remediation, 2026-07-19) ──
//
// The suites above run the gate against a curated subset of imported capabilities.
// This block instead loads the REAL, complete registered catalog via getCatalog()
// (the same aggregator both the MCP and chat channels use — see catalog.ts) and
// proves RULE-9/RULE-9B (native cardinality / "native chart" phrase leaks) fire
// zero times across every capability actually served, post-remediation of the
// get_dashas / register_d8_assess_domain / register_d7_channel / get_sade_sati /
// get_sensitive_points / get_divisionals / get_argala / ephemeris_cache_year /
// query_planet_transit / query_temporal_activation / query_activation_waveform /
// query_convergence_windows / query_contradictions / query_signals leaks.

describe('chart_agnostic_gate — full catalog (RULE-9/RULE-9B end-to-end)', () => {
  it('Gate passes GREEN on the entire live catalog for RULE-9 (native cardinality) violations', async () => {
    const { getCatalog } = await import('./catalog')
    const fullCatalog = getCatalog()
    expect(fullCatalog.length).toBeGreaterThan(0)

    const violations = checkAllCapabilities(fullCatalog).filter(
      v => v.rule === 'RULE-9-NATIVE_CARDINALITY_IN_DESCRIPTION' || v.rule === 'RULE-9B-NATIVE_CHART_PHRASE_IN_DESCRIPTION'
    )
    if (violations.length > 0) {
      for (const v of violations) {
        console.error(`VIOLATION: ${v.uri} — ${v.rule}: ${v.detail}`)
      }
    }
    expect(violations).toHaveLength(0)
  })
})
