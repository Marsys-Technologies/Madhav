import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: vi.fn() }))

import { NON_SERVING_RECALIBRATION_ASSETS, runBlocksReadings } from '../servingImpact'
import { LEL_DEPENDENT_ASSETS } from '@/lib/build/recalibrationEnqueue'

describe('serving-impact classification', () => {
  it('declares exactly the LEL recalibration run signature as non-blocking', () => {
    expect([...NON_SERVING_RECALIBRATION_ASSETS].sort()).toEqual([...LEL_DEPENDENT_ASSETS].sort())
  })

  it('a recalibration subset does not block', () => {
    expect(runBlocksReadings({ scope: 'asset_set', planned_assets: ['mi_pramana'] })).toBe(false)
    expect(runBlocksReadings({ scope: 'asset', planned_assets: ['ph_pramana'] })).toBe(false)
  })

  it.each([
    [{ scope: 'global', planned_assets: ['mi_pramana'] }],
    [{ scope: 'layer', planned_assets: ['mi_pramana'] }],
    [{ scope: 'asset_set', planned_assets: ['mi_pramana', 'ga_positions'] }],
    [{ scope: 'asset_set', planned_assets: [] }],
    [{ scope: 'asset_set', planned_assets: null }],
    [{ scope: 'asset_set' }],
    [{ scope: undefined, planned_assets: ['mi_pramana'] }],
    [{ scope: 'something-new', planned_assets: ['mi_pramana'] }],
  ])('blocks %j', (run) => {
    expect(runBlocksReadings(run as never)).toBe(true)
  })
})
