/**
 * SATYA-ŚEṢA W7 (Flagship Substance-Inline) — verification.
 *
 * Proves W7.1-W7.4 at the unit level: assess_wealth/assess_career's `reading` digest is
 * composed over already-computed data + a bounded set of read-only capability calls (mocked
 * fetch here — no live DB/HTTP), every family in the domain's TCI top tier is present (never
 * silently dropped, B.10), the gate-semantics rename (W7.3) never lets `synthesis_gate: OPEN`
 * masquerade as "this response delivered the whole slice", and the new fields are immune to
 * response-budget trimming even under an aggressively small budget_kb (W7.4).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  buildDomainReading,
  attachDomainReading,
  type ReadingFamilyEntry,
} from '../tools/registry_bridge.js'
import { IMMUNE_HONESTY_FIELDS, finalizeMcpBudget, autoDetectTrimmableSections } from '../lib/response_budget.js'
import type { Principal } from '../types.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }

function factRow(overrides: Record<string, unknown>): Record<string, unknown> {
  return {
    fact_id: 'fid_default', fact_category: 'test', fact_subject: 'X', fact_key: 'k',
    fact_value_num: null, fact_value_text: null, fact_value_jsonb: null,
    ...overrides,
  }
}

/** Routes the mocked fetch by (uri, args.category / args) to synthetic-but-real-shaped rows,
 *  mirroring the actual capability response shapes read in registry_bridge.ts.
 *
 *  TRACK A / SAMĀPANA §1 fix (2026-07-27): every previous version of this mock returned
 *  `{ ok: true, content }` where `content` was the UNWRAPPED inner payload directly
 *  (`{ rows: [...] }`). That is NOT what `/api/retrieval/capability` (route.ts) actually sends:
 *  every `CapabilityDescriptor.handler` (query_mechanisms.ts, chart_facts_query, query_remedies)
 *  returns a `{ content: X, is_error: boolean }` ToolResult wrapper, and route.ts's
 *  `NextResponse.json({ ok: true, content })` puts THAT WHOLE WRAPPER in the HTTP `content` field
 *  — so the real wire shape is `{ ok: true, content: { content: {...}, is_error: false } }`,
 *  doubly-wrapped. This mock's old flat shape was exactly the "flat fixture" failure mode already
 *  named in the `attachDomainReading (real content-wrapped shape)` test below for the OUTER
 *  assess_wealth payload — it just hadn't yet been applied to fetchReadingSupplements's OWN
 *  capability calls, which is precisely why every one of the tests in this file passed while the
 *  live 7-family emptiness bug shipped to production undetected. Wrapping `content` here in
 *  `{ content: ..., is_error: false }` makes this mock byte-faithful to route.ts and would have
 *  caught the bug before it shipped. */
