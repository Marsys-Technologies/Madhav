import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 chart_divisionals integrity contract (migration 654, F-A14).
 *
 * ga_vargas' integrity_check_sql was NULL (D-L1-6: an unearned count(*)>0 fallback, §N.8). This
 * textual test verifies the migration's SHAPE -- the four documented conjuncts survive, the
 * contract is read-only and bind-parameter-free per the real elevation-pipeline validator, and
 * conjunct (c)'s deliberate, documented red (F-A1's already-tracked timing defect, caught at the
 * D1-sign grain) is not silently suppressed or scoped away -- not a live-DB re-run of the
 * contract itself, which was verified and mutation-tested live against production during
 * authoring (see the migration's own header for the traced root cause).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/654_nirmana_l1_ga_vargas_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 654')
  }
  return migration.slice(start + 4, end)
}

describe('migration 654 — ga_vargas integrity_check_sql', () => {
  it('targets ga_vargas by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_vargas';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) sign \/ sign_number internal consistency/)
    expect(migration).toMatch(/-- \(b\) vargottama correctness/)
    expect(migration).toMatch(/-- \(c\) §N\.5 D1 authority/)
    expect(migration).toMatch(/-- \(d\) identity range guard/)
  })

  it('does NOT re-assert distinctness against chart_divisionals_unique_idx (D-CND-03 rule 4)', () => {
    expect(migration).not.toMatch(/GROUP BY chart_id, graha, ayanamsha_id, varga, fact_category, fact_key/)
    expect(migration).toMatch(/chart_divisionals_unique_idx.*ALREADY a DB UNIQUE/s)
  })

  it('documents conjunct (c) as a DELIBERATE, traced, currently-red true positive -- not suppressed', () => {
    // The header must disclose the red conjunct honestly (D-CND-03 discipline), not claim a
    // clean pass. This guards against a future edit quietly scoping the F-A1 rows away instead
    // of leaving the detector to catch them until the rebuild lands.
    expect(migration).toMatch(/ONE CONJUNCT RETURNS FALSE TODAY/)
    expect(migration).toMatch(/F-A1/)
    expect(migration).toMatch(/RED TODAY on 4 rows/)
    expect(migration).not.toMatch(/AND cd\.chart_id\s*<>\s*'482012f1/) // no silent per-chart exclusion
    expect(migration).not.toMatch(/AND cd\.ayanamsha_id\s*<>\s*'raman'/) // no silent per-ayanamsha exclusion
  })

  it('vargottama conjunct re-derives from the SAME writer definition it checks, not a restated literal', () => {
    expect(migration).toMatch(/vg\.vargottama = \(d1pos\.sign = vpos\.sign\)/)
    expect(migration).toMatch(/_compute_vargottama/)
  })
})
