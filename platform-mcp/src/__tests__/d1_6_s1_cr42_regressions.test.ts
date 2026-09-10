/**
 * D-1.6 S-1 — CR-42/R-19/R-20 regression tests (Phase-1 verifier rejection fix).
 *
 * Covers the two gaps the Phase-1 verifier flagged as untested on the flagship
 * "no silent wrong answer" fix:
 *
 *   1. bodha_remedies_get / bodha_remedies_search: `graha`/`planet` are now declared
 *      in the tool's zod schema, AND the `paramAliases` mapping (planet -> graha) is
 *      actually applied before the request reaches the underlying registry capability
 *      — guards against the exact SDK silent-param-strip regression that WAS the bug
 *      (a param not in the declared schema is dropped by the MCP SDK before the
 *      handler ever sees it).
 *   2. ref_dignity_reference_get(planet:'saturn') returns source:'bg_dignity_reference'
 *      with real structured rows, not the old classical_text_fallback corpus dump.
 *
 * `fetch` is mocked globally — no live PLATFORM_URL/DB required.
 */
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok, status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }
}

const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

// ── 1. bodha_remedies_get / bodha_remedies_search — schema + paramAliases ──────

describe('bodha_remedies_get / bodha_remedies_search — graha/planet schema + paramAliases (CR-42)', () => {
  const registeredSchemas = new Map<string, Record<string, unknown>>()
  const registeredHandlers = new Map<string, (params: Record<string, unknown>) => Promise<unknown>>()

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, _desc: string, schema: Record<string, unknown>, handler: (params: Record<string, unknown>) => Promise<unknown>) => {
        registeredSchemas.set(name, schema)
        registeredHandlers.set(name, handler)
      },
    } as unknown as McpServer
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('bodha_remedies_get declares both graha and planet in its zod schema', () => {
    const schema = registeredSchemas.get('bodha_remedies_get')
    expect(schema).toBeDefined()
    expect(Object.keys(schema!)).toContain('graha')
    expect(Object.keys(schema!)).toContain('planet')
  })

  it('bodha_remedies_search declares both graha and planet in its zod schema', () => {
    const schema = registeredSchemas.get('bodha_remedies_search')
    expect(schema).toBeDefined()
    expect(Object.keys(schema!)).toContain('graha')
    expect(Object.keys(schema!)).toContain('planet')
  })

  it('bodha_remedies_get: a caller-supplied `planet` is forwarded to the capability call AS `graha` (paramAliases applied)', async () => {
    // F-125: bodha_remedies_get now also carries the B.11 orientation gate
    // (requiresOrientation: true), so it issues a SECOND fetch call
    // (marsys://tool/L2/query_ucd) after the primary capability call — both mocked here.
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { resonances: [], prescriptions: [] } }))
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { content: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', entity_profiles: [] }, is_error: false } }))
    const handler = registeredHandlers.get('bodha_remedies_get')!
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', planet: 'Saturn' })

    expect(mockFetch).toHaveBeenCalledTimes(2)
    const body = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as {
      uri: string
      args: Record<string, unknown>
    }
    expect(body.uri).toBe('marsys://tool/L2/query_remedies')
    // The alias-only param name must NOT survive to the capability call...
    expect(body.args['planet']).toBeUndefined()
    // ...and its value must have landed on the capability's real param name.
    expect(body.args['graha']).toBe('Saturn')

    // The second call is the B.11 orientation pre-fetch (F-125) — same chart_id.
    const secondBody = JSON.parse((mockFetch.mock.calls[1][1] as { body: string }).body) as {
      uri: string
      args: Record<string, unknown>
    }
    expect(secondBody.uri).toBe('marsys://tool/L2/query_ucd')
    expect(secondBody.args['chart_id']).toBe('482012f1-710e-4a25-994a-93821f5871aa')
  })

  it('bodha_remedies_search: a caller-supplied `planet` is forwarded as `graha` too', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { resonances: [], prescriptions: [] } }))
    const handler = registeredHandlers.get('bodha_remedies_search')!
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', planet: 'saturn' })

    const body = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as {
      args: Record<string, unknown>
    }
    expect(body.args['planet']).toBeUndefined()
    expect(body.args['graha']).toBe('saturn')
  })

  it('when the caller supplies `graha` directly (not via the `planet` alias), it is forwarded unchanged', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { resonances: [], prescriptions: [] } }))
    const handler = registeredHandlers.get('bodha_remedies_get')!
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', graha: 'Venus' })

    const body = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as {
      args: Record<string, unknown>
    }
    expect(body.args['graha']).toBe('Venus')
    expect(body.args['planet']).toBeUndefined()
  })
})

// ── 2. ref_dignity_reference_get — structured table, not classical-text fallback ──

describe('ref_dignity_reference_get(planet) — structured bg_dignity_reference source, not classical_text_fallback (CR-42)', () => {
  let handler: (params: Record<string, unknown>) => Promise<{ structuredContent: { object: unknown } }>

  beforeAll(async () => {
    const { registerP1ReferenceTools } = await import('../tools/register_p1_reference.js')
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, h: typeof handler) => {
        if (name === 'ref_dignity_reference_get') handler = h
      },
    } as unknown as McpServer
    registerP1ReferenceTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('planet:"saturn" returns source:"bg_dignity_reference" with a real structured Saturn row, no corpus dump', async () => {
    // First fetch call is the platformQuery() hit against bg_dignity_reference.
    mockFetch.mockResolvedValueOnce(jsonResponse({
      rows: [{
        graha: 'Saturn',
        exaltation_sign: 'Libra',
        exaltation_degree: 20,
        debilitation_sign: 'Aries',
        debilitation_degree: 20,
        moolatrikona_sign: 'Aquarius',
        moolatrikona_from: 0,
        moolatrikona_to: 20,
        own_signs: ['Capricorn', 'Aquarius'],
        classical_citation: 'BPHS ch.4',
        notes: null,
      }],
    }))

    const result = await handler({ planet: 'saturn' })
    const obj = result.structuredContent.object as {
      content: {
        source: string
        structured_filter_applied: boolean
        planet: string
        rows: Array<{ graha: string; exaltation_sign: string }>
        total: number
      }
    }

    expect(obj.content.source).toBe('bg_dignity_reference')
    expect(obj.content.structured_filter_applied).toBe(true)
    expect(obj.content.total).toBe(1)
    expect(obj.content.rows[0].graha).toBe('Saturn')
    expect(obj.content.rows[0].exaltation_sign).toBe('Libra')
    // Never the old degraded corpus-search shape on a successful structured match.
    expect(obj.content.source).not.toBe('classical_text_fallback')

    // Only ONE fetch call was made — the structured DB query — no fallback hybrid
    // search call to query_classical_texts was ever issued.
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('falls back to classical_text_fallback (labelled honestly) only when no structured row matches', async () => {
    // First call: platformQuery() against bg_dignity_reference returns no rows.
    mockFetch.mockResolvedValueOnce(jsonResponse({ rows: [] }))
    // Second call: callRegistryCapability() hybrid search fallback.
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: { search_mode: 'hybrid_vector_keyword', query_used: 'not-a-real-planet dignity', citations: [], rows: [], total: 0 },
    }))

    const result = await handler({ planet: 'not-a-real-planet' })
    const obj = result.structuredContent.object as {
      content: { source: string; structured_filter_applied: boolean; fallback_reason: string }
    }

    expect(obj.content.source).toBe('classical_text_fallback')
    expect(obj.content.structured_filter_applied).toBe(false)
    expect(obj.content.fallback_reason).toMatch(/No structured bg_dignity_reference row/)
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })
})
