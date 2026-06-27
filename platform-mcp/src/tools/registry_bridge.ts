/**
 * D7 — Registry-backed MCP Tool Bridge
 * =====================================
 * Exposes the new registry capabilities as MCP tools on the server.
 * Called from server.ts during tool registration.
 *
 * This is the "by-construction-no-drift" connection:
 *   registry.getCapability(uri).handler === the function both channels call
 *
 * All new consolidated MCP tools delegate to the same CapabilityDescriptor.handler
 * that the chat channel calls via getCapability(uri). Same handler → drift impossible.
 *
 * D7 consolidated tool surface (§2.1 of brief) — ~12 workflow-shaped tools:
 *   get_chart_orientation  → marsys://tool/L2/query_ucd
 *   get_domain_reading     → marsys://tool/L2/query_domain_reading
 *   get_signals            → marsys://tool/L2/query_signals
 *   traverse_graph         → marsys://tool/L2/traverse_chart_graph
 *   get_positions          → marsys://tool/L1/get_positions
 *   get_dashas             → marsys://tool/L1/get_dashas
 *   get_temporal_windows   → marsys://tool/L3/query_temporal_activation
 *   get_projections        → marsys://tool/L3/query_projections
 *   get_classical_citation → marsys://tool/L0/query_classical_texts
 *   get_remedies           → marsys://tool/L2/query_remedies
 *   get_chart_quality      → marsys://tool/L2/query_quality_scorecard
 *   list_assets            → marsys://resource/asset-registry/all
 *
 * Provider-spec obligations (RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC §B.i):
 *   - outputSchema + structuredContent + text fallback (dual output)
 *   - cursor pagination on list/search tools
 *   - response_format / verbosity enum on umbrella tools
 *   - UUIDs resolved to names in output
 *   - tool names: snake_case, no hyphens, ≤64 chars
 *   - transport: Streamable HTTP only (matches server.ts)
 *
 * chart_agnostic_gate: all per_chart tools require chart_id; error if missing.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

// ── Platform URL (for proxy calls to the platform API) ───────────────────────

const PLATFORM_URL = (
  process.env['PLATFORM_URL'] ?? 'http://localhost:3000'
).replace(/\/$/, '')

// ── DB proxy helper ───────────────────────────────────────────────────────────

/**
 * Minimal DB proxy: calls platform API which holds the actual PG connection.
 * The MCP server does not hold a direct DB connection.
 */
