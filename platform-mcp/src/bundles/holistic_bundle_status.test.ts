/**
 * holistic_bundle_status.test.ts — ŚODHANA T2 (MC-002).
 *
 * Acceptance criterion: the bundle returns status: 'degraded' (and ok:false)
 * under an INJECTED sub-tool failure — it must be structurally impossible to
 * return ok:true while a majority of constituents errored.
 *
 * Anti-vacuous: the induced failure must actually flip the envelope. We drive
 * executeHolisticBundle with a mocked global.fetch that rejects the live-DB
 * primitives, and assert the settled envelope status.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { executeHolisticBundle } from './holistic_bundle.js'

const principal = { user_uid: 'test-user', key_id: 'test-key' }

function okResponse(body: unknown) {
  return { ok: true, status: 200, json: async () => body } as unknown as Response
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('executeHolisticBundle envelope health — MC-002', () => {
  it('returns status:degraded / ok:false when ALL sub-tools error (injected failure)', async () => {
    // Reject every primitive call; cache lookup/store swallow errors (non-fatal → miss).
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (String(url).includes('/cache/lookup')) return okResponse({ hit: false })
      if (String(url).includes('/cache/store')) return okResponse({ stored: true })
      throw new Error('HTTP 500') // every /primitives/* call fails
    }))

    const env = await executeHolisticBundle(
      { query_text: 'q', tier: 'native', chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
      principal,
    )

    expect(env.status).toBe('degraded')
    expect(env.ok).toBe(false)
    expect(env.provenance.sub_tools_errored.length).toBeGreaterThanOrEqual(5)
  })

  it('returns status:partial / ok:true when a MINORITY errors (read_asset ok, one DB primitive fails)', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      const u = String(url)
      if (u.includes('/cache/lookup')) return okResponse({ hit: false })
      if (u.includes('/cache/store')) return okResponse({ stored: true })
      if (u.includes('/primitives/read_asset')) return okResponse({ result: { rows: [1] } })
      throw new Error('HTTP 500')
    }))

    // subset: UCN/RM/CDLM route to read_asset (succeed), MSR routes to query_signals (fails) → 1/4 = 25%
    const env = await executeHolisticBundle(
      { query_text: 'q', tier: 'native', chart_id: '482012f1-710e-4a25-994a-93821f5871aa', subset: ['UCN', 'RM', 'CDLM', 'MSR'] },
      principal,
    )

    expect(env.status).toBe('partial')
    expect(env.ok).toBe(true)
    expect(env.provenance.sub_tools_errored).toEqual(['MSR'])
  })

  it('returns status:ok / ok:true when NO sub-tool errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      const u = String(url)
      if (u.includes('/cache/lookup')) return okResponse({ hit: false })
      if (u.includes('/cache/store')) return okResponse({ stored: true })
      return okResponse({ result: { rows: [1] } }) // every primitive succeeds
    }))

    const env = await executeHolisticBundle(
      { query_text: 'q', tier: 'native', chart_id: '482012f1-710e-4a25-994a-93821f5871aa', subset: ['UCN', 'RM'] },
      principal,
    )

    expect(env.status).toBe('ok')
    expect(env.ok).toBe(true)
    expect(env.provenance.sub_tools_errored).toEqual([])
  })
})
