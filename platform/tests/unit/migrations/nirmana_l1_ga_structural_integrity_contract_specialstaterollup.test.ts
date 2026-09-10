import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_special_state_rollup widening pass
 * (migration 799, F-A14) — twentieth and LAST migration in the 780-799 range (adjudication
 * #2012; the continuation adjudication #2057 is open requesting the next block).
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
 * aspect_matrix_summary; migration 798 added the aspect_parashari_given/received bundle
 * (39/57). This adds graha_special_state_rollup, taking coverage to 40/57.
 *
 * Four of five boolean flags (is_combust, is_retrograde, is_debilitated, is_exalted) re-derive
 * cleanly against ga_positions' own graha_position category. The fifth, is_vargottama, is a NEW
 * FINDING — F-A18 — genuinely red: the writer's `_build_special_state_rows` still computes it
 * via the SAME buggy inline navamsha formula F-A15 already fixed in a DIFFERENT function
 * (`_build_shadbala_extension_rows`'s graha_vargottama_amplification_factor); this second call
 * site was never updated. Disagrees with ga_vargas' D9 authority on the exact same 4/105 rows
 * as F-A15's own tracked residual — confirmed the same underlying pre-fix computation,
 * duplicated into a still-unfixed second location. Landed honestly RED per the
 * never-weaken-a-gate doctrine, not suppressed or narrowed.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 799
 * carries the ninety prior conjuncts (a)-(h6) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus five new conjuncts (a7)-(e7), one of which (e7,
 * F-A18) is itself genuinely red. This textual test verifies the migration's SHAPE — read-only
 * and bind-parameter-free, all ninety-five conjuncts survive — not a live-DB re-run of the full
 * combined contract; the new conjuncts were verified live in isolation during authoring, each
 * individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/799_nirmana_l1_ga_structural_integrity_contract_specialstaterollup.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 799')
  }
  return migration.slice(start + 4, end)
}

describe('migration 799 — ga_structural integrity_check_sql (graha_special_state_rollup)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the ninety prior conjuncts (a)-(h6) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(g6\) given -> received bidirectional correspondence/,
      /-- \(h6\) received -> given bidirectional correspondence/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all five new conjuncts (a7)-(e7), documenting F-A18 as a new genuinely-red finding', () => {
    expect(migration).toMatch(/-- \(a7\) graha_special_state_rollup fact_value_text domain/)
    expect(migration).toMatch(/-- \(b7\) is_combust must equal/)
    expect(migration).toMatch(/-- \(c7\) is_retrograde must equal/)
    expect(migration).toMatch(/-- \(d7\) is_debilitated \/ is_exalted must equal/)
    expect(migration).toMatch(/-- \(e7\) F-A18, GENUINELY RED TODAY/)
    expect(migration).toMatch(/F-A18/)
  })

  it('documents F-A18 as a live unfixed writer bug, distinct from the stale-data F-A15\\/F-A17\\/F-157 residuals', () => {
    expect(migration).toMatch(/genuinely unfixed WRITER bug/)
    expect(migration).toMatch(/_build_special_state_rows/)
    expect(migration).toMatch(/_get_varga_vargottama_flag/)
  })

  it('re-derives is_vargottama against ga_vargas\' D9 authority, mirroring migration 792\'s conjunct (b)', () => {
    const detectorSql = extractDetectorSql()
    const e7Section = detectorSql.slice(detectorSql.indexOf('-- (e7)'))
    expect(e7Section).toContain("fact_category = 'varga_vargottama_flag'")
    expect(e7Section).toContain("v.varga = 'D9'")
    expect(e7Section).toContain('v.vargottama')
  })

  it('re-derives is_combust and is_retrograde from ga_positions\' own graha_position category', () => {
    const detectorSql = extractDetectorSql()
    const b7Section = detectorSql.slice(
      detectorSql.indexOf('-- (b7)'),
      detectorSql.indexOf('-- (d7)'),
    )
    expect(b7Section).toContain("fact_category = 'graha_position'")
    expect(b7Section).toContain("fact_key = 'combustion_state'")
    expect(b7Section).toContain("fact_key = 'retrograde_flag'")
  })
})
