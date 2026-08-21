/**
 * f174_empty_reason_clamp.test.ts — PARIŚEṢA-V4 finding F-174.
 *
 * DEFECT. `attachDomainCompleteness` (registry_bridge.ts) interpolates a caught error's raw
 * `.message` verbatim into `domain_completeness_empty_reason` with no length bound and no
 * sanitization. Two sites: the `runDossier` re-call's own `diag.error.message` (~838-842),
 * and the outer catch's `String(e instanceof Error ? e.message : e)` (~844-852).
 *
 * WHY IT IS DANGEROUS (the eviction chain, per the F-174 plan record).
 * `domain_completeness_empty_reason` is in `IMMUNE_HONESTY_FIELDS` (response_budget.ts) — the
 * budget trimmer never string-truncates it and never auto-declares it trimmable. registry_bridge
 * mirrors the same string into `kernel.flags` AND nominates it via `protected_flags`
 * (F-177). `assembleSaraContent`'s ≤2KB kernel trim removes pointers and unprotected flags
 * first, protected flags only after those are exhausted, and stops once
 * `pointers.length === 0 && eligibleFlagCount === 0` — never deleting a protected flag. So an
 * arbitrarily long, protected error string starves the trim loop of anything else to cut,
 * consuming the entire byte budget and evicting every drill pointer
 * (`bodha_domain_reading_get` / `kala_windows_get` / `bodha_graph_traverse_get`) and every
 * unprotected flag before the kernel is forced to just exceed the ceiling. A raw error message
 * containing newlines/JSON also corrupts the `code:detail` shape `flagCodeOf` parses via
 * `split(':')[0]`.
 *
 * FIX. `clampErrorForDisclosure` (registry_bridge.ts) strips newlines/control chars, collapses
 * whitespace, and clamps to 200 chars (same bound as the existing precedent,
 * `kala_views/explain.ts:359`), appending `…[truncated]` when the clamp actually fires. Both
 * interpolation sites now route through it.
 *
 * These tests (1) force the dossier query to throw with a 10KB message and assert the SERVED
 * `domain_completeness_empty_reason` is bounded and sanitized, and (2) reconstruct the exact
 * kernel-mirroring + protected-flag mechanism `buildAssessResponse` uses (F-177) to prove all
 * 3 drill pointers survive when fed the real (clamped) message — and, by contrast, do NOT
 * survive when fed a raw unbounded message, which is the real failure mode this finding closes.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import type { SaraKernel } from '../lib/response_budget.js'

// `handler`, when set, intercepts runDossier; otherwise the real implementation runs.
const hoisted = vi.hoisted(() => ({
  handler: null as null | (() => never),
}))

vi.mock('../tools/dossier.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../tools/dossier.js')>()
  return {
    ...actual,
    runDossier: (args: never) =>
      hoisted.handler ? hoisted.handler() : actual.runDossier(args),
  }
})

const { attachDomainCompleteness } = await import('../tools/registry_bridge.js')
const { assembleSaraContent } = await import('../lib/response_budget.js')
const { judgmentFlag } = await import('../generated/envelope.js')

const CANON = '482012f1-710e-4a25-994a-93821f5871aa'

// A 10KB error message, deliberately shaped to also exercise the sanitize half of the fix:
// embedded newlines, a JSON-looking fragment, and control characters — exactly the shape that
// would corrupt the `code:detail` flag string `flagCodeOf` parses via `split(':')[0]`.
function tenKbHostileMessage(): string {
  const jsonish = '{"stack":"at foo\\n at bar"}\r\n\t'
  const filler = 'x'.repeat(200) + '\n'
  let msg = 'dossier query threw: ' + jsonish
  while (Buffer.byteLength(msg, 'utf8') < 10 * 1024) msg += filler
  return msg
}

afterEach(() => {
  hoisted.handler = null
  vi.restoreAllMocks()
})

describe('F-174 — domain_completeness_empty_reason is bounded and sanitized', () => {
  it('outer-catch path (runDossier throws): served message is clamped, sanitized, marked', () => {
    hoisted.handler = () => { throw new Error(tenKbHostileMessage()) }

    const response: Record<string, unknown> = {}
    attachDomainCompleteness(response, 'health', CANON)

    const served = response['domain_completeness_empty_reason']
    expect(typeof served).toBe('string')
    const msg = served as string

    // Bounded: 200-char clamp + the truncation marker, plus the fixed surrounding prose —
    // nowhere near the original 10KB.
    expect(msg.length).toBeLessThan(500)
    expect(Buffer.byteLength(msg, 'utf8')).toBeLessThan(1024)

    // Sanitized: no raw newlines/control chars survive into the interpolated segment.
    expect(msg).not.toMatch(/[\r\n\t\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/)

    // Truncation is disclosed, not silent (this message was long enough to clamp).
    expect(msg).toContain('…[truncated]')

    // The surrounding honest-disclosure prose is preserved verbatim.
    expect(msg).toContain("This IS a query failure: the dossier query threw:")
  })

  it('a short error message is NOT falsely marked as truncated', () => {
    hoisted.handler = () => { throw new Error('short failure') }

    const response: Record<string, unknown> = {}
    attachDomainCompleteness(response, 'wealth', CANON)

    const msg = response['domain_completeness_empty_reason'] as string
    expect(msg).toContain('short failure')
    expect(msg).not.toContain('…[truncated]')
  })
})

const LIVE_POINTERS = [
  { instrument: 'bodha_domain_reading_get', hint: 'marsys://tool/L2/query_domain_reading' },
  { instrument: 'kala_windows_get', hint: 'marsys://tool/L3/query_temporal_activation' },
  { instrument: 'bodha_graph_traverse_get', hint: 'mode:"contradictions" — marsys://tool/L2/traverse_chart_graph' },
]

/** Reconstructs the exact registry_bridge mechanism (F-177): the empty_reason is mirrored into
 *  `kernel.flags` and nominated via `protected_flags`, alongside a realistic dense
 *  assess_health-shaped kernel and the 3 declared drill pointers, then run through the real
 *  `assembleSaraContent` budget trim. */
