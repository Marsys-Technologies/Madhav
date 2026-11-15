// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Direction, MultiSchoolResult, SchoolName } from '@/lib/schools/types'

const { db, chart, signals, run } = vi.hoisted(() => ({
  db: vi.fn(), chart: vi.fn(), signals: vi.fn(), run: vi.fn(),
}))
vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: db }))
vi.mock('@/lib/schools/school_runner', () => ({ runSchoolsForDomain: run }))
vi.mock('@/lib/schools/chart_data_adapter', async () => {
  const real = await vi.importActual<typeof import('@/lib/schools/chart_data_adapter')>('@/lib/schools/chart_data_adapter')
  return { ...real, buildChartData: chart, buildSchoolSignals: signals }
})
import { runAndPersistSchoolConsensus } from '@/lib/schools/consensusCommand'
import { DOMAIN_AUTHORITY_WEIGHTS } from '@/lib/schools/chart_data_adapter'

const CHART = 'fixture-chart-987654321'
const DOMAINS = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL'] as const
const SCHOOLS: SchoolName[] = ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini']
const input = { chartId: CHART, ayanamshaId: 'true_chitra' }
const chartData = { chartId: CHART, chartType: 'varsha_kundali' }
function result(directions: Array<Direction | null> = ['positive', 'negative']): MultiSchoolResult {
  return {
    chartId: CHART, runDate: 'ignored-runner-date', domain: 'CAREER',
    schoolResults: directions.map((direction, i) => ({
      school: SCHOOLS[i]!, domain: 'CAREER', direction,
      domainScore: i + 1, schoolVerdict: `verdict-${i}`, topSignals: [], signalCoverage: 'primary',
    })),
    convergence: { domain: 'CAREER', schoolsAgreeing: 1, schoolsTotal: 2,
      schoolsEvaluated: 7, schoolsAvailable: 2, schoolsUnavailable: [], convergenceLevel: 'LOW',
      meanDomainScore: 1.5, stdDomainScore: 0.5, direction: 'mixed', perSchoolScores: {},
    },
  }
}
const writes = (table: string) => db.mock.calls.filter(c => c[0].includes(`INSERT INTO ${table}`))

beforeEach(() => {
  vi.resetAllMocks()
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-11-15T00:00:00.001Z'))
  db.mockResolvedValue({ rows: [] })
  chart.mockResolvedValue(chartData)
  signals.mockImplementation(async (_id, school, domain) => [{ signalId: `${school}/${domain}`, score: 4, weight: 0.75 }])
  run.mockImplementation(async () => result())
})
afterEach(() => vi.useRealTimers())

