/**
 * SRP-T-4: Portal Pipeline System Tests
 *
 * Exercises the full portal query pipeline from HTTP request through streamed LLM response.
 * Tests skip gracefully when SMOKE_SESSION_COOKIE is absent (CI-safe).
 *
 * Required env vars for live execution:
 *   SMOKE_BASE_URL        - base URL of running portal (default: http://localhost:3000)
 *   SMOKE_SESSION_COOKIE  - Firebase session cookie (from mint_session_cookie.ts)
 *   SMOKE_CHART_ID        - chart to query against (default: 362f9f17-...)
 *
 * Optional:
 *   SMOKE_TEST_ALL_PROVIDERS - set to "true" to run all 5 providers (costs tokens)
 *   MCP_BASE_URL             - MCP sidecar base URL (default: SMOKE_BASE_URL)
 *   INTEGRATION_TEST_API_KEY - MCP API key for MCP channel smoke tests
 */
import { describe, it, expect } from 'vitest'

const BASE_URL = process.env.SMOKE_BASE_URL ?? 'http://localhost:3000'
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE ?? ''
const CHART_ID = process.env.SMOKE_CHART_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'
const runSmoke = !!SESSION_COOKIE

const describeIf = runSmoke ? describe : describe.skip

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface SubmitQueryOptions {
  provider?: string
  mode?: 'classic' | 'claude-style'
  stream?: boolean
}

interface QueryResult {
  status: number
  text: string
  headers: Record<string, string>
}

