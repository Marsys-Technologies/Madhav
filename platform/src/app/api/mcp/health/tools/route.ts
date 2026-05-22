/**
 * /api/mcp/health/tools — Tool health metrics endpoint.
 *
 * Tier-gated: super_admin + acharya = 200 with full metrics.
 *             client = 403 with house-rules reference.
 *
 * Returns aggregate health metrics for all registered MCP tools:
 *   - call_count_24h, error_rate, avg_latency_ms, audit_finding_count
 *
 * MCPT v3.1.0-S4
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

function extractPrincipal(req: NextRequest): { audience_tier: string } | null {
  const audience_tier = req.headers.get('X-MCP-Audience-Tier')
  if (!audience_tier) return null
  return { audience_tier }
}

function validateToken(req: NextRequest): boolean {
  const token = req.headers.get('X-MCP-Internal-Token')
  return !!token && token === MCP_INTERNAL_TOKEN
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

  // Return tool health metrics
  // In production, these would be queried from tool_execution_log + mcp_audit_findings.
  // In this S4 implementation, we return the schema + live data where available.
  const now = new Date().toISOString()

  return NextResponse.json({
    ok: true,
    generated_at: now,
    lookback_hours: 24,
    tier: principal.audience_tier,
    tools: [
      'holistic_bundle', 'multi_school_bundle',
      'query_signals', 'query_chart_facts', 'query_dasha_periods',
      'query_panchanga', 'query_ephemeris', 'query_transit_event',
      'lel_query', 'vector_search', 'get_cgm_subgraph', 'cross_school_lookup',
      'read_asset', 'get_trace', 'list_recent_queries',
      'tool_health', 'data_coverage',
      'log_prediction', 'record_outcome', 'flag_disagreement',
    ].map(name => ({
      tool_name: name,
      call_count_24h: null,       // populated by nightly audit
      error_rate: null,           // populated by nightly audit
      avg_latency_ms: null,       // populated by nightly audit
      audit_finding_count: null,  // populated by nightly audit
      caveats: [],                // populated from tool_caveats table
      data_note: 'Live metrics pending. Apply migrations 073-076 and run nightly audit.',
    })),
  })
}

export async function POST(req: NextRequest): Promise<Response> {
  return GET(req)
}
