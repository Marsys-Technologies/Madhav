import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract (migration 745, F-A14).
 *
 * ga_structural's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the two documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and conjunct (b)'s
 * F-A15 cross-authority check targets the correct table/category -- not a live-DB re-run of the
 * contract itself (which is EXPECTED to read false live today, on the 4 rows F-A15 tracks; this
 * was verified and mutation-tested live against production, including a synthetic post-fix
 * overlay proving it's a real detector, during authoring).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/745_nirmana_l1_ga_structural_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 745')
  }
  return migration.slice(start + 4, end)
}

describe('migration 745 — ga_structural integrity_check_sql', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries both documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) amplification_factor domain/)
    expect(migration).toMatch(/-- \(b\) F-A15: amplification_factor must agree/)
  })

  it('documents F-A15 as a known-red finding, not a silently-narrowed check', () => {
    expect(migration).toMatch(/GENUINELY RED TODAY on 4\/105 rows/)
    expect(migration).toMatch(/synthetic post-fix overlay/)
  })

  it('conjunct (a) restricts amplification_factor to exactly the two legitimate values', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("fact_value_num NOT IN (1.0, 1.25)")
  })

  it("conjunct (b) cross-checks against ga_vargas' D9 varga_vargottama_flag authority (§N.5)", () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('chart_divisionals')
    expect(detectorSql).toContain("v.fact_category = 'varga_vargottama_flag' AND v.varga = 'D9'")
    expect(detectorSql).toContain('(a.fact_value_num = 1.25) <> v.vargottama')
  })
})
