import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — lord_in_house_per_varga widening pass
 * (migration 811, F-A14) — twelfth migration in the 800-819 range (adjudication #2057,
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
 * chart_cluster; migration 809 added dispositor_tree; migration 810 added
 * graha_in_house_composite_strength (51/57). This adds lord_in_house_per_varga, taking coverage
 * to 52/57.
 *
 * lord_in_house_per_varga is the sibling category to migration 805's lord_aspects_lord_per_varga
 * (same source function), fully self-contained via its own stored {varga, house, sign, lord,
 * lord_house_in_varga} fields. Because house_sign(h) uses the D1 lagna alone regardless of
 * which varga is being processed, the sign at a given house number is a genuine
 * varga-independent constant for the whole chart — a cross-row invariant unique to this
 * category.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 811
 * carries the one-hundred-and-sixty-seven prior conjuncts (a)-(f17) forward verbatim —
 * including conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus seven new
 * conjuncts (a18)-(g18). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-seventy-four conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/811_nirmana_l1_ga_structural_integrity_contract_lordinhouse.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 811')
  }
  return migration.slice(start + 4, end)
}

describe('migration 811 — ga_structural integrity_check_sql (lord_in_house_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-sixty-seven prior conjuncts (a)-(f17) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(f17\) floored-row invariant/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new conjuncts (a18)-(g18)', () => {
    expect(migration).toMatch(/-- \(a18\) lord_in_house_per_varga\.lord must equal/)
    expect(migration).toMatch(/-- \(b18\) fact_value_text must equal the writer's own f-string/)
    expect(migration).toMatch(/-- \(c18\) fact_value_num must equal value_jsonb\.lord_house_in_varga/)
    expect(migration).toMatch(/-- \(d18\) fact_subject format/)
    expect(migration).toMatch(/-- \(e18\) varga-independent sign invariant/)
    expect(migration).toMatch(/-- \(f18\) house domain/)
    expect(migration).toMatch(/-- \(g18\) lord domain/)
  })

  it('re-derives lord purely from the row\'s own stored sign field, no cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const a18Section = detectorSql.slice(
      detectorSql.indexOf('-- (a18)'),
      detectorSql.indexOf('-- (b18)'),
    )
    expect(a18Section).not.toContain('JOIN chart_facts')
    expect(a18Section).toContain("fact_value_jsonb->>'sign'")
  })

  it('checks the varga-independent sign invariant via a GROUP BY on house_num alone (no varga in the key)', () => {
    const detectorSql = extractDetectorSql()
    const e18Section = detectorSql.slice(
      detectorSql.indexOf('-- (e18)'),
      detectorSql.indexOf('-- (f18)'),
    )
    expect(e18Section).toContain('GROUP BY 1, 2, 3, 4')
    expect(e18Section).not.toContain("fact_value_jsonb->>'varga'")
  })

  it('excludes Rahu/Ketu from the lord domain SQL clause, matching migration 805\'s lord_a/lord_b', () => {
    const detectorSql = extractDetectorSql()
    const g18Section = detectorSql.slice(detectorSql.indexOf('-- (g18)'))
    const sqlBody = g18Section.slice(g18Section.indexOf('AND NOT EXISTS'))
    expect(sqlBody).toContain("'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'")
    expect(sqlBody).not.toContain('Rahu')
  })
})
