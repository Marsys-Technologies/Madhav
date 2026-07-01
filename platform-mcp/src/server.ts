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
import cookieParser from 'cookie-parser'
import type { Request, Response } from 'express'
import { validateMcpKeyFromHeader } from './auth.js'
import type { Principal } from './types.js'
// M6: surface spec for per-model declared profile
import { callPlatformSurfaceSpec } from './client.js'
// M5: DB-backed OAuth 2.0 endpoints
import { handleAuthorize, handleCallback } from './oauth/authorize.js'
import { handleToken } from './oauth/token.js'
import { handleOAuthDiscovery, handleOpenIDConfiguration } from './oauth/discovery.js'
import { validateAccessToken } from './oauth/token_store.js'
import { registerOAuthClient, validateOAuthClient } from './oauth/oauth_platform_client.js'
import { registerMitigationMapTool } from './tools/phala_mitigation_map.js'
import { registerPhalaOutlookTool } from './tools/phala_outlook.js'
import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
// KEYSTONE (M6+M7): mimamsa_lel_intake migrated to callPlatformPrimitive('lel_query').
import { registerMimamsaLelIntakeTool } from './tools/mimamsa_lel_intake.js'
import { registerMimamsaOutcomeTool } from './tools/mimamsa_outcome.js'
// KEYSTONE REQUEST: mimamsa_outcome (record_outcome / mimamsa_calibration) has no registry primitive.
// REQUEST to retrieval fork: expose 'record_outcome' capability in tool_name_bridge.
// Still served via sidecar until the registry primitive lands.
//
// KEYSTONE (M6+M7): holistic_bundle sidecar path (bo_2-8) RETIRED — registry path
// (holistic_bundle_chart_facts via callPlatformPrimitive) is the canonical route.
// import { registerHolisticBundleTool } from './tools/bo_2-8.js'  // RETIRED
import { registerPhalaEventAnchorsTool } from './tools/phala_event_anchors.js'
// KEYSTONE REQUEST: phala_event_anchors (phala_anchors table) has no registry primitive.
// REQUEST to retrieval fork: expose 'phala_event_anchors' capability in tool_name_bridge.
// Still served via sidecar until the registry primitive lands.
import { registerHolisticBundleRetrievalTool } from './tools/retrieval/holistic_bundle.js'
import { registerKalaTemporalRetrievalTool } from './tools/retrieval/kala_temporal.js'
// KEYSTONE REQUEST: kala_temporal_bundle (KA-3-COMPOSITE: timeline/convergence/obstruction/snapshot)
// has no registry primitive. REQUEST to retrieval fork: expose 'kala_temporal_bundle' capability.
// Still served via sidecar until the registry primitive lands.
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
// L0FR Stream F: Remedy Corpus retrieval tools
import { registerRemedyTools } from './tools/retrieval/remedy_tools.js'
// D7 — Registry bridge: consolidated workflow tools from the retrieval registry
import { registerRegistryBridgeTools } from './tools/registry_bridge.js'
// M2 — Chart selection: list_my_charts + select_chart
import { registerChartSelectionTools } from './tools/chart_selection.js'
// M3+M4 — Session tools: recall_session + list_my_sessions
import { registerSessionTools } from './tools/session_tools.js'
// R5 — Richness Layer: MCP resources (9 registered) + guided-reading prompts
import { registerResources } from './resources/index.js'
import { registerPrompts } from './prompts/index.js'

const app = express()
app.use(express.json())
app.use(cookieParser())

// ── OAuth 2.0 endpoints (M5: DB-backed, real Firebase identity) ──────────────
// Per MCP authorization spec + ChatGPT connector requirements

app.post('/mcp/oauth/authorize', (req, res) => void handleAuthorize(req, res))
// GET /mcp/oauth/callback — Firebase auth callback (stamps uid onto auth code)
app.get('/mcp/oauth/callback', (req, res) => void handleCallback(req, res))
app.post('/mcp/oauth/token', (req, res) => void handleToken(req, res))
app.post('/mcp/oauth/refresh', async (req: Request, res: Response) => {
  // Redirect to token endpoint with grant_type=refresh_token
  req.body.grant_type = 'refresh_token'
  await handleToken(req, res)
})

