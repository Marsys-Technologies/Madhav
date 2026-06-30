/**
 * retrieval/holistic_bundle.ts — BRAHMA-BO-2-9: B.11 Whole-Chart-Read composite tool
 *
 * B.11 Whole-Chart-Read discipline: every query routes through L2.5 Holistic
 * Synthesis first (MSR + CDLM + CGM + RM) before producing a domain-specific answer.
 *
 * This tool reads DIRECTLY from chart_facts (L1 + L2 bodha.* categories):
 *   1. ganita.positions   — L1 planet positions (Lahiri ayanamsha)
 *   2. bodha.signals      — L2 MSR signals (SCAFFOLD: 569 signals, all UNGROUNDED)
 *   3. bodha.domain_links — L2 CDLM cross-domain linkages
 *   4. bodha.resonance    — L2 RM resonance patterns
 *   5. bodha.graph        — L2 CGM edges (optional — enriches context)
 *
 * Tool name:  holistic_bundle
 * Input:      { chart_id?: string, include_graph?: boolean }
 * Output:     {
 *               positions, signals, domain_links, resonance, graph_edges?,
 *               grounding_status: 'SCAFFOLD',
 *               b11_floor_passed: boolean,
 *               provenance_envelope
 *             }
 *
 * Grounding status notice: ALL signals in this bundle carry:
 *   rule_id: null, grounding_status: 'UNGROUNDED'
 *   grounding_note: 'Scaffold pass — awaiting WS-3 rule_base'
 * This is a scaffold bundle. The l2-bodha-grounded session (after tag
 * ws3-rule-base-complete) re-derives with real rule IDs.
 *
 * Wiring: registerHolisticBundleRetrievalTool(server) in server.ts
 * Note: bo_2-8.ts (holistic_bundle via sidecar) remains registered in parallel.
 *
 * BRAHMA-BO-2-9 / l2-bodha-scaffold
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformPrimitive } from '../../client.js'
import type { Principal, McpEnvelopeError } from '../../types.js'

// REMEDIATION D7: NATIVE_CHART_ID removed. chart_id is now REQUIRED from caller.
// chart_agnostic_gate RULE-1/RULE-4: no default on chart_id.
// R2.1 (2026-06-30): Repointed from direct pg.Pool to callPlatformPrimitive —
// registry = served surface. No local Pool instantiation.

// ── Tool registration ──────────────────────────────────────────────────────────

export function registerHolisticBundleRetrievalTool(server: McpServer, getPrincipal: () => Principal): void {
  // REMEDIATION D7: chart_id is now REQUIRED (no default fallback to native chart).
  // chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
  // R2.1: delegates to callPlatformPrimitive('holistic_bundle', params) — no local Pool.
  server.tool(
    'holistic_bundle_chart_facts',
    {
      chart_id: z.string().uuid().describe(
        'Chart UUID. Required — no default chart.'
      ),
      include_graph: z.boolean().optional().default(false).describe(
        'Include bodha.graph (CGM edge set) in the bundle. Default: false.'
      ),
    },
    async ({ chart_id, include_graph = false }) => {
      if (!chart_id) {
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: 'chart_id is required', tool: 'holistic_bundle_chart_facts' }, null, 2) }],
          isError: true,
        }
      }

      try {
        const { status, envelope } = await callPlatformPrimitive(
          'holistic_bundle',
          { chart_id, include_graph },
          getPrincipal(),
        )

        if (status !== 200 || !envelope.ok) {
          return {
            content: [{
              type: 'text' as const,
              text: JSON.stringify({
                status: 'ERROR',
                error: (envelope as McpEnvelopeError).error?.message ?? status,
                chart_id,
                grounding_status: 'SCAFFOLD',
                b11_floor_passed: false,
              }, null, 2),
            }],
            isError: true,
          }
        }

        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify(envelope.result, null, 2),
          }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              status: 'ERROR',
              error: msg,
              chart_id,
              grounding_status: 'SCAFFOLD',
              b11_floor_passed: false,
            }, null, 2),
          }],
          isError: true,
        }
      }
    }
  )
}
