/**
 * D5 wave — L4 Phala capabilities: descriptor + gate tests
 * ==========================================================
 * Tests all 9 L4 capabilities added by D5.
 *
 * [verify-against: prod] — live DB queries require L4 build.
 */

import { describe, it, expect } from 'vitest'
import { checkCapability } from '../../../chart_agnostic_gate'
import { queryPredictiveAnchorsCapability } from '../query_predictive_anchors'
import { queryDomainResultCapability }      from '../query_domain_result'
import {
  queryAuspiciousWindowsCapability,
  querySpilloverCascadesCapability,
  queryFalsifiersCapability,
  queryAnomalyFlagsCapability,
  queryRemedyProgramCapability,
  queryCleasedAnchorsCapability,
  queryRectificationCapability,
} from '../query_phala_calibration'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const ALL_L4_CAPS = [
  queryPredictiveAnchorsCapability,
  queryDomainResultCapability,
  queryAuspiciousWindowsCapability,
  querySpilloverCascadesCapability,
  queryFalsifiersCapability,
  queryAnomalyFlagsCapability,
  queryRemedyProgramCapability,
  queryCleasedAnchorsCapability,
  queryRectificationCapability,
]

describe('D5 L4 Phala — chart_agnostic_gate', () => {
  for (const cap of ALL_L4_CAPS) {
    it(`${cap.name}: 0 gate violations`, () => {
      const violations = checkCapability(cap)
      expect(violations, JSON.stringify(violations)).toHaveLength(0)
    })
  }
})

describe('D5 L4 Phala — D1 contract fields', () => {
  for (const cap of ALL_L4_CAPS) {
    it(`${cap.name}: has all required D1 topology fields`, () => {
      expect(cap.archetype).toBeDefined()
      expect(cap.traversal_level).toBeDefined()
      expect(cap.tool_role).toBeDefined()
      expect(typeof cap.emits_references).toBe('boolean')
      expect(typeof cap.lel_capable).toBe('boolean')
      expect(cap.scope).toBe('per_chart')
    })

    it(`${cap.name}: description does not contain native chart UUID`, () => {
      expect(cap.description).not.toContain(NATIVE_CHART_ID)
    })

    it(`${cap.name}: chart_id in required_inputs`, () => {
      expect(cap.required_inputs).toContain('chart_id')
    })

    it(`${cap.name}: handler is a function`, () => {
      expect(typeof cap.handler).toBe('function')
    })
  }
})

describe('D5 L4 Phala — handler: chart_id absent → is_error', () => {
  for (const cap of ALL_L4_CAPS) {
    it(`${cap.name}: is_error when chart_id missing`, async () => {
      const result = await cap.handler({}, undefined)
      expect(result.is_error).toBe(true)
    })
  }
})

describe('D5 L4 Phala — specific constraints', () => {
  it('query_predictive_anchors: tool_role = umbrella (L4 entry point)', () => {
    expect(queryPredictiveAnchorsCapability.tool_role).toBe('umbrella')
  })

  it('query_predictive_anchors: has drill_children', () => {
    expect(queryPredictiveAnchorsCapability.drill_children).toContain('marsys://tool/L4/query_domain_result')
    expect(queryPredictiveAnchorsCapability.drill_children).toContain('marsys://tool/L4/query_falsifiers')
  })

  it('query_domain_result: description mentions 13 rows by design', () => {
    // ADHIṢṬHĀNA Lane A7: was '7 rows' — stale since SHABDA-SHUDDHI Lane L5 Fix 5 extended
    // ph_phaladesa.py to write all 13 canonical domains (see query_domain_result.ts header).
    expect(queryDomainResultCapability.description).toContain('13 rows')
  })

  it('query_rectification: emits_references = false (meta-analysis, not signal ref)', () => {
    expect(queryRectificationCapability.emits_references).toBe(false)
  })

  it('query_rectification: description mentions NO-AUTO-OVERRIDE', () => {
    expect(queryRectificationCapability.description).toContain('NO-AUTO-OVERRIDE')
  })

  it('query_anomaly_flags: archetype = calibration', () => {
    expect(queryAnomalyFlagsCapability.archetype).toBe('calibration')
  })

  it('query_falsifiers: emits_references = true (prediction_id refs)', () => {
    expect(queryFalsifiersCapability.emits_references).toBe(true)
  })
})
