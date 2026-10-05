/**
 * `fetchVargaRatification` — the served per-subject label 'not_voter' (D10 abstain diagnosis, fix B).
 * =====================================================================================
 * Background (POST/D10_ABSTAIN REPORT): in judgment_query(career) the receipt asks about SUN, MER and SAT, but
 * ga_vichara writes the career ratification vote only for the 10th lord + its single karaka (= SAT). SUN and MER therefore
 * read 'no_row', which a reader takes as "data missing / asset not built". They are in fact not voters for this domain.
 *
 * Contract pinned here (CLAUDE.md §N.6 / §N.7 item 6: an honest label, never a flattened or invented one):
 *  - STRICTER LABELLING ONLY, on `per_subject[].relation`: a requested subject with NO row, while the domain DOES carry a
 *    ratification row for another requested subject (so the vote was written, just not for this one), reads 'not_voter'.
 *  - Nothing else moves: the aggregated `relation`, `ok`, `domain_provisional` and the served mark are byte-identical to
 *    what the same rows produced when those subjects read 'no_row' (a 'not_voter' ranks with 'no_row' in the aggregation).
 *  - 'not_voter' is claimed only with positive evidence: no rows at all (asset not built / out-of-scope domain), a failed
 *    query, or a subject that HAS a row but no entry for this varga all stay 'no_row'.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { fetchVargaRatification, vargaConfirmedMark } from '../reading_checklist'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'

function stubRows(rows: Array<{ subject: string; value_jsonb: Record<string, unknown> }>) {
  queryMock.mockReset()
  queryMock.mockImplementation((sql: string) => {
    if (/chart_vichara/i.test(sql)) return Promise.resolve({ rows })
    return Promise.resolve({ rows: [] })
  })
}

// The shape judgment_query(career) really sends: bhavesha SAT, karakas SUN, MER, SAT (grahasToConfirm).
const CAREER_SUBJECTS = [
  { role: 'bhavesha', code: 'SAT' },
  { role: 'karaka', code: 'SUN' },
  { role: 'karaka', code: 'MER' },
  { role: 'karaka', code: 'SAT' },
]
const rel = (r: Awaited<ReturnType<typeof fetchVargaRatification>>, subject: string) =>
  r.per_subject.filter(s => s.subject === subject).map(s => s.relation)

beforeEach(() => queryMock.mockReset())

describe("fetchVargaRatification — 'not_voter' labelling", () => {
  it('the production D10 shape: only SAT voted (abstain), so SUN and MER are labelled not_voter, aggregate unchanged', async () => {
    stubRows([{ subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'abstain' } }, domain_provisional: false } }])
    const r = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', CAREER_SUBJECTS)
    expect(rel(r, 'SUN')).toEqual(['not_voter'])
    expect(rel(r, 'MER')).toEqual(['not_voter'])
    expect(rel(r, 'SAT')).toEqual(['abstain', 'abstain'])
    expect(r.relation).toBe('abstain')
    expect(r.ok).toBe(true)
    expect(r.domain_provisional).toBe(false)
    expect(vargaConfirmedMark('D10', r.relation)).toBe('D10? (varga did not vote)')
  })

  it('VERDICT-INVARIANT: the aggregate and the mark equal what no_row siblings produce (agree stays agree, oppose stays oppose)', async () => {
    for (const vote of ['agree', 'oppose', 'abstain', 'abstain_missing'] as const) {
      stubRows([{ subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: vote } } } }])
      const r = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', CAREER_SUBJECTS)
      expect(r.relation, `vote=${vote}`).toBe(vote)
      expect(rel(r, 'SUN'), `vote=${vote}`).toEqual(['not_voter'])
    }
    stubRows([{ subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'agree' } } } }])
    const agree = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', CAREER_SUBJECTS)
    expect(vargaConfirmedMark('D10', agree.relation)).toContain('✓')
  })

  it('a not_voter never outranks a real vote in the aggregate, and a lone not_voter set aggregates to no_row as before', async () => {
    // SUN has no row, SAT agrees: aggregate is agree, not influenced by the label.
    stubRows([{ subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'agree' } } } }])
    expect((await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', [
      { role: 'karaka', code: 'SUN' }, { role: 'bhavesha', code: 'SAT' }])).relation).toBe('agree')
    // The only requested subject without a row while another requested subject's row lacks this varga entirely: no_row.
    stubRows([{ subject: 'SAT', value_jsonb: { per_varga: {} } }])
    const r = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', [
      { role: 'karaka', code: 'SUN' }, { role: 'bhavesha', code: 'SAT' }])
    expect(r.relation).toBe('no_row')
    expect(rel(r, 'SUN')).toEqual(['not_voter'])
    expect(rel(r, 'SAT')).toEqual(['no_row'])        // HAS a row, just none for D10: genuinely no_row, not a non-voter
  })

  it('no rows at all (asset not built / out-of-scope domain) stays no_row: no positive evidence of a non-voter', async () => {
    stubRows([])
    const r = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', CAREER_SUBJECTS)
    expect(r.per_subject.every(s => s.relation === 'no_row')).toBe(true)
    expect(r.relation).toBe('no_row')
    expect(r.ok).toBe(true)
  })

  it('a failed query stays no_row with ok:false (never labelled not_voter)', async () => {
    queryMock.mockReset()
    queryMock.mockImplementation(() => Promise.resolve(null))
    const r = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', CAREER_SUBJECTS)
    expect(r.ok).toBe(false)
    expect(r.per_subject.every(s => s.relation === 'no_row')).toBe(true)
  })

  it('a subject whose row exists but carries no entry for this varga stays no_row', async () => {
    stubRows([
      { subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'agree' } } } },
      { subject: 'SUN', value_jsonb: { per_varga: { D9: { relation: 'agree' } } } },
    ])
    const r = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', CAREER_SUBJECTS)
    expect(rel(r, 'SUN')).toEqual(['no_row'])
    expect(rel(r, 'MER')).toEqual(['not_voter'])
  })
})
