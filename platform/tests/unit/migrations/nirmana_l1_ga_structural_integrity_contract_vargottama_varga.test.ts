import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — vargottama_per_varga widening pass (migration
 * 756, F-A14). Discovers F-A17, a new genuine §N.5-adjacent defect.
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag (3/57). This adds vargottama_per_varga, taking coverage to 4/57.
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 756
 * carries the four prior conjuncts (a)-(d) forward verbatim — including conjunct (b), already
 * genuinely red (tracked since migration 745) — plus one new conjunct (e), which is ALSO
 * genuinely red today (F-A17: 13/3780 rows where ga_structural's re-derived vargottama boolean
 * disagrees with ga_vargas' own precomputed varga_vargottama_flag, now confirmed to exist for
 * every varga, not just D9). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all five conjuncts survive — not a live-DB re-run of the full combined
 * contract (which cannot currently read true because of conjuncts (b) and (e)); conjunct (e) was
 * verified live in isolation during authoring, including a synthetic post-fix overlay proving it
 * clears cleanly once the 13 disagreeing rows are corrected.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/756_nirmana_l1_ga_structural_integrity_contract_vargottama_varga.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 756')
  }
  return migration.slice(start + 4, end)
}

describe('migration 756 — ga_structural integrity_check_sql (vargottama_per_varga, F-A17)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the four prior conjuncts (a)-(d) verbatim, including the still-red (b)', () => {
    expect(migration).toMatch(/-- \(a\) amplification_factor domain/)
    expect(migration).toMatch(/-- \(b\) F-A15: amplification_factor must agree/)
    expect(migration).toMatch(/STILL GENUINELY RED TODAY on 4\/105 rows/)
    expect(migration).toMatch(/-- \(c\) bhadra_flag\.active_at_birth_flag must agree exactly/)
    expect(migration).toMatch(/-- \(d\) panchaka_flag\.active_at_birth_flag must equal/)
  })

  it('carries the new conjunct (e) and documents F-A17 as a known-red finding, not a silently-narrowed check', () => {
    expect(migration).toMatch(/-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/)
    expect(migration).toMatch(/GENUINELY RED TODAY on 13\/3780 rows/)
    expect(migration).toMatch(/no plurality\s*\n?\s*-- violation on either side/)
  })

  it("conjunct (e) cross-checks against ga_vargas' varga_vargottama_flag for EVERY varga, not hardcoded to D9", () => {
    const detectorSql = extractDetectorSql()
    const eSection = detectorSql.slice(
      detectorSql.indexOf('-- (e)'),
      detectorSql.indexOf('AS integrity_passed'),
    )
    expect(eSection).toContain("v.fact_category = 'varga_vargottama_flag'")
    expect(eSection).not.toContain("v.varga = 'D9'")
    expect(eSection).toContain("v.varga = split_part(a.fact_subject, '_', 1)")
  })

  it('conjunct (e) maps all 9 classical-graha subject codes including the mean-node suffix, not a partial CASE', () => {
    const detectorSql = extractDetectorSql()
    const eSection = detectorSql.slice(
      detectorSql.indexOf('-- (e)'),
      detectorSql.indexOf('AS integrity_passed'),
    )
    for (const code of ['SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN']) {
      expect(eSection).toContain(`'${code}'`)
    }
  })
})
