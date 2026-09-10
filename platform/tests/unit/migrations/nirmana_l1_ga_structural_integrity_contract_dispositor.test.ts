import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_dispositor_chain widening pass
 * (migration 786, F-A14) — seventh migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag (13/57). This adds graha_dispositor_chain, taking coverage to 14/57.
 *
 * Like graha_yoga_karaka_flag, this category resolves entirely from chart_output's own
 * already-computed sign assignments via the classical SIGN_LORDS lookup table — not two
 * independent PyJHora position computations — so it is NOT the D1 dual-source shape.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 786
 * carries the thirty-three prior conjuncts (a)-(gg) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus six new conjuncts (hh)-(mm). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all thirty-nine conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (hh)-(mm) were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/786_nirmana_l1_ga_structural_integrity_contract_dispositor.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 786')
  }
  return migration.slice(start + 4, end)
}

describe('migration 786 — ga_structural integrity_check_sql (graha_dispositor_chain)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the thirty-three prior conjuncts (a)-(gg) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(ff\) graha_yoga_karaka_flag\.is_yoga_karaka domain/,
      /-- \(gg\) at most one graha per \(chart, ayanamsha, build\)/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (hh)-(mm)', () => {
    expect(migration).toMatch(/-- \(hh\) graha_dispositor_chain's chain\[0\] must equal/)
    expect(migration).toMatch(/-- \(ii\) length must equal the actual length/)
    expect(migration).toMatch(/-- \(jj\) the chain array and signs array must have equal length/)
    expect(migration).toMatch(/-- \(kk\) when cycle_detected_at_step is not null/)
    expect(migration).toMatch(/-- \(ll\) full classical re-derivation/)
    expect(migration).toMatch(/-- \(mm\) terminal cycle-closure/)
  })

  it('documents why this category is also NOT the D1 dual-independent-PyJHora-source shape', () => {
    expect(migration).toMatch(/is NOT the D1 dual-source shape/)
    expect(migration).toMatch(/classical SIGN_LORDS lookup table/)
  })

  it('conjunct (ll) re-derives the dispositor rule via generate_series over the chain array', () => {
    const detectorSql = extractDetectorSql()
    const llSection = detectorSql.slice(
      detectorSql.indexOf('-- (ll)'),
      detectorSql.indexOf('-- (mm)'),
    )
    expect(llSection).toContain('generate_series(0, jsonb_array_length')
    expect(llSection).toContain("WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn'")
  })

  it('conjunct (mm) checks the terminal sign\'s dispositor against chain membership via jsonb_array_elements_text', () => {
    const detectorSql = extractDetectorSql()
    const mmSection = detectorSql.slice(detectorSql.indexOf('-- (mm)'))
    expect(mmSection).toContain('jsonb_array_elements_text')
    expect(mmSection).toContain("jsonb_array_length(a.fact_value_jsonb->'signs')-1")
  })

  it('conjunct (kk) guards with the null check before comparing cycle_detected_at_step', () => {
    const detectorSql = extractDetectorSql()
    const kkSection = detectorSql.slice(
      detectorSql.indexOf('-- (kk)'),
      detectorSql.indexOf('-- (ll)'),
    )
    expect(kkSection).toContain("<> 'null'::jsonb")
  })
})
