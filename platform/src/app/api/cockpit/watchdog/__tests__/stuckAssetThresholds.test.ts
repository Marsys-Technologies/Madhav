import { describe, expect, it } from 'vitest'
import {
  DEFAULT_STUCK_ASSET_THRESHOLD_SECONDS,
  stuckThresholdOverrideParams,
  stuckThresholdSeconds,
} from '../stuckAssetThresholds'

// J-3c (EXEC-J3C-REPROJECT-1): ka_gochara_v5 substep 34 verify:bereavement, healthy run.
const MEASURED_LONGEST_HEALTHY_SUBSTEP_SECONDS = 1086.8

describe('stuck-asset thresholds (HYG-REAPER-LONG-SUBSTEP)', () => {
  it('keeps the 15-minute default for an asset with no entry', () => {
    expect(stuckThresholdSeconds('ga_dashas')).toBe(900)
    expect(DEFAULT_STUCK_ASSET_THRESHOLD_SECONDS).toBe(900)
  })

  it('gives ka_gochara_v5 at least 3x the measured longest healthy substep (SR-J3-REAPER-PAUSE stall rule: 3 x longest)', () => {
    expect(stuckThresholdSeconds('ka_gochara_v5')).toBeGreaterThanOrEqual(3 * MEASURED_LONGEST_HEALTHY_SUBSTEP_SECONDS)
  })

  it('an override can only lengthen the grace, never shorten the default', () => {
    expect(stuckThresholdSeconds('x', { x: 60 })).toBe(900)
    expect(stuckThresholdOverrideParams({ x: 60, y: 1800 })).toEqual([['y'], [1800]])
  })
})
