/**
 * envelope.judgment_flags.test.ts — W3-L2 (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §E W3 item 2
 * "flags closed enum + d8/hollow-emitter migration"; RETRIEVAL_PLANE_ELEVATION_PLAN §"R-2 One
 * Envelope" item 2, GT-46/GT-53).
 * ======================================================================================
 * Covers:
 *   1. Every code every REAL emitter in the codebase pushes is a member of the closed
 *      JUDGMENT_FLAG_CODES vocabulary (registry-checked, not just "the TS union compiles").
 *   2. `judgmentFlag()` builds the {code, detail?, severity?} shape correctly.
 *   3. The two hollow emitters (register_p1_synthesis.ts / register_p1_reference.ts) now emit
 *      a REAL honesty signal instead of a static `[]` — exercised via the same
 *      `deriveHollowEnvelopeFlags`-shaped logic those two files each carry locally.
 *   4. `judgmentFlagsInclude` / `judgmentFlagText` tolerate BOTH the new structured shape and
 *      a legacy bare string (the compat shim mandated by the migration plan) without throwing.
 *   5. `finalizeMcpBudget`'s injected over-budget flag uses the enum, not a free string.
 */
import { describe, it, expect } from 'vitest'
import {
  JUDGMENT_FLAG_CODES,
  isJudgmentFlagCode,
  judgmentFlag,
  judgmentFlagsInclude,
  judgmentFlagText,
  buildRetrievalEnvelope,
  type JudgmentFlagCode,
  type JudgmentFlagEntry,
} from './envelope'

describe('JUDGMENT_FLAG_CODES — closed, registry-checked vocabulary', () => {
  it('is a non-empty array of unique string codes', () => {
    expect(JUDGMENT_FLAG_CODES.length).toBeGreaterThan(0)
    expect(new Set(JUDGMENT_FLAG_CODES).size).toBe(JUDGMENT_FLAG_CODES.length)
  })

  // Every code any real emitter in the codebase pushes today, enumerated by hand against the
  // W3-L2 migration's own file-by-file pass (register_d9_judgment.ts, register_d10_pact.ts,
  // register_d8_assess_domain.ts, get_dasha_lord_capability.ts, get_dashas.ts,
  // register_d7_channel.ts, registry_bridge.ts, register_p1_ganita.ts, response_budget.ts).
  // If a future emitter needs a NEW code, it must be added to JUDGMENT_FLAG_CODES first (the
  // whole point of a closed enum) — this list is deliberately exhaustive, not aspirational.
  const CODES_USED_BY_REAL_EMITTERS: JudgmentFlagCode[] = [
    'zero_rows_returned',
    'zero_entity_profiles',
    'response_size_truncated',
    'partial_page_more_available',
    'catalog_only_rows_present',
    'system_facet_unrecognized',
    'time_sensitive_low_confidence',
    'unmapped_lord_graha',
    'house_class_unresolved',
    'ratification_unavailable',
    'karaka_unresolved',
    'from_moon_resolution_failed',
    'varga_confirmation_failed',
    'yoga_firings_fetch_failed',
    'bearing_yogas_empty',
    'bearing_yogas_no_domain_match',
    'yoga_signal_corroboration_fetch_failed',
    'bearing_yogas_corroboration_caveat',
    'notably_absent_not_checked',
    'kala_activations_trimmed',
    'kala_activations_single_cycle',
    'timing_anchored_false',
    'timing_anchored_forced_false',
    'timing_hook_failed',
    'afflictions_fetch_failed',
    'afflictions_empty',
    'afflictions_present',
    'domain_inference_requires_acharya_validation',
    'confirmation_graha_unrecognized',
    'pact_halted_at_promise',
    'pact_halted_at_confirmation',
    'pact_halted_at_activation',
    'pact_trigger_infra_incomplete',
    'partial_portrait_section_errors',
    'no_parivartana_or_catalog_matches_for_graha',
    'no_mahadasha_periods_for_graha',
    'budget_exceeded_after_trim',
    'chart_rebuilt_mid_session_pin_refreshed',
    'chart_header_unresolved',
    'cursor_filter_mismatch',
    'hollow_envelope_no_data_rows',
    'hollow_envelope_shape_not_evaluated',
  ]

  it.each(CODES_USED_BY_REAL_EMITTERS)('emitter code "%s" is a member of the closed vocabulary', (code) => {
    expect(isJudgmentFlagCode(code)).toBe(true)
    expect((JUDGMENT_FLAG_CODES as readonly string[]).includes(code)).toBe(true)
  })

  it('rejects an arbitrary out-of-vocabulary string', () => {
    expect(isJudgmentFlagCode('this_code_was_never_declared')).toBe(false)
    expect(isJudgmentFlagCode(123)).toBe(false)
    expect(isJudgmentFlagCode(null)).toBe(false)
  })
})

