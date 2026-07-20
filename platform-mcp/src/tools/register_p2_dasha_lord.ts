/**
 * register_p2_dasha_lord.ts — B8 derived-view MCP exposure (doctrine-waves D-1.5b, Lane B-7)
 * =================================================================================================
 * Exposes `marsys://tool/L1/get_dasha_lord_capability` (the new registry capability at
 * platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts) as a
 * dedicated MCP tool: `ganita_dasha_lord_capability_get` — following the `ganita_*_get`
 * naming convention every other L1 Gaṇita MCP tool uses (register_p1_ganita.ts).
 *
 * A NEW, self-contained file (own helper functions, no shared imports from
 * registry_bridge.ts / register_p1_ganita.ts) rather than an addition to either of those
 * large shared files — same anti-collision discipline the D9/D10 registry-side lanes used
 * (own new file only), since this wave's Lane B-6 is the declared single owner of the
 * TypeScript retrieval-registry/serving surface and this lane must not touch its files.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { budgetMcpContent } from '../lib/response_budget.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistryCapability(uri: string, args: Record<string, unknown>, principal: Principal): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[dasha_lord_capability] capability call failed (${res.status}): ${text.slice(0, 300)}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[dasha_lord_capability] capability error: ${data.error ?? 'unknown'}`)
  // Same one-level unwrap as register_p1_ganita.ts's callRegistryCapability (A4/CR-93-94):
  // the platform route wraps every handler's own {content, is_error} return under `content`.
  if (
    data.content && typeof data.content === 'object' && !Array.isArray(data.content) &&
    'is_error' in (data.content as Record<string, unknown>)
  ) {
    return (data.content as { content?: unknown }).content
  }
  return data.content
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// W3-L5 (budget unification): route through the shared auto-detect budget mechanism
// keyed off the `tool` field this file's handler stamps on every response.
function dualOutput(data: unknown) {
  let finalData = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const toolName = typeof obj['tool'] === 'string' ? obj['tool'] : 'unknown_tool'
    finalData = budgetMcpContent(obj, toolName)
  }
  const structuredContent = { type: 'object' as const, object: finalData }
  const json = JSON.stringify(finalData)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const data = { ok: false, error: { class: 'validation', message }, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
}

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function normalizeAyanamsha(id?: string): string {
  if (!id) return 'lahiri_chitrapaksha'
  return AYANAMSHA_ALIAS[id] ?? id
}

export function registerP2DashaLordTools(server: McpServer, principal: Principal): void {
  server.tool(
    'ganita_dasha_lord_capability_get',
    'B8 derived view (doctrine-waves D-1.5b): for every Vimśottarī Mahādaśā (MD) lord on this ' +
    'chart, serves {lord, house_class (kendra/trikona/dusthana/maraka/upachaya — ga_vichara\'s ' +
    'classify_actor classification), shadbala_percentile (rank among the 9 grahas by ' +
    'graha_shadbala_total.rupa), functional_lordship (stored graha_functional_class_per_ascendant), ' +
    'ratification_factor (ga_vichara varga_ratification, averaged across every domain this lord is ' +
    'a stored karaka for — null when the lord is karaka for no domain, honestly, not fabricated), ' +
    'and warning_tier (none/watch/elevated/high — a deterministic composite of the four signals ' +
    'above; never an LLM judgment, never a probability). Computed serving-layer aggregation over ' +
    'chart_dashas + chart_facts + chart_vichara — no new astronomical computation; every value ' +
    'traces to an existing fact via fact_ids. CLAUDE.md §N.6: every row is a confirmed, already-' +
    'computed value — there is no catalog-only layer on this surface.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
    },
    async ({ chart_id, ayanamsha_id }) => {
      if (!chart_id) return errorOutput('ganita_dasha_lord_capability_get', 'chart_id is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_dasha_lord_capability',
          { chart_id, ayanamsha_id: resolvedAyanamsha },
          principal,
        )
        return dualOutput({ tool: 'ganita_dasha_lord_capability_get', ...(data as Record<string, unknown>) })
      } catch (err) {
        return errorOutput('ganita_dasha_lord_capability_get', String(err), { chart_id })
      }
    },
  )
}