async function platformQuery(
  sql: string,
  params: unknown[]
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    throw new Error(`[registry_bridge] platform DB query failed: ${res.status}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

/**
 * Build a SynergyContext for capability handlers.
 */
function buildCtx(chartId?: string) {
  return {
    db: { query: platformQuery },
    chart_id: chartId,
    lel_enabled: false,
  }
}

// ── Dual output helper ────────────────────────────────────────────────────────

/**
 * Build MCP tool response with both structuredContent and text fallback.
 * Provider-spec obligation: dual output per MCP spec.
 */
function dualOutput(data: unknown): {
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
} {
  return {
    structuredContent: { type: 'object' as const, object: data },
    content: [{
      type: 'text' as const,
      text: JSON.stringify(data, null, 2),
    }],
  }
}

// ── Error output ──────────────────────────────────────────────────────────────

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const data = { ok: false, error: message, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
}

// ── Registry capability caller ────────────────────────────────────────────────

/**
 * Call a registry capability via the platform's /api/retrieval/capability endpoint.
 *
 * The MCP server is a separate Node package (platform-mcp) and cannot import
 * the Next.js platform's TypeScript modules directly. Instead, it calls the
 * platform's HTTP API, which holds the live registry and DB connection.
 *
 * Endpoint: POST /api/retrieval/capability
 * Body: { uri, args }
 * Response: { ok: boolean, content: unknown, error?: string }
 */
async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  _chartId?: string   // chart_id is already in args; kept for call-site clarity
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[registry_bridge] capability call failed (${res.status}): ${text.slice(0, 200)}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) {
    throw new Error(`[registry_bridge] capability error: ${data.error ?? 'unknown'}`)
  }
  return data.content
}

// ── Tool registrations ────────────────────────────────────────────────────────

/**
 * Register all D7 consolidated MCP tools on the server.
 *
 * All per_chart tools: chart_id is REQUIRED — no default fallback.
 * chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
 */
export function registerRegistryBridgeTools(server: McpServer): void {

  // ── get_chart_orientation (L-ORIENT umbrella) ─────────────────────────────
  // marsys://tool/L2/query_ucd
  server.tool(
    'get_chart_orientation',
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart to read. Required — no default chart.'
      ),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha for signals (default: 'LAHIRI')"
      ),
      top_k_signals: z.number().int().min(1).max(100).optional().describe(
        'Number of top MSR signals to return (default: 20)'
      ),
      response_format: z.enum(['full', 'summary', 'digest']).optional().describe(
        'Output verbosity: full (all fields), summary (key fields), digest (counts only). Default: summary.'
      ),
    },
    async ({ chart_id, ayanamsha_id, top_k_signals, response_format }) => {
      if (!chart_id) return errorOutput('get_chart_orientation', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_ucd',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', top_k_signals: top_k_signals ?? 20, response_format: response_format ?? 'summary' },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_chart_orientation', String(err), { chart_id })
      }
    }
  )

  // ── get_domain_reading (L-DOMAIN drill) ──────────────────────────────────
  // marsys://tool/L2/query_domain_reading
  server.tool(
    'get_domain_reading',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().describe(
        'Life domain to drill: career, relationship, character, spirituality, wealth, health, or other domain name.'
      ),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      cursor: z.string().optional().describe('Pagination cursor (from previous response.next_cursor)'),
    },
    async ({ chart_id, domain, ayanamsha_id, cursor }) => {
      if (!chart_id) return errorOutput('get_domain_reading', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_domain_reading',
          { chart_id, domain, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', cursor },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_domain_reading', String(err), { chart_id, domain })
      }
    }
  )

  // ── get_signals (L-SIGNAL ranked signals) ────────────────────────────────
  // marsys://tool/L2/query_signals
  server.tool(
    'get_signals',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      domain: z.string().optional().describe('Filter by domain (e.g. career, health)'),
      min_salience: z.number().min(0).max(1).optional().describe(
        'Minimum computed_salience threshold (0–1). Ranked by computed_salience DESC — NOT signature_tier.'
      ),
      limit: z.number().int().min(1).max(200).optional().describe('Max signals (default: 50)'),
      cursor: z.string().optional().describe('Pagination cursor'),
      lel_enabled: z.boolean().optional().describe(
        'Include lel_origin=true signals (Life Event Log calibration). Default: false.'
      ),
    },
    async ({ chart_id, ayanamsha_id, domain, min_salience, limit, cursor, lel_enabled }) => {
      if (!chart_id) return errorOutput('get_signals', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_signals',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', domain, min_salience, limit: limit ?? 50, cursor, lel_enabled: lel_enabled ?? false },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_signals', String(err), { chart_id })
      }
    }
  )

  // ── traverse_graph (CGM graph traversal) ─────────────────────────────────
  // marsys://tool/L2/traverse_chart_graph
  server.tool(
    'traverse_graph',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      seed_signal_ids: z.array(z.string()).min(1).describe(
        'Seed signal UUIDs to start traversal from (use signal_id values from get_signals).'
      ),
      mode: z.enum(['neighbors', 'paths', 'cluster']).optional().describe(
        'Traversal mode: neighbors (adjacent nodes), paths (shortest paths between seeds), cluster (community). Default: neighbors.'
      ),
      depth: z.number().int().min(1).max(3).optional().describe('Traversal depth (default: 2, max: 3)'),
    },
    async ({ chart_id, seed_signal_ids, mode, depth }) => {
      if (!chart_id) return errorOutput('traverse_graph', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L2/traverse_chart_graph',
          { chart_id, seed_signal_ids, mode: mode ?? 'neighbors', depth: depth ?? 2 },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('traverse_graph', String(err), { chart_id })
      }
    }
  )

  // ── get_positions (L1 Gaṇita graha positions) ────────────────────────────
  // marsys://tool/L1/get_positions
  server.tool(
    'get_positions',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      planet: z.string().optional().describe('Optional: filter by planet name (e.g. Sun, Moon, Mars)'),
    },
    async ({ chart_id, ayanamsha_id, planet }) => {
      if (!chart_id) return errorOutput('get_positions', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_positions',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', planet },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_positions', String(err), { chart_id })
      }
    }
  )

  // ── get_dashas (L1 Vimshottari dasha chain) ──────────────────────────────
  // marsys://tool/L1/get_dashas
  server.tool(
    'get_dashas',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      limit: z.number().int().min(1).max(200).optional().describe('Max dasha rows (default: 50)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ chart_id, ayanamsha_id, limit, cursor }) => {
      if (!chart_id) return errorOutput('get_dashas', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_dashas',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', limit: limit ?? 50, cursor },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_dashas', String(err), { chart_id })
      }
    }
  )

  // ── get_temporal_windows (L3 temporal activation + convergence) ──────────
  // marsys://tool/L3/query_temporal_activation + query_convergence_windows
  server.tool(
    'get_temporal_windows',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('Start date YYYY-MM-DD'),
      date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('End date YYYY-MM-DD'),
      include_convergence: z.boolean().optional().describe('Include convergence windows (default: true)'),
    },
    async ({ chart_id, ayanamsha_id, date_from, date_to, include_convergence }) => {
      if (!chart_id) return errorOutput('get_temporal_windows', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L3/query_temporal_activation',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', date_from, date_to, include_convergence: include_convergence ?? true },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_temporal_windows', String(err), { chart_id })
      }
    }
  )

  // ── get_projections (L3 probabilistic projections) ───────────────────────
  // marsys://tool/L3/query_projections
  server.tool(
    'get_projections',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      domain: z.string().optional().describe('Domain to project (e.g. career, relationship)'),
      horizon_years: z.number().int().min(1).max(20).optional().describe('Projection horizon in years (default: 5)'),
    },
    async ({ chart_id, ayanamsha_id, domain, horizon_years }) => {
      if (!chart_id) return errorOutput('get_projections', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L3/query_projections',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', domain, horizon_years: horizon_years ?? 5 },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_projections', String(err), { chart_id })
      }
    }
  )

  // ── get_classical_citation (L0 classical text retrieval) ─────────────────
  // marsys://tool/L0/query_classical_texts
  // Global scope — no chart_id required
  server.tool(
    'get_classical_citation',
    {
      query: z.string().describe('Topic or verse to search for in classical Jyotish texts.'),
      text_ids: z.array(z.string()).optional().describe('Optional: limit to specific text IDs'),
      limit: z.number().int().min(1).max(20).optional().describe('Max results (default: 5)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ query, text_ids, limit, cursor }) => {
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L0/query_classical_texts',
          { query, text_ids, limit: limit ?? 5, cursor },
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_classical_citation', String(err))
      }
    }
  )

  // ── get_remedies (L2 remedy prescriptions) ───────────────────────────────
  // marsys://tool/L2/query_remedies
  server.tool(
    'get_remedies',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().optional().describe('Filter remedies by life domain'),
      remedy_type: z.string().optional().describe('Filter by type: mantra, gemstone, ritual, upaya'),
    },
    async ({ chart_id, domain, remedy_type }) => {
      if (!chart_id) return errorOutput('get_remedies', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_remedies',
          { chart_id, domain, remedy_type },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_remedies', String(err), { chart_id })
      }
    }
  )

  // ── get_chart_quality (calibration + trust) ───────────────────────────────
  // marsys://tool/L2/query_quality_scorecard
  server.tool(
    'get_chart_quality',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
    },
    async ({ chart_id }) => {
      if (!chart_id) return errorOutput('get_chart_quality', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_quality_scorecard',
          { chart_id },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_chart_quality', String(err), { chart_id })
      }
    }
  )

  // ── list_assets (asset catalog) ───────────────────────────────────────────
  // marsys://resource/asset-registry/all
  // Global scope — no chart_id required
  server.tool(
    'list_assets',
    {
      layer: z.string().optional().describe('Filter by layer: L0, L1, L2, L3, L4, L5'),
      limit: z.number().int().min(1).max(200).optional().describe('Max assets (default: 81)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ layer, limit, cursor }) => {
      try {
        // list_assets → platform cockpit registry (direct HTTP; no @/ import possible)
        const data = await callRegistryCapability(
          'marsys://resource/asset-registry/all',
          { layer, limit: limit ?? 81, cursor }
        )
        return dualOutput({ ...(data as Record<string, unknown>), pagination: { cursor, limit } })
      } catch (err) {
        return errorOutput('list_assets', String(err))
      }
    }
  )
}
