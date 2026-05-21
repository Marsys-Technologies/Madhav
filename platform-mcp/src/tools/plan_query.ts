/**
 * plan_query.ts — MCP tool: pipeline planner (no execution).
 *
 * Tier 2 tool (MCP_BRIEF §4.1). Runs only the planner stage and returns the
 * PipelinePlan JSON. Enables inspection of what tools would run before
 * committing to execution. Use with execute_plan for differential workflows.
 *
 * Tool description is a PLACEHOLDER in this session (~30 words).
 * Full §4.6-standard description (120–180 words, 5 blocks) authors in MCP-2-S2.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPlan } from '../client.js'
import type { Principal } from '../types.js'

// ── Input schema ──────────────────────────────────────────────────────────────

const PlanQueryInputSchema = z.object({
  query: z.string().describe('The question to plan.'),
})

type PlanQueryInput = z.infer<typeof PlanQueryInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the plan_query MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerPlanQuery(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  // PLACEHOLDER description — full §4.6 description lands in MCP-2-S2.
  const placeholderDescription =
    'Returns the PipelinePlan JSON for the query without executing it. ' +
    'Inspect what tools would run before committing to execution. [Full ' +
    'description: MCP-2-S2]'

  server.tool(
    'plan_query',
    placeholderDescription,
    PlanQueryInputSchema.shape,
    async (args: PlanQueryInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPlan(args.query, principal)

      const text = JSON.stringify(envelope, null, 2)

      if (!envelope.ok || status >= 400) {
        return {
          content: [{ type: 'text' as const, text }],
          isError: true,
        }
      }

      return {
        content: [{ type: 'text' as const, text }],
      }
    }
  )
}
