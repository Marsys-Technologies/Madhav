/**
 * bodha_bo24.ts — BRAHMA BO-2-4: rm_walk tool
 *
 * Asset: bodha.resonance (RM resonance elements)
 * Contract: BRAHMA_L1_L5_REGISTRY_SEED_v1_0.md §C
 *
 * Tool: rm_walk(chart_id, element?) → resonance elements with provenance
 * Table: bodha_resonance (chart_id, ayanamsha_id, element_id, element_type,
 *                          strength, constituents, domains_primary,
 *                          net_resonance, source_citation)
 *
 * Source data: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md (canonical_id: RM, v2.2)
 * 37 elements (RM.01–RM.35 + RM.21A/B) for the native chart.
 *
 * Acceptance gate:
 *   - resonance elements present in response
 *   - every element carries non-null source_citation
 *   - provenance (constituents) non-null per element
 *
 * Architecture note (clean slate):
 *   The platform-mcp server is at tools:0 (clean slate). This tool is
 *   registered by calling registerRmWalk(server, principal) from server.ts.
 *   It calls /api/mcp/primitives/rm_walk on the platform, which proxies to
 *   the bodha_resonance table.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'

// ── Input schema ──────────────────────────────────────────────────────────────

const RmWalkSchema = z.object({
  /** Chart UUID to retrieve resonance elements for. */
  chart_id: z.string().uuid({
    message: 'chart_id must be a valid UUID (e.g. 362f9f17-95a5-490b-a5a7-027d3e0efda0)',
  }),

  /**
   * Optional specific element ID to retrieve (e.g. 'RM.01', 'RM.21A').
   * When omitted, returns all resonance elements for the chart.
   * Supports the full RM.NN pattern including letter suffixes (RM.21A, RM.21B).
   */
  element: z
    .string()
    .regex(/^RM\.\d+[A-Z]?$/, {
      message: "element must match RM.NN pattern, e.g. 'RM.01', 'RM.21A', 'RM.35'",
    })
    .optional(),

  /**
   * Ayanamsha identifier. Defaults to 'jh_true_chitra' (Lahiri/True Chitrapaksha).
   * Other values depend on what has been built for the chart.
   */
  ayanamsha_id: z.string().default('jh_true_chitra'),

  /**
   * Filter by element type.
   * Types: planet | house | lagna | dasha | yoga | meta | cross_varga | other
   */
  element_type: z
    .enum(['planet', 'house', 'lagna', 'dasha', 'yoga', 'meta', 'cross_varga', 'other'])
    .optional(),

  /**
   * Minimum strength threshold (0.0–1.0). Returns only elements with
   * strength ≥ this value. Useful for focusing on STRONGLY AMPLIFIED (≥0.90)
   * or TENSION-BEARING (≥0.75) elements.
   */
  min_strength: z.number().min(0).max(1).optional(),
})

export type RmWalkParams = z.infer<typeof RmWalkSchema>

// ── Tool description ──────────────────────────────────────────────────────────

const RM_WALK_DESCRIPTION = `\
What it does: Returns RM resonance elements from bodha.resonance (BO-2-4). \
Each element is a named resonance pattern from RM_v2_0.md (37 elements across \
RM.01–RM.35 including RM.21A/B). Every row carries source_citation, strength, \
constituents (MSR/CDLM anchors), and domains_primary for B.3 provenance compliance.

Outputs per element: element_id (e.g. RM.01), element_type (planet/house/lagna/\
dasha/yoga/meta/cross_varga), strength (0.0–1.0; 0.90=STRONGLY AMPLIFIED, \
0.75=TENSION-BEARING, 0.60=MIXED), constituents (MSR+CDLM anchor IDs), \
domains_primary, net_resonance (text summary), source_citation (non-null provenance).

When to prefer: Use rm_walk when you need the RM (Resonance Map) layer of the \
L2.5 holistic synthesis — resonance elements, their strengths, and MSR/CDLM anchor \
provenance. Pair with holistic_bundle (B.11 floor) for whole-chart synthesis. \
Use element= to drill into a single resonance (e.g. RM.17 Mercury MD activation). \
Use element_type='dasha' to surface temporal activation elements only. \
Use min_strength=0.90 to retrieve only STRONGLY AMPLIFIED elements. \
Prefer holistic_bundle over rm_walk when you need MSR+CGM+CDLM+RM in one call.`

// ── Registration ──────────────────────────────────────────────────────────────

/**
 * Register the rm_walk tool on the MCP server.
 *
 * rm_walk returns RM resonance elements from bodha_resonance with full
 * provenance (source_citation non-null, constituents non-null).
 *
 * @param server    The McpServer instance to register the tool on.
 * @param principal The resolved principal from Bearer key validation.
 */
export function registerRmWalk(server: McpServer, principal: Principal): void {
  server.registerTool(
    'rm_walk',
    {
      description: RM_WALK_DESCRIPTION,
      inputSchema: RmWalkSchema,
    },
    async (params: RmWalkParams) => {
      // Build query payload, omitting undefined optional fields
      const queryParams: Record<string, unknown> = {
        chart_id: params.chart_id,
        ayanamsha_id: params.ayanamsha_id,
      }
      if (params.element !== undefined) queryParams['element'] = params.element
      if (params.element_type !== undefined) queryParams['element_type'] = params.element_type
      if (params.min_strength !== undefined) queryParams['min_strength'] = params.min_strength

      const result = await callPlatformPrimitive('rm_walk', queryParams, principal)

      if (!result.envelope.ok) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  error: result.envelope.error,
                  tool: 'rm_walk',
                  asset: 'BO-2-4',
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        }
      }

      // Gate-1 contract: rm_walk returns {elements: [...], provenance_envelope: {...}}
      // result.envelope.result may be a flat array or already shaped; normalise here.
      const raw = result.envelope.result
      const elements: unknown[] = Array.isArray(raw)
        ? raw
        : (raw as { elements?: unknown[] })?.elements ?? []
      const provenanceEnvelope = Array.isArray(raw)
        ? {
            source_citation: elements.length > 0
              ? (elements[0] as { source_citation?: string })?.source_citation ?? null
              : null,
            constituents_sample: elements.length > 0
              ? (elements[0] as { constituents?: unknown[] })?.constituents ?? []
              : [],
            element_count: elements.length,
            asset_id: 'BO-2-4',
            tool: 'rm_walk',
          }
        : ((raw as { provenance_envelope?: unknown })?.provenance_envelope ?? {})

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(
              {
                elements,
                provenance_envelope: provenanceEnvelope,
              },
              null,
              2
            ),
          },
        ],
      }
    }
  )
}
