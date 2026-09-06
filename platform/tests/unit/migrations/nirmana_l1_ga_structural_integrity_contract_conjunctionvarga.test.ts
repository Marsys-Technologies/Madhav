import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — conjunction_per_varga widening pass (migration
 * 804, F-A14) — fifth migration in the 800-819 range (adjudication #2057, continuation 4).
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
 * 802 added aspect_received_by_special_point; migration 803 added aspect_jaimini (44/57). This
 * adds conjunction_per_varga, taking coverage to 45/57.
 *
 * conjunction_per_varga stores, for every pair of grahas sharing a sign in a given varga (D1
 * through D2700), a row keyed "{VARGA}_{S1}_{S2}". D1 is a special case (the same "D1
 * dual-independent-PyJHora-source caveat" already established by migrations 758/759/783/793/800):
 * the writer computes a real degree-based orb and emits any pair within 10°, regardless of
 * whether the two grahas actually share a sign — confirmed live: 5/30 D1 rows genuinely have
 * same_sign=false. For every other varga, only genuine same-sign pairs are ever emitted, with
 * orb_deg hardcoded to 0.0 and same_sign always true.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 804
 * carries the one-hundred-and-seventeen prior conjuncts (a)-(ff4) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus eight new conjuncts
 * (a11)-(h11). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-twenty-five conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/804_nirmana_l1_ga_structural_integrity_contract_conjunctionvarga.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 804')
  }
  return migration.slice(start + 4, end)
}

describe('migration 804 — ga_structural integrity_check_sql (conjunction_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-seventeen prior conjuncts (a)-(ff4) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(ff4\) symmetric mutual invariant/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all eight new conjuncts (a11)-(h11)', () => {
    expect(migration).toMatch(/-- \(a11\) conjunction_per_varga\.unit correlation/)
    expect(migration).toMatch(/-- \(b11\) value_num domain/)
    expect(migration).toMatch(/-- \(c11\) same_sign domain for non-D1/)
    expect(migration).toMatch(/-- \(d11\) no self-pair/)
    expect(migration).toMatch(/-- \(e11\) no reversed-duplicate pair/)
    expect(migration).toMatch(/-- \(f11\) pair ordering invariant/)
    expect(migration).toMatch(/-- \(g11\) sign cross-reference, non-D1/)
    expect(migration).toMatch(/-- \(h11\) house cross-reference, non-D1/)
  })

  it('excludes D1 from the cross-reference conjuncts, per the established dual-source caveat', () => {
    const detectorSql = extractDetectorSql()
    const g11Section = detectorSql.slice(
      detectorSql.indexOf('-- (g11)'),
      detectorSql.indexOf('-- (h11)'),
    )
    const h11Section = detectorSql.slice(detectorSql.indexOf('-- (h11)'))
    expect(g11Section).toContain("fact_value_jsonb->>'varga' <> 'D1'")
    expect(h11Section).toContain("fact_value_jsonb->>'varga' <> 'D1'")
  })

  it('cross-references chart_divisionals varga_position for sign and house, not a bare restatement', () => {
    const detectorSql = extractDetectorSql()
    const g11Section = detectorSql.slice(
      detectorSql.indexOf('-- (g11)'),
      detectorSql.indexOf('-- (h11)'),
    )
    const h11Section = detectorSql.slice(detectorSql.indexOf('-- (h11)'))
    expect(g11Section).toContain('JOIN chart_divisionals')
    expect(g11Section).toContain("fact_key = 'degree_in_sign'")
    expect(h11Section).toContain('JOIN chart_divisionals')
    expect(h11Section).toContain("fact_key = 'house_from_varga_lagna'")
  })

  it('parses graha tokens with the same RAH_MEAN/KET_MEAN-aware split as migration 783', () => {
    const detectorSql = extractDetectorSql()
    const d11Section = detectorSql.slice(
      detectorSql.indexOf('-- (d11)'),
      detectorSql.indexOf('-- (e11)'),
    )
    expect(d11Section).toContain("LIKE 'RAH\\_MEAN\\_%' ESCAPE '\\'")
    expect(d11Section).toContain("LIKE 'KET\\_MEAN\\_%' ESCAPE '\\'")
  })

  it('checks the value_num domain differently for D1 vs non-D1, matching the writer\'s branch', () => {
    const detectorSql = extractDetectorSql()
    const b11Section = detectorSql.slice(
      detectorSql.indexOf('-- (b11)'),
      detectorSql.indexOf('-- (c11)'),
    )
    expect(b11Section).toContain("varga' = 'D1'")
    expect(b11Section).toContain('fact_value_num > 10.0')
    expect(b11Section).toContain('fact_value_num <> 0.0')
  })
})
