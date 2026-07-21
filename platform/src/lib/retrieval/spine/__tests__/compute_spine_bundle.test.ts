/**
 * compute_spine_bundle.test.ts — unit tests for the spine bundle join.
 *
 * Mocks '@/lib/db/client' (the single query() entry point every underlying
 * capability — query_signals/query_temporal_activation/query_predictive_anchors/
 * query_calibration — calls through). Asserts the composition correctly threads
 * signal_id across all three downstream layers and the honest-empty path when
 * no signals are found.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { computeSpineBundle } from '../compute_spine_bundle'

const CHART_A = '11111111-1111-1111-1111-111111111111'

function sqlContains(sql: string, needle: string): boolean {
  return sql.replace(/\s+/g, ' ').includes(needle)
}

/**
 * Routes the shared queryMock to the right fixture based on which table the SQL
 * text targets — mirrors how each underlying capability issues its own distinct
 * SQL text, so one mock can serve all four composed capabilities correctly.
 */
function installFixtures(opts: {
  signals?: Array<Record<string, unknown>>
  activations?: Array<Record<string, unknown>>
  predicates?: Array<Record<string, unknown>>
  anchors?: Array<Record<string, unknown>>
  verdicts?: Array<Record<string, unknown>>
  reliability?: Array<Record<string, unknown>>
  multipliers?: Array<Record<string, unknown>>
  qa?: Array<Record<string, unknown>>
}) {
  queryMock.mockImplementation(async (sql: string) => {
    if (sqlContains(sql, 'FROM information_schema.columns')) {
      return { rows: [] } // no optional MSR-elevation columns present
    }
    // NOTE ON ORDER: query_temporal_activation.ts's activation SQL embeds a correlated
    // scalar subquery `(SELECT ... FROM bodha_msr_signals ms WHERE ...)` INSIDE its
    // `FROM kala_activation` query, so the raw SQL text contains BOTH substrings. The
    // kala_activation_predicates / kala_activation checks below MUST be tested before
    // the bare 'FROM bodha_msr_signals' branch, or every activation-table query would
    // be misrouted to the signals fixture (caught by this test suite's own assertions
    // the first time it was written — see compute_spine_bundle.ts's actual production
    // SQL, not a hypothetical).
    if (sqlContains(sql, 'FROM kala_activation_predicates')) {
      return { rows: opts.predicates ?? [] }
    }
    if (sqlContains(sql, 'FROM kala_activation')) {
      return { rows: opts.activations ?? [] }
    }
    if (sqlContains(sql, 'FROM bodha_msr_signals')) {
      return { rows: opts.signals ?? [] }
    }
    if (sqlContains(sql, 'FROM phala_anchors')) {
      return { rows: opts.anchors ?? [] }
    }
    if (sqlContains(sql, 'FROM mimamsa_calibration')) {
      return { rows: opts.verdicts ?? [] }
    }
    if (sqlContains(sql, 'FROM mimamsa_reliability')) {
      return { rows: opts.reliability ?? [] }
    }
    if (sqlContains(sql, 'FROM mimamsa_multipliers')) {
      return { rows: opts.multipliers ?? [] }
    }
    if (sqlContains(sql, 'FROM mimamsa_qa_eval')) {
      return { rows: opts.qa ?? [] }
    }
    return { rows: [] }
  })
}

