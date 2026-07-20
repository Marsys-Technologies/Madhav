/**
 * phala_mitigation_map.ts — MCP tool: mitigation_map
 * Layer L4 · Phala (Predictive Engine) · Asset PH-4-2 (phala.mitigation)
 * BRAHMA-PH-4-2
 *
 * Exposes the phala_mitigation table as an MCP-callable tool.
 *
 * Tool: mitigation_map(chart_id, anchor_id?) →
 *   {mitigations: [{anchor_id, mitigation_type, mitigation_text, source_l0_rule_id, source_citation, ...}],
 *    provenance_envelope}
 *
 * Contract:
 *   - mitigation_type ∈ {'mantra','charity','gemstone','ritual','timing'}
 *   - source_citation non-null on every mitigation row (BPHS chapter/verse or BG-0-7 concordance)
 *   - source_l0_rule_id traces to concordance_lookup.id or a BPHS-FALLBACK-* key
 *   - provenance_envelope present on every response
 *
 * Depends on:
 *   - PH-4-1 (phala.anchors): phala_anchors table
 *   - BG-0-7 (brahmagyan.concordance): concordance_lookup (L0 rule source)
 *   - BO-2-6 (bodha.remediation): optional L2 cross-reference
 *
 * FORENSIC ground: reference birth 1984-02-05 10:43 IST Bhubaneswar.
 * Every mitigation is grounded to BPHS/concordance — zero hallucinated remedies.
 *
 * Architecture:
 *   MCP tool → callPlatformPrimitive('/api/mcp/primitives/mitigation_map')
 *   → platform route → phala_mitigation DB table
 *
 * surgical: true (pure retrieval; no LLM calls)
 */

import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── Input schema ───────────────────────────────────────────────────────────────

export const MitigationMapInputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to retrieve mitigations for. Must be a valid chart UUID from the charts table.'
    ),
  anchor_id: z
    .string()
    .optional()
    .describe(
      'Optional: restrict results to a specific event anchor (phala_anchors.anchor_id). ' +
      'Omit to return mitigations across all anchors for this chart.'
    ),
  mitigation_type: z
    .enum(['mantra', 'charity', 'gemstone', 'ritual', 'timing'])
    .optional()
    .describe(
      'Optional: filter by classical remedy category. ' +
      'mantra — japa/stotra; charity — dāna; gemstone — ratna; ' +
      'ritual — homa/puja; timing — muhurta/electional. ' +
      'Omit to return all types.'
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(200)
    .default(100)
    .describe('Maximum number of mitigation rows to return. Default 100.'),
})

export type MitigationMapInput = z.infer<typeof MitigationMapInputSchema>

// ── Output shape (documented; actual shape comes from the platform) ────────────

/**
 * One mitigation row returned by mitigation_map.
 *
 * source_citation always traces to a BPHS chapter/verse or L0 concordance rule_id:
 *   - "BPHS.<chapter>.<verses>" (e.g. BPHS.25.41-56)
 *   - or a concordance_lookup.source_citation value
 *
 * source_l0_rule_id traces to concordance_lookup.id or a BPHS-FALLBACK-* key,
 * both resolving to BPHS canonical source material (BG-0-7).
 *
 * Grounding contract: source_citation is NON-NULL on every row — enforced at
 * the writer level (PH-4-2 mitigation.py) and at the DB level (NOT NULL column).
 */
export interface MitigationRow {
  anchor_id: string
  theme: string | null
  mitigation_type: 'mantra' | 'charity' | 'gemstone' | 'ritual' | 'timing'
  mitigation_text: string
  source_l0_rule_id: string
  source_citation: string            // NEVER null — BPHS chapter/verse or concordance ref
  l2_remediation_hub_id: string | null
  asset_version: string
  computed_at: string
}

export interface ProvenanceEnvelope {
  chart_id: string
  anchor_id_filter: string | null
  mitigation_type_filter: string | null
  asset: string                      // 'phala.mitigation'
  asset_version: string              // '1.0'
  build_tag: string                  // 'PH-4-2'
  source: string                     // 'phala.mitigation'
  computed_at: string
}

