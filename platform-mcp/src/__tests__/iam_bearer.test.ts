/**
 * iam_bearer.test.ts — Wave 4 4.edge_and_infra_hygiene
 *
 * Verifies that platform-mcp/src/client.ts:
 *   1. Sends an Authorization: Bearer <token> header on every outbound platform call.
 *   2. Sends the X-MCP-Internal-Token header alongside.
 *   3. Honours the SERVICE_TOKEN env-var override (used by this test in lieu of
 *      a live GCP metadata server / ADC).
 *
 * This is the test referenced in BRIEF_4_edge_and_infra_hygiene.md acceptance
 * item 3: "platform-mcp/src/client.ts adds IAM bearer (audited via grep + unit test)."
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const TEST_TOKEN = 'test-id-token-deadbeef'
const TEST_INTERNAL = 'test-internal-token'
const TEST_PLATFORM_URL = 'http://platform.test'

describe('platform-mcp client — IAM bearer + internal token discipline', () => {
  beforeEach(() => {
    vi.resetModules()
    process.env['SERVICE_TOKEN'] = TEST_TOKEN
    process.env['MCP_INTERNAL_TOKEN'] = TEST_INTERNAL
    process.env['PLATFORM_URL'] = TEST_PLATFORM_URL
  })

  afterEach(() => {
    delete process.env['SERVICE_TOKEN']
    delete process.env['MCP_INTERNAL_TOKEN']
    delete process.env['PLATFORM_URL']
    vi.restoreAllMocks()
  })

  it('callPlatformPrimitive sends Authorization: Bearer + X-MCP-Internal-Token', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true, trace_id: 't1', data: {} }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const { callPlatformPrimitive } = await import('../client.js')

    await callPlatformPrimitive(
      'chart_facts_query',
      { native_key: 'native' },
      { user_uid: 'u1', key_id: 'k1' } as any
    )

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const call = fetchSpy.mock.calls[0]!
    const init = call[1] as RequestInit
    const headers = init.headers as Record<string, string>

    expect(headers['Authorization']).toBe(`Bearer ${TEST_TOKEN}`)
    expect(headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL)
    expect(headers['X-MCP-User']).toBe('u1')
    expect(headers['X-MCP-Key-Id']).toBe('k1')
  })

  it('callPlatformTrace (GET) sends Authorization: Bearer + X-MCP-Internal-Token', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true, trace_id: 'abc', data: {} }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const { callPlatformTrace } = await import('../client.js')

    await callPlatformTrace('abc', { user_uid: 'u1', key_id: 'k1' } as any)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const init = fetchSpy.mock.calls[0]![1] as RequestInit
    const headers = init.headers as Record<string, string>

    expect(headers['Authorization']).toBe(`Bearer ${TEST_TOKEN}`)
    expect(headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL)
  })

  it('callPlatformRecent (GET) sends Authorization: Bearer + X-MCP-Internal-Token', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true, trace_id: 't', data: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const { callPlatformRecent } = await import('../client.js')

    await callPlatformRecent({ limit: 5 }, { user_uid: 'u1', key_id: 'k1' } as any)

    const init = fetchSpy.mock.calls[0]![1] as RequestInit
    const headers = init.headers as Record<string, string>

    expect(headers['Authorization']).toBe(`Bearer ${TEST_TOKEN}`)
    expect(headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL)
  })
})
