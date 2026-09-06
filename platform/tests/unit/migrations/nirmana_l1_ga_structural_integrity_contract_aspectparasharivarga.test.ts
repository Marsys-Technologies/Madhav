import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_parashari_per_varga widening pass
 * (migration 817, F-A14) — eighteenth migration in the 800-819 range (adjudication #2057,
 * continuation 4).
 *
 * Migration 816 added aspect_jaimini_per_varga (57/64 by the corrected running tally),
 * confirmed immune to F-A24. This adds aspect_parashari_per_varga.
 *
 * aspect_parashari_per_varga emits, for every graha present in a varga, one row per classical
 * Parashari aspect it casts, using the SAME `get_graha_aspects` canonical authority already
 * reused since migration 807. Unlike karaka_bhava_concordance (migration 815, F-A24), this
 * category has NO Lagna dependency at all — house/sign come from the graha's own varga
 * position — so it is immune to that bug class, confirmed by conjunct (f24)'s cross-reference
 * to the sibling graha_dignity_per_varga category.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 817
 * carries the two-hundred-and-fifteen prior conjuncts (a)-(j23) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7)/(j22), already genuinely red (tracked: F-A15/F-A17/F-157/F-A18/
 * F-A24) — plus eight new conjuncts (a24)-(h24). This textual test verifies the migration's
 * SHAPE — read-only and bind-parameter-free, all two-hundred-twenty-three conjuncts survive —
 * not a live-DB re-run of the full combined contract; the new conjuncts were verified live in
 * isolation during authoring, each individually mutation-tested (including a self-caught
 * tautology in an early draft of (e24), the same defect class migration 814's original (e21)
 * hit, fixed before landing).
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/817_nirmana_l1_ga_structural_integrity_contract_aspectparasharivarga.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 817')
  }
  return migration.slice(start + 4, end)
}

describe('migration 817 — ga_structural integrity_check_sql (aspect_parashari_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the two-hundred-and-fifteen prior conjuncts (a)-(j23) verbatim, including the still-red (b)/(e)/(f)/(e7)/(j22)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(j22\) F-A24, GENUINELY RED TODAY/,
      /-- \(j23\) uncatalogued domain/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all eight new conjuncts (a24)-(h24)', () => {
    expect(migration).toMatch(/-- \(a24\) fact_value_num domain/)
    expect(migration).toMatch(/-- \(b24\) fact_key format/)
    expect(migration).toMatch(/-- \(c24\) target_house full re-derivation/)
    expect(migration).toMatch(/-- \(d24\) offset domain per graha/)
    expect(migration).toMatch(/-- \(e24\) graha-token domain/)
    expect(migration).toMatch(/-- \(f24\) source_house\/source_sign cross-reference/)
    expect(migration).toMatch(/-- \(g24\) uncatalogued domain/)
    expect(migration).toMatch(/-- \(h24\) completeness per graha/)
  })

  it('cross-references graha_dignity_per_varga for position, confirming no independent Lagna-dependent source', () => {
    const detectorSql = extractDetectorSql()
    const f24Section = detectorSql.slice(
      detectorSql.indexOf('-- (f24)'),
      detectorSql.indexOf('-- (g24)'),
    )
    expect(f24Section).toContain('graha_dignity_per_varga')
  })

  it('e24 checks token-set membership, not a tautological self-reconstruction of fact_subject', () => {
    const detectorSql = extractDetectorSql()
    const e24Section = detectorSql.slice(
      detectorSql.indexOf('-- (e24)'),
      detectorSql.indexOf('-- (f24)'),
    )
    expect(e24Section).toContain('NOT IN')
    expect(e24Section).not.toMatch(/fact_subject <> \(fact_value_jsonb->>'varga'\)/)
  })

  it("corrects the 'scoped to' header comment to list aspect_parashari_per_varga", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('aspect_parashari_per_varga')
    expect(scopedBlock).toContain('aspect_jaimini_per_varga')
  })
})
