import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function failedResponse(body: string) {
  return {
    ok: false,
    status: 500,
    json: async () => ({ detail: body }),
    text: async () => body,
  }
}

const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

describe('F90 sidecar failure sanitization', () => {
  const handlers = new Map<string, (params: Record<string, unknown>) => Promise<{
    isError?: boolean
    structuredContent: { object: unknown }
  }>>()

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, _description: string, _schema: unknown, handler: (params: Record<string, unknown>) => Promise<unknown>) => {
        handlers.set(name, handler as (params: Record<string, unknown>) => Promise<{
          isError?: boolean
          structuredContent: { object: unknown }
        }>)
      },
    } as unknown as McpServer
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
    vi.restoreAllMocks()
  })

  it('does not disclose a sidecar POST failure body through kala_muhurta_get', async () => {
    const rawSidecarDetail = 'database trace: relation private_internal_state does not exist'
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    mockFetch.mockResolvedValueOnce(failedResponse(rawSidecarDetail))

    const result = await handlers.get('kala_muhurta_get')!({
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    })

    expect(result.isError).toBe(true)
    expect(JSON.stringify(result.structuredContent.object)).not.toContain(rawSidecarDetail)
    expect(JSON.stringify(result.structuredContent.object)).toContain('sidecar service unavailable')
    expect(errorSpy).toHaveBeenCalledWith(expect.stringContaining('sidecar POST failure'))
    expect(errorSpy).not.toHaveBeenCalledWith(expect.stringContaining(rawSidecarDetail))
  })

  it('does not disclose a sidecar GET failure body through ref_planet_position_get', async () => {
    const rawSidecarDetail = 'database trace: invalid internal ephemeris payload'
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    mockFetch.mockResolvedValueOnce(failedResponse(rawSidecarDetail))

    const result = await handlers.get('ref_planet_position_get')!({ date: '2026-08-19' })

    expect(result.isError).toBe(true)
    expect(JSON.stringify(result.structuredContent.object)).not.toContain(rawSidecarDetail)
    expect(JSON.stringify(result.structuredContent.object)).toContain('sidecar service unavailable')
    expect(errorSpy).toHaveBeenCalledWith(expect.stringContaining('sidecar GET failure'))
    expect(errorSpy).not.toHaveBeenCalledWith(expect.stringContaining(rawSidecarDetail))
  })
})
