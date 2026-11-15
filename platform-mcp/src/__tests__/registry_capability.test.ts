import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Principal } from '../types.js'

const principal: Principal = { user_uid: 'fixture-user', key_id: 'fixture-key', role: 'client' }
let rpc: typeof import('../lib/registry_capability.js')
beforeEach(async () => {
  vi.resetModules()
  vi.stubEnv('PLATFORM_URL', 'https://fixture.invalid/')
  vi.stubEnv('MCP_INTERNAL_TOKEN', 'fixture-internal-token')
  rpc = await import('../lib/registry_capability.js')
})
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('shared raw registry RPC', () => {
  it('retains exact service/principal headers, timeout and outer-content return boundary', async () => {
    const inner = { is_error: false, content: { rules: [] } }
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ ok: true, content: inner }) }))
    vi.stubGlobal('fetch', fetchMock)
    const timeout = vi.spyOn(AbortSignal, 'timeout')
    await expect(rpc.callRegistryCapability('fixture-uri', { limit: 500 }, undefined, principal)).resolves.toBe(inner)
    expect(fetchMock).toHaveBeenCalledWith('https://fixture.invalid/api/retrieval/capability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-MCP-Internal-Token': 'fixture-internal-token', 'X-MCP-User': 'fixture-user', 'X-MCP-Key-Id': 'fixture-key' },
      body: JSON.stringify({ uri: 'fixture-uri', args: { limit: 500 } }),
      signal: expect.any(AbortSignal),
    })
    expect(timeout).toHaveBeenCalledWith(20_000)
  })

  it('keeps the ToolResult error wrapper for caller-specific handling', async () => {
    const inner = { is_error: true, content: { error: 'fixture error' } }
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ ok: true, content: inner }) })))
    await expect(rpc.callRegistryCapability('fixture-uri', {}, undefined, principal)).resolves.toBe(inner)
  })

  it('retains outer capability errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ ok: false, error: 'fixture error' }) })))
    await expect(rpc.callRegistryCapability('fixture-uri', {}, undefined, principal)).rejects.toThrow('[registry_bridge] capability error: fixture error')
  })

  it('reads the original HTTP error body and preserves entitlement denial', async () => {
    const body = JSON.stringify({ error: { class: 'entitlement_denied', message: 'fixture denial' }, denial: { chart_id: 'fixture-chart', permission_required: 'view' } })
    const text = vi.fn(async () => body)
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 403, text })))
    await expect(rpc.callRegistryCapability('fixture-uri', {}, undefined, principal)).rejects.toThrow(rpc.describeProxyFailure('fixture-uri', 403, body))
    expect(text).toHaveBeenCalledOnce()
  })

  it('retains generic HTTP-body truncation and unreadable-body fallback', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 502, text: async () => 'x'.repeat(250) })))
    await expect(rpc.callRegistryCapability('fixture-uri', {}, undefined, principal)).rejects.toThrow(`[registry_bridge] primitive call 'fixture-uri' failed (502): ${'x'.repeat(200)}`)
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 502, text: async () => { throw new Error('fixture') } })))
    await expect(rpc.callRegistryCapability('fixture-uri', {}, undefined, principal)).rejects.toThrow("[registry_bridge] primitive call 'fixture-uri' failed (502): ")
  })
})
