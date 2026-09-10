/**
 * evidence_state.ts — honest zero-result detector for the MCP epistemics block.
 *
 * PARIŚEṢA F-126. `/api/mcp/primitives/[tool]` hardcoded
 * `confidence_band: 'high'` on every surgical primitive response, regardless of
 * what the tool actually returned. Live reproducer (production, canonical chart):
 *
 *   mimamsa_lel_query { query: "marriage relationship spouse partner wedding" }
 *     → result …{"events":[],"count":0,"total_matching":0}…
 *     → epistemics {"surgical":true,"confidence_band":"high", …}
 *
 * i.e. the envelope claimed HIGH confidence in a finding that does not exist.
 * That is the §N.8 Earned-Signal defect exactly: a grade asserted by a code path
 * that never measured the thing it grades. `'high'` here was not computed from
 * anything — no code path could ever have produced a different value.
 *
 * WHAT THIS MODULE DOES: measures the claim. It inspects the tool result the
 * route is about to serve and answers one narrow, checkable question — "did this
 * result set report zero rows?" — returning:
 *
 *   'empty'          the payload itself reports a zero count (nothing was found)
 *   'present'        the payload reports rows / a non-zero count
 *   'indeterminate'  the payload declares no count this detector can read
 *
 * HONEST SCOPE (deliberately conservative, per §N.8): 'empty' is returned ONLY
 * when the payload states its own emptiness through a numeric count field, or
 * when the ToolBundle carries zero results. A payload with no readable count is
 * 'indeterminate' and leaves the band untouched — this detector never guesses at
 * emptiness from the shape of a response, because a wrong 'empty' would be the
 * same class of unearned signal in the opposite direction. Any non-empty array
 * on the payload wins outright and reports 'present', so a payload that carries
 * real rows can never be graded empty by a stale/secondary zero counter.
 */

import type { EvidenceState, EpistemicsBlock } from '@/lib/mcp/types'

export type { EvidenceState }

/**
 * Count fields a retrieval payload may use to declare its own family size.
 * `total_matching` is the registry's D5 coverage-receipt convention (family size
 * before LIMIT/OFFSET); `count` is the served-page size.
 */
const COUNT_KEYS = [
  'total_matching',
  'total_count',
  'row_count',
  'matched_count',
  'count',
  'total',
] as const

/** Combine per-payload verdicts: any real row wins; all-empty is empty. */
function combine(states: EvidenceState[]): EvidenceState {
  if (states.length === 0) return 'indeterminate'
  if (states.includes('present')) return 'present'
  if (states.every(s => s === 'empty')) return 'empty'
  return 'indeterminate'
}

/** Evidence verdict for a single decoded payload object. */
function payloadEvidence(payload: unknown): EvidenceState {
  if (payload === null || payload === undefined) return 'empty'
  if (Array.isArray(payload)) return payload.length === 0 ? 'empty' : 'present'
  if (typeof payload === 'string') return payload.trim().length === 0 ? 'empty' : 'indeterminate'
  if (typeof payload !== 'object') return 'indeterminate'

  const obj = payload as Record<string, unknown>

  // A populated collection anywhere on the payload means rows WERE served —
  // never grade that empty, whatever a counter says.
  for (const value of Object.values(obj)) {
    if (Array.isArray(value) && value.length > 0) return 'present'
  }

  let sawCount = false
  for (const key of COUNT_KEYS) {
    const value = obj[key]
    if (typeof value === 'number' && Number.isFinite(value)) {
      sawCount = true
      if (value > 0) return 'present'
    }
  }

  return sawCount ? 'empty' : 'indeterminate'
}

/** True for the legacy ToolBundle wrapper built by tool_name_bridge.ts. */
function isToolBundle(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== 'object') return false
  const obj = value as Record<string, unknown>
  if (!Array.isArray(obj['results'])) return false
  return 'tool_bundle_id' in obj || 'tool_name' in obj || 'schema_version' in obj
}

/** Decode one ToolBundle result entry — `content` is a JSON string by convention. */
function decodeBundleEntry(entry: unknown): unknown {
  if (entry === null || typeof entry !== 'object') return entry
  const content = (entry as Record<string, unknown>)['content']
  if (typeof content !== 'string') return content
  try {
    return JSON.parse(content)
  } catch {
    // Not JSON — grade the raw text (empty string = empty, otherwise unreadable).
    return content
  }
}

/**
 * Detect whether a served tool result reports zero rows.
 *
 * Handles the two shapes the primitives route can hold: the legacy ToolBundle
 * wrapper (`{tool_bundle_id, results:[{content: "<json>"}], …}`) produced by
 * `tool_name_bridge.getToolByName().retrieve()`, and a bare handler payload.
 */
export function detectEvidenceState(result: unknown): EvidenceState {
  if (isToolBundle(result)) {
    const entries = (result as Record<string, unknown>)['results'] as unknown[]
    if (entries.length === 0) return 'empty'
    return combine(entries.map(e => payloadEvidence(decodeBundleEntry(e))))
  }
  return payloadEvidence(result)
}

/**
 * Confidence band for a surgical primitive, computed from the result it serves.
 *
 * A surgical primitive lookup that actually returned rows is 'high' (a single
 * deterministic fact read — the pre-existing, correct behaviour). A lookup that
 * returned nothing is graded `'none'`: there is no finding for a band to grade,
 * and 'high' would be a confidence claim about an absent answer. 'indeterminate'
 * leaves the pre-existing band alone rather than inventing a downgrade.
 */
export function surgicalConfidenceBand(
  state: EvidenceState,
): EpistemicsBlock['confidence_band'] {
  return state === 'empty' ? 'none' : 'high'
}
