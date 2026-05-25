/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - 34 tools registered (v4.2, per arch §3.7 + MCPT v3.2 Phase 4c + TR Wave PR #159 + UDA-2-S1 + UDA-2-S2 + UDA-2-S3 + UDA-2-S4 + UDA-2-S5).
 *
 * Tool count (v4.2, 34 tools):
 *   Tier 1 super-endpoint (1): chart_summary
 *   Tier 2 bundles (2): holistic_bundle, multi_school_bundle
 *   Tier 3 surgical primitives (22): query_chart_facts, query_signals, query_dasha_periods,
 *                query_panchanga, query_ephemeris, query_transit_event,
 *                lel_query, vector_search, get_cgm_subgraph, cross_school_lookup,
 *                query_varshphal, query_divisional_chart, query_remedial_mantras, muhurta_finder,
 *                msr_sql, temporal, kp_query, query_kp_ruling_planets,
 *                pattern_register, resonance_register,
 *                cluster_atlas, contradiction_register
 *                (last 4 added TR Wave PR #159 — Class A: engine existed;
 *                temporal added UDA-2-S2 — portal-only → MCP parity;
 *                kp_query + query_kp_ruling_planets added UDA-2-S3 — KP system parity;
 *                pattern_register + resonance_register added UDA-2-S4 — Discovery Layer parity;
 *                cluster_atlas + contradiction_register added UDA-2-S5 — Discovery Layer cluster/contradiction parity)
 *   Tier 4 raw-asset reads (2): read_asset, read_classical_text
 *   Tier 5 observability (2): get_trace, list_recent_queries
 *   Tier 5 perf (2): tool_health, data_coverage
 *   Tier 6 writes (3): log_prediction, record_outcome, flag_disagreement
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
// Tier 3: surgical primitives (original 10)
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
// Tier 3: TR Wave additions (PR #159 — Class A: engine existed)
import { registerQueryVarshphal } from './tools/query_varshphal.js'
import { registerQueryDivisionalChart } from './tools/query_divisional_chart.js'
import { registerQueryRemedialMantras } from './tools/query_remedial_mantras.js'
import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
// Tier 3: UDA-2-S1 — msr_sql portal-only → MCP parity
import { registerMsrSql } from './tools/msr_sql.js'
// Tier 3: UDA-2-S2 — temporal portal-only → MCP parity
import { registerTemporal } from './tools/temporal.js'
// Tier 3: UDA-2-S3 — kp_query + query_kp_ruling_planets portal-only → MCP parity
import { registerKpQuery } from './tools/kp_query.js'
import { registerQueryKpRulingPlanets } from './tools/query_kp_ruling_planets.js'
// Tier 3: UDA-2-S4 — pattern_register + resonance_register Discovery Layer parity
import { registerPatternRegister } from './tools/pattern_register.js'
import { registerResonanceRegister } from './tools/resonance_register.js'
// Tier 3: UDA-2-S5 — cluster_atlas + contradiction_register Discovery Layer cluster/contradiction parity
import { registerClusterAtlas } from './tools/cluster_atlas.js'
import { registerContradictionRegister } from './tools/contradiction_register.js'
// Tier 4: raw-asset reads
import { registerReadAsset } from './tools/read_asset.js'
import { registerReadClassicalText } from './tools/read_classical_text.js'
// Tier 5: observability + perf
import { registerGetTrace } from './tools/get_trace.js'
import { registerListRecentQueries } from './tools/list_recent_queries.js'
// Tier 6: write tools
import { registerLogPrediction } from './tools/log_prediction.js'
import { registerRecordOutcome } from './tools/record_outcome.js'
import { registerFlagDisagreement } from './tools/flag_disagreement.js'
// Tier 1: super-endpoint (MCPT v3.2 Phase 4c)
import { registerChartSummaryTool } from './tools/chart_summary.js'
// Tier 2: composite bundles (MCPT v3.1.0-S2)
import { registerHolisticBundle } from './tools/holistic_bundle_tool.js'
import { registerMultiSchoolBundle } from './tools/multi_school_bundle_tool.js'
// Perf system (MCPT v3.1.0-S4)
import { registerToolHealth } from './tools/tool_health.js'
import { registerDataCoverage } from './tools/data_coverage.js'
import type { Principal } from './types.js'
// Tier-aware catalog (MCPT v3.2 Phase 6b)
import { CATALOG } from './tools/catalog.js'
import { getCatalogForTier } from './tools/tier_catalog.js'

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
  // T.3 (red-team class-2): URL-key form restricted to super_admin tier only.
  // URL-embedded tokens leak into logs and referrers; acceptable only for the
  // fully-trusted super_admin audience. Client/acharya callers must use the
  // Authorization header.
  const headerAuth = req.headers['authorization']
  const queryKey = typeof req.query['api_key'] === 'string' ? req.query['api_key'] : undefined
  const fromUrlParam = !headerAuth && !!queryKey
  const authHeader = headerAuth ?? (queryKey ? `Bearer ${queryKey}` : undefined)

  const principal: Principal | null = await validateMcpKeyFromHeader(authHeader)

  if (!principal) {
    res.status(401).json({ error: 'Unauthorized', message: 'Invalid or missing Bearer API key' })
    return
  }

  // T.3: URL-key auth is restricted to super_admin tier.
  if (fromUrlParam && principal.audience_tier !== 'super_admin') {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'URL-key auth (?api_key=) restricted to super_admin tier; use Authorization header',
    })
    return
  }

  // Each request is fully stateless: new server + transport per request.
  const server = new McpServer({
    name: 'marsys-jis',
    version: '1.0.0',
  })

  const getPrincipal = (): Principal => principal

  // Build tier-aware catalog slice for this request (MCPT v3.2 Phase 6b).
  // getCatalogForTier returns the filtered + annotated set of ToolCatalogEntry
  // objects for the resolved audience_tier. Only descriptions vary — handlers
  // are identical across tiers (holistic_bundle output byte-equal for same call).
  const tier = principal.audience_tier
  const tierCatalog = getCatalogForTier(tier, CATALOG)
  const tierDescByName = new Map(tierCatalog.map(e => [e.name, e.description]))

  // Helper: returns the tier-adjusted description for a tool, or undefined if
  // the tool is not in the tier catalog (caller skips registration).
  const tierDesc = (name: string): string | undefined => tierDescByName.get(name)

  // Register MCP resources (marsys://chart-overview, marsys://house-rules, etc.).
  // Resources are read once at session attach — they orient Claude to the
  // singleton chart and operating discipline without burning per-turn tool calls.
  registerResources(server)

  // Register Tier 1 super-endpoint.
  registerChartSummaryTool(server, getPrincipal)

  // Register Tier 2 bundles (description varies by tier; handler unchanged).
  registerHolisticBundle(server, getPrincipal, tierDesc('holistic_bundle'))
  registerMultiSchoolBundle(server, getPrincipal, tierDesc('multi_school_bundle'))

  // Register Tier 3 surgical primitives (original 10).
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
  // TR Wave additions (PR #159 — Class A: existing retrieval engines).
  registerQueryVarshphal(server, getPrincipal)
  registerQueryDivisionalChart(server, getPrincipal)
  registerQueryRemedialMantras(server, getPrincipal)
  registerMuhurtaFinder(server, getPrincipal)
  registerMsrSql(server, getPrincipal)
  registerTemporal(server, getPrincipal)
  registerKpQuery(server, getPrincipal)
  registerQueryKpRulingPlanets(server, getPrincipal)
  registerPatternRegister(server, getPrincipal)
  registerResonanceRegister(server, getPrincipal)
  registerClusterAtlas(server, getPrincipal)
  registerContradictionRegister(server, getPrincipal)

  // Register Tier 4 raw-asset reads.
  registerReadAsset(server, getPrincipal)
  registerReadClassicalText(server, getPrincipal)

  // Register Tier 5 observability + perf tools.
  registerGetTrace(server, getPrincipal)
  registerListRecentQueries(server, getPrincipal)

  // Ops tools: hidden from client tier per OPS_TOOLS set in tier_catalog.ts.
  // OPS_TOOLS is the single source of truth — server.ts gates registration here
  // to match getCatalogForTier's filtering behavior.
  if (tier !== 'client') {
    registerToolHealth(server, getPrincipal)
    registerDataCoverage(server, getPrincipal)
    registerLogPrediction(server, getPrincipal)
    registerRecordOutcome(server, getPrincipal)
    registerFlagDisagreement(server, getPrincipal)
  }

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
