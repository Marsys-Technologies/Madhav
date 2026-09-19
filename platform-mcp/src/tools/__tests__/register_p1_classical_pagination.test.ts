import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import { registerP1AliasTools } from '../register_p1_aliases.js'
import { registerP1ReferenceTools } from '../register_p1_reference.js'
import { registerRegistryBridgeTools } from '../registry_bridge.js'

type ToolHandler = (params: Record<string, unknown>) => Promise<unknown>

function capturingServer() {
  const handlers = new Map<string, ToolHandler>()
  const schemas = new Map<string, Record<string, z.ZodTypeAny>>()
  const server = {
    tool: (name: string, ...rest: unknown[]) => {
      const schema = rest.length === 3 ? rest[1] : rest[0]
      const handler = rest.length === 3 ? rest[2] : rest[1]
      schemas.set(name, schema as Record<string, z.ZodTypeAny>)
      handlers.set(name, handler as ToolHandler)
    },
  } as unknown as McpServer
  return { server, handlers, schemas }
}

const principal: Principal = { user_uid: 'classical-pagination-user', key_id: 'classical-pagination-key' }

describe('classical MCP cursor forwarding', () => {
  beforeEach(() => vi.unstubAllGlobals())

  it('exposes page_cursor and forwards it byte-for-byte through alias, bridge, and every classical reference fallback', async () => {
    const { server, handlers, schemas } = capturingServer()
    registerP1AliasTools(server, principal)
    registerRegistryBridgeTools(server, principal)
    registerP1ReferenceTools(server, principal)

    const toolNames = [
      'ref_classical_citation_get', 'get_classical_citation', 'ref_rules_search',
      'ref_dignity_reference_get', 'ref_nakshatra_get',
    ]
    for (const name of toolNames) {
      expect(schemas.get(name), name).toHaveProperty('page_cursor')
      const required = name === 'get_classical_citation' ? { query: 'dasha' } : {}
      expect(z.object(schemas.get(name)!).safeParse({ ...required, page_cursor: 'opaque.classical.page.2' }).success, name).toBe(true)
    }

    const calls: Array<{ uri: string; args: Record<string, unknown> }> = []
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
      const body = JSON.parse(String(init.body)) as { uri: string; args: Record<string, unknown> }
      calls.push(body)
      return {
        ok: true,
        json: async () => ({
          ok: true,
          content: { content: { citations: [], more_available: false, next_page_cursor: null }, is_error: false },
        }),
        text: async () => '',
      }
    }))

    await handlers.get('ref_classical_citation_get')!({ keyword: 'dasha', page_cursor: 'alias.cursor' })
    await handlers.get('get_classical_citation')!({ query: 'dasha', page_cursor: 'bridge.cursor' })
    await handlers.get('ref_rules_search')!({ keyword: 'dasha', page_cursor: 'rules.cursor' })
    await handlers.get('ref_dignity_reference_get')!({ keyword: 'dignity', page_cursor: 'dignity.cursor' })
    await handlers.get('ref_nakshatra_get')!({ keyword: 'rohini', page_cursor: 'nakshatra.cursor' })

    expect(calls.filter((call) => call.uri === 'marsys://tool/L0/query_classical_texts').map((call) => call.args.page_cursor))
      .toEqual(['alias.cursor', 'bridge.cursor', 'rules.cursor', 'dignity.cursor', 'nakshatra.cursor'])
  })

  it('treats planet and nakshatra cursors as classical continuations even when structured rows exist', async () => {
    const { server, handlers } = capturingServer()
    registerP1ReferenceTools(server, principal)
    const capabilityCalls: Array<{ uri: string; args: Record<string, unknown> }> = []
    const databaseCalls: Array<{ sql: string; params: unknown[] }> = []

    vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit) => {
      const body = JSON.parse(String(init.body)) as Record<string, unknown>
      if (url.includes('/api/mcp/db/query')) {
        databaseCalls.push({
          sql: String(body.sql),
          params: Array.isArray(body.params) ? body.params : [],
        })
        return {
          ok: true,
          json: async () => ({ ok: true, rows: [{ graha: 'Saturn', nakshatra_id: 4, name_en: 'Rohini' }] }),
          text: async () => '',
        }
      }

      const call = body as { uri: string; args: Record<string, unknown> }
      capabilityCalls.push(call)
      return {
        ok: true,
        json: async () => ({
          ok: true,
          content: { content: { citations: [], more_available: false, next_page_cursor: null }, is_error: false },
        }),
        text: async () => '',
      }
    }))

    await handlers.get('ref_dignity_reference_get')!({
      planet: 'saturn',
      page_cursor: 'dignity.structured-row.cursor',
    })
    await handlers.get('ref_nakshatra_get')!({
      nakshatra: 'rohini',
      page_cursor: 'nakshatra.structured-row.cursor',
    })

    expect(databaseCalls).toEqual([])
    expect(capabilityCalls).toEqual([
      expect.objectContaining({
        uri: 'marsys://tool/L0/query_classical_texts',
        args: expect.objectContaining({
          query_text: 'saturn dignity',
          page_cursor: 'dignity.structured-row.cursor',
        }),
      }),
      expect.objectContaining({
        uri: 'marsys://tool/L0/query_classical_texts',
        args: expect.objectContaining({
          query_text: 'rohini nakshatra',
          page_cursor: 'nakshatra.structured-row.cursor',
        }),
      }),
    ])
  })
})
