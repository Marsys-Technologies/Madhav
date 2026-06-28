/**
 * D7 Channel Gate Test
 * ====================
 * Verifies that all D7_CAPABILITY_URIS are registered and pass the
 * chart-agnostic gate (7 rules). Runs as part of CI.
 *
 * GATE A: only tests the per-wave registration; does not re-test L0-L5 caps.
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { registerD7ChannelCapabilities, D7_CAPABILITY_URIS } from '../register_d7_channel'
import { clearRegistry, getAllCapabilities, hasCapability } from '../../index'
import { checkAllCapabilities } from '../../chart_agnostic_gate'

describe('D7 Channel — capability registration gate', () => {
  beforeAll(() => {
    clearRegistry()
    registerD7ChannelCapabilities()
  })

  it('registers all 17 D7 URIs', () => {
    for (const uri of D7_CAPABILITY_URIS) {
      expect(hasCapability(uri), `Missing capability: ${uri}`).toBe(true)
    }
    expect(D7_CAPABILITY_URIS.length).toBe(17)
  })

  it('all D7 capabilities pass the chart-agnostic gate (7 rules)', () => {
    const allCaps = getAllCapabilities()
    const d7Caps = allCaps.filter(c => (D7_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    const violations = checkAllCapabilities(d7Caps)
    expect(violations, violations.map(v => `${v.uri}: ${v.rule}`).join('\n')).toHaveLength(0)
  })

  it('per_chart caps require chart_id in required_inputs', () => {
    const allCaps = getAllCapabilities()
    const d7Caps = allCaps.filter(c => (D7_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    const perChartCaps = d7Caps.filter(c => c.scope === 'per_chart')
    for (const cap of perChartCaps) {
      expect(
        cap.required_inputs?.includes('chart_id'),
        `${cap.uri} is per_chart but required_inputs missing chart_id`
      ).toBe(true)
    }
    // Expect 3 per_chart: classical_attribution_lookup, chart_facts_query, query_remedies_for_chart
    expect(perChartCaps.length).toBe(3)
  })

  it('global caps do not require chart_id', () => {
    const allCaps = getAllCapabilities()
    const d7Caps = allCaps.filter(c => (D7_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    const globalCaps = d7Caps.filter(c => c.scope === 'global')
    for (const cap of globalCaps) {
      expect(
        cap.required_inputs?.includes('chart_id') ?? false,
        `${cap.uri} is global but has chart_id in required_inputs`
      ).toBe(false)
    }
  })

  it('no native identifiers in any D7 description or URI', () => {
    const NATIVE_ID = '482012f1-710e-4a25-994a-93821f5871aa'
    const NATIVE_NAMES = ['Abhisek Mohanty', '1984-02-05', 'Bhubaneswar']
    const allCaps = getAllCapabilities()
    const d7Caps = allCaps.filter(c => (D7_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    for (const cap of d7Caps) {
      const text = `${cap.description} ${cap.name} ${cap.uri}`
      expect(text, `Native chart_id found in ${cap.uri}`).not.toContain(NATIVE_ID)
      for (const n of NATIVE_NAMES) {
        expect(cap.description, `Native identifier '${n}' found in ${cap.uri}`).not.toContain(n)
      }
    }
  })

  it('Wave C — chart_facts_query is per_chart, emits_references, L1', () => {
    const allCaps = getAllCapabilities()
    const cap = allCaps.find(c => c.uri === 'marsys://tool/L1/chart_facts_query')
    expect(cap).toBeDefined()
    expect(cap!.scope).toBe('per_chart')
    expect(cap!.emits_references).toBe(true)
    expect(cap!.layer).toBe('L1')
  })

  it('Wave D — query_remedies_for_chart is per_chart', () => {
    const allCaps = getAllCapabilities()
    const cap = allCaps.find(c => c.uri === 'marsys://tool/L0/query_remedies_for_chart')
    expect(cap).toBeDefined()
    expect(cap!.scope).toBe('per_chart')
    expect(cap!.required_inputs).toContain('chart_id')
    expect(cap!.required_inputs).toContain('affliction')
  })

  it('Wave E — find_verses_about is global, prose_citation archetype', () => {
    const allCaps = getAllCapabilities()
    const cap = allCaps.find(c => c.uri === 'marsys://tool/L0/find_verses_about')
    expect(cap).toBeDefined()
    expect(cap!.scope).toBe('global')
    expect(cap!.archetype).toBe('prose_citation')
    expect(cap!.required_inputs).toContain('topic')
  })
})
