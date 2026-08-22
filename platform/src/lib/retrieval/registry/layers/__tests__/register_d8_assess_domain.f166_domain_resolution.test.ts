/**
 * register_d8_assess_domain.f166_domain_resolution.test.ts — F-166a regression.
 *
 * THE DEFECT: none of the four assess_* tools (assess_marriage/career/health/wealth) ever
 * disclosed which CANONICAL signal domain their domain-scoped legs (house_analysis,
 * bearing_yoga_firings, gochara_sweep, contradictions) were actually queried with. The file
 * already imports `SHASTRA_MAP` (register_d9_judgment.ts's F-57 vocabulary), but
 * `grep domain_resolution register_d8_assess_domain.ts` returned zero hits before this fix —
 * so assess_marriage's silent `domain: 'relationship'` alias (the handler literal) was
 * invisible on the wire, exactly the same disclosure gap F-57 closed for judgment_query.
 *
 * This suite asserts every assess_* response now carries a `domain_resolution` block with
 * the correct `requested` (the tool-name domain word) / `resolved_signal_domain` (the
 * canonical tag actually queried), and that assess_marriage specifically fires the
 * `domain_resolution_aliased` judgment flag (the other three happen to be exact matches).
 *
 * Mocking pattern copied from register_d8_verdict_skeleton.test.ts (same file, same
 * established mock shape for the four sub-capabilities + db client) — domain_resolution is
 * computed independently of those sub-capability results, but the full handler must still
 * run to completion (is_error: false) to reach the return statement that carries it.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

const domainReadingHandler = vi.fn()
const temporalHandler = vi.fn()
const contradictionsHandler = vi.fn()
const signalsHandler = vi.fn()

vi.mock('../L2_bodha/query_domain_reading', () => ({
  queryDomainReadingCapability: { handler: (...a: unknown[]) => domainReadingHandler(...a) },
}))
vi.mock('../L3_kala/query_temporal_activation', () => ({
  queryTemporalActivationCapability: { handler: (...a: unknown[]) => temporalHandler(...a) },
}))
vi.mock('../L2_bodha/query_contradictions', () => ({
  queryContradictionsCapability: { handler: (...a: unknown[]) => contradictionsHandler(...a) },
}))
vi.mock('../L2_bodha/query_signals', () => ({
  querySignalsCapability: { handler: (...a: unknown[]) => signalsHandler(...a) },
}))

import { clearRegistry, getCapability } from '../../index'
import { registerD8AssessDomainCapabilities } from '../register_d8_assess_domain'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function sig(id: string, cls: string, sss = 'structural') {
  return {
    signal_id: id,
    signal_type_class: cls,
    source_subsystem: sss,
    signal_summary_text: `summary-${id}`,
    computed_salience: 0.5,
  }
}

beforeEach(() => {
  queryMock.mockReset()
  domainReadingHandler.mockReset()
  temporalHandler.mockReset()
  contradictionsHandler.mockReset()
  signalsHandler.mockReset()

  domainReadingHandler.mockResolvedValue({
    is_error: false,
    content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [], lens_count: 0 },
  })
  temporalHandler.mockResolvedValue({
    is_error: false,
    content: { activations: [], predicates: [], activation_count: 0, signal_id_refs: [] },
  })
  contradictionsHandler.mockResolvedValue({
    is_error: false,
    content: { contradiction_count: 0, discoveries: [] },
  })
  signalsHandler.mockResolvedValue({
    is_error: false,
    content: {
      signals: Array.from({ length: 10 }, (_, i) => sig(`comp-${i}`, 'composite_state')),
      ranking_basis: { mode: 'composite', priors_version: '1.0', domain: 'career' },
    },
  })
  queryMock.mockImplementation(async (sql: string) => {
    if (String(sql).includes('brahma_vichara_constants')) {
      return {
        rows: [{
          value_jsonb: {
            wealth:   { vargas: ['D1', 'D2', 'D9', 'D11'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
            career:   { vargas: ['D1', 'D10', 'D9'], provisional: true, houses: [10], karaka: 'Saturn' },
            marriage: { vargas: ['D1', 'D9', 'D7'], provisional: true, houses: [7], karaka: 'Venus' },
            health:   { vargas: ['D1', 'D6', 'D9'], provisional: true, houses: [6], karaka: 'Saturn' },
            general:  { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
          },
        }],
      }
    }
    return { rows: [] }
  })
})

async function runAssess(uri: string) {
  clearRegistry()
  registerD8AssessDomainCapabilities()
  const cap = getCapability(uri)
  expect(cap, `capability ${uri} should be registered`).toBeDefined()
  const res = await cap!.handler({ chart_id: CHART_ID }, undefined)
  expect(res.is_error, `expected ${uri} to succeed: ${JSON.stringify(res.content)}`).toBe(false)
  return res.content as Record<string, unknown>
}

describe('F-166a — assess_* domain_resolution disclosure', () => {
  it('assess_marriage: requested="marriage", resolved_signal_domain="relationship", is_exact=false', async () => {
    const content = await runAssess('marsys://tool/L-DOMAIN/assess_marriage')
    const dr = content['domain_resolution'] as Record<string, unknown>
    expect(dr).toBeDefined()
    expect(dr['requested']).toBe('marriage')
    expect(dr['resolved_signal_domain']).toBe('relationship')
    expect(dr['is_exact']).toBe(false)
    expect(dr['is_canonical']).toBe(true)
  })

  it('assess_marriage fires domain_resolution_aliased', async () => {
    const content = await runAssess('marsys://tool/L-DOMAIN/assess_marriage')
    const flags = content['judgment_flags'] as Array<Record<string, unknown>>
    const flag = flags.find(f => f['code'] === 'domain_resolution_aliased')
    expect(flag, `judgment_flags: ${JSON.stringify(flags)}`).toBeDefined()
    expect(String(flag!['detail'] ?? '')).toMatch(/marriage/)
    expect(String(flag!['detail'] ?? '')).toMatch(/relationship/)
  })

  it('assess_career: requested="career", resolved_signal_domain="career", is_exact=true, no aliased flag', async () => {
    const content = await runAssess('marsys://tool/L-DOMAIN/assess_career')
    const dr = content['domain_resolution'] as Record<string, unknown>
    expect(dr['requested']).toBe('career')
    expect(dr['resolved_signal_domain']).toBe('career')
    expect(dr['is_exact']).toBe(true)
    const flags = content['judgment_flags'] as Array<Record<string, unknown>>
    expect(flags.find(f => f['code'] === 'domain_resolution_aliased')).toBeUndefined()
  })

  it('assess_health: requested="health", resolved_signal_domain="health", is_exact=true', async () => {
    const content = await runAssess('marsys://tool/L-DOMAIN/assess_health')
    const dr = content['domain_resolution'] as Record<string, unknown>
    expect(dr['requested']).toBe('health')
    expect(dr['resolved_signal_domain']).toBe('health')
    expect(dr['is_exact']).toBe(true)
  })

  it('assess_wealth: requested="wealth", resolved_signal_domain="wealth", is_exact=true', async () => {
    const content = await runAssess('marsys://tool/L-DOMAIN/assess_wealth')
    const dr = content['domain_resolution'] as Record<string, unknown>
    expect(dr['requested']).toBe('wealth')
    expect(dr['resolved_signal_domain']).toBe('wealth')
    expect(dr['is_exact']).toBe(true)
  })
})
