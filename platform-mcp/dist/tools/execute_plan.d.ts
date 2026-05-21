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
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
/**
 * Register the execute_plan MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export declare function registerExecutePlan(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=execute_plan.d.ts.map