import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — argala_natal_matrix widening pass (migration
 * 840, F-A14) — first migration in the NEW 840-859 range (L1 continuation 5, granted by the
 * Conductor's ruling on #2101 -- the requested 820-839 was already granted to L5 by #2086).
 *
 * Migration 819 added sambandha_grade (60/64 by the corrected running tally), the last migration
 * the exhausted 800-819 range could hold. This adds argala_natal_matrix.
 *
 * argala_natal_matrix is a full 12x12 sign-to-sign matrix per varga (144 atomic rows): for every
 * (target_sign, source_sign) pair, an argala score is stored, derived from the classical offset
 * and any natural-malefic occupants of the source sign. Occupancy is cross-referenced from the
 * sibling graha_dignity_per_varga category rather than freshly computed -- no Lagna dependency
 * at all, one of the few remaining categories immune to the F-A24/F-A25 bug class by
 * construction.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 840
 * carries the two-hundred-and-forty-one prior conjuncts (a)-(i26) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7)/(j22)/(i25), already genuinely red (tracked: F-A15/F-A17/F-157/
 * F-A18/F-A24/F-A25) — plus seven new conjuncts (a27)/(b27)/(c27)/(e27)/(f27)/(g27)/(h27). This
 * textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all
 * two-hundred-forty-eight conjuncts survive — not a live-DB re-run of the full combined contract;
 * the new conjuncts were verified live in isolation during authoring, each individually
 * mutation-tested, including a self-caught SQL modulo-sign hazard (D-L1-102) in an early draft
 * of (c27), fixed before landing.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/840_nirmana_l1_ga_structural_integrity_contract_argalanatalmatrix.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 840')
  }
  return migration.slice(start + 4, end)
}

describe('migration 840 — ga_structural integrity_check_sql (argala_natal_matrix)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the two-hundred-and-forty-one prior conjuncts (a)-(i26) verbatim, including the still-red (b)/(e)/(f)/(e7)/(j22)/(i25)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(j22\) F-A24, GENUINELY RED TODAY/,
      /-- \(i25\) F-A25, GENUINELY RED TODAY/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new conjuncts (a27)/(b27)/(c27)/(e27)/(f27)/(g27)/(h27)', () => {
    expect(migration).toMatch(/-- \(a27\) non-argala-offset domain/)
    expect(migration).toMatch(/-- \(b27\) fact_key format/)
    expect(migration).toMatch(/-- \(c27\) offset full re-derivation/)
    expect(migration).toMatch(/-- \(e27\) argala-offset full re-derivation/)
    expect(migration).toMatch(/-- \(f27\) fact_subject format/)
    expect(migration).toMatch(/-- \(g27\) target\/source sign_num domain/)
    expect(migration).toMatch(/-- \(h27\) exact count invariant/)
  })

  it('re-derives malefic occupancy from graha_dignity_per_varga, not a fresh occupancy computation', () => {
    const detectorSql = extractDetectorSql()
    const e27Section = detectorSql.slice(
      detectorSql.indexOf('-- (e27)'),
      detectorSql.indexOf('-- (f27)'),
    )
    expect(e27Section).toContain('graha_dignity_per_varga')
    expect(e27Section).toContain('RAH_MEAN')
  })

  it('uses safe-wraparound modulo arithmetic in (c27), avoiding the D-L1-102 sign hazard', () => {
    const detectorSql = extractDetectorSql()
    const c27Section = detectorSql.slice(
      detectorSql.indexOf('-- (c27)'),
      detectorSql.indexOf('-- (e27)'),
    )
    expect(c27Section).toContain('+ 120, 12')
  })

  it('documents this as the first migration in the new 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })

  it("corrects the 'scoped to' header comment to list argala_natal_matrix", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('argala_natal_matrix')
    expect(scopedBlock).toContain('sambandha_grade')
  })
})
