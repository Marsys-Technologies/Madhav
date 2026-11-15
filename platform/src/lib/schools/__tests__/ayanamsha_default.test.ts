// @vitest-environment node
/**
 * Lahiri-primary PR-5: the school-consensus build route and chart_data_adapter default to the STORED
 * id `lahiri_chitrapaksha` (they used to default to the short 'lahiri', which matches zero chart_facts
 * rows), normalise aliases through the PR-1 helper, and reject unknown ids / "all" with HTTP 400.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { queryMock, buildChartDataMock, buildSignalsMock, runMock, userMock } = vi.hoisted(() => ({
  queryMock: vi.fn(),
  buildChartDataMock: vi.fn(),
  buildSignalsMock: vi.fn(),
  runMock: vi.fn(),
  userMock: vi.fn(),
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: userMock }))
vi.mock('@/lib/schools/school_runner', () => ({ runSchoolsForDomain: runMock }))
vi.mock('@/lib/schools/chart_data_adapter', async () => {
  const real = await vi.importActual<typeof import('@/lib/schools/chart_data_adapter')>('@/lib/schools/chart_data_adapter')
  return { ...real, buildChartData: buildChartDataMock, buildSchoolSignals: buildSignalsMock }
})

import { POST } from '@/app/api/build/school-consensus/route'
import { AYANAMSHA_SERVE_ORDER } from '@/lib/retrieval/registry/constants'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function req(body: unknown) {
  return new Request('http://localhost/api/build/school-consensus', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }) as never
}

beforeEach(() => {
  queryMock.mockReset()
  buildChartDataMock.mockReset()
  buildSignalsMock.mockReset()
  runMock.mockReset()
  userMock.mockResolvedValue({ uid: 'admin' })
  queryMock.mockImplementation(async (sql: string) =>
    /FROM profiles/.test(sql) ? { rows: [{ role: 'super_admin' }] } : { rows: [] })
  // stop the route right after the ayanamsha is consumed
  buildChartDataMock.mockRejectedValue(new Error('stop-after-buildChartData'))
})

describe('POST /api/build/school-consensus: ayanamsha default and boundary', () => {
  it('omitted ayanamsha_id -> buildChartData gets the STORED id lahiri_chitrapaksha', async () => {
    await expect(POST(req({ chart_id: CHART }))).rejects.toThrow('stop-after-buildChartData')
    expect(buildChartDataMock).toHaveBeenCalledWith(CHART, 'lahiri_chitrapaksha')
    expect(AYANAMSHA_SERVE_ORDER).toContain(buildChartDataMock.mock.calls[0]![1])
  })

  it.each([['lahiri', 'lahiri_chitrapaksha'], ['LAHIRI', 'lahiri_chitrapaksha'], ['kp', 'krishnamurti'], ['true_chitra', 'true_chitra']])(
    '%j is normalised to the stored id %j', async (input, stored) => {
      await expect(POST(req({ chart_id: CHART, ayanamsha_id: input }))).rejects.toThrow('stop-after')
      expect(buildChartDataMock).toHaveBeenCalledWith(CHART, stored)
    })

  it('unknown ayanamsha_id -> 400 listing the stored ids; nothing is built', async () => {
    const res = await POST(req({ chart_id: CHART, ayanamsha_id: 'yukteshwar' }))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.code).toBe('invalid_ayanamsha_id')
    for (const id of AYANAMSHA_SERVE_ORDER) expect(body.error).toContain(id)
    expect(buildChartDataMock).not.toHaveBeenCalled()
    expect(queryMock.mock.calls.every((c) => !/DELETE/.test(String(c[0])))).toBe(true)
  })

  it('"all" -> 400 (the engines read one ayanamsha)', async () => {
    const res = await POST(req({ chart_id: CHART, ayanamsha_id: 'all' }))
    expect(res.status).toBe(400)
    expect(buildChartDataMock).not.toHaveBeenCalled()
  })

  it('non-super-admin is still 403 before any ayanamsha handling', async () => {
    queryMock.mockImplementation(async () => ({ rows: [{ role: 'guest' }] }))
    expect((await POST(req({ chart_id: CHART }))).status).toBe(403)
  })
})

describe('chart_data_adapter.buildChartData default', () => {
  it('queries chart_facts with the stored id by default; aliases normalise; unknown throws; "all" throws', async () => {
    const real = await vi.importActual<typeof import('@/lib/schools/chart_data_adapter')>('@/lib/schools/chart_data_adapter')
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
    await real.buildChartData(CHART).catch(() => undefined)
    const firstParams = queryMock.mock.calls[0]![1] as unknown[]
    expect(firstParams).toEqual([CHART, 'lahiri_chitrapaksha'])
    // every read is the Lahiri primary EXCEPT the KP sub-lord read, which is the KP frame (SS N-342 / N-359)
    for (const c of queryMock.mock.calls.filter((q) => !/kp_sub_lord/.test(String(q[0])))) expect((c[1] as unknown[])[1]).toBe('lahiri_chitrapaksha')

    queryMock.mockClear()
    await real.buildChartData(CHART, 'kp').catch(() => undefined)
    expect((queryMock.mock.calls[0]![1] as unknown[])[1]).toBe('krishnamurti')

    queryMock.mockClear()
    await expect(real.buildChartData(CHART, 'nonsense')).rejects.toThrow(/Unknown ayanamsha_id/)
    await expect(real.buildChartData(CHART, 'all')).rejects.toThrow(/one ayanamsha/)
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('chart_data_adapter.buildChartData: the KP sub-lord read is pinned to the KP frame (SS N-359)', () => {
  const KP_FRAME_LABEL = 'KP frame (Krishnamurti ayanamsha)'
  const kpCalls = () => queryMock.mock.calls.filter((c) => /kp_sub_lord/.test(String(c[0])))

  it.each([
    ['no id', undefined],
    ['the Lahiri primary id', 'lahiri_chitrapaksha'],
    ['the alias lahiri', 'lahiri'],
    ['the alias LAHIRI', 'LAHIRI'],
    ['raman', 'raman'],
    ['true_chitra', 'true_chitra'],
    ['explicit krishnamurti', 'krishnamurti'],
  ] as Array<[string, string | undefined]>)('%s: the cusp/graha KP read binds krishnamurti, never the requested frame', async (_label, id) => {
    const real = await vi.importActual<typeof import('@/lib/schools/chart_data_adapter')>('@/lib/schools/chart_data_adapter')
    queryMock.mockReset()
    queryMock.mockImplementation(async (sql: string) =>
      /kp_sub_lord/.test(sql) ? { rows: [{ bhava_or_planet: 'Ascendant', sub_lord: 'Saturn' }] } : { rows: [] })
    const chart = await (id === undefined ? real.buildChartData(CHART) : real.buildChartData(CHART, id))
    expect(kpCalls()).toHaveLength(1)
    expect(kpCalls()[0]![1]).toEqual([CHART, 'krishnamurti'])
    expect(chart.kpSubLords).toEqual({ ascendant: 'saturn' })
    expect(chart.kpSubLordsFrame).toBe(KP_FRAME_LABEL)
    // the rest of the ChartData is still read at the requested/primary ayanamsha
    const others = queryMock.mock.calls.filter((c) => !/kp_sub_lord/.test(String(c[0])))
    const want = id === undefined || /^lahiri/i.test(id) ? 'lahiri_chitrapaksha' : id.toLowerCase()
    for (const c of others) expect((c[1] as unknown[])[1]).toBe(want)
  })

  it('"all" and a nonsense id are refused before any query (no KP read is made at all)', async () => {
    const real = await vi.importActual<typeof import('@/lib/schools/chart_data_adapter')>('@/lib/schools/chart_data_adapter')
    queryMock.mockReset()
    await expect(real.buildChartData(CHART, 'all')).rejects.toThrow()
    await expect(real.buildChartData(CHART, 'not_an_ayanamsha_xyz')).rejects.toThrow()
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('no KP rows: no kpSubLords and no frame label', async () => {
    const real = await vi.importActual<typeof import('@/lib/schools/chart_data_adapter')>('@/lib/schools/chart_data_adapter')
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
    const chart = await real.buildChartData(CHART)
    expect(chart.kpSubLords).toBeUndefined()
    expect(chart.kpSubLordsFrame).toBeUndefined()
  })
})


// Command characterization: runs the real route (and, after extraction, the real coordinator).
const DOMAINS = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
const SCHOOLS = ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini']
const events: string[] = []
function resultFor(domain: string) {
  return {
    schoolResults: SCHOOLS.map((school, i) => ({
      school, domain, domainScore: i === 6 ? null : i + 0.5,
      direction: i < 4 ? 'positive' : 'neutral', schoolVerdict: `verdict-${school}`,
      ...(i === 0 ? { topSignals: [{ signalId: 'fixture-signal' }], pendingFlags: ['fixture-pending'] } : {}),
    })),
    convergence: { schoolsAgreeing: 4, schoolsTotal: 6, meanDomainScore: 3,
      stdDomainScore: 0.75, direction: 'mixed', perSchoolScores: { parashari: 0.5 } },
    weightedMeanScore: 2.75,
  }
}
function commandSetup() {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-11-15T23:59:59.999Z'))
  events.length = 0
  buildChartDataMock.mockImplementation(async (...args) => {
    events.push(`chart:${args.join(':')}`)
    return { chartId: CHART, chartType: 'natal' }
  })
  buildSignalsMock.mockImplementation(async (_chart, school, domain) => {
    events.push(`signal:${school}:${domain}`)
    return [{ signalId: `${school}:${domain}`, score: 2, weight: 1 }]
  })
  queryMock.mockImplementation(async (sql: string) => {
    events.push(sql.trim().split(/\s+/).slice(0, 3).join(' '))
    return /FROM profiles/.test(sql) ? { rows: [{ role: 'super_admin' }] } : { rows: [] }
  })
  runMock.mockImplementation(async (_chart, domain) => {
    events.push(`run:${domain}`)
    return resultFor(domain)
  })
}
afterEach(() => vi.useRealTimers())

describe('POST school consensus command characterization', () => {
  it('prefetches every school/domain before three deletes, then persists domains sequentially with exact wire counts', async () => {
    commandSetup()
    const response = await POST(req({ chart_id: CHART, ayanamsha_id: 'KP' }))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ ok: true, chart_id: CHART, domains: 5, analysis_rows: 30, convergence_rows: 5, disagreement_rows: 5 })
    expect(events.slice(0, 37)).toEqual([
      'SELECT role FROM', `chart:${CHART}:krishnamurti`,
      ...SCHOOLS.flatMap(school => DOMAINS.map(domain => `signal:${school}:${domain}`)),
    ])
    expect(events.slice(37, 40)).toEqual(['DELETE FROM school_analysis_runs', 'DELETE FROM convergence_scores', 'DELETE FROM school_disagreements'])
    expect(events.slice(40)).toEqual(DOMAINS.flatMap(domain => [
      `run:${domain}`, ...Array(6).fill('INSERT INTO school_analysis_runs'),
      'INSERT INTO convergence_scores', 'INSERT INTO school_disagreements',
    ]))
    for (const [chart, domain, options] of runMock.mock.calls) {
      expect(chart).toEqual({ chartId: CHART, chartType: 'natal' })
      expect(options).toEqual({ includeNarratives: true, liveSignals: Object.fromEntries(SCHOOLS.map(school => [school, [{ signalId: `${school}:${domain}`, score: 2, weight: 1 }]])) })
    }
    const writes = queryMock.mock.calls.filter(c => /INSERT INTO school_analysis_runs/.test(c[0]))
    expect(writes[0]![1]).toEqual([CHART, '2026-11-15', 'parashari', 'natal', 'CAREER', 0.5, 'positive', '[{"signalId":"fixture-signal"}]', 'verdict-parashari', ['fixture-pending'], 0.5 * 0.20, 0.20])
    expect(writes[1]![1][7]).toBe('[]')
    expect(writes[1]![1][9]).toEqual([])
    expect(writes.every(c => c[1][2] !== 'yogini')).toBe(true)
    expect(queryMock.mock.calls.filter(c => /INSERT INTO convergence_scores/.test(c[0]))[0]![1]).toEqual([CHART, 'CAREER', 4, 6, 3, 0.75, 2.75, 'mixed', '{"parashari":0.5}', '{}', null])
    expect(queryMock.mock.calls.filter(c => /INSERT INTO school_disagreements/.test(c[0]))[0]![1]).toEqual([CHART, `DIS.SCH.${CHART.slice(0, 8)}.CAREER.001`, 'CAREER', ['parashari','jaimini','tajika','kp'], ['nadi','bnn'], [], 'method_divergence', '4/7 schools positive; 2/7 negative. Context-dependent on dasha timing.', 'context_dependent', ''])
    expect(queryMock.mock.calls.slice(1, 4).map(c => c[1])).toEqual([[CHART], [CHART], [CHART]])
  })
  it('fails a late signal read before deleting any old state or running engines', async () => {
    commandSetup()
    const failure = new Error('signal-unavailable')
    buildSignalsMock.mockImplementation(async (_chart, school, domain) => {
      if (school === 'yogini' && domain === 'PSYCHOLOGICAL') throw failure
      return []
    })
    await expect(POST(req({ chart_id: CHART }))).rejects.toBe(failure)
    expect(buildSignalsMock).toHaveBeenCalledTimes(35)
    expect(queryMock.mock.calls).toHaveLength(1)
    expect(runMock).not.toHaveBeenCalled()
  })
  it('propagates insert failure with prior writes intact and no later domain execution', async () => {
    commandSetup()
    const accepted: unknown[][] = []
    const failure = new Error('insert-failed')
    queryMock.mockImplementation(async (sql, binds) => {
      if (/INSERT INTO convergence_scores/.test(sql) && binds[1] === 'HEALTH') throw failure
      accepted.push([sql, binds])
      return /FROM profiles/.test(sql) ? { rows: [{ role: 'super_admin' }] } : { rows: [] }
    })
    await expect(POST(req({ chart_id: CHART }))).rejects.toBe(failure)
    expect(runMock.mock.calls.map(c => c[1])).toEqual(['CAREER', 'HEALTH'])
    expect(accepted.filter(c => /INSERT INTO school_analysis_runs/.test(String(c[0])))).toHaveLength(12)
    expect(accepted.filter(c => /INSERT INTO convergence_scores/.test(String(c[0])))).toHaveLength(1)
    expect(accepted.filter(c => /INSERT INTO school_disagreements/.test(String(c[0])))).toHaveLength(1)
    expect(accepted.some(c => /BEGIN|ROLLBACK|COMMIT/.test(String(c[0])))).toBe(false)
  })
  it('unauthenticated input is forbidden before parsing body or querying role', async () => {
    commandSetup()
    userMock.mockResolvedValue(null)
    const json = vi.fn().mockRejectedValue(new Error('must-not-parse'))
    const response = await POST({ json } as never)
    expect(response.status).toBe(403)
    expect(await response.json()).toEqual({ error: 'Forbidden' })
    expect(json).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
    expect(buildChartDataMock).not.toHaveBeenCalled()
  })
  it('role query keeps exact SQL/binds and rejects a missing role before parsing', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    const json = vi.fn()
    expect((await POST({ json } as never)).status).toBe(403)
    expect(queryMock).toHaveBeenCalledExactlyOnceWith('SELECT role FROM profiles WHERE id = $1', ['admin'])
    expect(json).not.toHaveBeenCalled()
  })
  it.each([null, {}, { chart_id: '' }, { chart_id: false }])('missing chart %j is rejected before any command', async body => {
    expect((await POST(req(body))).status).toBe(400)
    expect(buildChartDataMock).not.toHaveBeenCalled()
  })
  it('malformed JSON follows the original chart-id-required response', async () => {
    const response = await POST({ json: () => Promise.reject(new SyntaxError('bad-json')) } as never)
    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({ error: 'chart_id required' })
    expect(buildChartDataMock).not.toHaveBeenCalled()
  })
})
