import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, _description: string, _schema: unknown, handler: ToolHandler) => {
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
  process.env['SERVICE_TOKEN'] = 'test-service-token'
})

describe('F-10 — prashna undertaking election windows', () => {
  it.each([
    ['health', 'medical'],
    ['career', 'start_business'],
  ])('filters election windows by the concrete %s action class', async (domain, expectedActionClass) => {
    const dbCalls: Array<{ sql: string; params: unknown[] }> = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, options?: { body?: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/mcp/db/query')) {
        const body = JSON.parse(options?.body ?? '{}') as { sql: string; params: unknown[] }
        dbCalls.push(body)
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)

    const result = await handlers.get('prashna_undertaking_get')!({
      chart_id: TEST_CHART_ID,
      domain,
      top_windows: 3,
    })

    expect(result.isError).toBeFalsy()
    const electionCall = dbCalls.find(({ sql }) => sql.includes('FROM phala_muhurta'))
    expect(electionCall).toBeDefined()
    expect(electionCall!.sql).toMatch(/AND pm\.action_class = \$2/)
    expect(electionCall!.params).toEqual([TEST_CHART_ID, expectedActionClass, 3])
  })

  it('rejects an unknown undertaking domain before selecting unfiltered election windows', async () => {
    const dbCalls: Array<{ sql: string; params: unknown[] }> = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, options?: { body?: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/mcp/db/query')) {
        dbCalls.push(JSON.parse(options?.body ?? '{}') as { sql: string; params: unknown[] })
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)

    const result = await handlers.get('prashna_undertaking_get')!({
      chart_id: TEST_CHART_ID,
      domain: 'misspelled_domain',
      top_windows: 3,
    })

    expect(result.isError).toBe(true)
    expect(dbCalls).toEqual([])
  })
})
