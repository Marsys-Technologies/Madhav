import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/626_nirmana_l0_cohort_exact_contract.sql'),
  'utf8',
)

describe('migration 626 — cohort exact integrity', () => {
  it('pins both projections and stays seed-aligned', () => {
    const cohort = ASSETS.find(asset => asset.asset_id === 'bg_cohort')

    expect(migration).toContain('921b0f62ca118932608ea3d3da89e8757ba7c6fbb64c41c2bbdc6b1f99e0c5fa')
    expect(migration).toContain('1f9e7fcf96941e891462ba1acd46b6c053f58d72d0dcb243a65d16a818c4decd')
    expect(migration).toContain('migration 626 refuses unknown bg_cohort registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(cohort).toMatchObject({
      count_sql: 'SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count',
      target_floor: 110000,
      depends_on: ['bg_ephemeris_engine'],
      expected_volume_formula: null,
      expected_volume_inputs: null,
    })
  })
})
