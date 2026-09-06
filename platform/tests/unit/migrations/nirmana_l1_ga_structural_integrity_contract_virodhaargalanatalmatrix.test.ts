import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — virodha_argala_natal_matrix widening pass
 * (migration 841, F-A14) — second migration in the 840-859 range (adjudication #2101, L1
 * continuation 5).
 *
 * Migration 840 added argala_natal_matrix (61/64 by the corrected running tally), confirmed
 * immune to F-A24/F-A25 by construction (its malefic-count filter never sees a "LAGNA"
 * occupant). This adds virodha_argala_natal_matrix — the LAST real remaining ga_structural
 * category (eclipse_proximity_natal remains a documented, permanently-excluded B.10
 * placeholder, not counted toward this tally).
 *
 * virodha_argala_natal_matrix shares the exact same 144-cell-per-varga loop and occupancy map
 * as argala_natal_matrix, but its score is a BINARY any-occupant check (no malefic filter). This
 * exposes F-A26: the occupancy map built by the per-varga caller (`_build_varga_relationship_rows`,
 * lines ~6210-6214) sweeps in the "LAGNA"/"Lagna" pseudo-entry every `varga_state` legitimately
 * carries for lagna-sign-number consumers, without excluding it — so a chart whose lagna sign is
 * also a virodha-offset source sign gets a spurious 1.0 even with no real graha there. Confirmed
 * on both Aries-lagna canonical charts (24/62640 D1 rows wrong), cross-checked against the
 * already-verified graha_dignity_per_varga category and mutation-proven in both directions.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 841
 * carries the two-hundred-and-forty-eight prior conjuncts (a)-(h27) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7)/(j22)/(i25), already genuinely red (tracked: F-A15/F-A17/F-157/
 * F-A18/F-A24/F-A25) — plus seven new conjuncts (a28)/(b28)/(c28)/(d28)/(e28)/(f28)/(g28), of
 * which (d28) is ITSELF genuinely red today (F-A26, newly discovered). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all two-hundred-fifty-five
 * conjuncts survive — not a live-DB re-run of the full combined contract; the new conjuncts were
 * verified live in isolation during authoring, each individually mutation-tested, including a
 * self-caught tautological fact_key-reconstruction defect in an early draft of (b28) (the same
 * tautology-conjunct class first caught at migration 814's (e21) and again at 817's (e24)),
 * replaced with a genuine regex format check before landing.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/841_nirmana_l1_ga_structural_integrity_contract_virodhaargalanatalmatrix.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 841')
  }
  return migration.slice(start + 4, end)
}

describe('migration 841 — ga_structural integrity_check_sql (virodha_argala_natal_matrix)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the two-hundred-and-forty-eight prior conjuncts (a)-(h27) verbatim, including the still-red (b)/(e)/(f)/(e7)/(j22)/(i25)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(j22\) F-A24, GENUINELY RED TODAY/,
      /-- \(i25\) F-A25, GENUINELY RED TODAY/,
      /-- \(a27\) non-argala-offset domain/,
      /-- \(h27\) exact count invariant/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new conjuncts (a28)/(b28)/(c28)/(d28)/(e28)/(f28)/(g28)', () => {
    expect(migration).toMatch(/-- \(a28\) non-virodha-offset domain/)
    expect(migration).toMatch(/-- \(b28\) fact_key format/)
    expect(migration).toMatch(/-- \(c28\) offset full re-derivation/)
    expect(migration).toMatch(/-- \(d28\) F-A26, GENUINELY RED TODAY/)
    expect(migration).toMatch(/-- \(e28\) fact_subject format/)
    expect(migration).toMatch(/-- \(f28\) target\/source sign_num domain/)
    expect(migration).toMatch(/-- \(g28\) exact count invariant/)
  })

  it('documents F-A26 as a newly-discovered genuinely-red conjunct, distinct from F-A24/F-A25', () => {
    expect(migration).toContain('F-A26')
    expect(migration).toContain('_build_varga_relationship_rows')
  })

  it('(b28) is a genuine regex format check, not a tautological self-reconstruction', () => {
    const detectorSql = extractDetectorSql()
    const b28Section = detectorSql.slice(
      detectorSql.indexOf('-- (b28)'),
      detectorSql.indexOf('-- (c28)'),
    )
    expect(b28Section).toContain('!~')
    expect(b28Section).toContain("'^from_sign_[0-9]+_offset_[0-9]+$'")
  })

  it('(d28) re-derives ANY-occupant status from graha_dignity_per_varga, no malefic token filter', () => {
    const detectorSql = extractDetectorSql()
    const d28Section = detectorSql.slice(
      detectorSql.indexOf('-- (d28)'),
      detectorSql.indexOf('-- (e28)'),
    )
    expect(d28Section).toContain('graha_dignity_per_varga')
    expect(d28Section).not.toContain('RAH_MEAN')
  })

  it('uses safe-wraparound modulo arithmetic in (c28), avoiding the D-L1-102 sign hazard', () => {
    const detectorSql = extractDetectorSql()
    const c28Section = detectorSql.slice(
      detectorSql.indexOf('-- (c28)'),
      detectorSql.indexOf('-- (d28)'),
    )
    expect(c28Section).toContain('+ 120, 12')
  })

  it('documents this as the second migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })

  it("corrects the 'scoped to' header comment to list virodha_argala_natal_matrix", () => {
    const scopedStart = migration.indexOf(
      '-- ga_structural integrity contract (target: chart_facts, scoped to',
    )
    const scopedBlock = migration.slice(scopedStart, migration.indexOf('SELECT\n', scopedStart))
    expect(scopedBlock).toContain('virodha_argala_natal_matrix')
    expect(scopedBlock).toContain('argala_natal_matrix')
    expect(scopedBlock).toContain('62 of 64')
  })
})
