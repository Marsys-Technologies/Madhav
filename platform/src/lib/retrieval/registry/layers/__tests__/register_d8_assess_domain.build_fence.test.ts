/**
 * assess_* mandatory served-generation fence (Pūrṇa R3 / review RC-1, RC-2).
 *
 * assess_* composes L1 chart facts and L2 derived stores. Every read it makes directly, and
 * every read of a composed handler that accepts a fence, must be restricted to the chart's served
 * generation (each asset's own writing run), and a chart with no resolvable generation must
 * fail closed instead of falling through to unfenced reads.
 *
 * Known residual (L3 Kāla ownership, deliberately untouched): query_temporal_activation reads
 * bodha_msr_signals without a fence. The temporal handler is mocked here, so these tests do not
 * cover it.
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
import { registerD8AssessDomainCapabilities, buildVargaAnalysisDirect } from '../register_d8_assess_domain'
import { ExplicitEmptyBuildFenceError } from '@/lib/retrieval/registry/generation/served_generation'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'
const SHARED = '33333333-3333-4333-8333-333333333333'

function receiptRow(asset_id: string, overrides: Record<string, unknown> = {}) {
  return {
    asset_id, chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: SERVED, rows_build_id: SERVED, receipt_state: 'proven', freshness_state: 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64), spec_active: true, receipt_run_state: 'completed',
    receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    ...overrides,
  }
}

const OPERATIVE_VARGAS = {
  wealth: { vargas: ['D1', 'D2'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
  career: { vargas: ['D1', 'D10'], provisional: true, houses: [10], karaka: 'Saturn' },
  marriage: { vargas: ['D1', 'D9'], provisional: true, houses: [7], karaka: 'Venus' },
  health: { vargas: ['D1', 'D6'], provisional: true, houses: [6], karaka: 'Saturn' },
  general: { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
}

function installRouter(receipts: Record<string, unknown>[]) {
  queryMock.mockImplementation(async (sql: string) => {
    const s = String(sql)
    if (s.includes('FROM asset_provenance_receipts receipt')) return { rows: receipts }
    if (s.includes('brahma_vichara_constants')) return { rows: [{ value_jsonb: OPERATIVE_VARGAS }] }
    return { rows: [] }
  })
}

async function run(tool = 'assess_wealth') {
  const cap = getCapability(`marsys://tool/L-DOMAIN/${tool}`)
  expect(cap).toBeDefined()
  return cap!.handler({ chart_id: CHART_ID }, undefined) as Promise<{ content: Record<string, unknown>; is_error: boolean }>
}

/** Every chart_facts / bodha_* read issued, with the fence (last array param) it carried. */
function derivedReads(): Array<{ sql: string; fence: unknown }> {
  return queryMock.mock.calls
    .map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
    .filter(({ sql }) => /FROM (chart_facts|bodha_)/.test(sql))
    .map(({ sql, params }) => ({ sql, fence: [...params].reverse().find((param) => Array.isArray(param)
      && param.every((item) => typeof item === 'string' && /^[0-9a-f-]{36}$/.test(item))) }))
}

beforeEach(() => {
  queryMock.mockReset()
  for (const handler of [domainReadingHandler, temporalHandler, contradictionsHandler, signalsHandler, yogaFiringsHandler]) {
    handler.mockReset()
  }
  domainReadingHandler.mockResolvedValue({ is_error: false, content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [] } })
  temporalHandler.mockResolvedValue({ is_error: false, content: { activations: [], predicates: [], signal_id_refs: [] } })
  contradictionsHandler.mockResolvedValue({ is_error: false, content: { contradictions: [], discoveries: [] } })
  signalsHandler.mockResolvedValue({ is_error: false, content: { signals: [] } })
  yogaFiringsHandler.mockResolvedValue({ is_error: false, content: { rows: [] } })
  clearRegistry()
  registerD8AssessDomainCapabilities()
})

