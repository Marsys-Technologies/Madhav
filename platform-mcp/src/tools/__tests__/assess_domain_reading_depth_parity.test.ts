/**
 * assess_domain_reading_depth_parity.test.ts — reconciled exit test for F-14 + F-124
 * (PARISESA-V4 REBASE, code train 3 of 3).
 * =========================================================================
 * F-14 (`par/night-F-14`, 5f8a129b4) and F-124 (`par/night-F-124`, 5f8871bcd) were two
 * independently-ratified COMPLETE fixes for the same underlying defect family (CL-14:
 * assess_career vs assess_marriage/assess_health depth asymmetry — see the reconciliation
 * record at 00_ARCHITECTURE/briefs/parisesa/state/phase0/rebase_f14_f124.json). Both touched
 * the exact same lines of registry_bridge.ts (DOMAIN_READING_FAMILIES + companion maps,
 * buildAssessResponse's completeness key check, and the assess_marriage/assess_health call
 * sites). This file supersedes both branches' exit tests
 * (assess_domain_reading_parity.test.ts from F-14, F124_domain_reading_wiring.test.ts from
 * F-124) with one file covering the reconciled fix.
 *
 * Defects fixed (all independently verifiable against current main before this fix):
 *  1. DOMAIN_READING_FAMILIES (+ companion VARGAS/HOUSES/KARAKA maps) had only 'wealth'/
 *     'career' keys -> buildDomainReading early-returned families_total=0 for health/
 *     relationship, so assess_health/assess_marriage never got a `reading` field at all.
 *  2. assess_marriage / assess_health handlers never called attachDomainCompleteness /
 *     attachDomainReading (assess_career/assess_wealth did).
 *  3. buildAssessResponse's grounding allow-list checked response['completeness'] — a key
 *     nothing ever sets — instead of response['domain_completeness'] /
 *     response['completeness_directive'], silently dropping both from ALL FOUR assess_*
 *     tools' output, including the ostensibly-working wealth/career pair.
 *  4. (F-14's exclusive contribution, not present in F-124) attachDomainCompleteness's no-op
 *     path (no precompiled concept-slice bundle for a domain) silently returned with no
 *     disclosure — now sets domain_completeness_empty_reason so a caller can tell "nothing to
 *     report" apart from "this domain was never wired" (B.10 / CLAUDE.md §N.7 item 6).
 *  5. (F-124's exclusive contribution, not present in F-14) buildDomainReading's per-varga
 *     family labels were hardcoded to a wealth/career ternary — applying only the map widening
 *     without also fixing this call site would have mislabeled health's D6 family "Dasamsa —
 *     career/status" and fabricated a nonexistent second varga for single-varga domains. Fixed
 *     with per-domain labels and a guarded (not fabricated) vargas[1].
 */
import { describe, test, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  DOMAIN_READING_FAMILIES,
  DOMAIN_READING_VARGAS,
  attachDomainCompleteness,
  attachDomainReading,
} from '../registry_bridge.js'

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: Record<string, unknown> }
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

beforeEach(() => { vi.unstubAllGlobals() })

/**
 * Call a tool through the real MCP registration seam (makeCapturingServer), with fetch
 * stubbed to avoid live DB/network calls. The L-DOMAIN capability is stubbed to return an
 * empty-but-valid content envelope; supplement calls (argala, mechanisms, etc.) are allowed
 * to throw — safeCall() in fetchReadingSupplements catches those and returns an honest
 * __fetch_error tag, which the family readers handle as domain_block_not_served.
 */
async function callTool(
  toolName: string,
  args: Record<string, unknown>,
): Promise<{ structuredContent: { type: 'object'; object: Record<string, unknown> } }> {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: RequestInit) => {
    const body = JSON.parse(opts.body as string) as { uri: string; args: Record<string, unknown> }
    const uri = body.uri
    if (uri === 'marsys://tool/L2/query_ucd') {
      return { ok: true, json: async () => ({ ok: true, content: { chart_id: args['chart_id'], digest: {}, entity_profiles: [] } }) }
    }
    if (uri.startsWith('marsys://tool/L-DOMAIN/')) {
      // Return a minimal valid L-DOMAIN bundle — no varga_analysis, no contradictions.
      // buildDomainReading will produce domain_block_not_served entries for all families
      // that depend on varga data, which is fine: families_total > 0, so reading IS set.
      return { ok: true, json: async () => ({ ok: true, content: { content: {}, is_error: false } }) }
    }
    // All other supplement URIs (L1/chart_facts_query, L2/query_mechanisms, etc.) —
    // throw so safeCall() catches and tags them as __fetch_error (benign).
    throw new Error(`assess_domain_reading_depth_parity stub: no stub for uri "${uri}"`)
  }))

  const { registerRegistryBridgeTools } = await import('../registry_bridge.js')
  const { server, handlers } = makeCapturingServer()
  registerRegistryBridgeTools(server, PRINCIPAL)

  const result = await handlers.get(toolName)!(args)
  if (result.isError) {
    throw new Error(`Tool "${toolName}" returned an error: ${JSON.stringify(result.structuredContent?.object)}`)
  }
  return result as { structuredContent: { type: 'object'; object: Record<string, unknown> } }
}

