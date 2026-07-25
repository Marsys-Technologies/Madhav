/**
 * Elevation Campaign v2.1 · Stream α (SATYA) — flagship completeness wiring verification.
 *
 * Proves that the obvious naive-caller entrypoint (assess_wealth / assess_career) is now backed
 * by dossier's 100%-accounted domain territory (option (b)(i)), instead of a shallow default.
 * This is the unit-level stand-in for γ's live "how is my wealth?" acceptance test: DB access is
 * not available here, but runDossier reads embedded slice bundles (pure, no I/O), so the exact
 * completeness a naive caller would now receive is fully verifiable in isolation.
 */
import { describe, it, expect } from 'vitest'
import { runDossier } from '../tools/dossier.js'
import { assembleDomainCompleteness, attachDomainCompleteness, buildDomainCompletenessPointer } from '../tools/registry_bridge.js'

const WEALTH_CHART = '482012f1-710e-4a25-994a-93821f5871aa'

describe('Elevation α — assess_* backed by dossier completeness', () => {
  it('dossier wealth slice for the flagship chart is a large, real concept territory', () => {
    const page = runDossier({ domain: 'wealth', chart_id: WEALTH_CHART, budget_kb: 64 })
    expect(page.ok).toBe(true)
    // The whole point: this is thousands of concepts, not the ~15% shallow default set.
    expect(page.slice_size).toBeGreaterThan(1000)
  })

  it('assembleDomainCompleteness pages to 100% and opens the synthesis gate', () => {
    const block = assembleDomainCompleteness('wealth', WEALTH_CHART)
    expect(block).not.toBeNull()
    const b = block as Record<string, unknown>
    // 100%-accounted: accounted === slice_size, pct 100, gate OPEN, composition scaffold present.
    expect(b['fully_accounted']).toBe(true)
    expect(b['accounted']).toBe(b['slice_size'])
    expect(b['pct']).toBe(100)
    expect(b['synthesis_gate']).toBe('OPEN')
    expect(b['composition_scaffold']).toBeDefined()
    // The coverage map enumerates the serving tools that carry this domain's concepts.
    expect(Array.isArray(b['coverage_map'])).toBe(true)
    expect((b['coverage_map'] as unknown[]).length).toBeGreaterThan(0)
    expect(b['distinct_serving_tools'] as number).toBeGreaterThan(0)
    // The per-state tally sums to the slice size (nothing silently dropped, B.10).
    const cbs = b['coverage_by_state'] as Record<string, number>
    const stateSum = Object.values(cbs).reduce((s, n) => s + n, 0)
    expect(stateSum).toBe(b['slice_size'])
  })

  it('attachDomainCompleteness folds the map + an un-missable steer into an assess_* response', () => {
    // BEFORE: a bare shallow assess response (the ~15% default a naive caller used to get).
    const response: Record<string, unknown> = {
      domain: 'wealth',
      verdict: { clauses: [] },
      judgment_flags: ['domain_inference_requires_acharya_validation'],
    }
    const before = JSON.stringify(response).length

    attachDomainCompleteness(response, 'wealth', WEALTH_CHART)

    // AFTER: complete accounting is attached, the directive is un-missable, and the steer flag
    // is prepended ahead of the pre-existing flags.
    expect(response['domain_completeness']).toBeDefined()
    expect(typeof response['completeness_directive']).toBe('string')
    expect(String(response['completeness_directive'])).toContain('dossier(')
    const flags = response['judgment_flags'] as string[]
    expect(String(flags[0])).toContain('complete_domain_accounting_attached')
    // Original flags are preserved, never dropped.
    expect(flags).toContain('domain_inference_requires_acharya_validation')
    // The response now carries meaningfully more grounding than the shallow default.
    expect(JSON.stringify(response).length).toBeGreaterThan(before + 500)
  })

  it('career slice is wired identically (both flagship domains)', () => {
    const block = assembleDomainCompleteness('career', WEALTH_CHART)
    expect(block).not.toBeNull()
    expect((block as Record<string, unknown>)['fully_accounted']).toBe(true)
  })

  it('returns null (assess_* unchanged) for a domain/chart with no precompiled slice', () => {
    expect(assembleDomainCompleteness('health', WEALTH_CHART)).toBeNull()
  })

  it('judgment_query pointer is compact (no heavy coverage_map) but carries the 100% accounting', () => {
    const ptr = buildDomainCompletenessPointer('wealth', WEALTH_CHART)
    expect(ptr).not.toBeNull()
    const p = ptr as Record<string, unknown>
    expect(p['fully_accounted']).toBe(true)
    expect(p['pct']).toBe(100)
    // Compact: the per-tool map is intentionally omitted for the 12KB judgment_query budget.
    expect(p['coverage_map']).toBeUndefined()
    expect(p['full_hydration']).toBeDefined()
    // Guards: non-flagship domain / non-string domain → null (judgment_query unchanged).
    expect(buildDomainCompletenessPointer('health', WEALTH_CHART)).toBeNull()
    expect(buildDomainCompletenessPointer(7, WEALTH_CHART)).toBeNull()
  })
})
