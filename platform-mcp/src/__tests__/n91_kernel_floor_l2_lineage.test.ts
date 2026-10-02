/**
 * N-91 — assess_* has no reading_contract on the wire, so the L2 lineage flag reaches the caller
 * ONLY in the Sāra kernel's `flags`. The 2 KB kernel trim must never drop it: both lineage codes are
 * in KERNEL_FLOOR_FLAG_CODES (same shape as f179_kernel_floor_flag_and_immune_field_additions.test.ts).
 */
import { describe, it, expect } from 'vitest'
import {
  assembleSaraContent,
  isProtectedKernelFlag,
  estimateBytes,
  KERNEL_FLOOR_FLAG_CODES,
  type SaraKernel,
} from '../lib/response_budget.js'
import { judgmentFlag } from '../generated/envelope.js'

const COUNTS = { contradictions: 0, yoga_fact_ids: 0, reading_families: 0 }
const bulkFlags = (n: number) => Array.from({ length: n }, (_, i) =>
  judgmentFlag('bearing_yogas_no_domain_match', `filler disclosure #${i}: ` + 'x'.repeat(80), 'info'))
const bulkPointers = (n: number) => Array.from({ length: n }, (_, i) => ({
  instrument: 'bodha_domain_reading_get', hint: `filler pointer #${i}: ` + 'y'.repeat(60),
}))
const kernelWith = (target: unknown): SaraKernel => ({
  verdict: 'A short deterministic verdict sentence.',
  // target LAST: a tail-first trim reaches it first unless it is floor-protected
  flags: [...bulkFlags(15), target],
  promise: null,
  pointers: bulkPointers(15),
} as unknown as SaraKernel)

const FLAGS = [
  judgmentFlag('l2_receipts_predate_l1', 'bo_laksana built against pre-rebuild ga_structural', 'warning'),
  judgmentFlag('l2_lineage_check_failed', 'lineage check could not run', 'warning'),
]

describe('N-91 — lineage flags survive a forced kernel trim (static floor)', () => {
  it('sanity: the fixture forces the trim loop (>2048B pre-trim)', () => {
    expect(estimateBytes(kernelWith(FLAGS[0]))).toBeGreaterThan(2048)
  })

  it.each(FLAGS.map(f => [f.code, f] as const))('%s survives the ≤2KB kernel trim', (code, flag) => {
    const kernel = kernelWith(flag)
    const before = kernel.flags.length // captured BEFORE assembleSaraContent mutates the kernel in place
    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    expect(assembled.kernel.flags).toContainEqual(expect.objectContaining({ code }))
    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
    expect(assembled.kernel.flags.length).toBeLessThan(before) // the filler really was cut
  })

  it('both codes are static members of KERNEL_FLOOR_FLAG_CODES (no per-call nomination needed)', () => {
    for (const code of ['l2_receipts_predate_l1', 'l2_lineage_check_failed']) {
      expect(KERNEL_FLOOR_FLAG_CODES.has(code)).toBe(true)
      expect(isProtectedKernelFlag(judgmentFlag(code as never, 'x'), new Set<string>())).toBe(true)
    }
    // the matcher is not unconditionally true
    expect(isProtectedKernelFlag(judgmentFlag('domain_inference_requires_acharya_validation', 'x'), new Set<string>())).toBe(false)
  })
})
