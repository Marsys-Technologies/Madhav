import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../catalog'
import { compileCapabilityKnowledge } from '../compiler'
import {
  P_NEEDS,
  evaluateAllPNeeds,
  evaluatePNeed,
  type ProducerProvenance,
} from '../r218_p_need_check'

// R218 (NIKASHA_CHANGE_REGISTER_v2_0.md, D5 rev. 2.1): "run each of P01-P24 through plan_retrieval
// [the planner LLM searching the semantic capability catalog]; PASS when the plan resolves to
// capabilities whose catalog units carry named producers (R85)." This is the behavioural test
// D5 rev. 2.1 says replaces the withdrawn signed necessity matrix.

const PROVENANCE_PATH = join(
  __dirname,
  '../../../../../../../00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/producer_provenance.derived.json',
)

describe('R218: planner P-need producer-provenance test', () => {
  it('T1 §2 carries exactly 24 P-needs, P01 through P24, no gaps or duplicates', () => {
    expect(P_NEEDS).toHaveLength(24)
    expect(P_NEEDS.map((n) => n.id)).toEqual(
      Array.from({ length: 24 }, (_, i) => `P${String(i + 1).padStart(2, '0')}`),
    )
    expect(new Set(P_NEEDS.map((n) => n.question)).size).toBe(24) // no duplicate question text
  })

  it('a capability with a named producer PASSES when it is the top-ranked resolution', () => {
    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-28T00:00:00.000Z')
    // Find a real SCU this snapshot actually carries, and fabricate a provenance file that gives
    // ONLY that one SCU a producer — deterministic and independent of the live provenance file's
    // current (and future-changing) content.
    const target = snapshot.scus[0]
    const provenance: ProducerProvenance = { scus: { [target.scu_id]: { producers: [{ asset_id: 'bg_test_asset' }] } } }
    const result = evaluatePNeed({ id: 'PX', question: target.description }, snapshot, provenance)
    expect(result.top_ranked_scu).toBe(target.scu_id)
    expect(result.pass).toBe(true)
    expect(result.reason).toContain('carries a named producer')
  })

  it('FAILS when the top-ranked resolution carries no producer, even if others in the set do', () => {
    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-28T00:00:00.000Z')
    const target = snapshot.scus[0]
    const other = snapshot.scus[1]
    // The provenance file names a producer for a DIFFERENT scu than the one that will rank first —
    // the top-ranked one must still fail, proving the check reads producer status per-scu, not
    // "does ANY resolved capability have one".
    const provenance: ProducerProvenance = {
      scus: { [other.scu_id]: { producers: [{ asset_id: 'bg_other' }] } },
    }
    const result = evaluatePNeed({ id: 'PX', question: target.description }, snapshot, provenance)
    expect(result.top_ranked_scu).toBe(target.scu_id)
    expect(result.pass).toBe(false)
    expect(result.reason).toContain('carries no named producer')
  })

  it('FAILS honestly (never PASSES) when the plan resolves nothing at all', () => {
    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-28T00:00:00.000Z')
    const emptySnapshot = { ...snapshot, scus: [] }
    const provenance: ProducerProvenance = { scus: {} }
    const result = evaluatePNeed(
      { id: 'PX', question: 'anything at all' },
      emptySnapshot,
      provenance,
    )
    expect(result.resolved_count).toBe(0)
    expect(result.pass).toBe(false)
    expect(result.reason).toBe('no capability resolved at all')
  })

  it('runs all 24 P-needs against the REAL live snapshot and Lane B\'s real, committed producer provenance', () => {
    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-28T00:00:00.000Z')
    const provenance = JSON.parse(readFileSync(PROVENANCE_PATH, 'utf-8')) as ProducerProvenance
    expect(Object.keys(provenance.scus).length).toBeGreaterThan(0)

    const report = evaluateAllPNeeds(snapshot, provenance)
    expect(report.results).toHaveLength(24)
    expect(report.summary.total).toBe(24)
    expect(report.summary.passed + report.summary.failed).toBe(24)
    // Packet-proof floor: this is a live measurement (not a hardcoded pass/fail table) — it must
    // resolve SOMETHING for every P-need (a total failure to resolve anything would itself be a
    // planner defect, distinct from a producer-provenance gap).
    for (const r of report.results) {
      expect(r.resolved_count).toBeGreaterThan(0)
    }
    // At least this wave's own measured floor holds: some P-needs pass, some genuinely do not
    // (editorial=false registry-derived stubs like assess_career/assess_marriage/compose_large_n
    // still lack a reviewed producer claim) — a suite reporting either 0 or 24 would itself be
    // suspicious (either the join or the search is broken).
    expect(report.summary.passed).toBeGreaterThan(0)
    expect(report.summary.failed).toBeGreaterThan(0)
  })
})
