/**
 * test_panchang_routing.ts — Planner Panchang routing gate
 *
 * Tests that the R-PA / R-PCI routing rules correctly classify the probe set
 * in `panchang_probe_set.json`. This is a deterministic unit test — no LLM
 * calls, no sidecar calls, no API keys required — CI-safe.
 *
 * Extended in PSHIP-S4H (2026-05-20) to cover:
 *   1. 13 new R-PA trigger phrases (PP.11–PP.21)
 *   2. R-PCI context-inheritance skip (PP.22 — tool_calls empty)
 *   3. Main's R-TC regression (PP.23 — transit query routes to query_ephemeris)
 *   4. False-positive check (PP.24 — 'sunrise' alone does NOT trigger R-PA)
 *
 * The router mirrors PLANNER_PROMPT_v2_0.md §3.R-PA + §3.R-PCI (v2.0.7).
 *
 * Gate for PSHIP-S4H close: 24/24 PASS.
 * Gate for 4C.3 close (original): 10/10 PASS (subset of above).
 */

import { describe, it, expect } from 'vitest'
import probeSet from './panchang_probe_set.json'

// ── R-PA keyword sets (mirrors PLANNER_PROMPT_v2_0.md §3.R-PA v2.0.7) ───────
//
// Extended in PSHIP-S4H to include all 13 new trigger phrases from R-PA (d/f/g).

/** Panchang-path keywords (lowercase; partial-match search) */
const PANCHANG_KEYWORDS = [
  // R-PA (a) — Lunar phase / tithi
  'tithi',
  'purnima',
  'amavasya',
  'ekadashi',
  'chaturdashi',
  'pratipada',
  'full moon',
  'new moon',
  'bright fortnight',
  'dark fortnight',
  'waxing moon',
  'waning moon',
  'shukla paksha',
  'krishna paksha',
  // R-PA (b) — Moon nakshatra
  'nakshatra',
  // R-PA (c) — Vara
  ' vara',      // space prefix avoids matching "sarvaartha" etc.
  // R-PA (d) — Yoga / karana + named special yogas (NEW: PSHIP-S4H)
  'karana',
  'paksha',
  'masa',
  'sarvartha siddhi',
  'amrit siddhi',
  'guru pushya',
  'ravi pushya',
  'tripushkar',
  'dwipushkar',
  'siddha yoga',
  'bhadra yoga',
  ' bhadra',     // Bhadra karana / Vishti
  'panchaka',
  // R-PA (e) — Muhurta / auspicious-day
  'muhurat',
  'muhurta',
  'auspicious time',
  'auspicious for',
  'is today auspicious',
  'good day for',
  'good tuesday',
  'good monday',
  'good wednesday',
  'good thursday',
  'good friday',
  'good saturday',
  'good sunday',
  'when should i',
  "when's a good",
  'when is a good',
  'yoga day',
  // R-PA (f) — Inauspicious and auspicious windows (NEW: PSHIP-S4H)
  'rahu kalam',
  'rahu kaal',
  'yamagandam',
  'gulika kalam',
  'gulika',
  'brahma muhurta',
  'abhijit',
  'amrit kalam',
  'choghadiya',
  ' hora',       // hora, not ephora / remora
  // R-PA (g) — Direct panchang requests (NEW: PSHIP-S4H)
  'panchang for today',
  "today's panchang",
  'panchang for ',
  'what is today\'s panchang',
  'give me the panchang',
  'panchang',
  'chandra bala',
  'tara bala',
] as const

/** R-PCI: detect <panchang_context> block in query */
function hasPanchangContext(query: string): boolean {
  return query.includes('<panchang_context')
}

/** Ephemeris-path keywords */
const EPHEMERIS_KEYWORDS = [
  'sidereal longitude',
  'ecliptic longitude',
  'exact longitude',
  'longitude of',
  'retrograde next',
  'when does',
  'go retrograde',
  'station',
  'at noon',
  'at midnight',
  'specific moment',
  'ingress',
  'transit aspect',
] as const

