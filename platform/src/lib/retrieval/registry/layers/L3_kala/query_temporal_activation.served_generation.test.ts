/**
 * K9-WRITE-SCOPE F5 — query_temporal_activation serves ONLY the published generation of the
 * candidate-scoped kala_activation_predicates.
 *
 * Doctrine: CLAUDE.md §N.6 (a served surface never shows unpublished rows; an honest gap is
 * reported, not hidden), §N.7.3/§N.7.6 (no wrapper-local constant; an honest null beats an
 * invented judgment). Served generation = the kala_layer_head generation, else 'legacy' — the
 * same rule the build readers use (ka_sangam.py / ka_vighnakara.py head-or-legacy predicate
 * selection).
 *
 * The in-memory store below answers the predicate SELECT the way Postgres would: it applies
 * a `generation = $N` constraint only if the SQL actually carries one, so removing the filter
 * from the handler makes the candidate row come back.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryTemporalActivationCapability } from './query_temporal_activation'

type Handler = (args: Record<string, unknown>, ctx?: unknown) => Promise<{
  content: Record<string, unknown>
  is_error?: boolean
}>
const handler = queryTemporalActivationCapability.handler as Handler
const CHART_ID = '11111111-1111-4111-8111-111111111111'

const ACTIVATION = {
  id: 'act-1', signal_id: 'sig-1', activation_start: '2026-01-01', activation_end: '2026-01-31',
  activation_peak_date: '2026-01-10', dasha_activation_proximity_score: 0.9, orb_strength: 0.5,
  domains_affected_array: ['wealth'],
}
const pred = (id: string, generation: string) => ({
  id, generation, signal_id: 'sig-1', ayanamsha_id: 'lahiri_chitrapaksha', signature_class: 'PLANET',
  derivation_ledger_jsonb: {},
})

function installStore(opts: { head: string | null; predicates: ReturnType<typeof pred>[] }) {
  queryMock.mockImplementation((sql: unknown, params: unknown[] = []) => {
    const text = typeof sql === 'string' ? sql : ''
    if (text.includes('FROM kala_layer_head')) {
      return Promise.resolve({ rows: opts.head ? [{ generation: opts.head }] : [] })
    }
    if (text.includes('FROM kala_activation_predicates')) {
      const bound = /\bgeneration\s*=\s*\$(\d+)/.exec(text)
      const rows = bound ? opts.predicates.filter(p => p.generation === params[Number(bound[1]) - 1]) : opts.predicates
      return Promise.resolve({ rows })
    }
    if (text.includes('SELECT id, signal_id, ayanamsha_id, signature_class')) {
      return Promise.resolve({ rows: [{ ...ACTIVATION, total_matching: 1 }] })
    }
    // The handler also issues non-SQL probes (as in the closure suite); they carry no text.
    if (!text) return Promise.resolve({ rows: [] })
    throw new Error(`unexpected query: ${text}`)
  })
}

const call = () => handler({ chart_id: CHART_ID, date_from: '2026-01-01', date_to: '2026-12-31' })

describe('query_temporal_activation — predicates are read from the served generation only', () => {
  beforeEach(() => queryMock.mockReset())

  it('a candidate-generation predicate alongside a served one is NOT returned', async () => {
    installStore({ head: 'g-head', predicates: [pred('p-served', 'g-head'), pred('p-candidate', 'candidate:b1')] })
    const { content } = await call()
    expect((content['predicates'] as { id: string }[]).map(p => p.id)).toEqual(['p-served'])
    expect(content['predicate_generation']).toBe('g-head')
    expect(content['predicate_empty_reason']).toBeNull()
  })

  it("with no published head only 'legacy' rows are served, never a candidate", async () => {
    installStore({ head: null, predicates: [pred('p-legacy', 'legacy'), pred('p-candidate', 'candidate:b1')] })
    const { content } = await call()
    expect((content['predicates'] as { id: string }[]).map(p => p.id)).toEqual(['p-legacy'])
    expect(content['predicate_generation']).toBe('legacy')
  })

  it('no served generation (no head, no legacy rows) gives an honest empty_reason, not candidate rows', async () => {
    installStore({ head: null, predicates: [pred('p-candidate', 'candidate:b1')] })
    const { content } = await call()
    expect(content['predicates']).toEqual([])
    expect(content['predicate_count']).toBe(0)
    expect(String(content['predicate_empty_reason'])).toMatch(/No generation is published/)
    expect(content['judgment_flags']).toContain('predicates_not_in_served_generation')
  })
})
