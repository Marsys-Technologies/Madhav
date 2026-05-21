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
  // §4.6-standard description — authored MCP-2-S2.
  //
  // What it does: Runs only the planner stage of the MARSYS-JIS pipeline and
  // returns the PipelinePlan JSON without executing any retrieval or synthesis.
  // The response shows which query class the planner assigned, which retrieval
  // tools would fire (with priority and estimated token cost), and the proposed
  // audience-tier budget — all before any compute is committed.
  //
  // When to prefer: Use plan_query for differential analysis: call it, inspect
  // or edit the plan (swap tools, adjust priority, change mode), then pass the
  // result to execute_plan. Also use it to understand why a prior ask_madhav
  // call chose certain tools — call plan_query with the same query and compare.
  // Do not use plan_query when you simply want an answer; use ask_madhav instead.
  //
  // Input shape hints:
  //   query — the question string, identical format to ask_madhav. The planner
  //     interprets natural-language intent to assign a query_class and select
  //     the appropriate retrieval tools. No mode or context_hint here — if you
  //     need mode control, set it in the plan object before passing to execute_plan.
  //
  // Output shape preview: {ok, plan: {query_class, tool_calls[], audience_tier,
  //   mode, ...}, trace_id, epistemics}.
  //
  // Example: plan_query({query: "Predict career outcome for Q3 2026"}) →
  //   {ok: true, plan: {query_class: "predictive",
  //   tool_calls: [{tool: "msr_sql", priority: 1},
  //   {tool: "query_dasha_periods", priority: 2}], ...},
  //   trace_id: "qry_2026-05-21_b7a1c3"}
  const fullDescription =
    'What it does: Runs only the planner stage of the MARSYS-JIS pipeline and ' +
    'returns the PipelinePlan JSON without executing any retrieval or synthesis. ' +
    'The response shows which query class the planner assigned, which retrieval ' +
    'tools would fire (with priority and estimated token cost), and the proposed ' +
    'audience-tier budget — all before any compute is committed.\n\n' +
    'When to prefer: Use plan_query for differential analysis: call it, inspect ' +
    'or edit the plan, then pass the result to execute_plan. Also use it to ' +
    'understand why a prior ask_madhav call chose certain tools — call plan_query ' +
    'with the same query and compare. Do not use plan_query when you simply want ' +
    'an answer; use ask_madhav instead.\n\n' +
    'Input shape hints: query — the question string, identical format to ask_madhav. ' +
    'The planner interprets natural-language intent to assign a query_class and ' +
    'select the appropriate retrieval tools. No mode or context_hint parameter here ' +
    '— set mode in the plan object before passing to execute_plan if needed.\n\n' +
    'Output shape preview: {ok, plan: {query_class, tool_calls[], audience_tier, ' +
    'mode, ...}, trace_id, epistemics}.\n\n' +
    'Example: plan_query({query: "Predict career outcome for Q3 2026"}) → ' +
    '{ok: true, plan: {query_class: "predictive", ' +
    'tool_calls: [{tool: "msr_sql", priority: 1}, ' +
    '{tool: "query_dasha_periods", priority: 2}], ...}, ' +
    'trace_id: "qry_2026-05-21_b7a1c3"}'

  server.tool(
    'plan_query',
    fullDescription,
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
