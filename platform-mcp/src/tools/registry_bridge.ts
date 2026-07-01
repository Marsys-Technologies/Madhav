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

// Service-to-service token — must match MCP_INTERNAL_TOKEN on amjis-web.
// Required by /api/retrieval/capability (F1 gate, M0.5).
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

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
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
    },
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

// ── B.11 orient-before-domain enforcement ─────────────────────────────────────

/**
 * B.11 Whole-Chart-Read Protocol (PROJECT_ARCHITECTURE §H.4):
 * Every domain-specific query must be preceded by an orientation digest
 * from the L2 UCD (query_ucd / get_chart_orientation). In the MCP channel,
 * which is stateless per-request and has no shared session state, we enforce
 * this STRUCTURALLY: each non-floor domain tool handler fetches the UCD
 * before doing its domain work and includes the result as `orientation_context`
 * in the output. This means orient-before-domain is guaranteed by construction —
 * the tool itself ensures orientation has happened, not a soft prompt convention.
 *
 * Floor tools (get_chart_orientation itself, get_classical_citation, list_assets)
 * are exempt — they ARE the floor or are chart-agnostic.
 *
 * If the UCD call fails (e.g. no bodha data yet), we return a graceful-empty
 * stub so the domain tool can still serve — a failed orientation is non-blocking
 * but annotated in the response.
 */
async function fetchOrientationContext(
  chart_id: string,
  ayanamsha_id: string = 'LAHIRI',
): Promise<{ orientation_context: unknown; orientation_ok: boolean }> {
  try {
    const ucdData = await callRegistryCapability(
      'marsys://tool/L2/query_ucd',
      { chart_id, ayanamsha_id, top_k_signals: 10, response_format: 'digest' },
      chart_id,
    )
    return { orientation_context: ucdData, orientation_ok: true }
  } catch (err) {
    // Non-blocking: domain tool still runs; orientation failure is annotated
    return {
      orientation_context: {
        b11_note: 'UCD orientation pre-fetch failed (graceful-empty). Domain tool executed without holistic context.',
        error: String(err),
      },
      orientation_ok: false,
    }
  }
}

// ── Tool registrations ────────────────────────────────────────────────────────

/**
 * Register all D7 consolidated MCP tools on the server.
 *
 * All per_chart tools: chart_id is REQUIRED — no default fallback.
 * chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
 *
 * B.11 enforcement: all per_chart domain tools call fetchOrientationContext()
 * before executing their domain query. The UCD result is included in the
 * response as `orientation_context` so the LLM always has holistic context.
 */
