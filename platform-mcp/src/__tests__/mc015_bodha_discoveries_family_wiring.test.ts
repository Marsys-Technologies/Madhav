/**
 * mc015_bodha_discoveries_family_wiring.test.ts — ŚODHANA-ŚEṢA W1 regression pin for MC-015.
 *
 * BUG (MC-015): PR #803 added ayanāṃśa-variant deduplication (`discovery_families`) to the
 * registry capability `marsys://tool/L2/query_discoveries` (platform/.../query_discoveries.ts).
 * On live production, `bodha_discoveries_get(domain="wealth", chart 482012f1)` kept returning
 * the SAME finding (aspect_parashari, house 1/4/9) repeated once per ayanāṃśa with NO
 * `discovery_families` collapse anywhere in the response.
 *
 * ROOT CAUSE: `bodha_discoveries_get` (register_p1_synthesis.ts) was never a proxy to the
 * registry capability at all — it ran its own hand-rolled SQL directly against
 * `bodha_discoveries` (a leftover from the R6 0b-deadtools/R-9 schema-drift fix), so it could
 * never see `discovery_families` no matter how correct the registry capability's collapse
 * logic was. The sibling `kala_projections_get` (register_p1_aliases.ts) never had this
 * problem because it was ALREADY a thin proxy to `marsys://tool/L3/query_projections` — it
 * picked up `projection_families` for free the moment PR #803 landed.
 *
 * This test reproduces the real repeated-finding shape (one aspect_parashari house-1/4/9
 * motif duplicated across 5 ayanāṃśas) as the mocked registry-capability response, and pins
 * two things against the ACTUAL `server.tool(...)` callback (not a reimplementation):
 *   1. `bodha_discoveries_get` calls the registry capability endpoint
 *      (`/api/retrieval/capability`, uri `marsys://tool/L2/query_discoveries`) — NOT the raw
 *      DB-query endpoint (`/api/mcp/db/query`) — for its data.
 *   2. The tool's response surfaces `discovery_families` — collapsed to ONE family, carrying
 *      a cross-ayanāṃśa agreement score and a bounded member_discovery_ids list — pass-through
 *      from the registry capability, not re-derived.
 *
 * Against the PRE-fix code (raw SQL against bodha_discoveries, no registry proxy at all) this
 * test fails on both counts: no `/api/retrieval/capability` call is ever made, and the response
 * has no `discovery_families` field whatsoever (just the flat, duplicated `discoveries` array).
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
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHAS = ['lahiri_chitrapaksha', 'raman', 'kp_newcomb', 'yukteshwar', 'true_chitra']

// The real repeated-finding case: one aspect_parashari (house 1/4/9) motif, duplicated once
// per ayanāṃśa — exactly the shape live production served with NO collapse.
const RAW_ROWS = AYANAMSHAS.map((ayanamsha_id, i) => ({
  discovery_id: `disc-house149-${i}`,
  ayanamsha_id,
  discovery_class: 'aspect_parashari',
  discovery_subsystem: 'graha_drishti',
  non_obviousness_score: 0.71,
  consequence_score: 0.64,
  composite_discovery_rank: i + 1,
  novelty_class: 'cross_house_amplification',
  corroboration_count: 3,
  corroborating_methods_array: ['parashari', 'jaimini'],
  affected_domains_array: ['wealth'],
  surface_reading: 'Surface: houses 1/4/9 linked by aspect.',
  depth_reading: 'Depth: the 1/4/9 linkage amplifies dharma-artha continuity.',
  surface_depth_delta: 0.3,
  hypothesis_text: 'Mutual aspect ties lagna, sukha, and bhagya houses into one wealth motif.',
  why_an_acharya_misses_it: 'Single-house scanning misses the 1-4-9 triangulation.',
  meaningfulness_basis: 'multi_house_triangulation',
  constituent_refs_jsonb: {},
  cross_subsystem_refs_jsonb: {},
  computed_date: '2026-07-01',
}))

// The collapsed family view query_discoveries.ts (the registry capability) is responsible for
// computing — this is what the FIXED bodha_discoveries_get must pass through untouched.
const DISCOVERY_FAMILIES = [{
  discovery_class: 'aspect_parashari',
  discovery_subsystem: 'graha_drishti',
  hypothesis_text: 'Mutual aspect ties lagna, sukha, and bhagya houses into one wealth motif.',
  member_count: 5,
  ayanamsha_count: 5,
  ayanamsha_ids: AYANAMSHAS,
  ayanamsha_agreement: '5/5 ayanamshas agree',
  member_discovery_ids: RAW_ROWS.map(r => r.discovery_id),
  best_composite_discovery_rank: 1,
  max_non_obviousness_score: 0.71,
  max_consequence_score: 0.64,
  affected_domains_array: ['wealth'],
  affected_domains_variant_count: 1,
  surface_reading: 'Surface: houses 1/4/9 linked by aspect.',
  depth_reading: 'Depth: the 1/4/9 linkage amplifies dharma-artha continuity.',
  why_an_acharya_misses_it: 'Single-house scanning misses the 1-4-9 triangulation.',
  novelty_class: 'cross_house_amplification',
}]

const REGISTRY_CONTENT = {
  chart_id: CHART_ID,
  rows: RAW_ROWS,
  count: RAW_ROWS.length,
  total_matching: RAW_ROWS.length,
  more_available: false,
  discovery_families: DISCOVERY_FAMILIES,
  discovery_family_count: DISCOVERY_FAMILIES.length,
  total_family_count: DISCOVERY_FAMILIES.length,
  more_families_available: false,
  ayanamsha_universe_count: 5,
  filters: { ayanamsha_id: null, discovery_class: null, domain: 'wealth', limit: 30, offset: 0 },
  provenance: { tables: ['bodha_discoveries'], source: 'test', note: 'test' },
}

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
})

describe('bodha_discoveries_get (MC-015) — registry proxy wiring + discovery_families pass-through', () => {
  it('calls the registry capability (marsys://tool/L2/query_discoveries), never raw SQL against bodha_discoveries', async () => {
    const capabilityCalls: Array<{ uri: string; args: Record<string, unknown> }> = []
    const dbQueryCalls: string[] = []

    vi.stubGlobal('fetch', vi.fn(async (url: string, opts: { body: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/retrieval/capability')) {
        const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
        capabilityCalls.push(body)
        return { ok: true, json: async () => ({ ok: true, content: REGISTRY_CONTENT }), text: async () => '' }
      }
      if (url.includes('/api/mcp/db/query')) {
        const body = JSON.parse(opts.body) as { sql?: string }
        if (body.sql) dbQueryCalls.push(body.sql)
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_discoveries_get')!

    const result = await handler({ chart_id: CHART_ID, domain: 'wealth' })
    expect(result.isError).toBeFalsy()

    // The wiring fix: this call MUST go through the registry capability...
    expect(capabilityCalls.length).toBeGreaterThan(0)
    expect(capabilityCalls[0]!.uri).toBe('marsys://tool/L2/query_discoveries')
    expect(capabilityCalls[0]!.args['chart_id']).toBe(CHART_ID)
    expect(capabilityCalls[0]!.args['domain']).toBe('wealth')
    // ...and NEVER fall back to a raw SQL query against bodha_discoveries directly
    // (the pre-fix code path — the exact bug this test pins against).
    expect(dbQueryCalls.some(sql => sql.includes('FROM bodha_discoveries'))).toBe(false)
  })

  it('surfaces discovery_families collapsed to ONE motif with a cross-ayanamsha agreement score and member refs, for the repeated house-1/4/9 aspect_parashari case', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string, opts: { body: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/retrieval/capability')) {
        const body = JSON.parse(opts.body) as { uri: string }
        expect(body.uri).toBe('marsys://tool/L2/query_discoveries')
        return { ok: true, json: async () => ({ ok: true, content: REGISTRY_CONTENT }), text: async () => '' }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_discoveries_get')!

    const result = await handler({ chart_id: CHART_ID, domain: 'wealth' })
    expect(result.isError).toBeFalsy()

    const content = (result.structuredContent?.object as {
      content: {
        rows: unknown[]
        discoveries: unknown[]
        discovery_families?: Array<{
          discovery_class: string
          ayanamsha_agreement: string
          member_discovery_ids: string[]
        }>
      }
    }).content

    // Pre-fix: this field simply does not exist on the response at all.
    expect(content.discovery_families).toBeDefined()
    expect(Array.isArray(content.discovery_families)).toBe(true)
    // The house-1/4/9 aspect_parashari motif, repeated 5x raw, collapses to ONE family.
    expect(content.discovery_families!.length).toBe(1)

    const family = content.discovery_families![0]!
    expect(family.discovery_class).toBe('aspect_parashari')
    // Cross-ayanāṃśa agreement score, e.g. "5/5 ayanamshas agree".
    expect(family.ayanamsha_agreement).toMatch(/^\d+\/\d+ ayanamshas agree$/)
    // Bounded member refs — more than one raw discovery collapsed into this family.
    expect(family.member_discovery_ids.length).toBeGreaterThan(1)

    // Back-compat fields this tool has always exposed remain populated too.
    expect(content.discoveries.length).toBe(RAW_ROWS.length)
  })
})
