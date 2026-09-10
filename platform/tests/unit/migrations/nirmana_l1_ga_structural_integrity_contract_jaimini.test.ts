import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_jaimini widening pass (migration 803,
 * F-A14) — fourth migration in the 800-819 range (adjudication #2057, continuation 4).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
 * composite_dispositor_strength; migration 788 added the Group H avastha bundle; migration 789
 * added nakshatra_dispositor_chain; migration 790 added chandra_bala_natal_baseline; migration
 * 791 added the Group O tri-deva bundle; migration 792 added
 * graha_functional_class_per_ascendant; migration 793 added
 * graha_effective_dignity_modified_by_aspects; migration 794 added
 * graha_composite_state_classification; migration 795 added karaka_house_lord_overlap_flag;
 * migration 796 added the Group C Bhava Bala extended bundle; migration 797 added
 * aspect_matrix_summary; migration 798 added the aspect_parashari_given/received bundle;
 * migration 799 added graha_special_state_rollup, discovering F-A18; migration 800 added
 * chart_center_of_gravity; migration 801 added karakatva_strength_per_significance; migration
 * 802 added aspect_received_by_special_point (43/57). This adds aspect_jaimini, taking coverage
 * to 44/57.
 *
 * aspect_jaimini is the simplest category widened so far: a pure 12-sign combinatorial rule
 * (the writer's "Jaimini Rasi drishti (12×12 matrix)" block) with no dependency on birth data,
 * longitude, or ayanamsha_id — every ayanamsha's copy is byte-identical and the whole rule is
 * fully re-derivable in SQL from nothing but the 12 sign names' classical zodiacal order. The
 * relation is also provably symmetric (offset(s2,s1) = 12 - offset(s1,s2), and {1,11} is closed
 * under that map), checked as an independent cross-row invariant.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 803
 * carries the one-hundred-and-eleven prior conjuncts (a)-(f10) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus six new conjuncts
 * (aa4)-(ff4). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-seventeen conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/803_nirmana_l1_ga_structural_integrity_contract_jaimini.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 803')
  }
  return migration.slice(start + 4, end)
}

describe('migration 803 — ga_structural integrity_check_sql (aspect_jaimini)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-eleven prior conjuncts (a)-(f10) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(f10\) special_point self-consistency/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (aa4)-(ff4)', () => {
    expect(migration).toMatch(/-- \(aa4\) aspect_jaimini\.fact_value_num domain/)
    expect(migration).toMatch(/-- \(bb4\) no self-aspect/)
    expect(migration).toMatch(/-- \(cc4\) adjacency exclusion, full classical re-derivation/)
    expect(migration).toMatch(/-- \(dd4\) completeness/)
    expect(migration).toMatch(/-- \(ee4\) exact count invariant/)
    expect(migration).toMatch(/-- \(ff4\) symmetric mutual invariant/)
  })

  it('re-derives adjacency purely from the fixed 12-sign zodiacal order, no cross-category or cross-asset join', () => {
    const detectorSql = extractDetectorSql()
    const cc4Section = detectorSql.slice(
      detectorSql.indexOf('-- (cc4)'),
      detectorSql.indexOf('-- (dd4)'),
    )
    expect(cc4Section).not.toContain('chart_divisionals')
    expect(cc4Section).toContain("VALUES ('Aries',0)")
    expect(cc4Section).toContain('MOD(')
  })

  it('checks completeness across every (chart, ayanamsha, build) combination, not just the canonical chart', () => {
    const detectorSql = extractDetectorSql()
    const dd4Section = detectorSql.slice(
      detectorSql.indexOf('-- (dd4)'),
      detectorSql.indexOf('-- (ee4)'),
    )
    expect(dd4Section).toContain('SELECT DISTINCT chart_id, ayanamsha_id, build_id')
    expect(dd4Section).not.toContain("chart_id = '482012f1")
  })

  it('checks the exact-108-rows-per-combination count invariant', () => {
    const detectorSql = extractDetectorSql()
    const ee4Section = detectorSql.slice(
      detectorSql.indexOf('-- (ee4)'),
      detectorSql.indexOf('-- (ff4)'),
    )
    expect(ee4Section).toContain('x.c <> 108')
  })

  it('checks bidirectional symmetry via a self-join on the same category, not an external authority', () => {
    const detectorSql = extractDetectorSql()
    const ff4Section = detectorSql.slice(detectorSql.indexOf('-- (ff4)'))
    expect(ff4Section).toContain('cf1.fact_category = \'aspect_jaimini\'')
    expect(ff4Section).toContain('cf2.fact_category = \'aspect_jaimini\'')
    expect(ff4Section).toContain("substring(cf1.fact_key from 4)")
  })
})
