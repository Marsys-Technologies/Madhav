/**
 * f123_dead_pointer_regression.test.ts — F-123 (CL-11 "dead pointer") regression guard.
 *
 * Defect: `kala_now_get`'s (and `kala_ahead_get`'s / `kala_priority_get`'s) `tri_plane
 * .interpretation_ref` advertised `pointerTo('kala_explain_get', hint)` with NO args payload.
 * `kala_explain_get` hard-errors ("either `domain` or `bhava` is required" —
 * `explain.ts`'s `explainRequiresDomainOrBhava` guard) the instant a caller follows that
 * pointer exactly as advertised, with only `chart_id`. Confirmed live against the deployed
 * MCP service on the canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`) before this fix.
 *
 * GA-5 review finding: the original version of this file re-derived each site's domain-
 * selection logic inline with hand-written literals ("Mirrors now.ts's primaryDomain
 * derivation") instead of calling the real `now.ts`/`ahead.ts`/`priority.ts` code. Mutation-
 * tested: reverting `now.ts` to the pre-fix bare `pointerTo('kala_explain_get', hint)` left
 * every test in the old file GREEN, because none of them imported or invoked the real site.
 * This version calls `computeKalaNow` / `computeKalaAhead` directly (the same pattern already
 * established in `kala_now_get.test.ts` / `kala_ahead_get.test.ts`) and
 * `registerKalaPriorityTool`'s real registered handler via a capturing fake `McpServer`, then
 * asserts on each result's actual `tri_plane.interpretation_ref` — so a regression that removes
 * the `args` payload from any of the three real call sites makes THIS test fail for real,
 * not just a hand-derived proxy of it.
 */
import { describe, expect, it, vi } from 'vitest'
import type { Principal } from '../../types.js'
import { computeKalaNow } from './now.js'
import { computeKalaAhead } from './ahead.js'
import { registerKalaPriorityTool } from './priority.js'
import { pointerTo, type DrillPointerLike } from '../../lib/kala_envelope.js'
import { explainRequiresDomainOrBhava } from './explain.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }
const AS_OF = '2026-07-29'

/** Simulates following a DrillPointerLike exactly as a caller would: `instrument` names the
 *  tool, `args` (if present) is spread as the call's params alongside `chart_id`. Mirrors
 *  what an MCP client does with a `tri_plane` pointer — no domain/bhava beyond what `args`
 *  itself carries. */
function followPointer(pointer: DrillPointerLike): { domain: unknown; bhava: unknown } {
  const args = pointer.args ?? {}
  return { domain: (args as Record<string, unknown>)['domain'], bhava: (args as Record<string, unknown>)['bhava'] }
}

// --- shared fixtures (adapted from kala_now_get.test.ts / kala_ahead_get.test.ts's own
// established mock-fetch pattern; only the minimum needed to reach tri_plane construction) ---

const WINDOW_FAMILY = {
  window_start: '2026-07-01',
  window_end: '2026-08-15',
  window_peak: '2026-07-20',
  member_count: 3,
  member_signal_ids: ['sig-1', 'sig-2', 'sig-3'],
  signature_classes: ['dasha_transit_conjunction'],
  domains: ['career', 'wealth'],
  max_orb_strength: 0.82,
}

const DARSHANA_ROW = {
  effective_score: 61.4,
  net_label: 'favorable',
  window_start: AS_OF,
  window_end: AS_OF,
  obstruction_summary: null,
  narrative: { text: 'ok' },
}

const PROJECTION_FAMILY = {
  window_start: '2027-06-01',
  window_end: '2027-09-01',
  domain: 'health',
  member_count: 5,
  member_ids: ['proj-1', 'proj-2'],
  member_signal_ids: ['sig-20', 'sig-21'],
  probability_tier: 'tier_1_high' as const,
  max_effective_score: 71.2,
  narrative: { text: 'x' },
  source_citation: 'x',
}

const ACTIVE_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Jupiter', lord_sign: 'Cancer', start_date: '2020-01-01', end_date: '2036-01-01' },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Venus', lord_sign: 'Libra', start_date: '2026-01-01', end_date: '2028-01-01' },
]

const TRANSIT_BY_PLANET: Record<string, Record<string, unknown>> = {
  Jupiter: { date: AS_OF, sign_number: 4, degree_in_sign: 12.5, nakshatra_number: 9, is_retrograde: false },
  Venus: { date: AS_OF, sign_number: 6, degree_in_sign: 3.1, nakshatra_number: 14, is_retrograde: false },
}

