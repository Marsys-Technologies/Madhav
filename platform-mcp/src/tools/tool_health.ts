/**
 * tool_health.ts — MCP tool: tool_health (perf brief §6.1)
 *
 * Returns aggregate health metrics for all registered MCP tools over the
 * last 24 hours. Tier-gated: super_admin + acharya only.
 *
 * MCPT v3.1.0-S4
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const TOOL_HEALTH_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns aggregate health metrics for all registered MCP tools over the last N hours ' +
    '(default 24h) — call counts, error rates, average latency, audit finding counts, and active caveats. ' +
    'Includes the tool↔asset reconciliation gate (G6) status from Unit 3.tool_asset_recon.',
  whenToPrefer:
    'Use to understand the operational state of the MCP server: which tools have elevated error rates, ' +
    'which have pending audit findings, and whether the post-2a tool↔asset reconciliation is GREEN. ' +
    'Do NOT use to answer chart questions — use query_signals or holistic_bundle for that.',
  tierNote: 'Available: all tiers (unconditional — R1 de-gating).',
})

/**
 * RECONCILIATION_GATE — Unit 3.tool_asset_recon G6 status snapshot.
 *
 * Updated on Stream-C commit; the live audit lives in
 * platform/src/lib/contract/tool_metadata.ts and is gated by
 * platform/src/lib/contract/__tests__/tool_asset_coverage.test.ts.
 *
 * If the gate flips RED at any point, regenerate this snapshot.
 */
const RECONCILIATION_GATE = {
  unit: '3.tool_asset_recon',
  gate: 'G6_tool_coverage',
  status: 'GREEN' as const,
  generated_at: '2026-05-28',
  assets: 19,
  tools: 77,
  orphans: 0,
  redundancies: 0,
  ayanamsha_mismatches: 0,
}

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const ToolHealthInputSchema = z.object({
  lookback_hours: z.number().int().min(1).max(168).optional().default(24).describe(
    'Hours to look back for metrics. Default: 24. Max: 168 (7 days).'
  ),
})

type ToolHealthInput = z.infer<typeof ToolHealthInputSchema>

export function registerToolHealth(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'tool_health',

    TOOL_HEALTH_DESCRIPTION,

    ToolHealthInputSchema.shape,

    async (input: ToolHealthInput) => {
      const principal = getPrincipal()

      try {
        const response = await fetch(`${PLATFORM_URL}/api/mcp/health/tools`, {
          method: 'GET',
          headers: {
            'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
            'X-MCP-User': principal.user_uid,
            // X-MCP-Audience-Tier removed (Stream A 3.tier_excision 2026-05-28).
            'X-MCP-Key-Id': principal.key_id,
          },
          signal: AbortSignal.timeout(10_000),
        })

        const data = await response.json() as Record<string, unknown>

        return okResult({
          ...data,
          lookback_hours: input.lookback_hours,
          reconciliation_gate: RECONCILIATION_GATE,
        } as unknown as { ok: boolean; [key: string]: unknown })
      } catch (err) {
        return errorResult({
          ok: false,
          trace_id: '',
          error: {
            class: 'internal',
            message: err instanceof Error ? err.message : String(err),
            remediation: 'Check platform connectivity',
          },
        })
      }
    }
  )
}
