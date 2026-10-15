/**
 * identity_cross_check_surfaces.test.ts — SS N-360 (Lahiri-primary PR-3 follow-up).
 *
 * The ONE shared `identity_cross_check` block (Lagna sign, Moon sign, Moon nakshatra, current Mahadasha lord)
 * is BUILT by the platform's shared builder; this package compares nothing. These tests pin the MCP seam:
 *
 *   graha_portrait   include_cross_check is declared and threaded; the platform's block survives the envelope
 *   chart_snapshot   the platform's block passes through untouched
 *   dossier          page 1 carries the block (fetched through the SAME proxied chart_snapshot handler), later
 *                    pages and the ≤2KB receipt do not; the page itself is unchanged; a failed fetch is honest
 *   budget           the key is trimmable (never hardFloor) and goes before confirmed data
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { applyResponseBudget, CROSS_CHECK_FIELDS, IMMUNE_HONESTY_FIELDS, estimateBytes, type TrimmableSection } from '../lib/response_budget.js'
import { IDENTITY_CROSS_CHECK_KEY, attachIdentityCrossCheckToPage, extractIdentityCrossCheck, fetchDossierIdentityCrossCheck } from '../lib/identity_cross_check.js'

vi.mock('../lib/authz.js', () => ({ remoteAuthorize: vi.fn(async () => true) }))

type ToolResult = {
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}
type ToolHandler = (args: Record<string, unknown>) => Promise<ToolResult>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler>; schemas: Map<string, Record<string, unknown>> } {
  const handlers = new Map<string, ToolHandler>()
  const schemas = new Map<string, Record<string, unknown>>()
  const server = {
    tool: (name: string, _desc: string, schema: Record<string, unknown>, handler: ToolHandler) => {
      handlers.set(name, handler)
      schemas.set(name, schema)
    },
  } as unknown as McpServer
  return { server, handlers, schemas }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'

// The shapes the platform builder emits in COMPACT mode (SS N-361: the always-on form), copied from its output:
// agree = one line; dissent = the dissenting ayanamshas only; single-ayanamsha and unresolved-generation = not_available.
const AGREE = {
  heading: 'Cross-check, not the reading', primary_id: LAHIRI, scope: 'identity_facts', mode: 'compact',
  agreement: 'all_agree', summary: 'Agrees across all five ayanamshas',
}
const DISSENT = {
  ...AGREE, agreement: 'dissent',
  summary: 'Dissent: Raman: Moon sign Pisces (primary Aquarius)',
  others: [{ ayanamsha_id: 'raman', label: 'Raman', status: 'dissents', dissenting: [{ fact_key: 'moon_sign', fact_label: 'Moon sign', value: 'Pisces', primary_value: 'Aquarius' }] }],
}
const SINGLE = { not_available: true, reason: 'single_ayanamsha_chart', heading: 'Cross-check, not the reading', primary_id: LAHIRI }
const UNRESOLVED = { not_available: true, reason: 'served_generation_unresolved', heading: 'Cross-check, not the reading', primary_id: LAHIRI }

function stubFetch(payloads: Record<string, unknown>, captured: Array<{ uri: string; args: Record<string, unknown> }> = []) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    captured.push(body)
    const defaults: Record<string, unknown> = {
      'marsys://tool/L2/query_ucd': { chart_id: body.args['chart_id'], digest: {}, entity_profiles: [] },
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2,
        moon_sign: 'Aquarius', sun_sign: 'Capricorn', ayanamsha: LAHIRI, current_maha_antar: 'Saturn/Mercury',
      },
    }
    const payload = body.uri in payloads ? payloads[body.uri] : defaults[body.uri]
    if (payload === undefined) throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    return { ok: true, json: async () => ({ ok: true, content: { content: payload, is_error: false } }), text: async () => '' }
  }))
}

beforeEach(() => { vi.unstubAllGlobals() })

// ── graha_portrait ────────────────────────────────────────────────────────────────────────────────
describe('graha_portrait: include_cross_check and the platform block through the MCP envelope', () => {
  const portraitPayload = (extra: Record<string, unknown> = {}) => ({
    chart_id: CHART, graha: 'Moon', graha_code: 'MOON',
    position: { rows: [{ fact_id: 'f-1', fact_subject: 'MOON' }], count: 1 },
    completeness: { position: '✓' }, notes: [],
    ...extra,
  })

  it('declares an optional boolean include_cross_check and threads it (only when true) to the capability', async () => {
    const { server, handlers, schemas } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L2/graha_portrait': portraitPayload() }, captured)
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const schema = schemas.get('graha_portrait') as Record<string, { isOptional: () => boolean; safeParse: (v: unknown) => { success: boolean } }>
    expect(schema['include_cross_check']!.isOptional()).toBe(true)
    expect(schema['include_cross_check']!.safeParse(true).success).toBe(true)
    expect(schema['include_cross_check']!.safeParse('yes').success).toBe(false)

    await handlers.get('graha_portrait')!({ chart_id: CHART, graha: 'Saturn', include_cross_check: true })
    await handlers.get('graha_portrait')!({ chart_id: CHART, graha: 'Saturn' })
    await handlers.get('graha_portrait')!({ chart_id: CHART, graha: 'Saturn', include_cross_check: false })
    const calls = captured.filter(c => c.uri === 'marsys://tool/L2/graha_portrait')
    expect(calls[0]!.args['include_cross_check']).toBe(true)
    expect('include_cross_check' in calls[1]!.args).toBe(false)
    expect('include_cross_check' in calls[2]!.args).toBe(false)
  })

  it.each([['v3'], ['legacy']] as const)('%s envelope: the Moon block (agree / dissent / single) passes through content untouched', async (format) => {
    for (const block of [AGREE, DISSENT, SINGLE, UNRESOLVED]) {
      const { server, handlers } = makeCapturingServer()
      stubFetch({ 'marsys://tool/L2/graha_portrait': portraitPayload({ [IDENTITY_CROSS_CHECK_KEY]: block }) })
      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      registerRegistryBridgeTools(server, PRINCIPAL)
      const res = await handlers.get('graha_portrait')!({ chart_id: CHART, graha: 'Moon', response_format: format })
      const env = res.structuredContent!.object as { content: Record<string, unknown> }
      expect(env.content[IDENTITY_CROSS_CHECK_KEY]).toEqual(block)
      expect(env.content['position']).toEqual({ rows: [{ fact_id: 'f-1', fact_subject: 'MOON' }], count: 1 })
    }
  })

  it('the block is absent from the envelope when the platform did not send one (other graha)', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://tool/L2/graha_portrait': portraitPayload({ graha: 'Saturn', graha_code: 'SAT' }) })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const res = await handlers.get('graha_portrait')!({ chart_id: CHART, graha: 'Saturn' })
    const env = res.structuredContent!.object as { content: Record<string, unknown> }
    expect(IDENTITY_CROSS_CHECK_KEY in env.content).toBe(false)
  })

  it('under a tight budget the block is shed BEFORE the position rows (hardFloor core), and the shed is reported', async () => {
    const { server, handlers } = makeCapturingServer()
    const fat = { ...AGREE, summary: 'Agrees across all five ayanamshas', padding: 'x'.repeat(30_000) }
    stubFetch({ 'marsys://tool/L2/graha_portrait': portraitPayload({ [IDENTITY_CROSS_CHECK_KEY]: fat }) })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const res = await handlers.get('graha_portrait')!({ chart_id: CHART, graha: 'Moon', budget_kb: 8 })
    const env = res.structuredContent!.object as { content: Record<string, unknown>; trim_report?: Array<{ path: string; kept_count: number }> }
    expect(IDENTITY_CROSS_CHECK_KEY in env.content).toBe(false)
    expect((env.content['position'] as { rows: unknown[] }).rows).toHaveLength(1)
    expect(env.trim_report?.find(e => e.path === IDENTITY_CROSS_CHECK_KEY)?.kept_count).toBe(0)
    expect(env.trim_report?.some(e => e.path === 'content.position.rows')).toBeFalsy()
  })
})

// ── chart_snapshot ────────────────────────────────────────────────────────────────────────────────
describe('chart_snapshot: the platform block passes through the MCP tool untouched', () => {
  const snapshot = (extra: Record<string, unknown> = {}) => ({
    chart_id: CHART, ayanamsha_id: LAHIRI, vargas: ['D1'], snapshot_text: 'D1 — Lagna Ari', byte_length: 14, within_budget: true,
    grids: { D1: [] }, additional_vargas: [], unresolved_vargas: [], ...extra,
  })

  it.each([['agree', AGREE], ['dissent', DISSENT], ['single', SINGLE], ['unresolved', UNRESOLVED]] as const)('%s case', async (_n, block) => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://tool/L1/chart_snapshot': snapshot({ [IDENTITY_CROSS_CHECK_KEY]: block }) })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const res = await handlers.get('chart_snapshot')!({ chart_id: CHART })
    const env = res.structuredContent!.object as { content: Record<string, unknown> }
    expect(env.content[IDENTITY_CROSS_CHECK_KEY]).toEqual(block)
    expect(env.content['snapshot_text']).toBe('D1 — Lagna Ari')
  })

  it('declares an optional boolean include_cross_check and threads it (only when true) to the capability (full mode)', async () => {
    const { server, handlers, schemas } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L1/chart_snapshot': snapshot({ [IDENTITY_CROSS_CHECK_KEY]: AGREE }) }, captured)
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const schema = schemas.get('chart_snapshot') as Record<string, { isOptional: () => boolean; safeParse: (v: unknown) => { success: boolean } }>
    expect(schema['include_cross_check']!.isOptional()).toBe(true)
    expect(schema['include_cross_check']!.safeParse('yes').success).toBe(false)
    await handlers.get('chart_snapshot')!({ chart_id: CHART, include_cross_check: true })
    await handlers.get('chart_snapshot')!({ chart_id: CHART })
    await handlers.get('chart_snapshot')!({ chart_id: CHART, include_cross_check: false })
    const calls = captured.filter(c => c.uri === 'marsys://tool/L1/chart_snapshot')
    expect(calls[0]!.args['include_cross_check']).toBe(true)
    expect('include_cross_check' in calls[1]!.args).toBe(false)
    expect('include_cross_check' in calls[2]!.args).toBe(false)
  })

  it('under a tight budget the block goes first and the grid survives', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://tool/L1/chart_snapshot': snapshot({ [IDENTITY_CROSS_CHECK_KEY]: { ...AGREE, padding: 'x'.repeat(60_000) } }) })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const res = await handlers.get('chart_snapshot')!({ chart_id: CHART, budget_kb: 8 })
    const env = res.structuredContent!.object as { content: Record<string, unknown> }
    expect(IDENTITY_CROSS_CHECK_KEY in env.content).toBe(false)
    expect(env.content['snapshot_text']).toBe('D1 — Lagna Ari')
  })
})

// ── dossier ───────────────────────────────────────────────────────────────────────────────────────
describe('dossier: page 1 carries the identity block, fetched through the proxied chart_snapshot handler', () => {
  async function dossier() {
    const { server, handlers } = makeCapturingServer()
    const { registerDossierTool, runDossier } = await import('../tools/dossier.js')
    registerDossierTool(server, PRINCIPAL)
    return { call: handlers.get('dossier')!, runDossier }
  }
  const page = (r: ToolResult) => r.structuredContent!.object as Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

  it.each([['agree', AGREE], ['dissent', DISSENT], ['single', SINGLE], ['unresolved', UNRESOLVED]] as const)('%s case: the block rides on page 1, the rest of the page is exactly runDossier\'s', async (_n, block) => {
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L1/chart_snapshot': { chart_id: CHART, [IDENTITY_CROSS_CHECK_KEY]: block } }, captured)
    const { call, runDossier } = await dossier()
    const res = page(await call({ domain: 'wealth', chart_id: CHART, budget_kb: 64 }))
    expect(res[IDENTITY_CROSS_CHECK_KEY]).toEqual(block)
    const { [IDENTITY_CROSS_CHECK_KEY]: _k, ...rest } = res
    void _k
    expect(rest).toEqual(JSON.parse(JSON.stringify(runDossier({ domain: 'wealth', chart_id: CHART, budget_kb: 64 }))))
    expect(captured).toEqual([{ uri: 'marsys://tool/L1/chart_snapshot', args: { chart_id: CHART } }])
  })

  it('page 2 (a cursor) does not repeat the block and makes no platform call', async () => {
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L1/chart_snapshot': { [IDENTITY_CROSS_CHECK_KEY]: AGREE } }, captured)
    const { call, runDossier } = await dossier()
    const first = runDossier({ domain: 'wealth', chart_id: CHART, budget_kb: 16 })
    expect(first.cursor).toBeTruthy()
    const res = page(await call({ domain: 'wealth', chart_id: CHART, budget_kb: 16, cursor: first.cursor }))
    expect(IDENTITY_CROSS_CHECK_KEY in res).toBe(false)
    expect(res['page_n']).toBe(2)
    expect(captured).toHaveLength(0)
  })

  it('the ≤2KB receipt path is untouched (no block, no platform call)', async () => {
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({}, captured)
    const { call } = await dossier()
    const res = page(await call({ domain: 'wealth', chart_id: CHART, receipt: true }))
    expect(res['mode']).toBe('receipt')
    expect(IDENTITY_CROSS_CHECK_KEY in res).toBe(false)
    expect(captured).toHaveLength(0)
  })

  it('a platform failure is the honest cross_check_read_failed form and never fails the page', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('ECONNREFUSED') }))
    const { call } = await dossier()
    const res = page(await call({ domain: 'wealth', chart_id: CHART, budget_kb: 64 }))
    expect(res['ok']).toBe(true)
    expect(res[IDENTITY_CROSS_CHECK_KEY]).toMatchObject({ not_available: true, reason: 'cross_check_read_failed', primary_id: LAHIRI })
  })

  it('a platform response without the block (or an error result) is cross_check_read_failed, never an invented agreement', async () => {
    for (const payload of [{ chart_id: CHART }, null]) {
      expect(extractIdentityCrossCheck({ content: payload, is_error: false })).toBeNull()
    }
    expect(extractIdentityCrossCheck({ content: { [IDENTITY_CROSS_CHECK_KEY]: AGREE }, is_error: true })).toBeNull()
    const f = vi.fn(async () => ({ ok: true, json: async () => ({ ok: true, content: { content: { error: 'x' }, is_error: true } }) })) as unknown as typeof fetch
    expect(await fetchDossierIdentityCrossCheck(CHART, PRINCIPAL, f)).toMatchObject({ not_available: true, reason: 'cross_check_read_failed' })
  })

  it('a block that does not fit the page budget is NOT attached; the shed is disclosed and the page is unchanged', () => {
    const base = { page_n: 1, budget_kb_applied: 1, judgment_flags: [] as string[], payload: 'p'.repeat(900) }
    const out = attachIdentityCrossCheckToPage(base, { ...AGREE, padding: 'x'.repeat(400) })
    expect(IDENTITY_CROSS_CHECK_KEY in out).toBe(false)
    expect(out.judgment_flags).toEqual(['identity_cross_check_shed_for_page_budget'])
    expect(out.payload).toBe(base.payload)
  })

  it('dossier compares nothing: the tool source has no ayanamsha comparison of its own', async () => {
    const { readFileSync } = await import('node:fs')
    for (const f of ['../tools/dossier.ts', '../lib/identity_cross_check.ts']) {
      const src = readFileSync(new URL(f, import.meta.url), 'utf8')
      expect(src).not.toMatch(/AYANAMSHA_SERVE_ORDER|import .*ayanamsha_cross_check|status: 'agrees'|agreement ===/)
    }
  })
})

// ── response budget ───────────────────────────────────────────────────────────────────────────────
describe('identity_cross_check is registered TRIMMABLE (never hardFloor, never immune) and goes before confirmed data', () => {
  interface Content { rows: Array<{ fact_id: string }>; identity_cross_check?: unknown; ayanamsha_cross_check?: unknown; padding: string }
  const section = (hardFloor: boolean): TrimmableSection<Content> => ({
    path: 'rows', label: 'rows', minKeep: 10, hardFloor,
    getArray: (c) => c.rows, setArray: (c, kept) => { c.rows = kept as Content['rows'] },
    recover: { instrument: 'ganita_positions_get', hint: 'narrow the scope' },
  })
  const make = (n: number, withX: boolean): Content => ({
    padding: 'p'.repeat(300),
    rows: Array.from({ length: n }, (_, i) => ({ fact_id: `f${i}` })),
    ...(withX ? { identity_cross_check: { heading: 'Cross-check, not the reading', summary: 'x'.repeat(900) } } : {}),
  })

  it('is a registered, non-immune field alongside ayanamsha_cross_check', () => {
    expect(CROSS_CHECK_FIELDS).toEqual(['ayanamsha_cross_check', IDENTITY_CROSS_CHECK_KEY])
    expect(IDENTITY_CROSS_CHECK_KEY).toBe('identity_cross_check')
    expect(IMMUNE_HONESTY_FIELDS.has(IDENTITY_CROSS_CHECK_KEY)).toBe(false)
  })

  it.each([false, true])('hardFloor=%s: dropping the block alone is enough -> every row survives', (hardFloor) => {
    const without = estimateBytes(make(40, false))
    const c = make(40, true)
    const maxKb = (without + 200) / 1024
    expect(estimateBytes(c)).toBeGreaterThan(maxKb * 1024)
    const res = applyResponseBudget(c, maxKb, [section(hardFloor)])
    expect(res.content.rows).toHaveLength(40)
    expect(res.content.identity_cross_check).toBeUndefined()
    expect(res.trim_report?.find((e) => e.path === IDENTITY_CROSS_CHECK_KEY)?.kept_count).toBe(0)
    expect(res.trim_report?.some((e) => e.path === 'rows')).toBe(false)
  })

  it('both cross-check keys are shed independently and each shed is reported under its own key', () => {
    const c = make(80, true)
    c.ayanamsha_cross_check = { heading: 'Cross-check, not the reading', summary: 'y'.repeat(900) }
    const res = applyResponseBudget(c, 1.0, [section(false)])
    expect(res.content.identity_cross_check).toBeUndefined()
    expect(res.content.ayanamsha_cross_check).toBeUndefined()
    const paths = (res.trim_report ?? []).map((e) => e.path)
    expect(paths).toContain('identity_cross_check')
    expect(paths).toContain('ayanamsha_cross_check')
    expect(paths).toContain('rows')
  })

  it('an under-budget response keeps the block', () => {
    const c = make(3, false)
    c.identity_cross_check = { heading: 'Cross-check, not the reading', summary: 'Agrees across all five ayanamshas' }
    const res = applyResponseBudget(c, 40, [section(false)])
    expect(res.trimmed).toBe(false)
    expect(res.content.identity_cross_check).toBeDefined()
  })
})