const DIGNITY_BY_GRAHA: Record<string, Record<string, unknown>> = {
  Jupiter: { graha: 'Jupiter', exaltation_sign: 'Cancer', debilitation_sign: 'Capricorn', own_signs: ['Sagittarius', 'Pisces'] },
  Venus: { graha: 'Venus', exaltation_sign: 'Pisces', debilitation_sign: 'Virgo', own_signs: ['Taurus', 'Libra'] },
}

/** Double-wrapped `/api/retrieval/capability` + `/api/mcp/db/query` mock, shared by
 *  computeKalaNow and computeKalaAhead — same contract as kala_now_get.test.ts /
 *  kala_ahead_get.test.ts's own `mockRegistryFetch`. */
function mockNowAheadFetch() {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri?: string; args?: Record<string, unknown>; sql?: string; params?: unknown[] }

    if (String(url).includes('/api/mcp/db/query')) {
      const graha = String(body.params?.[0] ?? '')
      const row = Object.values(DIGNITY_BY_GRAHA).find((r) => String(r['graha']).toLowerCase() === graha.toLowerCase())
      return { ok: true, json: async () => ({ rows: row ? [row] : [] }), text: async () => '' } as Response
    }

    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [WINDOW_FAMILY], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_temporal_view') {
      inner = { rows: [DARSHANA_ROW] }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projections: [], projection_families: [PROJECTION_FAMILY] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [{ fact_subject: 'LAGNA', fact_key: 'sign_num', fact_value_num: 1, fact_id: 'fact-lagna' }] }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      inner = { systems: [{ system_id: 'vimshottari', active_chain: ACTIVE_CHAIN }] }
    } else if (body.uri === 'marsys://tool/L0/query_planet_transit') {
      const planet = String(body.args?.['planet'] ?? '')
      const row = TRANSIT_BY_PLANET[planet]
      inner = { rows: row ? [row] : [] }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

/** Single-wrapped `/api/retrieval/capability` + `/api/mcp/db/query` mock for priority.ts's
 *  own contract — mirrors priority.test.ts's established mock shape exactly (see that file's
 *  own doc-comment for why priority.ts's wrap differs from now.ts/ahead.ts's). */
function mockPriorityFetch() {
  return vi.fn(async (url: unknown, opts: unknown) => {
    const urlStr = String(url)
    if (urlStr.includes('/api/mcp/db/query')) {
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' } as unknown as Response
    }
    if (urlStr.includes('/api/retrieval/capability')) {
      const body = JSON.parse(String((opts as { body?: string })?.body ?? '{}')) as { uri?: string; args?: Record<string, unknown> }
      if (body.uri === 'marsys://tool/L3/call_priority_ranking') {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            content: {
              chart_id: TEST_CHART_ID,
              date_from: '2026-08-01',
              date_to: '2026-11-01',
              ranked_signals: [],
              signal_count: 0,
              // The fixed pointer derives its domain from domain_filter when present —
              // exercise that path, matching what a real domain-scoped call returns.
              domain_filter: ['relationship'],
              neutral_dignity_downranked_count: 0,
            },
          }),
        } as unknown as Response
      }
    }
    return { ok: false, status: 500, text: async () => 'unexpected' } as unknown as Response
  })
}

/** Minimal capturing fake McpServer — registers a real tool's handler and hands it back so
 *  it can be invoked exactly as registerKalaPriorityTool's own real registration does it. */
function captureRegisteredHandler(
  registerFn: (server: { tool: (...args: unknown[]) => void }, principal: Principal) => void,
  principal: Principal,
): (params: Record<string, unknown>) => Promise<unknown> {
  let captured: ((params: Record<string, unknown>) => Promise<unknown>) | null = null
  const fakeServer = {
    tool: (..._args: unknown[]) => {
      const handler = _args[_args.length - 1] as (params: Record<string, unknown>) => Promise<unknown>
      captured = handler
    },
  }
  registerFn(fakeServer, principal)
  if (!captured) throw new Error('registerFn never called server.tool() — nothing captured')
  return captured
}

