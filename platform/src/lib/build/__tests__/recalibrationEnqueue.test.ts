/**
 * recalibrationEnqueue.test.ts — debounce + enqueue behavior.
 *
 * DB client + job invoker mocked. Coverage:
 *   1. Happy path: enqueues exactly one asset_set run over LEL_DEPENDENT_ASSETS.
 *   2. Quiet-window: a recent recalibration run coalesces (no second enqueue).
 *   3. force bypasses the quiet-window but still respects RUN_ACTIVE.
 *   4. RUN_ACTIVE coalesces (already queued, not an error).
 */

import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'

const { mockQuery, mockInvokeRunJob } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockInvokeRunJob: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))

import {
  enqueueLelRecalibration,
  LEL_DEPENDENT_ASSETS,
  LEL_RECAL_SCOPE_TARGET,
} from '@/lib/build/recalibrationEnqueue'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

// Registry: the LEL-dependent assets (all per_chart, dependency-ordered).
const REGISTRY = [
  { asset_id: 'ph_rectification', layer: 'phala',   scope: 'per_chart', depends_on: [],                  estimated_seconds: 30 },
  { asset_id: 'ph_pramana',       layer: 'phala',   scope: 'per_chart', depends_on: ['ph_rectification'], estimated_seconds: 30 },
  { asset_id: 'mi_jivanaghatana', layer: 'mimamsa', scope: 'per_chart', depends_on: ['ph_rectification'], estimated_seconds: 30 },
  { asset_id: 'mi_pramana',       layer: 'mimamsa', scope: 'per_chart', depends_on: ['mi_jivanaghatana'], estimated_seconds: 30 },
]

const q = mockQuery as unknown as MockInstance

beforeEach(() => {
  vi.clearAllMocks()
  mockInvokeRunJob.mockResolvedValue(undefined)
})

/** Seed the query chain for a successful enqueue (no force). */
function seedHappyPath({ lastRecal = false, active = false }: { lastRecal?: boolean; active?: boolean } = {}) {
  q.mockResolvedValueOnce({ rows: [{ value_jsonb: { seconds: 600 } }], rowCount: 1 }) // debounce constant
  q.mockResolvedValueOnce({ rows: lastRecal ? [{ id: 'prev-run' }] : [], rowCount: lastRecal ? 1 : 0 }) // last recal within window
  if (lastRecal) return // coalesced — no further queries
  q.mockResolvedValueOnce({ rows: active ? [{ id: 'active-run' }] : [], rowCount: active ? 1 : 0 }) // RUN_ACTIVE gate
  if (active) return
  q.mockResolvedValueOnce({ rows: REGISTRY, rowCount: REGISTRY.length }) // asset_registry
  q.mockResolvedValueOnce({ rows: [], rowCount: 0 }) // asset_throughput (all dormant)
  q.mockResolvedValueOnce({ rows: [{ id: 'run-recal-1' }], rowCount: 1 }) // INSERT build_runs
  q.mockResolvedValueOnce({ rows: [], rowCount: 1 }) // INSERT build_run_assets
}

describe('enqueueLelRecalibration', () => {
  it('LEL_DEPENDENT_ASSETS is the documented four-asset set', () => {
    expect([...LEL_DEPENDENT_ASSETS]).toEqual([
      'mi_jivanaghatana', 'mi_pramana', 'ph_rectification', 'ph_pramana',
    ])
    expect(LEL_RECAL_SCOPE_TARGET).toBe('mi_jivanaghatana,mi_pramana,ph_rectification,ph_pramana')
  })

  it('enqueues exactly one asset_set run over the LEL-dependent assets', async () => {
    seedHappyPath()
    const res = await enqueueLelRecalibration({ chartId: CHART, triggeredBy: 'uid-1' })

    expect(res.enqueued).toBe(true)
    if (res.enqueued) {
      expect(res.run_id).toBe('run-recal-1')
      // rebuild plan → all four, dependency-ordered.
      expect(res.plan).toContain('ph_rectification')
      expect(res.plan).toContain('mi_pramana')
    }
    expect(mockInvokeRunJob).toHaveBeenCalledOnce()

    // The build_runs INSERT carries scope='asset_set' + the LEL scope_target.
    const insert = q.mock.calls.find(c => typeof c[0] === 'string' && c[0].includes('INSERT INTO build_runs'))
    expect(insert).toBeDefined()
    const params = insert![1] as unknown[]
    expect(params[1]).toBe('asset_set')
    expect(params[2]).toBe(LEL_RECAL_SCOPE_TARGET)
  })

  it('coalesces (debounced) when a recalibration ran within the quiet-window', async () => {
    seedHappyPath({ lastRecal: true })
    const res = await enqueueLelRecalibration({ chartId: CHART })

    expect(res.enqueued).toBe(false)
    if (!res.enqueued) expect(res.reason).toBe('debounced')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
    // No build_runs INSERT happened.
    expect(q.mock.calls.some(c => typeof c[0] === 'string' && c[0].includes('INSERT INTO build_runs'))).toBe(false)
  })

  it('force bypasses the quiet-window and enqueues even after a recent recal', async () => {
    // With force, the debounce query is SKIPPED entirely — first query is RUN_ACTIVE.
    q.mockResolvedValueOnce({ rows: [], rowCount: 0 }) // RUN_ACTIVE gate
    q.mockResolvedValueOnce({ rows: REGISTRY, rowCount: REGISTRY.length }) // registry
    q.mockResolvedValueOnce({ rows: [], rowCount: 0 }) // throughput
    q.mockResolvedValueOnce({ rows: [{ id: 'run-forced' }], rowCount: 1 }) // INSERT build_runs
    q.mockResolvedValueOnce({ rows: [], rowCount: 1 }) // INSERT build_run_assets

    const res = await enqueueLelRecalibration({ chartId: CHART, force: true })
    expect(res.enqueued).toBe(true)
    if (res.enqueued) expect(res.run_id).toBe('run-forced')
    // No debounce constant read occurred.
    expect(q.mock.calls.some(c => typeof c[0] === 'string' && c[0].includes('mimamsa_recalibration_debounce_seconds'))).toBe(false)
  })

  it('force still respects RUN_ACTIVE (does not double-run a chart)', async () => {
    q.mockResolvedValueOnce({ rows: [{ id: 'active-run' }], rowCount: 1 }) // RUN_ACTIVE gate
    const res = await enqueueLelRecalibration({ chartId: CHART, force: true })
    expect(res.enqueued).toBe(false)
    if (!res.enqueued) {
      expect(res.reason).toBe('run_active')
      expect(res.existing_run_id).toBe('active-run')
    }
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('coalesces when a run is already active (already queued, not an error)', async () => {
    seedHappyPath({ active: true })
    const res = await enqueueLelRecalibration({ chartId: CHART })
    expect(res.enqueued).toBe(false)
    if (!res.enqueued) expect(res.reason).toBe('run_active')
  })
})
