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
    '(default 24h) — call counts, error rates, average latency, audit finding counts, and active caveats.',
  whenToPrefer:
    'Use to understand the operational state of the MCP server: which tools have elevated error rates, ' +
    'which have pending audit findings. Essential for operator debugging. ' +
    'Do NOT use to answer chart questions — use query_signals or holistic_bundle for that.',
  tierNote: 'Available: all tiers (unconditional — R1 de-gating).',
})

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

        return okResult({ ...data, lookback_hours: input.lookback_hours } as unknown as { ok: boolean; [key: string]: unknown })
      } catch (err) {
        return errorResult({
          ok: false,
          error: err instanceof Error ? err.message : String(err),
        })
      }
    }
  )
}
