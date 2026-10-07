import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * Pravāha A5.3 — ka_gochara_v5 must be INERT to all planners.
 *
 * Mirrors PR #2799's a25_v41_candidate_inert.test.ts. Two planner surfaces
 * select from asset_registry by is_active:
 *   1. runPreparation's planning set — src/lib/build/runPreparation.ts:183:
 *        WHERE is_active = true
 *   2. recalibrationEnqueue's writer sweep — src/lib/build/recalibrationEnqueue.ts:141:
 *        WHERE is_active = true AND has_writer = true
 *
 * This test reproduces both predicates over the SEED (the runSeed() source of
 * truth — the upsert's ON CONFLICT clause keeps is_active under seed control)
 * and asserts the A5.3 skeleton asset is selected by NEITHER. The writer
 * module itself is a registered skeleton whose every execution path raises
 * NotImplementedError pending steward pins 3-7 (M20261001T014547-357e).
 */
const A53_ASSET_ID = 'ka_gochara_v5'

describe('A5.3 ka_gochara_v5 asset planner inertness', () => {
  it('the seed row exists, is inactive, and carries the migration-1304 dependencies (inactive rows are never planned)', () => {
    const row = ASSETS.find((a) => a.asset_id === A53_ASSET_ID)
    expect(row, 'seed row missing').toBeDefined()
    expect(row!.is_active).toBe(false)
    expect(row!.depends_on ?? []).toEqual(['ga_positions', 'ga_dashas'])      // the migration-1304 value (PR 3101); the planner never selects an inactive row
    expect(row!.has_writer).toBe(true)
  })

  it("runPreparation's predicate (is_active = true) does not select it", () => {
    const planningSet = ASSETS.filter((a) => a.is_active === true)
    expect(planningSet.map((a) => a.asset_id)).not.toContain(A53_ASSET_ID)
  })

  it("recalibrationEnqueue's predicate (is_active AND has_writer) does not select it", () => {
    const sweep = ASSETS.filter(
      (a) => a.is_active === true && (a as { has_writer?: boolean }).has_writer === true
    )
    expect(sweep.map((a) => a.asset_id)).not.toContain(A53_ASSET_ID)
  })

  it('no seeded asset depends on it (no DAG build can schedule it)', () => {
    const dependents = ASSETS.filter((a) => (a.depends_on ?? []).includes(A53_ASSET_ID))
    expect(dependents.map((a) => a.asset_id)).toEqual([])
  })
})
