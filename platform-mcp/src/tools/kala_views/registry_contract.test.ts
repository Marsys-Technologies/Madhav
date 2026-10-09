/** Cross-package imports are test-only: deployment units share a structural contract. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { registerAllKalaViews } from './register_all.js'
import { createKalaLegacyAdapter, type KalaView } from './registry_alias.js'
import { legacyViewContract, makeLegacyViewHandler, makePublicView } from '../../../../platform/src/lib/retrieval/registry/layers/L3_kala/view_common'
import { VIDHI_PRIMITIVES } from '../../../../platform/src/lib/vidhi/registry_data'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

const views: KalaView[] = ['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain']
const chart = '00000000-0000-4000-8000-000000000281'
const principal = { user_uid: 'CODEX-k3', key_id: 'CODEX-key', role: 'guest' as const }
const frame = { domain: 'career', entity: 'CODEX undertaking', horizon: '90 days', intent_verb: 'plan' }
type Registered = { schema: z.ZodRawShape; call: (args: Record<string, unknown>) => Promise<CallToolResult> }
const registered = new Map<string, Registered>()
const fetchMock = vi.fn()

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-10-09T01:00:00Z'))
  registered.clear()
  registerAllKalaViews({ tool(name: string, _description: string, schema: z.ZodRawShape, call: Registered['call']) {
    registered.set(name, { schema, call })
  } } as unknown as McpServer, principal)
  fetchMock.mockReset()
  // Transport failure is honest unavailable substrate, not a fabricated stage.
  fetchMock.mockImplementation(async (url: string) => url.includes('/api/mcp/authz')
    ? { ok: true, json: async () => ({ authorized: true }) }
    : { ok: false, status: 503, text: async () => 'CODEX unavailable substrate' })
  vi.stubGlobal('fetch', fetchMock)
})
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals() })

function adapterFor(view: KalaView) {
  const tool = registered.get(`kala_${view}_get`)!
  return createKalaLegacyAdapter(principal, view, args => tool.call(z.object(tool.schema).parse(args)))
}

describe('K7-1b generated bridge and authentic registry adapter', () => {
  it('the existing Vidhi floor resolves all seven names by catalog_name_direct (fails on base)', () => {
    const bridge = JSON.parse(readFileSync(resolve('../platform/src/generated/projections/web_tool_bridge.generated.json'), 'utf8'))
    const liveNames = new Set(VIDHI_PRIMITIVES.map(primitive => primitive.live_tool))
    const expected = views.map(view => [`kala_${view}_get`, `marsys://tool/L3/kala_${view}_get`, 'catalog_name_direct'])
      .sort((a, b) => a[0].localeCompare(b[0]))
    const selected = bridge.vidhi_live_tool_bridge.entries
      .filter((entry: { name: string }) => views.some(view => entry.name === `kala_${view}_get`) && liveNames.has(entry.name))
      .map((entry: { name: string; uri: string; resolution_kind: string }) => [entry.name, entry.uri, entry.resolution_kind])
    expect(selected).toEqual(expected)
  })
  it.each(views)('%s public descriptor preserves its unavailable-stage disclosure', async view => {
    const result = await makePublicView(view).handler({ chart_id: chart })
    expect(result).toEqual({ is_error: true, content: {
      tool: `kala_${view}_get`, chart_id: chart, manifest_id: null,
      empty_reason: 'legacy_adapter_unavailable', stage_capability: `marsys://tool/L3/${view}_read`,
      unavailable_stage_bindings: legacyViewContract(view).unavailable_stage_bindings,
    } })
  })
  it('NOW injects the actual old callback and preserves its authorized empty response', async () => {
    const args = { chart_id: chart, as_of: '2026-10-07', question_frame: frame }
    const adapter = adapterFor('now')
    const old = await adapter.invoke('kala_now_get', args)
    const actual = await makeLegacyViewHandler('now', adapter)(args)
    expect(actual).toEqual(old)
  })
  it('ELECT preserves the actual permanent withholding envelope under registry dispatch', async () => {
    const args = { chart_id: chart, undertaking: 'business', question_frame: { entity: 'death' } }
    const adapter = adapterFor('elect')
    expect(await makeLegacyViewHandler('elect', adapter)(args)).toEqual(await adapter.invoke('kala_elect_get', args))
  })
  it('EXPLAIN preserves the actual missing-domain response instead of making an assertion id', async () => {
    const args = { chart_id: chart, question_frame: frame }
    const adapter = adapterFor('explain')
    expect(await makeLegacyViewHandler('explain', adapter)(args)).toEqual(await adapter.invoke('kala_explain_get', args))
  })
  it('ritual Mode-3 preserves the actual ELECT redirect across explicit registry injection', async () => {
    const args = { chart_id: chart, undertaking: 'sign the contract', question_frame: frame }
    const adapter = adapterFor('ritual')
    expect(await makeLegacyViewHandler('ritual', adapter)(args)).toEqual(await adapter.invoke('kala_ritual_get', args))
  })
  it('the real adapter denies authorization before entering a view callback', async () => {
    fetchMock.mockImplementation(async () => ({ ok: true, json: async () => ({ authorized: false }) }))
    const result = await makeLegacyViewHandler('now', adapterFor('now'))({ chart_id: chart })
    expect([result.is_error, result.content, fetchMock.mock.calls.length]).toEqual([true, {
      tool: 'kala_now_get', chart_id: chart, manifest_id: null, empty_reason: 'authorization_denied',
      stage_capability: 'marsys://tool/L3/now_read', unavailable_stage_bindings: ['at'],
    }, 1])
  })
})
