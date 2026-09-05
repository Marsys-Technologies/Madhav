import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_yoga integrity contract (migration 746, F-A14).
 *
 * ga_yoga's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual test
 * verifies the migration's SHAPE -- the three documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and conjunct (a)'s
 * F-A16 documentation is intact -- not a live-DB re-run of the contract itself (which is EXPECTED
 * to read false live today, on the 4 rows F-A16 tracks; this was verified and mutation-tested
 * live against production, including a synthetic post-fix overlay proving it's a real detector,
 * during authoring).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/746_nirmana_l1_ga_yoga_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 746')
  }
  return migration.slice(start + 4, end)
}

describe('migration 746 — ga_yoga integrity_check_sql', () => {
  it('targets ga_yoga by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_yoga';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) F-A16: strength_formula_version must never be set/)
    expect(migration).toMatch(/-- \(b\) bhanga_active \/ bhanga_na_reason mutual exclusivity/)
    expect(migration).toMatch(/-- \(c\) is_partial honesty/)
  })

  it('documents F-A16 as a known-red finding, not a silently-narrowed check', () => {
    expect(migration).toMatch(/GENUINELY RED TODAY on/)
    expect(migration).toMatch(/4\/212 rows/)
    expect(migration).toMatch(/jaimini_karakamsha_rahu/)
  })

  it('conjunct (a) requires strength_formula_version to imply a non-null strength', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('strength_formula_version IS NOT NULL AND strength IS NULL')
  })

  it('conjunct (b) checks bhanga_active/bhanga_na_reason as an exact XOR', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('(bhanga_active IS NULL) <> (bhanga_na_reason IS NOT NULL)')
  })

  it('conjunct (c) requires partial_formation_pct whenever is_partial is true', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('is_partial = true AND partial_formation_pct IS NULL')
  })

  it('does not assert distinctness — the table UNIQUE already matches the natural key', () => {
    const codeOnly = extractDetectorSql()
      .split('\n')
      .map((line) => line.replace(/--.*$/, ''))
      .join('\n')
    expect(codeOnly).not.toMatch(/\bDISTINCT\b/i)
    expect(codeOnly).not.toMatch(/\bGROUP BY\b/i)
  })
})
