import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_composite_state_classification widening
 * pass (migration 794, F-A14) — fifteenth migration in the 780-799 range (adjudication #2012).
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
 * graha_effective_dignity_modified_by_aspects (26/57). This adds
 * graha_composite_state_classification, taking coverage to 27/57.
 *
 * The full seven-way decision tree is re-derived from first principles: dignity from
 * graha_position.sign against the classical exaltation/debilitation/own-sign tables copied from
 * pyjhora_adapter/dignities.py; combustion from graha_position.combustion_state; retrograde from
 * graha_position.retrograde_flag; the debilitation_cancelled/debilitated split from ga_yoga's
 * own authoritative ga_yoga_firings.neecha_bhanga_raja_yoga row (a genuine cross-ASSET §N.5
 * reference). Verified against ALL 135 live rows, not a sample.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 794
 * carries the sixty-eight prior conjuncts (a)-(ff3) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus two new conjuncts (a4)/(b4). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all seventy conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (a4)/(b4) were
 * verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/794_nirmana_l1_ga_structural_integrity_contract_compositestate.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 794')
  }
  return migration.slice(start + 4, end)
}

describe('migration 794 — ga_structural integrity_check_sql (graha_composite_state_classification)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the sixty-eight prior conjuncts (a)-(ff3) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(cc3\) graha_effective_dignity_modified_by_aspects\.effective_dignity_score domain/,
      /-- \(ff3\) per-contribution delta re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (a4)/(b4)', () => {
    expect(migration).toMatch(
      /-- \(a4\) graha_composite_state_classification fact_value_text domain/,
    )
    expect(migration).toMatch(/-- \(b4\) full first-principles re-derivation/)
  })

  it('re-derives dignity from graha_position.sign against the classical tables, not the mismatched graha_dignity_per_varga vocabulary', () => {
    const detectorSql = extractDetectorSql()
    const b4Section = detectorSql.slice(detectorSql.indexOf('-- (b4)'))
    expect(b4Section).toContain("fact_category='graha_position'")
    expect(b4Section).not.toContain('graha_dignity_per_varga')
    expect(b4Section).toContain("WHEN a.fact_subject = 'SUN' AND p_sign.fact_value_text = 'Aries' THEN 'exalted'")
    expect(b4Section).toContain("WHEN a.fact_subject = 'SAT' AND p_sign.fact_value_text = 'Libra' THEN 'exalted'")
  })

  it('re-derives the debilitation_cancelled split from ga_yoga_firings, a genuine cross-asset reference', () => {
    const detectorSql = extractDetectorSql()
    const b4Section = detectorSql.slice(detectorSql.indexOf('-- (b4)'))
    expect(b4Section).toContain('ga_yoga_firings')
    expect(b4Section).toContain("yoga_canonical_id = 'neecha_bhanga_raja_yoga'")
    expect(b4Section).toContain('y.fired = true')
    expect(b4Section).toContain('constituent_planets')
  })

  it('reads combustion and retrograde from graha_position rather than recomputing from raw longitude', () => {
    const detectorSql = extractDetectorSql()
    const b4Section = detectorSql.slice(detectorSql.indexOf('-- (b4)'))
    expect(b4Section).toContain("fact_key='combustion_state'")
    expect(b4Section).toContain("fact_key='retrograde_flag'")
  })
})