describe('computeSpineBundle', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })

  it('threads signal_id across activation windows and phala anchors', async () => {
    installFixtures({
      signals: [
        { signal_id: 'SIG-1', signal_headline_text: 'Jupiter in 10th', computed_salience: 0.9, domains_affected_array: ['career'], valence: 'positive' },
        { signal_id: 'SIG-2', signal_headline_text: 'Saturn aspect', computed_salience: 0.5, domains_affected_array: ['career'], valence: 'mixed' },
      ],
      activations: [
        { id: 1, signal_id: 'SIG-1', activation_start: '2020-01-01', activation_end: '2021-01-01' },
      ],
      anchors: [
        { anchor_id: 'A-1', signal_id: 'SIG-1', domain: 'career', magnitude: 0.7 },
        { anchor_id: 'A-2', signal_id: 'SIG-3', domain: 'career', magnitude: 0.3 }, // unrelated signal — must NOT leak onto SIG-1/SIG-2
      ],
      verdicts: [{ composite_verdict: 'confirmed', n: 5 }],
      reliability: [{ stratum_key: 'career_near', n: 12 }],
      multipliers: [
        { weight_id: 'W-1', domain: 'career', applied_multiplier: 1.2 },
        { weight_id: 'W-2', domain: 'health', applied_multiplier: 0.9 }, // wrong domain — must be filtered out
      ],
      qa: [{ check_id: 'Q-1', status: 'PASS' }],
    })

    const bundle = await computeSpineBundle({ chart_id: CHART_A, domain: 'career', top_k: 10 })

    expect(bundle.signal_count).toBe(2)
    const sig1 = bundle.signals.find(s => s.signal_id === 'SIG-1')!
    const sig2 = bundle.signals.find(s => s.signal_id === 'SIG-2')!

    expect(sig1.activation_windows).toHaveLength(1)
    expect(sig1.activation_windows[0]['signal_id']).toBe('SIG-1')
    expect(sig2.activation_windows).toHaveLength(0) // no activation row for SIG-2 — honest empty, not borrowed

    expect(sig1.phala_anchors).toHaveLength(1)
    expect(sig1.phala_anchors[0]['anchor_id']).toBe('A-1')
    expect(sig2.phala_anchors).toHaveLength(0) // A-2 belongs to SIG-3, never leaks onto SIG-2

    // Domain-filtered calibration: only the 'career' multiplier survives.
    expect(bundle.calibration.multipliers).toHaveLength(1)
    expect(bundle.calibration.multipliers[0]['weight_id']).toBe('W-1')
    expect(bundle.calibration.verdict_distribution).toEqual([{ composite_verdict: 'confirmed', n: 5 }])
    expect(bundle.calibration.qa_fail_count).toBe(0)

    expect(bundle.empty_reason).toBeNull()
    expect(bundle.provenance.tables).toContain('bodha_msr_signals')
    expect(bundle.provenance.composed_from_capabilities).toHaveLength(4)
  })

  it('reports an honest empty_reason when no signals exist for the domain, without querying activations/anchors', async () => {
    installFixtures({ signals: [] })

    const bundle = await computeSpineBundle({ chart_id: CHART_A, domain: 'spirituality', top_k: 10 })

    expect(bundle.signal_count).toBe(0)
    expect(bundle.signals).toEqual([])
    expect(bundle.empty_reason).toMatch(/No signals found/)

    // query_temporal_activation is skipped entirely when there are no signal_ids to filter by
    // (a real DB round-trip saved, not merely an empty result).
    const activationCalls = queryMock.mock.calls.filter(([sql]) => sqlContains(sql as string, 'FROM kala_activation') && !sqlContains(sql as string, 'predicates'))
    expect(activationCalls).toHaveLength(0)
  })

  it('is deterministic: two calls against identical fixture data produce byte-identical content', async () => {
    installFixtures({
      signals: [{ signal_id: 'SIG-9', signal_headline_text: 'x', computed_salience: 0.4, domains_affected_array: ['wealth'], valence: null }],
      activations: [{ id: 9, signal_id: 'SIG-9', activation_start: '2022-01-01', activation_end: '2022-06-01' }],
      anchors: [{ anchor_id: 'A-9', signal_id: 'SIG-9', domain: 'wealth', magnitude: 0.5 }],
      verdicts: [], reliability: [], multipliers: [], qa: [],
    })

    const first = await computeSpineBundle({ chart_id: CHART_A, domain: 'wealth', top_k: 10 })
    const second = await computeSpineBundle({ chart_id: CHART_A, domain: 'wealth', top_k: 10 })

    expect(JSON.stringify(second)).toBe(JSON.stringify(first))
  })

  it('rejects a missing domain before issuing any query', async () => {
    installFixtures({})
    await expect(computeSpineBundle({ chart_id: CHART_A, domain: '' as unknown as string })).rejects.toThrow(/domain is required/)
  })
})