export function registerRegistryBridgeTools(server: McpServer): void {

  // ── get_chart_orientation (L-ORIENT umbrella) ─────────────────────────────
  // marsys://tool/L2/query_ucd
  server.tool(
    'get_chart_orientation',
    'Mandatory first call for any chart reading. Retrieves the L2 Bodha synthesis layer\'s Unified Chart Digest (UCD) — the holistic portrait of the chart distilled from 573 MSR signals, the CDLM domain activation grid, the CGM causal graph, and the Life Event Log. In classical Jyotish, an acharya reads the whole chart before any domain. This tool enforces that discipline: it surfaces the Lagna lord condition, Moon nakshatra character, dominant cross-domain themes, and active contradictions. Call this before get_domain_reading, get_signals, or any other per-chart tool — the B.11 Whole-Chart-Read Protocol requires it.',
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
        const fmt = response_format ?? 'summary'
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_ucd',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', top_k_signals: top_k_signals ?? 20, response_format: fmt },
          chart_id
        )
        // F-026: Apply response_format bounding at MCP layer
        const responseData = data as Record<string, unknown>
        if (fmt === 'digest') {
          // Counts only — strip signal arrays
          return dualOutput({
            chart_id: responseData['chart_id'],
            ayanamsha_id: responseData['ayanamsha_id'],
            msr_signal_count: responseData['msr_signal_count'],
            convergence_domains: responseData['convergence_domains'],
            provenance: responseData['provenance'],
            response_format: 'digest',
          })
        } else if (fmt === 'summary') {
          // Top-k signals only (cap at 10)
          const signals = (responseData['top_signals'] as unknown[]) ?? []
          return dualOutput({ ...responseData, top_signals: signals.slice(0, 10), response_format: 'summary' })
        }
        // 'full' — cap at 100 signals hard limit
        const signals = (responseData['top_signals'] as unknown[]) ?? []
        return dualOutput({ ...responseData, top_signals: signals.slice(0, 100), response_format: 'full' })
      } catch (err) {
        return errorOutput('get_chart_orientation', String(err), { chart_id })
      }
    }
  )

  // ── get_domain_reading (L-DOMAIN drill) ──────────────────────────────────
  // marsys://tool/L2/query_domain_reading
  server.tool(
    'get_domain_reading',
    'Retrieves the L2 Bodha domain activation reading for a specific life domain (career, relationship, health, wealth, spirituality, character). In Jyotish, each domain (bhava) is governed by a karaka planet and a set of signifying houses — career by the 10th lord and its dispositor chain; relationship by the 7th lord and Venus; health by the Lagna lord and the 6th/8th. This tool surfaces which MSR signals are active in the named domain, ranked by computed_salience, with their constituent L1 facts and classical derivation chain. Always returns an orientation_context from the L2 UCD as the holistic frame (B.11 by construction).',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().describe(
        'Life domain to drill: career, relationship, character, spirituality, wealth, health, or other domain name.'
      ),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      cursor: z.string().optional().describe('Pagination cursor (from previous response.next_cursor)'),
      max_lenses: z.number().int().min(1).max(12).optional().describe(
        'Max question lenses to return (default: 3 for token safety; pass 12 for full payload).'
      ),
      max_signals_per_lens: z.number().int().min(1).max(100).optional().describe(
        'Max signals per lens (default: 20).'
      ),
    },
    async ({ chart_id, domain, ayanamsha_id, cursor, max_lenses, max_signals_per_lens }) => {
      if (!chart_id) return errorOutput('get_domain_reading', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before domain drill
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id, ayanamsha_id ?? 'LAHIRI')
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_domain_reading',
          { chart_id, domain, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', cursor },
          chart_id
        )
        // F-021: Bound the response — default 3 lenses × 20 signals (was 17MB / 90k signal objects)
        const domainData = data as Record<string, unknown>
        const lenses = (domainData['question_lenses'] as unknown[]) ?? []
        const maxLenses = max_lenses ?? 3
        const maxSig = max_signals_per_lens ?? 20
        const boundedLenses = lenses.slice(0, maxLenses).map((lens) => {
          const l = lens as Record<string, unknown>
          const signals = (l['signals'] as unknown[]) ?? []
          const signalIdRefs = (l['signal_id_refs'] as unknown[]) ?? []
          // F-023: dedup signal_id_refs (was byte-for-byte duplicate of template_element_ids)
          const uniqueSignalIdRefs = [...new Set(signalIdRefs as string[])]
          return { ...l, signals: signals.slice(0, maxSig), signal_id_refs: uniqueSignalIdRefs }
        })
        return dualOutput({
          orientation_context,
          orientation_ok,
          ...domainData,
          question_lenses: boundedLenses,
          lenses_total: lenses.length,
          lenses_returned: boundedLenses.length,
          token_safety_note: `Bounded to ${maxLenses} lenses × ${maxSig} signals. Pass max_lenses=12 + max_signals_per_lens=100 for full payload.`,
        })
      } catch (err) {
        return errorOutput('get_domain_reading', String(err), { chart_id, domain })
      }
    }
  )

  // ── get_signals (L-SIGNAL ranked signals) ────────────────────────────────
  // marsys://tool/L2/query_signals
  server.tool(
    'get_signals',
    'Retrieves ranked MSR (Multi-Signal Repository) signals for a chart — the 573-signal corpus of astrological patterns derived from L1 Gaṇita facts. Each signal encodes a classical Jyotish observation (yoga, placement, aspect, nakshatra condition) with its constituent L1 fact_ids, a computed_salience score reflecting how prominently it operates in this chart, and the domain tags it activates. Use min_salience to focus on high-confidence signals (≥0.7 = strong; ≥0.5 = moderate). The signal layer is the analytical backbone: get_domain_reading and get_chart_orientation both synthesize from this corpus. Query directly when you need raw signal evidence for a specific claim.',
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
        // B.11: fetch holistic orientation before signal drill
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id, ayanamsha_id ?? 'LAHIRI')
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_signals',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', domain, min_salience, limit: limit ?? 50, cursor, lel_enabled: lel_enabled ?? false },
          chart_id
        )
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
        // B.11: fetch holistic orientation before graph traversal
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id)
        const data = await callRegistryCapability(
          'marsys://tool/L2/traverse_chart_graph',
          { chart_id, seed_signal_ids, mode: mode ?? 'neighbors', depth: depth ?? 2 },
          chart_id
        )
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
    'Retrieves the Vimshottari dasha chain from L1 Gaṇita — the 120-year planetary period sequence that governs the timing of karma in Parashara Jyotish. Each planet rules a fixed span (Sun 6 yr, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17, Ketu 7, Venus 20), subdivided into antardasha (sub-periods) and pratyantardasha. The running period lord colors all life events during its tenure: its natal placement, lordship, aspects received, and conjunctions determine what it delivers. Use this to identify which lords are active now and in the near future, then cross-reference with get_temporal_windows and get_signals to see which yogas those lords activate.',
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
    'Retrieves the L3 Kāla temporal activation layer for a date range — identifying which Jyotish periods (Vimshottari dasha, antardasha, pratyantardasha) are running, which MSR signals are activated by those period lords, and where convergence windows occur (multiple activation streams peaking simultaneously). In classical Jyotish, timing is the hardest discipline: a powerful yoga (structural combination) only gives its results when its constituent lords run their period. This tool applies that temporal gate — distinguishing signals that are structurally present from those that are temporally ripe. Returns orientation_context (B.11) alongside temporal data.',
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
        // B.11: fetch holistic orientation before temporal domain query
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id, ayanamsha_id ?? 'LAHIRI')
        const data = await callRegistryCapability(
          'marsys://tool/L3/query_temporal_activation',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', date_from, date_to, include_convergence: include_convergence ?? true },
          chart_id
        )
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
      max_projections: z.number().int().min(1).max(200).optional().describe(
        'Max projections to return (default: 20; was unbounded at 117KB+).'
      ),
    },
    async ({ chart_id, ayanamsha_id, domain, horizon_years, max_projections }) => {
      if (!chart_id) return errorOutput('get_projections', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before predictive projection
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id, ayanamsha_id ?? 'LAHIRI')
        const data = await callRegistryCapability(
          'marsys://tool/L3/query_projections',
          { chart_id, ayanamsha_id: ayanamsha_id ?? 'LAHIRI', domain, horizon_years: horizon_years ?? 5 },
          chart_id
        )
        // F-008: Cap projections array — was 117KB unbounded
        const projData = data as Record<string, unknown>
        const projections = (projData['projections'] as unknown[]) ?? []
        const cap = max_projections ?? 20
        const boundedProjections = projections.slice(0, cap)
        return dualOutput({
          orientation_context,
          orientation_ok,
          ...projData,
          projections: boundedProjections,
          projections_total: projections.length,
          projections_returned: boundedProjections.length,
        })
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
        // B.11: fetch holistic orientation before remedy prescription
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id)
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_remedies',
          { chart_id, domain, remedy_type },
          chart_id
        )
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
        // B.11: fetch holistic orientation before quality/calibration surface
        const { orientation_context, orientation_ok } = await fetchOrientationContext(chart_id)
        const data = await callRegistryCapability(
          'marsys://tool/L2/query_quality_scorecard',
          { chart_id },
          chart_id
        )
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
