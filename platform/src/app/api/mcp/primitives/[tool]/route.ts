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
// Trigger capability registration for all layers (L0–L5) at module load.
// Without this import, only L0 capabilities (registered via a separate import chain)
// are in the registry — L1/L2/L3/L4/L5 getCapability() calls return undefined.
import '@/lib/retrieval/registry/catalog'
// D7 migration Step 4: all imports consolidated into tool_name_bridge (primitives_registry RETIRED)
// DO NOT restore lib/mcp/primitives_registry imports — see RETRIEVAL_D7_CALLER_MAP_v1_0.md §2.4
import {
  getToolByName,
  resolveToolUri,
  TOOL_NAME_TO_URI,
  isAllowedSurgicalTool,
  isPerChartPrimitive,
  MCP_TO_RETRIEVAL_TOOL,
} from '@/lib/retrieval/registry/tool_name_bridge'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import type { QueryPlan } from '@/lib/router/types'
import {
  buildEnvelope,
  buildErrorEnvelope,
  buildEpistemicsBlock,
  buildEntitlementDenialEnvelope,
} from '@/lib/mcp/epistemics'
import { checkRateLimit, buildRateLimitErrorEnvelope } from '@/lib/mcp/rate_limiter'
import { traceEmitter } from '@/lib/trace/emitter'
import { buildTraceSummary } from '@/lib/mcp/trace_summary'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

export const maxDuration = 60

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
  // NOTE: X-MCP-Audience-Tier is NOT a gate — entitlement is owned by the channel layer
  // (MCP fork's authorizeChartAccess). Header was excised from the MCP fork client on
  // 2026-05-28 (tier_excision). Read for informational/logging purposes only; default to
  // 'client' when absent. See R2.0 fix: removing 401 on missing audience-tier.
  const userUid = request.headers.get('x-mcp-user')
  const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as
    | 'client'
    | 'super_admin'
    | null
  const keyId = request.headers.get('x-mcp-key-id')

  if (!userUid || !keyId) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Missing principal headers (X-MCP-User, X-MCP-Key-Id)',
      }),
      { status: 401 }
    )
  }

  // Audience tier: informational only — channel layer owns entitlement.
  // Default to 'client' when header is absent (MCP fork no longer sends it).
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

  // Tool-registry check: operator may disable a tool at runtime via tool_registry table.
  // Returns 503 {tool_disabled: true} when tool_registry.tool_enabled = false.
  // Degrades gracefully: if the DB is unreachable or tool_registry row doesn't exist,
  // execution proceeds (fail-open to avoid total outage on registry table loss).
  try {
    const registryResult = await query<{ tool_enabled: boolean }>(
      `SELECT tool_enabled FROM tool_registry WHERE tool_name = $1 LIMIT 1`,
      [mcpToolName]
    )
    if (registryResult.rows.length > 0 && registryResult.rows[0].tool_enabled === false) {
      return NextResponse.json(
        {
          ok: false,
          tool_disabled: true,
          error: {
            class: 'tool_disabled',
            message: `Tool '${mcpToolName}' is currently disabled by the operator.`,
            remediation: 'Check /admin/mcp/health for status. Contact admin to re-enable.',
          },
        },
        { status: 503 }
      )
    }
  } catch (registryErr) {
    // Fail-open: log but don't block the tool call
    console.warn(`[mcp:primitives] tool_registry lookup failed for ${mcpToolName} — proceeding`, registryErr)
  }

  // Resolve the underlying retrieval tool name (from primitives_registry whitelist)
  const retrievalToolName = MCP_TO_RETRIEVAL_TOOL[mcpToolName]

  // D7: Get the retrieval tool via the registry bridge (no audience_tier forwarded — DG1 ruling)
  const tool = getToolByName(retrievalToolName)
  if (!tool) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'internal',
        message: `Retrieval tool not found in registry: ${retrievalToolName}`,
        remediation: 'Platform retrieval tool registry may be misconfigured (TOOL_NAME_TO_URI missing entry)',
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

  // M0 entitlement gate — enforce authorizeChartAccess for per_chart primitives.
  if (isPerChartPrimitive(mcpToolName)) {
    const chartId =
      (toolParams['chart_id'] as string | undefined) ??
      request.headers.get('x-mcp-chart-id') ??
      null
    if (!chartId) {
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'validation', message: 'CHART_REQUIRED', remediation: 'Supply chart_id in params or X-MCP-Chart-Id header for per-chart tools.' }),
        { status: 400 }
      )
    }
    const role = await resolveMcpPrincipalRole(userUid)
    const perm = await authorizeChartAccess({ principal: { uid: userUid, role }, chartId, db: { query } })
    if (perm === 'deny') {
      // R5.1 C2 item 3 (Denial ≠ empty): distinct entitlement_denied envelope, never the
      // bare 'auth' class — an MCP caller must be able to tell "you have no rights here"
      // apart from "this filter matched nothing" (Ring-3 red-team finding).
      return NextResponse.json(
        buildEntitlementDenialEnvelope({ chart_id: chartId, permission_required: 'view' }),
        { status: 401 }
      )
    }
  }

  // Generate a trace ID for this primitive call
  const queryId = crypto.randomUUID()

  // Build a minimal query plan for the tool (surgical: bypasses full pipeline)
  const queryPlan: QueryPlan = {
    query_plan_id: queryId,
    query_text: `surgical_primitive:${mcpToolName}`,
    query_class: 'holistic',
    domains: [],
    forward_looking: false,
    tools_authorized: [retrievalToolName],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'structured_data',
    manifest_fingerprint: '',
    schema_version: '1.0',
  }

  // Wire CGM graph traversal params from toolParams into queryPlan
  if (retrievalToolName === 'cgm_graph_walk') {
    if (typeof toolParams.node_id === 'string' && toolParams.node_id.trim().length > 0) {
      queryPlan.graph_seed_hints = [toolParams.node_id.trim()]
    }
    if (typeof toolParams.hops === 'number') {
      queryPlan.graph_traversal_depth = toolParams.hops
    }
  }

  // Execute the retrieval tool via registry bridge.
  // C-2 (tier_excision / DG1 ruling): audience_tier no longer exists on the
  // query plan — the registry is universal-access, so there is nothing to strip.
  let toolResult: unknown
  try {
    const rawResult = await tool.retrieve(queryPlan as unknown as Record<string, unknown>, toolParams)
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
        mcp_tool: mcpToolName,
        query_summary: buildTraceSummary(mcpToolName, toolParams),
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

  // F-033: strip audience_tier from served MCP envelope (no-audience-tier doctrine)
  const { audience_tier: _tier, ...envelope } = buildEnvelope({
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
  return NextResponse.json(envelope)
}
