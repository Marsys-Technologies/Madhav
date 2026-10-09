import { afterEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { createKalaLegacyAdapter, registerKalaViewAlias, type KalaView } from './registry_alias.js'
import { registerAllKalaViews } from './register_all.js'

const principal = { user_uid: 'CODEX-k3', key_id: 'CODEX-key', role: 'guest' as const }
const observed = vi.hoisted(() => ({ views: [] as string[] }))
vi.mock('./registry_alias.js', async importOriginal => {
  const actual = await importOriginal<typeof import('./registry_alias.js')>()
  return { ...actual, registerKalaViewAlias: (...args: Parameters<typeof actual.registerKalaViewAlias>) => {
    observed.views.push(args[2])
    return actual.registerKalaViewAlias(...args)
  } }
})
afterEach(() => vi.unstubAllGlobals())

describe('K7-1b thin public aliases and explicit legacy adapter', () => {
  it('all seven actual public registrars use the common adapter boundary (fails on base)', () => {
    observed.views.length = 0
    registerAllKalaViews({ tool: vi.fn() } as unknown as McpServer, principal)
    expect(observed.views.sort()).toEqual(['ahead', 'elect', 'explain', 'now', 'priority', 'ritual', 'story'])
  })
  it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'] as KalaView[])(
    '%s preserves the exact legacy arguments, including question_frame and identity', async view => {
      const legacy = vi.fn(async () => ({ content: [] }))
      const args = { chart_id: 'CODEX-chart', as_of: '2026-10-09', horizon_years: 5,
        undertaking: 'business', domain: 'career', question_frame: { entity: 'CODEX business' } }
      await createKalaLegacyAdapter(principal, view, legacy).invoke(`kala_${view}_get`, args)
      expect(legacy.mock.calls[0]?.[0]).toBe(args)
    },
  )
  it('preserves a successful MCP envelope by reference, including structuredContent', async () => {
    const old = { content: [{ type: 'text' as const, text: '{"empty_reason":"no_matching_rows"}' }],
      structuredContent: { empty_reason: 'no_matching_rows', rows: [], coverage: [] } }
    const result = await createKalaLegacyAdapter(principal, 'now', async () => old).invoke('kala_now_get', {})
    expect(result).toEqual({ content: old, is_error: false })
  })
  it('preserves an old error envelope and its error flag', async () => {
    const old = { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED' }], isError: true }
    const result = await createKalaLegacyAdapter(principal, 'elect', async () => old).invoke('kala_elect_get', {})
    expect(result).toEqual({ content: old, is_error: true })
  })
  it('refuses cross-view execution instead of inferring an event class', async () => {
    const adapter = createKalaLegacyAdapter(principal, 'elect', async () => ({ content: [] }))
    await expect(adapter.invoke('kala_ritual_get', { undertaking: 'business' })).rejects.toThrow('cannot answer')
  })
  it('authorizes with the injected principal, never a default chart or user', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ authorized: true }) }))
    vi.stubGlobal('fetch', fetchMock)
    await createKalaLegacyAdapter(principal, 'now', async () => ({ content: [] })).authorize('CODEX-chart')
    expect(JSON.parse(fetchMock.mock.calls[0]?.[1].body)).toEqual({
      user_uid: principal.user_uid, chart_id: 'CODEX-chart', required: 'view',
    })
  })
  it('keeps the SDK input shape and per-request context on the installed alias', async () => {
    let callback: (...args: unknown[]) => unknown = () => undefined
    const server = { tool: (_name: string, _description: string, _schema: unknown, call: typeof callback) => {
      callback = call
    } } as unknown as McpServer
    const legacy = vi.fn(async () => ({ content: [] }))
    registerKalaViewAlias(server, principal, 'now', 'kala_now_get', 'NOW', { chart_id: z.string() }, legacy)
    const args = { chart_id: 'CODEX-chart' }, extra = { requestId: 'CODEX-request' }
    await callback(args, extra)
    expect(legacy.mock.calls[0]).toEqual([args, extra])
  })
  it('rejects a misregistered public name before installing a tool', () => {
    expect(() => registerKalaViewAlias({ tool: vi.fn() } as unknown as McpServer, principal,
      'now', 'now_read', 'NOW', {}, async () => ({ content: [] }))).toThrow('Unexpected public name')
  })
})
