/**
 * G2-B "Citations at first paint" (PPR-08, FD-2/FD-6) —
 * `pipeline/citation_resolver.ts`.
 *
 * Proves the resolver's epistemic scope claim directly: a ref that WAS part
 * of this turn's retrieved evidence resolves (grade `primary`); a ref that
 * was NOT — even if it is a perfectly real id elsewhere — resolves to null
 * (the honest "not grounded for this answer" outcome the rewriter turns into
 * `unverified` + a hallucination-counter increment).
 *
 * V3-E-032 (S4) widening: the module now recognizes THREE id-shape families
 * (`SIG.MSR.NNN`, standard UUIDs, 16-hex-char `chart_facts.fact_id`) across
 * FOUR source tables (`bodha_msr_signals`, `chart_facts`, `chart_divisionals`,
 * `chart_dashas`), all chart-scoped. The suite below proves:
 *   - the original SIG.MSR.NNN → bodha_msr_signals path is unchanged (no
 *     regression);
 *   - a genuinely-retrieved non-MSR id (a `chart_facts.fact_id`-shaped hex
 *     token) now resolves to a real label — this is the RED→GREEN
 *     regression proof against the pre-widening behavior, which could only
 *     ever match `SIG.MSR.NNN` and therefore returned null for this exact
 *     input;
 *   - an id NOT present in this turn's retrieved evidence still resolves to
 *     null regardless of shape (no over-crediting);
 *   - a DB fault on one source table's prefetch is distinguishable
 *     (`faulted: true`) from a clean "nothing to resolve" prefetch, without
 *     changing the resolve-to-null behavior for this turn's citations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))

import {
  extractCandidateSignalIds,
  fetchCandidateSignalLabels,
  buildTurnCitationResolver,
} from '@/lib/pariprashna/pipeline/citation_resolver'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

const CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

function toolBundle(toolName: string, contents: string[]): ToolBundle {
  return {
    tool_name: toolName,
    results: contents.map((content) => ({ content })),
  } as unknown as ToolBundle
}

/** Route the mocked `query()` by which table the SQL text targets. */
function bySql(handlers: Record<string, (params: unknown[]) => { rows: unknown[] }>) {
  queryMock.mockImplementation((sql: unknown, params: unknown[]) => {
    if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
    for (const [needle, handler] of Object.entries(handlers)) {
      if (sql.includes(needle)) return Promise.resolve(handler(params))
    }
    return Promise.resolve({ rows: [] })
  })
}

describe('extractCandidateSignalIds', () => {
  it('scans every tool result for SIG.MSR.NNN-shaped ids, deduplicated (no regression)', () => {
    const ids = extractCandidateSignalIds({
      validToolResults: [
        toolBundle('msr_sql', ['signal_id=SIG.MSR.001 fired', 'also SIG.MSR.002 and SIG.MSR.001 again']),
        toolBundle('cgm_graph_walk', ['no signal ids in this one']),
      ],
    })
    expect(ids.legacyMsrRefs.sort()).toEqual(['SIG.MSR.001', 'SIG.MSR.002'])
    expect(ids.uuidRefs).toEqual([])
    expect(ids.factIdRefs).toEqual([])
  })

  it('scans for standard UUID-shaped ids (bodha_msr_signals.signal_id / chart_divisionals.id / dasha_row_id), deduplicated', () => {
    const ids = extractCandidateSignalIds({
      validToolResults: [
        toolBundle('msr_sql', [
          JSON.stringify({ signal_id: '79725c1c-4386-4ebc-8df3-15419fb436f9', headline: 'x' }),
          JSON.stringify({ signal_id: '79725C1C-4386-4EBC-8DF3-15419FB436F9' }), // same id, different case
        ]),
        toolBundle('get_dashas', [JSON.stringify({ dasha_row_id: 'd001ba69-2899-4472-af28-e9c073f3a413' })]),
      ],
    })
    expect(ids.uuidRefs.sort()).toEqual(
      ['79725c1c-4386-4ebc-8df3-15419fb436f9', 'd001ba69-2899-4472-af28-e9c073f3a413'].sort(),
    )
  })

  it('scans for 16-lowercase-hex-char chart_facts.fact_id tokens, deduplicated', () => {
    const ids = extractCandidateSignalIds({
      validToolResults: [
        toolBundle('chart_facts_query', [
          JSON.stringify({ fact_id: '78720121094c0de8', fact_value_text: 'Cancer' }),
          JSON.stringify({ fact_id: '78720121094c0de8' }), // dup
        ]),
      ],
    })
    expect(ids.factIdRefs).toEqual(['78720121094c0de8'])
  })

  it('does not cross-contaminate a 64-char sha256 result_hash into the 16-hex fact_id family', () => {
    const ids = extractCandidateSignalIds({
      validToolResults: [
        toolBundle('chart_facts_query', [
          JSON.stringify({ result_hash: 'sha256:' + 'a'.repeat(64) }),
        ]),
      ],
    })
    expect(ids.factIdRefs).toEqual([])
  })

  it('returns empty arrays for every family when nothing matches', () => {
    expect(extractCandidateSignalIds({ validToolResults: [] })).toEqual({
      legacyMsrRefs: [],
      uuidRefs: [],
      factIdRefs: [],
    })
  })
})

