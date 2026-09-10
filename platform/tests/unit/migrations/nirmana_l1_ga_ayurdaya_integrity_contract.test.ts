import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_ayurdaya integrity contract (migration 750, F-A14).
 *
 * ga_ayurdaya's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the three documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the exact
 * classification thresholds/method names match the writer's own constants -- not a live-DB
 * re-run of the contract itself, which was verified and mutation-tested live against production
 * during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/750_nirmana_l1_ga_ayurdaya_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 750')
  }
  return migration.slice(start + 4, end)
}

describe('migration 750 — ga_ayurdaya integrity_check_sql', () => {
  it('targets ga_ayurdaya by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_ayurdaya';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) classification \(stored as fact_value_text/)
    expect(migration).toMatch(/-- \(b\) applicable_method's embedded value_jsonb\.totals/)
    expect(migration).toMatch(/-- \(c\) each total_years row's own value must equal/)
  })

  it("matches the writer's own classify_ayus() thresholds exactly", () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("fact_value_num < 32.0 THEN 'alpayu'")
    expect(detectorSql).toContain("fact_value_num < 64.0 THEN 'madhyayu'")
    expect(detectorSql).toContain("ELSE 'purnayu'")
  })

  it('cross-checks all three method subjects by name (PINDAYU, NISARGAYU, AMSAYU)', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("p.fact_subject = 'PINDAYU'")
    expect(detectorSql).toContain("n.fact_subject = 'NISARGAYU'")
    expect(detectorSql).toContain("a.fact_subject = 'AMSAYU'")
  })

  it('re-derives the total from per_graha + lagna_years via jsonb_each_text, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('jsonb_each_text(fact_value_jsonb->\'per_graha\')')
    expect(detectorSql).toContain("fact_value_jsonb->>'lagna_years'")
  })
})
