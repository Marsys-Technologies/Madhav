/**
 * kala_frame_wiring_n412.test.ts: SS N-412 items 2, 3 and 4 (Lahiri-primary combined batch, PR-4).
 *
 *  (2) `natal_ayanamsha_id` echoes the REQUESTED id, which over-claims for the sections served from Lahiri-only Kāla tables
 *      (kala_kota_chakra, kala_sudarshana_varsha, kala_moorti_nirnaya, kala_vedha_gochara, kala_tithi_pravesha: their writers pin
 *      CANONICAL_AYANAMSHA = lahiri_chitrapaksha and their handlers take no ayanamsha filter). The frame now lists those sections
 *      with their real frame and the label/note say so.
 *  (3) The frame must survive response-budget trimming: `ayanamsha_frame` is in IMMUNE_HONESTY_FIELDS (a >120-char scalar
 *      honesty object that the last-resort string walk used to cut mid-sentence).
 *  (4) Wiring: the ayanamsha / frame parameters flow from the TOOL INPUT through the now/ahead views to the reads. The test
 *      records every capability call the views make: per-ayanamsha reads must carry the requested id, and the Lahiri-only reads
 *      must NOT (that absence is what makes the Lahiri-only claim true). Dropping the wiring fails these.
 *
 * No network, no DB: global fetch is a recording mock that answers every capability with an empty payload.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { registerKalaNowGetTool, computeKalaNow } from '../tools/kala_views/now.js'
import { registerKalaAheadGetTool, computeKalaAhead } from '../tools/kala_views/ahead.js'
import {
  buildKalaAyanamshaFrame, KALA_NOW_LAHIRI_ONLY_SECTIONS, KALA_AHEAD_LAHIRI_ONLY_SECTIONS,
} from '../lib/kala_ayanamsha_frame.js'
import { budgetMcpContent, IMMUNE_HONESTY_FIELDS } from '../lib/response_budget.js'

const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }
const LAHIRI = 'lahiri_chitrapaksha'
const RAMAN = 'raman'

interface Call { uri: string; args: Record<string, unknown> }
let calls: Call[] = []

beforeEach(() => {
  calls = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    if (String(url).includes('/api/mcp/authz')) return { ok: true, json: async () => ({ authorized: true }), text: async () => '' } as Response
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri?: string; args?: Record<string, unknown> }
    if (body.uri) calls.push({ uri: body.uri, args: body.args ?? {} })
    return { ok: true, json: async () => ({ ok: true, content: { content: {}, is_error: false } }), text: async () => '' } as Response
  }))
})

const callsTo = (uri: string) => calls.filter((c) => c.uri === uri)

function captureHandler(register: (s: McpServer, p: Principal) => void): (params: Record<string, unknown>) => Promise<Record<string, unknown>> {
  let handler: ((params: Record<string, unknown>) => Promise<Record<string, unknown>>) | null = null
  register({ tool: (...a: unknown[]) => { handler = a[3] as typeof handler } } as unknown as McpServer, PRINCIPAL)
  return handler!
}

function payload(result: Record<string, unknown>): Record<string, unknown> {
  const sc = result['structuredContent'] as { object?: Record<string, unknown> } | undefined
  if (sc?.object) return sc.object
  const content = result['content'] as Array<{ text?: string }>
  return JSON.parse(String(content[0]?.text ?? '{}')) as Record<string, unknown>
}

const NOW_LAHIRI_ONLY_URIS = [
  'marsys://tool/L3/query_kota_chakra', 'marsys://tool/L3/query_sudarshana_varsha', 'marsys://tool/L3/query_moorti_nirnaya',
  'marsys://tool/L3/query_vedha_gochara', 'marsys://tool/L3/query_tithi_pravesha',
]

describe('item 2: the frame states the real frame of Lahiri-only Kāla tables', () => {
  it('a non-primary request lists every Lahiri-only section at lahiri_chitrapaksha and says natal_ayanamsha_id does not describe them', () => {
    const f = buildKalaAyanamshaFrame(RAMAN, KALA_NOW_LAHIRI_ONLY_SECTIONS)
    expect(f.natal_ayanamsha_id).toBe(RAMAN)
    expect(f.lahiri_only_sections.map((s) => s.section)).toEqual(
      ['kota_chakra', 'sudarshana_varsha', 'moorti_nirnaya', 'vedha_gochara', 'tithi_pravesha'])
    for (const s of f.lahiri_only_sections) expect(s.ayanamsha_id).toBe(LAHIRI)
    expect(f.label).toContain('Lahiri-only tables (kota_chakra, sudarshana_varsha, moorti_nirnaya, vedha_gochara, tithi_pravesha)')
    expect(f.label).toContain(`stored at ${LAHIRI} whatever ayanamsha_id was requested`)
    expect(f.note).toContain(`${LAHIRI} readings, NOT ${RAMAN} readings`)
  })

  it('the primary request needs no correction: single frame, no note', () => {
    const f = buildKalaAyanamshaFrame(LAHIRI, KALA_NOW_LAHIRI_ONLY_SECTIONS)
    expect(f.frame_mixed).toBe(false)
    expect(f.note).toBeNull()
    expect(f.label).toBe(`Single frame: natal facts and transit positions both at ${LAHIRI} (primary)`)
  })

  it('kala_now_get serves the correction, and each named section is a real key of the result', async () => {
    const result = await computeKalaNow(CHART, { ayanamsha_id: RAMAN, as_of: '2026-07-29' }, PRINCIPAL)
    expect(result.ayanamsha_frame.natal_ayanamsha_id).toBe(RAMAN)
    expect(result.ayanamsha_frame.lahiri_only_sections).toEqual(KALA_NOW_LAHIRI_ONLY_SECTIONS)
    for (const s of result.ayanamsha_frame.lahiri_only_sections) expect(Object.keys(result)).toContain(s.section)
  })

  it('the claim is TRUE: the reads behind the Lahiri-only sections carry no ayanamsha_id, while the per-ayanamsha reads carry the requested one', async () => {
    await computeKalaNow(CHART, { ayanamsha_id: RAMAN, as_of: '2026-07-29' }, PRINCIPAL)
    for (const uri of NOW_LAHIRI_ONLY_URIS) {
      const c = callsTo(uri)
      expect(c.length, uri).toBeGreaterThan(0)
      for (const call of c) expect(call.args, uri).not.toHaveProperty('ayanamsha_id')
    }
    for (const call of callsTo('marsys://tool/L3/query_temporal_activation')) expect(call.args['ayanamsha_id']).toBe(RAMAN)
  })

  it('kala_ahead_get names the Lahiri-only birth-year cutoff of period_echo', async () => {
    const result = await computeKalaAhead(CHART, { ayanamsha_id: RAMAN }, PRINCIPAL)
    expect(result.ayanamsha_frame.lahiri_only_sections).toEqual(KALA_AHEAD_LAHIRI_ONLY_SECTIONS)
    expect(result.ayanamsha_frame.lahiri_only_sections[0]!.section).toBe('period_echo')
    expect(Object.keys(result)).toContain('period_echo')
    expect(result.ayanamsha_frame.note).toContain(`${LAHIRI} readings, NOT ${RAMAN} readings`)
    for (const call of callsTo('marsys://tool/L3/query_life_arc')) expect(call.args).not.toHaveProperty('ayanamsha_id')
  }, 30_000)
})

describe('item 3: the frame note survives response-budget trimming', () => {
  it('ayanamsha_frame is in the immune honesty set', () => {
    expect(IMMUNE_HONESTY_FIELDS.has('ayanamsha_frame')).toBe(true)
  })

  it('a payload large enough to trim keeps the frame label, note and sections byte-for-byte', () => {
    const frame = buildKalaAyanamshaFrame(RAMAN, KALA_NOW_LAHIRI_ONLY_SECTIONS)
    const expected = structuredClone(frame) // the budget trims the response IN PLACE, so keep an untouched copy to compare against
    expect(frame.note!.length).toBeGreaterThan(120) // the shape the last-resort string walk truncates
    expect(frame.label.length).toBeGreaterThan(120)
    // Many long scalar fields (shorter than the note) that no array shed can remove: the budget cannot be met without the
    // last-resort string walk, which truncates the LONGEST strings first, i.e. the frame note before any of these.
    const prose: Record<string, string> = {}
    for (let i = 0; i < 300; i++) prose[`field_${i}`] = `long prose field ${i} `.padEnd(200, 'x')
    const content: Record<string, unknown> = {
      tool: 'kala_now_get',
      ayanamsha_frame: frame,
      windows: Array.from({ length: 400 }, (_, i) => ({ id: i, text: 'window row '.repeat(30) })),
      prose,
    }
    const originalBytes = JSON.stringify(content).length
    const trimmed = budgetMcpContent(content, 'kala_now_get', 2) as Record<string, unknown>
    expect(JSON.stringify(trimmed).length).toBeLessThan(originalBytes / 2) // trimming really happened (the response is mutated in place)
    expect(JSON.stringify(trimmed)).toContain('[truncated for budget]') // the last-resort walk ran
    expect(trimmed['ayanamsha_frame']).toEqual(expected)
  })
})

describe('item 4: the frame / ayanamsha parameters flow from the tool input to the reads', () => {
  it('kala_now_get: tool input ayanamsha_id reaches the per-ayanamsha reads and the served frame; omitted = Lahiri', async () => {
    const handler = captureHandler(registerKalaNowGetTool)
    const out = payload(await handler({ chart_id: CHART, ayanamsha_id: RAMAN, as_of: '2026-07-29' }))
    expect((out['ayanamsha_frame'] as { natal_ayanamsha_id: string }).natal_ayanamsha_id).toBe(RAMAN)
    const activation = callsTo('marsys://tool/L3/query_temporal_activation')
    expect(activation.length).toBeGreaterThan(0)
    for (const c of activation) expect(c.args['ayanamsha_id']).toBe(RAMAN)
    for (const c of callsTo('marsys://tool/L3/query_active_dashas')) expect(c.args['ayanamsha_id']).toBe(RAMAN)
    for (const c of callsTo('marsys://tool/L1/get_dignity')) expect(c.args['ayanamsha_id']).toBe(RAMAN)

    calls = []
    const dflt = payload(await handler({ chart_id: CHART, as_of: '2026-07-29' }))
    expect((dflt['ayanamsha_frame'] as { natal_ayanamsha_id: string; frame_mixed: boolean }).natal_ayanamsha_id).toBe(LAHIRI)
    expect((dflt['ayanamsha_frame'] as { frame_mixed: boolean }).frame_mixed).toBe(false)
    for (const c of callsTo('marsys://tool/L3/query_temporal_activation')) expect(c.args['ayanamsha_id']).toBe(LAHIRI)
  })

  it('kala_now_get: the question_frame input reaches the served result', async () => {
    const handler = captureHandler(registerKalaNowGetTool)
    const out = payload(await handler({
      chart_id: CHART, as_of: '2026-07-29', question_frame: { domain: 'career', horizon: 'this year' },
    }))
    expect(out['question_frame']).toMatchObject({ domain: 'career', horizon: 'this year' })
  })

  it('kala_ahead_get: tool input ayanamsha_id reaches the per-ayanamsha reads and the served frame; omitted = Lahiri', async () => {
    const handler = captureHandler(registerKalaAheadGetTool)
    const out = payload(await handler({ chart_id: CHART, ayanamsha_id: RAMAN }))
    expect((out['ayanamsha_frame'] as { natal_ayanamsha_id: string }).natal_ayanamsha_id).toBe(RAMAN)
    const activation = callsTo('marsys://tool/L3/query_temporal_activation')
    expect(activation.length).toBeGreaterThan(0)
    for (const c of activation) expect(c.args['ayanamsha_id']).toBe(RAMAN)
    for (const c of callsTo('marsys://tool/L3/query_active_dashas')) expect(c.args['ayanamsha_id']).toBe(RAMAN)

    calls = []
    const dflt = payload(await handler({ chart_id: CHART }))
    expect((dflt['ayanamsha_frame'] as { natal_ayanamsha_id: string }).natal_ayanamsha_id).toBe(LAHIRI)
    for (const c of callsTo('marsys://tool/L3/query_temporal_activation')) expect(c.args['ayanamsha_id']).toBe(LAHIRI)
  }, 30_000)

  it('kala_ahead_get: the question_frame input reaches the served result', async () => {
    const handler = captureHandler(registerKalaAheadGetTool)
    const out = payload(await handler({ chart_id: CHART, question_frame: { domain: 'wealth', horizon: '5y' } }))
    expect(out['question_frame']).toMatchObject({ domain: 'wealth' })
  }, 30_000)
})
