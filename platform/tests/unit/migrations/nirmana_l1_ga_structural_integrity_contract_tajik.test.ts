import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_tajik widening pass (migration 784,
 * F-A14) — fifth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb (11/57). This adds aspect_tajik, taking coverage to 12/57.
 *
 * aspect_tajik is another D1-sourced category (ga_structural's own in-memory chart_output), so
 * per the now-established D1 dual-independent-PyJHora-source discipline this migration ships six
 * self-consistency/domain/cross-field conjuncts against the row's own already-stored fields
 * instead of re-deriving against an external authority.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 784
 * carries the twenty-five prior conjuncts (a)-(y) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus six new conjuncts (z)-(ee). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all thirty-one conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (z)-(ee) were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/784_nirmana_l1_ga_structural_integrity_contract_tajik.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 784')
  }
  return migration.slice(start + 4, end)
}

describe('migration 784 — ga_structural integrity_check_sql (aspect_tajik)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the twenty-five prior conjuncts (a)-(y) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(w\) conjunction_within_orb\.orb_deg domain/,
      /-- \(y\) pair ordering invariant/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (z)-(ee)', () => {
    expect(migration).toMatch(/-- \(z\) aspect_tajik fact_key domain/)
    expect(migration).toMatch(/-- \(aa\) fact_value_num must equal value_jsonb\.orb_deg/)
    expect(migration).toMatch(/-- \(bb\) value_jsonb\.orb_strength must equal/)
    expect(migration).toMatch(/-- \(cc\) value_jsonb\.applying must match/)
    expect(migration).toMatch(/-- \(dd\) value_jsonb\.salience must equal/)
    expect(migration).toMatch(/-- \(ee\) orb_deg must satisfy/)
  })

  it('documents why aspect_tajik ships self-consistency conjuncts rather than re-deriving against an external authority', () => {
    expect(migration).toMatch(/D1 dual-independent-PyJHora-source discipline/)
    expect(migration).toMatch(/four _per_varga occurrences/)
  })

  it('conjunct (z) restricts fact_key to exactly the four live Tajik types, excluding Nakta', () => {
    const detectorSql = extractDetectorSql()
    const zSection = detectorSql.slice(
      detectorSql.indexOf('-- (z)'),
      detectorSql.indexOf('-- (aa)'),
    )
    expect(zSection).toContain("NOT IN ('yamaya', 'ithasala', 'eesarpha', 'manaau')")
  })

  it('conjunct (bb) re-derives orb_strength from orb_deg and deeptamsa_sum_deg, not restated', () => {
    const detectorSql = extractDetectorSql()
    const bbSection = detectorSql.slice(
      detectorSql.indexOf('-- (bb)'),
      detectorSql.indexOf('-- (cc)'),
    )
    expect(bbSection).toContain("(fact_value_jsonb->>'orb_deg')::numeric")
    expect(bbSection).toContain("(fact_value_jsonb->>'deeptamsa_sum_deg')::numeric")
    expect(bbSection).toContain('GREATEST(0.0, 1.0 -')
  })

  it('conjunct (cc) intentionally excludes yamaya from the applying-motion constraint', () => {
    const detectorSql = extractDetectorSql()
    const ccSection = detectorSql.slice(
      detectorSql.indexOf('-- (cc)'),
      detectorSql.indexOf('-- (dd)'),
    )
    expect(ccSection).not.toContain("fact_key = 'yamaya'")
    expect(ccSection).toContain("fact_key = 'ithasala'")
    expect(ccSection).toContain("fact_key = 'eesarpha'")
    expect(ccSection).toContain("fact_key = 'manaau'")
  })

  it('conjunct (ee) re-derives the writer\'s own per-type orb threshold branch structure', () => {
    const detectorSql = extractDetectorSql()
    const eeSection = detectorSql.slice(detectorSql.indexOf('-- (ee)'))
    expect(eeSection).toContain("fact_key = 'yamaya'")
    expect(eeSection).toContain("fact_key IN ('ithasala', 'eesarpha')")
    expect(eeSection).toContain("fact_key = 'manaau'")
  })
})