describe('unit: domain maps wired for all four assess_* domains', () => {
  test('DOMAIN_READING_FAMILIES has non-empty health + relationship arrays', () => {
    for (const domain of ['health', 'relationship'] as const) {
      const families = DOMAIN_READING_FAMILIES[domain]
      expect(families).toBeDefined()
      expect(Array.isArray(families)).toBe(true)
      expect((families as readonly string[]).length).toBeGreaterThan(0)
    }
  })

  test('DOMAIN_READING_VARGAS carries the FULL corrected varga set per domain (F-164)', () => {
    // F-164 (GA-5 follow-up on #1419): these were single-varga literals that had drifted
    // from brahma_vichara_constants.operative_vargas (health/relationship were both missing
    // their D9 rāśi-promise cross-check leg; relationship was also missing D7).
    expect(DOMAIN_READING_VARGAS['health']).toEqual(['D6', 'D9'])
    expect(DOMAIN_READING_VARGAS['relationship']).toEqual(['D9', 'D7'])
    expect(DOMAIN_READING_VARGAS['wealth']).toEqual(['D2', 'D9', 'D11'])
    expect(DOMAIN_READING_VARGAS['career']).toEqual(['D10', 'D9'])
  })

  test('attachDomainReading sets response[reading] for health domain (unit level)', async () => {
    const response: Record<string, unknown> = {}
    attachDomainCompleteness(response, 'health', CANONICAL_CHART_ID)
    await attachDomainReading(response, 'health', CANONICAL_CHART_ID, 'LAHIRI', PRINCIPAL)
    expect(response['reading']).toBeDefined()
    expect(Array.isArray(response['reading'])).toBe(true)
    expect(response['completeness_directive']).toBeDefined()
  }, 10_000)
})

describe('integration: all four assess_* tools via the real MCP handler seam', () => {
  test('reading digest: all four assess_* tools surface substance-inline reading', async () => {
    for (const tool of ['assess_wealth', 'assess_career', 'assess_marriage', 'assess_health']) {
      const res = await callTool(tool, { chart_id: CANONICAL_CHART_ID })
      const grounding = res.structuredContent.object.grounding as Record<string, unknown>
      expect(grounding).toHaveProperty('reading')
      expect(Array.isArray(grounding.reading)).toBe(true)
      expect((grounding.reading as unknown[]).length).toBeGreaterThan(0)
    }
  })

  test('health reading digest carries correctly-labeled families, not a copy-pasted career/wealth label', async () => {
    // Guards defect #5: applying only the map-widening half of the fix (without also fixing
    // buildDomainReading's per-varga label ternary) would silently mislabel health's D6 family
    // "Dasamsa — career/status" — a wrong classical-chart claim, not merely a missing one.
    const res = await callTool('assess_health', { chart_id: CANONICAL_CHART_ID })
    const grounding = res.structuredContent.object.grounding as Record<string, unknown>
    const reading = grounding.reading as Array<{ family: string; sentences: string[] }>
    const d6Family = reading.find((r) => r.family === 'divisional_D6')
    expect(d6Family).toBeDefined()
    const d6Text = d6Family!.sentences.join(' ')
    expect(d6Text).toMatch(/Ṣaṣṭhāṃśa|health\/vitality/)
    expect(d6Text).not.toMatch(/career\/status|Dasamsa/i)
    // relationship (assess_marriage) must not fabricate a second (D1) varga family either.
    const marriageRes = await callTool('assess_marriage', { chart_id: CANONICAL_CHART_ID })
    const marriageGrounding = marriageRes.structuredContent.object.grounding as Record<string, unknown>
    const marriageReading = marriageGrounding.reading as Array<{ family: string }>
    expect(marriageReading.some((r) => r.family === 'divisional_D9')).toBe(true)
    expect(marriageReading.some((r) => r.family === 'divisional_D1')).toBe(false)
  })

  test('completeness accounting: honest presence OR honest absence-disclosure, never silent', async () => {
    // career/wealth: precompiled dossier bundles exist -> real domain_completeness populated.
    for (const tool of ['assess_wealth', 'assess_career']) {
      const grounding = (await callTool(tool, { chart_id: CANONICAL_CHART_ID })).structuredContent.object.grounding as Record<string, unknown>
      expect(grounding).toHaveProperty('domain_completeness')
      expect(grounding).toHaveProperty('completeness_directive')
      expect(grounding).not.toHaveProperty('domain_completeness_empty_reason')
    }
    // health/marriage: no precompiled bundle today -> honest empty-reason disclosure, NOT a
    // silent omission and NOT a fabricated map.
    for (const tool of ['assess_marriage', 'assess_health']) {
      const grounding = (await callTool(tool, { chart_id: CANONICAL_CHART_ID })).structuredContent.object.grounding as Record<string, unknown>
      expect(grounding).not.toHaveProperty('domain_completeness')
      expect(grounding).toHaveProperty('domain_completeness_empty_reason')
      expect(String(grounding.domain_completeness_empty_reason)).toMatch(/no precompiled/i)
    }
  })
})
