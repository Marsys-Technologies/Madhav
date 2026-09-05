/**
 * build_tail_watch — unit tests.
 *
 * NIRMĀṆA L2-W3 (N-14 / N-15). These assert the properties the D-SALIENCE tail clause
 * actually depends on, not merely that the function returns rows.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
import { query as mockQuery } from '@/lib/db/client'
import {
  buildTailWatch,
  RARE_CLASS_MAX_MEMBERS,
  SALIENCE_FOLD_RANK,
  RARE_CLASS_LEADER_PCTL,
} from '../build_tail_watch'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'

/** The three queries fire via Promise.all in a fixed order: rare, anomalies, null-pctl. */
function stub(rare: unknown[], anomalies: unknown[], nullPctl = 0) {
  ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockReset()
  ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockImplementation((sql: string) => {
    if (sql.includes('bodha_anomalies')) return Promise.resolve({ rows: anomalies })
    if (sql.includes('salience_pctl_in_class IS NULL')) return Promise.resolve({ rows: [{ n: nullPctl }] })
    return Promise.resolve({ rows: rare })
  })
}

const rareRow = (over: Record<string, unknown> = {}) => ({
  signal_id: 'sig-1', signal_type_id: 'dosha_label:dosha_name', signal_type_class: 'dosha',
  signal_summary_text: 'a dosha', salience_pctl_in_class: 1.0, class_n: 5,
  top_k_salience_rank: 4200, ...over,
})
const anomalyRow = (over: Record<string, unknown> = {}) => ({
  signal_id: 'sig-2', signal_type_id: 'vargottama_per_varga:is_vargottama',
  signal_type_class: 'varga_pattern', sigma_from_baseline: 6.17, anomaly_value: 0.917,
  signal_summary_text: 'vargottama', ...over,
})

describe('components', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns both components, each labelled and counted', async () => {
    stub([rareRow()], [anomalyRow()])
    const r = await buildTailWatch(CHART, AYA)
    expect(r.tail_watch.map((x) => x.component)).toEqual([
      'rare_class_leader', 'low_salience_high_consequence',
    ])
    expect(r.tail_watch_components).toEqual({
      rare_class_leader: 1, low_salience_high_consequence: 1,
    })
    expect(r.tail_watch_empty_reason).toBeNull()
  })

  it('every row discloses why it was promoted', async () => {
    stub([rareRow()], [anomalyRow()])
    const r = await buildTailWatch(CHART, AYA)
    // D-SALIENCE: "promotion (tail side) is disclosed on-row". A tail row that cannot
    // say why it is in the tail is just a row.
    for (const row of r.tail_watch) {
      expect(row.promotion_reason).toBeTruthy()
      expect(row.promotion_reason).toMatch(/^promoted: /)
    }
    expect(r.tail_watch[0].promotion_reason).toContain('rare-class leader')
    expect(r.tail_watch[0].promotion_reason).toContain('5 signals chart-wide')
    expect(r.tail_watch[1].promotion_reason).toContain('6.17σ')
  })

  it('the anomaly reason states the inverse-salience relationship, not just a number', async () => {
    stub([], [anomalyRow()])
    const r = await buildTailWatch(CHART, AYA)
    // The whole point of this component is that consequence is weighted by the INVERSE
    // of salience — a reader who does not know that will misread a high score as "this
    // is prominent", which is the opposite of what it means.
    expect(r.tail_watch[0].promotion_reason).toContain('INVERSE')
  })
})

describe('honest gaps', () => {
  beforeEach(() => vi.clearAllMocks())

  it('an empty tail explains itself and never returns a bare []', async () => {
    stub([], [], 0)
    const r = await buildTailWatch(CHART, AYA)
    expect(r.tail_watch).toEqual([])
    expect(r.tail_watch_empty_reason).toBeTruthy()
    expect(r.tail_watch_empty_reason).toContain('no tail rows')
  })

  it('an empty tail discloses signals excluded for a NULL percentile', async () => {
    // The exact W1 defect: the six rarest classes carried NULL salience_pctl_in_class,
    // so the rare-class predicate silently excluded the population it exists to find.
    // If that ever recurs, the empty reason must say so rather than read as "no tail".
    stub([], [], 149)
    const r = await buildTailWatch(CHART, AYA)
    expect(r.tail_watch_empty_reason).toContain('149 signals')
    expect(r.tail_watch_empty_reason).toContain('salience_pctl_in_class')
  })

  it('a query failure is distinguishable from a genuinely empty tail', async () => {
    ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('boom'))
    const r = await buildTailWatch(CHART, AYA)
    expect(r.tail_watch).toEqual([])
    expect(r.tail_watch_empty_reason).toContain('could not be computed')
    // and it must NOT claim the tail was assessed and found empty
    expect(r.tail_watch_empty_reason).not.toContain('no tail rows')
  })
})

describe('predicate thresholds are passed to SQL, not hardcoded in prose', () => {
  beforeEach(() => vi.clearAllMocks())

  it('binds the doctrine constants as parameters', async () => {
    stub([], [])
    await buildTailWatch(CHART, AYA, { limitPerComponent: 7 })
    const rareCall = (mockQuery as unknown as ReturnType<typeof vi.fn>).mock.calls
      .find((c) => String(c[0]).includes('class_n'))
    expect(rareCall?.[1]).toEqual([
      CHART, AYA, RARE_CLASS_LEADER_PCTL, RARE_CLASS_MAX_MEMBERS, SALIENCE_FOLD_RANK, 7,
    ])
  })

  it('clamps the per-component limit into a sane range', async () => {
    stub([], [])
    await buildTailWatch(CHART, AYA, { limitPerComponent: 5000 })
    const rareCall = (mockQuery as unknown as ReturnType<typeof vi.fn>).mock.calls
      .find((c) => String(c[0]).includes('class_n'))
    expect(rareCall?.[1]?.[5]).toBe(50)
  })
})
