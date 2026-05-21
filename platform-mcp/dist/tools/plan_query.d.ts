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
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
/**
 * Register the plan_query MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export declare function registerPlanQuery(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=plan_query.d.ts.map