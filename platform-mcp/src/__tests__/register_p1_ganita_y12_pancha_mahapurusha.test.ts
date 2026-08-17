/**
 * register_p1_ganita_y12_pancha_mahapurusha.test.ts — Y-12 (D-1.6 Lane S-3, CR-33/CR-43)
 * regression pin.
 *
 * The bug (live-confirmed on chart 482012f1 this session): ganita_yogas_get's v3
 * `pancha_mahapurusha` verdict block (buildPanchaMahapurushaVerdict in register_p1_ganita.ts)
 * was grounded in the CALLER'S OWN PAGINATED `rows` array. A caller-supplied small `limit`
 * (e.g. limit=3) could return a page with ZERO yoga_label rows at all — and the verdict then
 * asserted "Sasa (Saturn Mahapurusha Yoga) is not formed" (and the same for all 5 named
 * yogas) purely because pagination excluded their yoga_label rows from THIS page, even
 * though the rows genuinely exist in the full unpaginated set. This is the exact violation
 * Gate Ś item 7 names: "a page containing the Sasa row can never say 'Sasa not formed'".
 *
 * The fix: buildPanchaMahapurushaVerdict is now grounded in a SEPARATE, dedicated,
 * unpaginated get_yoga_dosha fetch (limit=500, offset=0), independent of the caller's own
 * pagination window on ganita_yogas_get.
 *
 * No live platform/DB required — `fetch` is mocked per-uri, same harness as
 * registry_bridge_r5w1_signals_synthesis.test.ts.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, _desc: string, _schema: unknown, handler: ToolHandler) => {
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'

// A minimal Sasa Yoga yoga_label row — present in the FULL (unpaginated) dataset, but
// deliberately EXCLUDED from the tiny 3-row page below (the exact truncation scenario).
const SASA_ROW = {
  fact_id: 'sasa-fact-1',
  fact_category: 'yoga_label',
  fact_subject: 'sasa',
  ayanamsha_id: 'lahiri_chitrapaksha',
  fact_key: 'yoga_name',
  fact_value_text: 'Sasa Yoga',
  fact_value_jsonb: { fire_reason: 'requires_pass', classical_citations: [{ text_id: 'bphs', chapter: 75 }] },
}
// This deliberately has the same category and display text as SASA_ROW, but it is not a
// catalog label. It reproduces the C.7 ambiguity: without the fact_key pin, array order lets
// this unrelated measurement donate its citation to the Sasa verdict.
const WRONG_KEY_SASA_DECOY = {
  fact_id: 'sasa-decoy',
  fact_category: 'yoga_label',
  fact_subject: 'sasa',
  ayanamsha_id: 'lahiri_chitrapaksha',
  fact_key: 'display_alias',
  fact_value_text: 'Sasa Yoga',
  fact_value_jsonb: { classical_citations: [{ text_id: 'wrong-key-decoy', chapter: 999 }] },
}
const OTHER_ROW_1 = { fact_id: 'flag-1', fact_category: 'bhadra_flag', fact_subject: 'BHADRA_FLAG_BIRTH', fact_key: 'active_at_birth_flag', fact_value_text: 'false', fact_value_jsonb: null }
const OTHER_ROW_2 = { fact_id: 'flag-2', fact_category: 'panchaka_flag', fact_subject: 'PANCHAKA_FLAG_BIRTH', fact_key: 'active_at_birth_flag', fact_value_text: 'true', fact_value_jsonb: null }
const OTHER_ROW_3 = { fact_id: 'flag-3', fact_category: 'panchaka_flag', fact_subject: 'PANCHAKA_FLAG_BIRTH', fact_key: 'nakshatra_position', fact_value_text: 'Purva Bhadrapada', fact_value_jsonb: null }

const SATURN_POSITION_ROWS = [
  { fact_subject: 'SAT', fact_key: 'sign', fact_value_text: 'Capricorn' },
  { fact_subject: 'SAT', fact_key: 'house_d1', fact_value_num: 10 },
]

function stubFetch(payloads: Record<string, unknown>, captured: Array<{ uri: string; args: Record<string, unknown> }>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    captured.push(body)
    if (!(body.uri in payloads)) {
      throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    }
    const capabilityHandlerReturn = { content: payloads[body.uri], is_error: false }
    return {
      ok: true,
      json: async () => ({ ok: true, content: capabilityHandlerReturn }),
      text: async () => '',
    }
  }))
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('ganita_yogas_get — Y-12 pancha_mahapurusha truncation-fabrication fix (CR-33/CR-43)', () => {
  it('does not assert "not formed" for Sasa when the caller-paginated page excludes its row but the unpaginated set contains it', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []

    stubFetch({
      // The main (paginated) call: limit=3, offset=0 — returns ZERO yoga_label rows,
      // reproducing the live-observed truncation scenario exactly.
      'marsys://tool/L1/get_yoga_dosha': {
        chart_id: TEST_CHART_ID,
        categories: ['yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag'],
        // NOTE: stubFetch answers EVERY get_yoga_dosha call with this same payload
        // regardless of args — see the second test below for a variant that
        // distinguishes the paginated vs. unpaginated calls by argument.
        rows: [OTHER_ROW_1, OTHER_ROW_2, OTHER_ROW_3, WRONG_KEY_SASA_DECOY, SASA_ROW],
        total: 10,
        firings_pointer: { tool: 'ganita_yoga_firings_get', table: 'ga_yoga_firings', fired_count: 13, note: 'x' },
        catalog_only_rows_in_page: 1,
        dosha_label_gate: { applied: true, all: false, excluded_total: 22, note: 'x' },
      },
      'marsys://tool/L1/get_positions': { rows: SATURN_POSITION_ROWS },
      'marsys://tool/L1/get_chart_header': { chart_id_short: '00000000', name: 'Test', lagna_sign: 'Aries', lagna_deg: 0, moon_sign: 'Aries', sun_sign: 'Aries', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: null },
    }, captured)

    const { registerP1GanitaTools } = await import('../tools/register_p1_ganita.js')
    registerP1GanitaTools(server, PRINCIPAL)
    const handler = handlers.get('ganita_yogas_get')
    expect(handler).toBeDefined()

    const result = await handler!({ chart_id: TEST_CHART_ID, limit: 3, response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as Record<string, unknown>
    const pancha = verdict['pancha_mahapurusha'] as { per_yoga: { yoga: string; status: string; statement: string }[] } | undefined
    expect(pancha).toBeDefined()

    const sasaEntry = pancha!.per_yoga.find(p => p.yoga.startsWith('Sasa'))
    expect(sasaEntry).toBeDefined()
    // The load-bearing assertion: Sasa's yoga_label row IS present in the (mocked)
    // unpaginated get_yoga_dosha fetch this fix wires — the verdict must read "formed",
    // never "not formed" fabricated from the caller's tiny limit=3 page.
    expect(sasaEntry!.status).toBe('formed')
    // The canonical yoga_name row supplies the citation even though a wrong-key decoy occurs
    // first. Before the C.7 pin this would surface the decoy's citation by array order.
    expect(sasaEntry!.statement).toContain('bphs ch.75')
    expect(sasaEntry!.statement).not.toContain('wrong-key-decoy')

    // Confirm the dedicated unpaginated call was actually made (limit=500, offset=0) —
    // proves the fix's wiring, not just a coincidentally-correct mock.
    const dedicatedCall = captured.find(
      c => c.uri === 'marsys://tool/L1/get_yoga_dosha' && c.args['limit'] === 500 && c.args['offset'] === 0,
    )
    expect(dedicatedCall).toBeDefined()
  })

  it('grounds the verdict in the unpaginated fetch even when the caller page is genuinely empty of yoga_label rows', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []

    // Distinguish the two get_yoga_dosha calls by their `limit` arg: the caller-paginated
    // call (limit=3) returns NO yoga_label rows; the dedicated unpaginated call (limit=500)
    // returns Sasa's row. This is the sharpest possible reproduction of the truncation bug.
    vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
      const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
      captured.push(body)
      if (body.uri === 'marsys://tool/L1/get_yoga_dosha') {
        const isPaginatedCall = body.args['limit'] === 3
        const rows = isPaginatedCall ? [OTHER_ROW_1, OTHER_ROW_2, OTHER_ROW_3] : [OTHER_ROW_1, OTHER_ROW_2, OTHER_ROW_3, SASA_ROW]
        const payload = {
          chart_id: TEST_CHART_ID, rows, total: 10,
          firings_pointer: { tool: 'ganita_yoga_firings_get', table: 'ga_yoga_firings', fired_count: 13, note: 'x' },
          catalog_only_rows_in_page: isPaginatedCall ? 0 : 1,
          dosha_label_gate: { applied: true, all: false, excluded_total: 22, note: 'x' },
        }
        return { ok: true, json: async () => ({ ok: true, content: { content: payload, is_error: false } }), text: async () => '' }
      }
      if (body.uri === 'marsys://tool/L1/get_positions') {
        return { ok: true, json: async () => ({ ok: true, content: { content: { rows: SATURN_POSITION_ROWS }, is_error: false } }), text: async () => '' }
      }
      if (body.uri === 'marsys://tool/L1/get_chart_header') {
        return { ok: true, json: async () => ({ ok: true, content: { content: { chart_id_short: '00000000', name: 'Test', lagna_sign: 'Aries', lagna_deg: 0, moon_sign: 'Aries', sun_sign: 'Aries', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: null }, is_error: false } }), text: async () => '' }
      }
      throw new Error(`stubFetch: unexpected uri "${body.uri}"`)
    }))

    const { registerP1GanitaTools } = await import('../tools/register_p1_ganita.js')
    registerP1GanitaTools(server, PRINCIPAL)
    const handler = handlers.get('ganita_yogas_get')!

    const result = await handler({ chart_id: TEST_CHART_ID, limit: 3, response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as Record<string, unknown>
    const pancha = verdict['pancha_mahapurusha'] as { per_yoga: { yoga: string; status: string }[] } | undefined
    const sasaEntry = pancha!.per_yoga.find(p => p.yoga.startsWith('Sasa'))

    // Pre-fix this would be 'not formed' (grounded in the empty 3-row page). Post-fix it
    // must read 'formed' — grounded in the dedicated unpaginated fetch that DOES carry
    // Sasa's row, even though the caller's own page carries zero yoga_label rows.
    expect(sasaEntry!.status).toBe('formed')

    // The page-level receipt (verdict.yogas_fired etc) is legitimately 0 for this tiny
    // page — that field is honestly page-scoped (see its own `note`). Only the
    // pancha_mahapurusha per-yoga verdict must NOT inherit that truncation.
    expect(verdict['yogas_fired']).toBe(0)
  })

  it('uses only the dosha_name catalog row when reconciling Kala Sarpa against its D1 computation', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    const wrongKeyCatalogDecoy = {
      fact_id: 'kala-sarpa-decoy',
      fact_category: 'dosha_label',
      fact_subject: 'kala_sarpa',
      fact_key: 'display_alias',
      fact_value_text: 'Kala Sarpa Dosha',
    }
    const canonicalCatalogRow = {
      fact_id: 'kala-sarpa-catalog',
      fact_category: 'dosha_label',
      fact_subject: 'kala_sarpa',
      fact_key: 'dosha_name',
      fact_value_text: 'Kala Sarpa Dosha',
    }
    const natalComputation = {
      fact_id: 'kala-sarpa-d1',
      fact_category: 'kala_sarpa_per_varga',
      fact_key: 'ks_detection',
      fact_value_jsonb: { fires: false, rahu_house: 2, ketu_house: 8 },
    }

    stubFetch({
      'marsys://tool/L1/get_yoga_dosha': {
        rows: [wrongKeyCatalogDecoy, canonicalCatalogRow],
        total: 2,
        kala_sarpa_per_varga: { natal: [natalComputation], divisional_fired: [] },
      },
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '00000000', name: 'Test', lagna_sign: 'Aries', lagna_deg: 0,
        moon_sign: 'Aries', sun_sign: 'Aries', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: null,
      },
    }, captured)

    const { registerP1GanitaTools } = await import('../tools/register_p1_ganita.js')
    registerP1GanitaTools(server, PRINCIPAL)
    const handler = handlers.get('ganita_structural_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, facet: 'dosha_fires', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as { kala_sarpa_dosha: { reconciliation_note: string } }
    // The genuine D1 calculation remains authority; this assertion specifically proves the
    // secondary catalog-row reduction cannot be diverted by a same-category wrong-key row.
    expect(verdict.kala_sarpa_dosha.reconciliation_note).toContain('fact_id kala-sarpa-catalog')
    expect(verdict.kala_sarpa_dosha.reconciliation_note).not.toContain('fact_id kala-sarpa-decoy')
    expect(captured[0]).toMatchObject({ uri: 'marsys://tool/L1/get_yoga_dosha' })
  })
})
