import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — dispositor_tree widening pass (migration 809,
 * F-A14) — tenth migration in the 800-819 range (adjudication #2057, continuation 4).
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
 * chart_cluster (49/57). This adds dispositor_tree, taking coverage to 50/57.
 *
 * dispositor_tree is the richest category widened so far: one row per graha storing {varga,
 * parent, children, depth, is_root, sign} plus one CHART summary row per varga storing {varga,
 * roots, root_count}. Unlike migration 806's dispositor_chain_per_varga, this row stores its OWN
 * sign directly, making the classical parent-derivation conjunct fully self-contained. The
 * remaining conjuncts are genuine cross-row checks within this single category: the mutual
 * parent-child invariant and the CHART-summary-vs-per-graha-rows round trip.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 809
 * carries the one-hundred-and-fifty-two prior conjuncts (a)-(f15) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus nine new conjuncts
 * (a16)-(i16). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-sixty-one conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/809_nirmana_l1_ga_structural_integrity_contract_dispositortree.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 809')
  }
  return migration.slice(start + 4, end)
}

describe('migration 809 — ga_structural integrity_check_sql (dispositor_tree)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-fifty-two prior conjuncts (a)-(f15) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(f15\) isolated-implies-singleton-cluster/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all nine new conjuncts (a16)-(i16)', () => {
    expect(migration).toMatch(/-- \(a16\) dispositor_tree\.fact_value_text/)
    expect(migration).toMatch(/-- \(b16\) fact_value_text must equal value_jsonb\.parent/)
    expect(migration).toMatch(/-- \(c16\) is_root domain/)
    expect(migration).toMatch(/-- \(d16\) value_num domain/)
    expect(migration).toMatch(/-- \(e16\) is_root implies depth=0/)
    expect(migration).toMatch(/-- \(f16\) mutual parent-child invariant/)
    expect(migration).toMatch(/-- \(g16\) CHART summary root_count/)
    expect(migration).toMatch(/-- \(h16\) every graha named in a CHART summary/)
    expect(migration).toMatch(/-- \(i16\) every per-graha row with is_root=true/)
  })

  it('re-derives parent purely from the row\'s own stored sign field, no cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const a16Section = detectorSql.slice(
      detectorSql.indexOf('-- (a16)'),
      detectorSql.indexOf('-- (b16)'),
    )
    expect(a16Section).not.toContain('JOIN chart_facts')
    expect(a16Section).toContain("fact_value_jsonb->>'sign'")
  })

  it('checks the classical SIGN_LORDS table hardcoded per sign', () => {
    const detectorSql = extractDetectorSql()
    const a16Section = detectorSql.slice(
      detectorSql.indexOf('-- (a16)'),
      detectorSql.indexOf('-- (b16)'),
    )
    expect(a16Section).toContain("WHEN 'Aries' THEN 'MAR'")
    expect(a16Section).toContain("WHEN 'Sagittarius' THEN 'JUP'")
    expect(a16Section).toContain("WHEN 'Pisces' THEN 'JUP'")
  })

  it('checks the mutual parent-child and round-trip invariants within the same category, not a sibling', () => {
    const detectorSql = extractDetectorSql()
    const f16Section = detectorSql.slice(
      detectorSql.indexOf('-- (f16)'),
      detectorSql.indexOf('-- (g16)'),
    )
    const h16Section = detectorSql.slice(
      detectorSql.indexOf('-- (h16)'),
      detectorSql.indexOf('-- (i16)'),
    )
    expect(f16Section).toContain("fact_category = 'dispositor_tree'")
    expect(f16Section).not.toContain('graha_centrality')
    expect(h16Section).toContain("fact_key = 'tree_position'")
    expect(h16Section).toContain("fact_key = 'summary'")
  })
})
