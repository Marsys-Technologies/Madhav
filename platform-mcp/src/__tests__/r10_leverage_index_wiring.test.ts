/**
 * PARIŚODHANA Phase-B1 — R-10 fix verification.
 *
 * PARISHODHANA_RECONCILIATION_v1_0.md disposed R-10 as LIVE-OPEN: `leverage_index` was
 * completely ABSENT (not null — not present as a key at all) from `assess_wealth`'s response
 * shape, confirmed by a full-response grep against chart 482012f1-710e-4a25-994a-93821f5871aa
 * — even though ganita_vichara_get(family=leverage_index, domain=wealth) returns 7 real,
 * populated rows (one per graha: JUP/MAR/MER/MOON/SAT/SUN/VEN) for that same chart. The
 * underlying L1 ga_vichara computation was never broken; this was a pure serving-layer
 * wiring gap (assess_wealth never joined it in).
 *
 * This suite proves `attachLeverageIndex` (registry_bridge.ts) closes that gap: it joins the
 * already-computed chart_vichara leverage_index rows in as `leverage_index_by_graha` (never
 * recomputing them, §N.5), degrades honestly on an empty/failed join (B.10), and never
 * disturbs unrelated fields already on the response (assess_wealth's other working fields
 * must not regress).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { attachLeverageIndex } from '../tools/registry_bridge.js'
import type { Principal } from '../types.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }

/** The 7 real rows live-verified for this chart (family=leverage_index, domain=wealth) —
 *  shape mirrors get_vichara.ts's actual SELECT column list. */
function realLeverageRows(): Record<string, unknown>[] {
  const subjects = ['JUP', 'MAR', 'MER', 'MOON', 'SAT', 'SUN', 'VEN']
  return subjects.map((subject, i) => ({
    id: String(107667 + i),
    chart_id: CHART_ID,
    ayanamsha_id: AYANAMSHA,
    vichara_family: 'leverage_index',
    subject,
    domain: 'wealth',
    varga_id: null,
    value_num: i * 0.5,
    value_text: null,
    value_jsonb: {
      capability: 0.5, dignity_score: 0.5, years_to_start: 1, md_duration_years: 2,
      domain_load_bearing_weight: 1, dasha_runway_weight: 1.02,
    },
    constituent_fact_ids: [`fid_${subject}_1`, `fid_${subject}_2`],
    formula_version: 'leverage_index_v1',
    source_citation: 'CR-69/CR-60 / DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §8',
    computed_at: '2026-07-26 22:05:40.433534+00',
  }))
}

/** Mocks the doubly-wrapped `/api/retrieval/capability` wire shape (route.ts wraps every
 *  handler's own `{ content, is_error }` ToolResult inside ITS OWN `content` field — the same
 *  shape Track A's fix (registry_bridge.ts unwrapCapabilityContent) exists to peel off). */
function mockVicharaFetch(rows: Record<string, unknown>[], emptyReason?: string) {
  return vi.fn(async (_url: unknown, init: { body?: string }) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string; args: Record<string, unknown> }
    expect(body.uri).toBe('marsys://tool/L1/get_vichara')
    expect(body.args['family']).toBe('leverage_index')
    const innerContent: Record<string, unknown> = {
      chart_id: CHART_ID,
      verdict: { chart_id: CHART_ID, total_rows: rows.length, served_rows: rows.length, family_counts: { leverage_index: rows.length } },
      digest: { families_present: rows.length > 0 ? ['leverage_index'] : [] },
      rows,
      total_matching: rows.length,
      more_available: false,
      ...(emptyReason ? { empty_reason: emptyReason } : {}),
    }
    return { ok: true, json: async () => ({ ok: true, content: { content: innerContent, is_error: false } }) }
  })
}

