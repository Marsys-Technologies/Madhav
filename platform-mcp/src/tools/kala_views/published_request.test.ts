import { afterEach, expect, it, vi } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import { registerAllKalaViews } from './register_all.js'
const authorize = vi.hoisted(() => vi.fn(async () => true))
vi.mock('../../lib/authz.js', () => ({ remoteAuthorize: authorize }))
const chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
const principal = { user_uid: 'k9-fixture', key_id: 'k9-fixture', role: 'guest' as const }
const selectors = { at: '2026-10-16T12:00:00Z', date_from: '2026-10-16T00:00:00Z',
  date_to: '2026-10-17T00:00:00Z', event_class: 'travel', assertion_id: 'k9-sentinel' }
function installed() {
  const tools = new Map<string, (args: Record<string, unknown>) => Promise<CallToolResult>>()
  registerAllKalaViews({ tool(name: string, _desc: string, shape: z.ZodRawShape,
    callback: (args: Record<string, unknown>) => Promise<CallToolResult>) {
    tools.set(name, args => callback(z.object(shape).parse(args)))
  } } as unknown as McpServer, principal)
  return tools
}
afterEach(() => { vi.unstubAllGlobals(); authorize.mockResolvedValue(true) })
it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'])
  ('installed public %s forwards exact stage selectors once, carrying its manifest and sentinel', async view => {
    const content = { view, chart_id, manifest_id: 'k9-manifest', generation: 'k9-generation', empty_reason: null,
      manifest: { manifest_id: 'k9-manifest', generation: 'k9-generation' },
      rows: [{ data: { assertion: { payload: { effective_state: 'information_unavailable', release: { instant: null } } } } }] }
    const fetcher = vi.fn(async (_url: string, _init: RequestInit) => ({ ok: true, json: async () => ({ ok: true, content: { is_error: false, content } }) }))
    vi.stubGlobal('fetch', fetcher)
    const result = await installed().get(`kala_${view}_get`)!({ chart_id, published_request: selectors })
    expect(result.isError).not.toBe(true)
    expect(result.structuredContent).toEqual({ type: 'object', object: content })
    expect(JSON.parse((result.content[0] as { text: string }).text)).toEqual(content)
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(JSON.parse(String(fetcher.mock.calls[0][1].body)))
      .toEqual({ uri: `marsys://tool/L3/kala_${view}_get`, args: { chart_id, published_request: selectors } })
    expect(authorize).toHaveBeenCalledWith(principal, chart_id)
  })
it('authorization denial never calls a stage or a legacy fallback', async () => {
  authorize.mockResolvedValue(false)
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher)
  expect((await installed().get('kala_now_get')!({ chart_id, published_request: selectors })).isError).toBe(true)
  expect(fetcher).not.toHaveBeenCalled()
})
it.each(['query_failed', 'invalid_published_snapshot'])('a failed %s is explicit and never falls back', async reason => {
  vi.stubGlobal('fetch', vi.fn(async () => reason === 'query_failed' ? { ok: false, status: 503 } :
    { ok: true, json: async () => ({ ok: true, content: { is_error: false, content: { manifest_id: 'wrong' } } }) }))
  const result = await installed().get('kala_now_get')!({ chart_id, published_request: selectors })
  expect(result).toMatchObject({ isError: true, structuredContent: { object: { manifest_id: null, empty_reason: reason } } })
})
it.each(['manifest_id', 'generation', 'missing_manifest', 'empty_reason', 'missing_success'])
  ('rejects a stage snapshot with a broken %s binding', async mutation => {
    const content: Record<string, unknown> = { view: 'now', chart_id, manifest_id: 'manifest', generation: 'g1',
      manifest: { manifest_id: 'manifest', generation: 'g1' }, empty_reason: null, rows: [{ data: {} }] }
    if (mutation === 'manifest_id') content.manifest = { manifest_id: 'other', generation: 'g1' }
    if (mutation === 'generation') content.manifest = { manifest_id: 'manifest', generation: 'other' }
    if (mutation === 'missing_manifest') delete content.manifest
    if (mutation === 'empty_reason') content.empty_reason = 'no_matching_rows'
    const response = { content, ...(mutation === 'missing_success' ? {} : { is_error: false }) }
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ ok: true, content: response }) })))
    expect(await installed().get('kala_now_get')!({ chart_id, published_request: selectors }))
      .toMatchObject({ isError: true, structuredContent: { object: { manifest_id: null, empty_reason: 'invalid_published_snapshot' } } })
  })
it('ritual keeps its Mode-3 redirect before I/O even beside a published request', async () => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher)
  expect(await installed().get('kala_ritual_get')!({ chart_id, undertaking: 'travel', published_request: selectors }))
    .toMatchObject({ content: [{ text: expect.stringContaining('wrong_view') }] })
  expect(fetcher).not.toHaveBeenCalled()
})
