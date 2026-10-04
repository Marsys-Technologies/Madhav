/**
 * register_d8_assess_domain.l2_lineage_flag.test.ts — N-91 echo-class disclosure, assess_* wiring.
 *
 * assess_* has NO reading_contract on the wire; the lineage flag reaches the caller in
 * content.judgment_flags -> kernel.flags (and is floored there by KERNEL_FLOOR_FLAG_CODES, tested in
 * platform-mcp). This runs the REAL assess handler with composed legs mocked (register_d8 build_fence
 * pattern) and the REAL detector over a SQL-routed `query` mock, plus the optional
 * `lineageStale` input of buildVerdictLayer (overview clause `grounded`).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

const domainReadingHandler = vi.fn()
const temporalHandler = vi.fn()
const contradictionsHandler = vi.fn()
const signalsHandler = vi.fn()
const yogaFiringsHandler = vi.fn()

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
vi.mock('../L1_ganita/get_yoga_firings', () => ({
  getYogaFiringsCapability: { handler: (...a: unknown[]) => yogaFiringsHandler(...a) },
}))

import { clearRegistry, getCapability } from '../../index'
import { registerD8AssessDomainCapabilities, buildVerdictLayer } from '../register_d8_assess_domain'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'

function receiptRow(asset_id: string) {
  return {
    asset_id, chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: SERVED, rows_build_id: SERVED, receipt_state: 'proven', freshness_state: 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64), spec_active: true, receipt_run_state: 'completed',
    receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
  }
}

const OPERATIVE_VARGAS = {
  wealth: { vargas: ['D1', 'D2'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
  career: { vargas: ['D1', 'D10'], provisional: true, houses: [10], karaka: 'Saturn' },
  marriage: { vargas: ['D1', 'D9'], provisional: true, houses: [7], karaka: 'Venus' },
  health: { vargas: ['D1', 'D6'], provisional: true, houses: [6], karaka: 'Saturn' },
  general: { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
}

type Lineage = 'stale' | 'current' | 'error'

function installRouter(lineage: Lineage) {
  queryMock.mockImplementation(async (sql: string) => {
    const s = String(sql)
    if (s.includes('asset_output_digest_specs') && s.includes('l1_pins')) {
      if (lineage === 'error') throw new Error('permission denied for table asset_provenance_receipts')
      return {
        rows: [
          { asset_id: 'ga_structural', chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_state: 'proven', observed_at: new Date('2026-10-04T10:00:00Z'), output_digest: lineage === 'stale' ? 'NEW' : 'PINNED', spec_active: true, registry_current: true, l1_pins: null },
          { asset_id: 'bo_laksana', chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_state: 'proven', observed_at: new Date('2026-09-08T18:22:33Z'), output_digest: 'l2', spec_active: true, registry_current: true,
            l1_pins: [{ asset_id: 'ga_structural', output_digest: 'PINNED', observed_at: '2026-09-07T08:37:20Z' }] },
        ],
      }
    }
    if (s.includes('FROM asset_provenance_receipts receipt')) return { rows: [receiptRow('ga_structural')] }
    if (s.includes('brahma_vichara_constants')) return { rows: [{ value_jsonb: OPERATIVE_VARGAS }] }
    return { rows: [] }
  })
}

async function run(tool = 'assess_career') {
  const cap = getCapability(`marsys://tool/L-DOMAIN/${tool}`)
  expect(cap).toBeDefined()
  return cap!.handler({ chart_id: CHART_ID }, undefined) as Promise<{ content: Record<string, unknown>; is_error: boolean }>
}
const codesOf = (c: Record<string, unknown>) => (c['judgment_flags'] as Array<{ code: string } | string>).map(f => (typeof f === 'string' ? f : f.code))

beforeEach(() => {
  queryMock.mockReset()
  for (const handler of [domainReadingHandler, temporalHandler, contradictionsHandler, signalsHandler, yogaFiringsHandler]) handler.mockReset()
  domainReadingHandler.mockResolvedValue({ is_error: false, content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [] } })
  temporalHandler.mockResolvedValue({ is_error: false, content: { activations: [], predicates: [], signal_id_refs: [] } })
  contradictionsHandler.mockResolvedValue({ is_error: false, content: { contradictions: [], discoveries: [] } })
  signalsHandler.mockResolvedValue({ is_error: false, content: { signals: [] } })
  yogaFiringsHandler.mockResolvedValue({ is_error: false, content: { rows: [] } })
  clearRegistry()
  registerD8AssessDomainCapabilities()
})

describe('assess_* — L2 lineage flag wiring (kernel.flags source)', () => {
  it.each(['assess_career', 'assess_health', 'assess_marriage', 'assess_wealth'])('%s: stale L2 pin -> l2_receipts_predate_l1 in judgment_flags', async (tool) => {
    installRouter('stale')
    const r = await run(tool)
    expect(r.is_error).toBe(false)
    const flags = r.content['judgment_flags'] as Array<{ code: string; detail?: string }>
    const f = flags.find(x => x.code === 'l2_receipts_predate_l1')
    expect(f).toBeDefined()
    expect(f!.detail).toContain('bo_laksana')
    expect(codesOf(r.content)).not.toContain('l2_lineage_check_failed')
  })

  it('current pin: no lineage flag', async () => {
    installRouter('current')
    const r = await run()
    expect(r.is_error).toBe(false)
    expect(codesOf(r.content)).not.toContain('l2_receipts_predate_l1')
    expect(codesOf(r.content)).not.toContain('l2_lineage_check_failed')
  })

  it('detector error: fail closed — l2_lineage_check_failed, assessment still serves', async () => {
    installRouter('error')
    const r = await run()
    expect(r.is_error).toBe(false)
    expect(codesOf(r.content)).toContain('l2_lineage_check_failed')
    expect(codesOf(r.content)).not.toContain('l2_receipts_predate_l1')
  })

  it('the served verdict overview clause reads grounded:false (ids still cited) when the flag is served, and grounded as before when not', async () => {
    const signal = { signal_id: 'SIG.MSR.1', signal_type_class: 'yoga', constituent_facts_array: ['fact-a', 'fact-b'], computed_salience: 0.9 }
    signalsHandler.mockResolvedValue({ is_error: false, content: { signals: [signal], returned_count: 1 } })
    const overview = (r: { content: Record<string, unknown> }) => {
      const clauses = (r.content['verdict'] as { clauses: Array<{ clause_id?: string; grounded: boolean; fact_ids: string[] }> }).clauses
      return clauses.find(c => c.clause_id === 'overview')!
    }
    installRouter('stale')
    const stale = overview(await run())
    installRouter('current')
    const fine = overview(await run())
    // Only meaningful if the fixture actually reached the overview with ids; assert that explicitly.
    expect(fine.fact_ids.length).toBeGreaterThan(0)
    expect(fine.grounded).toBe(true)
    expect(stale.fact_ids).toEqual(fine.fact_ids)
    expect(stale.grounded).toBe(false)
  })
})

describe('buildVerdictLayer — lineageStale (overview clause grounded)', () => {
  const BASE = {
    domain_label: 'Career',
    top10: [{ constituent_fact_ids: ['f1', 'f2'] }] as Array<Record<string, unknown>>,
    bearingYogaFirings: [] as Array<Record<string, unknown>>,
    domainMatchedYogaFactIds: [] as string[],
    vargaAnalysis: {} as Record<string, unknown>,
    contradictions: { status: 'no_contradictions_in_domain' } as Record<string, unknown>,
    chartWideContradictionCount: 0,
    temporalOk: false,
    stageTemporalCount: 0,
  }
  const overview = (v: ReturnType<typeof buildVerdictLayer>) => v.clauses.find(c => c.clause_id === 'overview')!

  it('unset (existing callers): grounded when it cites ids', () => {
    expect(overview(buildVerdictLayer(BASE)).grounded).toBe(true)
  })
  it('lineageStale false: unchanged', () => {
    expect(overview(buildVerdictLayer({ ...BASE, lineageStale: false })).grounded).toBe(true)
  })
  it('lineageStale true: grounded false, ids still cited (never dropped)', () => {
    const c = overview(buildVerdictLayer({ ...BASE, lineageStale: true }))
    expect(c.grounded).toBe(false)
    expect(c.fact_ids).toEqual(['f1', 'f2'])
  })
  it('no ids and not stale: grounded false as before', () => {
    expect(overview(buildVerdictLayer({ ...BASE, top10: [] })).grounded).toBe(false)
  })
})