describe('R-10 — attachLeverageIndex wires the already-computed ga_vichara leverage_index family into assess_wealth', () => {
  afterEach(() => { vi.unstubAllGlobals() })

  it('populates leverage_index_by_graha with all 7 real rows (one per graha), read-only from the L1 row', async () => {
    vi.stubGlobal('fetch', mockVicharaFetch(realLeverageRows()))
    const response: Record<string, unknown> = {}
    await attachLeverageIndex(response, 'wealth', CHART_ID, AYANAMSHA, PRINCIPAL)

    expect(response['leverage_index_by_graha']).toBeDefined()
    const rows = response['leverage_index_by_graha'] as Record<string, unknown>[]
    expect(rows).toHaveLength(7)
    expect(rows.map((r) => r['subject'])).toEqual(['JUP', 'MAR', 'MER', 'MOON', 'SAT', 'SUN', 'VEN'])

    // §N.5 — every row is a read-only projection of the L1 vichara row, never a recomputation:
    // the emitted leverage_index/capability/constituent_fact_ids/formula_version must equal the
    // L1 row's own fields verbatim, not a derived/re-scored value.
    const jup = rows[0]!
    expect(jup['leverage_index']).toBe(0) // i=0 → value_num = 0 * 0.5
    expect(jup['capability']).toBe(0.5)
    expect(jup['constituent_fact_ids']).toEqual(['fid_JUP_1', 'fid_JUP_2'])
    expect(jup['formula_version']).toBe('leverage_index_v1')
    expect(jup['source_citation']).toContain('CR-69/CR-60')

    expect(response['leverage_index_empty_reason']).toBeUndefined()
    expect(typeof response['leverage_index_note']).toBe('string')
    expect(String(response['leverage_index_note'])).toContain('ganita_vichara_get')
  })

  it('degrades to an honest empty array + reason when the chart genuinely has no leverage_index rows (B.10 — never fabricates a substitute)', async () => {
    vi.stubGlobal('fetch', mockVicharaFetch([], 'No chart_vichara rows for this chart for family \'leverage_index\'.'))
    const response: Record<string, unknown> = {}
    await attachLeverageIndex(response, 'wealth', CHART_ID, AYANAMSHA, PRINCIPAL)

    expect(response['leverage_index_by_graha']).toEqual([])
    expect(String(response['leverage_index_empty_reason'])).toContain('No chart_vichara rows')
  })

  it('degrades to an honest gap (never throws, never fabricates) when the underlying capability call fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('simulated network failure') }))
    const response: Record<string, unknown> = {}
    await expect(attachLeverageIndex(response, 'wealth', CHART_ID, AYANAMSHA, PRINCIPAL)).resolves.toBeUndefined()

    expect(response['leverage_index_by_graha']).toEqual([])
    expect(String(response['leverage_index_empty_reason'])).toContain('leverage_index join failed')
    expect(String(response['leverage_index_empty_reason'])).toContain('simulated network failure')
  })

  it('never disturbs unrelated fields already on the response (assess_wealth PRESERVE-LIST — other working fields must not regress)', async () => {
    vi.stubGlobal('fetch', mockVicharaFetch(realLeverageRows()))
    const response: Record<string, unknown> = {
      orientation_context: { chart_id: CHART_ID }, orientation_ok: true,
      content: { varga_analysis: { direct_consumption: true } },
      domain_completeness: { slice_size: 13820, pct: 100 },
      judgment_flags: ['some_existing_flag'],
    }
    const before = JSON.parse(JSON.stringify(response))
    await attachLeverageIndex(response, 'wealth', CHART_ID, AYANAMSHA, PRINCIPAL)

    expect(response['orientation_context']).toEqual(before['orientation_context'])
    expect(response['orientation_ok']).toEqual(before['orientation_ok'])
    expect(response['content']).toEqual(before['content'])
    expect(response['domain_completeness']).toEqual(before['domain_completeness'])
    expect(response['judgment_flags']).toEqual(before['judgment_flags'])
    // The new field is additive, not a replacement of anything pre-existing.
    expect(response['leverage_index_by_graha']).toBeDefined()
  })
})
