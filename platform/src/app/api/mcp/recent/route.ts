/**
 * /api/mcp/recent — Recent MCP queries for the calling principal.
 *
 * GET — Returns recent MCP call history for the key_id resolved from
 * the X-MCP-Key-Id header. Used by the list_recent_queries MCP tool.
 *
 * Auth model (two-layer, same as /api/mcp/execute):
 *   Layer 1: X-MCP-Internal-Token — service-to-service secret.
 *   Layer 2: X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id — resolved principal.
 *
 * Query params:
 *   limit  — number of rows to return (default 20, max 100).
 *   since  — ISO date string (default: 7 days ago).
 *
 * Returns: {ok: true, result: { queries: RecentQueryRow[] }, epistemics: {surgical: true}}
 *
 * Used by:
 *   - list_recent_queries MCP tool (platform-mcp/src/tools/list_recent_queries.ts).
 *   - Native admin UI (future) for auditing MCP usage and cost.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { buildEnvelope, buildErrorEnvelope, buildEpistemicsBlock } from '@/lib/mcp/epistemics'
import { validateServiceToken } from '@/lib/mcp/service_token'

// ── Row shape for query results ──────────────────────────────────────────────

interface RecentQueryRow {
  trace_id: string
  created_at: string
  tool: string
  source: string
  query_summary: string
}

// ── Raw DB row ────────────────────────────────────────────────────────────────

interface DbTraceRow {
  query_id: string
  created_at: string
  step_name: string
  // mcp_tool column added by migration 116: stores the MCP-facing name
  // (e.g. query_chart_facts). NULL for rows written before migration 116.
  mcp_tool: string | null
  data_summary: Record<string, unknown> | null
  payload: { items?: Array<{ text?: string }> } | null
}

// ── GET handler ──────────────────────────────────────────────────────────────

export async function GET(request: Request) {
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

  // Parse query params
  const url = new URL(request.url)
  const rawLimit = parseInt(url.searchParams.get('limit') ?? '20', 10)
  const limit = Math.min(Math.max(1, isNaN(rawLimit) ? 20 : rawLimit), 100)

  const sinceParam = url.searchParams.get('since')
  let since: Date
  if (sinceParam) {
    since = new Date(sinceParam)
    if (isNaN(since.getTime())) {
      return NextResponse.json(
        buildErrorEnvelope({
          error_class: 'validation',
          message: `Invalid 'since' date: ${sinceParam}`,
          remediation: 'Provide an ISO 8601 date string, e.g. "2026-05-01"',
        }),
        { status: 400 }
      )
    }
  } else {
    // Default: 7 days ago
    since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
  }

  // Query query_trace_steps for MCP calls by this key_id.
  // MCP calls are tagged in payload items text as JSON containing "key_id":"<id>".
  // We look for entries where the source tag matches mcp or mcp_primitive.
  try {
    const { rows } = await query<DbTraceRow>(
      `SELECT DISTINCT ON (qts.query_id)
         qts.query_id,
         qts.created_at::text,
         qts.step_name,
         -- mcp_tool column added by migration 116; NULL for pre-migration rows.
         -- Prefer this over step_name so list_recent_queries returns MCP-facing
         -- names (query_chart_facts) instead of retrieval-side names (chart_facts_query).
         qts.mcp_tool,
         qts.data_summary,
         qts.payload
       FROM query_trace_steps qts
       WHERE qts.created_at >= $1
         AND qts.user_id = $2
         AND qts.payload IS NOT NULL
         AND EXISTS (
           SELECT 1
           FROM jsonb_array_elements(
             CASE WHEN qts.payload ? 'items' THEN qts.payload->'items' ELSE '[]'::jsonb END
           ) AS item
           WHERE item->>'text' LIKE $3
         )
       ORDER BY qts.query_id, qts.created_at DESC
       LIMIT $4`,
      [since.toISOString(), userUid, `%"key_id":"${keyId}"%`, limit]
    )

    const queries: RecentQueryRow[] = rows.map((row) => {
      // Determine tool name with three-tier fallback:
      //   1. mcp_tool column (migration 116, canonical MCP-facing name e.g. query_chart_facts)
      //   2. data_summary.mcp_tool (written by buildTraceSummary since MCPT v3.2)
      //   3. step_name (retrieval-side name e.g. chart_facts_query — pre-migration fallback)
      const dataSummary = row.data_summary as Record<string, unknown> | null
      const mcpTool =
        row.mcp_tool ??
        (dataSummary?.mcp_tool as string | undefined) ??
        row.step_name ??
        'unknown'
      const source = (dataSummary?.source as string | undefined) ?? 'mcp'

      // Extract query summary: prefer data_summary.query_summary (canonical param representation
      // populated by buildTraceSummary in the primitives and execute routes), then fall back
      // to a text scan of payload items, then to a generic step-name label.
      let querySummary = ''

      // 1. Canonical: data_summary.query_summary written by buildTraceSummary
      if (dataSummary && typeof dataSummary.query_summary === 'string' && dataSummary.query_summary) {
        querySummary = dataSummary.query_summary
      }

      // 2. Legacy: scan payload items for non-JSON text (pre-buildTraceSummary traces)
      if (!querySummary) {
        const items = (row.payload as { items?: Array<{ text?: string }> } | null)?.items ?? []
        for (const item of items) {
          if (item.text && item.text.includes('"key_id"')) {
            try {
              const parsed = JSON.parse(item.text)
              if (typeof parsed === 'object' && parsed !== null) {
                // Not a query text — skip
              }
            } catch {
              // text is not JSON — might be the query itself
              if (item.text.length > 0 && !item.text.startsWith('{')) {
                querySummary = item.text.slice(0, 80)
                break
              }
            }
          }
        }
      }

      // 3. Final fallback: step_name-based label
      if (!querySummary) {
        querySummary = `${mcpTool} call`
      }

      return {
        trace_id: row.query_id,
        created_at: row.created_at,
        tool: mcpTool,
        source,
        query_summary: querySummary,
      }
    })

    return NextResponse.json(
      buildEnvelope({
        trace_id: '',
        audience_tier: audienceTier,
        epistemics: buildEpistemicsBlock({ surgical: true, confidence_band: 'high' }),
        result: { queries },
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
    console.error('[mcp:recent] DB query failed', msg)
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'internal',
        message: `Failed to retrieve recent queries: ${msg}`,
      }),
      { status: 500 }
    )
  }
}
