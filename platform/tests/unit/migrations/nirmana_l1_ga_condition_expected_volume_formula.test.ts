import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 ga_condition expected_volume_formula (migration 851, ninth in the 840-859
 * range).
 *
 * Closes F-C10 (L1_W1_ANALYSIS_BATCH_C.md, MUST): `target_floor` (2,880) is a genuine,
 * live-verified achieved count for this fully-deterministic structural asset (one row per
 * graha per varga/avastha type, no variable-length data) -- the floor itself was never wrong.
 * `expected_volume_formula` was NULL, leaving 2,880 an undocumented arithmetic identity
 * rather than a derived, auditable formula (C12: "derive, never pick"). This migration
 * populates it with the real, live-verified 8-component breakdown (45*6 + 1305*2 = 2880).
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * revert the formula to NULL or a fabricated number.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/851_nirmana_l1_ga_condition_expected_volume_formula.sql'),
  'utf8',
)

describe('migration 851 — ga_condition expected_volume_formula', () => {
  it('sets expected_volume_formula to the live-verified 8-component breakdown summing to 2880', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).toMatch(/expected_volume_formula = '45\(ga_condition_composite\)/)
    expect(sqlBody).toContain('= 2880')
    expect(sqlBody).toContain("WHERE asset_id = 'ga_condition'")
  })

  it('names all 8 real component categories, not a bare number', () => {
    for (const category of [
      'ga_condition_composite',
      'graha_avastha_baladi_per_varga',
      'graha_avastha_deeptaadi_per_varga',
      'graha_avastha_jagradadi_per_varga',
      'graha_avastha_lajjitadi',
      'graha_avastha_lajjitadi_per_varga',
      'graha_avastha_sayanadi',
      'graha_avastha_sayanadi_per_varga',
    ]) {
      expect(migration).toContain(category)
    }
  })

  it('touches ONLY expected_volume_formula -- no target_floor or count_sql rewrite', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/SET\s+(?!expected_volume_formula\s*=)/i)
  })

  it('cites F-C10 as the finding this closes', () => {
    expect(migration).toContain('F-C10')
  })

  it('documents this as the ninth migration in the 840-859 range and notes the L3 range encroachment', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
    expect(migration).toContain('#2156')
  })
})
