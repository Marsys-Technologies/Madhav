/**
 * get_trace.ts — MCP Tier 5 observability tool: retrieve the full query trace.
 *
 * Returns the complete query_trace_steps payload for a prior MCP query.
 * Every step is included: classify, compose_bundle, each retrieval tool,
 * synthesis, and done. Includes inputs, outputs, latencies, token estimates.
 *
 * Per D12 (full transparency): no tier-based redaction. Full prompts,
 * payloads, and retrieval results are returned to all authenticated callers.
 * Operational implication: do not issue API keys to principals you would
 * not trust with full prompt and signal-ID visibility.
 *
 * When to prefer: Use get_trace after an ask_madhav call when you want to
 * understand what retrieval tools fired, which signals were retrieved, how
 * long each stage took, and what the synthesis prompt contained. Essential
 * for differential analysis (plan → edit → execute → compare traces).
 * Do NOT use get_trace for answering chart questions — use ask_madhav for that.
 *
 * Input: trace_id — the trace_id from any prior MCP tool response.
 * Output: {ok, result: {trace_id, steps: TraceStep[], step_count, latency_ms_total}}.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerGetTrace(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=get_trace.d.ts.map