function assembleWithEmptyReason(emptyReasonMsg: string) {
  const kernel: SaraKernel = {
    verdict:
      'Health / Vitality assessment draws on 10 composite-ranked signal(s) for this chart, cross-referenced ' +
      'against classical yoga firings, varga placements, contradictions, and dasha timing below. Significator ' +
      'condition (D1): Sun (kāraka) is neutral in Capricorn (10th house) — ṣaḍbala 8.47, rank 1/9. 13 yoga(s) ' +
      'fired on this chart overall, but none name only this domain\'s bhāveśa/kāraka(s) — shown for context, ' +
      'not domain-confirmed.',
    flags: [
      judgmentFlag(
        'domain_inference_requires_acharya_validation',
        'Health domain synthesis reconciles 1st/6th/8th lords + Sun kāraka from L1 chart_facts (via drill). ' +
        'Affliction assessment and maraka timing require acharya review of the assembled bundle.',
        'warning',
      ),
      judgmentFlag(
        'bearing_yogas_no_domain_match',
        '13 yoga(s) fired on this chart but none name only this domain\'s bhāveśa/kāraka(s) — shown for context.',
        'info',
      ),
      emptyReasonMsg,
    ],
    promise: null,
    pointers: LIVE_POINTERS.map(p => ({ ...p })),
  } as unknown as SaraKernel

  return assembleSaraContent({
    kernel,
    budget_kb: 40,
    counts: { contradictions: 0, yoga_fact_ids: 0, reading_families: 12 },
    protected_flags: [emptyReasonMsg],
  })
}

describe('F-174 — the real (clamped) empty_reason does not evict the drill pointers', () => {
  it('closes the finding: served (clamped) message + protected mirroring ⇒ all 3 pointers survive', () => {
    hoisted.handler = () => { throw new Error(tenKbHostileMessage()) }
    const response: Record<string, unknown> = {}
    attachDomainCompleteness(response, 'health', CANON)
    const servedMsg = response['domain_completeness_empty_reason'] as string

    const assembled = assembleWithEmptyReason(servedMsg)

    expect(assembled.kernel.pointers).toHaveLength(3)
    for (const p of LIVE_POINTERS) {
      expect(assembled.kernel.pointers).toContainEqual(expect.objectContaining({ instrument: p.instrument }))
    }
    // The disclosure itself is not silently dropped either.
    expect(assembled.kernel.flags).toContain(servedMsg)
  })

  it('reproduces the pre-fix failure mode: an UNBOUNDED error string evicts the pointers', () => {
    // This is what `emptyReasonMsg` would have been WITHOUT clampErrorForDisclosure — the raw,
    // unbounded, unsanitized error text — mirrored + protected exactly the same way. Proves the
    // eviction chain the finding describes is real, and that the fix (bounding the served
    // message) is what closes it.
    const unboundedMsg =
      "No domain_completeness/completeness_directive block was assembled for domain='health' — " +
      'honestly omitted rather than fabricated (B.10). This IS a query failure: the dossier query ' +
      `threw: ${tenKbHostileMessage()}.`

    const assembled = assembleWithEmptyReason(unboundedMsg)

    // The protected disclosure itself survives (that's the whole point of protected_flags) —
    // but it alone blows the 2KB kernel ceiling, starving the trim of anything else to cut,
    // so the pointers (and the other unprotected flags) are gone.
    expect(assembled.kernel.pointers.length).toBeLessThan(3)
  })
})
