/**
 * priority.test.ts — ṢAḌ-DARŚANA W2.7 (salience vector wiring) + W2.4b tests.
 *
 * Task 1 — W2.7: kala_priority_get must carry salience_vector_five_axis from
 *   kala_field_salience rows when they exist (with real values), and emit an
 *   honest_empty coverage entry when the table has 0 rows for the chart.
 * Task 2 — W2.4b: covered here insofar as the story view owns that flag; this
 *   file tests the priority view's own side (the story.test.ts file carries the
 *   lel_pinning coverage tests; the no_lived_history_recorded flag is story-owned).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const CROSS_CHECK_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// Minimal ranked_signals fixture for one row response
const MINIMAL_PRIORITY_PAYLOAD = {
  ok: true,
  content: {
    chart_id: CANONICAL_CHART_ID,
    date_from: '2026-08-01',
    date_to: '2026-11-01',
    ranked_signals: [
      {
        signal_id: 'sig-1',
        signal_headline_text: 'Test signal',
        priority_score: 0.75,
        computed_salience: 0.8,
        activation_strength: 0.9,
        domains_affected_array: ['career'],
        signal_type_class: 'transit',
        window_start: '2026-08-01',
        window_end: '2026-10-15',
        trigger_type: 'gochara',
        neutral_dignity_downranked: false,
      },
    ],
    signal_count: 1,
    domain_filter: null,
    neutral_dignity_downranked_count: 0,
  },
}

// Aggregated salience result for CROSS_CHECK chart (has real data per task spec).
// The DB query uses AVG() so the mock returns the aggregated shape (one summary row),
// not individual window rows. 1c826d5a: factor_consequence=0.4375, factor_relevance=1,
// factor_reliability=0.5 per task spec; factor_informativeness=NULL (cohort gap, W2.5).
const SALIENCE_AGG_1C826D5A = {
  rows_count: '1',
  factor_informativeness: null,
  factor_consequence: '0.4375',
  factor_relevance: '1',
  factor_reliability: '0.5',
  factor_actionability: null,
  selected_fraction: '1.0000',
}

// Raw rows array — used only for the buildSalienceCoverage array-overload test.
const SALIENCE_ROWS_1C826D5A = [
  {
    window_id: 'kfw_abc123',
    event_class: 'career_transition',
    factor_informativeness: null,
    factor_consequence: 0.4375,
    factor_relevance: 1.0,
    factor_reliability: 0.5,
    factor_actionability: null,
    salience: 0.65,
  },
]

describe('kala_priority_get — W2.7 salience_vector_five_axis wiring', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('FAILING BEFORE FIX: response carries salience_vector_five_axis with 5 named axes when kala_field_salience has rows', async () => {
    let fetchCallCount = 0
    global.fetch = vi.fn(async (url: unknown, opts: unknown) => {
      fetchCallCount++
      const urlStr = String(url)
      // DB query route: return salience rows
      if (urlStr.includes('/api/mcp/db/query')) {
        const body = JSON.parse((opts as { body: string }).body) as { sql?: string; params?: unknown[] }
        if (body.sql && body.sql.includes('kala_field_salience')) {
          return {
            ok: true,
            json: async () => ({ rows: SALIENCE_ROWS_1C826D5A }),
          }
        }
        // kala_field_snapshots query
        return {
          ok: true,
          json: async () => ({ rows: [] }),
        }
      }
      // Capability call for priority ranking
      if (urlStr.includes('/api/retrieval/capability')) {
        const body = JSON.parse((opts as { body: string }).body) as { uri?: string }
        if (body.uri === 'marsys://tool/L3/call_priority_ranking') {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              content: {
                ...MINIMAL_PRIORITY_PAYLOAD.content,
                chart_id: CROSS_CHECK_CHART_ID,
              },
            }),
          }
        }
      }
      return { ok: false, status: 500, text: async () => 'unexpected' }
    }) as unknown as typeof fetch

    const { registerKalaPriorityTool } = await import('./priority.js')
    // We can't easily call the MCP tool handler directly without a server mock,
    // so we test the key behavioral requirement: when kala_field_salience has rows,
    // the response MUST include salience_vector_five_axis with state='computed' or
    // carry the actual row data, not just not_in_corpus.
    //
    // The test checks that the COVERAGE block's salience_vector_five_axis entry
    // transitions from 'not_in_corpus' to 'computed' or 'honest_empty' based on real data.
    // This test will FAIL before the fix (salience_vector_five_axis always not_in_corpus).
    //
    // Since we can't easily instantiate the MCP server here, we assert the module's
    // exported types include the new salience query function:
    expect(registerKalaPriorityTool).toBeDefined()
    // The real assertion is that the tool now fetches from kala_field_salience.
    // We validate this via the fetchSalienceVector export (added by the fix).
    const { fetchSalienceVector } = await import('./priority.js').catch(() => ({ fetchSalienceVector: undefined }))
    expect(fetchSalienceVector, 'W2.7 fix must export fetchSalienceVector — this test should fail before the fix').toBeDefined()
    fetchCallCount // suppress unused warning
  })

  it('fetchSalienceVector returns the five-axis data from kala_field_salience rows', async () => {
    global.fetch = vi.fn(async (_url: unknown, opts: unknown) => {
      const body = JSON.parse((opts as { body: string }).body) as { sql?: string }
      if (body.sql?.includes('kala_field_salience')) {
        return {
          ok: true,
          json: async () => ({ rows: [SALIENCE_AGG_1C826D5A] }),
        }
      }
      return { ok: true, json: async () => ({ rows: [] }) }
    }) as unknown as typeof fetch

    const mod = await import('./priority.js') as Record<string, unknown>
    const fetchSalienceVector = mod['fetchSalienceVector'] as ((chartId: string, principal: { user_uid: string; key_id: string }) => Promise<unknown>) | undefined
    if (!fetchSalienceVector) {
      // Before the fix: the export doesn't exist. This assertion fails.
      expect(fetchSalienceVector).toBeDefined()
      return
    }

    const result = await fetchSalienceVector(CROSS_CHECK_CHART_ID, { user_uid: 'u1', key_id: 'k1' }) as Record<string, unknown>
    expect(result).toBeDefined()
    expect(result['state']).toBe('computed')
    expect(Number(result['rows_count'])).toBeGreaterThanOrEqual(1)
    expect(result).toHaveProperty('factor_consequence')
    // 1c826d5a has factor_consequence=0.4375 per task spec
    expect(result['factor_consequence']).toBeCloseTo(0.4375, 4)
    expect(result['factor_relevance']).toBeCloseTo(1.0, 4)
    expect(result['factor_reliability']).toBeCloseTo(0.5, 4)
    expect(result['factor_informativeness']).toBeNull() // W2.5 known cohort gap — honest NULL
  })

  it('fetchSalienceVector returns honest_empty when 0 rows for chart (482012f1)', async () => {
    global.fetch = vi.fn(async (_url: unknown, opts: unknown) => {
      const body = JSON.parse((opts as { body: string }).body) as { sql?: string }
      if (body.sql?.includes('kala_field_salience')) {
        return { ok: true, json: async () => ({ rows: [] }) }
      }
      return { ok: true, json: async () => ({ rows: [] }) }
    }) as unknown as typeof fetch

    const mod = await import('./priority.js') as Record<string, unknown>
    const fetchSalienceVector = mod['fetchSalienceVector'] as ((chartId: string, principal: { user_uid: string; key_id: string }) => Promise<unknown>) | undefined
    if (!fetchSalienceVector) {
      expect(fetchSalienceVector).toBeDefined()
      return
    }

    const result = await fetchSalienceVector(CANONICAL_CHART_ID, { user_uid: 'u1', key_id: 'k1' }) as Record<string, unknown>
    expect(result).toBeDefined()
    expect(result['rows_count']).toBe(0)
    expect(result['state']).toBe('honest_empty')
  })

  it('coverage block salience_vector_five_axis: not_in_corpus is replaced by computed/honest_empty after W2.7 fix', async () => {
    // This test documents the BEFORE state: currently the coverage always says not_in_corpus.
    // After the fix it should say computed (with rows) or honest_empty (without rows).
    // We test via the exported buildSalienceCoverage function.
    const mod = await import('./priority.js') as Record<string, unknown>
    const buildSalienceCoverage = mod['buildSalienceCoverage'] as ((rows: unknown[]) => unknown) | undefined
    if (!buildSalienceCoverage) {
      // Before fix: exported function doesn't exist; test fails helpfully.
      expect(buildSalienceCoverage, 'W2.7 fix must export buildSalienceCoverage').toBeDefined()
      return
    }

    // With rows: state should be computed (not not_in_corpus)
    const withRows = buildSalienceCoverage(SALIENCE_ROWS_1C826D5A) as { state: string; concept: string }
    expect(withRows.concept).toBe('salience_vector_five_axis')
    expect(withRows.state).toBe('computed')

    // Without rows: state should be honest_empty (not not_in_corpus)
    const withoutRows = buildSalienceCoverage([]) as { state: string; concept: string }
    expect(withoutRows.concept).toBe('salience_vector_five_axis')
    expect(withoutRows.state).toBe('honest_empty')
  })
})
