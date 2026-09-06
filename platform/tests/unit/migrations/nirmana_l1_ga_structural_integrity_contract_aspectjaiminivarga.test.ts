import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_jaimini_per_varga widening pass
 * (migration 816, F-A14) — seventeenth migration in the 800-819 range (adjudication #2057,
 * continuation 4).
 *
 * Migration 815 added karaka_bhava_concordance (56/64 by the corrected running tally) and
 * discovered F-A24 (a genuinely-red Aries-lagna-hardcode writer bug). This adds
 * aspect_jaimini_per_varga.
 *
 * aspect_jaimini_per_varga is the per-varga sibling of migration 803's aspect_jaimini — the SAME
 * pure 12-sign Jaimini Rasi drishti combinatorial rule with NO dependency on birth data, lagna,
 * or ayanamsha_id, just emitted identically for every one of the 29 vargas. Because the rule has
 * no Lagna dependency at all, this category is IMMUNE to the F-A24 class of bug — confirmed by
 * this migration's own conjuncts (0 violations across all 29 vargas), not merely assumed from
 * the absence of a Lagna reference in the writer's code.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 816
 * carries the two-hundred-and-five prior conjuncts (a)-(j22) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7)/(j22), already genuinely red (tracked: F-A15/F-A17/F-157/F-A18/
 * F-A24) — plus ten new conjuncts (a23)-(j23), each reusing migration 803's D1-only conjunct
 * shapes extended with a varga dimension. This textual test verifies the migration's SHAPE —
 * read-only and bind-parameter-free, all two-hundred-fifteen conjuncts survive — not a live-DB
 * re-run of the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/816_nirmana_l1_ga_structural_integrity_contract_aspectjaiminivarga.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 816')
  }
  return migration.slice(start + 4, end)
}

describe('migration 816 — ga_structural integrity_check_sql (aspect_jaimini_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the two-hundred-and-five prior conjuncts (a)-(j22) verbatim, including the still-red (b)/(e)/(f)/(e7)/(j22)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(j22\) F-A24, GENUINELY RED TODAY/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all ten new conjuncts (a23)-(j23)', () => {
    expect(migration).toMatch(/-- \(a23\) fact_value_num domain/)
    expect(migration).toMatch(/-- \(b23\) no self-aspect/)
    expect(migration).toMatch(/-- \(c23\) source_sign_type domain/)
    expect(migration).toMatch(/-- \(d23\) adjacency exclusion/)
    expect(migration).toMatch(/-- \(e23\) completeness/)
    expect(migration).toMatch(/-- \(f23\) exact count invariant/)
    expect(migration).toMatch(/-- \(g23\) symmetric mutual invariant/)
    expect(migration).toMatch(/-- \(h23\) fact_subject format/)
    expect(migration).toMatch(/-- \(i23\) fact_key format/)
    expect(migration).toMatch(/-- \(j23\) uncatalogued domain/)
  })

  it('documents this category as immune to F-A24 (no Lagna dependency), confirmed not assumed', () => {
    expect(migration).toMatch(/IMMUNE to\s*\n?-- the F-A24 class of bug/)
    expect(migration).toContain('confirmed, not assumed')
  })

  it('re-derives the classical zodiacal-order rule per varga, not a cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const d23Section = detectorSql.slice(
      detectorSql.indexOf('-- (d23)'),
      detectorSql.indexOf('-- (e23)'),
    )
    expect(d23Section).toContain('Aries')
    expect(d23Section).toContain("VALUES")
    expect(d23Section).not.toContain('graha_dignity_per_varga')
  })

  it("corrects the 'scoped to' header comment to list aspect_jaimini_per_varga", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('aspect_jaimini_per_varga')
    expect(scopedBlock).toContain('karaka_bhava_concordance')
  })
})
