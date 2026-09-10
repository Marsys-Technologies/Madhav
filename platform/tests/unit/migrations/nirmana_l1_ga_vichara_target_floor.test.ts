import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 ga_vichara target_floor correction (migration 846, seventh in the 840-859 range).
 *
 * Closes the residual half of F-D10 (L1_W1_ANALYSIS_BATCH_D.md): the finding's own derived
 * model (5 x (1595+35+9+9) + 9 = 8,249) had already been applied to target_floor at some point,
 * but landed nine short at 8,240 -- confirmed live, cycle 109, against chart_vichara's own
 * count_sql (8,249 today). The gap never surfaced as a build failure since achieved (8,249)
 * already exceeded the stale floor (8,240); it was only a registry drift.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * revert the floor to a stale or fabricated number.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/846_nirmana_l1_ga_vichara_target_floor.sql'),
  'utf8',
)

describe('migration 846 — ga_vichara target_floor correction', () => {
  it('sets target_floor to 8249, the live achieved count, not the stale 8240', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET target_floor = 8249 WHERE asset_id = 'ga_vichara'/)
  })

  it('touches ONLY target_floor -- no count_sql rewrite', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/SET\s+count_sql\s*=/i)
  })

  it('cites F-D10 as the finding this closes', () => {
    expect(migration).toContain('F-D10')
  })

  it('documents this as the seventh migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })
})
