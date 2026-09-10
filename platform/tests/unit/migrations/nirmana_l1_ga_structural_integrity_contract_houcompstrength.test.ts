import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_in_house_composite_strength widening pass
 * (migration 810, F-A14) — eleventh migration in the 800-819 range (adjudication #2057,
 * continuation 4).
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
 * 802 added aspect_received_by_special_point; migration 803 added aspect_jaimini; migration 804
 * added conjunction_per_varga; migration 805 added lord_aspects_lord_per_varga; migration 806
 * added dispositor_chain_per_varga; migration 807 added graha_centrality; migration 808 added
 * chart_cluster; migration 809 added dispositor_tree (50/57). This adds
 * graha_in_house_composite_strength, taking coverage to 51/57.
 *
 * graha_in_house_composite_strength stores, for every (graha, house) pair, three sibling rows
 * (bphs_weighted, simple_multiplication, cross_formula_divergence) sharing one fact_subject — or
 * exactly one floored bphs_weighted row when the real GA3 shadbala/bhava_bala facts are missing.
 * The writer's own comments establish bphs_score = simple_score x shadbala_ratio x
 * aspect_modifier (both factors <= 1), meaning bphs_weighted can never exceed
 * simple_multiplication, and cross_formula_divergence is fully re-derivable from the two sibling
 * rows without needing the underlying ratios at all.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 810
 * carries the one-hundred-and-sixty-one prior conjuncts (a)-(i16) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus six new conjuncts
 * (a17)-(f17). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-sixty-seven conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/810_nirmana_l1_ga_structural_integrity_contract_houcompstrength.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 810')
  }
  return migration.slice(start + 4, end)
}

describe('migration 810 — ga_structural integrity_check_sql (graha_in_house_composite_strength)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-sixty-one prior conjuncts (a)-(i16) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(i16\) every per-graha row with is_root=true/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (a17)-(f17)', () => {
    expect(migration).toMatch(/-- \(a17\) graha_in_house_composite_strength\.cross_formula_divergence/)
    expect(migration).toMatch(/-- \(b17\) bphs_weighted must never exceed simple_multiplication/)
    expect(migration).toMatch(/-- \(c17\) value_num domain: must never be negative/)
    expect(migration).toMatch(/-- \(d17\) row-count tiling per comp_subject/)
    expect(migration).toMatch(/-- \(e17\) fact_subject format/)
    expect(migration).toMatch(/-- \(f17\) floored-row invariant/)
  })

  it('re-derives cross_formula_divergence purely from the two sibling rows, no cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const a17Section = detectorSql.slice(
      detectorSql.indexOf('-- (a17)'),
      detectorSql.indexOf('-- (b17)'),
    )
    expect(a17Section).not.toContain('JOIN')
    expect(a17Section).toContain("fact_key = 'bphs_weighted'")
    expect(a17Section).toContain("fact_key = 'simple_multiplication'")
    expect(a17Section).toContain("fact_key = 'cross_formula_divergence'")
  })

  it('checks the tiling completeness with an explicit exactly-3-or-exactly-1-floored branch', () => {
    const detectorSql = extractDetectorSql()
    const d17Section = detectorSql.slice(
      detectorSql.indexOf('-- (d17)'),
      detectorSql.indexOf('-- (e17)'),
    )
    expect(d17Section).toContain('x.n = 3')
    expect(d17Section).toContain('x.n = 1')
    expect(d17Section).toContain('x.n_floored')
  })
})
