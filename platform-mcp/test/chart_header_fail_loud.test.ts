/**
 * chart_header_fail_loud.test.ts — W3-L1 (GT-47 / W-9) registry_bridge chart_header
 * resolution honesty.
 *
 * Before this fix, every one of registry_bridge.ts's ~5 chart_header call sites did:
 *   try { chart_header = await callRegistryCapability(...) as ChartHeader }
 *   catch { chart_header = null }
 * which (a) silently dropped a resolution failure with no signal, AND (b) — a live-verified
 * defect this same fix closes — assigned the WHOLE capability ToolResult wrapper
 * (`{content: ChartHeader, is_error}`) to `chart_header` via an `as ChartHeader` cast that
 * skipped the `.content` unwrap every other consumer (`get_signals` et al.) performs. A real
 * production `get_chart_orientation` v3 call was observed serving
 * `chart_header: { content: {...real header...}, is_error: false }` — every field access
 * (`chart_header.lagna_sign`) silently read `undefined`.
 *
 * `resolveChartHeader` (extracted, now shared across all 5 call sites) fixes both: it
 * unwraps `.content` correctly, and returns `flags: ['chart_header_unresolved']` whenever
 * resolution fails or comes back error-shaped, instead of a bare null.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

process.env['SERVICE_TOKEN'] = 'test-service-token'
process.env['MCP_INTERNAL_TOKEN'] = 'test-internal-token'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { resolveChartHeader, CHART_HEADER_UNRESOLVED_FLAG } from '../src/tools/registry_bridge.js'

const MOCK_PRINCIPAL = { user_uid: 'test-uid', audience_tier: 'super_admin' as const, key_id: 'test-key-001' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const REAL_HEADER = {
  chart_id_short: '482012f1',
  name: 'Abhisek Mohanty',
  lagna_sign: 'Aries',
  lagna_deg: 12.43,
  moon_sign: 'Aquarius',
  sun_sign: 'Capricorn',
  ayanamsha: 'lahiri_chitrapaksha',
  current_maha_antar: 'Mercury MD / Saturn AD',
}

function jsonResponse(body: unknown, status = 200) {
  return { ok: status < 300, status, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) }
}

describe('resolveChartHeader (registry_bridge) — W3-L1 fail-loud contract', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('resolves normally: real header, empty flags (also proves the .content unwrap fix)', async () => {
    // The capability route double-wraps: {ok:true, content: {content: <header>, is_error:false}}
    mockFetch.mockResolvedValue(
      jsonResponse({ ok: true, content: { content: REAL_HEADER, is_error: false } }),
    )
    const result = await resolveChartHeader(CHART_ID, 'lahiri_chitrapaksha', MOCK_PRINCIPAL)
    expect(result.flags).toEqual([])
    expect(result.chart_header).toEqual(REAL_HEADER)
    // The historical bug this fix closes: chart_header must NOT be the wrapper object.
    expect(result.chart_header).not.toHaveProperty('content')
    expect(result.chart_header).not.toHaveProperty('is_error')
  })

  it('network/HTTP failure calling the capability: null header, honesty flag (never silent)', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: false, error: 'boom' }, 500))
    const result = await resolveChartHeader(CHART_ID, 'lahiri_chitrapaksha', MOCK_PRINCIPAL)
    expect(result.chart_header).toBeNull()
    expect(result.flags).toEqual([CHART_HEADER_UNRESOLVED_FLAG])
  })

  it('capability handler reports is_error:true: null header, honesty flag', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ ok: true, content: { content: 'chart_id is required', is_error: true } }),
    )
    const result = await resolveChartHeader(CHART_ID, 'lahiri_chitrapaksha', MOCK_PRINCIPAL)
    expect(result.chart_header).toBeNull()
    expect(result.flags).toEqual([CHART_HEADER_UNRESOLVED_FLAG])
  })

  it('fetch throws (e.g. timeout/abort): null header, honesty flag', async () => {
    mockFetch.mockRejectedValue(new Error('The operation was aborted'))
    const result = await resolveChartHeader(CHART_ID, 'lahiri_chitrapaksha', MOCK_PRINCIPAL)
    expect(result.chart_header).toBeNull()
    expect(result.flags).toEqual([CHART_HEADER_UNRESOLVED_FLAG])
  })

  it('propagates an upstream DB-level resolution flag via metadata.flags even when is_error is false', async () => {
    // chart_header.ts's fetchChartHeaderResolution surfaces a DB-level failure this way:
    // header fields are nulled but is_error stays false (best-effort content).
    mockFetch.mockResolvedValue(
      jsonResponse({
        ok: true,
        content: {
          content: { ...REAL_HEADER, name: null, lagna_sign: null, moon_sign: null, sun_sign: null, current_maha_antar: null },
          is_error: false,
          metadata: { flags: [CHART_HEADER_UNRESOLVED_FLAG] },
        },
      }),
    )
    const result = await resolveChartHeader(CHART_ID, 'lahiri_chitrapaksha', MOCK_PRINCIPAL)
    // Header is still served (best-effort, never a hard failure) but honestly flagged.
    expect(result.chart_header).not.toBeNull()
    expect(result.flags).toEqual([CHART_HEADER_UNRESOLVED_FLAG])
  })
})
