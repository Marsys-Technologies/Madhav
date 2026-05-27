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
 * When to prefer: Use get_trace after an holistic_bundle call when you want to
 * understand what retrieval tools fired, which signals were retrieved, how
 * long each stage took, and what the synthesis prompt contained. Essential
 * for differential analysis (plan → edit → execute → compare traces).
 * Do NOT use get_trace for answering chart questions — use holistic_bundle for that.
 *
 * Input: trace_id — the trace_id from any prior MCP tool response.
 * Output: {ok, result: {trace_id, steps: TraceStep[], step_count, latency_ms_total}}.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformTrace } from '../client.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const GET_TRACE_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns the full query_trace_steps ledger for a prior MCP query — ' +
    'every pipeline stage (classify, compose_bundle, each retrieval tool, synthesis, done) ' +
    'with inputs, outputs, latencies, and token estimates per step.',
  whenToPrefer:
    'Use get_trace after a holistic_bundle call to debug what happened, verify which tools fired, ' +
    'inspect the synthesis prompt, or understand per-stage latency. ' +
    'Use for differential analysis (plan → edit → execute → compare traces). ' +
    'Do NOT use get_trace to answer chart questions — that is holistic_bundle\'s job.',
})

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerGetTrace(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'get_trace',

    GET_TRACE_DESCRIPTION,

    // ── Input schema ──────────────────────────────────────────────────────────
    {
      trace_id: z
        .string()
        .min(8)
        .describe(
          'The trace_id from a prior MCP tool response. ' +
          'Also called query_id in the audit system. ' +
          'Format: UUID (e.g., "a4f3e2b1-0c1d-4e5f-a6b7-c8d9e0f1a2b3").'
        ),
    },

    // ── Handler ────────────────────────────────────────────────────────────────
    async ({ trace_id }) => {
      const principal = getPrincipal()

      const result = await callPlatformTrace(trace_id, principal)

      if (!result.envelope.ok) {
        const errEnv = result.envelope
        const errorMsg = 'error' in errEnv
          ? `${errEnv.error.class}: ${errEnv.error.message}`
          : 'Unknown error from platform trace endpoint'
        return {
          content: [{ type: 'text' as const, text: `Error: ${errorMsg}` }],
          isError: true,
        }
      }

      // MCPT v3.1.0-S4: Fetch audit findings for this trace and include in response.
      // Findings are populated by the nightly audit job (03:00 UTC); may be empty
      // for traces from the current day.
      let audit_findings: unknown[] = []
      try {
        const auditResponse = await fetch(
          `${process.env['PLATFORM_URL'] ?? 'http://localhost:3000'}/api/mcp/health/audit-findings?trace_id=${encodeURIComponent(trace_id)}`,
          {
            method: 'GET',
            headers: {
              'X-MCP-Internal-Token': process.env['MCP_INTERNAL_TOKEN'] ?? '',
              'X-MCP-User': principal.user_uid,
              // X-MCP-Audience-Tier removed (Stream A 3.tier_excision 2026-05-28).
              'X-MCP-Key-Id': principal.key_id,
            },
            signal: AbortSignal.timeout(3_000),
          }
        )
        if (auditResponse.ok) {
          const auditData = (await auditResponse.json()) as { findings?: unknown[] }
          audit_findings = auditData.findings ?? []
        }
      } catch {
        // Audit findings are optional; non-fatal if unavailable
        audit_findings = []
      }

      // Merge audit_findings into the envelope result
      const enrichedEnvelope = {
        ...result.envelope,
        audit_findings,
        audit_findings_note: audit_findings.length === 0
          ? 'No audit findings for this trace (nightly audit runs at 03:00 UTC; today\'s traces may not yet have findings).'
          : `${audit_findings.length} finding(s) attached by nightly audit.`,
      }

      return okResult(enrichedEnvelope)
    }
  )
}
