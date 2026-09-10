import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 fact_category_ownership backfill for ga_ayurdaya (migration 845, sixth in the
 * 840-859 range).
 *
 * Closes the ownership-registry half of F-E4 (L1_W1_ANALYSIS_BATCH_E.md):
 * `fact_category='ayurdaya'` had no row in `fact_category_ownership` at all (confirmed live,
 * cycle 108) -- the same GA.1-class registry-disagreement pattern D-L1-105/F-C9 already fixed
 * once for ga_structural (migration 842). Unlike ga_structural's count_sql (a JOIN against this
 * table), ga_ayurdaya's count_sql filters on fact_category directly -- so this is an
 * attribution/audit-trail gap (§N.5), not a functional undercount; count_sql is untouched here.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * drop the ownership row or change the owning asset.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/845_nirmana_l1_ga_ayurdaya_category_ownership_backfill.sql',
  ),
  'utf8',
)

describe('migration 845 — fact_category_ownership backfill (ga_ayurdaya)', () => {
  it("inserts the 'ayurdaya' category, owned by ga_ayurdaya", () => {
    expect(migration).toContain("('ayurdaya', 'ga_ayurdaya')")
  })

  it('uses the same idempotent ON CONFLICT DO NOTHING pattern migration 410/842 established', () => {
    expect(migration).toContain('ON CONFLICT (fact_category, owning_asset_id) DO NOTHING')
  })

  it('does not touch asset_registry.count_sql -- ga_ayurdaya filters on fact_category directly, not via this table', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/UPDATE\s+asset_registry/i)
  })

  it('cites F-E4 as the finding this closes', () => {
    expect(migration).toContain('F-E4')
  })

  it('documents this as the sixth migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })
})
