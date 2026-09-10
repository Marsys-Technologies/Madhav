import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_sensitive_degree integrity contract (migration 744, F-A14).
 *
 * ga_sensitive_degree's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This
 * textual test verifies the migration's SHAPE -- the four documented conjuncts survive, the
 * contract is read-only and bind-parameter-free per the real elevation-pipeline validator, and
 * the modular-arithmetic offsets/margins match what was measured and mutation-fixed live -- not a
 * live-DB re-run of the contract itself, which was verified and mutation-tested live against
 * production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/744_nirmana_l1_ga_sensitive_degree_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 744')
  }
  return migration.slice(start + 4, end)
}

describe('migration 744 — ga_sensitive_degree integrity_check_sql', () => {
  it('targets ga_sensitive_degree by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_sensitive_degree';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) YOGI point_longitude must equal/)
    expect(migration).toMatch(/-- \(b\) AVAYOGI point_longitude must equal/)
    expect(migration).toMatch(/-- \(c\) SAHAYOGI must equal/)
    expect(migration).toMatch(/-- \(d\) DUPLICATE_YOGI\.assigned_graha must equal/)
  })

  it('YOGI offset formula uses the classical 93°20\' constant with a +720 non-negative margin', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('93.333333')
    expect(detectorSql).toContain('+ 720')
  })

  it('AVAYOGI offset formula uses the classical 186°40\' constant with the same +720 margin fix', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('186.666667')
    // Regression guard for the mutation-caught bug: a +360 margin is insufficient because
    // Postgres numeric mod() can return a NEGATIVE remainder for a negative dividend, which
    // silently fails a "> tolerance" comparison regardless of magnitude.
    expect(detectorSql).not.toMatch(/186\.666667 \+ 360\)/)
  })

  it('both offset conjuncts use LEAST-based modular-distance tolerance, not a raw diff check', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toMatch(/AND LEAST\(\s*\n\s*mod\(\(y\.fact_value_num/)
    expect(detectorSql).toMatch(/AND LEAST\(\s*\n\s*mod\(\(av\.fact_value_num/)
  })

  it('re-derives DUPLICATE_YOGI.assigned_graha from the L0 reference_signs authority, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('reference_signs')
    expect(detectorSql).toContain("g.fact_key = 'assigned_graha'")
  })
})
