import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { computeKalaNow, registerKalaNowGetTool } from './now.js'
import { registerKalaStoryTool } from './story.js'
const forecast = vi.hoisted(() => vi.fn())
vi.mock('../retrieval/register_gochara_windows.js', () => ({ computeGocharaForecast: forecast }))
vi.mock('../../lib/authz.js', () => ({ remoteAuthorize: async () => true }))
const chart = '11111111-1111-4111-8111-111111111111'
const principal = { user_uid: 'CODEX-k2', key_id: 'CODEX-k2-key', role: 'guest' as const }
const disclosure = { resolution: 'era', resolution_source: 'stored', is_timing_window: false,
  timing_window_blocked_reason: 'era_resolution' }
const era = { event_class: 'major_gain', generation: '3.0', window_start: '2024-02-05',
  window_end: '2034-01-30', peak_date: '2028-01-01', valence: 'gain', signed_intensity: 2.5,
  calibration_state: 'calibrated', resolution_disclosure: disclosure }
const timing = { ...era, generation: '5.0', resolution_disclosure: { ...disclosure,
  resolution: 'day', is_timing_window: true, timing_window_blocked_reason: null } }
const parva = { id: 1, parva_index: 1, dasha_planet: 'Mercury', start_year: 2020, end_year: 2027,
  parva_quality: 'building', theme_keywords: ['career'], high_convergence_count: null, avg_effective_score: null,
  convergence_null_reason: 'source_table_empty_for_chart', narrative: { summary: null },
  source_citation: 'CODEX:MD=Mercury', computed_at: '2026-08-13T00:00:00Z' }
const tools = new Map<string, (args: Record<string, unknown>) => Promise<unknown>>()
beforeEach(() => {
  vi.stubEnv('SM_GAMMA_C4_ENABLED', 'true')
  forecast.mockResolvedValue({ windows: [era] })
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}'))
    if (url.includes('/api/mcp/authz')) return { ok: true, json: async () => ({ authorized: true }) }
    if (url.includes('/api/mcp/db/query')) return { ok: true, json: async () => ({ rows: [] }) }
    let content: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L1/get_dignity') content = { rows: [
      { fact_subject: 'LAGNA', fact_key: 'sign_num', fact_value_num: 1, fact_id: 'CODEX-lagna' },
      { fact_subject: 'MOON', fact_key: 'sign_num', fact_value_num: 11, fact_id: 'CODEX-moon' },
    ] }
    if (body.uri === 'marsys://tool/L0/query_planet_transit') content = { rows: [
      { sign_number: 11, date: '2026-10-09', degree_in_sign: 20, is_retrograde: false },
    ] }
    if (body.uri === 'marsys://tool/L3/query_life_arc') content = { parvas: [parva] }
    return { ok: true, json: async () => ({ ok: true, content: { content, is_error: false } }) }
  }))
  tools.clear()
  const server = { tool(name: string, _description: string, shape: z.ZodRawShape,
    call: (args: Record<string, unknown>) => Promise<unknown>) {
    tools.set(name, args => call(z.object(shape).parse(args)))
  } } as unknown as McpServer
  registerKalaStoryTool(server, principal)
  registerKalaNowGetTool(server, principal)
})
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs() })
it('NOW golden: the 3.0 era is visible as context with exact disclosure, never an active timing window', async () => {
  const result = await computeKalaNow(chart, { as_of: '2026-10-09' }, principal)
  expect(result.gochara_narrative).toMatchObject({ active_windows: [], context_windows: [{
    generation: '3.0', qualification: 'context_only', resolution_disclosure: disclosure,
  }], field_gochara_alignment: 'insufficient_data', narrative_tier: 'thin',
    resolution_disclosure: { timing_rows_in_page: 0, context_only_rows_in_page: 1 } })
})
it('a context row cannot be promoted by a contradictory timing flag', async () => {
  forecast.mockResolvedValue({ windows: [{ ...era, resolution_disclosure: timing.resolution_disclosure }] })
  const result = await computeKalaNow(chart, { as_of: '2026-10-09' }, principal)
  expect(result.gochara_narrative).toMatchObject({ active_windows: [], context_windows: [{ qualification: 'context_only' }] })
})
it('disclosed day windows remain active; context never inflates narrative richness', async () => {
  forecast.mockResolvedValue({ windows: [timing, era] })
  const result = await computeKalaNow(chart, { as_of: '2026-10-09' }, principal)
  expect(result.gochara_narrative).toMatchObject({ active_windows: [{ generation: '5.0',
    qualification: 'timing_window', resolution_disclosure: timing.resolution_disclosure }],
    context_windows: [{ generation: '3.0' }], narrative_tier: 'moderate' })
})
it('missing disclosure yields an honest null and never an actionable window', async () => {
  forecast.mockResolvedValue({ windows: [{ ...era, generation: '5.0', resolution_disclosure: undefined }] })
  const result = await computeKalaNow(chart, { as_of: '2026-10-09' }, principal)
  expect(result.gochara_narrative).toMatchObject({ active_windows: [], context_windows: [{ resolution_disclosure: null }],
    resolution_disclosure: { unavailable_rows_in_page: 1 } })
})
it('STORY public-name golden carries chapter identity and null reason through the installed alias', async () => {
  const result = await tools.get('kala_story_get')!({ chart_id: chart }) as { structuredContent: { object: unknown } }
  expect(result.structuredContent.object).toMatchObject({ tool: 'kala_story_get', chapter_count: 1, chapters: [{
    parva_index: 1, dasha_planet: 'Mercury', high_convergence_count: null, avg_effective_score: null,
    convergence_null_reason: 'source_table_empty_for_chart', narrative: { summary: null },
  }] })
})
it('NOW public-name golden carries context and disclosure through the installed alias', async () => {
  const result = await tools.get('kala_now_get')!({ chart_id: chart, as_of: '2026-10-09' }) as { structuredContent: { object: unknown } }
  expect(result.structuredContent.object).toMatchObject({ tool: 'kala_now_get', as_of_date: '2026-10-09',
    gochara_narrative: { active_windows: [], context_windows: [{ qualification: 'context_only', resolution_disclosure: disclosure }] } })
})

