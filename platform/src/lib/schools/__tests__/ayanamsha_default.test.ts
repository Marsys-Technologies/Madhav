// @vitest-environment node
/**
 * Lahiri-primary PR-5: the school-consensus build route and chart_data_adapter default to the STORED
 * id `lahiri_chitrapaksha` (they used to default to the short 'lahiri', which matches zero chart_facts
 * rows), normalise aliases through the PR-1 helper, and reject unknown ids / "all" with HTTP 400.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

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
