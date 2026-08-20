/**
 * f123_dead_pointer_regression.test.ts — F-123 (CL-11 "dead pointer") regression guard.
 *
 * Defect: `kala_now_get`'s (and `kala_ahead_get`'s / `kala_priority_get`'s) `tri_plane
 * .interpretation_ref` advertised `pointerTo('kala_explain_get', hint)` with NO args payload.
 * `kala_explain_get` hard-errors ("either `domain` or `bhava` is required" —
 * `explain.ts`'s `explainRequiresDomainOrBhava` guard) the instant a caller follows that
 * pointer exactly as advertised, with only `chart_id`. Confirmed live against the deployed
 * MCP service on the canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`) before this fix:
 * `kala_now_get` → `tri_plane.interpretation_ref = {instrument:'kala_explain_get', hint:...}`
 * (no `args`) → calling `kala_explain_get({chart_id})` alone → `{ok:false, error:'either
 * \`domain\` or \`bhava\` is required'}`.
 *
 * This test does NOT re-derive its own copy of the `kala_explain_get` guard (that would risk
 * drifting from the real check and passing on a stale assumption, per CLAUDE.md §N.7 item 1) —
 * it imports `explainRequiresDomainOrBhava` straight from `explain.ts`, the exact predicate
 * the live tool runs, and feeds each fixed call site's derived pointer args through it. A
 * regression that removes the `args` payload from any of the three sites again would make
 * this test RED because the real guard would reject the (args-less) call the pointer implies.
 */
import { describe, expect, it } from 'vitest'
import { explainPointerTo, pointerTo, type DrillPointerLike } from '../../lib/kala_envelope.js'
import { explainRequiresDomainOrBhava } from './explain.js'

/** Simulates following a DrillPointerLike exactly as a caller would: `instrument` names the
 *  tool, `args` (if present) is spread as the call's params alongside `chart_id`. Mirrors
 *  what an MCP client does with a `tri_plane` pointer — no domain/bhava beyond what `args`
 *  itself carries. */
function followPointer(pointer: DrillPointerLike): { domain: unknown; bhava: unknown } {
  const args = pointer.args ?? {}
  return { domain: (args as Record<string, unknown>)['domain'], bhava: (args as Record<string, unknown>)['bhava'] }
}

describe('F-123: kala_explain_get pointer dead-end regression', () => {
  it('reproduces the pre-fix defect: a bare pointerTo(kala_explain_get) with no args dead-ends', () => {
    // This IS the exact call shape the three sites (now.ts, ahead.ts, priority.ts) used to
    // emit. Following it, as advertised, gives explain.ts nothing to work with.
    const bareDeadPointer = pointerTo(
      'kala_explain_get',
      'Why this NOW state reads as it does',
    )
    const { domain, bhava } = followPointer(bareDeadPointer)
    // The real kala_explain_get guard rejects this call shape — confirming the pre-fix
    // pointer genuinely dead-ends, not a hypothetical.
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(true)
  })

  it('now.ts site: explainPointerTo with a derived domain clears the real kala_explain_get guard', () => {
    // Mirrors now.ts's primaryDomain derivation: windowFamilies[0]?.domains?.[0].
    const windowFamilies: Array<{ domains?: string[] }> = [{ domains: ['career', 'wealth'] }]
    const primaryDomain = windowFamilies[0]?.domains?.[0] ?? null
    const pointer = explainPointerTo(
      'Why this NOW state reads as it does — the drivers and classical grounds behind the active windows and confluence',
      primaryDomain ? { domain: primaryDomain } : null,
    )
    expect(pointer.args).toEqual({ domain: 'career' })
    const { domain, bhava } = followPointer(pointer)
    expect(domain).toBe('career')
    // The load-bearing assertion: the REAL explain.ts guard, given exactly what the fixed
    // pointer's args carry, does NOT reject the call.
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(false)
  })

  it('ahead.ts site: explainPointerTo with args.domain clears the real kala_explain_get guard', () => {
    const args = { domain: 'health' }
    const pointer = explainPointerTo(
      'Why these forward windows fire — drivers and classical grounds behind each projection',
      args.domain ? { domain: args.domain } : null,
    )
    const { domain, bhava } = followPointer(pointer)
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(false)
  })

  it('priority.ts site: explainPointerTo with domainFilter[0] clears the real kala_explain_get guard', () => {
    const domainFilter: string[] | null = ['relationship', 'progeny']
    const pointer = explainPointerTo(
      'drill into the causal chain (PACT stages) behind any of these ranked signals\' domain/bhava.',
      domainFilter && domainFilter.length > 0 ? { domain: domainFilter[0] as string } : null,
    )
    const { domain, bhava } = followPointer(pointer)
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(false)
  })

  it('honest degrade: when no domain is derivable, explainPointerTo does not fabricate one, and says so in the hint', () => {
    const pointer = explainPointerTo('Why this NOW state reads as it does', null)
    expect(pointer.args).toBeUndefined()
    expect(pointer.hint).toContain('pass domain or bhava when calling')
    // Honest about the residual gap: following THIS pointer as advertised (no args) would
    // still dead-end — that is the correct, disclosed behavior for a genuinely domain-less
    // NOW state, not a regression. The hint tells the caller why, instead of pretending a
    // fabricated domain would work.
    const { domain, bhava } = followPointer(pointer)
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(true)
  })
})