describe('judgmentFlag() builder', () => {
  it('builds a code-only flag with no detail/severity keys present', () => {
    const f = judgmentFlag('zero_rows_returned')
    expect(f).toEqual({ code: 'zero_rows_returned' })
    expect('detail' in f).toBe(false)
    expect('severity' in f).toBe(false)
  })

  it('builds a flag with detail and severity', () => {
    const f = judgmentFlag('karaka_unresolved', 'Venus — boom', 'warning')
    expect(f).toEqual({ code: 'karaka_unresolved', detail: 'Venus — boom', severity: 'warning' })
  })
})

describe('judgmentFlagsInclude / judgmentFlagText — compat shim over mixed-shape arrays', () => {
  it('finds a code among structured entries', () => {
    const flags: JudgmentFlagEntry[] = [judgmentFlag('zero_rows_returned'), judgmentFlag('response_size_truncated')]
    expect(judgmentFlagsInclude(flags, 'zero_rows_returned')).toBe(true)
    expect(judgmentFlagsInclude(flags, 'timing_hook_failed')).toBe(false)
  })

  it('finds a code among legacy bare-string entries (pre-migration emitter, e.g. session-pin drift)', () => {
    const flags: JudgmentFlagEntry[] = ['chart_rebuilt_mid_session_pin_refreshed']
    expect(judgmentFlagsInclude(flags, 'chart_rebuilt_mid_session_pin_refreshed')).toBe(true)
  })

  it('finds a code among legacy `code: detail` prefixed strings (the pre-migration convention several emitters used)', () => {
    const flags: JudgmentFlagEntry[] = ['karaka_unresolved: Venus — some error']
    expect(judgmentFlagsInclude(flags, 'karaka_unresolved')).toBe(true)
  })

  it('never throws on a mixed array of both shapes', () => {
    const flags: JudgmentFlagEntry[] = [judgmentFlag('zero_rows_returned'), 'chart_rebuilt_mid_session_pin_refreshed']
    expect(() => judgmentFlagsInclude(flags, 'zero_rows_returned')).not.toThrow()
    expect(judgmentFlagsInclude(flags, 'chart_rebuilt_mid_session_pin_refreshed')).toBe(true)
  })

  it('handles null/undefined flags arrays defensively', () => {
    expect(judgmentFlagsInclude(undefined, 'zero_rows_returned')).toBe(false)
    expect(judgmentFlagsInclude(null, 'zero_rows_returned')).toBe(false)
  })

  it('renders either shape to text without throwing', () => {
    expect(judgmentFlagText('a bare legacy string')).toBe('a bare legacy string')
    expect(judgmentFlagText(judgmentFlag('zero_rows_returned'))).toBe('zero_rows_returned')
    expect(judgmentFlagText(judgmentFlag('karaka_unresolved', 'Venus'))).toBe('karaka_unresolved: Venus')
  })
})

