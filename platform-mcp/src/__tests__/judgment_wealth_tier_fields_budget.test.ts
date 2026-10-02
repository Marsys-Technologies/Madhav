/**
 * judgment_wealth_tier_fields_budget.test.ts — TI-served-tier-legs: the tier fields the wealth
 * legs now carry (evidence_tier, verified_count, tier_breakdown, incomplete_reason, plus the
 * checklist-level units_served_unverified_tier) must SURVIVE the real 12 KB judgment_query
 * response budget.
 *
 * Drives the REAL registered `judgment_query` MCP tool (registry_bridge.ts: the real
 * judgmentSections declarations, applyMcpBudget -> finalizeMcpBudget -> applyResponseBudget) with
 * a fetch-stubbed capability payload large enough to force trimming, and checks:
 *   (i)  trimming genuinely engaged (trim_report present) — otherwise the test proves nothing;
 *   (ii) every served wealth unit keeps `evidence_tier` and `verified_count`, every incomplete unit
 *        keeps `incomplete_reason`, the three wealth response blocks keep all four tier fields,
 *        and the checklist-level `units_served_unverified_tier` is intact;
 *   (iii) the hardFloor sections (bearing_yogas, bearing_afflictions, affliction_mechanisms) keep at
 *        least their declared minKeep (3 / 3 / 2) and keep exactly what they keep WITHOUT the
 *        tier fields present (the new fields displace nothing the §N.6 floor protects).
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
    tool: (name: string, _desc: string, _schema: unknown, handler: ToolHandler) => { handlers.set(name, handler) },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function stubFetch(payload: unknown) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    const defaults: Record<string, unknown> = {
      'marsys://tool/L2/query_ucd': { chart_id: body.args['chart_id'], digest: {}, entity_profiles: [] },
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2,
        moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha',
        current_maha_antar: 'Saturn/Mercury',
      },
    }
    const out = body.uri === 'marsys://tool/L-JUDGMENT/judgment_query' ? payload : defaults[body.uri]
    if (out === undefined) throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    return { ok: true, json: async () => ({ ok: true, content: { content: out, is_error: false } }), text: async () => '' }
  }))
}

beforeEach(() => vi.unstubAllGlobals())

const big = (tag: string, i: number) => ({
  signal_id: `${tag}-${i}`, signal_summary_text: `${tag} ${i} `.padEnd(420, 'x'), computed_salience: 0.9 - i / 1000,
  constituent_facts_array: [`f-${i}-a`, `f-${i}-b`, `f-${i}-c`],
})

function lagnaRows(n: number, tier: string) {
  return Array.from({ length: n }, (_, i) => ({ fact_id: `L-${i}`, fact_subject: 'INDU_LAGNA', fact_key: `k${i}`, fact_value_num: 1, fact_value_text: null, verification_pass_status: tier }))
}

/** A wealth judgment_query capability payload: three legs in three DIFFERENT tier states. */
function payload(withTierFields: boolean) {
  const tier = (fields: Record<string, unknown>) => (withTierFields ? fields : {})
  const unit = (name: string, state: string, extra: Record<string, unknown>, count = 0) => ({
    unit: name, state, count, detail: `${name} detail `.padEnd(200, 'd'), ...extra,
  })
  const units = [
    unit('special_lagnas', 'served', tier({ tier_breakdown: { single: 21 }, verified_count: 0, evidence_tier: 'present_at_unverified_tier' }), 21),
    unit('yogi_avayogi', 'source_incomplete', tier({ incomplete_reason: 'unservable_tier' })),
    unit('tajaka', 'served', tier({ tier_breakdown: { two_pass_verified: 1 }, verified_count: 1, evidence_tier: 'verified' }), 1),
  ]
  return {
    chart_id: CHART_ID,
    about: { domain: 'wealth', bhava: 2, label: 'Wealth', karakas: ['Jupiter'], operative_varga: 'D9' },
    receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D9✓', yogas_checked: 3, bhanga_checked: false, timing_anchored: true },
    fact_id_refs: Array.from({ length: 150 }, (_, i) => `fact-ref-${i}-`.padEnd(40, 'r')),
    drill_pointers: [{ instrument: 'ganita_chart_facts_get', hint: 'x', pointer_type: 'confirm_in_varga' }],
    judgment_flags: [],
    reading_checklist: {
      contract_id: 'judgment-reading-checklist-v2',
      units,
      exhaustive: false, non_exhaustive: 'salience_sampled', units_served: 2, units_total: 3, units_unserved: ['yogi_avayogi'],
      ...(withTierFields ? { units_served_unverified_tier: 1 } : {}),
    },
    checklist: {
      varga_confirmation: { varga: 'D9', rows: Array.from({ length: 12 }, (_, i) => ({ k: i, text: `v${i}`.padEnd(160, 'v') })) },
      bearing_yogas: Array.from({ length: 30 }, (_, i) => big('yoga', i)),
      bearing_afflictions: Array.from({ length: 30 }, (_, i) => big('aff', i)),
      affliction_mechanisms: Array.from({ length: 20 }, (_, i) => big('mech', i)),
      wealth_special_lagnas: {
        state: 'served', rows: lagnaRows(21, 'single'),
        ...tier({ tier_breakdown: { single: 21 }, verified_count: 0, evidence_tier: 'present_at_unverified_tier', incomplete_reason: null }),
      },
      wealth_yogi_avayogi: {
        state: 'source_incomplete', rows: [],
        ...tier({ tier_breakdown: {}, verified_count: 0, evidence_tier: null, incomplete_reason: 'unservable_tier' }),
      },
      wealth_tajaka: {
        state: 'served', as_of_date: '2026-09-19', row: { varsha_year: 42, verification_pass_status: 'two_pass_verified' },
        ...tier({ tier: 'two_pass_verified', verified_count: 1, evidence_tier: 'verified', incomplete_reason: null }),
      },
    },
  }
}

