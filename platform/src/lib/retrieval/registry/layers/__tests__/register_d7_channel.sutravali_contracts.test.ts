import { afterEach, describe, expect, it, vi } from 'vitest'
import { getCatalog } from '../../catalog'

function capability(uri: string) {
  const found = getCatalog().find((candidate) => candidate.uri === uri)
  if (!found) throw new Error(`Missing capability ${uri}`)
  return found
}

function successfulFetch(rows: readonly Record<string, unknown>[]) {
  return vi.fn(async () => ({ ok: true, status: 200, json: async () => rows }))
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Sutravali registry source-query contracts', () => {
  it('preserves every optional filter and the bounded response shape for the flexible query', async () => {
    const fetchMock = successfulFetch([{ rule_id: 'rule-1', text_id: 'bphs' }])
    vi.stubGlobal('fetch', fetchMock)

    const response = await capability('marsys://tool/L0/query_sutravali_rules').handler({
      planet: 'Saturn', house: 10, sign: 'Capricorn', antecedent_pattern: 'retrograde', limit: 250,
    })

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = (fetchMock.mock.calls as unknown as [string, RequestInit][])[0]!
    expect(url).toContain('/api/brahma/sutravali/query_rules')
    expect(init.method).toBe('POST')
    expect(JSON.parse(String(init.body))).toEqual({
      planet: 'Saturn', house: 10, sign: 'Capricorn', antecedent_pattern: 'retrograde', limit: 200,
    })
    expect(response).toEqual({
      content: {
        rules: [{ rule_id: 'rule-1', text_id: 'bphs' }],
        returned_count: 1,
        filters: { planet: 'Saturn', house: 10, sign: 'Capricorn', antecedent_pattern: 'retrograde', limit: 200 },
      },
      is_error: false,
    })
  })

  it('requires text_id before querying and retains deterministic limit/offset pagination on the text route', async () => {
    const textCapability = capability('marsys://tool/L0/list_sutravali_rules_by_text')
    await expect(textCapability.handler({})).resolves.toEqual({ content: { error: 'text_id is required' }, is_error: true })

    const fetchMock = successfulFetch([{ rule_id: 'rule-2' }])
    vi.stubGlobal('fetch', fetchMock)
    const response = await textCapability.handler({ text_id: 'bphs', limit: 999, offset: 50 })

    expect(fetchMock).toHaveBeenCalledOnce()
    expect(String((fetchMock.mock.calls as unknown as [string, RequestInit][])[0]![0])).toContain('list_rules_by_text/bphs?limit=500&offset=50')
    expect(response).toEqual({
      content: { rules: [{ rule_id: 'rule-2' }], returned_count: 1, text_id: 'bphs', limit: 500, offset: 50 },
      is_error: false,
    })
  })

  // R3 boundary ("remaining residual classification", packet 4): query_rules_for_planet's
  // sidecar route (python-sidecar/routers/sutravali.py) used to bind two parameters for one
  // SQL placeholder and could never succeed — see
  // python-sidecar/tests/test_sutravali_query_rules_for_planet.py for the sidecar-side fix and
  // regression test. This capability is now contracted
  // (source-query:query-sutravali-rules-for-planet:v1) — this test covers the TypeScript-side
  // request construction the way its two siblings above already do.
  it('builds the planet-scoped query string and forwards rows for query_sutravali_rules_for_planet', async () => {
    const fetchMock = successfulFetch([{ rule_id: 'rule-3', text_id: 'bphs' }])
    vi.stubGlobal('fetch', fetchMock)

    const response = await capability('marsys://tool/L0/query_sutravali_rules_for_planet').handler({
      planet: 'Saturn', house: 10, limit: 999,
    })

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url] = (fetchMock.mock.calls as unknown as [string, RequestInit][])[0]!
    expect(String(url)).toContain('/api/brahma/sutravali/query_rules_for_planet?')
    expect(String(url)).toContain('planet=Saturn')
    expect(String(url)).toContain('house=10')
    expect(String(url)).toContain('limit=500') // clamped to the 500 max
    expect(response).toEqual({
      content: { rules: [{ rule_id: 'rule-3', text_id: 'bphs' }], returned_count: 1, planet: 'Saturn', limit: 500 },
      is_error: false,
    })
  })

  it('requires planet before querying', async () => {
    const planetCapability = capability('marsys://tool/L0/query_sutravali_rules_for_planet')
    await expect(planetCapability.handler({})).resolves.toEqual({ content: { error: 'planet is required' }, is_error: true })
  })
})
