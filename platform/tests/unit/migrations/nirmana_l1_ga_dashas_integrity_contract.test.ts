import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 chart_dashas integrity contract (migration 653, F-A14).
 *
 * ga_dashas' integrity_check_sql was NULL (D-L1-6: with it NULL the freeze-time detector falls
 * back to `count(*) > 0`, an unearned signal per §N.8). This textual test verifies the migration's
 * SHAPE (the four documented conjuncts survive, the mudda carve-out is not silently dropped, the
 * SQL is read-only and bind-parameter-free per the real elevation-pipeline validator) -- not a
 * live-DB re-run of the contract itself, which was verified and mutation-tested live against
 * production during authoring (see the migration's own header).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/653_nirmana_l1_ga_dashas_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 653')
  }
  return migration.slice(start + 4, end)
}

describe('migration 653 — ga_dashas integrity_check_sql', () => {
  it('targets ga_dashas by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_dashas';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) §N\.3 accretion detector/)
    expect(migration).toMatch(/-- \(b\) §N\.5 upstream authority/)
    expect(migration).toMatch(/-- \(c\) MD-level \(level_n=1\) periods/)
    expect(migration).toMatch(/-- \(d\) range guard/)
  })

  it('checks house_d1 / sign / nakshatra as three INDEPENDENT conjuncts, not one OR-combined EXISTS', () => {
    // The mutation-caught defect this migration's header documents: combining all three fields
    // with OR inside one EXISTS lets a correct field mask a corrupted one. Each field's fact_key
    // must appear in its own dedicated NOT EXISTS block.
    const houseBlockCount = (migration.match(/fact_key = 'house_d1'/g) ?? []).length
    const signBlockCount = (migration.match(/fact_key = 'sign'/g) ?? []).length
    const nakshatraBlockCount = (migration.match(/fact_key = 'nakshatra'/g) ?? []).length
    expect(houseBlockCount).toBe(1)
    expect(signBlockCount).toBe(1)
    expect(nakshatraBlockCount).toBe(1)
    // Never a single EXISTS body containing all three OR'd together.
    expect(migration).not.toMatch(/fact_key = 'house_d1'[\s\S]{0,400}OR[\s\S]{0,200}fact_key = 'sign'/)
  })

  it('never asserts lord_natal_dignity_d1 / lord_natal_shadbala_total (the R-43/WP-1.8 exception)', () => {
    expect(migration).not.toMatch(/lord_natal_dignity_d1\s*(=|IS)/)
    expect(migration).not.toMatch(/lord_natal_shadbala_total\s*(=|IS)/)
    expect(migration).toMatch(/R-43\/WP-1\.8/)
  })

  it('scopes the MD-tiling conjunct to exclude mudda, and documents why', () => {
    expect(migration).toMatch(/system_id <> 'mudda'/)
    expect(migration).toMatch(/solar-return/)
    expect(migration).toMatch(/1996 leap-year boundary|1996 leap.year/)
  })

  it('names the true natural key including parent_row_id, and documents why it is required', () => {
    expect(migration).toMatch(
      /GROUP BY chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_date/,
    )
    expect(migration).toMatch(/hybrid storage/)
  })
})