it('an explicit instant carries unavailable negative space through the installed NOW alias', async () => {
  const at = '2026-10-09T12:00:00+05:30'
  const snapshot = { view: 'now', chart_id: chart, manifest_id: 'CODEX-build', generation: '4.1',
    manifest: { manifest_id: 'CODEX-build', generation: '4.1' }, empty_reason: null,
    rows: [{ source_table: 'kala_obstruction', record_id: 'CODEX-unavailable', density: 'catalog_only',
      qualification: 'published', data: { assertion: { payload: { effective_state: 'information_unavailable',
        release: { kind: 'unknown', instant: null } }, roots: { record_ids: ['CODEX-window'] } } } }],
    coverage: [{ unsearched_reason: 'not_searched' }], pagination: { more_available: false } }
  const original = vi.mocked(fetch).getMockImplementation()!
  vi.mocked(fetch).mockImplementation(async (url, init) => {
    const body = JSON.parse(String(init?.body ?? '{}'))
    if (body.uri === 'marsys://tool/L3/now_read') return { ok: true,
      json: async () => ({ ok: true, content: { content: snapshot, is_error: false } }) } as Response
    return original(url, init)
  })
  const result = await tools.get('kala_now_get')!({ chart_id: chart, as_of: '2026-10-09', at }) as {
    structuredContent: { object: Record<string, unknown> }
  }
  expect(result.structuredContent.object.published_now).toEqual({ at, capability: 'marsys://tool/L3/now_read',
    status: 'published', empty_reason: null, snapshot })
  const stageCalls = vi.mocked(fetch).mock.calls.map(([, init]) => JSON.parse(String(init?.body ?? '{}')))
    .filter(body => body.uri === 'marsys://tool/L3/now_read')
  expect(stageCalls).toEqual([{ uri: 'marsys://tool/L3/now_read', args: { chart_id: chart, at } }])
})

it('omitting the instant preserves the old public envelope and performs no stage request', async () => {
  const result = await tools.get('kala_now_get')!({ chart_id: chart, as_of: '2026-10-09' }) as {
    structuredContent: { object: Record<string, unknown> }
  }
  expect(result.structuredContent.object).not.toHaveProperty('published_now')
  expect(vi.mocked(fetch).mock.calls.map(([, init]) => JSON.parse(String(init?.body ?? '{}')).uri))
    .not.toContain('marsys://tool/L3/now_read')
})

it.each(['2026-10-09', 'junk', '2026-02-30T10:00:00Z'])('rejects ambiguous/invalid instant %s before any dispatch', async at => {
  vi.mocked(fetch).mockClear()
  expect(() => tools.get('kala_now_get')!({ chart_id: chart, at })).toThrow()
  expect(fetch).not.toHaveBeenCalled()
})

it('a failed published NOW request stays information_unavailable at the actual public boundary', async () => {
  const original = vi.mocked(fetch).getMockImplementation()!
  vi.mocked(fetch).mockImplementation(async (url, init) => {
    const body = JSON.parse(String(init?.body ?? '{}'))
    if (body.uri === 'marsys://tool/L3/now_read') return { ok: true,
      json: async () => ({ ok: true, content: { content: { empty_reason: 'query_failed' }, is_error: true } }) } as Response
    return original(url, init)
  })
  const result = await tools.get('kala_now_get')!({ chart_id: chart, at: '2026-10-09T12:00:00Z' }) as {
    structuredContent: { object: Record<string, unknown> }
  }
  expect(result.structuredContent.object.published_now)
    .toMatchObject({ status: 'information_unavailable', empty_reason: 'query_failed', snapshot: null })
})