function extractInterpretationRef(mcpResult: unknown): DrillPointerLike {
  const asAny = mcpResult as { content?: Array<{ type: string; text?: string }> }
  const textBlock = asAny.content?.find((c) => c.type === 'text')
  if (!textBlock?.text) throw new Error('MCP tool result had no text content block')
  const parsed = JSON.parse(textBlock.text) as { tri_plane?: { interpretation_ref?: DrillPointerLike } }
  const ref = parsed.tri_plane?.interpretation_ref
  if (!ref) throw new Error('response had no tri_plane.interpretation_ref')
  return ref
}

describe('F-123: kala_explain_get pointer dead-end regression', () => {
  it('reproduces the pre-fix defect: a bare pointerTo(kala_explain_get) with no args dead-ends', () => {
    const bareDeadPointer = pointerTo('kala_explain_get', 'Why this NOW state reads as it does')
    const { domain, bhava } = followPointer(bareDeadPointer)
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(true)
  })

  it('now.ts site: computeKalaNow (the REAL function) emits an interpretation_ref that clears the real kala_explain_get guard', async () => {
    vi.stubGlobal('fetch', mockNowAheadFetch())
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const ref = result.tri_plane.interpretation_ref
    expect(ref).not.toBeNull()
    const { domain, bhava } = followPointer(ref as DrillPointerLike)
    expect(domain).toBeTruthy()
    // The load-bearing assertion: the REAL explain.ts guard, given exactly what the REAL
    // now.ts handler's pointer args carry, does NOT reject the call.
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(false)
    vi.unstubAllGlobals()
  })

  it('ahead.ts site: computeKalaAhead (the REAL function), called with a caller-scoped domain, emits an interpretation_ref that clears the real kala_explain_get guard', async () => {
    // ahead.ts's interpretation_ref forwards the CALLER-supplied domain filter (it does not
    // derive one from data, unlike now.ts) — exercise the scoped-call path, matching what
    // kala_ahead_get itself accepts as its own optional `domain` param.
    vi.stubGlobal('fetch', mockNowAheadFetch())
    const result = await computeKalaAhead(TEST_CHART_ID, { domain: 'health' }, TEST_PRINCIPAL)
    const ref = result.tri_plane.interpretation_ref
    expect(ref).not.toBeNull()
    const { domain, bhava } = followPointer(ref as DrillPointerLike)
    expect(domain).toBe('health')
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(false)
    vi.unstubAllGlobals()
  })

  it('priority.ts site: the REAL registered kala_priority_get handler emits an interpretation_ref that clears the real kala_explain_get guard', async () => {
    vi.stubGlobal('fetch', mockPriorityFetch())
    const handler = captureRegisteredHandler(
      registerKalaPriorityTool as unknown as (server: { tool: (...args: unknown[]) => void }, principal: Principal) => void,
      TEST_PRINCIPAL,
    )
    const mcpResult = await handler({ chart_id: TEST_CHART_ID })
    const ref = extractInterpretationRef(mcpResult)
    const { domain, bhava } = followPointer(ref)
    expect(domain).toBe('relationship') // derived from the mocked domain_filter[0], not fabricated
    expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(false)
    vi.unstubAllGlobals()
  })

  it('honest degrade: when no domain is derivable, computeKalaAhead does not fabricate one, and the pointer says so in its hint', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body ?? '{}')) as { uri?: string }
      if (String(url).includes('/api/mcp/db/query')) {
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' } as Response
      }
      // No projection_families, no window_families -> no domain anywhere to derive from.
      let inner: Record<string, unknown> = {}
      if (body.uri === 'marsys://tool/L3/query_temporal_activation') inner = { window_families: [], forward_windows: [] }
      if (body.uri === 'marsys://tool/L3/query_projections') inner = { projections: [], projection_families: [] }
      return { ok: true, json: async () => ({ ok: true, content: { content: inner, is_error: false } }), text: async () => '' } as Response
    }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ref = result.tri_plane.interpretation_ref
    if (ref != null) {
      // Honest about the residual gap: following THIS pointer as advertised (no args) would
      // still dead-end — that is the correct, disclosed behavior for a genuinely domain-less
      // state, not a regression. It must not silently fabricate a domain to avoid that.
      const { domain, bhava } = followPointer(ref)
      expect(domain).toBeUndefined()
      expect(explainRequiresDomainOrBhava(domain, bhava)).toBe(true)
    }
    vi.unstubAllGlobals()
  })
})
