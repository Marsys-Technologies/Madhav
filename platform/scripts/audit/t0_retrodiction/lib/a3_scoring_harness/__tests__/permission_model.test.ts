/**
 * permission_model.test.ts — D-4b permission-bridge lane.
 *
 * SYNTHETIC/mocked HTTP only (a fake `fetchImpl` — no live sidecar, no DB,
 * no network), same "no live-data dependency in the unit test file"
 * discipline as model_interface.test.ts. The actual live end-to-end proof
 * (real sidecar, real chart 482012f1, real curve numbers) was run manually
 * against a locally-started sidecar during this lane's verification pass —
 * see the lane's own PR description for the cited real output; that proof
 * is not re-run automatically here because it requires a live uvicorn
 * process + Cloud SQL proxy, unavailable in CI (mirrors
 * `tests/integration/test_muhurat_finder_e2e.test.ts`'s own exclusion
 * rationale in vitest.config.ts).
 */
import { describe, it, expect, vi } from 'vitest'
import {
  permissionSystemModel,
  allPermissionSystemModels,
  PERMISSION_SYSTEM_IDS,
  PermissionCurveFetchError,
  PermissionModelNotBoundError,
} from '../permission_model'
import type { ChartContext } from '../model_interface'

const CHART: ChartContext = { chartId: 'synthetic-chart-permission', substrate: {} }
const RANGE: [Date, Date] = [new Date('2013-12-01T00:00:00Z'), new Date('2013-12-11T00:00:00Z')]

function fakeFetch(systemId: string, points: { t_datetime_ist: string; intensity: number }[]): typeof fetch {
  return vi.fn(async () =>
    new Response(
      JSON.stringify({ systems: { [systemId]: points } }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
  ) as unknown as typeof fetch
}

describe('PERMISSION_SYSTEM_IDS', () => {
  it('is exactly the 12 D-5 generators (8 dasha + sade_sati + guru_shani_double_transit + av_threshold + planetary_return)', () => {
    expect(PERMISSION_SYSTEM_IDS).toHaveLength(12)
    expect(new Set(PERMISSION_SYSTEM_IDS)).toEqual(new Set([
      'vimshottari', 'yogini', 'ashtottari', 'chara_karaka', 'naisargika', 'mudda', 'kalachakra', 'narayana',
      'sade_sati', 'guru_shani_double_transit', 'av_threshold', 'planetary_return',
    ]))
  })
})

describe('permissionSystemModel — validation', () => {
  it('rejects an unknown system_id at construction time, before any fetch', () => {
    // @ts-expect-error deliberately invalid id for the test
    expect(() => permissionSystemModel('not_a_real_system')).toThrow(/not one of the 12/)
  })
})

describe('permissionSystemModel — the bind()/curve() async bridge', () => {
  it('curve() throws PermissionModelNotBoundError before bind() has run for this (chart, eventClass, range)', () => {
    const model = permissionSystemModel('vimshottari', { sidecarUrl: 'http://fake' })
    expect(() => model.curve(CHART, 'marriage', RANGE)).toThrow(PermissionModelNotBoundError)
  })

  it('after bind(), curve() returns the mapped CurvePoint[] from the sidecar response, synchronously', async () => {
    const fetchImpl = fakeFetch('vimshottari', [
      { t_datetime_ist: '2013-12-01T05:30:00', intensity: 0.0 },
      { t_datetime_ist: '2013-12-06T05:30:00', intensity: 1.0 },
      { t_datetime_ist: '2013-12-11T05:30:00', intensity: 0.0 },
    ])
    const model = permissionSystemModel('vimshottari', { sidecarUrl: 'http://fake', fetchImpl })
    await model.bind!(CHART, 'marriage', RANGE)
    const curve = model.curve(CHART, 'marriage', RANGE)
    expect(curve).toHaveLength(3)
    expect(curve[1].intensity).toBe(1.0)
    expect(curve[1].date.toISOString()).toContain('2013-12-06')
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    const [url, init] = (fetchImpl as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('http://fake/api/compute/permission_curve')
    const body = JSON.parse((init as RequestInit).body as string)
    expect(body).toMatchObject({ chart_id: CHART.chartId, event_class: 'marriage', system_ids: ['vimshottari'] })
  })

  it('modelId equals the requested system_id (genuinely swappable per TemporalCurveModel)', () => {
    const model = permissionSystemModel('sade_sati', { sidecarUrl: 'http://fake' })
    expect(model.modelId).toBe('sade_sati')
  })

  it('a bind() for a DIFFERENT range does not satisfy curve() for the original range (cache is keyed per triple, not just per model)', async () => {
    const fetchImpl = fakeFetch('mudda', [{ t_datetime_ist: '2013-12-01T05:30:00', intensity: 1.0 }])
    const model = permissionSystemModel('mudda', { sidecarUrl: 'http://fake', fetchImpl })
    const otherRange: [Date, Date] = [new Date('1999-01-01T00:00:00Z'), new Date('1999-01-02T00:00:00Z')]
    await model.bind!(CHART, 'marriage', otherRange)
    expect(() => model.curve(CHART, 'marriage', RANGE)).toThrow(PermissionModelNotBoundError)
  })
})

describe('permissionSystemModel — error surfacing (never a silent empty curve)', () => {
  it('throws PermissionCurveFetchError on a non-2xx sidecar response', async () => {
    const fetchImpl = vi.fn(async () =>
      new Response(JSON.stringify({ detail: 't_end must be >= t_start' }), { status: 400 })
    ) as unknown as typeof fetch
    const model = permissionSystemModel('yogini', { sidecarUrl: 'http://fake', fetchImpl })
    await expect(model.bind!(CHART, 'marriage', RANGE)).rejects.toThrow(PermissionCurveFetchError)
    await expect(model.bind!(CHART, 'marriage', RANGE)).rejects.toThrow(/t_end must be >= t_start/)
  })

  it('throws PermissionCurveFetchError on a network failure', async () => {
    const fetchImpl = vi.fn(async () => {
      throw new Error('ECONNREFUSED')
    }) as unknown as typeof fetch
    const model = permissionSystemModel('ashtottari', { sidecarUrl: 'http://fake', fetchImpl })
    await expect(model.bind!(CHART, 'marriage', RANGE)).rejects.toThrow(PermissionCurveFetchError)
  })

  it('throws PermissionCurveFetchError if the response is missing the requested system entirely', async () => {
    const fetchImpl = vi.fn(async () =>
      new Response(JSON.stringify({ systems: {} }), { status: 200 })
    ) as unknown as typeof fetch
    const model = permissionSystemModel('kalachakra', { sidecarUrl: 'http://fake', fetchImpl })
    await expect(model.bind!(CHART, 'marriage', RANGE)).rejects.toThrow(PermissionCurveFetchError)
  })
})

describe('allPermissionSystemModels', () => {
  it('returns exactly 12 models, one per PERMISSION_SYSTEM_IDS entry, all sharing the injected opts', () => {
    const fetchImpl = vi.fn() as unknown as typeof fetch
    const models = allPermissionSystemModels({ sidecarUrl: 'http://fake', fetchImpl })
    expect(models).toHaveLength(12)
    expect(models.map((m) => m.modelId).sort()).toEqual([...PERMISSION_SYSTEM_IDS].sort())
  })
})