export interface MitigationMapResult {
  mitigations: MitigationRow[]
  total_count: number
  all_cited: boolean                 // true iff every mitigation has source_citation
  provenance_envelope: ProvenanceEnvelope
}

// ── Tool description ───────────────────────────────────────────────────────────

export const MITIGATION_MAP_DESCRIPTION =
  'Returns per-anchor classical mitigations for a Jyotish chart ' +
  '(phala.mitigation / PH-4-2). ' +
  'Each mitigation maps one event anchor (phala.anchors / PH-4-1) to a classical remedy ' +
  'grounded in L0 concordance (BG-0-7 / BPHS) and cross-referenced with ' +
  'L2 bodha.remediation (BO-2-6). ' +
  'source_citation is NON-NULL on every row — always traces to a specific BPHS ' +
  'chapter/verse (e.g. BPHS.25.41-56) or a concordance_lookup.source_citation value. ' +
  'mitigation_type ∈ {mantra, charity, gemstone, ritual, timing}. ' +
  'Use anchor_id to narrow to a single event anchor. ' +
  'Use mitigation_type to filter by remedy category. ' +
  'Response always includes a provenance_envelope with asset, build_tag, and computed_at. ' +
  'surgical: true — pure retrieval, no LLM synthesis. ' +
  'surgical: true — pure retrieval, no LLM synthesis.'

// ── Tool handler ───────────────────────────────────────────────────────────────

/**
 * mitigation_map MCP tool handler.
 *
 * Delegates to /api/mcp/primitives/mitigation_map on the platform service.
 * Returns the platform's MitigationMapResult with provenance_envelope.
 *
 * Error contract:
 *   - If phala_anchors (PH-4-1) is not yet built, the platform returns an error
 *     envelope with class "not_found"; we pass it through.
 *   - If chart_id has no anchor data, returns an empty mitigations array (not an error).
 *   - If anchor_id does not exist for this chart, returns an empty mitigations array.
 */
export async function handleMitigationMap(
  input: MitigationMapInput,
  principal: Principal
): Promise<unknown> {
  const authorized = await remoteAuthorize(principal, input.chart_id)
  if (!authorized) {
    return {
      content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }],
      isError: true,
    }
  }

  const params: Record<string, unknown> = {
    chart_id: input.chart_id,
    limit: input.limit,
  }
  if (input.anchor_id) {
    params['anchor_id'] = input.anchor_id
  }
  if (input.mitigation_type) {
    params['mitigation_type'] = input.mitigation_type
  }

  const result = await callPlatformPrimitive('mitigation_map', params, principal)
  const env = result.envelope
  if (!env.ok) return env

  // WP-1.3j serving-bug fix (F-L10-024): the surgical primitives route returns a
  // ToolBundle — env.result = { results: [{ content: "<json string>" }], ... } — whose
  // content is the query_remedy_program capability payload keyed `remedies` (NOT
  // `mitigations`). The prior wrapper read env.result.mitigations directly, which is
  // undefined on a ToolBundle → it always yielded an EMPTY mitigations array despite
  // 600+ real rows/chart. Fix: unwrap the ToolBundle, parse the content, and surface
  // the real `remedies` (bounded + total disclosed by the capability).
  const capContent = unwrapCapabilityContent(env.result)
  const rawRemedies = Array.isArray(capContent?.['remedies'])
    ? (capContent!['remedies'] as Record<string, unknown>[])
    : []
  const totalMatching = typeof capContent?.['total_matching'] === 'number'
    ? (capContent!['total_matching'] as number)
    : rawRemedies.length
  const moreAvailable = capContent?.['more_available'] === true

  // Real phala_mitigation rows cite via `classical_citation` (NOT the fictional
  // source_citation the old shim assumed). Report citation coverage honestly.
  const uncited = rawRemedies.filter((m) => !m['classical_citation'] && !m['source_citation'])
  if (uncited.length > 0) {
    console.warn(`[PH-4-2] mitigation_map: ${uncited.length}/${rawRemedies.length} rows lack a classical_citation.`)
  }

  const provenanceEnvelope: ProvenanceEnvelope = {
    chart_id: input.chart_id,
    anchor_id_filter: input.anchor_id ?? null,
    mitigation_type_filter: input.mitigation_type ?? null,
    asset: 'phala.mitigation',
    asset_version: '1.0',
    build_tag: 'PH-4-2',
    source: 'phala_mitigation',
    computed_at: new Date().toISOString(),
  }

  return {
    ...env,
    result: {
      // `mitigations` retained as the documented key; `remedies` mirrors the capability's
      // native key so either consumer shape resolves to the real rows.
      mitigations: rawRemedies as unknown as MitigationRow[],
      remedies: rawRemedies,
      total_count: totalMatching,
      returned_count: rawRemedies.length,
      more_available: moreAvailable,
      all_cited: uncited.length === 0,
      provenance_envelope: provenanceEnvelope,
    },
  }
}

