import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_yuddha_per_varga widening pass (migration
 * 759, F-A14) — the LAST migration in the 752-759 range.
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga (6/57). This adds
 * graha_yuddha_per_varga, taking coverage to 7/57. integrity_check_sql is a single UPDATE ... SET
 * column, not additive SQL, so migration 759 carries the nine prior conjuncts (a)-(i) forward
 * verbatim — including conjuncts (b)/(e)/(f), already genuinely red (tracked since migrations
 * 745/756/757) — plus three new conjuncts (j)/(k)/(l). This textual test verifies the migration's
 * SHAPE — read-only and bind-parameter-free, all twelve conjuncts survive — not a live-DB re-run
 * of the full combined contract (which cannot currently read true because of (b)/(e)/(f));
 * conjuncts (j)/(k)/(l) were verified live in isolation during authoring, each individually
 * mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/759_nirmana_l1_ga_structural_integrity_contract_yuddha.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 759')
  }
  return migration.slice(start + 4, end)
}

describe('migration 759 — ga_structural integrity_check_sql (graha_yuddha_per_varga, last in 752-759)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the nine prior conjuncts (a)-(i) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(c\) bhadra_flag\.active_at_birth_flag must agree exactly/,
      /-- \(d\) panchaka_flag\.active_at_birth_flag must equal/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(g\) For genuinely non-self-paired rows/,
      /-- \(h\) combustion_per_varga\.is_combust must equal/,
      /-- \(i\) combustion_per_varga\.arc_deg \(varga != 'D1'/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all three new conjuncts (j)/(k)/(l)', () => {
    expect(migration).toMatch(/-- \(j\) graha_yuddha_per_varga\.orb_deg .* must be <= 1\.0/)
    expect(migration).toMatch(/-- \(k\) graha_yuddha_per_varga\.graha1\/graha2 must never be Sun, Rahu, or Ketu/)
    expect(migration).toMatch(/-- \(l\) graha_yuddha_per_varga\.orb_deg \(varga != 'D1'/)
  })

  it('documents the D1 exclusion for (l) as the same shape as migration 758, not a fresh investigation', () => {
    expect(migration).toMatch(/5\/116 violations, ALL on D1/)
    expect(migration).toMatch(/same shape as[\s\S]{0,20}combustion_per_varga's own D1 exclusion/)
  })

  it('this is the last migration in the 752-759 range', () => {
    expect(migration).toMatch(/this is migration 759, the LAST number in\s*\n?\s*-- the 752-759 range/)
  })

  it('conjunct (k) excludes exactly Sun/Rahu/Ketu from both graha1 and graha2', () => {
    const detectorSql = extractDetectorSql()
    const kSection = detectorSql.slice(
      detectorSql.indexOf('-- (k)'),
      detectorSql.indexOf('-- (l)'),
    )
    expect(kSection).toContain("fact_value_jsonb->>'graha1' IN ('Sun', 'Rahu', 'Ketu')")
    expect(kSection).toContain("fact_value_jsonb->>'graha2' IN ('Sun', 'Rahu', 'Ketu')")
  })
})
