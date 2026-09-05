import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_prashna integrity contract (migration 751, F-A14) — the LAST previously-untouched
 * asset in the F-A14 campaign.
 *
 * ga_prashna's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the three documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the migration
 * honestly documents why ga_prashna_judgment carries no conjunct (genuinely empty, not silently
 * skipped) -- not a live-DB re-run of the contract itself, which was verified and mutation-tested
 * live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/751_nirmana_l1_ga_prashna_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 751')
  }
  return migration.slice(start + 4, end)
}

describe('migration 751 — ga_prashna integrity_check_sql', () => {
  it('targets ga_prashna by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_prashna';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts, all scoped to ga_prashna_lagna', () => {
    expect(migration).toMatch(/-- \(a\) lagna_rashi must be one of the twelve classical signs/)
    expect(migration).toMatch(/-- \(b\) lagna_degree, when stored/)
    expect(migration).toMatch(/-- \(c\) every ga_prashna_lagna row must reference/)
    const detectorSql = extractDetectorSql()
    expect(detectorSql).not.toContain('ga_prashna_judgment')
  })

  it('documents honestly why ga_prashna_judgment carries no conjunct (empty, not skipped silently)', () => {
    expect(migration).toMatch(/ga_prashna_judgment is genuinely empty on every built chart today/)
    expect(migration).toMatch(/could not be/)
    expect(migration).toMatch(/mutation-proved/)
  })

  it('conjunct (c) cross-checks against a real prashna_charts registration, not a restated count', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('FROM prashna_charts pc WHERE pc.chart_id = l.chart_id')
  })
})
