/**
 * query_signal_state.ts — MCP Tier 3 surgical primitive: date-indexed signal state lookup.
 *
 * What it does: Surfaces date-indexed signal lit/dormant/ripening rows from the
 * signal_states table (migration 023). Populated by platform/scripts/temporal/signal_activator.py.
 * Supports single-date, date-range, and multi-filter queries. Degrades gracefully when the
 * table is empty — returns a diagnostic note row rather than crashing.
 *
 * When to prefer: Use query_signal_state when you need to know which MSR signals are
 * 'lit', 'ripening', or 'dormant' on a given date (or date range). Prefer query_signals for
 * raw MSR signal corpus lookup without date-indexing. Prefer holistic_bundle when
 * cross-domain synthesis or interpretation is also required.
 *
 * Input shape hints:
 *   chart_id — optional UUID; defaults to native chart (Abhisek Mohanty).
 *   date — optional YYYY-MM-DD; single query date. When omitted, defaults to today UTC.
 *   end_date — optional YYYY-MM-DD; when provided, date becomes range start.
 *   state_filter — optional; restrict to 'lit', 'dormant', or 'ripening'.
 *   limit — optional; max rows to return (default 50, max 200).
 *
 * Output shape preview: {ok, result: {results: ToolBundleResult[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_signal_state({date: "2026-05-25", state_filter: "lit", limit: 20}) →
 *   {ok: true, result: {results: [{signal_id: "SIG.MSR.001", state: "lit", ...}]}, ...}
 *
 * Data source: signal_states table populated by signal_activator.py.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_SIGNAL_STATE_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Surfaces date-indexed signal activation states (lit/ripening/dormant) from the ' +
    'signal_states table for a given chart, date or date range, and optional state/signal-ID filters. ' +
    'Populated by signal_activator.py. Degrades gracefully when table is empty — returns diagnostic note. ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'signal_states table: 573+ MSR signals with daily lit/ripening/dormant states',
  whenToPrefer:
    'Use query_signal_state when you need to know which signals are lit/ripening/dormant on a specific date. ' +
    'Prefer query_signals for raw MSR signal corpus lookup without date-indexing. ' +
    'Prefer holistic_bundle when cross-domain synthesis or interpretation is also required.',
})

const QuerySignalStateInputSchema = z.object({
  chart_id: z.string().uuid().optional().describe(
    'UUID of a specific chart to scope the query to. Defaults to the native chart (Abhisek Mohanty).'
  ),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
    'Query date in YYYY-MM-DD format. When end_date is also provided, this becomes the range start. ' +
    'Defaults to today UTC when omitted.'
  ),
  end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
    'End date (YYYY-MM-DD) for a date-range query. When provided, date is treated as the range start.'
  ),
  state_filter: z.enum(['lit', 'dormant', 'ripening']).optional().describe(
    'Restrict results to signals in a specific state: "lit" (fully active), "ripening" (approaching peak), ' +
    'or "dormant" (inactive/background). When omitted, all states are returned.'
  ),
  signal_ids: z.array(z.string()).optional().describe(
    'Restrict results to specific MSR signal IDs (e.g. ["SIG.MSR.001", "SIG.MSR.002"]). ' +
    'When omitted, all signals are returned. Useful for checking activation state of known signals of interest.'
  ),
  dasha_system: z.string().optional().describe(
    'Restrict results to a specific dasha computation system (e.g. "vimshottari"). ' +
    'When omitted, all dasha systems are returned.'
  ),
  limit: z.number().int().min(1).max(500).optional().default(50).describe(
    'Max signal-state rows to return (default 50, max 500).'
  ),
})

type QuerySignalStateInput = z.infer<typeof QuerySignalStateInputSchema>

export function registerQuerySignalState(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_signal_state',
    QUERY_SIGNAL_STATE_DESCRIPTION,
    QuerySignalStateInputSchema.shape,
    async (args: QuerySignalStateInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_signal_state',
        {
          ...(args.chart_id !== undefined ? { chart_id: args.chart_id } : {}),
          // Portal tool uses query_date; map MCP's 'date' to 'query_date' for API compat
          ...(args.date !== undefined ? { query_date: args.date } : {}),
          ...(args.end_date !== undefined ? { end_date: args.end_date } : {}),
          // Portal tool uses states[] array; map single state_filter to states array
          ...(args.state_filter !== undefined ? { states: [args.state_filter] } : {}),
          ...(args.signal_ids && args.signal_ids.length > 0 ? { signal_ids: args.signal_ids } : {}),
          ...(args.dasha_system ? { dasha_system: args.dasha_system } : {}),
          limit: args.limit ?? 50,
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
