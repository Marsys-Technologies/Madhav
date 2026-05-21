/**
 * execute_plan.ts — MCP tool: execute an explicit PipelinePlan.
 *
 * Tier 2 tool (MCP_BRIEF §4.1). Accepts a PipelinePlan JSON object (typically
 * the output of plan_query, optionally edited by the caller) and runs the
 * pipeline from arbitration onward. The platform re-validates the plan against
 * PipelinePlanSchema — no client-side re-validation required here.
 *
 * Together with plan_query, enables the differential-analysis workflow described
 * in MCP_BRIEF §3: plan → inspect/edit → execute → compare.
 *
 * Tool description is a PLACEHOLDER in this session (~30 words).
 * Full §4.6-standard description (120–180 words, 5 blocks) authors in MCP-2-S2.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatform } from '../client.js'
import type { Principal } from '../types.js'

// ── Input schema ──────────────────────────────────────────────────────────────

const ExecutePlanInputSchema = z.object({
  // The plan is a JSON object (PipelinePlan); we accept it as an unknown
  // value here and let the platform re-validate against PipelinePlanSchema.
  plan: z
    .unknown()
    .describe(
      'A PipelinePlan object, typically from plan_query output (optionally edited).'
    ),
})

type ExecutePlanInput = z.infer<typeof ExecutePlanInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the execute_plan MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerExecutePlan(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  // §4.6-standard description — authored MCP-2-S2.
  //
  // What it does: Executes an explicit PipelinePlan object — typically the
  // output of plan_query, optionally edited by the caller — and runs the full
  // MARSYS-JIS pipeline from arbitration onward (retrieval → synthesis →
  // epistemics). This is the second half of the differential-analysis workflow:
  // generate a plan with plan_query, edit it, then execute with this tool and
  // compare the result against the unmodified run.
  //
  // When to prefer: Use execute_plan when you need precise control over which
  // retrieval tools fire and in what priority order. The platform re-validates
  // the plan against PipelinePlanSchema before execution and re-checks
  // audience-tier-permitted tools — a client-tier caller cannot escalate
  // privileges by editing the plan. The B.11 Whole-Chart-Read floor is still
  // enforced for holistic queries even on edited plans. Use ask_madhav instead
  // when you do not need to inspect or modify the plan first.
  //
  // Input shape hints:
  //   plan — a PipelinePlan object, typically from plan_query output. Must be
  //     a structurally valid PipelinePlan; invalid plans return {ok: false,
  //     error: {class: "validation", ...}}. Editing tool_calls[] is the most
  //     common modification (add, remove, or reprioritize tools).
  //
  // Output shape preview: same envelope as ask_madhav — {ok, answer_markdown,
  //   citations[], trace_id, plan, synthesis_audit, suggested_followups[]}.
  //
  // Example: execute_plan({plan: {...planFromPlanQuery, tool_calls: [
  //   {tool: "msr_sql", priority: 1}, {tool: "cgm_graph_walk", priority: 1}]}})
  //   → {ok: true, answer_markdown: "...", citations: [...], trace_id: "qry_..."}
  const fullDescription =
    'What it does: Executes an explicit PipelinePlan object — typically the ' +
    'output of plan_query, optionally edited — and runs the full MARSYS-JIS ' +
    'pipeline from arbitration onward (retrieval → synthesis → epistemics). ' +
    'This is the second half of the differential-analysis workflow: generate ' +
    'a plan with plan_query, edit it, then execute with this tool and compare.\n\n' +
    'When to prefer: Use execute_plan when you need precise control over which ' +
    'retrieval tools fire and in what priority order. The platform re-validates ' +
    'the plan against PipelinePlanSchema and re-checks audience-tier-permitted ' +
    'tools — no privilege escalation via plan editing. The B.11 Whole-Chart-Read ' +
    'floor is still enforced for holistic queries even on edited plans. Use ' +
    'ask_madhav instead when you do not need to inspect or modify the plan first.\n\n' +
    'Input shape hints: plan — a PipelinePlan object from plan_query output. ' +
    'Must be structurally valid; invalid plans return {ok: false, error: ' +
    '{class: "validation", ...}}. Editing tool_calls[] is the most common ' +
    'modification (add, remove, or reprioritize retrieval tools).\n\n' +
    'Output shape preview: same envelope as ask_madhav — {ok, answer_markdown, ' +
    'citations[], trace_id, plan, synthesis_audit, suggested_followups[]}.\n\n' +
    'Example: execute_plan({plan: {...planFromPlanQuery, tool_calls: [' +
    '{tool: "msr_sql", priority: 1}, {tool: "cgm_graph_walk", priority: 1}]}}) ' +
    '→ {ok: true, answer_markdown: "...", citations: [...], trace_id: "qry_..."}'

  server.tool(
    'execute_plan',
    fullDescription,
    ExecutePlanInputSchema.shape,
    async (args: ExecutePlanInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatform(
        {
          tool: 'execute_plan',
          params: { plan: args.plan },
        },
        principal
      )

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
