/**
 * cross_scenario.test.ts — MCPT v3.2 Phase 9a: Cross-Scenario Equivalence.
 *
 * Verifies that the MCP chart_summary super-endpoint and the direct
 * query_chart_facts per-category path return IDENTICAL structured facts.
 *
 * Both paths read from the same chart_facts DB table via callPlatformPrimitive.
 * They must return equivalent Claim sets — any disagreement here is a routing
 * bug introduced during Phase 4 refactoring and must be surfaced, not papered over.
 *
 * If genuine factual disagreement is found, the test fails hard (no suppression).
 * The accuracy runner will write a cross_scenario.json artifact per §G of the plan.
 *
 * Design:
 *   - Uses vitest mocks (no live DB) — both paths receive identical structured mock data.
 *   - claim_extractor.ts converts raw DB rows → Claim objects deterministically.
 *   - diffClaims() compares by (source_category, subject, predicate) key.
 *   - 100% agreement expected: same table, same data, just different routing.
 *
 * MCPT v3.2 Phase 9a
 */

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { writeFileSync, mkdirSync } from 'fs'
import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { extractClaims, diffClaims } from './claim_extractor.js'
import type { ClaimDiffResult } from './claim_extractor.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ACCURACY_DIR = join(__dirname, '../../../accuracy')

// ── Set SERVICE_TOKEN to bypass GCP metadata fetch ─────────────────────────────
process.env['SERVICE_TOKEN'] = 'test-service-token'

// ── Mock fetch used by callPlatformPrimitive ──────────────────────────────────
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import tools after mocks are set up ──────────────────────────────────────
import { registerChartSummaryTool } from '../../src/tools/chart_summary.js'
import { registerQueryChartFacts } from '../../src/tools/query_chart_facts.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

function getGitSha(): string {
  try {
    return execSync('git rev-parse --short HEAD', { stdio: ['pipe', 'pipe', 'pipe'] })
      .toString()
      .trim()
  } catch {
    return 'unknown'
  }
}

function ensureAccuracyDir(): void {
  mkdirSync(ACCURACY_DIR, { recursive: true })
}

// ── Mock server factory ───────────────────────────────────────────────────────

type ToolHandler = (args: Record<string, unknown>) => Promise<{ content: Array<{ type: string; text: string }> }>

function makeMockServer() {
  const handlers = new Map<string, ToolHandler>()

  const server = {
    tool: vi.fn((
      name: string,
      _description: string,
      _schema: Record<string, unknown>,
      handler: ToolHandler
    ) => {
      handlers.set(name, handler)
    }),
  }

  return {
    server,
    callTool: async (name: string, args: Record<string, unknown>) => {
      const handler = handlers.get(name)
      if (!handler) throw new Error(`No handler registered for tool: ${name}`)
      return handler(args)
    },
  }
}

const MOCK_PRINCIPAL = {
  user_uid: 'test-uid',
  audience_tier: 'super_admin' as const,
  key_id: 'test-key-001',
}

// ── Canonical mock data ───────────────────────────────────────────────────────
//
// These represent the rows that the chart_facts DB would return.
// Both paths (chart_summary and direct query_chart_facts) read the same DB rows,
// so they must agree 100%.

const MOCK_PLANET_ROWS_D1 = [
  {
    fact_id: 'PLN.001',
    category: 'planet',
    divisional_chart: 'D1',
    planet_name: 'Sun',
    sign: 'Capricorn',
    house: 10,
    value_text: 'Sun in Capricorn 10H',
  },
  {
    fact_id: 'PLN.002',
    category: 'planet',
    divisional_chart: 'D1',
    planet_name: 'Moon',
    sign: 'Aquarius',
    house: 11,
    value_text: 'Moon in Aquarius 11H',
  },
  {
    fact_id: 'PLN.003',
    category: 'planet',
    divisional_chart: 'D1',
    planet_name: 'Saturn',
    sign: 'Libra',
    house: 7,
    value_text: 'Saturn in Libra 7H',
  },
]

