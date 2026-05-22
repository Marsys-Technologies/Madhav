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

    `What it does: Returns aggregate health metrics for all registered MCP tools over
the last N hours (default: 24). Metrics include call counts, error rates, average
latency, audit finding counts, and active tool caveats. Available to super_admin
and acharya tiers only; client tier receives 403 with house-rules reference.

When to prefer: Use tool_health when you want to understand the operational state
of the MCP server — which tools are being called most, which have elevated error
rates, which have pending audit findings. Essential for operator debugging.
Do NOT use tool_health to answer chart questions — use query_signals or holistic_bundle.

Input: lookback_hours (optional, default 24, max 168).

Output: {ok, generated_at, lookback_hours, tools: [{tool_name, call_count_24h,
error_rate, avg_latency_ms, audit_finding_count, caveats}]}.

Tier restriction: super_admin + acharya only. client tier = 403.`,

    ToolHealthInputSchema.shape,

    async (input: ToolHealthInput) => {
      const principal = getPrincipal()

      // Tier gate
      if (principal.audience_tier === 'client' || principal.audience_tier === 'public_redacted') {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: 'Forbidden',
                message: 'tool_health is restricted to super_admin and acharya tiers. See marsys://house-rules.',
              }),
            },
          ],
          isError: true,
        }
      }

      try {
        const response = await fetch(`${PLATFORM_URL}/api/mcp/health/tools`, {
          method: 'GET',
          headers: {
            'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
            'X-MCP-User': principal.user_uid,
            'X-MCP-Audience-Tier': principal.audience_tier,
            'X-MCP-Key-Id': principal.key_id,
          },
          signal: AbortSignal.timeout(10_000),
        })

        const data = await response.json() as Record<string, unknown>

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({ ...data, lookback_hours: input.lookback_hours }),
            },
          ],
        }
      } catch (err) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: err instanceof Error ? err.message : String(err),
              }),
            },
          ],
          isError: true,
        }
      }
    }
  )
}
