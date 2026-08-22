/**
 * f179_kernel_floor_flag_and_immune_field_additions.test.ts — PARIŚEṢA-V4 finding F-179.
 *
 * F-179 is an audit lane: which honesty/disclosure flags are trim-eligible and should not
 * be. The audit's real output is the classification table (see the PR body); this file pins
 * the resulting code changes with §N.8 "prove-it-can-fail" tests — each protected code gets
 * a test that constructs a kernel dense enough to force a real trim and asserts the code
 * survives it (mutation-check: removing the code from `KERNEL_FLOOR_FLAG_CODES` — or the
 * field from `IMMUNE_HONESTY_FIELDS` — flips the corresponding assertion to fail).
 *
 * Verified-reachable additions to `KERNEL_FLOOR_FLAG_CODES` (both are emitted into
 * `SaraKernel.flags` by register_d8_assess_domain.ts / registry_bridge.ts's
 * buildAssessResponse — the ONLY code path that ever populates a Sāra kernel's flags):
 *   - significator_condition_unavailable  (the D1 dignity/ṣaḍbala leg was never checked)
 *   - hollow_envelope_no_data_rows        (no verdict was composed at all)
 *
 * `catalog_only_rows_present` (F-174 item 2) was AUDITED and deliberately NOT added to the
 * static floor — F-177's own shipped tests pin it as a normal, per-call-nominable flag, and
 * it fires unconditionally on every assess_* call, so statically flooring it would both
 * overturn that prior intentional decision and permanently inflate the floor's footprint —
 * the exact over-protection this audit was warned against. See the reasoning recorded beside
 * `KERNEL_FLOOR_FLAG_CODES` in response_budget.ts.
 *
 * Verified-reachable addition to `IMMUNE_HONESTY_FIELDS`:
 *   - weaknesses_empty_reason (register_p1_synthesis.ts) — a real, per-call-derived
 *     narrative in the same "_empty_reason" family as the already-immune
 *     domain_completeness_empty_reason, routinely >120 chars.
 *
 * A large set of codes/fields the plan's pre-computed inventory suggested were NOT added,
 * with the verified reason recorded inline at their definition site in response_budget.ts
 * (the codes/fields never reach a Sāra kernel or are already immune by a different, stronger
 * mechanism — see the comment blocks beside `KERNEL_FLOOR_FLAG_CODES` and
 * `IMMUNE_HONESTY_FIELDS`). This file does not re-test negatives for those — the audit
 * record documenting WHY they're absent lives in the source comments, per §0.1's "no new
 * abstractions" discipline (no parallel registry of "known-absent" codes is created here).
 */
import { describe, it, expect } from 'vitest'
import {
  assembleSaraContent,
  isProtectedKernelFlag,
  estimateBytes,
  finalizeMcpBudget,
  KERNEL_FLOOR_FLAG_CODES,
  IMMUNE_HONESTY_FIELDS,
  type SaraKernel,
  type TrimmableSection,
} from '../lib/response_budget.js'
import { judgmentFlag } from '../generated/envelope.js'

const COUNTS = { contradictions: 0, yoga_fact_ids: 0, reading_families: 0 }

/** Bulk unprotected flags + pointers, sized to force the ≤2KB kernel trim loop to run
 *  through every eligible entry before reaching a floor-protected one. */
function bulkUnprotectedFlags(n: number) {
  return Array.from({ length: n }, (_, i) =>
    judgmentFlag('bearing_yogas_no_domain_match', `filler disclosure #${i}: ` + 'x'.repeat(80), 'info'))
}
function bulkPointers(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    instrument: 'bodha_domain_reading_get',
    hint: `filler pointer #${i}: ` + 'y'.repeat(60),
  }))
}

function kernelWithTargetFlag(targetFlag: unknown): SaraKernel {
  return {
    verdict: 'A short deterministic verdict sentence.',
    flags: [targetFlag, ...bulkUnprotectedFlags(15)],
    promise: null,
    pointers: bulkPointers(15),
  } as unknown as SaraKernel
}

