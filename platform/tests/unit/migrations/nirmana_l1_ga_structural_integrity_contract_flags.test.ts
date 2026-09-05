import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — flags widening pass (migration 755, F-A14).
 *
 * Migration 745 (cycle 34) covered graha_vargottama_amplification_factor — 1/57 of
 * ga_structural's owned categories. This adds bhadra_flag and panchaka_flag (both physically
 * emitted by ga_panchanga_writer.py but OWNED by ga_structural per fact_category_ownership),
 * taking coverage to 3/57. integrity_check_sql is a single UPDATE ... SET column, not additive
 * SQL, so migration 755 carries migration 745's two original conjuncts (a)/(b) forward verbatim
 * — including conjunct (b), which remains genuinely red today (tracked, expected, per F-A15's
 * cycle-42 fix not yet having propagated to the 2 affected charts' stored rows). This textual
 * test verifies the migration's SHAPE — read-only and bind-parameter-free, all four conjuncts
 * survive — not a live-DB re-run of the full combined contract (which cannot currently read true
 * because of conjunct (b)); the two NEW conjuncts (c)/(d) were verified INDIVIDUALLY, in
 * isolation, live against production during authoring, each returning true alone.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/755_nirmana_l1_ga_structural_integrity_contract_flags.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 755')
  }
  return migration.slice(start + 4, end)
}

describe('migration 755 — ga_structural integrity_check_sql (flags widening)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it("carries migration 745's two original conjuncts (a)/(b) verbatim, including the still-red (b)", () => {
    expect(migration).toMatch(/-- \(a\) amplification_factor domain/)
    expect(migration).toMatch(/-- \(b\) F-A15: amplification_factor must agree/)
    expect(migration).toMatch(/STILL GENUINELY RED TODAY on 4\/105 rows/)
  })

  it('carries both new conjuncts (c)/(d)', () => {
    expect(migration).toMatch(/-- \(c\) bhadra_flag\.active_at_birth_flag must agree exactly/)
    expect(migration).toMatch(/-- \(d\) panchaka_flag\.active_at_birth_flag must equal/)
  })

  it('documents why eclipse_proximity_natal was deliberately NOT attempted (honest B.10 floor)', () => {
    expect(migration).toMatch(/EXTERNAL_COMPUTATION_REQUIRED placeholder/)
    expect(migration).toMatch(/absence-of-check, not a red or green one/)
  })

  it('conjunct (c) cross-checks bhadra_flag against panchanga_karana by chart_id alone (ayanamsha-invariant), not per-ayanamsha', () => {
    const detectorSql = extractDetectorSql()
    const cSection = detectorSql.slice(
      detectorSql.indexOf('-- (c)'),
      detectorSql.indexOf('-- (d)'),
    )
    expect(cSection).toContain("k.chart_id = b.chart_id")
    expect(cSection).not.toContain('k.ayanamsha_id = b.ayanamsha_id')
    expect(cSection).toContain("k.fact_category = 'panchanga_karana'")
    expect(cSection).toContain("k.fact_key = 'vishti_bhadra_flag'")
  })

  it('conjunct (d) re-derives panchaka_flag from the stored nakshatra number, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    const dSection = detectorSql.slice(detectorSql.indexOf('-- (d)'), detectorSql.indexOf('AS integrity_passed'))
    expect(dSection).toContain("n.fact_category = 'panchanga_nakshatra_moon'")
    expect(dSection).toContain('ARRAY[23,24,25,26,27]')
  })
})
