/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - Three tools registered: ask_madhav, plan_query, execute_plan.
 *   (Tier 3 primitives, read_asset, get_trace, list_recent_queries land in MCP-3.)
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
  const principal: Principal | null = await validateMcpKeyFromHeader(
    req.headers['authorization']
  )

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
