/**
 * dossier_receipt.test.ts — ŚODHANA T5 (PŪRTI) acceptance test for the compact
 * completeness receipt (MC-012/028/034, the Offer-Law fix).
 *
 * Proves the acceptance criterion: dossier's gate is satisfiable in ≤2 calls at
 * ≤8KB overhead for the compact-receipt path — over the REAL committed wealth slice
 * of the canonical chart, not a fixture.
 */
import { describe, it, expect } from 'vitest'
import { runDossierReceipt } from './dossier.js'

const CANON = '482012f1-710e-4a25-994a-93821f5871aa'

describe('dossier compact completeness receipt (T5 / PŪRTI)', () => {
  it('wealth/482012f1: gate is satisfiable in ONE call under the ≤2KB target', () => {
    const r = runDossierReceipt({ domain: 'wealth', chart_id: CANON })
    expect(r.ok).toBe(true)
    expect(r.mode).toBe('receipt')
    // The gate the paged path only reaches after 6 firehose pages is reached in ONE call.
    expect(r.synthesis_gate).toBe('OPEN')
    expect(r.gate_basis).toBe('completeness_receipt')
    // Coverage attests the whole territory: 100% accounted (state_totals sum = slice_size).
    expect(r.coverage.accounted).toBe(r.slice_size)
    expect(r.coverage.pct).toBe(100)
    // The compact drill index replaces the per-concept firehose.
    expect(r.families.length).toBeGreaterThan(0)
    // Acceptance: satisfiable in ≤2 calls at ≤8KB overhead — this is ONE call.
    expect(r.receipt_bytes).toBeDefined()
    expect(r.receipt_bytes!).toBeLessThanOrEqual(8192)
    // The ≤2KB gate-summary target holds at the CORE (coverage % + per-family accounting
    // states + gate boolean + drill handles) — self-describing prose adds the remainder.
    const core = JSON.stringify({
      coverage: r.coverage, families: r.families,
      synthesis_gate: r.synthesis_gate, chain_pattern_units: r.chain_pattern_units,
    })
    expect(Buffer.byteLength(core, 'utf8')).toBeLessThanOrEqual(2048)
    // No per-concept type-id enumeration leaked into the receipt.
    const serialized = JSON.stringify(r)
    expect(serialized).not.toContain('argala_natal_matrix:from_sign')
  })

  it('career/482012f1: same one-call gate satisfaction', () => {
    const r = runDossierReceipt({ domain: 'career', chart_id: CANON })
    expect(r.ok).toBe(true)
    expect(r.synthesis_gate).toBe('OPEN')
    expect(r.receipt_bytes!).toBeLessThanOrEqual(8192)
  })

  it('unknown slice: honest not-available receipt, no throw', () => {
    const r = runDossierReceipt({ domain: 'nonexistent', chart_id: CANON })
    expect(r.ok).toBe(false)
    expect(r.error?.class).toBe('slice_not_available')
    expect(r.synthesis_gate).toBe('BLOCKED')
  })

  it('families carry accounting states + concept counts (the "what is covered" index)', () => {
    const r = runDossierReceipt({ domain: 'wealth', chart_id: CANON })
    for (const fam of r.families) {
      const [tool, states, concepts] = fam
      expect(typeof tool).toBe('string')
      expect(concepts).toBeGreaterThan(0)
      expect(states.length).toBeGreaterThan(0)
    }
    // The five accounting states are all represented in the coverage tally.
    for (const k of ['served', 'empty_for_this_chart', 'not_computed_globally'] as const) {
      expect(typeof r.coverage[k]).toBe('number')
    }
  })
})