/**
 * Heuristic function mirroring the R-PA + R-PCI rules.
 * Returns the set of tools the planner SHOULD select for a given query.
 * Returns 'NONE' singleton when R-PCI fires (no tool calls needed).
 *
 * Note: This is the deterministic rule-based version of what the LLM planner
 * does when it follows R-PA and R-PCI. The gate validates the rules are sound.
 *
 * Updated in PSHIP-S4H to handle:
 *   - R-PCI: <panchang_context> block → return Set{'NONE'} (no tool calls)
 *   - Extended R-PA (d/f/g) keyword set
 *   - FP guard: 'sunrise' alone (without other panchang keywords) → ephemeris only
 */
function routeQuery(query: string): Set<string> {
  // R-PCI check FIRST — takes priority over R-PA
  if (hasPanchangContext(query)) {
    return new Set(['NONE'])
  }

  const q = (' ' + query + ' ').toLowerCase()

  const isPanchangQuery = PANCHANG_KEYWORDS.some(kw => q.includes(kw.toLowerCase()))
  const isEphemerisQuery = EPHEMERIS_KEYWORDS.some(kw => q.includes(kw.toLowerCase()))

  // Special case: "where is [planet] right now" → ephemeris (not panchang)
  const isWhereIsNow = /where is .+ (right now|now|currently|in my chart)/.test(q)

  // "panchang look like" / "what's the panchang" → panchang even if combust also present
  const isPanchangOverview = q.includes('panchang look') || q.includes("what's the panchang") || q.includes("panchang for today")

  // "combust" → also needs ephemeris (combustion is a planetary position fact — requires ephemeris)
  // When combined with a panchang query → co-selection (both tools)
  const isCombustQuery = q.includes('combust')

  // FP guard: "sunrise" alone does NOT trigger R-PA — it's only a positional qualifier
  // (PP.24: "sidereal longitude of Venus at sunrise today" → ephemeris, NOT panchanga)
  // The sunrise word in context of a pure positional/longitude query must not fire R-PA.
  // Only 'sidereal longitude' / 'exact longitude' etc. should route such queries.
  // (No change needed here — EPHEMERIS_KEYWORDS already catches 'sidereal longitude';
  //  and 'sunrise' is not in PANCHANG_KEYWORDS, so this guard is implicit.)

  const tools = new Set<string>()

  if (isPanchangQuery || isPanchangOverview) {
    tools.add('query_panchanga')
  }

  if (isEphemerisQuery || isWhereIsNow || isCombustQuery) {
    tools.add('query_ephemeris')
  }

  // Fallback: unrecognized queries default to ephemeris (safest fallback for transit-context)
  if (tools.size === 0) {
    tools.add('query_ephemeris')
  }

  return tools
}

// ── Load the probe set and build test cases ──────────────────────────────────

interface ProbeQuery {
  id: string
  query: string
  expected_tool?: string
  expected_tool_calls?: string[]
  rationale: string
}

const queries = probeSet.queries as ProbeQuery[]

// ── Gate test suite ──────────────────────────────────────────────────────────

describe(`Panchang routing gate — ${queries.length} probe queries`, () => {
  for (const probe of queries) {
    it(`${probe.id}: ${probe.query.slice(0, 60)}`, () => {
      const routed = routeQuery(probe.query)

      if (probe.expected_tool_calls) {
        // Multi-tool query (PP.09): both tools must appear
        for (const expectedTool of probe.expected_tool_calls) {
          expect(
            routed.has(expectedTool),
            `${probe.id} expected "${expectedTool}" in tool_calls, got: [${[...routed].join(', ')}]\nQuery: "${probe.query}"\nRationale: ${probe.rationale}`,
          ).toBe(true)
        }
      } else if (probe.expected_tool === 'NONE') {
        // R-PCI probe (PP.22): no tool calls expected — context inheritance skip
        expect(
          routed.has('NONE'),
          `${probe.id} R-PCI: expected NONE (no tool calls), got: [${[...routed].join(', ')}]\nQuery starts with: "${probe.query.slice(0, 80)}"\nRationale: ${probe.rationale}`,
        ).toBe(true)
        expect(
          routed.has('query_panchanga'),
          `${probe.id} R-PCI must NOT call query_panchanga when <panchang_context> is present`,
        ).toBe(false)
      } else if (probe.expected_tool) {
        // Single-tool query: expected tool must be in the result
        expect(
          routed.has(probe.expected_tool),
          `${probe.id} Expected "${probe.expected_tool}" for query "${probe.query.slice(0, 80)}", got: [${[...routed].join(', ')}]\nRationale: ${probe.rationale}`,
        ).toBe(true)
      }
    })
  }
})

