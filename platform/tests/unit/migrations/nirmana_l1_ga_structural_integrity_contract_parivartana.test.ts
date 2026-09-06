import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — parivartana_per_varga widening pass (migration
 * 757, F-A14). Ships the already-fixed-at-the-writer-level F-157 finding as a real, currently-red
 * data conjunct.
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga (4/57). This adds
 * parivartana_per_varga, taking coverage to 5/57. integrity_check_sql is a single UPDATE ... SET
 * column, not additive SQL, so migration 757 carries the five prior conjuncts (a)-(e) forward
 * verbatim — including conjuncts (b) and (e), already genuinely red (tracked since migrations 745
 * and 756) — plus two new conjuncts (f)/(g). Conjunct (f) is ALSO genuinely red today (F-157: 439
 * of 624 rows are still self-paired, materialized before the writer's own fix landed). This
 * textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all seven
 * conjuncts survive — not a live-DB re-run of the full combined contract (which cannot currently
 * read true); conjuncts (f)/(g) were verified live in isolation during authoring, including a
 * synthetic post-fix proof (deleting the self-paired rows) showing conjunct (f) genuinely clears.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/757_nirmana_l1_ga_structural_integrity_contract_parivartana.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 757')
  }
  return migration.slice(start + 4, end)
}

describe('migration 757 — ga_structural integrity_check_sql (parivartana_per_varga, F-157)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the five prior conjuncts (a)-(e) verbatim, including the still-red (b) and (e)', () => {
    expect(migration).toMatch(/-- \(a\) amplification_factor domain/)
    expect(migration).toMatch(/-- \(b\) F-A15: amplification_factor must agree/)
    expect(migration).toMatch(/-- \(c\) bhadra_flag\.active_at_birth_flag must agree exactly/)
    expect(migration).toMatch(/-- \(d\) panchaka_flag\.active_at_birth_flag must equal/)
    expect(migration).toMatch(/-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/)
  })

  it('carries both new conjuncts (f)/(g) and documents F-157 as a known-red finding, not a silently-narrowed check', () => {
    expect(migration).toMatch(/-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/)
    expect(migration).toMatch(/GENUINELY RED TODAY on 439\/624 rows/)
    expect(migration).toMatch(/-- \(g\) For genuinely non-self-paired rows/)
  })

  it('documents why graha_dignity_per_varga was investigated but not pursued (vocabulary mismatch, not a defect)', () => {
    expect(migration).toMatch(/VOCABULARY GRANULARITY mismatch, not a computation defect/)
  })

  it('conjunct (f) checks planet_a/planet_b equality directly, re-deriving the writer\'s own guard', () => {
    const detectorSql = extractDetectorSql()
    const fSection = detectorSql.slice(
      detectorSql.indexOf('-- (f)'),
      detectorSql.indexOf('-- (g)'),
    )
    expect(fSection).toContain("fact_value_jsonb->>'planet_a' = fact_value_jsonb->>'planet_b'")
  })

  it('conjunct (g) re-derives the classical parivartana condition in BOTH directions via SIGN_LORDS, excludes self-paired rows already covered by (f)', () => {
    const detectorSql = extractDetectorSql()
    const gSection = detectorSql.slice(detectorSql.indexOf('-- (g)'))
    expect(gSection).toContain("fact_value_jsonb->>'planet_a' <> fact_value_jsonb->>'planet_b'")
    expect(gSection).toContain("fact_value_jsonb->>'sign_a'")
    expect(gSection).toContain("fact_value_jsonb->>'sign_b'")
    // spot-check a few classical sign-lord pairs are present, not just a subset
    for (const [sign, lord] of [
      ['Aries', 'Mars'], ['Cancer', 'Moon'], ['Leo', 'Sun'],
      ['Sagittarius', 'Jupiter'], ['Capricorn', 'Saturn'],
    ]) {
      expect(gSection).toContain(`WHEN '${sign}' THEN '${lord}'`)
    }
  })
})
