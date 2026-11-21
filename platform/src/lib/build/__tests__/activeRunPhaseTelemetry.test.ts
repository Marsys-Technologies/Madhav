import { beforeEach, describe, expect, it, vi } from 'vitest'

const h = vi.hoisted(() => ({
  query: vi.fn(),
  blockedProbe: vi.fn(),
  phaseProbe: vi.fn(),
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: h.query }))
vi.mock('@/lib/db/columnPresence', () => ({
  blockedByAssetIdColumnPresent: h.blockedProbe,
  phaseTelemetryColumnsPresent: h.phaseProbe,
}))

import { readActiveBuildRun } from '../activeRunData'
import { readPreparationDuration } from '../preparationDuration'
import type { RegistryEntry } from '../plan'

const CHART = '00000000-0000-4000-8000-000000000010'
const RUN = {
  id: 'run-1421',
  scope: 'layer',
  scope_target: 'ganita',
  action: 'build',
  state: 'running',
  plan: ['ga_positions', 'ga_dashas'],
  current_asset_id: 'ga_dashas',
  created_at: '2026-11-21T00:00:00Z',
  started_at: '2026-11-21T00:00:01Z',
  pause_requested_at: null,
  stop_requested_at: null,
}

beforeEach(() => {
  vi.resetAllMocks()
  h.blockedProbe.mockResolvedValue(true)
  h.phaseProbe.mockResolvedValue(true)
})

describe('NIR-03 & NIR-06 activeRunData + preparationDuration phase telemetry', () => {
  it.each([true, false])(
    'readActiveBuildRun selects durable phase columns when present=%s and degrades gracefully otherwise',
    async (phasePresent) => {
      h.phaseProbe.mockResolvedValue(phasePresent)
      const assetRows = [
        {
          asset_id: 'ga_dashas',
          position: 1,
          state: 'building',
          started_at: '2026-11-21T00:00:02Z',
          ended_at: null,
          error: null,
          disposition: null,
          blocked_by_asset_id: null,
          phase: phasePresent ? 'writing' : null,
          substep_index: phasePresent ? 14 : null,
          substep_total: phasePresent ? 35 : null,
          substep_label: phasePresent ? 'Vimshottari · Lahiri' : null,
          compute_ms: phasePresent ? 85 : null,
          write_ms: null,
          verify_ms: null,
          publish_ms: null,
        },
      ]
      h.query
        .mockResolvedValueOnce({ rows: [RUN] })
        .mockResolvedValueOnce({ rows: assetRows })

      const res = await readActiveBuildRun(CHART)
      expect(res).toEqual({ run: RUN, assets: assetRows })

      const assetSql = String(h.query.mock.calls[1][0])
      expect(assetSql.includes('phase, substep_index, substep_total, substep_label')).toBe(phasePresent)
      expect(assetSql.includes('NULL::text AS phase, NULL::integer AS substep_index')).toBe(!phasePresent)
    },
  )

  it('readPreparationDuration returns phase_breakdown when migration 1421 telemetry exists', async () => {
    h.phaseProbe.mockResolvedValue(true)
    h.query
      .mockResolvedValueOnce({
        rows: [{ sample_count: 4, last_seconds: 120, lower_seconds: 110, upper_seconds: 135 }],
      })
      .mockResolvedValueOnce({
        rows: [{ sample_runs: 3, compute_ms: 400, write_ms: 112000, verify_ms: 3500, publish_ms: 1200 }],
      })

    const res = await readPreparationDuration({
      chartId: CHART,
      action: 'rebuild',
      scope: 'layer',
      target: 'ganita',
      assets: ['ga_positions'],
      registry: [],
    })

    expect(res).toEqual({
      sample_count: 4,
      last_seconds: 120,
      lower_seconds: 110,
      upper_seconds: 135,
      phase_breakdown: {
        compute_ms: 400,
        write_ms: 112000,
        verify_ms: 3500,
        publish_ms: 1200,
        total_ms: 117100,
        sample_runs: 3,
      },
    })
  })

  it('readPreparationDuration skips phase_breakdown on pre-1421 schemas and combines separate layers when present', async () => {
    h.phaseProbe.mockResolvedValue(false)
    h.query.mockResolvedValueOnce({
      rows: [{ sample_count: 2, last_seconds: 90, lower_seconds: 80, upper_seconds: 100 }],
    })
    const pre = await readPreparationDuration({
      chartId: CHART,
      action: 'rebuild',
      scope: 'layer',
      target: 'ganita',
      assets: ['ga_positions'],
      registry: [],
    })
    expect(pre).toEqual({ sample_count: 2, last_seconds: 90, lower_seconds: 80, upper_seconds: 100 })
    expect(h.query).toHaveBeenCalledTimes(1)

    vi.resetAllMocks()
    h.phaseProbe.mockResolvedValue(true)
    const registry = [
      { asset_id: 'ga_positions', layer: 'ganita', depends_on: [], estimated_seconds: 10 },
      { asset_id: 'bo_laksana', layer: 'bodha', depends_on: ['ga_positions'], estimated_seconds: 20 },
    ] as RegistryEntry[]
    h.query
      .mockResolvedValueOnce({ rows: [{ sample_count: 0, last_seconds: null, lower_seconds: null, upper_seconds: null }] })
      .mockResolvedValueOnce({ rows: [{ sample_count: 1, last_seconds: 60, lower_seconds: 60, upper_seconds: 60 }] })
      .mockResolvedValueOnce({ rows: [{ sample_count: 1, last_seconds: 180, lower_seconds: 180, upper_seconds: 180 }] })
      .mockResolvedValueOnce({ rows: [{ sample_runs: 1, compute_ms: 200, write_ms: 58000, verify_ms: 1000, publish_ms: 800 }] })
      .mockResolvedValueOnce({ rows: [{ sample_runs: 1, compute_ms: 300, write_ms: 175000, verify_ms: 4000, publish_ms: 700 }] })

    const combined = await readPreparationDuration({
      chartId: CHART,
      action: 'rebuild',
      scope: 'asset_set',
      target: 'ga_positions,bo_laksana',
      assets: ['ga_positions', 'bo_laksana'],
      registry,
    })
    expect(combined).toEqual({
      sample_count: 0,
      last_seconds: null,
      lower_seconds: null,
      upper_seconds: null,
      separate_layers: { ganita: 60, bodha: 180 },
      phase_breakdown: {
        compute_ms: 500,
        write_ms: 233000,
        verify_ms: 5000,
        publish_ms: 1500,
        total_ms: 240000,
        sample_runs: 1,
      },
    })
  })
})
