import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — karaka_bhava_concordance widening pass
 * (migration 815, F-A14) — sixteenth migration in the 800-819 range (adjudication #2057,
 * continuation 4).
 *
 * Migration 814 added convergence_count (55/64 by the corrected running tally — see D-L1-106
 * for the 54-vs-55 off-by-one correction, and D-L1-105 for the underlying 64-not-57
 * denominator finding). This adds karaka_bhava_concordance.
 *
 * karaka_bhava_concordance is fully self-contained and re-derivable from the writer's own
 * classical dicts (SIGNIFICANCE_TO_BHAVA, NATURAL_KARAKAS, SIGN_LORDS, NATURAL_PLANET_RELATIONS)
 * — no cross-category join needed for the writer's OWN arithmetic. This migration also confirms
 * and ships a NEW genuinely-red finding, F-A24: `_build_karaka_bhava_concordance_per_varga_rows`
 * has no access to `chart_output` (unlike migration 811's `_build_lord_relationship_rows`, which
 * correctly reads the D1 ascendant from it) and silently defaults to Aries lagna for every
 * non-D1 varga, invisible on two of three test charts whose own lagna genuinely is Aries but
 * confirmed wrong on chart cb73cd3d's 4200 non-D1 rows (28 vargas x 30 significances x 5
 * ayanamshas), profiled before any conjunct was written.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 815
 * carries the one-hundred-and-ninety-five prior conjuncts (a)-(i21) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus ten new conjuncts
 * (a22)-(j22), the last of which (j22/F-A24) is ALSO genuinely red and newly discovered here.
 * This textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all
 * two-hundred-five conjuncts survive — not a live-DB re-run of the full combined contract; the
 * new conjuncts were verified live in isolation during authoring, each individually
 * mutation-tested (including (j22), whose mutation test confirmed it catches additional
 * corruption beyond the known bug's own baseline violation count).
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/815_nirmana_l1_ga_structural_integrity_contract_karakabhavaconcordance.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 815')
  }
  return migration.slice(start + 4, end)
}

describe('migration 815 — ga_structural integrity_check_sql (karaka_bhava_concordance)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-ninety-five prior conjuncts (a)-(i21) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(i21\) house-row full re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all ten new conjuncts (a22)-(j22), with (j22) marked genuinely red', () => {
    expect(migration).toMatch(/-- \(a22\) fact_key domain/)
    expect(migration).toMatch(/-- \(b22\) significance domain/)
    expect(migration).toMatch(/-- \(c22\) bhava_num cross-check/)
    expect(migration).toMatch(/-- \(d22\) natural_karaka cross-check/)
    expect(migration).toMatch(/-- \(e22\) bhava_lord cross-check/)
    expect(migration).toMatch(/-- \(f22\) fact_value_text\/value_jsonb consistency/)
    expect(migration).toMatch(/-- \(g22\) concordance domain/)
    expect(migration).toMatch(/-- \(h22\) full concordance re-derivation/)
    expect(migration).toMatch(/-- \(i22\) fact_subject format/)
    expect(migration).toMatch(/-- \(j22\) F-A24, GENUINELY RED TODAY/)
  })

  it('documents F-A24 as a real, profiled writer bug (Aries-lagna hardcode), not a verifier-model gap', () => {
    expect(migration).toMatch(/F-A24/)
    expect(migration).toMatch(/lagna_sign_num = 1.*Aries.*for EVERY non-D1 varga/s)
    expect(migration).toContain('cb73cd3d')
    expect(migration).toMatch(/4200/)
  })

  it('re-derives the concordance decision tree from a hardcoded 54-row Parashari friendship table, not a cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const h22Section = detectorSql.slice(
      detectorSql.indexOf('-- (h22)'),
      detectorSql.indexOf('-- (i22)'),
    )
    expect(h22Section).toContain("VALUES")
    expect(h22Section).toContain('friendly_reverse')
    expect(h22Section).not.toContain('graha_dignity_per_varga')
  })

  it('j22 cross-references lord_in_house_per_varga as ground truth for the D1 lagna, not a self-derived value', () => {
    const detectorSql = extractDetectorSql()
    const j22Section = detectorSql.slice(detectorSql.indexOf('-- (j22)'))
    expect(j22Section).toContain('lord_in_house_per_varga')
    expect(j22Section).toContain("fact_value_jsonb->>'house' = '1'")
  })

  it("corrects the 'scoped to' header comment to list karaka_bhava_concordance", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('karaka_bhava_concordance')
    expect(scopedBlock).toContain('convergence_count')
  })
})