/**
 * Unwrap the surgical-primitives ToolBundle into the underlying capability content object.
 * The route wraps the capability payload as { results: [{ content: "<json string>" }] };
 * older/direct shapes (a plain content object) are passed through unchanged.
 */
function unwrapCapabilityContent(envResult: unknown): Record<string, unknown> | null {
  if (envResult == null || typeof envResult !== 'object') return null
  const r = envResult as Record<string, unknown>
  const bundleResults = r['results']
  if (Array.isArray(bundleResults) && bundleResults.length > 0) {
    const first = bundleResults[0] as Record<string, unknown> | undefined
    const content = first?.['content']
    if (typeof content === 'string') {
      try { return JSON.parse(content) as Record<string, unknown> } catch { return null }
    }
    if (content && typeof content === 'object') return content as Record<string, unknown>
  }
  // Direct content object fallback (already unwrapped).
  if ('remedies' in r || 'mitigations' in r) return r
  return null
}

// ── MCP server registration helper ────────────────────────────────────────────

/**
 * Register the mitigation_map tool on an McpServer instance.
 *
 * Usage in server.ts:
 *   import { registerMitigationMapTool } from './tools/phala_mitigation_map.js'
 *   registerMitigationMapTool(server, principal)
 *
 * The tool is surgical (pure retrieval) and appropriate for all principal tiers.
 *
 * Contract assertions:
 *   - source_citation non-null on all returned mitigations (BPHS/BG-0-7 grounding)
 *   - provenance_envelope present in every response
 *   - mitigation_type in {'mantra','charity','gemstone','ritual','timing'}
 */
export function registerMitigationMapTool(
  server: {
    tool: (
      name: string,
      description: string,
      schema: Record<string, unknown>,
      handler: (args: unknown) => Promise<unknown>
    ) => void
  },
  principal: Principal
): void {
  server.tool(
    'mitigation_map',
    MITIGATION_MAP_DESCRIPTION,
    {
      chart_id: z
        .string()
        .uuid()
        .describe(
          'UUID of the chart. Must be a valid chart UUID from the charts table.'
        ),
      anchor_id: z
        .string()
        .optional()
        .describe('Optional: filter to one event anchor (phala_anchors.anchor_id).'),
      mitigation_type: z
        .enum(['mantra', 'charity', 'gemstone', 'ritual', 'timing'])
        .optional()
        .describe(
          'Optional remedy category: mantra | charity | gemstone | ritual | timing.'
        ),
      limit: z
        .number()
        .int()
        .min(1)
        .max(200)
        .default(100)
        .describe('Max mitigation rows. Default 100.'),
    },
    async (args: unknown) => {
      // F-016: wrap in MCP content array — handleMitigationMap returns a raw envelope,
      // but MCP tools must return { content: [{ type: 'text', text: string }] }
      const parsed = MitigationMapInputSchema.parse(args)
      const result = budgetMcpContent(await handleMitigationMap(parsed, principal), 'mitigation_map')
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
      }
    }
  )
}