// M5: Dynamic client registration (RFC 7591 / MCP OAuth spec)
// Writes to mcp_oauth_clients table via platform API.
app.post('/mcp/oauth/register', async (req: Request, res: Response) => {
  const authHeader = req.headers['authorization']
  // Registration requires a valid Bearer key to identify the registering user.
  const principal = await validateMcpKeyFromHeader(authHeader)
  if (!principal) {
    res.status(401).json({ error: 'Unauthorized', message: 'Bearer key required to register an OAuth client' })
    return
  }

  const body = req.body as { redirect_uris?: string[]; scope?: string }
  if (!Array.isArray(body.redirect_uris) || body.redirect_uris.length === 0) {
    res.status(400).json({ error: 'invalid_client_metadata', error_description: 'redirect_uris required' })
    return
  }

  // Validate any registered client_id/secret from body (for test use-case, skip — new registration).
  void validateOAuthClient  // imported for side-channel use; suppress lint

  const scopes = body.scope ? body.scope.split(' ') : undefined
  const result = await registerOAuthClient({
    ownerUid: principal.user_uid,
    redirectUris: body.redirect_uris,
    scopes,
  })

  if (!result) {
    res.status(500).json({ error: 'server_error', error_description: 'Client registration failed' })
    return
  }

  // RFC 7591 response
  res.status(201).json({
    client_id: result.client_id,
    client_secret: result.client_secret,
    redirect_uris: body.redirect_uris,
    grant_types: ['authorization_code', 'client_credentials'],
    response_types: ['code'],
    scope: (scopes ?? ['mcp:tools', 'mcp:resources', 'mcp:prompts']).join(' '),
  })
})

