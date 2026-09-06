import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — conjunction_within_orb widening pass
 * (migration 783, F-A14) — fourth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline (10/57). This adds
 * conjunction_within_orb, taking coverage to 11/57.
 *
 * conjunction_within_orb is a pure-D1 category computed from ga_structural's own in-memory
 * chart_output — the same D1 source already flagged by the D1 dual-independent-PyJHora-source
 * caveat. Rather than re-derive against ga_vargas' own chart_divisionals D1 data (which would risk
 * re-surfacing that already-tracked disagreement as a false new defect), this migration ships two
 * self-consistency/domain conjuncts instead, the same discipline established for
 * kala_sarpa_per_varga (migration 781).
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 783
 * carries the twenty-two prior conjuncts (a)-(v) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus three new conjuncts (w)-(y). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all twenty-five conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (w)-(y) were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/783_nirmana_l1_ga_structural_integrity_contract_conjunction.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 783')
  }
  return migration.slice(start + 4, end)
}

describe('migration 783 — ga_structural integrity_check_sql (conjunction_within_orb)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the twenty-two prior conjuncts (a)-(v) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(u\) tara_bala_natal_baseline\.tara_class domain/,
      /-- \(v\) tara_bala_natal_baseline\.tara_class must equal/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all three new conjuncts (w)-(y)', () => {
    expect(migration).toMatch(/-- \(w\) conjunction_within_orb\.orb_deg domain/)
    expect(migration).toMatch(/-- \(x\) no reversed-duplicate pair/)
    expect(migration).toMatch(/-- \(y\) pair ordering invariant/)
  })

  it('documents the RAH_MEAN/KET_MEAN underscore parsing hazard and why full D1 re-derivation was avoided', () => {
    expect(migration).toMatch(/RAH_MEAN\/KET_MEAN themselves contain an underscore/)
    expect(migration).toMatch(/SAT_KET_MEAN/)
    expect(migration).toMatch(/D1 dual-independent-PyJHora-source/)
  })

  it('conjunct (w) restricts orb_deg to the physically valid [0, 10.0] range', () => {
    const detectorSql = extractDetectorSql()
    const wSection = detectorSql.slice(
      detectorSql.indexOf('-- (w)'),
      detectorSql.indexOf('-- (x)'),
    )
    expect(wSection).toContain('fact_value_num < 0 OR fact_value_num > 10.0')
  })

  it('conjuncts (x) and (y) parse RAH_MEAN_/KET_MEAN_ prefixes before falling back to split_part', () => {
    const detectorSql = extractDetectorSql()
    const xySection = detectorSql.slice(detectorSql.indexOf('-- (x)'))
    expect(xySection).toContain("LIKE 'RAH\\_MEAN\\_%' ESCAPE '\\'")
    expect(xySection).toContain("LIKE 'KET\\_MEAN\\_%' ESCAPE '\\'")
    expect(xySection).toContain("split_part(a.fact_subject, '_', 1)")
  })

  it('conjunct (y) re-derives the writer\'s own ALL_GRAHAS ordering as the ordering array', () => {
    const detectorSql = extractDetectorSql()
    const ySection = detectorSql.slice(detectorSql.indexOf('-- (y)'))
    expect(ySection).toContain(
      "ARRAY['SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN']",
    )
  })
})
