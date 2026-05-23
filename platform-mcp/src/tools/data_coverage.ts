/**
 * data_coverage.ts — MCP tool: data_coverage (perf brief §6.2)
 *
 * Returns data coverage report: expected vs actual row counts per tool/category.
 * Surfaced from data_source_expected table + tool_caveats.
 * Tier-gated: super_admin + acharya only.
 *
 * MCPT v3.1.0-S4
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const DataCoverageInputSchema = z.object({
  tool_filter: z.string().optional().describe(
    'Optional tool name filter. If omitted, returns coverage for all tools.'
  ),
})

type DataCoverageInput = z.infer<typeof DataCoverageInputSchema>

export function registerDataCoverage(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'data_coverage',

    `What it does: Returns expected vs actual row counts per category. Categories backfilled
through MCPT v3.3 (KP, Tajaka, Shadbala, Ashtakavarga, Upagraha, Bhava-Bala) return
populated counts. Residuals tracked in \`mcp_audit_findings\`. Also surfaces active tool
caveats. Tier-gated: super_admin + acharya only.

When to prefer: Use data_coverage before calling a tool that relies on backfilled data
(query_chart_facts with category kp_cusp, varshphal, shadbala, etc.) to check if data
is actually present. Use tool_health for operational metrics; use data_coverage for
data availability. Do NOT use for chart interpretation — use query_signals for that.

Input: tool_filter (optional string to filter by tool name).

Output: {ok, coverage: [{tool, category, expected_rows, actual_rows, backfill_phase,
status, caveat?}], caveats: [{tool, caveat, severity}]}.

Tier restriction: super_admin + acharya only. client tier = 403.`,

    DataCoverageInputSchema.shape,

    async (input: DataCoverageInput) => {
      const principal = getPrincipal()

      // Tier gate
      if (principal.audience_tier === 'client' || principal.audience_tier === 'public_redacted') {
        return errorResult({
          ok: false,
          error: 'Forbidden',
          message: 'data_coverage is restricted to super_admin and acharya tiers.',
        })
      }

      try {
        const response = await fetch(`${PLATFORM_URL}/api/mcp/health/coverage`, {
          method: 'GET',
          headers: {
            'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
            'X-MCP-User': principal.user_uid,
            'X-MCP-Audience-Tier': principal.audience_tier,
            'X-MCP-Key-Id': principal.key_id,
          },
          signal: AbortSignal.timeout(10_000),
        })

        const data = await response.json() as {
          ok: boolean
          coverage?: Array<{ tool: string; [key: string]: unknown }>
          [key: string]: unknown
        }

        // Apply tool filter if requested
        if (input.tool_filter && data.coverage) {
          data.coverage = data.coverage.filter(c => c.tool === input.tool_filter)
        }

        return okResult(data)
      } catch (err) {
        return errorResult({
          ok: false,
          error: err instanceof Error ? err.message : String(err),
        })
      }
    }
  )
}