const MOCK_HOUSE_ROWS_D1 = [
  {
    fact_id: 'HSE.001',
    category: 'house',
    divisional_chart: 'D1',
    house_number: 1,
    sign: 'Aries',
    lord: 'Mars',
  },
  {
    fact_id: 'HSE.007',
    category: 'house',
    divisional_chart: 'D1',
    house_number: 7,
    sign: 'Libra',
    lord: 'Venus',
  },
  {
    fact_id: 'HSE.010',
    category: 'house',
    divisional_chart: 'D1',
    house_number: 10,
    sign: 'Capricorn',
    lord: 'Saturn',
  },
]

const MOCK_YOGA_ROWS = [
  {
    fact_id: 'YGA.001',
    category: 'yoga',
    yoga_name: 'Hamsa Yoga',
    is_active: true,
    value_text: 'Hamsa Yoga active',
  },
  {
    fact_id: 'YGA.002',
    category: 'yoga',
    yoga_name: 'Bhadra Yoga',
    is_active: false,
    value_text: 'Bhadra Yoga partial',
  },
]

const MOCK_ARUDHA_ROWS = [
  {
    fact_id: 'ARU.001',
    category: 'arudha',
    arudha_name: 'AL',
    house_number: 1,
    sign: 'Aries',
  },
  {
    fact_id: 'ARU.007',
    category: 'arudha',
    arudha_name: 'A7',
    house_number: 7,
    sign: 'Libra',
  },
]

const MOCK_DASHA_ROWS = [
  {
    fact_id: 'DSH.001',
    category: 'dasha_vimshottari',
    dasha_lord: 'Moon',
    start_date: '2024-01-15',
    end_date: '2034-01-15',
  },
]

const MOCK_BIRTH_METADATA_ROWS = [
  {
    fact_id: 'BMD.001',
    category: 'birth_metadata',
    key: 'birth_date',
    value_text: '1984-02-05',
  },
  {
    fact_id: 'BMD.002',
    category: 'birth_metadata',
    key: 'lagna',
    value_text: 'Aries',
  },
]

const MOCK_SENSITIVE_POINT_ROWS = [
  {
    fact_id: 'SPS.001',
    category: 'sensitive_point',
    point_name: 'Rahu',
    sign: 'Gemini',
    house: 3,
  },
]

// Assembled bulk categories (non-divisional-sensitive)
const BULK_ROWS_BY_CATEGORY = {
  birth_metadata: MOCK_BIRTH_METADATA_ROWS,
  yoga: MOCK_YOGA_ROWS,
  arudha: MOCK_ARUDHA_ROWS,
  dasha_vimshottari: MOCK_DASHA_ROWS,
  sensitive_point: MOCK_SENSITIVE_POINT_ROWS,
}

// Divisional rows for D1 (planet + house)
const D1_ROWS_BY_CATEGORY = {
  planet: MOCK_PLANET_ROWS_D1,
  house: MOCK_HOUSE_ROWS_D1,
}

// Minimal D9/D10 for the multi-divisional test (different data to test that
// chart_summary correctly collects per-divisional rows)
const D9_PLANET_ROWS = [
  {
    fact_id: 'PLN.D9.001',
    category: 'planet',
    divisional_chart: 'D9',
    planet_name: 'Sun',
    sign: 'Scorpio',
    house: 8,
    value_text: 'Sun in Scorpio 8H (D9)',
  },
]

const D9_ROWS_BY_CATEGORY = {
  planet: D9_PLANET_ROWS,
  house: [],
}

// ── Platform mock response builder ────────────────────────────────────────────

function makeBatchedResponse(rowsByCategory: Record<string, unknown[]>) {
  return {
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        ok: true,
        result: { rows_by_category: rowsByCategory },
        trace_id: 'trace-cross-scenario-001',
        epistemics: { surgical: true, confidence_band: 'high' },
      }),
  }
}

function makeSingleCategoryResponse(rows: unknown[]) {
  return {
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        ok: true,
        result: { rows },
        trace_id: 'trace-cross-scenario-002',
        epistemics: { surgical: true, confidence_band: 'high' },
      }),
  }
}