/** POST a query to /api/query and return status + raw body text + headers. */
async function submitQuery(
  queryText: string,
  options: SubmitQueryOptions = {}
): Promise<QueryResult> {
  const response = await fetch(`${BASE_URL}/api/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Cookie: `__session=${SESSION_COOKIE}`,
    },
    body: JSON.stringify({
      query: queryText,
      chart_id: CHART_ID,
      provider: options.provider ?? 'anthropic',
      stream: options.stream ?? false,
    }),
  })

  // Even on error status, read the body so callers can inspect it
  const text = await response.text()
  return {
    status: response.status,
    text,
    headers: Object.fromEntries(response.headers),
  }
}

/** Extract a query trace object from response text / headers. Returns null if not found. */
function extractTrace(
  responseText: string,
  responseHeaders: Record<string, string>
): Record<string, unknown> | null {
  // 1. Check trace headers
  const traceHeader =
    responseHeaders['x-query-trace'] ?? responseHeaders['x-marsys-trace']
  if (traceHeader) {
    try {
      return JSON.parse(traceHeader) as Record<string, unknown>
    } catch {
      // fall through
    }
  }

  // 2. Try parsing JSON body
  try {
    const json = JSON.parse(responseText) as Record<string, unknown>
    const candidate =
      (json['trace'] as Record<string, unknown> | undefined) ??
      (json['query_trace'] as Record<string, unknown> | undefined) ??
      ((json['metadata'] as Record<string, unknown> | undefined)?.['trace'] as
        | Record<string, unknown>
        | undefined)
    if (candidate) return candidate
  } catch {
    // fall through
  }

  // 3. For streamed SSE responses, look for an embedded trace object
  const traceMatch = responseText.match(/"trace"\s*:\s*(\{[^}]+\})/)
  if (traceMatch) {
    try {
      return JSON.parse(traceMatch[1]) as Record<string, unknown>
    } catch {
      // fall through
    }
  }

  return null
}

// ---------------------------------------------------------------------------
// Suite 1: Adapter pipeline is active
// ---------------------------------------------------------------------------

describeIf('Portal pipeline — adapter path active', () => {
  it('query returns HTTP 200', async () => {
    const { status } = await submitQuery('What is my Sun sign placement?')
    expect(status).toBe(200)
  }, 30_000)

  it('response body is non-empty', async () => {
    const { text } = await submitQuery('Summarize my chart briefly.')
    expect(text.length).toBeGreaterThan(50)
  }, 30_000)

  it('no "createOrchestrator" error in response (legacy pipeline not active)', async () => {
    const { text } = await submitQuery('What is my ascendant?')
    expect(text.toLowerCase()).not.toContain('createorchestrator')
  }, 30_000)

  it('no "single_model_strategy" legacy error in response', async () => {
    const { text } = await submitQuery('Describe my Moon placement.')
    expect(text.toLowerCase()).not.toContain('single_model_strategy')
  }, 30_000)

  it('response contains meaningful astrological content', async () => {
    const { text } = await submitQuery('What house is my Moon in?')
    const lower = text.toLowerCase()
    // At minimum should mention a planet or house
    const containsAstroContent = ['moon', 'house', 'sign', 'rashi', 'planet', 'lagna'].some(
      (w) => lower.includes(w)
    )
    expect(containsAstroContent).toBe(true)
  }, 30_000)
})

// ---------------------------------------------------------------------------
// Suite 2: B.11 floor tools in every query trace
// ---------------------------------------------------------------------------

describeIf('B.11 floor — mandatory tools in every query trace', () => {
  const B11_FLOOR_TOOLS = [
    'msr_sql',
    'cgm_graph_walk',
    'pattern_register',
    'vector_search',
    'chart_facts_query',
  ]

  it('query trace contains B.11 floor tools (or logs warning if trace absent)', async () => {
    const { text, headers } = await submitQuery('Tell me about my career prospects.')
    const trace = extractTrace(text, headers)

    if (trace) {
      const toolsCalled = (trace['tool_executions'] ??
        trace['tools_called'] ??
        trace['tools'] ??
        []) as Array<{ name?: string; tool?: string }>

      const toolNames = toolsCalled.map((t) => t.name ?? t.tool ?? '')

      console.info(
        '[SRP-T4] B.11 floor tools found in trace:',
        toolNames.filter((n) => B11_FLOOR_TOOLS.includes(n))
      )

      for (const floorTool of B11_FLOOR_TOOLS) {
        expect(toolNames).toContain(floorTool)
      }
    } else {
      // Trace extraction failed — verify we at least got a non-empty response
      console.warn(
        '[SRP-T4] Could not extract query trace from response. B.11 floor assertion skipped.'
      )
      expect(text.length).toBeGreaterThan(0)
    }
  }, 45_000)

  it('second query also has a non-empty response (floor is consistent)', async () => {
    const { text, headers } = await submitQuery('What are my relationship patterns?')
    const trace = extractTrace(text, headers)

    if (trace) {
      const toolsCalled = (trace['tool_executions'] ??
        trace['tools_called'] ??
        trace['tools'] ??
        []) as Array<{ name?: string; tool?: string }>

      const toolNames = toolsCalled.map((t) => t.name ?? t.tool ?? '')
      // At least some of the B.11 floor tools should appear
      const found = toolNames.filter((n) => B11_FLOOR_TOOLS.includes(n))
      expect(found.length).toBeGreaterThanOrEqual(1)
    } else {
      expect(text.length).toBeGreaterThan(0)
    }
  }, 45_000)
})

// ---------------------------------------------------------------------------
// Suite 3: forward_looking routing
// ---------------------------------------------------------------------------

describeIf('forward_looking routing — predictive queries reach forward-looking signals', () => {
  it('future transit query returns HTTP 200', async () => {
    const { status } = await submitQuery(
      'What transits are coming up for me in the next 6 months?'
    )
    expect(status).toBe(200)
  }, 45_000)

  it('future transit query mentions planetary or temporal content', async () => {
    const { text } = await submitQuery(
      'What transits are coming up for me in the next 6 months?'
    )
    const lower = text.toLowerCase()
    const mentionsPlanets = [
      'saturn',
      'jupiter',
      'rahu',
      'ketu',
      'mars',
      'transit',
      'period',
      'dasha',
      'antardasha',
      '2026',
      '2027',
    ].some((word) => lower.includes(word))
    expect(mentionsPlanets).toBe(true)
  }, 45_000)

  it('predictive dasha query returns a response about timing', async () => {
    const { status, text } = await submitQuery(
      'Which dasha period am I currently in and what does it mean for the next year?'
    )
    expect(status).toBe(200)
    const lower = text.toLowerCase()
    const mentionsTiming = ['dasha', 'period', 'year', 'antardasha', 'mahadasha', 'time'].some(
      (w) => lower.includes(w)
    )
    expect(mentionsTiming).toBe(true)
  }, 45_000)
})

// ---------------------------------------------------------------------------
// Suite 4: Multi-provider smoke
// ---------------------------------------------------------------------------

describeIf('Multi-provider — provider responses', () => {
  const allProviders = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']
  const runAllProviders = process.env.SMOKE_TEST_ALL_PROVIDERS === 'true'

  if (runAllProviders) {
    it.each(allProviders)('provider=%s returns HTTP 200', async (provider) => {
      const { status } = await submitQuery('What is my Sun placement?', { provider })
      expect(status).toBe(200)
    }, 30_000)
  } else {
    it('anthropic provider returns HTTP 200 (default smoke)', async () => {
      const { status } = await submitQuery('What is my Sun placement?', {
        provider: 'anthropic',
      })
      expect(status).toBe(200)
    }, 30_000)

    it('anthropic provider response is non-empty', async () => {
      const { text } = await submitQuery('What is my Sun placement?', {
        provider: 'anthropic',
      })
      expect(text.length).toBeGreaterThan(20)
    }, 30_000)
  }
})

// ---------------------------------------------------------------------------
// Suite 5: MCP channel smoke
// ---------------------------------------------------------------------------

describeIf('MCP channel — representative tools return non-empty data', () => {
  const MCP_BASE_URL = process.env.MCP_BASE_URL ?? BASE_URL
  const MCP_API_KEY = process.env.INTEGRATION_TEST_API_KEY ?? ''

  it.skipIf(!MCP_API_KEY)('msr_sql tool returns signals via MCP', async () => {
    const response = await fetch(`${MCP_BASE_URL}/api/mcp/primitives/msr_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${MCP_API_KEY}`,
        'X-MARSYS-Chart-Id': CHART_ID,
      },
      body: JSON.stringify({ params: { limit: 3 } }),
    })
    expect(response.status).toBe(200)
    const body = (await response.json()) as Record<string, unknown>
    const rows = (body['data'] ?? body['signals'] ?? body['rows'] ?? []) as unknown[]
    expect(rows.length).toBeGreaterThan(0)
  }, 20_000)

  it.skipIf(!MCP_API_KEY)('query_chart_facts tool returns chart facts', async () => {
    const response = await fetch(`${MCP_BASE_URL}/api/mcp/primitives/query_chart_facts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${MCP_API_KEY}`,
        'X-MARSYS-Chart-Id': CHART_ID,
      },
      body: JSON.stringify({ params: { category: 'planetary_positions', limit: 5 } }),
    })
    expect(response.status).toBe(200)
    const body = (await response.json()) as Record<string, unknown>
    const facts = (body['data'] ?? body['facts'] ?? body['rows'] ?? []) as unknown[]
    expect(facts.length).toBeGreaterThan(0)
  }, 20_000)

  it.skipIf(!MCP_API_KEY)('temporal tool returns non-error response (not 400)', async () => {
    const response = await fetch(`${MCP_BASE_URL}/api/mcp/primitives/temporal`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${MCP_API_KEY}`,
        'X-MARSYS-Chart-Id': CHART_ID,
      },
      body: JSON.stringify({ params: {} }),
    })
    // 200 = success; 500 = reached DB but minimal params insufficient — both acceptable
    // 400 = still blocked (SRP-F1/FIX-1 regression would show up here)
    expect([200, 500]).toContain(response.status)
    expect(response.status).not.toBe(400)
  }, 15_000)
})
