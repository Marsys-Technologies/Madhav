import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_tajaka integrity contract (migration 659, F-A14) — the LAST free number in L1's
 * 650-659 migration range.
 *
 * ga_tajaka's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the four documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the
 * accretion conjunct correctly omits build_id (the table's own UNIQUE constraint includes it,
 * so a naive "just check the UNIQUE key" conjunct would be redundant AND blind to the real
 * accretion risk) -- not a live-DB re-run of the contract itself, which was verified and
 * mutation-tested live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/659_nirmana_l1_ga_tajaka_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 659')
  }
  return migration.slice(start + 4, end)
}

describe('migration 659 — ga_tajaka integrity_check_sql', () => {
  it('targets ga_tajaka by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_tajaka';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) §N\.3 accretion detector/)
    expect(migration).toMatch(/-- \(b\) window validity/)
    expect(migration).toMatch(/-- \(c\) year_lord vocabulary/)
    expect(migration).toMatch(/-- \(d\) year_lord_method/)
  })

  it('accretion conjunct groups WITHOUT build_id, unlike the table\'s own UNIQUE constraint', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toMatch(/GROUP BY chart_id, ayanamsha_id, varsha_year/)
    expect(detectorSql).not.toMatch(/GROUP BY chart_id, ayanamsha_id, build_id, varsha_year/)
    expect(migration).toMatch(/UNIQUE key[\s\S]{0,20}includes build_id/)
  })

  it('year_lord vocabulary excludes Rahu/Ketu — a classical Tajika convention, not an observed gap', () => {
    const detectorSql = extractDetectorSql()
    // The IN(...) vocabulary list itself must name only the seven classical grahas — "Rahu"/
    // "Ketu" may still appear in the conjunct's own explanatory comment.
    expect(detectorSql).toContain("'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'")
    expect(migration).toMatch(/never year-lord candidates/)
  })

  it('discloses the exhausted migration range and the remaining F-A14 backlog', () => {
    expect(migration).toMatch(/LAST free number/)
    expect(migration).toMatch(/newly-assigned range from a future cycle/)
  })

  it('window duration tolerance allows real solar-return variance, not an exact 365-day pin', () => {
    expect(migration).toMatch(/NOT BETWEEN 364 AND 367/)
  })
})
