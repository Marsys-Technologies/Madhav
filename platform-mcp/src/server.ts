/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - 19 tools registered as of MCP-4-S1 (16 read + 3 write).
 *
 * Tool count (v1, all registered as of MCP-4-S1):
 *   Tier 1: ask_madhav
 *   Tier 2: plan_query, execute_plan
 *   Tier 3 (10): query_chart_facts, query_signals, query_dasha_periods,
 *                query_panchanga, query_ephemeris, query_transit_event,
 *                lel_query, vector_search, get_cgm_subgraph, cross_school_lookup
 *   Tier 4 (1): read_asset
 *   Tier 5 (2): get_trace, list_recent_queries
 *   Tier 6 — Write tools (3, MCP-4-S1): log_prediction, record_outcome, flag_disagreement
 *
 * Cloud Run configuration (amjis-mcp service):
 *   Memory: 512 MB, Min instances: 1, Concurrency: 80, Region: asia-south1.
 *   Health check: GET /health → 200 { status: "ok", service: "marsys-mcp" }
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js'
import express from 'express'
import type { Request, Response } from 'express'
import { validateMcpKeyFromHeader } from './auth.js'
import { registerResources } from './resources/index.js'
import { registerAskMadhav } from './tools/ask_madhav.js'
import { registerPlanQuery } from './tools/plan_query.js'
import { registerExecutePlan } from './tools/execute_plan.js'
// MCP-3-S1: Tier 3 surgical primitives
import { registerQueryChartFacts } from './tools/query_chart_facts.js'
import { registerQuerySignals } from './tools/query_signals.js'
import { registerQueryDashaPeriods } from './tools/query_dasha_periods.js'
import { registerQueryPanchanga } from './tools/query_panchanga.js'
import { registerQueryEphemeris } from './tools/query_ephemeris.js'
import { registerQueryTransitEvent } from './tools/query_transit_event.js'
import { registerLelQuery } from './tools/lel_query.js'
import { registerVectorSearch } from './tools/vector_search.js'
import { registerGetCgmSubgraph } from './tools/get_cgm_subgraph.js'
import { registerCrossSchoolLookup } from './tools/cross_school_lookup.js'
// MCP-3-S2: Tier 4 + Tier 5 tools
import { registerReadAsset } from './tools/read_asset.js'
import { registerGetTrace } from './tools/get_trace.js'
import { registerListRecentQueries } from './tools/list_recent_queries.js'
// MCP-4-S1: Tier 6 write tools (PPL + disagreement)
import { registerLogPrediction } from './tools/log_prediction.js'
import { registerRecordOutcome } from './tools/record_outcome.js'
import { registerFlagDisagreement } from './tools/flag_disagreement.js'
import type { Principal } from './types.js'

const app = express()
app.use(express.json())

// ── MCP endpoint ──────────────────────────────────────────────────────────────

/**
 * POST /mcp — main MCP protocol endpoint (Streamable HTTP transport).
 *
 * Per the MCP protocol specification, all JSON-RPC messages (initialize,
 * tools/list, tools/call, etc.) are POST'd to this single endpoint.
 * The StreamableHTTPServerTransport handles SSE streaming for long-running
 * calls and direct responses for quick ones.
 *
 * Each request gets its own McpServer + transport instance, enforcing
 * statelessness (D10: no conversation history; no shared session state).
 */