describe('fetchCandidateSignalLabels', () => {
  beforeEach(() => queryMock.mockReset())

  it('(no regression) resolves grade primary for a SIG.MSR.NNN id from bodha_msr_signals', async () => {
    bySql({
      bodha_msr_signals: () => ({
        rows: [{ signal_id: 'SIG.MSR.413', name: 'Mercury convergence', description: 'a deep dive' }],
      }),
    })
    const { labels, faulted } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: ['SIG.MSR.413'],
      uuidRefs: [],
      factIdRefs: [],
    })
    expect(faulted).toBe(false)
    expect(labels.get('SIG.MSR.413')).toEqual({
      reader_label: 'Mercury convergence — a deep dive',
      grade: 'primary',
      source_table: 'bodha_msr_signals',
      source_column: 'signal_id',
    })
    // chart-scoped: chart_id is the first bound param.
    const call = queryMock.mock.calls.find(([sql]) => String(sql).includes('bodha_msr_signals'))
    expect(call?.[1]).toEqual([CHART_ID, ['SIG.MSR.413']])
  })

  it('RED→GREEN: a genuinely-retrieved chart_facts.fact_id (non-MSR shape) now resolves to a real label', async () => {
    bySql({
      chart_facts: () => ({
        rows: [{ fact_id: '78720121094c0de8', citation_human: 'upagraha_position.DHUMA.sign = Cancer (true_chitra).' }],
      }),
    })
    const { labels, faulted } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: [],
      uuidRefs: [],
      factIdRefs: ['78720121094c0de8'],
    })
    expect(faulted).toBe(false)
    // Pre-widening, this id shape was never even extracted (SIG.MSR.NNN-only
    // regex) and fetchCandidateSignalLabels never queried chart_facts at
    // all — this exact input would have been an unconditional null/unverified.
    const resolved = buildTurnCitationResolver(labels).resolve('78720121094c0de8')
    expect(resolved).not.toBeNull()
    expect(resolved?.grade).toBe('primary')
    expect(resolved?.reader_label).toBe('upagraha_position.DHUMA.sign = Cancer (true_chitra).')
  })

  it('RED→GREEN: a genuinely-retrieved UUID signal_id (the live-schema shape) now resolves, where SIG.MSR.NNN never would', async () => {
    // Live-schema finding (S4): bodha_msr_signals.signal_id is a genuine UUID
    // column in production — "SIG.MSR.NNN" never occurs there. Pre-widening,
    // a real UUID signal_id in retrieved evidence could never match the old
    // /SIG\.MSR\.\d{3}/ regex and so could never be extracted as a candidate.
    bySql({
      bodha_msr_signals: () => ({
        rows: [{ signal_id: '79725c1c-4386-4ebc-8df3-15419fb436f9', name: 'argala natal matrix', description: null }],
      }),
    })
    const { labels } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: [],
      uuidRefs: ['79725c1c-4386-4ebc-8df3-15419fb436f9'],
      factIdRefs: [],
    })
    const resolved = buildTurnCitationResolver(labels).resolve('79725c1c-4386-4ebc-8df3-15419fb436f9')
    expect(resolved).not.toBeNull()
    expect(resolved?.grade).toBe('primary')
  })

  it('negative control: an id NOT present in this turn evidence resolves to null (no over-crediting)', async () => {
    // The prefetch is only ever keyed on candidates THIS turn actually
    // extracted — a real fact_id that exists in chart_facts but was never
    // passed as a candidate (i.e. never part of this turn's evidence) must
    // never be looked up, let alone credited.
    bySql({
      // Mirrors the real `WHERE fact_id = ANY($2::text[])` filter — a fixture
      // row for a DIFFERENT fact_id than what was requested must not surface.
      chart_facts: (params) => {
        const requested = params[1] as string[]
        const row = { fact_id: '78720121094c0de8', citation_human: 'real row, real chart, wrong turn' }
        return { rows: requested.includes(row.fact_id) ? [row] : [] }
      },
    })
    const { labels } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: [],
      uuidRefs: [],
      factIdRefs: ['00000000deadbeef'], // NOT the id the mocked DB has
    })
    expect(labels.size).toBe(0)
    const resolved = buildTurnCitationResolver(labels).resolve('78720121094c0de8')
    expect(resolved).toBeNull()
  })

  it('a DB fault on one source table is distinguishable (faulted: true) without over-crediting or under-crediting the others', async () => {
    queryMock.mockImplementation((sql: unknown) => {
      if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
      if (sql.includes('chart_facts')) return Promise.reject(new Error('db unavailable'))
      if (sql.includes('bodha_msr_signals')) {
        return Promise.resolve({ rows: [{ signal_id: 'SIG.MSR.413', name: 'still resolves', description: null }] })
      }
      return Promise.resolve({ rows: [] })
    })
    const { labels, faulted } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: ['SIG.MSR.413'],
      uuidRefs: [],
      factIdRefs: ['78720121094c0de8'],
    })
    expect(faulted).toBe(true)
    // The faulted source contributes nothing (fail-closed — unchanged this-turn behavior)...
    expect(labels.has('78720121094c0de8')).toBe(false)
    // ...but a source that succeeded is unaffected by the other's fault.
    expect(labels.get('SIG.MSR.413')?.reader_label).toBe('still resolves')
  })

  it('a clean prefetch with real candidates but zero matching rows is NOT faulted (honest "nothing to resolve", not a degraded state)', async () => {
    bySql({}) // every query resolves { rows: [] }
    const { labels, faulted } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: ['SIG.MSR.999'],
      uuidRefs: [],
      factIdRefs: [],
    })
    expect(faulted).toBe(false)
    expect(labels.size).toBe(0)
  })

  it('short-circuits to an empty, non-faulted result with zero candidate ids (no query call)', async () => {
    const { labels, faulted } = await fetchCandidateSignalLabels(CHART_ID, {
      legacyMsrRefs: [],
      uuidRefs: [],
      factIdRefs: [],
    })
    expect(labels.size).toBe(0)
    expect(faulted).toBe(false)
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('buildTurnCitationResolver — epistemic scope', () => {
  const label = (reader_label: string) =>
    ({ reader_label, grade: 'primary' as const, source_table: 'bodha_msr_signals', source_column: 'signal_id' })

  it('a ref that WAS part of this turn evidence resolves, grade primary', () => {
    const labels = new Map([['SIG.MSR.413', label('Mercury convergence')]])
    const resolver = buildTurnCitationResolver(labels)
    const resolved = resolver.resolve('SIG.MSR.413')
    expect(resolved).not.toBeNull()
    expect(resolved?.grade).toBe('primary')
    expect(resolved?.reader_label).toBe('Mercury convergence')
    expect(resolved?.audit_detail).toContain('SIG.MSR.413')
    expect(resolved?.audit_detail).toContain('bodha_msr_signals')
  })

  it('a ref that was NOT part of this turn evidence resolves to null (never borrows a grade)', () => {
    const labels = new Map([['SIG.MSR.413', label('Mercury convergence')]])
    const resolver = buildTurnCitationResolver(labels)
    // A real-looking id, but absent from THIS turn's prefetched map.
    expect(resolver.resolve('SIG.MSR.999')).toBeNull()
  })

  it('readerLabel mirrors the same map for the register-leak lint REWRITE path', () => {
    const labels = new Map([['SIG.MSR.413', label('Mercury convergence')]])
    const resolver = buildTurnCitationResolver(labels)
    expect(resolver.readerLabel('SIG.MSR.413')).toBe('Mercury convergence')
    expect(resolver.readerLabel('SIG.MSR.999')).toBeNull()
  })
})
