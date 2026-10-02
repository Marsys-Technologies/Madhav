import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * Pravāha A2.5 — ka_gochara_v4_41_candidate must be INERT to all planners.
 *
 * Two planner surfaces select from asset_registry by is_active:
 *   1. runPreparation's planning set — src/lib/build/runPreparation.ts:183:
 *        WHERE is_active = true
 *   2. recalibrationEnqueue's writer sweep — src/lib/build/recalibrationEnqueue.ts:141:
 *        WHERE is_active = true AND has_writer = true
 *
 * This test reproduces both predicates over the SEED (the runSeed() source of
 * truth — the upsert's ON CONFLICT clause keeps is_active under seed control)
 * and asserts the A2.5 candidate asset is selected by NEITHER. The only
 * activation path is the steward dispatch script's transient flip/restore
 * (scripts/dispatch_a25_v41_candidate_job.py).
 */
const A25_ASSET_ID = 'ka_gochara_v4_41_candidate'

describe('A2.5 candidate asset planner inertness', () => {
  it('the seed row exists, is inactive, and is dependency-free', () => {
    const row = ASSETS.find((a) => a.asset_id === A25_ASSET_ID)
    expect(row, 'seed row missing').toBeDefined()
    expect(row!.is_active).toBe(false)
    expect(row!.depends_on ?? []).toEqual([])
    expect(row!.has_writer).toBe(true)
    // ASTRA A2.5 A10: the seed must carry the same timeout the dispatch stages
    // (7200s) — ON CONFLICT DO NOTHING preserves the seeded value, and the
    // runner reads the registry timeout, so a seeded default (600) would
    // silently cap this two-hour job at ten minutes.
    expect((row as unknown as { writer_timeout_seconds?: number }).writer_timeout_seconds).toBe(7200)
  })

  it("runPreparation's predicate (is_active = true) does not select it", () => {
    const planningSet = ASSETS.filter((a) => a.is_active === true)
    expect(planningSet.map((a) => a.asset_id)).not.toContain(A25_ASSET_ID)
  })

  it("recalibrationEnqueue's predicate (is_active AND has_writer) does not select it", () => {
    const sweep = ASSETS.filter(
      (a) => a.is_active === true && (a as { has_writer?: boolean }).has_writer === true
    )
    expect(sweep.map((a) => a.asset_id)).not.toContain(A25_ASSET_ID)
  })

  it('no seeded asset depends on it (no DAG build can schedule it)', () => {
    const dependents = ASSETS.filter((a) => (a.depends_on ?? []).includes(A25_ASSET_ID))
    expect(dependents.map((a) => a.asset_id)).toEqual([])
  })
})
