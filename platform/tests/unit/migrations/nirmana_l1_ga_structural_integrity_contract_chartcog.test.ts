import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — chart_center_of_gravity widening pass
 * (migration 800, F-A14) — FIRST migration in the new 800-819 range (adjudication #2057,
 * continuation 4, granted after the 780-799 range was fully exhausted by migration 799).
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
 * migration 799 added graha_special_state_rollup, discovering F-A18 (40/57). This adds
 * chart_center_of_gravity, taking coverage to 41/57.
 *
 * chart_center_of_gravity is a per-varga, chart-level rollup (29 vargas per chart) — a full
 * re-derivation would require a 13-hop recursive dispositor-chain walk per graha per varga in
 * SQL. Per the established "don't always need to re-derive the full source algorithm"
 * precedent, this migration ships strong internal cross-field consistency conjuncts instead,
 * verified against ALL 435 live rows (not a sample).
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 800
 * carries the ninety-five prior conjuncts (a)-(e7) forward verbatim — including conjuncts (b)/
 * (e)/(f)/(e7), already genuinely red (tracked) — plus six new conjuncts (a8)-(f8). This
 * textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all
 * one-hundred-one conjuncts survive — not a live-DB re-run of the full combined contract; the
 * new conjuncts were verified live in isolation during authoring, each individually
 * mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/800_nirmana_l1_ga_structural_integrity_contract_chartcog.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 800')
  }
  return migration.slice(start + 4, end)
}

describe('migration 800 — ga_structural integrity_check_sql (chart_center_of_gravity)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the ninety-five prior conjuncts (a)-(e7) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (a8)-(f8)', () => {
    expect(migration).toMatch(/-- \(a8\) chart_center_of_gravity\.final_dispositor fact_value_text domain/)
    expect(migration).toMatch(/-- \(b8\) cluster_count \/ final_dispositor's own fact_value_num/)
    expect(migration).toMatch(/-- \(c8\) cluster_count self-consistency/)
    expect(migration).toMatch(/-- \(d8\) final_dispositor cross-field consistency/)
    expect(migration).toMatch(/-- \(e8\) final_dispositor genuine-argmax invariant/)
    expect(migration).toMatch(/-- \(f8\) tally-sum invariant/)
  })

  it('re-derives cluster_count from the tally JSON keys rather than restating it', () => {
    const detectorSql = extractDetectorSql()
    const c8Section = detectorSql.slice(
      detectorSql.indexOf('-- (c8)'),
      detectorSql.indexOf('-- (d8)'),
    )
    expect(c8Section).toContain("jsonb_object_keys(f.fact_value_jsonb->'tally')")
  })

  it('checks the genuine-argmax property via cross-entry comparison, not a bare restatement', () => {
    const detectorSql = extractDetectorSql()
    const e8Section = detectorSql.slice(
      detectorSql.indexOf('-- (e8)'),
      detectorSql.indexOf('-- (f8)'),
    )
    expect(e8Section).toContain('jsonb_each_text')
    expect(e8Section).toContain('t.v::numeric > a.fact_value_num')
  })

  it('checks the tally-sum invariant equals exactly 9 (all ALL_GRAHAS members)', () => {
    const detectorSql = extractDetectorSql()
    const f8Section = detectorSql.slice(detectorSql.indexOf('-- (f8)'))
    expect(f8Section).toContain('x.total <> 9')
  })
})
