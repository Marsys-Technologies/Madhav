/**
 * D5 wave — L3 Kāla capabilities: descriptor + gate tests
 * =========================================================
 * Tests all 11 L3 capabilities added by D5:
 *   6 data tools + 5 service wrappers
 *
 * Scope:
 *   1. All D1 contract fields present
 *   2. chart_id in required_inputs for per_chart tools
 *   3. No native chart UUID in description or defaults
 *   4. chart_agnostic_gate: 0 violations
 *   5. STUBBED tools (query_obstruction_periods, query_temporal_view)
 *      return {stubbed: true, data: []} not is_error
 *   6. Handler: chart_id absent → is_error on per_chart tools
 *
 * [verify-against: prod] — live DB queries require L3 build.
 */

import { describe, it, expect } from 'vitest'
import { checkCapability } from '../../../chart_agnostic_gate'
import { queryTemporalActivationCapability }  from '../query_temporal_activation'
import { queryConvergenceWindowsCapability }  from '../query_convergence_windows'
import { queryLifeArcCapability }             from '../query_life_arc'
import { queryProjectionsCapability }         from '../query_projections'
import { queryObstructionPeriodsCapability }  from '../query_obstruction_periods'
import { queryTemporalViewCapability }        from '../query_temporal_view'
import {
  callTransitSearchCapability,
  callEphemerisAtTCapability,
  callDashaEligibilityCapability,
  callMuhurtaScoreCapability,
  callPriorityRankingCapability,
} from '../call_service_wrappers'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const ALL_L3_CAPS = [
  queryTemporalActivationCapability,
  queryConvergenceWindowsCapability,
  queryLifeArcCapability,
  queryProjectionsCapability,
  queryObstructionPeriodsCapability,
  queryTemporalViewCapability,
  callTransitSearchCapability,
  callEphemerisAtTCapability,
  callDashaEligibilityCapability,
  callMuhurtaScoreCapability,
  callPriorityRankingCapability,
]

describe('D5 L3 Kāla — chart_agnostic_gate', () => {
  for (const cap of ALL_L3_CAPS) {
    it(`${cap.name}: 0 gate violations`, () => {
      const violations = checkCapability(cap)
      expect(violations, JSON.stringify(violations)).toHaveLength(0)
    })
  }
})

describe('D5 L3 Kāla — D1 contract fields', () => {
  for (const cap of ALL_L3_CAPS) {
    it(`${cap.name}: has archetype, traversal_level, tool_role, emits_references, lel_capable, scope`, () => {
      expect(cap.archetype).toBeDefined()
      expect(cap.traversal_level).toBeDefined()
      expect(cap.tool_role).toBeDefined()
      expect(typeof cap.emits_references).toBe('boolean')
      expect(typeof cap.lel_capable).toBe('boolean')
      expect(cap.scope).toMatch(/^(per_chart|global)$/)
    })

    it(`${cap.name}: description does not contain native chart UUID`, () => {
      expect(cap.description).not.toContain(NATIVE_CHART_ID)
    })

    if (cap.scope === 'per_chart') {
      it(`${cap.name}: chart_id in required_inputs`, () => {
        expect(cap.required_inputs).toContain('chart_id')
      })
    }
  }
})

// WP-1.3(a) / F-L10-012,018 (LCA-19): these two tools were STUBBED-PENDING-DATA but
// their tables (kala_obstruction 602-638/chart, kala_darshana 750/chart) are now populated
// and the tools serve the real rows. The old "returns stubbed=true" assertions were removed;
// see wp13a_computed_but_unserved.test.ts for the DB-mocked serving-path coverage.
describe('D5 L3 Kāla — WP-1.3(a) un-stubbed serving tools', () => {
  it('query_obstruction_periods: no longer advertises stubbing in its description', () => {
    expect(queryObstructionPeriodsCapability.description).not.toContain('STUBBED-PENDING-DATA')
  })

  it('query_temporal_view: no longer advertises stubbing in its description', () => {
    expect(queryTemporalViewCapability.description).not.toContain('STUBBED-PENDING-DATA')
  })

  it('query_obstruction_periods: chart_id absent → is_error=true', async () => {
    const result = await queryObstructionPeriodsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('query_temporal_view: chart_id absent → is_error=true', async () => {
    const result = await queryTemporalViewCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })
})

describe('D5 L3 Kāla — handler: chart_id absent → is_error', () => {
  const perChartCaps = ALL_L3_CAPS.filter(c => c.scope === 'per_chart')

  for (const cap of perChartCaps) {
    it(`${cap.name}: is_error when chart_id missing`, async () => {
      const result = await cap.handler({}, undefined)
      expect(result.is_error).toBe(true)
    })
  }
})

describe('D5 L3 Kāla — tool roles', () => {
  it('query_temporal_activation: tool_role = umbrella (L3 entry point)', () => {
    expect(queryTemporalActivationCapability.tool_role).toBe('umbrella')
  })

  it('query_temporal_activation: has drill_children', () => {
    expect(queryTemporalActivationCapability.drill_children).toContain('marsys://tool/L3/query_convergence_windows')
    expect(queryTemporalActivationCapability.drill_children).toContain('marsys://tool/L3/query_life_arc')
  })

  it('call_* service wrappers: tool_role = temporal', () => {
    const serviceCaps = [callTransitSearchCapability, callEphemerisAtTCapability, callMuhurtaScoreCapability]
    for (const cap of serviceCaps) {
      expect(cap.tool_role).toBe('temporal')
    }
  })

  it('global service caps have scope = global', () => {
    expect(callTransitSearchCapability.scope).toBe('global')
    expect(callEphemerisAtTCapability.scope).toBe('global')
    expect(callMuhurtaScoreCapability.scope).toBe('global')
  })

  it('per_chart service caps have scope = per_chart', () => {
    expect(callDashaEligibilityCapability.scope).toBe('per_chart')
    expect(callPriorityRankingCapability.scope).toBe('per_chart')
  })
})
