/**
 * /api/mcp/primitives/[tool] — MCP surgical primitive dispatcher.
 *
 * POST handler that exposes the 10 whitelisted retrieval tools as surgical
 * MCP primitives. Surgical calls bypass the planner and B.11 floor; they are
 * tagged surgical: true in the epistemics block (MCP_BRIEF §5.3, §6 G1).
 *
 * Auth model (two-layer, same as /api/mcp/execute):
 *   Layer 1: X-MCP-Internal-Token — service-to-service secret (proves caller
 *     is the trusted amjis-mcp Cloud Run sidecar).
 *   Layer 2: X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id — resolved principal
 *     (set by the MCP server after its own Bearer key validation).
 *
 * Whitelist enforcement: only tool names in MCP_TO_RETRIEVAL_TOOL are allowed.
 * Any other tool name returns {ok: false, error: {class: "validation"}} 400.
 *
 * Trace logging: every call writes a query_trace_steps entry with
 *   source: "mcp_primitive" and surgical: true.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { getTool } from '@/lib/retrieve/index'
import {
  buildEnvelope,
  buildErrorEnvelope,
  buildEpistemicsBlock,
} from '@/lib/mcp/epistemics'
import {
  isAllowedSurgicalTool,
  MCP_TO_RETRIEVAL_TOOL,
} from '@/lib/mcp/primitives_registry'
import { checkRateLimit, buildRateLimitErrorEnvelope } from '@/lib/mcp/rate_limiter'
import { traceEmitter } from '@/lib/trace/emitter'

export const maxDuration = 60

// ── Service-to-service token validation ─────────────────────────────────────

function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    if (process.env.NODE_ENV === 'development') return true
    console.error('[mcp:primitives] MCP_INTERNAL_TOKEN not set in production')
    return false
  }
  return token === expected
}

// ── Route params ─────────────────────────────────────────────────────────────

interface RouteParams {
  params: Promise<{ tool: string }>
}

// ── POST handler ─────────────────────────────────────────────────────────────

export async function POST(request: Request, { params }: RouteParams) {
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

  // Rate limiting: primitives are lightweight (no LLM calls) — skip token pre-check.
  const rateLimitResult = await checkRateLimit(keyId)
  if (!rateLimitResult.allowed) {
    return NextResponse.json(
      buildRateLimitErrorEnvelope(rateLimitResult.reason ?? 'rate_limit'),
      { status: 429, headers: { 'Retry-After': String(rateLimitResult.retry_after_seconds ?? 60) } }
    )
  }

  // Resolve dynamic route segment: the MCP-facing tool name
  const { tool: mcpToolName } = await params

  // Whitelist check
  if (!isAllowedSurgicalTool(mcpToolName)) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'validation',
        message: `Tool not in surgical whitelist: ${mcpToolName}`,
        remediation: 'Use ask_madhav for full-pipeline queries. Surgical primitives are: ' +
          Object.keys(MCP_TO_RETRIEVAL_TOOL).join(', '),
      }),
      { status: 400 }
    )
  }

  // Resolve the underlying retrieval tool name
  const retrievalToolName = MCP_TO_RETRIEVAL_TOOL[mcpToolName]

  // Get the retrieval tool instance
  const tool = getTool(retrievalToolName)
  if (!tool) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'internal',
        message: `Retrieval tool not found in registry: ${retrievalToolName}`,
        remediation: 'Platform retrieval tool registry may be misconfigured',
      }),
      { status: 500 }
    )
  }

  // Parse the request body for tool params
  let body: { params?: Record<string, unknown> }
  try {
    body = await request.json()
  } catch {
    body = { params: {} }
  }

  const toolParams = body.params ?? {}

  // Generate a trace ID for this primitive call
  const queryId = crypto.randomUUID()

  // Build a minimal query plan for the tool (surgical: bypasses full pipeline)
  const queryPlan = {
    query_plan_id: queryId,
    query_text: `surgical_primitive:${mcpToolName}`,
    query_class: 'holistic' as const,
    domains: [],
    forward_looking: false,
    audience_tier: audienceTier,
    tools_authorized: [retrievalToolName],
    history_mode: 'synthesized' as const,
    panel_mode: false,
    expected_output_shape: 'structured_data' as const,
    manifest_fingerprint: '',
    schema_version: '1.0' as const,
  }

  // Execute the retrieval tool
  let toolResult: unknown
  try {
    const rawResult = await tool.retrieve(queryPlan, toolParams)
    toolResult = rawResult
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error(`[mcp:primitives] tool.execute failed for ${retrievalToolName}`, msg)
    return NextResponse.json(
      buildErrorEnvelope({
        trace_id: queryId,
        error_class: 'orchestrator_error',
        message: `Tool execution failed: ${msg}`,
      }),
      { status: 500 }
    )
  }

  // Log the trace step tagged as surgical primitive (fire-and-forget)
  traceEmitter.emitStep({
    event: 'step_done',
    query_id: queryId,
    step: {
      query_id: queryId,
      step_name: retrievalToolName,
      step_seq: 1,
      user_id: userUid,
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      status: 'done',
      step_type: 'sql',   // surgical primitives are DB/retrieval calls; sql covers sql+vector
      data_summary: {
        tool_name: retrievalToolName,
        result: `mcp_primitive:${mcpToolName}`,
      },
      payload: {
        // Store MCP source tag and surgical flag in the payload for audit trail
        items: [
          {
            id: queryId,
            source: 'mcp_primitive',
            layer: 'system' as const,
            token_estimate: 0,
            text: JSON.stringify({ surgical: true, mcp_tool: mcpToolName, key_id: keyId }),
            score: 1,
          },
        ],
      },
    },
  })

  // Build surgical epistemics block
  const epistemics = buildEpistemicsBlock({
    surgical: true,
    confidence_band: 'high',
    horizon_days: null,
    falsifier: null,
  })

  return NextResponse.json(
    buildEnvelope({
      trace_id: queryId,
      audience_tier: audienceTier,
      epistemics,
      result: toolResult,
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    })
  )
}
