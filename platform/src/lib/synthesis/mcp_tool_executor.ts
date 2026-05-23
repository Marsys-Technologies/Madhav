/**
 * mcp_tool_executor.ts — Real MCP tool executor for runAgenticLoop (R11.G-S1).
 *
 * Replaces the stub `toolExecutor` callback in runAgenticLoop invocations with
 * a function that dispatches tool calls through the MARSYS retrieval tool
 * registry — the same path the planner uses during its pre-fetch phase.
 *
 * Error handling: any failure returns a string starting with "ERROR: ".
 * The loop engine (safeExecuteTool) also wraps the executor, but we return
 * error strings here so the model receives a descriptive message and can react.
 * The loop must NOT abort on tool failure.
 *
 * Phase: R11.G-S1 (closes the F-S3 deliberate stub).
 */

import 'server-only'

import type { LoopToolCall } from './agentic_loop'
import { getTool } from '@/lib/retrieve/index'
import type { QueryPlan } from '@/lib/retrieve/types'

// ---------------------------------------------------------------------------
// Context type
// ---------------------------------------------------------------------------

/**
 * Minimum context required by executeMCPTool.
 * The queryPlan carries chart id, audience tier, and all retrieval context.
 * Accepts QueryPlan or the route-local LegacyQueryPlanShape (structurally compatible).
 */
export interface MCPToolExecutorCtx {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  queryPlan: QueryPlan | Record<string, any>
}

// ---------------------------------------------------------------------------
// executeMCPTool
// ---------------------------------------------------------------------------

/**
 * Execute a single MCP tool call and return its result serialised as a JSON
 * string consumable by the LLM.
 *
 * AC.G1.1 — function is exported for test access.
 * AC.G1.4 — any failure returns "ERROR: <msg>"; never throws.
 */
export async function executeMCPTool(
  toolCall: LoopToolCall,
  ctx: MCPToolExecutorCtx,
): Promise<string> {
  const tool = getTool(toolCall.name)
  if (!tool) {
    return (
      `ERROR: Unknown tool "${toolCall.name}". ` +
      `The tool is not registered in the MARSYS retrieval tool registry.`
    )
  }

  try {
    // Pass the agentic loop's tool input directly as planner params so the
    // tool can use the same params path as the planner-driven pre-fetch.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result = await tool.retrieve(ctx.queryPlan as any, toolCall.input)
    return JSON.stringify({
      tool: toolCall.name,
      results: result.results,
      result_count: result.results.length,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return `ERROR: Tool "${toolCall.name}" execution failed: ${message}`
  }
}
