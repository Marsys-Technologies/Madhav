/**
 * query_signals (msr_sql) — the PROJECTION facet: WP-1.3(g) / LCA-7
 * =================================================================
 * msr_sql served a FIXED 17-of-82-column projection regardless of request. This
 * facet lets a caller pick which bodha_msr_signals columns are served, validated
 * against a static whitelist of real column names (NO arbitrary SQL — injection-safe),
 * and makes the FULL column set reachable via projection: ['*'].
 *
 * DB is mocked — no live connection required.
 */

import { describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

// A representative row carrying every column the internal pipeline + a few extras touch.
const FAKE_ROW: Record<string, unknown> = {
  signal_id: 'sig-1', signal_type_id: 't1', signal_type_class: 'yoga',
  signal_tradition: 'parashari', signal_summary_text: 's', signal_headline_text: 'h',
  computed_salience: 0.9, top_k_salience_rank: 1, domains_affected_array: ['career'],
  constituent_facts_array: ['F-1'], source_subsystem: 'parashara', valence: 'positive',
  verification_pass_status: 'pass', citation_human: 'BPHS', lel_origin: false,
  signature_tier: 'major', configuration_jsonb: {},
  // extra columns beyond the default 17:
  orb_tightness: 0.5, dignity_score: 0.7, shadbala_norm: 0.6, epistemic_tier: 'A',
}

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '5' }] }
    if (sql.includes('FROM bodha_msr_signals')) return { rows: [FAKE_ROW] }
    if (sql.includes('FROM chart_facts')) return { rows: [] }
    return { rows: [] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'
import { querySignalsCapability } from '../query_signals'

/** Extract the served signal object from a handler response. */
function servedSignal(result: Awaited<ReturnType<typeof querySignalsCapability.handler>>) {
  const content = result.content as Record<string, unknown>
  const signals = content.signals as Record<string, unknown>[]
  return signals[0]
}

describe('query_signals — projection facet (WP-1.3(g) / LCA-7)', () => {
  it('default (no projection): serves the legacy 17-column set, unchanged', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler({ chart_id: CHART_A }, {})
    expect(result.is_error).toBe(false)
    const sig = servedSignal(result)
    // legacy columns present
    expect(sig).toHaveProperty('signal_id')
    expect(sig).toHaveProperty('computed_salience')
    // columns OUTSIDE the default 17 are NOT served by default
    expect(sig).not.toHaveProperty('orb_tightness')
    expect(sig).not.toHaveProperty('dignity_score')
  })

  it('projection: [subset] serves ONLY the requested columns', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_id', 'valence', 'orb_tightness', 'dignity_score'] }, {},
    )
    expect(result.is_error).toBe(false)
    const sig = servedSignal(result)
    expect(Object.keys(sig).sort()).toEqual(['dignity_score', 'orb_tightness', 'signal_id', 'valence'])
  })

  it("projection: ['*'] makes the full column set reachable", async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler({ chart_id: CHART_A, projection: ['*'] }, {})
    expect(result.is_error).toBe(false)
    const sig = servedSignal(result)
    // columns beyond the default 17 are now reachable
    expect(sig).toHaveProperty('orb_tightness')
    expect(sig).toHaveProperty('epistemic_tier')
    expect(sig).toHaveProperty('shadbala_norm')
    const content = result.content as Record<string, unknown>
    const prov = content.provenance as Record<string, unknown>
    expect(prov).toHaveProperty('projection_note')
  })

  it('rejects an unknown/injected column WITHOUT touching the DB (injection-safe)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_id', 'valence; DROP TABLE bodha_msr_signals'] }, {},
    )
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>).error)).toMatch(/[Uu]nknown|not a projectable/)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it('rejects a plausible-but-nonexistent column name (whitelist, not just syntax)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_id', 'made_up_column'] }, {},
    )
    expect(result.is_error).toBe(true)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it('SELECT always fetches internal-required columns even when the caller projects a narrow set', async () => {
    // Composite ranking / demotion / freshness depend on computed_salience etc.;
    // narrowing the SERVED projection must not starve the internal pipeline.
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_headline_text'] }, {},
    )
    expect(result.is_error).toBe(false)
    const signalSelect = vi.mocked(mockQuery).mock.calls
      .map(c => String(c[0]))
      .find(s => s.includes('FROM bodha_msr_signals') && !s.includes('COUNT(*)'))!
    expect(signalSelect).toContain('computed_salience')
    expect(signalSelect).toContain('signal_headline_text')
    // served row is projected down to the requested single column
    expect(Object.keys(servedSignal(result))).toEqual(['signal_headline_text'])
  })
})
