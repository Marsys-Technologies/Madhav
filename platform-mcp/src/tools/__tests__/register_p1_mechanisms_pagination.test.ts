import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { registerP1AliasTools } from '../register_p1_aliases.js'
import type { Principal } from '../../types.js'

type ToolHandler = (params: Record<string, unknown>) => Promise<{
  structuredContent: { object: unknown }
  content: Array<{ type: string; text: string }>
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler>; schemas: Map<string, Record<string, z.ZodTypeAny>> } {
  const handlers = new Map<string, ToolHandler>()
  const schemas = new Map<string, Record<string, z.ZodTypeAny>>()
  const server = {
    tool: (name: string, _description: string, schema: Record<string, z.ZodTypeAny>, handler: ToolHandler) => {
      schemas.set(name, schema)
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers, schemas }
}

const principal: Principal = { user_uid: 'mechanism-pagination-user', key_id: 'mechanism-pagination-key' }
const chartId = '482012f1-710e-4a25-994a-93821f5871aa'

describe('bodha_mechanisms_get cursor continuation', () => {
  beforeEach(() => vi.unstubAllGlobals())

  it('exposes and forwards next_page_cursor unchanged from the first page to the second registry call', async () => {
    const { server, handlers, schemas } = makeCapturingServer()
    registerP1AliasTools(server, principal)
    const handler = handlers.get('bodha_mechanisms_get')
    expect(handler).toBeDefined()
    expect(schemas.get('bodha_mechanisms_get')).toHaveProperty('page_cursor')
    expect(z.object(schemas.get('bodha_mechanisms_get')!).safeParse({ chart_id: chartId, page_cursor: 'opaque-page-2' }).success).toBe(true)

    const calls: Array<{ uri: string; args: Record<string, unknown> }> = []
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
      const body = JSON.parse(String(init.body)) as { uri: string; args: Record<string, unknown> }
      calls.push(body)
      const first = calls.length === 1
      return {
        ok: true,
        json: async () => ({
          ok: true,
          content: {
            content: {
              build_id: 'build-a',
              rows: first ? [{ mechanism_id: 'm1' }] : [{ mechanism_id: 'm2' }],
              more_available: first,
              next_page_cursor: first ? 'opaque-page-2' : null,
            },
            is_error: false,
          },
        }),
      }
    }))

    const first = await handler!({ chart_id: chartId, limit: 1 })
    const firstPayload = first.structuredContent.object as { content: { next_page_cursor: string } }
    const second = await handler!({ chart_id: chartId, limit: 1, page_cursor: firstPayload.content.next_page_cursor })

    expect((second.structuredContent.object as { content: { rows: Array<{ mechanism_id: string }> } }).content.rows)
      .toEqual([{ mechanism_id: 'm2' }])
    expect(calls).toEqual([
      { uri: 'marsys://tool/L2/query_mechanisms', args: { chart_id: chartId, ayanamsha_id: 'lahiri_chitrapaksha', limit: 1 } },
      { uri: 'marsys://tool/L2/query_mechanisms', args: { chart_id: chartId, ayanamsha_id: 'lahiri_chitrapaksha', limit: 1, page_cursor: 'opaque-page-2' } },
    ])
  })
})
