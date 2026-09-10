import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_sensitive integrity contract (migration 743, F-A14).
 *
 * ga_sensitive's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the three documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the
 * verification-status allowlist and bhava_arudha exception rule match what was measured live --
 * not a live-DB re-run of the contract itself, which was verified and mutation-tested live
 * against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/743_nirmana_l1_ga_sensitive_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 743')
  }
  return migration.slice(start + 4, end)
}

describe('migration 743 — ga_sensitive integrity_check_sql', () => {
  it('targets ga_sensitive by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_sensitive';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) verification_pass_status vocabulary/)
    expect(migration).toMatch(/-- \(b\) special_lagna's sign_lord/)
    expect(migration).toMatch(/-- \(c\) bhava_arudha's classical Parashari 2-exception rule/)
  })

  it('verification-status conjunct allows exactly two_pass_verified and floored, nothing else', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("verification_pass_status NOT IN ('two_pass_verified', 'floored')")
  })

  it('scopes to the same category family the count_sql already declares', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("'upagraha_position'")
    expect(detectorSql).toContain("'bhrigu_nadi_point'")
    expect(detectorSql).toContain("fact_category LIKE 'esoteric_point_%'")
    expect(detectorSql).toContain("fact_category LIKE 'tajik_%'")
    expect(detectorSql).toContain("fact_category = 'bhava_arudha'")
  })

  it('re-derives special_lagna sign_lord from the L0 reference_signs authority, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('reference_signs')
    expect(detectorSql).toContain("l.fact_category = 'special_lagna'")
    expect(detectorSql).toContain("l.fact_key = 'sign_lord'")
  })

  it('bhava_arudha exception rule checks both the origin house and the 7th-from-origin', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("substring(fact_subject from 'BHAVA_ARUDHA_A(\\d+)')::int")
    expect(detectorSql).toContain('- 1 + 6) % 12) + 1')
  })
})
