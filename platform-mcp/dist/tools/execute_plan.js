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
import { z } from 'zod';
import { callPlatform } from '../client.js';
// ── Input schema ──────────────────────────────────────────────────────────────
const ExecutePlanInputSchema = z.object({
    // The plan is a JSON object (PipelinePlan); we accept it as an unknown
    // value here and let the platform re-validate against PipelinePlanSchema.
    plan: z
        .unknown()
        .describe('A PipelinePlan object, typically from plan_query output (optionally edited).'),
});
// ── Tool registration ─────────────────────────────────────────────────────────
/**
 * Register the execute_plan MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerExecutePlan(server, getPrincipal) {
    // PLACEHOLDER description — full §4.6 description lands in MCP-2-S2.
    const placeholderDescription = 'Executes an explicit PipelinePlan (from plan_query, optionally edited). ' +
        'Enables plan inspection + modification + re-execution workflows. [Full ' +
        'description: MCP-2-S2]';
    server.tool('execute_plan', placeholderDescription, ExecutePlanInputSchema.shape, async (args) => {
        const principal = getPrincipal();
        const { status, envelope } = await callPlatform({
            tool: 'execute_plan',
            params: { plan: args.plan },
        }, principal);
        const text = JSON.stringify(envelope, null, 2);
        if (!envelope.ok || status >= 400) {
            return {
                content: [{ type: 'text', text }],
                isError: true,
            };
        }
        return {
            content: [{ type: 'text', text }],
        };
    });
}
//# sourceMappingURL=execute_plan.js.map