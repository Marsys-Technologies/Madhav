/**
 * D5 wave — L5 Mīmāṃsā new capabilities: descriptor + gate tests
 * ================================================================
 * Tests the 3 new L5 capabilities added by D5:
 *   query_predictions, query_signal_families, query_manifestation_grammar
 *
 * [verify-against: prod] — live DB queries require L5 build.
 */

import { describe, it, expect } from 'vitest'
import { checkCapability } from '../../../chart_agnostic_gate'
import { queryPredictionsCapability }        from '../query_predictions'
import { querySignalFamiliesCapability }     from '../query_signal_families'
import { queryManifestationGrammarCapability } from '../query_manifestation_grammar'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const ALL_D5_L5_CAPS = [
  queryPredictionsCapability,
  querySignalFamiliesCapability,
  queryManifestationGrammarCapability,
]

describe('D5 L5 Mīmāṃsā — chart_agnostic_gate', () => {
  for (const cap of ALL_D5_L5_CAPS) {
    it(`${cap.name}: 0 gate violations`, () => {
      const violations = checkCapability(cap)
      expect(violations, JSON.stringify(violations)).toHaveLength(0)
    })
  }
})

describe('D5 L5 Mīmāṃsā — D1 contract fields', () => {
  for (const cap of ALL_D5_L5_CAPS) {
    it(`${cap.name}: has all required D1 topology fields`, () => {
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
  }
})

describe('D5 L5 Mīmāṃsā — scope enforcement', () => {
  it('query_predictions: scope = per_chart, chart_id required', () => {
    expect(queryPredictionsCapability.scope).toBe('per_chart')
    expect(queryPredictionsCapability.required_inputs).toContain('chart_id')
  })

  it('query_signal_families: scope = global (no chart_id)', () => {
    expect(querySignalFamiliesCapability.scope).toBe('global')
    expect(querySignalFamiliesCapability.required_inputs ?? []).not.toContain('chart_id')
  })

  it('query_manifestation_grammar: scope = per_chart, chart_id required', () => {
    expect(queryManifestationGrammarCapability.scope).toBe('per_chart')
    expect(queryManifestationGrammarCapability.required_inputs).toContain('chart_id')
  })
})

describe('D5 L5 Mīmāṃsā — handler: chart_id absent → is_error', () => {
  it('query_predictions: is_error when chart_id missing', async () => {
    const result = await queryPredictionsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('query_manifestation_grammar: is_error when chart_id missing', async () => {
    const result = await queryManifestationGrammarCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })
})

describe('D5 L5 Mīmāṃsā — specific properties', () => {
  it('query_predictions: emits_references = true (prediction_id → ph_pramana)', () => {
    expect(queryPredictionsCapability.emits_references).toBe(true)
  })

  // NIRMĀṆA L5 W3-3: this used to assert the description contained the literal '50 rows'.
  // That count was a wrapper-local constant shadowing a live value (§N.7 item 3) and had
  // drifted (live 2026-09-05: 139 canonical / 56 Abhinandan). The assertion now pins the
  // SHAPE claim the description is actually responsible for, and forbids the regression:
  // any hardcoded row count coming back into this prose.
  it('query_predictions: description describes sparsity by shape, not by a pinned row count', () => {
    expect(queryPredictionsCapability.description).toContain('sparse')
    expect(queryPredictionsCapability.description).toContain('total_matching')
    expect(queryPredictionsCapability.description).not.toMatch(/\b\d+ rows per chart\b/)
  })

  it('query_signal_families: emits_references = false (global catalog)', () => {
    expect(querySignalFamiliesCapability.emits_references).toBe(false)
  })

  it('query_manifestation_grammar: emits_references = true (signal_id back to bo_laksana)', () => {
    expect(queryManifestationGrammarCapability.emits_references).toBe(true)
  })

  it('query_manifestation_grammar: archetype = calibration', () => {
    expect(queryManifestationGrammarCapability.archetype).toBe('calibration')
  })
})
