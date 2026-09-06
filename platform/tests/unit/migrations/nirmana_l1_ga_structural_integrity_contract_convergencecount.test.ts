import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — convergence_count widening pass (migration
 * 814, F-A14) — fifteenth migration in the 800-819 range (adjudication #2057, continuation 4).
 *
 * Migration 813 added contradiction_pair (54/64 by the corrected running tally — see D-L1-105
 * for the governance-table registry-gap finding that established the true denominator is 64,
 * not 57). This adds convergence_count.
 *
 * convergence_count stores two row shapes per varga: one row per graha (entity='graha',
 * total_edges = degree in the Parashari-aspect-or-conjunction graph) and one row per house 1-12
 * (entity='house', total_edges = count of the same edges touching that house). The graha-entity
 * adjacency test is byte-identical to migration 807's graha_centrality adjacency test, so this
 * migration cross-references graha_centrality's own degree_centrality directly rather than
 * re-deriving the aspect graph a second time. The house-entity rows get a genuine full
 * re-derivation reconstructed from graha_centrality's own connected_to arrays joined to each
 * endpoint's house via the sibling graha_dignity_per_varga category.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 814
 * carries the one-hundred-and-eighty-six prior conjuncts (a)-(g20) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus nine new conjuncts
 * (a21)-(i21). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-ninety-five conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested (including a self-caught tautology in an early
 * draft of (e21), fixed before landing).
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/814_nirmana_l1_ga_structural_integrity_contract_convergencecount.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 814')
  }
  return migration.slice(start + 4, end)
}

describe('migration 814 — ga_structural integrity_check_sql (convergence_count)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-eighty-six prior conjuncts (a)-(g20) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(g20\) varga\/subject consistency/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all nine new conjuncts (a21)-(i21)', () => {
    expect(migration).toMatch(/-- \(a21\) fact_key domain/)
    expect(migration).toMatch(/-- \(b21\) entity domain/)
    expect(migration).toMatch(/-- \(c21\) value_num\/value_jsonb consistency/)
    expect(migration).toMatch(/-- \(d21\) total_edges non-negativity/)
    expect(migration).toMatch(/-- \(e21\) graha-row subject-token domain/)
    expect(migration).toMatch(/-- \(f21\) house-row subject format/)
    expect(migration).toMatch(/-- \(g21\) house field domain/)
    expect(migration).toMatch(/-- \(h21\) graha-row cross-reference/)
    expect(migration).toMatch(/-- \(i21\) house-row full re-derivation/)
  })

  it('cross-references convergence_count graha rows against graha_centrality.degree_centrality, not a re-derived graph', () => {
    const detectorSql = extractDetectorSql()
    const h21Section = detectorSql.slice(
      detectorSql.indexOf('-- (h21)'),
      detectorSql.indexOf('-- (i21)'),
    )
    expect(h21Section).toContain('graha_centrality')
    expect(h21Section).toContain('degree_centrality')
  })

  it('re-derives house-row totals from graha_centrality connected_to joined via graha_dignity_per_varga, not a fresh aspect walk', () => {
    const detectorSql = extractDetectorSql()
    const i21Section = detectorSql.slice(detectorSql.indexOf('-- (i21)'))
    expect(i21Section).toContain('graha_centrality')
    expect(i21Section).toContain('connected_to')
    expect(i21Section).toContain('graha_dignity_per_varga')
    expect(i21Section).not.toContain('_graha_aspects_house')
  })

  it('e21 checks token-set membership, not a tautological self-reconstruction of fact_subject', () => {
    const detectorSql = extractDetectorSql()
    const e21Section = detectorSql.slice(
      detectorSql.indexOf('-- (e21)'),
      detectorSql.indexOf('-- (f21)'),
    )
    // the fixed conjunct checks membership in a fixed token set, never rebuilds fact_subject
    // from its own substring (the tautology caught during mutation-testing)
    expect(e21Section).toContain('NOT IN')
    expect(e21Section).not.toMatch(/fact_subject <> \(fact_value_jsonb->>'varga'\)/)
  })

  it("corrects the 'scoped to' header comment to list convergence_count, not a stale 45-category snapshot", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('convergence_count')
    expect(scopedBlock).toContain('contradiction_pair')
    expect(scopedBlock).not.toContain('45 of 57')
  })
})