function mockCapabilityFetch() {
  return vi.fn(async (_url: unknown, init: { body?: string }) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string; args: Record<string, unknown> }
    const { uri, args } = body
    let innerContent: unknown = { rows: [] }

    if (uri === 'marsys://tool/L1/chart_facts_query') {
      const category = args['category']
      if (category === 'net_argala_per_varga') {
        innerContent = {
          rows: [
            factRow({ fact_id: 'argala_h2', fact_subject: 'D1_HOUSE_2', fact_value_num: -4 }),
            factRow({ fact_id: 'argala_h11', fact_subject: 'D1_HOUSE_11', fact_value_num: -3 }),
            factRow({ fact_id: 'argala_h10', fact_subject: 'D1_HOUSE_10', fact_value_num: 2 }),
          ],
        }
      } else if (category === 'special_lagna') {
        innerContent = {
          rows: [
            factRow({ fact_id: 'bl_sign', fact_subject: 'BHAVA_LAGNA', fact_key: 'sign', fact_value_text: 'Taurus' }),
            factRow({ fact_id: 'gl_sign', fact_subject: 'GHATI_LAGNA', fact_key: 'sign', fact_value_text: 'Gemini' }),
          ],
        }
      } else if (category === 'bhava_arudha') {
        innerContent = { rows: [factRow({ fact_id: 'al1', fact_subject: 'AL1', fact_key: 'sign', fact_value_text: 'Leo' })] }
      } else if (category === 'karakamsa_position') {
        innerContent = {
          rows: [
            factRow({ fact_id: 'kar_sign', fact_subject: 'KARAKAMSA', fact_key: 'sign', fact_value_text: 'Aries' }),
            factRow({ fact_id: 'kar_ak', fact_subject: 'KARAKAMSA', fact_key: 'atmakaraka_graha', fact_value_text: 'Moon' }),
          ],
        }
      } else if (category === 'nakshatra_cross_ayanamsha') {
        // TRACK A fix: fetchReadingSupplements now overrides ayanamsha_id to 'INVARIANT' for
        // this specific call (the rows are stored INVARIANT-wide, not per-ayanamsha) — assert
        // that override actually arrives here, mirroring the real ga_nakshatra.py storage.
        if (args['ayanamsha_id'] !== 'INVARIANT') {
          innerContent = { rows: [] }
        } else {
          innerContent = {
            rows: [
              factRow({ fact_id: 'jup_consist', fact_subject: 'JUP', fact_key: 'nak_5ay_consistency', fact_value_text: '5/5' }),
              factRow({ fact_id: 'sat_consist', fact_subject: 'SAT', fact_key: 'nak_5ay_consistency', fact_value_text: '5/5' }),
              factRow({ fact_id: 'lagna_consist', fact_subject: 'LAGNA', fact_key: 'nak_5ay_consistency', fact_value_text: '0/5' }),
            ],
          }
        }
      }
    } else if (uri === 'marsys://tool/L2/query_mechanisms') {
      innerContent = {
        rows: [
          { mechanism_id: 'm1', mechanism_name: 'Jupiter convergent chain', mechanism_class: 'convergent_dispositor_chain', valence: 'benefic', member_node_ids_array: ['a', 'b', 'c'] },
          { mechanism_id: 'm2', mechanism_name: 'Venus-Mercury exchange', mechanism_class: 'mutual_reception', valence: 'mixed', member_node_ids_array: ['d', 'e'] },
        ],
        total_matching: 2, chain_circuit_count: 1,
      }
    } else if (uri === 'marsys://tool/L2/query_remedies') {
      innerContent = {
        narration: { lead: 'Your Bodha remedy layer flags Saturn as your #1 remedy-priority target — resonance_score 0.812, priority class high.' },
        prescriptions: [
          { target_graha: 'Saturn', remedy_label_human: 'Blue sapphire (test)', remedy_category: 'gemstone', tradition: 'parashari', classical_strength_rating: 'strong' },
        ],
      }
    }
    // Real wire shape (route.ts): { ok: true, content: <handler's own { content, is_error }> }.
    const content = { content: innerContent, is_error: false }
    return { ok: true, json: async () => ({ ok: true, content }) }
  })
}

const BASE_DATA_WEALTH: Record<string, unknown> = {
  varga_analysis: {
    direct_consumption: true,
    per_varga: {
      D2: { graha_dignity: [{ graha: 'Jupiter', dignity: 'exalted', house_display: '11th', fact_id: 'd2_jup' }], ashtakavarga_available: true, ashtakavarga_pinda_sarva: [{ graha: 'Jupiter', pinda_sarva: 32, fact_id: 'd2_av_jup' }] },
      D11: { graha_dignity: [{ graha: 'Venus', dignity: 'own_sign', house_display: '2nd', fact_id: 'd11_ven' }], ashtakavarga_available: false, empty_reason: 'not yet computed for D11' },
    },
    indu_lagna: { sign: 'Scorpio', sign_lord: 'Mars', house_d1: 8, nakshatra: 'Anuradha', fact_ids: ['indu_1'] },
  },
  activating_dasha: { activations: [{ lord: 'Jupiter', start: '2027-01-01' }] },
  contradictions: { items: [{ tension_label: 'promise vs denial', adjudication: null }], total_count: 1 },
}

