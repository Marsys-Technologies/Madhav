import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — sambandha_grade widening pass (migration 819,
 * F-A14) — twentieth and LAST migration in the 800-819 range (adjudication #2057, continuation
 * 4) -- 819 is the final free number; a fresh range grant is needed before F-A14 can widen
 * further.
 *
 * Migration 818 added bhava_significance_link (59/64 by the corrected running tally),
 * discovering F-A25. This adds sambandha_grade.
 *
 * sambandha_grade computes a 4-fold planet-pair relationship grade per varga: a real
 * degree-based conjunction score, a mutual Parashari aspect score, a parivartana score, and a
 * mutual-reception score, averaged to one grade. Unlike every other category widened so far, the
 * conjunction component genuinely needs actual ecliptic degree data that no already-shipped
 * sibling category stores for non-D1 vargas. Rather than fabricate a degree-based re-derivation
 * this migration cannot honestly perform for 28 of 29 vargas, it ships strong domain/format/
 * self-consistency conjuncts for all rows, plus a genuine partial cross-reference for D1 against
 * migration 783's own conjunction_within_orb category, which stores the real orb_deg for every
 * D1 graha pair -- the same "don't always need to re-derive the full source algorithm"
 * precedent migration 800 established.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 819
 * carries the two-hundred-and-thirty-two prior conjuncts (a)-(i25) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7)/(j22)/(i25), already genuinely red (tracked: F-A15/F-A17/F-157/
 * F-A18/F-A24/F-A25) — plus nine new conjuncts (a26)-(i26). This textual test verifies the
 * migration's SHAPE — read-only and bind-parameter-free, all two-hundred-forty-one conjuncts
 * survive — not a live-DB re-run of the full combined contract; the new conjuncts were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/819_nirmana_l1_ga_structural_integrity_contract_sambandhagrade.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 819')
  }
  return migration.slice(start + 4, end)
}

describe('migration 819 — ga_structural integrity_check_sql (sambandha_grade)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the two-hundred-and-thirty-two prior conjuncts (a)-(i25) verbatim, including the still-red (b)/(e)/(f)/(e7)/(j22)/(i25)', () => {
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

  it('carries all nine new conjuncts (a26)-(i26)', () => {
    expect(migration).toMatch(/-- \(a26\) fact_key domain/)
    expect(migration).toMatch(/-- \(b26\) value_num domain/)
    expect(migration).toMatch(/-- \(c26\) grade formula self-consistency/)
    expect(migration).toMatch(/-- \(d26\) conjunction_score domain/)
    expect(migration).toMatch(/-- \(e26\) mutual_aspect_score domain/)
    expect(migration).toMatch(/-- \(f26\) exchange_score domain/)
    expect(migration).toMatch(/-- \(g26\) reception_score domain/)
    expect(migration).toMatch(/-- \(h26\) fact_subject varga-prefix consistency/)
    expect(migration).toMatch(/-- \(i26\) D1-only conjunction_score cross-reference/)
  })

  it('cross-references conjunction_within_orb for D1 ground truth rather than fabricating a full degree-based re-derivation', () => {
    const detectorSql = extractDetectorSql()
    const i26Section = detectorSql.slice(detectorSql.indexOf('-- (i26)'))
    expect(i26Section).toContain('conjunction_within_orb')
    expect(i26Section).toContain("varga' = 'D1'")
  })

  it("documents this as the last migration in the 800-819 range, requiring a fresh grant to continue", () => {
    expect(migration).toMatch(/LAST migration this range can hold/)
    expect(migration).toContain('819 is the final free number')
  })

  it("corrects the 'scoped to' header comment to list sambandha_grade", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('sambandha_grade')
    expect(scopedBlock).toContain('bhava_significance_link')
  })
})
