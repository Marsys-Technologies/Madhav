/**
 * f177_kernel_flag_disclosure_protection.test.ts — PARIŚEṢA-V4 finding F-177.
 *
 * DEFECT. `assembleSaraContent`'s ≤2KB kernel-invariant trim loop dropped `kernel.flags`
 * entries from the TAIL of the array. That is position-based, not priority-based: the LAST
 * flag pushed is the FIRST one deleted. PR #1382 mirrors `domain_completeness_empty_reason`
 * (the disclosure telling a caller a domain's `grounding` was dropped all-or-nothing) into
 * `kernel.flags` precisely so the disclosure survives budget pressure — but pushes it LAST.
 * On any real built chart dense enough to reach the cap it was therefore the first entry
 * deleted. Because #1382 also made the older `domain_slice_not_configured` flag permanently
 * unreachable (gated on `!hasAttachedReading`, and a `reading` is now always attached), a
 * caller received NEITHER disclosure — the exact outcome #1382's own GA-5 review comment
 * claimed to prevent.
 *
 * LIVE BASELINE (chart 482012f1, 2026-08-21, pre-fix, via the deployed MCP surface):
 * `assess_health` verbosity:'concise' and 'detailed' and `assess_marriage` verbosity:
 * 'detailed' each returned only 2 of the 3 pointers `buildAssessResponse` declares — proof
 * the trim loop actually ran — and no `domain_completeness_empty_reason` entry in
 * `kernel.flags`. The fixtures below reconstruct that observed shape: the real 3-flag
 * assess_health kernel, the real 3 pointers, an oversized verdict, and the empty_reason
 * mirrored last.
 *
 * FIX. `assembleSaraContent` accepts `protected_flags`; nominated flags are trimmed only
 * after every unprotected flag and every pointer is gone, and if only protected flags remain
 * the trim STOPS rather than delete an honesty disclosure. Same ranking `IMMUNE_HONESTY_FIELDS`
 * gives scalar honesty fields and `hardFloor` gives dense array sections (CLAUDE.md §N.6.2).
 */
import { describe, it, expect } from 'vitest'
import { assembleSaraContent, isProtectedKernelFlag, estimateBytes, type SaraKernel } from '../lib/response_budget.js'
import { judgmentFlag } from '../generated/envelope.js'

// The real disclosure text shape (observed on a sparser chart where it survived the trim).
const EMPTY_REASON = 'No precompiled health concept-slice bundle exists yet for this domain; ' +
  'the completeness accounting below is therefore absent rather than empty.'

// Verbatim from the live pre-fix assess_health kernel on chart 482012f1 (3 flags).
function liveAssessHealthFlags() {
  return [
    judgmentFlag(
      'domain_inference_requires_acharya_validation',
      'Health domain synthesis reconciles 1st/6th/8th lords + Sun kāraka from L1 chart_facts (via drill). ' +
      'Affliction assessment and maraka timing require acharya review of the assembled bundle.',
      'warning',
    ),
    judgmentFlag(
      'bearing_yogas_no_domain_match',
      '13 yoga(s) fired on this chart but none name only this domain\'s bhāveśa/kāraka(s) — shown for context (Y-2, D-1.6/S-3).',
      'info',
    ),
    judgmentFlag(
      'catalog_only_rows_present',
      'bearing_yoga_firings (ga_yoga_firings) is the firings-authoritative source; by_stage.yoga / ' +
      'verdict_skeleton.by_stage.yoga (bodha_msr_signals) are single-pass catalog-label matches (JL-004) ' +
      'and must never be read as confirmed findings (CLAUDE.md §N.6.1).',
      'info',
    ),
  ]
}