const BASE_DATA_CAREER: Record<string, unknown> = {
  varga_analysis: {
    direct_consumption: true,
    per_varga: {
      D10: { graha_dignity: [{ graha: 'Moon', dignity: 'exalted', house_display: '10th', fact_id: 'd10_moon' }], ashtakavarga_available: true, ashtakavarga_pinda_sarva: [{ graha: 'Saturn', pinda_sarva: 28, fact_id: 'd10_av_sat' }] },
      D9: { graha_dignity: [{ graha: 'Mercury', dignity: 'moolatrikona', house_display: '3rd', fact_id: 'd9_merc' }], ashtakavarga_available: false, empty_reason: 'not yet computed for D9' },
    },
  },
  activating_dasha: { activations: [{ lord: 'Mercury', start: '2026-09-01' }] },
  contradictions: { items: [], total_count: 0 },
}

describe('SATYA-ŚEṢA W7 — substance-inline reading digest', () => {
  let fetchSpy: ReturnType<typeof mockCapabilityFetch>
  beforeEach(() => {
    fetchSpy = mockCapabilityFetch()
    vi.stubGlobal('fetch', fetchSpy)
  })
  afterEach(() => { vi.unstubAllGlobals() })

  it('wealth: every one of the 13 TCI-frozen families is present, never silently dropped', async () => {
    const { reading, families_total } = await buildDomainReading('wealth', CHART_ID, AYANAMSHA, BASE_DATA_WEALTH, PRINCIPAL)
    expect(families_total).toBe(13)
    expect(reading).toHaveLength(13)
    const expected = [
      'per_varga_ashtakavarga', 'divisional_D2', 'divisional_D11', 'indu_lagna',
      'argala_house_2', 'argala_house_11', 'full_dispositor_closure',
      'all_chart_mechanisms_and_chains', 'special_lagnas', 'cross_ayanamsha_agreement',
      'timing_windows', 'remedies', 'contradictions_with_adjudication',
    ]
    expect(reading.map((r: ReadingFamilyEntry) => r.family)).toEqual(expected)
    // Every family carries real, non-empty prose — never a bare label (D1 of the addendum:
    // "a final answer that mentions a concept's name without its computed value is a MISS").
    for (const family of reading) {
      expect(family.sentences.length).toBeGreaterThan(0)
      expect(family.sentences.every((s) => s.length > 10)).toBe(true)
    }
  })

  it('career: every one of the 12 TCI-frozen families is present', async () => {
    const { reading, families_total } = await buildDomainReading('career', CHART_ID, AYANAMSHA, BASE_DATA_CAREER, PRINCIPAL)
    expect(families_total).toBe(12)
    expect(reading.map((r: ReadingFamilyEntry) => r.family)).toContain('karakamsha_or_swamsha')
    expect(reading.map((r: ReadingFamilyEntry) => r.family)).toContain('argala_house_10')
    expect(reading.map((r: ReadingFamilyEntry) => r.family)).not.toContain('indu_lagna')
  })

  it('argala families carry the real net_argala substance + fact_id, not just the label', async () => {
    const { reading } = await buildDomainReading('wealth', CHART_ID, AYANAMSHA, BASE_DATA_WEALTH, PRINCIPAL)
    const h2 = reading.find((r: ReadingFamilyEntry) => r.family === 'argala_house_2')!
    expect(h2.status).toBe('served')
    expect(h2.sentences[0]).toContain('-4')
    expect(h2.fact_ids).toContain('argala_h2')
  })

  it('divisional/ashtakavarga families reflect substance ALREADY in `data` (D1 fix) — never re-fetched, never a bare label', async () => {
    const { reading } = await buildDomainReading('wealth', CHART_ID, AYANAMSHA, BASE_DATA_WEALTH, PRINCIPAL)
    const d2 = reading.find((r: ReadingFamilyEntry) => r.family === 'divisional_D2')!
    expect(d2.sentences.join(' ')).toContain('Jupiter')
    expect(d2.sentences.join(' ')).toContain('exalted')
    expect(d2.fact_ids).toContain('d2_jup')
  })

  it('a family whose data source has nothing reports an honest gap, never a fabricated substitute (B.10)', async () => {
    const emptyMechanisms = mockCapabilityFetch()
    vi.stubGlobal('fetch', vi.fn(async (_url: unknown, init: { body?: string }) => {
      const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
      if (body.uri === 'marsys://tool/L2/query_mechanisms') {
        const innerContent = { rows: [], total_matching: 0, chain_circuit_count: 0, empty_reason: 'No mechanisms for this chart.' }
        return { ok: true, json: async () => ({ ok: true, content: { content: innerContent, is_error: false } }) }
      }
      return emptyMechanisms(_url, init)
    }))
    const { reading } = await buildDomainReading('wealth', CHART_ID, AYANAMSHA, BASE_DATA_WEALTH, PRINCIPAL)
    const closure = reading.find((r: ReadingFamilyEntry) => r.family === 'full_dispositor_closure')!
    expect(closure.status).toBe('empty_for_this_chart')
    expect(closure.sentences[0]).toContain('No convergent_dispositor_chain')
  })

  it('attachDomainReading (W7.3): renames the full-slice bookkeeping gate so OPEN can never be misread as this-response-delivered', async () => {
    const response: Record<string, unknown> = {
      ...BASE_DATA_WEALTH,
      domain_completeness: { slice_size: 13820, accounted: 13820, pct: 100, synthesis_gate: 'OPEN' },
    }
    await attachDomainReading(response, 'wealth', CHART_ID, AYANAMSHA, PRINCIPAL)
    const completeness = response['domain_completeness'] as Record<string, unknown>
    // The raw dossier bookkeeping value survives, but under a DIFFERENT field name —
    // `synthesis_gate` itself must never appear bare on this headline response (W7.3).
    expect(completeness['synthesis_gate']).toBeUndefined()
    expect(completeness['slice_accounting_gate']).toBe('OPEN')
    expect(String(completeness['reading_digest_status'])).toContain('/13 families summarized inline')
    expect(String(response['completeness_directive'])).toContain('SUBSTANCE-INLINE')
    expect(Array.isArray(response['reading'])).toBe(true)
  })

  it('regression (PŪRṆA-VIRĀMA, live-probe-discovered): attachDomainReading reads substance from the REAL `{ content: {...} }`-wrapped response shape, not just a flat fixture', async () => {
    // register_d8_assess_domain.ts's L-DOMAIN/assess_wealth capability returns
    // `{ content: { varga_analysis, activating_dasha, contradictions, ... } }`; registry_bridge.ts's
    // assess_wealth handler spreads that directly onto `response`
    // (`{ orientation_context, orientation_ok, ...data }`), so on the real wire the substance
    // lives at `response.content.varga_analysis`, never `response.varga_analysis`. The original
    // W7 build only tested against a flat (uncontented) fixture and shipped reading `undefined`
    // for every family in production — deployed, live-probed, and found empty end-to-end.
    const response: Record<string, unknown> = {
      orientation_context: {}, orientation_ok: true,
      content: { ...BASE_DATA_WEALTH },
      domain_completeness: { slice_size: 13820, accounted: 13820, pct: 100, synthesis_gate: 'OPEN' },
    }
    await attachDomainReading(response, 'wealth', CHART_ID, AYANAMSHA, PRINCIPAL)
    const reading = response['reading'] as ReadingFamilyEntry[]
    expect(Array.isArray(reading)).toBe(true)
    const d2 = reading.find((r) => r.family === 'divisional_D2')!
    expect(d2.status).toBe('served')
    expect(d2.sentences.join(' ')).toContain('Jupiter')
    const timing = reading.find((r) => r.family === 'timing_windows')!
    expect(timing.status).toBe('served')
    const contradictions = reading.find((r) => r.family === 'contradictions_with_adjudication')!
    expect(contradictions.status).toBe('served')
    // The families_served count embedded in reading_digest_status must not read 0/N on real data.
    const completeness = response['domain_completeness'] as Record<string, unknown>
    expect(String(completeness['reading_digest_status'])).not.toContain('0/13')
  })

  it('regression (SAMĀPANA Track A, 2026-07-27): fetchReadingSupplements-backed families parse ' +
    'the REAL doubly-wrapped `{ content: { content: X, is_error }, ... }` internal-route shape — ' +
    'the standing bug was NOT a routing/auth/concurrency divergence (that hypothesis, tested and ' +
    'documented in PŪRṆA-VIRĀMA §4/§9.1, is refuted here); it was registry_bridge.ts reading ' +
    '`rows`/`narration`/`prescriptions` one level too shallow off every capability handler\'s own ' +
    '`{ content, is_error }` ToolResult wrapper, which /api/retrieval/capability (route.ts) passes ' +
    'through unwrapped inside ITS OWN `content` field. Live-verified against the deployed chart: ' +
    'the SAME capability + SAME args via its standalone MCP tool (bodha_mechanisms_get, ' +
    'ganita_chart_facts_get, bodha_remedies_get) returns rich real data — proving the HTTP round-' +
    'trip itself was never the defect, only this file\'s unwrapping of its response.', async () => {
    const { reading } = await buildDomainReading('wealth', CHART_ID, AYANAMSHA, BASE_DATA_WEALTH, PRINCIPAL)
    const previouslyEmptyFamilies = [
      'argala_house_2', 'argala_house_11', 'full_dispositor_closure',
      'all_chart_mechanisms_and_chains', 'special_lagnas', 'cross_ayanamsha_agreement', 'remedies',
    ]
    for (const family of previouslyEmptyFamilies) {
      const entry = reading.find((r: ReadingFamilyEntry) => r.family === family)!
      expect(entry, `family ${family} must be present`).toBeDefined()
      expect(entry.status, `family ${family} must be 'served' given real (populated) supplement data`).toBe('served')
      expect(entry.sentences.join(' ').length).toBeGreaterThan(10)
    }
  })

  it('W7.4: `reading` and `domain_completeness` are in the trim-immune honesty set', () => {
    expect(IMMUNE_HONESTY_FIELDS.has('reading')).toBe(true)
    expect(IMMUNE_HONESTY_FIELDS.has('domain_completeness')).toBe(true)
    expect(IMMUNE_HONESTY_FIELDS.has('completeness_directive')).toBe(true)
    expect(IMMUNE_HONESTY_FIELDS.has('coverage_map')).toBe(true)
  })

  it('W7.4 regression: an aggressively small budget_kb still carries the full, untruncated digest', async () => {
    const { reading } = await buildDomainReading('wealth', CHART_ID, AYANAMSHA, BASE_DATA_WEALTH, PRINCIPAL)
    // A response dominated by large unrelated arrays (simulating a real assess_wealth
    // payload's bulk) alongside the digest.
    const response: Record<string, unknown> = {
      reading,
      domain_completeness: { slice_size: 13820, coverage_map: Array.from({ length: 60 }, (_, i) => ({ serving_tool: `tool_${i}`, concept_count: i })) },
      completeness_directive: 'SUBSTANCE-INLINE: read `reading` directly.',
      big_unrelated_array: Array.from({ length: 500 }, (_, i) => ({ id: i, blob: 'x'.repeat(200) })),
    }
    const before = JSON.stringify(response.reading)
    const sections = autoDetectTrimmableSections(response, 'assess_wealth')
    const out = finalizeMcpBudget(response, { maxKb: 2, sections }) // 2KB — far under the digest's own size
    expect(JSON.stringify(out['reading'])).toBe(before) // byte-identical — never touched
    expect(out['domain_completeness']).toBeDefined()
    expect((out['domain_completeness'] as Record<string, unknown>)['coverage_map']).toBeDefined()
    expect(out['completeness_directive']).toBe('SUBSTANCE-INLINE: read `reading` directly.')
    // The unrelated array is what actually got shrunk to make room.
    expect((out['big_unrelated_array'] as unknown[]).length).toBeLessThan(500)
  })
})