describe('F-179 — KERNEL_FLOOR_FLAG_CODES additions survive a forced kernel trim', () => {
  it('sanity: the fixture actually forces the trim loop to run (>2048B pre-trim)', () => {
    const kernel = kernelWithTargetFlag(judgmentFlag('significator_condition_unavailable', 'probe'))
    expect(estimateBytes(kernel)).toBeGreaterThan(2048)
  })

  it('significator_condition_unavailable survives a forced trim (static floor, no per-call nomination)', () => {
    const flag = judgmentFlag(
      'significator_condition_unavailable',
      'the D1 (rāśi) dignity/ṣaḍbala condition of this domain\'s bhāveśa, kāraka(s) and bhāva ' +
        'occupants could not be assembled this call.',
      'warning',
    )
    const kernel = kernelWithTargetFlag(flag)
    const flagsBefore = kernel.flags.length // captured BEFORE assembleSaraContent mutates kernel in place
    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    expect(assembled.kernel.flags).toContainEqual(expect.objectContaining({ code: 'significator_condition_unavailable' }))
    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
    // The bulk filler DID get cut — proof this is a real trim, not a no-op.
    expect(assembled.kernel.flags.length).toBeLessThan(flagsBefore)
  })

  it('hollow_envelope_no_data_rows survives a forced trim', () => {
    const flag = judgmentFlag(
      'hollow_envelope_no_data_rows',
      'assessment capability omitted deterministic composition data; no verdict, promise, or evidence was invented.',
    )
    const kernel = kernelWithTargetFlag(flag)
    const flagsBefore = kernel.flags.length // captured BEFORE assembleSaraContent mutates kernel in place
    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    expect(assembled.kernel.flags).toContainEqual(expect.objectContaining({ code: 'hollow_envelope_no_data_rows' }))
    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
    expect(assembled.kernel.flags.length).toBeLessThan(flagsBefore)
  })

  it('mutation-check: isProtectedKernelFlag would read false for these codes if removed from the Set (proves the assertions above are load-bearing, not incidental)', () => {
    // Directly exercises the Set membership these tests depend on — no per-call
    // protected_flags nomination is passed, so this is PURELY the static floor.
    const emptyPerCallSet = new Set<string>()
    for (const code of ['significator_condition_unavailable', 'hollow_envelope_no_data_rows']) {
      expect(KERNEL_FLOOR_FLAG_CODES.has(code)).toBe(true)
      expect(isProtectedKernelFlag(judgmentFlag(code as never, 'x'), emptyPerCallSet)).toBe(true)
    }
    // Codes deliberately NOT added (audited, left trimmable) read false — confirms the
    // matcher isn't just returning true unconditionally. `catalog_only_rows_present` in
    // particular is doctrinally important (§N.6.1) but was deliberately kept OUT of the
    // static floor — see the reasoning recorded beside KERNEL_FLOOR_FLAG_CODES.
    expect(isProtectedKernelFlag(judgmentFlag('domain_inference_requires_acharya_validation', 'x'), emptyPerCallSet)).toBe(false)
    expect(isProtectedKernelFlag(judgmentFlag('catalog_only_rows_present', 'x'), emptyPerCallSet)).toBe(false)
  })
})

describe('F-179 — IMMUNE_HONESTY_FIELDS addition: weaknesses_empty_reason survives the last-resort truncation walk', () => {
  it('sanity: weaknesses_empty_reason is a realistic >120-char narrative', () => {
    const reason = 'no event class for this chart currently carries an unsuppressed \'denied\' ' +
      'verdict: 2 denied row(s) suppressed because n_support=0 (zero corroborating evidence for ' +
      'a denial that would otherwise appear as a weakness); 1 class(es) have no evidence available.'
    expect(reason.length).toBeGreaterThan(120)
  })

  it('is registered in IMMUNE_HONESTY_FIELDS', () => {
    expect(IMMUNE_HONESTY_FIELDS.has('weaknesses_empty_reason')).toBe(true)
  })

  it('survives truncateLongStringsInPlace\'s last-resort walk even under an extreme budget', () => {
    const reason = 'no event class for this chart currently carries an unsuppressed \'denied\' ' +
      'verdict: 2 denied row(s) suppressed because n_support=0 (zero corroborating evidence for ' +
      'a denial that would otherwise appear as a weakness); 1 class(es) have no evidence available.'
    expect(reason.length).toBeGreaterThan(120)
    const content = {
      // Forces the whole pipeline past PASS1/2 (no declared sections) and past the
      // trim_report/drill_pointers degrade steps, all the way to the last-resort scalar walk.
      padding: 'p'.repeat(20_000),
      weaknesses_empty_reason: reason,
    }
    const sections: TrimmableSection<typeof content>[] = []
    const result = finalizeMcpBudget(content, { maxKb: 1, sections })
    // Sanity: the mechanism actually fired (the sacrificial padding field WAS mangled) —
    // otherwise this test would pass vacuously with nothing ever touched.
    expect(result.padding.length).toBeLessThan(20_000)
    // The real assertion: the immune field is byte-for-byte untouched.
    expect(result.weaknesses_empty_reason).toBe(reason)
  })
})
