/**
 * /api/mcp/trace/[trace_id] — Full query trace step ledger for a prior MCP call.
 *
 * GET — Returns all query_trace_steps rows for a given trace_id (query_id).
 * Used by the get_trace MCP tool.
 *
 * Per D12 (full transparency): no tier-based redaction. All authenticated callers
 * receive full step payloads including prompts, retrieval results, and payloads.
 * Do not issue API keys to principals who should not have full trace visibility.
 *
 * Auth model (two-layer, same as /api/mcp/execute):
 *   Layer 1: X-MCP-Internal-Token — service-to-service secret.
 *   Layer 2: X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id — resolved principal.
 *
 * Returns: {ok: true, result: { trace_id, steps: TraceStep[], step_count, latency_ms_total }}
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { buildEnvelope, buildErrorEnvelope, buildEpistemicsBlock } from '@/lib/mcp/epistemics'
import { validateServiceToken } from '@/lib/mcp/service_token'
import { detectEvidenceState, surgicalConfidenceBand } from '@/lib/mcp/evidence_state'

// ── TraceStep shape (matches query_trace_steps schema) ───────────────────────

interface TraceStep {
  query_id: string
  step_seq: number
  step_name: string
  // mcp_tool column added by migration 116: MCP-facing name (e.g. query_chart_facts).
  // NULL for rows written before migration 116. Callers should prefer mcp_tool when
  // present; step_name holds the retrieval-side name (e.g. chart_facts_query).
  mcp_tool: string | null
  step_type: string
  status: string
  started_at: string | null
  completed_at: string | null
  latency_ms: number | null
  parallel_group: string | null
  data_summary: Record<string, unknown> | null
  payload: Record<string, unknown> | null
  user_id: string | null
}

// ── Route params ─────────────────────────────────────────────────────────────

interface RouteParams {
  params: Promise<{ trace_id: string }>
}

// ── GET handler ──────────────────────────────────────────────────────────────

export async function GET(request: Request, { params }: RouteParams) {
  // Layer 1: service-to-service auth
  if (!validateServiceToken(request)) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Invalid service token',
        remediation: 'MCP server must pass MCP_INTERNAL_TOKEN header',
      }),
      { status: 401 }
    )
  }

  // Layer 2: resolved principal headers
  const userUid = request.headers.get('x-mcp-user')
  const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as
    | 'client'
    | 'super_admin'
    | null
  const keyId = request.headers.get('x-mcp-key-id')

  if (!userUid || !audienceTierHeader || !keyId) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Missing principal headers (X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id)',
      }),
      { status: 401 }
    )
  }

  const audienceTier: 'client' | 'super_admin' =
    audienceTierHeader === 'super_admin' ? 'super_admin' : 'client'

  const { trace_id } = await params

  if (!trace_id || trace_id.length < 8) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'validation',
        message: 'trace_id is required and must be a valid UUID',
        remediation: 'Pass the trace_id from a prior ask_madhav or other MCP tool response',
      }),
      { status: 400 }
    )
  }

  try {
    const { rows } = await query<TraceStep>(
      `SELECT
         query_id, step_seq, step_name,
         -- mcp_tool column added by migration 116: MCP-facing name, e.g. query_chart_facts.
         -- NULL for rows written before migration 116 is applied.
         mcp_tool,
         step_type, status,
         started_at::text AS started_at, completed_at::text AS completed_at,
         latency_ms, parallel_group, data_summary, payload, user_id
       FROM query_trace_steps
       WHERE query_id = $1
       ORDER BY step_seq ASC`,
      [trace_id]
    )

    if (rows.length === 0) {
      return NextResponse.json(
        buildErrorEnvelope({
          error_class: 'validation',
          message: `No trace found for trace_id: ${trace_id}`,
          remediation: 'Verify the trace_id from a prior MCP response envelope',
        }),
        { status: 404 }
      )
    }

    // Compute total latency from step latencies
    const totalLatencyMs = rows.reduce((sum, step) => sum + (step.latency_ms ?? 0), 0)

    // F-161 hardening (not a live-reachable fix — see note below): `confidence_band`
    // was hardcoded 'high' here, the same §N.8 pattern F-126 fixed in the primitives
    // route. Unlike that route, `rows.length === 0` above already returns a 404 error
    // envelope before this code runs, so `steps` here can never be empty and
    // `detectEvidenceState` will always grade 'present' → 'high'. The detector is
    // wired up anyway for defense-in-depth and consistency with the sibling routes,
    // but there is no zero-row defect for it to catch at this call site today.
    const result = {
      trace_id,
      steps: rows,
      step_count: rows.length,
      latency_ms_total: totalLatencyMs,
    }
    const evidenceState = detectEvidenceState(result)

    return NextResponse.json(
      buildEnvelope({
        trace_id,
        audience_tier: audienceTier,
        epistemics: buildEpistemicsBlock({
          surgical: true,
          confidence_band: surgicalConfidenceBand(evidenceState),
          evidence_state: evidenceState,
          horizon_days: null,
          falsifier: null,
        }),
        result,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      })
    )
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[mcp:trace] DB query failed', msg)
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'internal',
        message: `Failed to retrieve trace: ${msg}`,
      }),
      { status: 500 }
    )
  }
}
