/**
 * f181_kernel_ceiling_exceeded_disclosure.test.ts — PARIŚEṢA-V4 finding F-181.
 *
 * DEFECT. `assembleSaraContent`'s ≤2KB kernel trim loop can legitimately exit while the
 * kernel is STILL over `KERNEL_MAX_BYTES` — every eligible (unprotected) pointer and flag is
 * already gone, and what remains (verdict, promise, and any `KERNEL_FLOOR_FLAG_CODES`-floored
 * flag) is, by design, never deleted to force a fit. Before this fix, that condition was
 * silently unreported: `composition_report.kernel_bytes` recorded the true (over-ceiling)
 * size, but nothing in `kernel.flags` told a caller that the kernel's OWN 2KB invariant —
 * distinct from the whole-envelope `budget_exceeded_after_trim` signal, which is checked at
 * a different seam (registry_bridge.ts's buildAssessResponse, AFTER assembleSaraContent
 * returns) — had been breached.
 *
 * FIX. `assembleSaraContent` now emits `judgmentFlag('kernel_ceiling_exceeded_for_disclosure')`
 * into `kernel.flags`, immediately after the trim loop and before `composition_report` is
 * built, guarded on `estimateBytes(kernel) > KERNEL_MAX_BYTES`. The code is registered in
 * `JUDGMENT_FLAG_CODES` (both `platform/src/lib/retrieval/envelope.ts` and its generated
 * mirror) and in `KERNEL_FLOOR_FLAG_CODES` itself, so it can never be evicted by a later trim.
 */
import { describe, it, expect } from 'vitest'
import {
  assembleSaraContent,
  estimateBytes,
  KERNEL_FLOOR_FLAG_CODES,
  type SaraKernel,
} from '../lib/response_budget.js'
import { judgmentFlag, isJudgmentFlagCode } from '../generated/envelope.js'

const COUNTS = { contradictions: 0, yoga_fact_ids: 0, reading_families: 0 }

function findFlag(flags: unknown[], code: string) {
  return flags.find(f => typeof f === 'object' && f !== null && (f as { code?: string }).code === code)
}

describe('F-181 — kernel_ceiling_exceeded_for_disclosure', () => {
  it('is a registered closed-vocabulary code', () => {
    expect(isJudgmentFlagCode('kernel_ceiling_exceeded_for_disclosure')).toBe(true)
  })

  it('is itself floor-protected (cannot be evicted by a later trim)', () => {
    expect(KERNEL_FLOOR_FLAG_CODES.has('kernel_ceiling_exceeded_for_disclosure')).toBe(true)
  })

  it('POSITIVE: a protected-flags-only kernel exceeding 2048B emits the flag, and composition_report.kernel_bytes > 2048', () => {
    // Two floor-protected disclosures alone exceed 2048B — the trim loop cannot touch
    // either (no per-call nomination needed; both are in the static KERNEL_FLOOR_FLAG_CODES
    // set), so it exits with the kernel still over the ceiling.
    const long = (n: number) => judgmentFlag(
      'significator_condition_unavailable',
      `disclosure-${n}: ` + 'x'.repeat(1200),
      'warning',
    )
    const kernel: SaraKernel = {
      verdict: 'v',
      flags: [long(1), long(2)],
      promise: null,
      pointers: [],
    } as unknown as SaraKernel
    expect(estimateBytes(kernel)).toBeGreaterThan(2048) // sanity: genuinely irreducible

    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })

    const flag = findFlag(assembled.kernel.flags, 'kernel_ceiling_exceeded_for_disclosure')
    expect(flag).toBeDefined()
    expect(assembled.composition_report.kernel_bytes).toBeGreaterThan(2048)
    // Honesty invariant: composition_report always reports the TRUE post-trim size.
    expect(assembled.composition_report.kernel_bytes).toBe(estimateBytes(assembled.kernel))
    // Neither original protected disclosure was sacrificed to hide the overage.
    expect(findFlag(assembled.kernel.flags, 'significator_condition_unavailable')).toBeDefined()
  })

  it('NEGATIVE CONTROL: a kernel that fits under 2048B after trimming never emits the flag', () => {
    const kernel: SaraKernel = {
      verdict: 'A short deterministic verdict sentence.',
      flags: [judgmentFlag('bearing_yogas_no_domain_match', 'a short, ordinary disclosure.', 'info')],
      promise: null,
      pointers: [{ instrument: 'bodha_domain_reading_get', hint: 'marsys://tool/L2/query_domain_reading' }],
    } as unknown as SaraKernel
    expect(estimateBytes(kernel)).toBeLessThanOrEqual(2048)

    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })

    expect(findFlag(assembled.kernel.flags, 'kernel_ceiling_exceeded_for_disclosure')).toBeUndefined()
    expect(assembled.composition_report.kernel_bytes).toBeLessThanOrEqual(2048)
  })

  it('NEGATIVE CONTROL: a kernel that overflows pre-trim but is successfully brought under 2048B by trimming eligible pointers/flags never emits the flag', () => {
    const kernel: SaraKernel = {
      verdict: 'A short deterministic verdict sentence.',
      flags: [
        judgmentFlag('significator_condition_unavailable', 'the protected disclosure.', 'warning'),
        ...Array.from({ length: 10 }, (_, i) =>
          judgmentFlag('bearing_yogas_no_domain_match', `filler #${i}: ` + 'x'.repeat(80), 'info')),
      ],
      promise: null,
      pointers: Array.from({ length: 10 }, (_, i) => ({
        instrument: 'bodha_domain_reading_get',
        hint: `filler pointer #${i}: ` + 'y'.repeat(60),
      })),
    } as unknown as SaraKernel
    expect(estimateBytes(kernel)).toBeGreaterThan(2048) // sanity: pre-trim it IS over budget

    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })

    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
    expect(findFlag(assembled.kernel.flags, 'kernel_ceiling_exceeded_for_disclosure')).toBeUndefined()
    // The protected disclosure survived; the filler was what absorbed the cut.
    expect(findFlag(assembled.kernel.flags, 'significator_condition_unavailable')).toBeDefined()
  })

  it('mutation-check: the emission is exactly gated on estimateBytes(kernel) > KERNEL_MAX_BYTES, not on trimming having occurred at all', () => {
    // A kernel with ZERO pointers/flags to trim, but whose verdict ALONE exceeds 2048B —
    // the trim loop's own break condition (line "pointers.length === 0 && eligibleFlagCount
    // === 0") fires on the FIRST iteration, yet the ceiling disclosure must still fire.
    const kernel: SaraKernel = {
      verdict: 'v'.repeat(2200),
      flags: [],
      promise: null,
      pointers: [],
    } as unknown as SaraKernel
    expect(estimateBytes(kernel)).toBeGreaterThan(2048)

    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    expect(findFlag(assembled.kernel.flags, 'kernel_ceiling_exceeded_for_disclosure')).toBeDefined()
  })
})
