/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * CLEAN SLATE — legacy-teardown (feature/legacy-teardown).
 * All tool registrations stripped. 0 tools registered.
 * Serves: auth + transport + health only.
 * Rebuild tools per layer during the Layer-0 → Layer-3 arc.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - Cloud Run configuration (amjis-mcp service):
 *   Memory: 512 MB, Min instances: 1, Concurrency: 80, Region: asia-south1.
 *   Health check: GET /health → 200 { status: "ok", service: "marsys-mcp" }
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js'
import express from 'express'
import type { Request, Response } from 'express'
import { validateMcpKeyFromHeader } from './auth.js'
import type { Principal } from './types.js'
// L0FR Stream A: OAuth 2.0 endpoints for ChatGPT MCP
import { handleAuthorize } from './oauth/authorize.js'
import { handleToken } from './oauth/token.js'
import { handleOAuthDiscovery, handleOpenIDConfiguration } from './oauth/discovery.js'
import { validateAccessToken } from './oauth/token_store.js'
import { registerMitigationMapTool } from './tools/phala_mitigation_map.js'
import { registerPhalaOutlookTool } from './tools/phala_outlook.js'
import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
import { registerMimamsaLelIntakeTool } from './tools/mimamsa_lel_intake.js'
import { registerMimamsaOutcomeTool } from './tools/mimamsa_outcome.js'
import { registerHolisticBundleTool } from './tools/bo_2-8.js'
import { registerPhalaEventAnchorsTool } from './tools/phala_event_anchors.js'
import { registerHolisticBundleRetrievalTool } from './tools/retrieval/holistic_bundle.js'
import { registerKalaTemporalRetrievalTool } from './tools/retrieval/kala_temporal.js'
// Stream G — L1 Gaṇita PyJHora capabilities (BRAHMA-G-1)
import {
  registerComputeNatalPositionsTool,
  registerQueryDashaPeriodsTool,
  registerQuerySpecialLagnasTool,
} from './tools/retrieval/pyhora_natal.js'
// L0FR Stream A: L0 Brahmagyan pattern-validation capabilities
import { registerL0BrahmagyanTools } from './tools/l0_brahmagyan.js'
// L0FR Stream B: L0 Ephemeris capabilities (ephemeris_daily 1900-2150)
import { registerEphemerisTools } from './tools/l0_ephemeris.js'

const app = express()
app.use(express.json())

// ── OAuth 2.0 endpoints (L0FR Stream A) ──────────────────────────────────────
// Per MCP authorization spec + ChatGPT connector requirements

app.post('/mcp/oauth/authorize', (req, res) => void handleAuthorize(req, res))
app.post('/mcp/oauth/token', (req, res) => void handleToken(req, res))
app.post('/mcp/oauth/refresh', async (req: Request, res: Response) => {
  // Redirect to token endpoint with grant_type=refresh_token
  req.body.grant_type = 'refresh_token'
  await handleToken(req, res)
})

// OAuth discovery metadata
app.get('/mcp/.well-known/oauth-authorization-server', handleOAuthDiscovery)
app.get('/mcp/.well-known/openid-configuration', handleOpenIDConfiguration)

// ── MCP endpoint (with OAuth token support) ───────────────────────────────────

/**
 * POST /mcp — main MCP protocol endpoint (Streamable HTTP transport).
 *
 * Each request gets its own McpServer + transport instance, enforcing
 * statelessness (D10: no conversation history; no shared session state).
 */
app.post('/mcp', async (req: Request, res: Response) => {
  const headerAuth = req.headers['authorization']
  const queryKey = typeof req.query['api_key'] === 'string' ? req.query['api_key'] : undefined
  const fromUrlParam = !headerAuth && !!queryKey
  const authHeader = headerAuth ?? (queryKey ? `Bearer ${queryKey}` : undefined)

  let principal: Principal | null = await validateMcpKeyFromHeader(authHeader)

  // L0FR: also accept OAuth access tokens (for ChatGPT integration)
  if (!principal && authHeader?.startsWith('Bearer ')) {
    const token = authHeader.slice('Bearer '.length)
    const oauthRecord = validateAccessToken(token)
    if (oauthRecord) {
      // Map OAuth principal to MCP Principal shape
      principal = {
        user_uid: oauthRecord.uid,
        key_id: 'oauth:' + token.slice(0, 8),
      } as Principal
    }
  }

  if (!principal) {
    res.status(401).json({ error: 'Unauthorized', message: 'Invalid or missing Bearer API key' })
    return
  }

  void fromUrlParam

  const server = new McpServer({
    name: 'marsys-jis',
    version: '1.0.0',
  })

  // L0 Brahmagyan tools (L0FR Stream A pattern-validation capabilities)
  registerL0BrahmagyanTools(server)
  // L0 Ephemeris tools (L0FR Stream B — ephemeris_daily 1900-2150)
  registerEphemerisTools(server)

  // L1 Gaṇita — PyJHora natal computation tools (Stream G / BRAHMA-G-1)
  registerComputeNatalPositionsTool(server)    // graha_sthana: 9 planets + Lagna
  registerQueryDashaPeriodsTool(server)        // Vimshottari mahadasha chain
  registerQuerySpecialLagnasTool(server)       // Lagna + upagrahas (Gulika, Maandi, etc.)

  // L2 Bodha tools
  registerHolisticBundleTool(server, principal)
  registerHolisticBundleRetrievalTool(server)  // chart_facts direct read (l2-bodha-scaffold)
  registerKalaTemporalRetrievalTool(server)    // L3 Kāla composite bundle (l3-kala)
  // L4 Phala tools
  registerPhalaEventAnchorsTool(server)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMitigationMapTool(server as any, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMuhurtaFinder(server as any, () => principal)
  registerPhalaOutlookTool(server)
  // L5 Mīmāṃsā tools
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaLelIntakeTool(server as any)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaOutcomeTool(server as any)

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
app.get('/mcp', (_req: Request, res: Response) => {
  res.status(405).json({
    error: 'Method Not Allowed',
    message: 'Use POST /mcp for Streamable HTTP transport (stateless mode). SSE GET not supported.',
  })
})

// ── Health check ──────────────────────────────────────────────────────────────

app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', service: 'marsys-mcp', version: '1.0.0', tools: 13,
    stream_g_capabilities: ['compute_natal_positions', 'query_dasha_periods', 'query_special_lagnas'] })
})

// ── Start server ──────────────────────────────────────────────────────────────

const port = parseInt(process.env['MCP_PORT'] ?? '8080', 10)
app.listen(port, () => {
  console.log(`[mcp:server] MARSYS-JIS MCP server listening on :${port} (Stream G: +3 PyJHora tools)`)
  console.log(`[mcp:server] Platform URL: ${process.env['PLATFORM_URL'] ?? 'http://localhost:3000'}`)
})