// The 3 pointers buildAssessResponse declares. NOTE: `instrument` values must name
// ALREADY-REGISTERED live MCP tools — the CI boot-time pointer validator
// (platform/scripts/audit/tap/sc_pointer_validation.ts, SC-17/18/19) statically scans every
// `instrument: '<literal>'` in the repo, test fixtures included.
function livePointers() {
  return [
    { instrument: 'bodha_domain_reading_get', hint: 'marsys://tool/L2/query_domain_reading' },
    { instrument: 'kala_windows_get', hint: 'marsys://tool/L3/query_temporal_activation' },
    { instrument: 'bodha_graph_traverse_get', hint: 'mode:"contradictions" — marsys://tool/L2/traverse_chart_graph' },
  ]
}

/** A dense assess_health-shaped kernel whose serialized size exceeds KERNEL_MAX_BYTES (2048),
 *  with the empty_reason disclosure mirrored LAST exactly as registry_bridge pushes it. */
function denseKernel(): SaraKernel {
  return {
    verdict:
      'Health / Vitality assessment draws on 10 composite-ranked signal(s) for this chart, cross-referenced ' +
      'against classical yoga firings, varga placements, contradictions, and dasha timing below. Significator ' +
      'condition (D1): Sun (kāraka) is neutral in Capricorn (10th house) — ṣaḍbala 8.47, rank 1/9. 13 yoga(s) ' +
      'fired on this chart overall, but none name only this domain\'s bhāveśa/kāraka(s) — shown for context, ' +
      'not domain-confirmed. Ṣaṣṭhāṃśa (D6) placements were consumed directly from L1 to confirm this domain\'s ' +
      'operative-varga promise (see varga_analysis.per_varga for per-graha dignity and, where computed, ' +
      'per-varga Ashtakavarga). 1 domain-tagged tension(s) surfaced for this domain (of 3 chart-wide) — see ' +
      'contradictions for the adjudication detail. A dated daśā-activation window is available for this ' +
      'domain\'s signals — see activating_dasha for the exact bounds.',
    flags: [...liveAssessHealthFlags(), EMPTY_REASON],
    promise: null,
    pointers: livePointers(),
  } as unknown as SaraKernel
}

const COUNTS = { contradictions: 0, yoga_fact_ids: 0, reading_families: 12 }

