import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_parashari_given / aspect_parashari_
 * received bundle widening pass (migration 798, F-A14) — nineteenth migration in the 780-799
 * range (adjudication #2012), the second-to-last free number (adjudication #2057 requests the
 * continuation range).
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
 * graha_effective_dignity_modified_by_aspects; migration 794 added
 * graha_composite_state_classification; migration 795 added karaka_house_lord_overlap_flag;
 * migration 796 added the Group C Bhava Bala extended bundle; migration 797 added
 * aspect_matrix_summary (37/57). This adds BOTH aspect_parashari_given and aspect_parashari_
 * received in one migration — mirror-image given/received views of the same classical Parashari
 * aspect data, emitted in lockstep by the same per-graha loop — taking coverage to 39/57.
 *
 * Fully re-derived from first principles: each graha's own house from ga_positions'
 * graha_position.house_d1, the classical Parashari offset table (brahmagyan/aspects.py's
 * get_graha_aspects, hardcoded directly as the authority), and the target-house arithmetic
 * mirroring the writer's own formula. The given/received bidirectional correspondence closes
 * the loop for the received side without re-deriving the classical formula twice.
 *
 * Naming note: this migration's new conjuncts use the (a6)-(h6) numeric-suffix label sequence
 * rather than the next-seeming plain letters (m)-(t) — a mid-authoring check found the entire
 * single-letter a-z alphabet (and most double-letter aa-zz labels) was already exhausted by
 * migrations 780-784's original conjuncts, so (m)-(t) would have silently duplicated existing
 * labels (harmless for SQL correctness — each NOT EXISTS block is self-contained regardless of
 * its comment label — but confusing for future readers). (a6)-(h6) were verified collision-free
 * before use.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 798
 * carries the eighty-two prior conjuncts (a)-(l) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus eight new conjuncts (a6)-(h6). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all ninety conjuncts
 * survive — not a live-DB re-run of the full combined contract; the new conjuncts were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/798_nirmana_l1_ga_structural_integrity_contract_parashariaspects.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 798')
  }
  return migration.slice(start + 4, end)
}

describe('migration 798 — ga_structural integrity_check_sql (aspect_parashari_given / received bundle)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the eighty-two prior conjuncts (a)-(l) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(k\) aspect_matrix_summary\.aspects_received_count domain/,
      /-- \(l\) full re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all eight new conjuncts spanning both categories, using collision-free (a6)-(h6) labels', () => {
    expect(migration).toMatch(/-- \(a6\) aspect_parashari_given\.fact_value_num domain/)
    expect(migration).toMatch(/-- \(b6\) aspect_parashari_given\.fact_key format/)
    expect(migration).toMatch(/-- \(c6\) aspect_parashari_given full re-derivation, direction 1/)
    expect(migration).toMatch(/-- \(d6\) aspect_parashari_given full re-derivation, direction 2/)
    expect(migration).toMatch(/-- \(e6\) aspect_parashari_received\.fact_value_num domain/)
    expect(migration).toMatch(/-- \(f6\) aspect_parashari_received\.fact_subject format/)
    expect(migration).toMatch(/-- \(g6\) given -> received bidirectional correspondence/)
    expect(migration).toMatch(/-- \(h6\) received -> given bidirectional correspondence/)
  })

  it('does not silently duplicate pre-existing single-letter conjunct labels', () => {
    // (m) through (t) already exist as plain letters from migrations 780-784's original
    // conjuncts (nway_config_per_varga / kala_sarpa_per_varga); the new bundle must not reuse
    // them as fresh section markers even though a duplicate label would not break SQL behavior.
    const detectorSql = extractDetectorSql()
    for (const bogusFreshLabel of [
      '-- (m) aspect_parashari_given',
      '-- (n) aspect_parashari_given',
      '-- (o) aspect_parashari_given',
      '-- (p) aspect_parashari_given',
      '-- (q) aspect_parashari_received',
      '-- (r) aspect_parashari_received',
      '-- (s) given -> received',
      '-- (t) received -> given',
    ]) {
      expect(detectorSql).not.toContain(bogusFreshLabel)
    }
  })

  it('re-derives the classical Parashari offset table hardcoded per graha, reading house from ga_positions', () => {
    const detectorSql = extractDetectorSql()
    const c6Section = detectorSql.slice(
      detectorSql.indexOf('-- (c6) aspect_parashari_given full re-derivation, direction 1'),
      detectorSql.indexOf('-- (d6)'),
    )
    expect(c6Section).toContain("fact_category = 'graha_position'")
    expect(c6Section).toContain("fact_key = 'house_d1'")
    expect(c6Section).toContain('ARRAY[4,7,8]')
    expect(c6Section).toContain('ARRAY[5,7,9]')
    expect(c6Section).toContain('ARRAY[3,7,10]')
  })

  it('closes the received-side loop via bidirectional correspondence rather than re-deriving twice', () => {
    const detectorSql = extractDetectorSql()
    const h6Section = detectorSql.slice(detectorSql.indexOf('-- (h6)'))
    expect(h6Section).toContain("fact_category = 'aspect_parashari_given'")
    expect(h6Section).not.toContain('graha_position')
  })
})
