/**
 * /api/mcp/health/tools — Tool health metrics endpoint.
 *
 * Tier-gated: super_admin + acharya = 200 with full metrics.
 *             client = 403 with house-rules reference.
 *
 * Returns aggregate health metrics for all registered MCP tools:
 *   - call_count_24h, error_rate, avg_latency_ms, audit_finding_count
 *
 * Reads from mv_tool_metrics_24h and mv_tool_grounding_24h (migration 082).
 * Graceful fallback when MVs don't exist or are empty (Phase 7b not yet applied).
 *
 * MCPT v3.2 Phase 7c
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { query } from '@/lib/db/client'

const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const ALL_TOOL_NAMES = [
  'holistic_bundle', 'multi_school_bundle',
  'query_signals', 'query_chart_facts', 'query_dasha_periods',
  'query_panchanga', 'query_ephemeris', 'query_transit_event',
  'lel_query', 'vector_search', 'get_cgm_subgraph', 'cross_school_lookup',
  'read_asset', 'get_trace', 'list_recent_queries',
  'tool_health', 'data_coverage',
  'log_prediction', 'record_outcome', 'flag_disagreement',
]

function extractPrincipal(req: NextRequest): { audience_tier: string } | null {
  const audience_tier = req.headers.get('X-MCP-Audience-Tier')
  if (!audience_tier) return null
  return { audience_tier }
}

function validateToken(req: NextRequest): boolean {
  const token = req.headers.get('X-MCP-Internal-Token')
  return !!token && token === MCP_INTERNAL_TOKEN
}

interface MetricsRow {
  mcp_tool_name: string
  calls_24h: number
  error_calls: number
  ok_rate: number | null
  p50_latency_ms: number | null
  last_call_at: string | null
}

interface GroundingRow {
  mcp_tool_name: string
  audit_findings_count: number
  violation_rate: number | null
}

export async function GET(req: NextRequest): Promise<Response> {
  if (!validateToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const principal = extractPrincipal(req)
  if (!principal) {
    return NextResponse.json({ error: 'Missing principal headers' }, { status: 401 })
  }

  // Tier gate: client tier is not allowed
  if (principal.audience_tier === 'client' || principal.audience_tier === 'public_redacted') {
    return NextResponse.json(
      {
        error: 'Forbidden',
        message: 'tool_health is available to super_admin and acharya tiers only. See house-rules for tier capabilities.',
        house_rules_uri: 'marsys://house-rules',
      },
      { status: 403 }
    )
  }

  const now = new Date().toISOString()

  // Build base tool map (all known tools, nulls until populated from MVs)
  const toolMap: Record<string, {
    tool_name: string
    call_count_24h: number | null
    error_rate: number | null
    avg_latency_ms: number | null
    audit_finding_count: number | null
    last_call_at: string | null
    caveats: string[]
  }> = {}

  for (const name of ALL_TOOL_NAMES) {
    toolMap[name] = {
      tool_name: name,
      call_count_24h: null,
      error_rate: null,
      avg_latency_ms: null,
      audit_finding_count: null,
      last_call_at: null,
      caveats: [],
    }
  }

  // Attempt to read from mv_tool_metrics_24h (migration 082)
  let mvAvailable = false
  try {
    const metricsResult = await query<MetricsRow>(
      `SELECT mcp_tool_name,
              calls_24h,
              error_calls,
              ok_rate,
              p50_latency_ms,
              last_call_at
       FROM mv_tool_metrics_24h`
    )

    for (const row of metricsResult.rows) {
      const tool = row.mcp_tool_name
      if (!toolMap[tool]) {
        toolMap[tool] = {
          tool_name: tool,
          call_count_24h: null,
          error_rate: null,
          avg_latency_ms: null,
          audit_finding_count: null,
          last_call_at: null,
          caveats: [],
        }
      }
      const totalCalls = Number(row.calls_24h)
      const errorCalls = Number(row.error_calls)
      toolMap[tool].call_count_24h = totalCalls
      toolMap[tool].error_rate = totalCalls > 0 ? errorCalls / totalCalls : 0
      toolMap[tool].avg_latency_ms = row.p50_latency_ms !== null ? Number(row.p50_latency_ms) : null
      toolMap[tool].last_call_at = row.last_call_at ?? null
    }
    mvAvailable = true
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    // MV doesn't exist yet (Phase 7b/migration 082 not applied) — graceful skip
    const isMvMissing = message.includes('does not exist') || message.includes('relation')
    if (!isMvMissing) {
      // Unexpected error — log but don't fail the whole request
      console.error('[tool_health] mv_tool_metrics_24h query failed:', message)
    }
  }

  // Attempt to read from mv_tool_grounding_24h (migration 082)
  if (mvAvailable) {
    try {
      const groundingResult = await query<GroundingRow>(
        `SELECT mcp_tool_name, audit_findings_count, violation_rate
         FROM mv_tool_grounding_24h`
      )
      for (const row of groundingResult.rows) {
        const tool = row.mcp_tool_name
        if (toolMap[tool]) {
          toolMap[tool].audit_finding_count = Number(row.audit_findings_count)
        }
      }
    } catch {
      // grounding MV failure is non-fatal
    }
  }

  const tools = Object.values(toolMap)

  return NextResponse.json({
    ok: true,
    generated_at: now,
    lookback_hours: 24,
    tier: principal.audience_tier,
    mv_available: mvAvailable,
    tools,
    ...(mvAvailable ? {} : {
      note: 'audit MVs not yet populated — apply migration 082 and Phase 7b nightly audit job',
    }),
  })
}

export async function POST(req: NextRequest): Promise<Response> {
  return GET(req)
}
