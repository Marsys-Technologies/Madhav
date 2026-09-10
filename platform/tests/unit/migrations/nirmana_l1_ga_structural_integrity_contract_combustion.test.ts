import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — combustion_per_varga widening pass (migration
 * 758, F-A14).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga (5/57). This adds combustion_per_varga, taking coverage to 6/57.
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 758
 * carries the seven prior conjuncts (a)-(g) forward verbatim — including conjuncts (b)/(e)/(f),
 * already genuinely red (tracked since migrations 745/756/757) — plus two new conjuncts (h)/(i).
 * This textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all nine
 * conjuncts survive — not a live-DB re-run of the full combined contract (which cannot currently
 * read true because of (b)/(e)/(f)); conjuncts (h)/(i) were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/758_nirmana_l1_ga_structural_integrity_contract_combustion.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 758')
  }
  return migration.slice(start + 4, end)
}

describe('migration 758 — ga_structural integrity_check_sql (combustion_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the seven prior conjuncts (a)-(g) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(c\) bhadra_flag\.active_at_birth_flag must agree exactly/,
      /-- \(d\) panchaka_flag\.active_at_birth_flag must equal/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(g\) For genuinely non-self-paired rows/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (h)/(i)', () => {
    expect(migration).toMatch(/-- \(h\) combustion_per_varga\.is_combust must equal/)
    expect(migration).toMatch(/-- \(i\) combustion_per_varga\.arc_deg \(varga != 'D1'/)
  })

  it('documents why conjunct (i) excludes D1 (the same dual-D1-source situation F-A17 already root-caused)', () => {
    expect(migration).toMatch(/SAME dual-D1-source situation F-A17/)
    expect(migration).toMatch(/75\/2175 violations, ALL on D1/)
  })

  it('conjunct (h) checks internal self-consistency against the row\'s own stored arc_deg/orb_limit', () => {
    const detectorSql = extractDetectorSql()
    const hSection = detectorSql.slice(
      detectorSql.indexOf('-- (h)'),
      detectorSql.indexOf('-- (i)'),
    )
    expect(hSection).toContain("fact_value_jsonb->>'arc_deg'")
    expect(hSection).toContain("fact_value_jsonb->>'orb_limit'")
  })

  it('conjunct (i) excludes D1 and re-derives arc from ga_vargas\' own varga_position data', () => {
    const detectorSql = extractDetectorSql()
    const iSection = detectorSql.slice(detectorSql.indexOf('-- (i)'))
    expect(iSection).toContain("split_part(a.fact_subject, '_', 1) <> 'D1'")
    expect(iSection).toContain("fact_category = 'varga_position'")
    expect(iSection).toContain("fact_key = 'degree_in_sign'")
  })
})
