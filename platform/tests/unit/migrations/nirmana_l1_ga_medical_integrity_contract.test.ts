import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_medical integrity contract (migration 740, F-A14) — the FIRST migration in L1's
 * newly-granted continuation range (740-749, adjudication #1947).
 *
 * ga_medical's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the four documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the
 * NON-NEGOTIABLE disclosure invariants (indication_tier / not_diagnosis) are asserted
 * unconditionally, matching the writer's own stated discipline -- not a live-DB re-run of the
 * contract itself, which was verified and mutation-tested live against production during
 * authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/740_nirmana_l1_ga_medical_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 740')
  }
  return migration.slice(start + 4, end)
}

describe('migration 740 — ga_medical integrity_check_sql', () => {
  it('targets ga_medical by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_medical';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) §A Ethical Framework/)
    expect(migration).toMatch(/-- \(b\) indication_strength must equal/)
    expect(migration).toMatch(/-- \(c\) FORENSIC gate/)
  })

  it('asserts the NON-NEGOTIABLE disclosure invariants unconditionally, no exceptions', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("indication_tier <> 'jyotish_indication'")
    expect(detectorSql).toContain('not_diagnosis IS DISTINCT FROM true')
    // Neither check may be scoped to a specific chart/ayanamsha — it applies to every row.
    expect(detectorSql).not.toMatch(/indication_tier[\s\S]{0,80}chart_id\s*=/)
    expect(detectorSql).not.toMatch(/not_diagnosis[\s\S]{0,80}chart_id\s*=/)
  })

  it('re-derives indication_strength from the writer\'s own threshold formula, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('condition_score < 0.4')
    expect(detectorSql).toContain('condition_score <= 0.6')
    expect(migration).toMatch(/indication_strength_from_score/)
  })

  it('FORENSIC gate is scoped to the canonical chart + lahiri_chitrapaksha only, matching the writer\'s own scope', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("chart_id = '482012f1-710e-4a25-994a-93821f5871aa'")
    expect(detectorSql).toContain("ayanamsha_id = 'lahiri_chitrapaksha'")
    expect(detectorSql).toContain("graha = 'Sun' AND indication_strength <> 'strong'")
    expect(detectorSql).toContain("graha = 'Saturn' AND indication_strength <> 'mild'")
  })
})
