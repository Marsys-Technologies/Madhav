import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_condition varga_dignity_composite integrity contract (migration 658, F-A14).
 *
 * ga_condition's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the three documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and conjunct (a)'s
 * deliberate, documented red (F-C8, the still-unmerged PR #1853 fix) is disclosed honestly, not
 * silently suppressed or scoped away -- not a live-DB re-run of the contract itself, which was
 * verified and mutation-tested live against production during authoring (including a synthetic
 * "already fixed" overlay proving the conjunct is a real detector, not a permanent-red
 * placeholder).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/658_nirmana_l1_ga_condition_varga_composite_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 658')
  }
  return migration.slice(start + 4, end)
}

describe('migration 658 — ga_condition varga_dignity_composite integrity_check_sql', () => {
  it('targets ga_condition by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_condition';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) varga_dignity_composite must equal/)
    expect(migration).toMatch(/-- \(b\) is_deeply_combust implies is_combust/)
    expect(migration).toMatch(/-- \(c\) range guard/)
  })

  it('discloses the F-C8 red honestly — cites #1853, does not claim a clean pass', () => {
    expect(migration).toMatch(/ONE CONJUNCT RETURNS FALSE TODAY/)
    expect(migration).toMatch(/#1853/)
    expect(migration).toMatch(/F-C8/)
    // Never scoped around by excluding rows or charts from conjunct (a).
    expect(extractDetectorSql()).not.toMatch(/chart_id\s*<>/i)
  })

  it('re-derives the SAME normalization map F-A12 used (_DIVISIONAL_DIGNITY_NORMALIZE), not a fresh guess', () => {
    expect(migration).toMatch(/_DIVISIONAL_DIGNITY_NORMALIZE/)
    expect(migration).toMatch(/F-A12/)
    const detectorSql = extractDetectorSql()
    // The exact 7-way Title-Case -> score mapping the writer's corrected fallback uses.
    for (const label of ['Exalted', 'Moolatrikona', 'Own', 'Friend', 'Neutral', 'Debilitated']) {
      expect(detectorSql).toContain(`'${label}'`)
    }
  })

  it('verified the conjunct both ways — red on live data, green on a corrected overlay', () => {
    expect(migration).toMatch(/135\/135 mismatches/)
    expect(migration).toMatch(/0\/135 mismatches/)
  })
})
