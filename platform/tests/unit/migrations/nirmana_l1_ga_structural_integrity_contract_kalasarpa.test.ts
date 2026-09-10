import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — kala_sarpa_per_varga widening pass (migration
 * 781, F-A14) — second migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga (8/57). This adds
 * kala_sarpa_per_varga, taking coverage to 9/57.
 *
 * kala_sarpa_per_varga implements a genuinely non-trivial cyclic arc-membership algorithm
 * (whether all 7 classical grahas fall within the Rahu→Ketu or Ketu→Rahu arc) — re-deriving that
 * walk in SQL would be substantially more complex than this campaign's established per-conjunct
 * scope. Instead this migration ships five self-consistency/domain/cross-field re-derivation
 * conjuncts against the row's own already-stored fields, the same discipline already used for
 * combustion_per_varga's conjunct (h) and graha_yuddha_per_varga's (j)/(k).
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 781
 * carries the fifteen prior conjuncts (a)-(o) forward verbatim — including conjuncts (b)/(e)/(f),
 * already genuinely red (tracked) — plus five new conjuncts (p)-(t). This textual test verifies
 * the migration's SHAPE — read-only and bind-parameter-free, all twenty conjuncts survive — not a
 * live-DB re-run of the full combined contract; conjuncts (p)-(t) were verified live in isolation
 * during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/781_nirmana_l1_ga_structural_integrity_contract_kalasarpa.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 781')
  }
  return migration.slice(start + 4, end)
}

describe('migration 781 — ga_structural integrity_check_sql (kala_sarpa_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the fifteen prior conjuncts (a)-(o) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(m\) nway_config_per_varga\.stellium's fact_value_num/,
      /-- \(o\) every graha named in value_jsonb\.grahas \(varga != 'D1'/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all five new conjuncts (p)-(t)', () => {
    expect(migration).toMatch(/-- \(p\) kala_sarpa_per_varga\.ks_detection's fact_value_num/)
    expect(migration).toMatch(/-- \(q\) fact_value_text must equal value_jsonb\.variant/)
    expect(migration).toMatch(/-- \(r\) fact_value_text domain: must be one of/)
    expect(migration).toMatch(/-- \(s\) fires \(fact_value_num=1\.0\) must hold if and only if/)
    expect(migration).toMatch(/-- \(t\) value_jsonb\.variant_name must equal/)
  })

  it('documents why the full arc-membership algorithm was NOT re-derived in SQL, and cites the same-discipline precedent', () => {
    expect(migration).toMatch(/substantially more complex than this\s*\n?\s*-- campaign's established per-conjunct scope/)
    expect(migration).toMatch(/combustion_per_varga's conjunct \(h\)/)
  })

  it('conjunct (r) restricts the domain to exactly the three legitimate variant values', () => {
    const detectorSql = extractDetectorSql()
    const rSection = detectorSql.slice(
      detectorSql.indexOf('-- (r)'),
      detectorSql.indexOf('-- (s)'),
    )
    expect(rSection).toContain("NOT IN ('none', 'kala_sarpa', 'kala_amrita')")
  })

  it('conjunct (t) re-derives variant_name from BOTH variant and rahu_house, not restated', () => {
    const detectorSql = extractDetectorSql()
    const tSection = detectorSql.slice(detectorSql.indexOf('-- (t)'))
    expect(tSection).toContain("'KALA_SARPA_RAHU_H'")
    expect(tSection).toContain("'KALA_AMRITA_RAHU_H'")
    expect(tSection).toContain("fact_value_jsonb->>'rahu_house'")
  })
})
