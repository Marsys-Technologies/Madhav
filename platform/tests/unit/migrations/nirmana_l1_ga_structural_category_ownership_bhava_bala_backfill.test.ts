import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 fact_category_ownership backfill for ga_structural (migration 842, third in the
 * 840-859 range).
 *
 * Closes D-L1-105 (L1_STATE.md decisions log, cycle 86): `fact_category_ownership` was found
 * missing registry rows for 7 real, migration-796-covered categories (`bhava_bala_positional`/
 * `bhava_bala_directional`/`bhava_bala_temporal`/`bhava_bala_aspectual`/`bhava_bala_occupant`/
 * `bhava_bala_lord`/`bhava_bala_total_extended`) -- confirmed live, each a real, data-populated
 * `chart_facts` category (60 rows per chart) owned by no asset at all. D-L1-105 deliberately
 * deferred the fix as an "open, correctly-scoped follow-up" rather than folding it into an
 * unrelated integrity-contract migration. This is also the live mechanism behind F-C9
 * (L1_W2_DECIDE_v1_0.md §3): `ga_structural`'s `count_sql` (a `JOIN fact_category_ownership`
 * since migration 410) omits ~5,157 owned rows because the registry undercounts, not because
 * `count_sql` itself is wrong -- migration 410 already pointed it at this table.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * drop one of the 7 names, change the owning asset, or lose the idempotent ON CONFLICT guard.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/842_nirmana_l1_ga_structural_category_ownership_bhava_bala_backfill.sql',
  ),
  'utf8',
)

const SEVEN_CATEGORIES = [
  'bhava_bala_positional',
  'bhava_bala_directional',
  'bhava_bala_temporal',
  'bhava_bala_aspectual',
  'bhava_bala_occupant',
  'bhava_bala_lord',
  'bhava_bala_total_extended',
]

describe('migration 842 — fact_category_ownership backfill (ga_structural Bhava Bala group)', () => {
  it('inserts all seven Bhava Bala categories, each owned by ga_structural', () => {
    for (const category of SEVEN_CATEGORIES) {
      expect(migration).toContain(`('${category}', 'ga_structural')`)
    }
  })

  it('inserts exactly seven rows, not more and not fewer', () => {
    const matches = migration.match(/\('bhava_bala_\w+', 'ga_structural'\)/g) ?? []
    expect(matches).toHaveLength(SEVEN_CATEGORIES.length)
  })

  it('uses the same idempotent ON CONFLICT DO NOTHING pattern migration 410 established', () => {
    expect(migration).toContain('ON CONFLICT (fact_category, owning_asset_id) DO NOTHING')
  })

  it('does not touch asset_registry.count_sql -- migration 410 already points it at this table', () => {
    expect(migration).not.toMatch(/UPDATE\s+asset_registry/i)
  })

  it('cites D-L1-105 and F-C9 as the findings this closes', () => {
    expect(migration).toContain('D-L1-105')
    expect(migration).toContain('F-C9')
  })

  it('documents this as the third migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })
})
