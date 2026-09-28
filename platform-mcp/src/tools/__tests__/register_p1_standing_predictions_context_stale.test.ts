/**
 * standing_predictions_read — chart-context staleness pass-through
 * (Jātaka Phase-A3, independent-review Important finding #5).
 *
 * `standing_predictions_read` is a `regAlias(...)` registration whose zod
 * schema previously carried only `domain` and `status`. `include_stale` —
 * the opt-in the underlying `query_prospective_ledger` capability now
 * exposes (migration 1123 / Jātaka Phase-A3 item 2) — was silently stripped
 * before it ever reached `callRegistryCap`, making the MCP-level disclosure
 * of chart-context-stale rows unreachable through this alias even though
 * `capability_knowledge.snapshot.json` advertises it.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { registerP1AliasTools } from '../register_p1_aliases.js'
import type { Principal } from '../../types.js'

type ToolHandler = (params: Record<string, unknown>) => Promise<unknown>

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

const principal: Principal = { user_uid: 'standing-predictions-stale-user', key_id: 'standing-predictions-stale-key' }
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

describe('standing_predictions_read — include_stale pass-through', () => {
  beforeEach(() => vi.unstubAllGlobals())

  it('accepts include_stale in its schema and forwards it to callRegistryCap', async () => {
    const { server, handlers, schemas } = makeCapturingServer()
    registerP1AliasTools(server, principal)

    const schema = schemas.get('standing_predictions_read')
    expect(schema).toBeDefined()

    const calls: Array<{ uri: string; args: Record<string, unknown> }> = []
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
      calls.push(JSON.parse(String(init.body)) as { uri: string; args: Record<string, unknown> })
      return {
        ok: true,
        json: async () => ({ ok: true, content: { content: { predictions: [] }, is_error: false } }),
      }
    }))

    // Mirrors the real MCP SDK's request path (validateToolInput in
    // @modelcontextprotocol/sdk/server/mcp.js): the raw args are parsed
    // through the registered zod schema BEFORE the handler ever sees them,
    // and zod's default (non-passthrough) object parsing silently strips
    // any key the schema does not declare. Calling the handler with the
    // raw params directly (skipping this parse) would hide exactly the bug
    // this test exists to catch.
    const parsed = z.object(schema!).parse({ chart_id: CHART, include_stale: true })
    const handler = handlers.get('standing_predictions_read')!
    await handler(parsed)

    expect(calls).toHaveLength(1)
    expect(calls[0]!.args).toMatchObject({ include_stale: true })
  })
})