// OAuth discovery metadata (add registration_endpoint per M5)
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

  // M5: also accept OAuth access tokens (DB-backed; survives restart + multi-instance).
  if (!principal && authHeader?.startsWith('Bearer ')) {
    const token = authHeader.slice('Bearer '.length)
    // DB-backed validation via platform API (replaces in-memory validateAccessToken).
    const oauthRecord = await validateAccessToken(token)
    if (oauthRecord) {
      // Fail-closed: never allow 'anonymous' uid through the entitlement gate.
      if (!oauthRecord.uid || oauthRecord.uid === 'anonymous') {
        res.status(401).json({ error: 'Unauthorized', message: 'OAuth token carries no verified uid' })
        return
      }
      // One identity core (M5.1): OAuth maps to the same Principal shape as Bearer key.
      // Role defaults to 'guest'; super_admin role requires Bearer key with profile lookup.
      principal = {
        user_uid: oauthRecord.uid,
        key_id: 'oauth:' + token.slice(0, 8),
        role: 'guest',
      } satisfies Principal
    }
  }

  if (!principal) {
    res.status(401).json({ error: 'Unauthorized', message: 'Invalid or missing Bearer API key' })
    return
  }

  void fromUrlParam

  // M6: Resolve effective model family.
  // Precedence: x-mcp-model-family header override > per-key binding > 'universal' fallback.
  // The header lets a client override at runtime (e.g. testing a different profile).
  const ALLOWED_FAMILIES = ['anthropic', 'gemini', 'openai', 'deepseek'] as const
  type ModelFamily = typeof ALLOWED_FAMILIES[number]
  const headerFamily = typeof req.headers['x-mcp-model-family'] === 'string'
    ? req.headers['x-mcp-model-family']
    : undefined
  const effectiveFamily: string = (
    (headerFamily && (ALLOWED_FAMILIES as readonly string[]).includes(headerFamily)
      ? headerFamily
      : principal.model_family) ??
    'universal'
  )

  // M6.2: Fetch the surface spec for the effective family.
  // Non-blocking: surface spec is advisory for shaping; failure falls back to serving all tools.
  // Fire-and-forget; surfaceSpec.envelope holds the spec result.
  let responseFormat: 'minimal' | 'standard' | 'detailed' = 'standard'
  try {
    const surfaceResult = await callPlatformSurfaceSpec(effectiveFamily)
    if (surfaceResult.status === 200 && surfaceResult.envelope.ok) {
      const spec = surfaceResult.envelope.result as Record<string, unknown> | null
      if (spec && typeof spec['response_format'] === 'string') {
        const rf = spec['response_format']
        if (rf === 'minimal' || rf === 'standard' || rf === 'detailed') {
          responseFormat = rf
        }
      }
    }
  } catch {
    // Non-fatal: surface spec failure does not block tool serving.
  }

  // Pass effectiveFamily + responseFormat to tools that accept them.
  // Currently stored as request-scoped constants for tool callbacks.
  void effectiveFamily
  void responseFormat

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
  // KEYSTONE: holistic_bundle sidecar path (bo_2-8) RETIRED.
  // Registry path: holistic_bundle_chart_facts (retrieval/holistic_bundle.ts → callPlatformPrimitive).
  registerHolisticBundleRetrievalTool(server, () => principal)  // chart_facts via registry (L2 Bodha — chart-SCOPED; requires chart_id)
  registerKalaTemporalRetrievalTool(server)    // L3 Kāla composite bundle (chart-SCOPED; sidecar — REQUEST: registry primitive pending)
  // L0 Brahmagyan Remedy tools (Stream F — 7 capabilities)
  registerRemedyTools(server, () => principal)
  // L4 Phala tools
  registerPhalaEventAnchorsTool(server, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMitigationMapTool(server as any, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMuhurtaFinder(server as any, () => principal)
  registerPhalaOutlookTool(server, principal)
  // L5 Mīmāṃsā tools
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaLelIntakeTool(server as any, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaOutcomeTool(server as any, principal)

  // D7 — Registry-backed consolidated workflow tools (12 MCP tools → registry URIs)
  // These are chart-agnostic: chart_id required on per_chart tools, no default.
  registerRegistryBridgeTools(server)

  // M2 — Chart selection: list_my_charts + select_chart (2 tools)
  // list_my_charts: entitled chart list by display name; select_chart: validate + return chart_id.
  registerChartSelectionTools(server, principal)

  // M3+M4 — Session tools: recall_session + list_my_sessions (2 tools)
  // recall_session: resume session with entitlement re-check; list_my_sessions: session history.
  registerSessionTools(server, principal)

  // R5 — Richness Layer: 9 MCP resources + 3 guided-reading prompts
  // M0: principal passed for chart-snapshot gate
  registerResources(server, principal)
  registerPrompts(server)

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

// Tool count computed from registration calls (update when adding/removing tools):
// L0 Brahmagyan pattern-validation: 5
// L0 Ephemeris: 5
// L1 Stream G PyJHora: 3
// L2 Bodha — holistic_bundle_chart_facts (registry path; sidecar path RETIRED): 1
// L3 Kāla (kala_temporal_bundle — sidecar; REQUEST: registry primitive pending): 1
// L0FR Remedy: 7
// L4 Phala (event_anchors + mitigation_map + muhurta_finder + phala_outlook): 4
// L5 Mīmāṃsā (lel_query via registry + record_outcome via sidecar): 2
// D7 Registry bridge (registerRegistryBridgeTools — 14 MCP tools): 14
// M2 Chart selection (list_my_charts + select_chart): 2
// M3+M4 Session tools (recall_session + list_my_sessions): 2
// KEYSTONE: holistic_bundle sidecar retired (-1). Total: 46
const REGISTERED_TOOL_COUNT = 46

app.get('/health', (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'marsys-mcp',
    version: '1.0.0',
    tools: REGISTERED_TOOL_COUNT,
    stream_g_capabilities: ['compute_natal_positions', 'query_dasha_periods', 'query_special_lagnas'],
  })
})

// ── Start server ──────────────────────────────────────────────────────────────

const port = parseInt(process.env['MCP_PORT'] ?? '8080', 10)
app.listen(port, () => {
  console.log(`[mcp:server] MARSYS-JIS MCP server listening on :${port} (Stream G: +3 PyJHora tools)`)
  console.log(`[mcp:server] Platform URL: ${process.env['PLATFORM_URL'] ?? 'http://localhost:3000'}`)
})