app.post('/mcp', async (req: Request, res: Response) => {
  // Validate the Bearer key before doing any work.
  //
  // Auth source priority:
  //   1. Authorization: Bearer <key> header (preferred — Claude Code via .mcp.json,
  //      direct API clients, anything that supports custom headers).
  //   2. ?api_key=<key> URL query parameter (fallback — Claude.ai's "Add custom
  //      connector" UI has no Bearer field as of 2026-05; this lets users embed
  //      the key in the connector URL itself).
  //
  // Trade-off: URL-embedded tokens leak into logs/referrers. Acceptable per
  // D12 (full-transparency tier) for personal/super_admin keys; do NOT use this
  // path for client-tier or shared keys.
  const headerAuth = req.headers['authorization']
  const queryKey = typeof req.query['api_key'] === 'string' ? req.query['api_key'] : undefined
  const authHeader = headerAuth ?? (queryKey ? `Bearer ${queryKey}` : undefined)

  const principal: Principal | null = await validateMcpKeyFromHeader(authHeader)

  if (!principal) {
    res.status(401).json({ error: 'Unauthorized', message: 'Invalid or missing Bearer API key' })
    return
  }

  // Each request is fully stateless: new server + transport per request.
  const server = new McpServer({
    name: 'marsys-jis',
    version: '1.0.0',
  })

  const getPrincipal = (): Principal => principal

  // Register MCP resources (marsys://chart-overview, marsys://house-rules).
  // Resources are read once at session attach — they orient Claude to the
  // singleton chart and operating discipline without burning per-turn tool calls.
  registerResources(server)

  // Register Tier 1 + Tier 2 tools.
  registerAskMadhav(server, getPrincipal)
  registerPlanQuery(server, getPrincipal)
  registerExecutePlan(server, getPrincipal)

  // Register Tier 3 surgical primitives (MCP-3-S1).
  registerQueryChartFacts(server, getPrincipal)
  registerQuerySignals(server, getPrincipal)
  registerQueryDashaPeriods(server, getPrincipal)
  registerQueryPanchanga(server, getPrincipal)
  registerQueryEphemeris(server, getPrincipal)
  registerQueryTransitEvent(server, getPrincipal)
  registerLelQuery(server, getPrincipal)
  registerVectorSearch(server, getPrincipal)
  registerGetCgmSubgraph(server, getPrincipal)
  registerCrossSchoolLookup(server, getPrincipal)

  // Register Tier 4 raw-asset tool (MCP-3-S2).
  registerReadAsset(server, getPrincipal)

  // Register Tier 5 observability tools (MCP-3-S2).
  registerGetTrace(server, getPrincipal)
  registerListRecentQueries(server, getPrincipal)

  // Register Tier 6 write tools (MCP-4-S1):
  //   log_prediction  — PPL interim substrate (mcp_predictions table, migration 071)
  //   record_outcome  — outcome recording against prior predictions
  //   flag_disagreement — governance disagreement register (mcp_disagreements table)
  registerLogPrediction(server, getPrincipal)
  registerRecordOutcome(server, getPrincipal)
  registerFlagDisagreement(server, getPrincipal)

  // Stateless mode: sessionIdGenerator: undefined (per MCP SDK docs).
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  })

  try {
    await server.connect(transport)
    await transport.handleRequest(req, res, req.body)
  } catch (err) {
    console.error('[mcp:server] Unhandled error in MCP request', err)
    if (!res.headersSent) {
      res.status(500).json({ error: 'Internal server error' })
    }
  }
})

// ── GET /mcp — SSE subscription endpoint ─────────────────────────────────────
// Some MCP clients use a separate GET for SSE event streams. Return 405 with
// a clear message — we use the stateless POST-only pattern.
app.get('/mcp', (_req: Request, res: Response) => {
  res.status(405).json({
    error: 'Method Not Allowed',
    message: 'Use POST /mcp for Streamable HTTP transport (stateless mode). SSE GET not supported.',
  })
})

// ── Health check ──────────────────────────────────────────────────────────────

app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', service: 'marsys-mcp', version: '1.0.0' })
})

// ── Start server ──────────────────────────────────────────────────────────────

const port = parseInt(process.env['MCP_PORT'] ?? '8080', 10)
app.listen(port, () => {
  console.log(`[mcp:server] MARSYS-JIS MCP server listening on :${port}`)
  console.log(`[mcp:server] Platform URL: ${process.env['PLATFORM_URL'] ?? 'http://localhost:3000'}`)
})
