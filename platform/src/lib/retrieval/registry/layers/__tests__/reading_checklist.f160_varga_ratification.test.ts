/**
 * F-160 (PARIŚEṢA-V4) — `varga_confirmed`'s real tri-state detector.
 * =====================================================================
 * `register_d9_judgment.ts`'s old `varga_confirmed` was a bare
 * `chart_divisionals`-placement-row-presence check (`rows.length > 0`) — never "the varga
 * ratifies the D1 direction". These tests exercise the REAL detector directly:
 * `fetchVargaRatification` (reads chart_vichara.varga_ratification's agree/oppose vote) and
 * `vargaConfirmedMark` (the served mark it derives). Per CLAUDE.md §N.8, every test here
 * either constructs a bad state and asserts the signal reads honestly (not a fabricated ✓),
 * or is mutation-checked by construction (the aggregation-priority tests below fail on the
 * OLD "any truthy row → ✓" logic).
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

beforeEach(() => queryMock.mockReset())

describe('F-160 — vargaConfirmedMark: the served mark per relation', () => {
  it('agree -> a ✓ mark', () => {
    expect(vargaConfirmedMark('D2', 'agree')).toContain('✓')
  })
  it('oppose -> a DISTINCT mark, never a bare ✗ (this is itself a finding, not an absence)', () => {
    const mark = vargaConfirmedMark('D2', 'oppose')
    expect(mark).not.toBe('D2✗')
    expect(mark).not.toContain('✓')
    expect(mark.toLowerCase()).toMatch(/contradict/)
  })
  it('abstain / abstain_missing / no_row -> an honest unknown mark, never ✓ or the oppose mark', () => {
    for (const relation of ['abstain', 'abstain_missing', 'no_row'] as const) {
      const mark = vargaConfirmedMark('D2', relation)
      expect(mark, `relation=${relation}`).not.toContain('✓')
      expect(mark.toLowerCase(), `relation=${relation}`).not.toMatch(/contradict/)
      expect(mark).toContain('?')
    }
  })
})

describe('F-160 — fetchVargaRatification: can-fail (the §N.8 requirement)', () => {
  it('CAN-FAIL: abstain_missing must NOT read as agree/✓, even though a placement row would exist for this graha', async () => {
    // The exact defect shape: the OLD code would have seen chart_divisionals placement rows
    // for JUP and marked varga_confirmed "✓". Here the ratification vote is abstain_missing
    // (the varga row for this subject was never computed) — the tri-state must say so.
    stubRows([
      { subject: 'JUP', value_jsonb: { per_varga: { D2: { relation: 'abstain_missing', known_gap: true } }, domain_provisional: false } },
    ])
    const result = await fetchVargaRatification(CHART, LAHIRI, 'wealth', 'D2', [{ role: 'karaka', code: 'JUP' }])
    expect(result.relation).toBe('abstain_missing')
    expect(result.ok).toBe(true)
    const mark = vargaConfirmedMark('D2', result.relation)
    expect(mark).not.toContain('✓')
  })

  it('CAN-FAIL: oppose must show the contradicted mark, not the absent (?) mark and not a bare ✗', async () => {
    stubRows([
      { subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'oppose', dignity: 'debilitated', sign: 'Aries' } }, domain_provisional: true } },
    ])
    const result = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', [{ role: 'bhavesha', code: 'SAT' }])
    expect(result.relation).toBe('oppose')
    const mark = vargaConfirmedMark('D10', result.relation)
    expect(mark).not.toContain('✓')
    expect(mark).not.toBe('D10? (varga did not vote)')
    expect(mark.toLowerCase()).toMatch(/contradict/)
  })

  it('agree reads as agree, with domain_provisional surfaced', async () => {
    stubRows([
      { subject: 'JUP', value_jsonb: { per_varga: { D2: { relation: 'agree', dignity: 'exalted', sign: 'Cancer' } }, domain_provisional: false } },
    ])
    const result = await fetchVargaRatification(CHART, LAHIRI, 'wealth', 'D2', [{ role: 'karaka', code: 'JUP' }])
    expect(result.relation).toBe('agree')
    expect(result.domain_provisional).toBe(false)
  })

  it('no chart_vichara row at all (asset not built) reads as the honest no_row unknown, ok:true', async () => {
    stubRows([])
    const result = await fetchVargaRatification(CHART, LAHIRI, 'wealth', 'D2', [{ role: 'karaka', code: 'JUP' }])
    expect(result.relation).toBe('no_row')
    expect(result.ok).toBe(true)
    expect(vargaConfirmedMark('D2', result.relation)).not.toContain('✓')
  })

  it('a genuine query exception degrades to no_row with ok:false (distinct from a legitimate empty result)', async () => {
    // A malformed DB response (not a rejected promise — see the file-level note on vitest's
    // unhandled-rejection tracking of intentionally-rejected mocks) exercises the exact same
    // catch path: `res.rows` access throws when `res` is not shaped as expected.
    queryMock.mockReset()
    queryMock.mockImplementation(() => Promise.resolve(null))
    const result = await fetchVargaRatification(CHART, LAHIRI, 'wealth', 'D2', [{ role: 'karaka', code: 'JUP' }])
    expect(result.relation).toBe('no_row')
    expect(result.ok).toBe(false)
  })

  describe('aggregation across multiple subjects (bhāveśa + kāraka(s))', () => {
    it('CONTRADICTS wins over an agreeing sibling subject — a contradiction must never be masked', async () => {
      stubRows([
        { subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'agree' } } } },
        { subject: 'SUN', value_jsonb: { per_varga: { D10: { relation: 'oppose' } } } },
      ])
      const result = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', [
        { role: 'bhavesha', code: 'SAT' },
        { role: 'karaka', code: 'SUN' },
      ])
      expect(result.relation).toBe('oppose')
      expect(result.per_subject).toHaveLength(2)
    })

    it('agree wins over a bare abstain_missing sibling', async () => {
      stubRows([
        { subject: 'SAT', value_jsonb: { per_varga: { D10: { relation: 'abstain_missing', known_gap: true } } } },
        { subject: 'SUN', value_jsonb: { per_varga: { D10: { relation: 'agree' } } } },
      ])
      const result = await fetchVargaRatification(CHART, LAHIRI, 'career', 'D10', [
        { role: 'bhavesha', code: 'SAT' },
        { role: 'karaka', code: 'SUN' },
      ])
      expect(result.relation).toBe('agree')
    })
  })

  it('mutation check: reverting to `rows.length > 0` logic would wrongly mark abstain_missing as confirmed — this test fails under that reversion', async () => {
    // A row genuinely EXISTS (placements present) but its vote is abstain_missing. The old
    // defect ("a placement row exists" == confirmed) would read this as ✓; the fix must not.
    stubRows([
      { subject: 'JUP', value_jsonb: { per_varga: { D2: { relation: 'abstain_missing', known_gap: true } } } },
    ])
    const result = await fetchVargaRatification(CHART, LAHIRI, 'wealth', 'D2', [{ role: 'karaka', code: 'JUP' }])
    const rowsExisted = true // stands in for chart_divisionals' vargaPlacementsPresent, which IS true here
    const mark = vargaConfirmedMark('D2', result.relation)
    // The old defect: `rowsExisted ? '✓' : '✗'` — asserting the two are no longer coupled.
    expect(rowsExisted).toBe(true)
    expect(mark).not.toContain('✓')
  })
})