describe('Mimamsa school consensus application command', () => {
  it('calls the existing ports with exact selected frame, school/domain binds and signal identity', async () => {
    expect(await runAndPersistSchoolConsensus(input)).toEqual({ domains: 5, analysisRows: 10, convergenceRows: 5, disagreementRows: 5 })
    expect(chart).toHaveBeenCalledExactlyOnceWith(CHART, 'true_chitra')
    expect(signals.mock.calls).toEqual(SCHOOLS.flatMap(school => DOMAINS.map(domain => [CHART, school, domain])))
    for (let i = 0; i < DOMAINS.length; i++) {
      expect(run.mock.calls[i]).toEqual([chartData, DOMAINS[i], {
        includeNarratives: true,
        liveSignals: Object.fromEntries(SCHOOLS.map(school => [school, [{ signalId: `${school}/${DOMAINS[i]}`, score: 4, weight: 0.75 }]])),
      }])
    }
    expect(db.mock.calls.slice(0, 3)).toEqual([
      ['DELETE FROM school_analysis_runs WHERE chart_id = $1', [CHART]],
      ['DELETE FROM convergence_scores WHERE chart_id = $1', [CHART]],
      ['DELETE FROM school_disagreements WHERE chart_id = $1', [CHART]],
    ])
    for (const [, binds] of writes('school_analysis_runs')) {
      const [id, date, school, type, domain, score, direction, top, verdict, pending, weighted, weight] = binds
      expect([id, date, type, top, pending]).toEqual([CHART, '2026-11-15', 'varsha_kundali', '[]', []])
      expect(weight).toBe(DOMAIN_AUTHORITY_WEIGHTS[domain as keyof typeof DOMAIN_AUTHORITY_WEIGHTS][school as SchoolName])
      expect(weighted).toBe(score * weight)
      expect(direction).toBe(school === 'parashari' ? 'positive' : 'negative')
      expect(verdict).toBe(school === 'parashari' ? 'verdict-0' : 'verdict-1')
    }
    // An absent weighted score stays undefined; the command must not invent zero/null.
    expect(writes('convergence_scores')[0]![1]).toEqual([CHART, 'CAREER', 1, 2, 1.5, 0.5, undefined, 'mixed', '{}', '{}', null])
  })

  it('preserves explicit narrative, score JSON and per-school weighted JSON at their original positions', async () => {
    const value = result()
    value.weightedMeanScore = null
    value.perSchoolWeighted = { jaimini: 0.123 }
    value.convergence.perSchoolScores = { jaimini: 2.75 }
    value.convergence.convergenceNarrative = 'fixture narrative — exact'
    run.mockResolvedValue(value)
    await runAndPersistSchoolConsensus(input)
    expect(writes('convergence_scores')[0]![1].slice(6)).toEqual([null, 'mixed', '{"jaimini":2.75}', '{"jaimini":0.123}', 'fixture narrative — exact'])
    expect(writes('school_disagreements')[0]![1][9]).toBe('fixture narrative — exact')
  })

  it('skips null school scores, retains zero scores and keeps unavailable schools out of adjudication', async () => {
    const value = result(['positive', 'negative', 'neutral'])
    value.schoolResults[0]!.domainScore = null
    value.schoolResults[1]!.domainScore = 0
    value.schoolResults[2]!.domainScore = null
    run.mockResolvedValue(value)
    expect(await runAndPersistSchoolConsensus(input)).toEqual({ domains: 5, analysisRows: 5, convergenceRows: 5, disagreementRows: 0 })
    expect(writes('school_analysis_runs')[0]![1][5]).toBe(0)
    expect(writes('school_analysis_runs')[0]![1][10]).toBe(0)
    expect(writes('school_disagreements')).toHaveLength(0)
  })

  it('retains fallback authority weight for an unrecognized engine school without normalizing it', async () => {
    const value = result(['positive'])
    value.schoolResults[0]!.school = 'future-school' as SchoolName
    run.mockResolvedValue(value)
    await runAndPersistSchoolConsensus(input)
    expect(writes('school_analysis_runs')[0]![1].slice(10)).toEqual([1 / 7, 1 / 7])
    expect(writes('school_analysis_runs')[0]![1][2]).toBe('future-school')
  })

  it.each([
    [['positive', 'positive', 'positive', 'negative'], 'temporal_scope', 'context_dependent', true],
    [['positive', 'positive', 'negative', 'negative'], 'temporal_scope', 'unresolved', true],
    [['positive', 'positive', 'positive', 'positive', 'positive', 'negative'], 'signal_gap', 'affirming_majority', false],
    [['positive', 'negative', 'negative', 'negative', 'negative', 'negative'], 'method_divergence', 'denying_majority', false],
    [['positive', 'neutral'], 'signal_gap', 'unresolved', false],
    [['positive', null], 'signal_gap', 'unresolved', false],
    [['positive', 'positive', 'positive', 'positive', 'negative', 'negative'], 'method_divergence', 'context_dependent', false],
  ] as Array<[Array<Direction | null>, string, string, boolean]>)('preserves inline disagreement %j -> %s/%s', async (directions, classification, verdict, timing) => {
    run.mockResolvedValue(result(directions))
    await runAndPersistSchoolConsensus(input)
    const positives = SCHOOLS.filter((_school, i) => directions[i] === 'positive')
    const negatives = SCHOOLS.filter((_school, i) => i < directions.length && directions[i] !== 'positive')
    const resolution = timing
      ? 'Majority schools confirm outcome direction; KP/Tājika timing divergence signals uncertain window boundaries — widen prediction window.'
      : `${positives.length}/7 schools positive; ${negatives.length}/7 negative. Context-dependent on dasha timing.`
    expect(writes('school_disagreements')[0]![1]).toEqual([
      CHART, `DIS.SCH.${CHART.slice(0, 8)}.CAREER.001`, 'CAREER', positives, negatives, [], classification, resolution, verdict, '',
    ])
  })

  it.each([[], ['positive'], ['neutral'], ['negative']])('keeps no-divergence cases %j free of disagreement rows', async (...directions) => {
    run.mockResolvedValue(result(directions as Array<Direction | null>))
    const counts = await runAndPersistSchoolConsensus(input)
    expect(counts.disagreementRows).toBe(0)
    expect(writes('school_disagreements')).toHaveLength(0)
  })

  it('awaits persistence before starting the next domain', async () => {
    let release: () => void = () => { throw new Error('not initialized') }
    const gate = new Promise<void>(resolve => { release = resolve })
    let notifyReached: () => void = () => { throw new Error('not initialized') }
    const reached = new Promise<void>(resolve => { notifyReached = resolve })
    db.mockImplementation(async sql => {
      if (sql.includes('INSERT INTO school_analysis_runs') && run.mock.calls.length === 1) {
        notifyReached()
        await gate
      }
      return { rows: [] }
    })
    const pending = runAndPersistSchoolConsensus(input)
    await reached
    expect(run).toHaveBeenCalledTimes(1)
    expect(writes('convergence_scores')).toHaveLength(0)
    release()
    await pending
    expect(run.mock.calls.map(c => c[1])).toEqual(DOMAINS)
  })

  it.each([1, 2, 3, 4, 6, 7, 8, 10, 11])('preserves nontransactional accepted prefix when DB operation %i fails', async failedAt => {
    const accepted: unknown[][] = []
    const failure = new Error(`query-${failedAt}`)
    db.mockImplementation(async (sql, binds) => {
      if (db.mock.calls.length === failedAt) throw failure
      accepted.push([sql, binds])
      return { rows: [] }
    })
    await expect(runAndPersistSchoolConsensus(input)).rejects.toBe(failure)
    expect(db).toHaveBeenCalledTimes(failedAt)
    expect(accepted).toHaveLength(failedAt - 1)
    expect(db.mock.calls.some(c => /BEGIN|COMMIT|ROLLBACK/.test(c[0]))).toBe(false)
    expect(run.mock.calls.map(c => c[1])).toEqual(failedAt <= 3 ? [] : failedAt <= 7 ? ['CAREER'] : ['CAREER', 'HEALTH'])
    expect(signals).toHaveBeenCalledTimes(35)
  })

  it('chart failure preserves all old state and avoids signal reads', async () => {
    const failure = new Error('missing chart')
    chart.mockRejectedValue(failure)
    await expect(runAndPersistSchoolConsensus(input)).rejects.toBe(failure)
    expect(signals).not.toHaveBeenCalled()
    expect(db).not.toHaveBeenCalled()
    expect(run).not.toHaveBeenCalled()
  })

  it('engine failure leaves prior-domain rows and completed deletes intact', async () => {
    const failure = new Error('engine health failed')
    run.mockImplementation(async (_chart, domain) => {
      if (domain === 'HEALTH') throw failure
      return result()
    })
    await expect(runAndPersistSchoolConsensus(input)).rejects.toBe(failure)
    expect(db.mock.calls).toHaveLength(7)
    expect(writes('school_analysis_runs')).toHaveLength(2)
    expect(writes('convergence_scores')).toHaveLength(1)
    expect(writes('school_disagreements')).toHaveLength(1)
    expect(run).toHaveBeenCalledTimes(2)
  })
})