describe('assess_* served-generation fence', () => {
  it('fails closed before any leg when no chart receipt resolves to a served generation', async () => {
    installRouter([receiptRow('ga_structural', { freshness_state: 'stale' })])
    const result = await run()
    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({
      code: 'no_served_generation',
      unresolved_assets: [{ asset_id: 'ga_structural', reason: 'receipt_not_fresh' }],
    })
    expect(domainReadingHandler).not.toHaveBeenCalled()
    expect(derivedReads()).toEqual([])
  })

  it('fails closed when served-generation resolution itself errors', async () => {
    queryMock.mockRejectedValue(new Error('receipts unavailable'))
    const result = await run('assess_marriage')
    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({ code: 'served_generation_resolution_failed' })
    expect(domainReadingHandler).not.toHaveBeenCalled()
  })

  it('fences every direct read and every fence-accepting leg to the served build set', async () => {
    installRouter([receiptRow('ga_structural'), receiptRow('bo_samvada')])
    const result = await run()
    expect(result.is_error).toBe(false)

    for (const handler of [domainReadingHandler, signalsHandler, yogaFiringsHandler]) {
      expect(handler).toHaveBeenCalled()
      expect(handler.mock.calls[0]![0]).toMatchObject({ build_id: [SERVED] })
    }
    const reads = derivedReads()
    expect(reads.length).toBeGreaterThan(0)
    // No chart-fact or derived-store read escapes the fence.
    for (const read of reads) {
      expect(read.sql).toMatch(/build_id = ANY\(\$\d+::uuid\[\]\)/)
      expect(read.fence).toEqual([SERVED])
    }
    expect(reads.some(({ sql }) => sql.includes('FROM bodha_msr_signals'))).toBe(true)
    expect(reads.some(({ sql }) => sql.includes("'graha_dignity_per_varga'"))).toBe(true)
    expect(result.content['generation_provenance']).toMatchObject({
      selection: 'per_asset_served_generation',
      served_build_ids: [SERVED],
    })
  })

  it('flags a contradictions leg that resolved a different served generation mid-request', async () => {
    installRouter([receiptRow('ga_structural')])
    contradictionsHandler.mockResolvedValue({
      is_error: false,
      content: { contradictions: [], discoveries: [], generation_provenance: { generation_hash: 'sha256:a-newer-generation' } },
    })
    const mixed = await run()
    const flags = mixed.content['judgment_flags'] as Array<{ code: string }>
    expect(flags.map((entry) => entry.code)).toContain('served_generation_changed_mid_request')

    const sameGeneration = (mixed.content['generation_provenance'] as { generation_hash: string }).generation_hash
    contradictionsHandler.mockResolvedValue({
      is_error: false,
      content: { contradictions: [], discoveries: [], generation_provenance: { generation_hash: sameGeneration } },
    })
    const consistent = await run()
    expect((consistent.content['judgment_flags'] as Array<{ code: string }>).map((entry) => entry.code))
      .not.toContain('served_generation_changed_mid_request')
  })

  it('discloses unresolved and withheld assets instead of reading their runs', async () => {
    installRouter([
      receiptRow('ga_structural'),
      receiptRow('ga_vichara', { rows_build_id: SHARED, receipt_build_id: SHARED }),
      receiptRow('ga_strength', { rows_build_id: SHARED, receipt_build_id: SHARED, freshness_state: 'stale' }),
    ])
    const result = await run('assess_career')
    expect(result.is_error).toBe(false)
    const flags = result.content['judgment_flags'] as Array<{ code: string; detail: string }>
    const flag = flags.find((entry) => entry.code === 'served_generation_unresolved_assets')
    expect(flag?.detail).toContain('ga_strength (receipt_not_fresh)')
    expect(flag?.detail).toContain('ga_vichara')
    for (const read of derivedReads()) expect(read.fence).toEqual([SERVED])
    expect(domainReadingHandler.mock.calls[0]![0]).toMatchObject({ build_id: [SERVED] })
  })

  // Independent review finding: buildVargaAnalysisDirect's outer catch was the one composite
  // caller in this session's build-fence migration whose catch block did NOT rethrow
  // ExplicitEmptyBuildFenceError (fetchInduLagna's own catch, a few lines up in the same file,
  // already did) — structurally unreachable through the full assess_* handler (its own
  // served-generation gate above already guarantees a non-empty build_id by the time this
  // runs), so this calls the exported function directly, per the R3 boundary ruling's "at
  // least one judgment/checklist caller" test requirement.
  it('throws (never degrades to a generic "direct consumption failed" note) on an explicit-empty build fence', async () => {
    installRouter([receiptRow('ga_structural')])
    // Warm the module-level DOMAIN_DIRECT_VARGAS cache via the full handler once, then call
    // buildVargaAnalysisDirect directly with an explicit-empty fence.
    await run()
    await expect(buildVargaAnalysisDirect(CHART_ID, 'lahiri_chitrapaksha', 'wealth', []))
      .rejects.toThrow(ExplicitEmptyBuildFenceError)
  })
})
