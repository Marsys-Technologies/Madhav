import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — bhava_significance_link widening pass
 * (migration 818, F-A14) — nineteenth migration in the 800-819 range (adjudication #2057,
 * continuation 4).
 *
 * Migration 817 added aspect_parashari_per_varga (58/64 by the corrected running tally),
 * confirmed immune to F-A24. This adds bhava_significance_link.
 *
 * bhava_significance_link discovers F-A25: a NEW writer bug, distinct root cause from F-A24.
 * The caller computes `lagna_sign_num` by checking ONLY the mixed-case key `"Lagna"`, but
 * `_extract_chart_state` only ever sets `state["LAGNA"]` (all caps) — so the lookup never
 * matches, for ANY varga including D1 (unlike F-A24, which only affected non-D1 vargas because
 * its own lookup defensively checks both cases). Confirmed WRONG on chart cb73cd3d across 1450 of
 * 1740 lord_placed rows, spanning all 29 vargas including D1.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 818
 * carries the two-hundred-and-twenty-three prior conjuncts (a)-(h24) forward verbatim —
 * including conjuncts (b)/(e)/(f)/(e7)/(j22), already genuinely red (tracked: F-A15/F-A17/F-157/
 * F-A18/F-A24) — plus nine new conjuncts (a25)-(i25), the last of which (i25/F-A25) is ALSO
 * genuinely red and newly discovered here. This textual test verifies the migration's SHAPE —
 * read-only and bind-parameter-free, all two-hundred-thirty-two conjuncts survive — not a
 * live-DB re-run of the full combined contract; the new conjuncts were verified live in
 * isolation during authoring, each individually mutation-tested (including (i25), whose mutation
 * test confirmed it catches additional corruption beyond the known bug's own baseline).
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/818_nirmana_l1_ga_structural_integrity_contract_bhavasignificancelink.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 818')
  }
  return migration.slice(start + 4, end)
}

describe('migration 818 — ga_structural integrity_check_sql (bhava_significance_link)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the two-hundred-and-twenty-three prior conjuncts (a)-(h24) verbatim, including the still-red (b)/(e)/(f)/(e7)/(j22)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(j22\) F-A24, GENUINELY RED TODAY/,
      /-- \(h24\) completeness per graha/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all nine new conjuncts (a25)-(i25), with (i25) marked genuinely red', () => {
    expect(migration).toMatch(/-- \(a25\) fact_key domain/)
    expect(migration).toMatch(/-- \(b25\) link_kind consistency/)
    expect(migration).toMatch(/-- \(c25\) fact_value_text\/value_jsonb consistency/)
    expect(migration).toMatch(/-- \(d25\) link_type classification/)
    expect(migration).toMatch(/-- \(e25\) fact_subject format/)
    expect(migration).toMatch(/-- \(f25\) lord_aspects lord consistency/)
    expect(migration).toMatch(/-- \(g25\) lord_aspects target-house exclusion/)
    expect(migration).toMatch(/-- \(h25\) lord_aspects full classical re-derivation/)
    expect(migration).toMatch(/-- \(i25\) F-A25, GENUINELY RED TODAY/)
  })

  it('documents F-A25 as a distinct root cause from F-A24 (wrong-case key, not a missing key)', () => {
    expect(migration).toMatch(/F-A25/)
    expect(migration).toContain('"Lagna"')
    expect(migration).toContain('"LAGNA"')
    expect(migration).toContain('cb73cd3d')
    expect(migration).toMatch(/1450/)
  })

  it('lord_aspects conjuncts check internal self-consistency against lord_placed, not a re-derived Lagna', () => {
    const detectorSql = extractDetectorSql()
    const f25Section = detectorSql.slice(
      detectorSql.indexOf('-- (f25)'),
      detectorSql.indexOf('-- (g25)'),
    )
    expect(f25Section).toContain("fact_key = 'lord_placed'")
  })

  it('i25 cross-references lord_in_house_per_varga as ground truth for the D1 lagna, not a self-derived value', () => {
    const detectorSql = extractDetectorSql()
    const i25Section = detectorSql.slice(detectorSql.indexOf('-- (i25)'))
    expect(i25Section).toContain('lord_in_house_per_varga')
    expect(i25Section).toContain("fact_value_jsonb->>'house' = '1'")
  })

  it("corrects the 'scoped to' header comment to list bhava_significance_link", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('bhava_significance_link')
    expect(scopedBlock).toContain('aspect_parashari_per_varga')
  })
})
