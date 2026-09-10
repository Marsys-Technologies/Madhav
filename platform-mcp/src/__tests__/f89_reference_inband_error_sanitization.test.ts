import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }
}

const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

describe('F89 reference capability in-band errors', () => {
  let handler: (params: Record<string, unknown>) => Promise<{
    isError?: boolean
    structuredContent: { object: unknown }
  }>

  beforeAll(async () => {
    const { registerP1ReferenceTools } = await import('../tools/register_p1_reference.js')
    const mockServer = {
      tool: (name: string, _description: string, _schema: unknown, registeredHandler: typeof handler) => {
        if (name === 'ref_rules_search') handler = registeredHandler
      },
    } as unknown as McpServer
    registerP1ReferenceTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('turns an in-band capability error into the existing sanitized typed error', async () => {
    const rawBackendSignature = 'invalid byte sequence for encoding '
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: { content: rawBackendSignature, is_error: true },
    }))

    const result = await handler({ keyword: '\u0000' })
    const serialized = JSON.stringify(result.structuredContent.object)

    expect(result.isError).toBe(true)
    expect(serialized).toContain('internal_error')
    expect(serialized).toContain('An internal error occurred while serving this request.')
    expect(serialized).not.toContain(rawBackendSignature)
  })

  it('unwraps non-error capability ToolResult content before building the public envelope', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: {
        content: { rows: [{ title: 'Brihat Jataka' }], total: 1 },
        is_error: false,
      },
    }))

    const result = await handler({ keyword: 'jataka' })
    const object = result.structuredContent.object as { content: Record<string, unknown> }

    expect(result.isError).toBeUndefined()
    expect(object.content).toEqual({ rows: [{ title: 'Brihat Jataka' }], total: 1 })
  })
})
