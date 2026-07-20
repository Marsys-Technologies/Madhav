/**
 * bo_2-8.ts — holistic_bundle MCP tool (L2 Bodha, BRAHMA-BO-2-8)
 *
 * B.11 whole-chart-read entrypoint. One call returns all 4 L2 Bodha subsystems
 * (MSR signals + CGM graph edges + CDLM domain links + RM resonance) coherently.
 *
 * Tool name:  holistic_bundle
 * Input:      { chart_id: string }
 * Output:     { signals, graph_edges, domain_links, resonance, provenance_envelope }
 *
 * Architecture:
 *   - Calls the Python sidecar at POST /api/compute/brahma/bodha/holistic_bundle
 *   - Per-subsystem error isolation: one failed subsystem produces an empty array,
 *     not a bundle failure; provenance_envelope.subsystems_errored records failures.
 *   - No caching at this layer (caching deferred to BO-2-9 or platform layer).
 *   - Surgical: false — this IS the B.11 floor, not a bypass of it.
 *
 * BRAHMA-BO-2-8
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── Environment ────────────────────────────────────────────────────────────────

const PYTHON_SIDECAR_URL = (
  process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
).replace(/\/$/, '')

const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''
const TOOL_TIMEOUT_MS = 30_000

// ── Response types ─────────────────────────────────────────────────────────────

export interface SignalRow {
  signal_id: string
  domain: string
  valence: string
  confidence: number | null
  salience: number | null
  state: string | null
  signal_text: string
  source_citation: string | null
  graha_refs: string[] | null
  house_refs: number[] | null
  created_at: string
}

export interface GraphEdgeRow {
  edge_id: string
  from_signal_id: string
  to_signal_id: string
  edge_type: string
  weight: number | null
  label: string | null
  created_at: string
}

export interface DomainLinkRow {
  link_id: string
  from_domain: string
  to_domain: string
  link_type: string
  signal_ids: string[] | null
  strength: number | null
  note: string | null
  created_at: string
}

export interface ResonanceRow {
  resonance_id: string
  theme: string
  signal_ids: string[] | null
  resonance_type: string
  amplitude: number | null
  note: string | null
  created_at: string
}

export interface ProvenanceEnvelope {
  chart_id: string
  queried_at: string
  subsystems_ok: string[]
  subsystems_errored: string[]
  signal_count: number
  graph_edge_count: number
  domain_link_count: number
  resonance_count: number
  b11_floor_passed: boolean
  error?: string
}

export interface HolisticBundleResult {
  signals: SignalRow[]
  graph_edges: GraphEdgeRow[]
  domain_links: DomainLinkRow[]
  resonance: ResonanceRow[]
  provenance_envelope: ProvenanceEnvelope
}

// ── Sidecar caller ─────────────────────────────────────────────────────────────

async function callSidecarHolisticBundle(chartId: string): Promise<HolisticBundleResult> {
  const url = `${PYTHON_SIDECAR_URL}/api/compute/brahma/bodha/holistic_bundle`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(SIDECAR_API_KEY ? { 'X-API-Key': SIDECAR_API_KEY } : {}),
    },
    body: JSON.stringify({ chart_id: chartId }),
    signal: AbortSignal.timeout(TOOL_TIMEOUT_MS),
  })

  if (!response.ok) {
    const text = await response.text().catch(() => '(no body)')
    throw new Error(`Sidecar returned HTTP ${response.status}: ${text}`)
  }

  const json = (await response.json()) as { ok: boolean; result: HolisticBundleResult }
  if (!json.ok || !json.result) {
    throw new Error('Sidecar returned ok:false or missing result')
  }

  return json.result
}

// ── MCP tool registration ──────────────────────────────────────────────────────

/**
 * Register the holistic_bundle tool on the given McpServer instance.
 *
 * Called once per request in server.ts (stateless per-request server pattern).
 */
export function registerHolisticBundleTool(
  server: McpServer,
  principal: Principal
): void {
  server.tool(
    // Tool name
    'holistic_bundle',

    // Description (shown to the LLM)
    [
      'B.11 whole-chart-read entrypoint (Brahma L2 Bodha, BO-2-8).',
      'Returns all four L2 Bodha subsystems coherently in one call:',
      '  signals      — MSR (Multidimensional Signal Register): grounded signals per domain',
      '  graph_edges  — CGM (Chart Graph Model): valenced edges (reinforce/contradict/…)',
      '  domain_links — CDLM (Cross-Domain Linkage Matrix): cross-domain linkages',
      '  resonance    — RM (Resonance Map): thematic resonance elements',
      'provenance_envelope carries subsystem health + B.11 floor pass/fail flag.',
      'Use before any synthesis query that must read the whole chart.',
    ].join('\n'),

    // Input schema
    {
      chart_id: z
        .string()
        .min(1)
        .describe('UUID of the chart to read (e.g. the native chart UUID from the charts table)'),
    },

    // Handler
    async ({ chart_id }): Promise<{ content: Array<{ type: 'text'; text: string }> }> => {
      // M0 entitlement gate — require view access to the requested chart
      const authorized = await remoteAuthorize(principal, chart_id)
      if (!authorized) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'AUTHZ_DENIED', chart_id }) }], isError: true } as never
      }

      const t0 = Date.now()
      let bundle: HolisticBundleResult

      try {
        bundle = await callSidecarHolisticBundle(chart_id)
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        const errorBundle: HolisticBundleResult = {
          signals: [],
          graph_edges: [],
          domain_links: [],
          resonance: [],
          provenance_envelope: {
            chart_id,
            queried_at: new Date().toISOString(),
            subsystems_ok: [],
            subsystems_errored: ['MSR', 'CGM', 'CDLM', 'RM'],
            signal_count: 0,
            graph_edge_count: 0,
            domain_link_count: 0,
            resonance_count: 0,
            b11_floor_passed: false,
            error: message,
          },
        }
        const latency = Date.now() - t0
        const budgetedError = budgetMcpContent(
          {
            ok: false,
            tool: 'holistic_bundle',
            brahma_unit: 'BO-2-8',
            latency_ms: latency,
            result: errorBundle,
            error: message,
          },
          'holistic_bundle',
        )
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(budgetedError, null, 2),
            },
          ],
        }
      }

      const latency = Date.now() - t0
      const envelope = bundle.provenance_envelope

      const budgeted = budgetMcpContent(
        {
          ok: true,
          tool: 'holistic_bundle',
          brahma_unit: 'BO-2-8',
          latency_ms: latency,
          b11_floor_passed: envelope.b11_floor_passed,
          summary: {
            signal_count: envelope.signal_count,
            graph_edge_count: envelope.graph_edge_count,
            domain_link_count: envelope.domain_link_count,
            resonance_count: envelope.resonance_count,
            subsystems_ok: envelope.subsystems_ok,
            subsystems_errored: envelope.subsystems_errored,
          },
          result: bundle,
        },
        'holistic_bundle',
      )

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(budgeted, null, 2),
          },
        ],
      }
    }
  )
}
