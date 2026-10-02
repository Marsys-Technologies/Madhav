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

describe('N-91 — WORST CASE (S-L1: all 8 L2 assets stale) fits the 2 KB assess kernel without evicting other disclosures', () => {
  // The exact worst-case served detail of l2LineageFlag (platform l2_lineage.test.ts pins <= 300 B).
  const WORST = '8 L2 asset(s) (bo_arudha, bo_grounding, bo_karanajala +5 more) were built before 18 L1 asset(s) were rebuilt; cited fact_ids may not resolve until L2 is rebuilt.'
  const verdict = 'Career / Vocation assessment draws on 10 composite-ranked signal(s) for this chart, cross-referenced against classical yoga firings, varga placements, contradictions, and dasha timing below. ' +
    'Significator condition (D1): Saturn, the 10th bhaveshas, is exalted in Libra at 7.83 deg; the 10th bhava is occupied by Mercury. ' +
    '3 classical yoga(s) fire for this domain. D10 places the 10th lord in own sign. No domain contradictions were found; 3 chart-wide contradictions exist. A promise-bearing dasha window is active now through 2031.'

  it('sanity: the realistic verdict is ~600-700 B and the worst-case flag detail is within the 300 B cap', () => {
    expect(Buffer.byteLength(WORST, 'utf8')).toBeLessThanOrEqual(300)
    expect(Buffer.byteLength(verdict, 'utf8')).toBeGreaterThan(500)
  })

  it('kernel stays <= 2048 B, the lineage flag survives, no kernel_ceiling_exceeded_for_disclosure, other floor disclosures kept', () => {
    const lineage = judgmentFlag('l2_receipts_predate_l1', WORST, 'warning')
    const kernel = {
      verdict,
      flags: [
        judgmentFlag('domain_inference_requires_acharya_validation', 'Domain-level inference from classical sources requires acharya validation before it is treated as a prediction.', 'warning'),
        judgmentFlag('catalog_only_rows_present', 'catalog-only yoga rows are counted separately from confirmed firings; see ganita_yoga_firings_get.', 'info'),
        judgmentFlag('significator_condition_unavailable', 'the D1 dignity/shadbala condition of one occupant could not be assembled this call.', 'warning'),
        lineage,
      ],
      promise: null,
      pointers: bulkPointers(6),
    } as unknown as SaraKernel
    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    const codes = (assembled.kernel.flags as Array<{ code?: string }>).map(f => f.code)
    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
    expect(codes).toContain('l2_receipts_predate_l1')
    expect(codes).toContain('significator_condition_unavailable') // another floor disclosure is not evicted
    expect(codes).not.toContain('kernel_ceiling_exceeded_for_disclosure')
  })

  it('CONTROL: the previous ~1.6 KB detail WOULD breach the ceiling (this test is sensitive to detail size)', () => {
    const fat = judgmentFlag('l2_receipts_predate_l1', 'x'.repeat(1600), 'warning')
    const kernel = { verdict, flags: [fat], promise: null, pointers: bulkPointers(6) } as unknown as SaraKernel
    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    expect((assembled.kernel.flags as Array<{ code?: string }>).map(f => f.code)).toContain('kernel_ceiling_exceeded_for_disclosure')
  })
})
