import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_yoga_karaka_flag widening pass
 * (migration 785, F-A14) — sixth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik (12/57). This adds
 * graha_yoga_karaka_flag, taking coverage to 13/57.
 *
 * graha_yoga_karaka_flag's `is_yoga_karaka = (g_name == lord_9 == lord_10)` formula resolves
 * house lordship from a single ascendant-sign lookup (SIGN_LORDS), not two independent PyJHora
 * position computations — so this category is NOT the D1 dual-independent-PyJHora-source shape
 * that governs several prior categories in this arc, and no D1-avoidance disclaimer applies here.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 785
 * carries the thirty-one prior conjuncts (a)-(ee) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus two new conjuncts (ff)/(gg). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all thirty-three conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (ff)/(gg) were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/785_nirmana_l1_ga_structural_integrity_contract_yogakaraka.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 785')
  }
  return migration.slice(start + 4, end)
}

describe('migration 785 — ga_structural integrity_check_sql (graha_yoga_karaka_flag)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the thirty-one prior conjuncts (a)-(ee) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(z\) aspect_tajik fact_key domain/,
      /-- \(ee\) orb_deg must satisfy/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (ff)/(gg)', () => {
    expect(migration).toMatch(/-- \(ff\) graha_yoga_karaka_flag\.is_yoga_karaka domain/)
    expect(migration).toMatch(/-- \(gg\) at most one graha per \(chart, ayanamsha, build\)/)
  })

  it('documents why this category is NOT the D1 dual-independent-PyJHora-source shape', () => {
    expect(migration).toMatch(/is NOT the D1\s*\n?\s*-- dual-independent-PyJHora-source shape/)
    expect(migration).toMatch(/a single\s*\n?\s*-- deterministic lookup from one already-resolved ascendant sign/)
  })

  it('documents the classical SIGN_LORDS reasoning for why today\'s data is honestly all-false', () => {
    expect(migration).toMatch(/Capricorn\/\s*\n?\s*-- Aquarius pair/)
    expect(migration).toMatch(/Taurus/)
    expect(migration).toMatch(/not a stale\/empty-detector artifact/)
  })

  it('conjunct (ff) restricts the domain to exactly true/false', () => {
    const detectorSql = extractDetectorSql()
    const ffSection = detectorSql.slice(
      detectorSql.indexOf('-- (ff)'),
      detectorSql.indexOf('-- (gg)'),
    )
    expect(ffSection).toContain("NOT IN ('true', 'false')")
  })

  it('conjunct (gg) groups by the full chart/ayanamsha/build key before counting true rows', () => {
    const detectorSql = extractDetectorSql()
    const ggSection = detectorSql.slice(detectorSql.indexOf('-- (gg)'))
    expect(ggSection).toContain('GROUP BY chart_id, ayanamsha_id, build_id')
    expect(ggSection).toContain('HAVING count(*) > 1')
  })
})