// ── Helper: parse tool result text → JSON ─────────────────────────────────────

function parseToolResult(result: { content: Array<{ type: string; text: string }> }): unknown {
  return JSON.parse(result.content[0].text)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('MCPT v3.2 P9a — Cross-Scenario Equivalence: claim_extractor unit', () => {
  test('extractClaims handles empty output gracefully', () => {
    expect(extractClaims({ ok: true, rows: [] })).toHaveLength(0)
  })

  test('extractClaims handles null/undefined gracefully', () => {
    expect(extractClaims(null)).toHaveLength(0)
    expect(extractClaims(undefined)).toHaveLength(0)
    expect(extractClaims('not an object')).toHaveLength(0)
  })

  test('extractClaims extracts planet_placement from rows_by_category', () => {
    const claims = extractClaims({
      rows_by_category: {
        planet: [
          {
            fact_id: 'PLN.001',
            category: 'planet',
            divisional_chart: 'D1',
            planet_name: 'Saturn',
            sign: 'Libra',
            house: 7,
            value_text: 'Saturn in Libra 7H',
          },
        ],
      },
    })

    expect(claims.length).toBeGreaterThan(0)
    const placement = claims.find(c => c.subject === 'Saturn' && c.predicate === 'placed_in')
    expect(placement).toBeDefined()
    expect(placement?.type).toBe('planet_placement')
    expect(placement?.source_category).toBe('planet')
    expect(placement?.confidence).toBe(1.0)
  })

  test('extractClaims extracts yoga claims from rows_by_category', () => {
    const claims = extractClaims({
      rows_by_category: {
        yoga: MOCK_YOGA_ROWS,
      },
    })
    expect(claims.length).toBeGreaterThan(0)
    const hamsaClaim = claims.find(c => c.subject === 'Hamsa Yoga')
    expect(hamsaClaim).toBeDefined()
    expect(hamsaClaim?.type).toBe('yoga')
    expect(hamsaClaim?.predicate).toBe('is_active')
  })

  test('extractClaims extracts dasha claims', () => {
    const claims = extractClaims({
      rows_by_category: {
        dasha_vimshottari: MOCK_DASHA_ROWS,
      },
    })
    expect(claims.length).toBeGreaterThan(0)
    const startClaim = claims.find(c => c.predicate === 'active_from')
    expect(startClaim).toBeDefined()
    expect(startClaim?.subject).toBe('MD-Moon')
    expect(startClaim?.object).toBe('2024-01-15')
  })

  test('extractClaims extracts arudha claims', () => {
    const claims = extractClaims({
      rows_by_category: {
        arudha: MOCK_ARUDHA_ROWS,
      },
    })
    const alClaim = claims.find(c => c.subject === 'AL' && c.predicate === 'falls_in_house')
    expect(alClaim).toBeDefined()
    expect(alClaim?.object).toBe('1')
  })

  test('extractClaims extracts from flat rows[] with category field', () => {
    const flatRows = [
      ...MOCK_PLANET_ROWS_D1,
      ...MOCK_YOGA_ROWS,
    ]
    const claims = extractClaims({ rows: flatRows })
    expect(claims.length).toBeGreaterThan(0)
    const planetClaims = claims.filter(c => c.source_category === 'planet')
    const yogaClaims = claims.filter(c => c.source_category === 'yoga')
    expect(planetClaims.length).toBeGreaterThan(0)
    expect(yogaClaims.length).toBeGreaterThan(0)
  })

  test('extractClaims unwraps result envelope', () => {
    const claims = extractClaims({
      ok: true,
      result: {
        rows_by_category: {
          yoga: MOCK_YOGA_ROWS,
        },
      },
    })
    expect(claims.length).toBeGreaterThan(0)
  })

  test('diffClaims returns 100% for identical sets', () => {
    const claims = extractClaims({ rows_by_category: BULK_ROWS_BY_CATEGORY })
    const result = diffClaims(claims, claims)
    expect(result.agreement_pct).toBe(100)
    expect(result.disagreements).toHaveLength(0)
  })

  test('diffClaims returns 100% for two empty sets', () => {
    const result = diffClaims([], [])
    expect(result.agreement_pct).toBe(100)
    expect(result.disagreements).toHaveLength(0)
  })

  test('diffClaims detects object-value disagreement', () => {
    const setA = extractClaims({
      rows_by_category: {
        yoga: [{ fact_id: 'YGA.001', category: 'yoga', yoga_name: 'Hamsa Yoga', is_active: true }],
      },
    })
    // Same claim but different is_active value
    const setB = extractClaims({
      rows_by_category: {
        yoga: [{ fact_id: 'YGA.001', category: 'yoga', yoga_name: 'Hamsa Yoga', is_active: false }],
      },
    })
    const result = diffClaims(setA, setB)
    expect(result.agreement_pct).toBeLessThan(100)
    expect(result.disagreements.length).toBeGreaterThan(0)
  })

  test('diffClaims detects missing claim in set B', () => {
    const setA = extractClaims({
      rows_by_category: {
        yoga: MOCK_YOGA_ROWS,
      },
    })
    // Empty set B
    const setB: ReturnType<typeof extractClaims> = []
    const result = diffClaims(setA, setB)
    expect(result.agreement_pct).toBe(0)
    expect(result.disagreements.length).toBeGreaterThan(0)
  })
})

describe('MCPT v3.2 P9a — Cross-Scenario Equivalence: MCP path vs direct path', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('chart_summary(D1 only) and query_chart_facts per-category return same claims', async () => {
    const { server, callTool } = makeMockServer()

    // Register both tools
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    registerQueryChartFacts(
      server as unknown as Parameters<typeof registerQueryChartFacts>[0],
      () => MOCK_PRINCIPAL
    )

    // ── Path A: chart_summary with D1 only ──────────────────────────────────
    // Call 1: bulk categories (birth_metadata, yoga, arudha, dasha_vimshottari, sensitive_point)
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(BULK_ROWS_BY_CATEGORY))
    // Call 2: D1 planet + house
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(D1_ROWS_BY_CATEGORY))

    const summaryResult = await callTool('chart_summary', {
      divisional_charts: ['D1'],
    })
    const summaryEnvelope = parseToolResult(summaryResult)
    const claimsA = extractClaims(summaryEnvelope)

    // ── Path B: query_chart_facts per category (old pattern) ─────────────────
    // Each category is fetched separately with a flat rows response.
    // We use the same mock data to simulate the same DB table.

    // birth_metadata
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_BIRTH_METADATA_ROWS))
    // planet
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_PLANET_ROWS_D1))
    // house
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_HOUSE_ROWS_D1))
    // yoga
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_YOGA_ROWS))
    // arudha
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_ARUDHA_ROWS))
    // dasha_vimshottari
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_DASHA_ROWS))
    // sensitive_point
    mockFetch.mockResolvedValueOnce(makeSingleCategoryResponse(MOCK_SENSITIVE_POINT_ROWS))

    const categories = [
      'birth_metadata',
      'planet',
      'house',
      'yoga',
      'arudha',
      'dasha_vimshottari',
      'sensitive_point',
    ]
    const allRows: unknown[] = []
    for (const cat of categories) {
      const r = await callTool('query_chart_facts', { category: cat })
      const envelope = parseToolResult(r) as { ok: boolean; result?: { rows?: unknown[] } }
      if (envelope.ok && envelope.result?.rows) {
        allRows.push(...envelope.result.rows)
      }
    }
    const claimsB = extractClaims({ rows: allRows })

    // ── Compare ──────────────────────────────────────────────────────────────
    const diffResult: ClaimDiffResult = diffClaims(claimsA, claimsB)

    if (diffResult.disagreements.length > 0) {
      console.log('[cross_scenario] Disagreements found:')
      console.log(JSON.stringify(diffResult.disagreements, null, 2))
    }

    // Write result artifact to accuracy/cross_scenario.json
    ensureAccuracyDir()
    const gitSha = getGitSha()
    const artifact = {
      run_at: new Date().toISOString(),
      git_sha: gitSha,
      test: 'chart_summary_D1_vs_query_chart_facts_per_category',
      claims_path_a: claimsA.length,
      claims_path_b: claimsB.length,
      agreement_pct: diffResult.agreement_pct,
      total_compared: diffResult.total_compared,
      matching: diffResult.matching,
      disagreements: diffResult.disagreements,
      verdict: diffResult.agreement_pct === 100 ? 'pass' : 'accuracy_regression',
    }
    const crossScenarioPath = join(ACCURACY_DIR, 'cross_scenario.json')
    writeFileSync(crossScenarioPath, JSON.stringify(artifact, null, 2))
    console.log(`[cross_scenario] Artifact written to: ${crossScenarioPath}`)

    // The two paths read from the same DB table via the same primitive.
    // Any disagreement is a routing bug.
    expect(diffResult.agreement_pct).toBe(100)
    expect(diffResult.disagreements).toHaveLength(0)
  })

  test('chart_summary and batched query_chart_facts return same claims', async () => {
    const { server, callTool } = makeMockServer()

    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    registerQueryChartFacts(
      server as unknown as Parameters<typeof registerQueryChartFacts>[0],
      () => MOCK_PRINCIPAL
    )

    // ── Path A: chart_summary with D1 only ──────────────────────────────────
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(BULK_ROWS_BY_CATEGORY))
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(D1_ROWS_BY_CATEGORY))

    const summaryResult = await callTool('chart_summary', { divisional_charts: ['D1'] })
    const summaryEnvelope = parseToolResult(summaryResult)
    const claimsA = extractClaims(summaryEnvelope)

    // ── Path B: batched query_chart_facts in one call (categories array) ─────
    const allCategoryRows = {
      ...BULK_ROWS_BY_CATEGORY,
      planet: MOCK_PLANET_ROWS_D1,
      house: MOCK_HOUSE_ROWS_D1,
    }
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(allCategoryRows))

    const batchedResult = await callTool('query_chart_facts', {
      categories: [
        'birth_metadata',
        'planet',
        'house',
        'yoga',
        'arudha',
        'dasha_vimshottari',
        'sensitive_point',
      ],
    })
    const batchedEnvelope = parseToolResult(batchedResult) as {
      ok: boolean
      result?: { rows_by_category?: Record<string, unknown[]> }
    }
    const claimsB = extractClaims(batchedEnvelope)

    const diffResult = diffClaims(claimsA, claimsB)

    if (diffResult.disagreements.length > 0) {
      console.log('[cross_scenario] Batched disagreements:')
      console.log(JSON.stringify(diffResult.disagreements, null, 2))
    }

    expect(diffResult.agreement_pct).toBe(100)
    expect(diffResult.disagreements).toHaveLength(0)
  })

  test('chart_summary with D1+D9 collects all divisional rows without duplication', async () => {
    const { server, callTool } = makeMockServer()

    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )

    // Bulk call
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(BULK_ROWS_BY_CATEGORY))
    // D1 planet + house
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(D1_ROWS_BY_CATEGORY))
    // D9 planet + house
    mockFetch.mockResolvedValueOnce(makeBatchedResponse(D9_ROWS_BY_CATEGORY))

    const summaryResult = await callTool('chart_summary', { divisional_charts: ['D1', 'D9'] })
    const summaryEnvelope = parseToolResult(summaryResult) as {
      ok: boolean
      rows_by_category: Record<string, unknown[]>
      total_rows: number
    }

    expect(summaryEnvelope.ok).toBe(true)

    // D1 has 3 planet rows; D9 has 1 planet row → combined should be 4
    const planetRows = summaryEnvelope.rows_by_category['planet'] ?? []
    expect(planetRows.length).toBe(MOCK_PLANET_ROWS_D1.length + D9_PLANET_ROWS.length)

    // Confirm no D1 rows are duplicated
    const d1Rows = planetRows.filter(
      (r: unknown) => (r as Record<string, unknown>)['divisional_chart'] === 'D1'
    )
    expect(d1Rows.length).toBe(MOCK_PLANET_ROWS_D1.length)
  })
})
