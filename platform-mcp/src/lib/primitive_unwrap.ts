/**
 * primitive_unwrap — the ONE shared unwrapper for surgical-primitive envelopes.
 *
 * WHY THIS EXISTS (ṢAḌ-DARŚANA W3 lattice-unwrap fix, 2026-08-02):
 *
 * `/api/mcp/primitives/<tool>` (platform route.ts) does NOT return the registry
 * capability's raw payload on `envelope.result`. It returns the legacy ToolBundle
 * built by `tool_name_bridge.ts`'s `capabilityResultToToolBundle`: the capability
 * handler's `{ content: {...}, is_error: false }` goes through `toToolBundleResults`
 * branch 3 ("Single ToolResult") → `[{ content: JSON.stringify(contentObject) }]`.
 * The REAL payload is therefore at:
 *
 *     envelope.result.results[0].content   — as a JSON **string**
 *
 * and never at `envelope.result.<key>`. Reading `envelope.result.rows` (or any
 * payload key) directly is always `undefined` in production — the exact defect
 * class PR #823 fixed in `fetchReadingSupplements` (registry_bridge.ts), and
 * which `muhurta_finder.ts` / `mechanism_retrodiction.ts` / `mimamsa_lel_intake.ts`
 * / `phala_mitigation_map.ts` each fixed with a file-local copy of this idiom.
 * This module is the shared, single-sourced version of that idiom; new
 * `callPlatformPrimitive` consumers must use it rather than fork another copy.
 *
 * HONESTY CONTRACT (§N.8 Earned-Signal): the unwrap reports a machine-readable
 * `failure` cause when the wire shape is not what it pins, so callers can set
 * their `*_available` flags from a REAL detector on the parsed payload — never
 * from "the HTTP call returned 200". A wrapper-parse failure must be
 * distinguishable from a genuinely absent section and from honest empty rows.
 *
 * The wire shape itself is load-bearing for other consumers (route + bridge are
 * deliberately NOT changed) — the unwrap is entirely MCP-side.
 */

/** Machine-readable cause when the primitive payload could not be recovered. */
export type PrimitiveUnwrapFailure =
  | 'result_not_object'   // envelope.result missing / not an object
  | 'results_missing'     // ToolBundle-shaped wrapper with no results array
  | 'results_empty'       // results array present but has no entries
  | 'content_missing'     // results[0] carried no content field
  | 'content_not_json'    // results[0].content is a string but not parseable JSON
  | 'payload_not_object'  // parsed content is valid JSON but not an object

export interface PrimitiveUnwrapResult {
  /** The capability handler's `content` object, or null on failure. */
  payload: Record<string, unknown> | null
  /** null on success; the distinct wrapper-drift cause otherwise. */
  failure: PrimitiveUnwrapFailure | null
}

/**
 * Unwrap `envelope.result` from `callPlatformPrimitive` into the capability's
 * raw content object.
 *
 * Handles, in order (mirrors `unwrapMuhurtaFinderResult`'s defensive idiom):
 *  1. the production ToolBundle (`results[0].content` as a JSON string);
 *  2. a bridge-drift ToolBundle whose `results[0].content` is already an object;
 *  3. a hypothetical direct-object result (no `results` array, not
 *     ToolBundle-marked) — passed through unchanged so unit-test fixtures and
 *     any future bridge simplification keep working.
 *
 * Never throws; never yields a plausible-looking `{}` for a malformed wrapper.
 */
export function unwrapPrimitiveResult(envelopeResult: unknown): PrimitiveUnwrapResult {
  if (envelopeResult === null || typeof envelopeResult !== 'object' || Array.isArray(envelopeResult)) {
    return { payload: null, failure: 'result_not_object' }
  }

  const raw = envelopeResult as Record<string, unknown>
  const results = raw['results']

  if (!Array.isArray(results)) {
    // Not carrying a results array. If it is ToolBundle-marked, that is wrapper
    // drift (a bundle with its results stripped), NOT a direct payload — report
    // it honestly instead of letting "section absent" take the blame downstream.
    if ('tool_bundle_id' in raw) {
      return { payload: null, failure: 'results_missing' }
    }
    // Direct-object result (shape 3) — pass through.
    return { payload: raw, failure: null }
  }

  if (results.length === 0) {
    return { payload: null, failure: 'results_empty' }
  }

  const first = results[0]
  if (first === null || typeof first !== 'object' || !('content' in (first as Record<string, unknown>))) {
    return { payload: null, failure: 'content_missing' }
  }

  const content = (first as Record<string, unknown>)['content']

  if (typeof content === 'string') {
    let parsed: unknown
    try {
      parsed = JSON.parse(content)
    } catch {
      return { payload: null, failure: 'content_not_json' }
    }
    if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return { payload: null, failure: 'payload_not_object' }
    }
    return { payload: parsed as Record<string, unknown>, failure: null }
  }

  if (content !== null && typeof content === 'object' && !Array.isArray(content)) {
    // Bridge-drift tolerance: content already parsed by an upstream layer.
    return { payload: content as Record<string, unknown>, failure: null }
  }

  return { payload: null, failure: 'payload_not_object' }
}

/**
 * Standard honest reason string for a wrapper-parse failure — names the tool,
 * the cause, and states explicitly that this is NOT an empty result, so the
 * string can be surfaced verbatim in `unavailable_reason` fields.
 */
export function unwrapFailureReason(toolName: string, failure: PrimitiveUnwrapFailure): string {
  return (
    `${toolName}: ToolBundle unwrap failed (${failure}) — the primitive returned 200 but its ` +
    'payload could not be recovered from the wrapper; treating as UNAVAILABLE, not as empty data'
  )
}
