import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 ga_panchanga target_floor re-baseline (migration 843, fourth in the 840-859
 * range).
 *
 * Closes F-B31 (L1_W1_ANALYSIS_BATCH_B.md): `target_floor` was still 221 against a live
 * achieved count of 437 (confirmed live via count_sql re-execution, cycle 105) -- the same
 * stale-floor defect class as F-A9/F-B1/F-D14/F-E1/F-E15, already re-baselined per cycle 103's
 * investigation, just never itself corrected. The finding's false `expected_volume_formula`
 * half is already fixed (confirmed NULL live); only the floor number was left behind.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * revert the floor to a stale or fabricated number.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/843_nirmana_l1_ga_panchanga_target_floor.sql'),
  'utf8',
)

describe('migration 843 — ga_panchanga target_floor re-baseline', () => {
  it('sets target_floor to 437, the live achieved count, not a fabricated number', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET target_floor = 437 WHERE asset_id = 'ga_panchanga'/)
  })

  it('touches ONLY target_floor -- no count_sql or expected_volume_formula rewrite', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/count_sql\s*=/)
    expect(sqlBody).not.toMatch(/expected_volume_formula\s*=/)
  })

  it('cites F-B31 as the finding this closes', () => {
    expect(migration).toContain('F-B31')
  })

  it('documents this as the fourth migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })
})