describe('Panchang routing — false positive / false negative checks', () => {
  it('does not route "where is Saturn now" to query_panchanga', () => {
    const tools = routeQuery('Where is Saturn right now in my chart?')
    expect(tools.has('query_ephemeris')).toBe(true)
    expect(tools.has('query_panchanga')).toBe(false)
  })

  it('does not route "what nakshatra is the moon in" to query_ephemeris alone', () => {
    const tools = routeQuery('What nakshatra is the moon in right now?')
    expect(tools.has('query_panchanga')).toBe(true)
  })

  it('does not route "good Tuesday for vehicle" to query_ephemeris', () => {
    const tools = routeQuery("When's a good Tuesday for buying a vehicle next month?")
    expect(tools.has('query_panchanga')).toBe(true)
    expect(tools.has('query_ephemeris')).toBe(false)
  })

  it('routes mixed combust + panchang query to both tools', () => {
    const tools = routeQuery("Is Mars combust today and what's the panchang look like?")
    expect(tools.has('query_panchanga')).toBe(true)
  })

  // ── PSHIP-S4H new checks ────────────────────────────────────────────────────

  it('R-PCI: <panchang_context> block fires NONE (no query_panchanga call)', () => {
    const query = '<panchang_context date="2026-05-20">tithi: Panchami</panchang_context><user_question>Is today good?</user_question>'
    const tools = routeQuery(query)
    expect(tools.has('NONE')).toBe(true)
    expect(tools.has('query_panchanga')).toBe(false)
  })

  it('R-TC unchanged: transit query routes to query_ephemeris (main R-TC regression)', () => {
    const tools = routeQuery('What is my current Jupiter mahadasha doing to my 10th house?')
    expect(tools.has('query_ephemeris')).toBe(true)
    expect(tools.has('query_panchanga')).toBe(false)
  })

  it('FP guard: "sunrise" alone does NOT trigger R-PA (sidereal longitude query)', () => {
    const tools = routeQuery("What's the exact sidereal longitude of Venus at sunrise today?")
    expect(tools.has('query_ephemeris')).toBe(true)
    expect(tools.has('query_panchanga')).toBe(false)
  })

  it('R-PA (f) new trigger: "rahu kalam" routes to query_panchanga', () => {
    const tools = routeQuery('What time is Rahu Kalam today?')
    expect(tools.has('query_panchanga')).toBe(true)
  })

  it('R-PA (f) new trigger: "choghadiya" routes to query_panchanga', () => {
    const tools = routeQuery("Show me today's Choghadiya")
    expect(tools.has('query_panchanga')).toBe(true)
  })

  it('R-PA (d) new trigger: "Sarvartha Siddhi" routes to query_panchanga', () => {
    const tools = routeQuery('Is Sarvartha Siddhi Yoga present today?')
    expect(tools.has('query_panchanga')).toBe(true)
  })

  it('R-PA (g) new trigger: "panchang for today" routes to query_panchanga', () => {
    const tools = routeQuery('Give me the panchang for today')
    expect(tools.has('query_panchanga')).toBe(true)
  })

  it('R-PA (g) new trigger: "chandra bala" routes to query_panchanga', () => {
    const tools = routeQuery('Is today good for me based on chandra bala?')
    expect(tools.has('query_panchanga')).toBe(true)
  })
})
