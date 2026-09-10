import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_effective_dignity_modified_by_aspects
 * widening pass (migration 793, F-A14) — fourteenth migration in the 780-799 range
 * (adjudication #2012).
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
 * graha_functional_class_per_ascendant (25/57). This adds
 * graha_effective_dignity_modified_by_aspects, taking coverage to 26/57.
 *
 * Unlike most recently-widened categories, graha_effective_dignity_modified_by_aspects is FULLY
 * SELF-CONTAINED: no cross-category join or external authority reference is needed at all. The
 * row's own value_jsonb stores {formula, base_dignity, contributions: [...]}, and fact_value_num
 * is a deterministic function purely of these already-stored fields.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 793
 * carries the sixty-four prior conjuncts (a)-(bb3) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus four new conjuncts (cc3)/(dd3)/(ee3)/(ff3).
 * This textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all
 * sixty-eight conjuncts survive — not a live-DB re-run of the full combined contract; conjuncts
 * (cc3)/(dd3)/(ee3)/(ff3) were verified live in isolation during authoring, each individually
 * mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/793_nirmana_l1_ga_structural_integrity_contract_effdignity.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 793')
  }
  return migration.slice(start + 4, end)
}

describe('migration 793 — ga_structural integrity_check_sql (graha_effective_dignity_modified_by_aspects)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the sixty-four prior conjuncts (a)-(bb3) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(zz2\) graha_functional_class_per_ascendant fact_value_text domain/,
      /-- \(bb3\) full re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all four new conjuncts (cc3)/(dd3)/(ee3)/(ff3)', () => {
    expect(migration).toMatch(
      /-- \(cc3\) graha_effective_dignity_modified_by_aspects\.effective_dignity_score domain/,
    )
    expect(migration).toMatch(/-- \(dd3\) value_jsonb\.base_dignity domain/)
    expect(migration).toMatch(/-- \(ee3\) full cross-field re-derivation/)
    expect(migration).toMatch(/-- \(ff3\) per-contribution delta re-derivation/)
  })

  it('documents the category as fully self-contained, needing no cross-category join', () => {
    expect(migration).toMatch(/FULLY SELF-CONTAINED/)
    expect(migration).toMatch(/no cross-category join or external authority reference/)
  })

  it('conjunct (ee3) sums contributions[].delta via jsonb_array_elements, not a restated total', () => {
    const detectorSql = extractDetectorSql()
    const ee3Section = detectorSql.slice(
      detectorSql.indexOf('-- (ee3)'),
      detectorSql.indexOf('-- (ff3)'),
    )
    expect(ee3Section).toContain("jsonb_array_elements(a.fact_value_jsonb->'contributions')")
    expect(ee3Section).toContain('delta_sum')
    expect(ee3Section).toContain('LEAST(GREATEST(')
  })

  it('conjunct (ff3) checks per-contribution delta against the benefic/malefic functional_class buckets', () => {
    const detectorSql = extractDetectorSql()
    const ff3Section = detectorSql.slice(detectorSql.indexOf('-- (ff3)'))
    expect(ff3Section).toContain(
      "('functional_benefic', 'yogakaraka', 'temporal_benefic')",
    )
    expect(ff3Section).toContain("('temporal_malefic', 'functional_malefic')")
    expect(ff3Section).toContain('0.25 *')
  })
})
