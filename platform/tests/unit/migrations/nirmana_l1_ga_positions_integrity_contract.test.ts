import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_positions integrity contract (migration 656, F-A14).
 *
 * ga_positions' integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the four documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the FORENSIC
 * gate conjunct stays scoped to the canonical chart only (never asserted chart-agnostically,
 * which would be a false claim about a different native's chart) -- not a live-DB re-run of the
 * contract itself, which was verified and mutation-tested live against production during
 * authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/656_nirmana_l1_ga_positions_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 656')
  }
  return migration.slice(start + 4, end)
}

describe('migration 656 — ga_positions integrity_check_sql', () => {
  it('targets ga_positions by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_positions';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) cross-category consistency/)
    expect(migration).toMatch(/-- \(b\) longitude_sidereal/)
    expect(migration).toMatch(/-- \(c\) FORENSIC gate/)
    expect(migration).toMatch(/-- \(d\) range guard/)
  })

  it('scopes the FORENSIC conjunct to the canonical chart only, not chart-agnostically', () => {
    const detectorSql = extractDetectorSql()
    // Every FORENSIC check must be gated on the canonical chart_id literal.
    const forensicBlocks = detectorSql.split("chart_id = '482012f1-710e-4a25-994a-93821f5871aa'")
    expect(forensicBlocks.length - 1).toBeGreaterThanOrEqual(3) // Sun, Moon nakshatra, Lagna
    expect(detectorSql).not.toMatch(/fact_value_text <> 'Capricorn'\s*\)\s*\n\s*\)\s*\n\s*AND NOT EXISTS/) // no un-scoped repeat
  })

  it('uses 1-indexed sign_num array lookup, not a fencepost-shifted one', () => {
    // Mutation-caught during authoring: sign_num is 1-indexed (LAGNA=1=Aries), so the array
    // lookup must index by sign_num directly, never sign_num + 1.
    expect(migration).toMatch(/\[t\.sign_num::int\]/)
    expect(migration).not.toMatch(/\[t\.sign_num::int \+ 1\]/)
  })

  it('longitude formula subtracts 1 from sign_num before multiplying by 30 (1-indexed correction)', () => {
    expect(migration).toMatch(/\(t\.sign_num - 1\) \* 30 \+ t\.deg_val/)
  })
})
