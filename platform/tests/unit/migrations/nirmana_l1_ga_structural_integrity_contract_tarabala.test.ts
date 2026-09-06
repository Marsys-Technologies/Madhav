import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — tara_bala_natal_baseline widening pass
 * (migration 782, F-A14) — third migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga (9/57). This adds tara_bala_natal_baseline, taking coverage to 10/57.
 *
 * tara_bala_natal_baseline is a cross-writer-owned category (physically emitted by
 * ga_panchanga_writer.py's _emit_tara_bala_baseline, owned by ga_structural per
 * fact_category_ownership) — the same pattern as bhadra_flag/panchaka_flag in migration 755.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 782
 * carries the twenty prior conjuncts (a)-(t) forward verbatim — including conjuncts (b)/(e)/(f),
 * already genuinely red (tracked) — plus two new conjuncts (u)/(v). This textual test verifies
 * the migration's SHAPE — read-only and bind-parameter-free, all twenty-two conjuncts survive —
 * not a live-DB re-run of the full combined contract; conjuncts (u)/(v) were verified live in
 * isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/782_nirmana_l1_ga_structural_integrity_contract_tarabala.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 782')
  }
  return migration.slice(start + 4, end)
}

describe('migration 782 — ga_structural integrity_check_sql (tara_bala_natal_baseline)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the twenty prior conjuncts (a)-(t) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(p\) kala_sarpa_per_varga\.ks_detection's fact_value_num/,
      /-- \(t\) value_jsonb\.variant_name must equal/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (u)/(v)', () => {
    expect(migration).toMatch(/-- \(u\) tara_bala_natal_baseline\.tara_class domain/)
    expect(migration).toMatch(/-- \(v\) tara_bala_natal_baseline\.tara_class must equal/)
  })

  it('documents the cross-writer-owned category, same pattern as migration 755', () => {
    expect(migration).toMatch(/physically EMITTED by ga_panchanga_writer\.py/)
    expect(migration).toMatch(/OWNED by ga_structural per fact_category_ownership/)
  })

  it('conjunct (u) restricts the domain to exactly the nine classical Tara quality names', () => {
    const detectorSql = extractDetectorSql()
    const uSection = detectorSql.slice(
      detectorSql.indexOf('-- (u)'),
      detectorSql.indexOf('-- (v)'),
    )
    expect(uSection).toContain(
      "NOT IN\n        ('Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak', 'Sadhaka', 'Vadha', 'Mitra', 'Atimitra')",
    )
  })

  it('conjunct (v) re-derives tara_class from fact_subject and panchanga_nakshatra_moon, not restated', () => {
    const detectorSql = extractDetectorSql()
    const vSection = detectorSql.slice(detectorSql.indexOf('-- (v)'))
    expect(vSection).toContain("fact_category = 'panchanga_nakshatra_moon'")
    expect(vSection).toContain("fact_subject = 'NAKSHATRA_MOON_BIRTH'")
    expect(vSection).toContain('substring(a.fact_subject from 13)')
  })

  it('conjunct (v) guards against the Postgres modulo-sign bug (D-L1-55) with positive safety margins', () => {
    const detectorSql = extractDetectorSql()
    const vSection = detectorSql.slice(detectorSql.indexOf('-- (v)'))
    expect(vSection).toContain('+ 270')
    expect(vSection).toContain('+ 90')
    expect(migration).toMatch(/Per D-L1-55/)
  })
})