describe('F-177 — the kernel trim must not delete the domain-completeness disclosure', () => {
  it('reproduces the pre-fix baseline: the fixture IS dense enough to trigger the 2KB trim', () => {
    // Guards against every assertion below silently passing because nothing was ever trimmed.
    const kernel = denseKernel()
    const flagsBefore = kernel.flags.length
    const pointersBefore = kernel.pointers.length
    expect(estimateBytes(kernel)).toBeGreaterThan(2048)

    const assembled = assembleSaraContent({ kernel, budget_kb: 40, counts: COUNTS })
    // Entries were actually cut, and the ceiling was reached. (Which list absorbs the cut is
    // fixture-dependent — the live chart-482012f1 responses lost a pointer AND a flag because
    // their real kernels were larger still; this fixture only needs to prove the loop runs.)
    const entriesBefore = flagsBefore + pointersBefore
    const entriesAfter = assembled.kernel.flags.length + assembled.kernel.pointers.length
    expect(entriesAfter).toBeLessThan(entriesBefore)
    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
  })

  it('WITHOUT protected_flags the disclosure is dropped (the F-177 defect, pinned)', () => {
    const assembled = assembleSaraContent({ kernel: denseKernel(), budget_kb: 40, counts: COUNTS })
    expect(assembled.kernel.flags).not.toContain(EMPTY_REASON)
  })

  it('WITH protected_flags the disclosure survives the trim', () => {
    const assembled = assembleSaraContent({
      kernel: denseKernel(),
      budget_kb: 40,
      counts: COUNTS,
      protected_flags: [EMPTY_REASON],
    })
    expect(assembled.kernel.flags).toContain(EMPTY_REASON)
  })

  it('protection is positional-independent: a flag pushed AFTER the disclosure cannot displace it', () => {
    // registry_bridge pushes `hollow_envelope_no_data_rows` / `budget_exceeded_after_trim`
    // after the mirror. Ordering-only protection would regress here; explicit protection does not.
    const kernel = denseKernel()
    kernel.flags.push(judgmentFlag(
      'hollow_envelope_no_data_rows',
      'assessment capability omitted deterministic composition data; no verdict, promise, or evidence was invented.',
    ))
    const assembled = assembleSaraContent({
      kernel, budget_kb: 40, counts: COUNTS, protected_flags: [EMPTY_REASON],
    })
    expect(assembled.kernel.flags).toContain(EMPTY_REASON)
  })

  it('trimming is NOT disabled: genuinely lower-priority flags are still cut to meet the ceiling', () => {
    const kernel = denseKernel()
    const before = kernel.flags.length
    const assembled = assembleSaraContent({
      kernel, budget_kb: 40, counts: COUNTS, protected_flags: [EMPTY_REASON],
    })
    // Unprotected flags absorbed the cut instead.
    expect(assembled.kernel.flags.length).toBeLessThan(before)
    expect(assembled.kernel.flags).not.toContainEqual(
      expect.objectContaining({ code: 'catalog_only_rows_present' }),
    )
    // And the ceiling was actually respected once the protected entry fits.
    expect(estimateBytes(assembled.kernel)).toBeLessThanOrEqual(2048)
  })

  it('honesty beats the byte cap: an irreducible protected-only kernel is not silently gutted', () => {
    // Two protected disclosures alone exceed 2KB. The trim must STOP, not delete a disclosure.
    const long = (n: number) => `disclosure-${n}: ` + 'x'.repeat(1200)
    const kernel = {
      verdict: 'v', flags: [long(1), long(2)], promise: null, pointers: [],
    } as unknown as SaraKernel
    const assembled = assembleSaraContent({
      kernel, budget_kb: 40, counts: COUNTS, protected_flags: [long(1), long(2)],
    })
    // F-181 (post-dates this test): assembleSaraContent now ALSO appends
    // `kernel_ceiling_exceeded_for_disclosure` whenever the kernel is still over its own
    // ceiling after the trim loop — exactly this scenario — so the two original protected
    // disclosures are joined by that third, itself-floor-protected flag, not silently gutted
    // down to 2. Both original disclosures must still be present.
    expect(assembled.kernel.flags).toHaveLength(3)
    expect(assembled.kernel.flags).toContain(long(1))
    expect(assembled.kernel.flags).toContain(long(2))
    expect(assembled.kernel.flags).toContainEqual(
      expect.objectContaining({ code: 'kernel_ceiling_exceeded_for_disclosure' }),
    )
    expect(estimateBytes(assembled.kernel)).toBeGreaterThan(2048)
    // composition_report stays honest about the real post-trim size.
    expect(assembled.composition_report.kernel_bytes).toBe(estimateBytes(assembled.kernel))
  })

  it('pointer/flag alternation is not skewed by protected entries', () => {
    // A protected flag must not inflate the flag count and cause pointers to be over-cut.
    const kernel = denseKernel()
    const withProtection = assembleSaraContent({
      kernel, budget_kb: 40, counts: COUNTS, protected_flags: [EMPTY_REASON],
    })
    expect(withProtection.kernel.pointers.length).toBeGreaterThan(0)
  })
})

describe('F-177 — isProtectedKernelFlag matching', () => {
  it('matches string flags by exact value', () => {
    expect(isProtectedKernelFlag(EMPTY_REASON, new Set([EMPTY_REASON]))).toBe(true)
    expect(isProtectedKernelFlag('something else', new Set([EMPTY_REASON]))).toBe(false)
  })

  it('matches object flags by closed-vocabulary code', () => {
    const flag = judgmentFlag('catalog_only_rows_present', 'detail')
    expect(isProtectedKernelFlag(flag, new Set(['catalog_only_rows_present']))).toBe(true)
    expect(isProtectedKernelFlag(flag, new Set(['bearing_yogas_no_domain_match']))).toBe(false)
  })

  it('an empty protected set protects nothing (default behavior unchanged)', () => {
    expect(isProtectedKernelFlag(EMPTY_REASON, new Set())).toBe(false)
  })
})