async function runTool(p: unknown, budget_kb?: number) {
  const { server, handlers } = makeCapturingServer()
  stubFetch(p)
  const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
  registerRegistryBridgeTools(server, PRINCIPAL)
  const result = await handlers.get('judgment_query')!({ chart_id: CHART_ID, domain: 'wealth', response_format: 'v3', ...(budget_kb === undefined ? {} : { budget_kb }) })
  expect(result.isError).toBeFalsy()
  const env = result.structuredContent?.object as Record<string, unknown>
  const content = env['content'] as Record<string, unknown>
  return { env, content, checklist: content['checklist'] as Record<string, unknown>, rc: content['reading_checklist'] as Record<string, unknown> }
}

describe('judgment_query 12 KB budget keeps the wealth tier fields', () => {
  it('trimming engages, and every tier field survives on units, blocks and the checklist summary', async () => {
    const { env, checklist, rc } = await runTool(payload(true))
    // (i) the test is only meaningful if the budget actually trimmed this response
    expect(Array.isArray(env['trim_report']) && (env['trim_report'] as unknown[]).length > 0).toBe(true)

    // (ii) units
    const units = new Map((rc['units'] as Array<Record<string, unknown>>).map(u => [u['unit'] as string, u]))
    expect(units.get('special_lagnas')).toMatchObject({ state: 'served', verified_count: 0, evidence_tier: 'present_at_unverified_tier' })
    expect(units.get('tajaka')).toMatchObject({ state: 'served', verified_count: 1, evidence_tier: 'verified' })
    expect(units.get('yogi_avayogi')).toMatchObject({ state: 'source_incomplete', incomplete_reason: 'unservable_tier' })
    // blocks
    const block = (k: string) => checklist[k] as Record<string, unknown>
    expect(block('wealth_special_lagnas')).toMatchObject({ verified_count: 0, evidence_tier: 'present_at_unverified_tier', incomplete_reason: null })
    expect(block('wealth_yogi_avayogi')).toMatchObject({ verified_count: 0, evidence_tier: null, incomplete_reason: 'unservable_tier' })
    expect(block('wealth_tajaka')).toMatchObject({ tier: 'two_pass_verified', verified_count: 1, evidence_tier: 'verified', incomplete_reason: null })
    // checklist-level count of served-at-a-non-verified tier
    expect(rc['units_served_unverified_tier']).toBe(1)
  })

  it('hardFloor sections keep their minKeep and exactly what they keep without the tier fields', async () => {
    const withTier = await runTool(payload(true))
    const without = await runTool(payload(false))
    const kept = (r: { checklist: Record<string, unknown> }, k: string) => (r.checklist[k] as unknown[]).length
    expect(kept(withTier, 'bearing_yogas')).toBeGreaterThanOrEqual(3)
    expect(kept(withTier, 'bearing_afflictions')).toBeGreaterThanOrEqual(3)
    expect(kept(withTier, 'affliction_mechanisms')).toBeGreaterThanOrEqual(2)
    for (const k of ['bearing_yogas', 'bearing_afflictions', 'affliction_mechanisms']) {
      expect({ k, n: kept(withTier, k) }).toEqual({ k, n: kept(without, k) })
    }
  })

  it('even under a stress budget (4 KB, every declared array at its floor, long strings truncated) the scalar tier fields are never trimmed away', async () => {
    const { rc, checklist } = await runTool(payload(true), 4)
    const units = new Map((rc['units'] as Array<Record<string, unknown>>).map(u => [u['unit'] as string, u]))
    expect(units.get('special_lagnas')).toMatchObject({ verified_count: 0, evidence_tier: 'present_at_unverified_tier' })
    expect(units.get('tajaka')).toMatchObject({ verified_count: 1, evidence_tier: 'verified' })
    expect(units.get('yogi_avayogi')).toMatchObject({ incomplete_reason: 'unservable_tier' })
    expect(checklist['wealth_tajaka']).toMatchObject({ evidence_tier: 'verified', verified_count: 1 })
    expect(rc['units_served_unverified_tier']).toBe(1)
  })
})
