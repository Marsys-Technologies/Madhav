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
import { registerMitigationMapTool } from './tools/phala_mitigation_map.js'
import { registerPhalaOutlookTool } from './tools/phala_outlook.js'
import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
import { registerMimamsaLelIntakeTool } from './tools/mimamsa_lel_intake.js'
import { registerMimamsaOutcomeTool } from './tools/mimamsa_outcome.js'
import { registerHolisticBundleTool } from './tools/bo_2-8.js'
import { registerPhalaEventAnchorsTool } from './tools/phala_event_anchors.js'
import { registerHolisticBundleRetrievalTool } from './tools/retrieval/holistic_bundle.js'
import { registerKalaTemporalRetrievalTool } from './tools/retrieval/kala_temporal.js'

const app = express()
app.use(express.json())

// ── MCP endpoint ──────────────────────────────────────────────────────────────

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

  const principal: Principal | null = await validateMcpKeyFromHeader(authHeader)

  if (!principal) {
    res.status(401).json({ error: 'Unauthorized', message: 'Invalid or missing Bearer API key' })
    return
  }

  void fromUrlParam

  const server = new McpServer({
    name: 'marsys-jis',
    version: '1.0.0',
  })

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
  res.json({ status: 'ok', service: 'marsys-mcp', version: '1.0.0', tools: 1 })
})

// ── Start server ──────────────────────────────────────────────────────────────

const port = parseInt(process.env['MCP_PORT'] ?? '8080', 10)
app.listen(port, () => {
  console.log(`[mcp:server] MARSYS-JIS MCP server listening on :${port} (1 tool: mitigation_map)`)
  console.log(`[mcp:server] Platform URL: ${process.env['PLATFORM_URL'] ?? 'http://localhost:3000'}`)
})
