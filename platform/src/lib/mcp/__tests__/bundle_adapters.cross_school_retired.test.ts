/**
 * bundle_adapters.cross_school_retired.test.ts — SS N-370: the live multi-school bundle's
 * `cross_school_lookup` slot is an explicit NOT_AVAILABLE entry, not a call that answers HTTP 400.
 * ============================================================================================
 * Defect: executeMultiSchoolBundle issued `runSubTool('cross_school_lookup', 'cross_school_lookup', ...)`.
 * The primitive was removed from the whitelist by WP-1.7 (no backing registry capability), so the
 * primitives route answers 400 and the entry was reported as an ERROR (`errored: true`,
 * `error_class: 'validation_error'`) on every bundle call, which also counted against the bundle health.
 *
 * DB-free: global fetch is stubbed; the stub answers 400 for any tool that is not whitelisted (as the
 * real route does for cross_school_lookup) and 200 for the school evidence calls.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u-1', audience_tier: 'client', key_id: 'k-1' }

interface Recorded { toolName: string; body: Record<string, unknown> }

function stubFetch(opts: { schoolStatus?: number } = {}): { calls: Recorded[] } {
  const calls: Recorded[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/api/mcp/bundles/cache/store')) return { ok: true, status: 200, json: async () => ({ ok: true }) }
    const raw = init?.body ? JSON.parse(String(init.body)) as Record<string, unknown> : {}
    const body = (raw['params'] as Record<string, unknown>) ?? raw
    const toolName = url.split('/api/mcp/primitives/')[1] ?? 'unknown'
    calls.push({ toolName, body })
    if (toolName === 'cross_school_lookup') {
      return { ok: false, status: 400, json: async () => ({ ok: false, error: { class: 'validation', message: `Tool not in surgical whitelist: ${toolName}` } }) }
    }
    const status = opts.schoolStatus ?? 200
    if (status !== 200) return { ok: false, status, json: async () => ({ ok: false, error: { class: 'upstream', message: 'down' } }) }
    return { ok: true, status: 200, json: async () => ({ ok: true, result: { rows: [{ k: 1 }] } }) }
  }))
  return { calls }
}

async function run(params: Record<string, unknown> = {}) {
  const { executeMultiSchoolBundle } = await import('../bundle_adapters')
  const events: Array<Record<string, unknown>> = []
  let envelope: Record<string, unknown> | undefined
  await executeMultiSchoolBundle(
    { claim: 'career', tier: 'client', chart_id: CHART_ID, ...params },
    PRINCIPAL,
    (event) => {
      events.push(event as unknown as Record<string, unknown>)
      if (event.type === 'bundle.completed') envelope = (event as unknown as { envelope: Record<string, unknown> }).envelope
    },
  )
  const entries = envelope!['bundle_entries'] as Array<Record<string, unknown>>
  return { events, envelope: envelope!, entries, provenance: envelope!['provenance'] as Record<string, unknown> }
}

beforeEach(() => { vi.resetModules() })
afterEach(() => { vi.unstubAllGlobals() })

describe('multi_school_bundle: cross_school_lookup is retired (SS N-370)', () => {
  it('never calls the retired primitive (the old code issued the call and got HTTP 400)', async () => {
    const { calls } = stubFetch()
    await run()
    expect(calls.map((c) => c.toolName)).not.toContain('cross_school_lookup')
    expect(calls.length).toBeGreaterThan(0) // the school evidence calls still run
  })

  it('keeps the slot as the first entry, shaped as NOT_AVAILABLE: not an error, not an empty result', async () => {
    stubFetch()
    const { entries } = await run()
    const e = entries[0]!
    expect(e['sub_tool']).toBe('cross_school_lookup')
    expect(e['not_available']).toBe(true)
    expect(e['reason']).toBe('capability_retired_wp_1_7')
    expect(e['errored']).toBe(false)
    expect(e['upstream_status']).toBeNull() // no upstream call was made
    expect(e['latency_ms']).toBe(0)
    for (const k of ['error_class', 'attempted_params', 'data', 'rows_returned', 'signal_ids_available']) {
      expect(e, k).not.toHaveProperty(k)
    }
    // every other entry is a real call result and carries no not_available marker
    expect(entries.slice(1).every((x) => x['not_available'] === undefined)).toBe(true)
  })

  it('accounting: the slot is neither fired nor errored; it is listed under provenance.sub_tools_not_available', async () => {
    stubFetch()
    const { provenance } = await run()
    expect(provenance['sub_tools_fired'] as string[]).not.toContain('cross_school_lookup')
    expect(provenance['sub_tools_errored'] as string[]).not.toContain('cross_school_lookup')
    expect(provenance['sub_tools_errored']).toEqual([])
    expect(provenance['sub_tools_not_available']).toEqual([{ sub_tool: 'cross_school_lookup', reason: 'capability_retired_wp_1_7' }])
    expect(provenance['sub_tools_fired']).toEqual(expect.arrayContaining(['parashara_evidence', 'kp_evidence']))
  })

  it('health is judged on the calls that ran: all school calls ok -> status ok (the old 400 made it "partial")', async () => {
    stubFetch()
    const { envelope } = await run()
    expect(envelope['status']).toBe('ok')
    expect(envelope['ok']).toBe(true)
  })

  it('health still degrades when the school calls themselves fail (the retired slot cannot mask them)', async () => {
    stubFetch({ schoolStatus: 500 })
    const { envelope, provenance } = await run()
    expect(envelope['status']).toBe('degraded')
    expect(envelope['ok']).toBe(false)
    expect((provenance['sub_tools_errored'] as string[]).length).toBeGreaterThan(0)
    expect(provenance['sub_tools_errored'] as string[]).not.toContain('cross_school_lookup')
  })

  it('emits no started / completed / error event for the slot (nothing ran)', async () => {
    stubFetch()
    const { events } = await run()
    expect(events.filter((e) => e['sub_tool'] === 'cross_school_lookup')).toEqual([])
  })

  it('school_verdicts (detailed) are unaffected', async () => {
    stubFetch()
    const { envelope } = await run({ response_format: 'detailed' })
    const verdicts = envelope['school_verdicts'] as Array<{ school: string; verdict_available: boolean }>
    expect(verdicts.length).toBeGreaterThan(0)
    expect(verdicts.every((v) => v.verdict_available)).toBe(true)
  })
})