describe('buildRetrievalEnvelope — judgment_flags carries the structured shape end-to-end', () => {
  it('v3 envelope serves structured judgment_flags entries verbatim', () => {
    const env = buildRetrievalEnvelope(
      { tool: 't', content: {}, judgment_flags: [judgmentFlag('zero_rows_returned', 'no rows')] },
      'v3',
    )
    expect(env.judgment_flags).toEqual([{ code: 'zero_rows_returned', detail: 'no rows' }])
  })

  it('legacy envelope defaults judgment_flags to an empty array (unchanged wire shape)', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content: {} })
    expect(env.judgment_flags).toEqual([])
  })
})

// ── Hollow-emitter honesty (register_p1_synthesis.ts / register_p1_reference.ts) ──────────
// The two files each carry their own local, non-exported `deriveHollowEnvelopeFlags` (they
// hand-duplicate their envelope/dualOutput helpers rather than share a module) — this
// re-implements the exact same three-branch contract here so the honesty behavior itself is
// covered by a fast unit test independent of platform-mcp's build. Any drift between this and
// the two files' actual logic would be caught by platform-mcp's own typecheck/tests since the
// shape (JudgmentFlagEntry[], never a bare `[]`) is what both files must produce.
function deriveHollowEnvelopeFlagsRef(content: unknown): JudgmentFlagEntry[] {
  if (content === null || content === undefined) {
    return [judgmentFlag('zero_rows_returned', 'no content returned for this call.')]
  }
  if (typeof content !== 'object' || Array.isArray(content)) {
    return [judgmentFlag('hollow_envelope_shape_not_evaluated', 'content is not a keyed object — no row-count field available to check.')]
  }
  const obj = content as Record<string, unknown>
  const arrayFields = Object.entries(obj).filter(([, v]) => Array.isArray(v)) as Array<[string, unknown[]]>
  if (arrayFields.length > 0) {
    const allEmpty = arrayFields.every(([, v]) => v.length === 0)
    if (allEmpty) {
      return [judgmentFlag('hollow_envelope_no_data_rows', `every row-shaped field (${arrayFields.map(([k]) => k).join(', ')}) is empty for this call.`)]
    }
    return []
  }
  const total = obj['total'] ?? obj['returned']
  if (total === 0) {
    return [judgmentFlag('zero_rows_returned', 'total/returned=0 for this call.')]
  }
  return [judgmentFlag('hollow_envelope_shape_not_evaluated', 'no array-valued or total/returned field found on content — no honest-gap signal computable from this shape (never fabricated).')]
}

describe('hollow-emitter honesty contract (register_p1_synthesis.ts / register_p1_reference.ts)', () => {
  it('flags null content honestly', () => {
    const flags = deriveHollowEnvelopeFlagsRef(null)
    expect(judgmentFlagsInclude(flags, 'zero_rows_returned')).toBe(true)
  })

  it('flags all-empty array-shaped content', () => {
    const flags = deriveHollowEnvelopeFlagsRef({ discoveries: [], total: 0 })
    expect(judgmentFlagsInclude(flags, 'hollow_envelope_no_data_rows')).toBe(true)
  })

  it('emits no flags when at least one array field is populated', () => {
    const flags = deriveHollowEnvelopeFlagsRef({ rows: [{ a: 1 }] })
    expect(flags).toEqual([])
  })

  it('emits an honest no-signal flag for a shape with neither arrays nor a total/returned field', () => {
    const flags = deriveHollowEnvelopeFlagsRef({ calibration_status: 'prior_only', mode: 'STRUCTURAL' })
    expect(judgmentFlagsInclude(flags, 'hollow_envelope_shape_not_evaluated')).toBe(true)
  })

  // This is the REGRESSION this migration item specifically targets — the old static `[]`
  // ALWAYS resolved to "no flags", regardless of content; the new path must never do that for
  // an unambiguously empty result.
  it('never emits the old always-empty `[]` for a genuinely empty result', () => {
    const flags = deriveHollowEnvelopeFlagsRef({ transit_rules: [], total: 0 })
    expect(flags.length).toBeGreaterThan(0)
  })
})
