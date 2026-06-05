/**
 * retrieval/holistic_bundle.ts — BRAHMA-BO-2-9: B.11 Whole-Chart-Read composite tool
 *
 * B.11 Whole-Chart-Read discipline: every query routes through L2.5 Holistic
 * Synthesis first (MSR + CDLM + CGM + RM) before producing a domain-specific answer.
 *
 * This tool reads DIRECTLY from chart_facts (L1 + L2 bodha.* categories):
 *   1. ganita.positions   — L1 planet positions (Lahiri ayanamsha)
 *   2. bodha.signals      — L2 MSR signals (SCAFFOLD: 569 signals, all UNGROUNDED)
 *   3. bodha.domain_links — L2 CDLM cross-domain linkages
 *   4. bodha.resonance    — L2 RM resonance patterns
 *   5. bodha.graph        — L2 CGM edges (optional — enriches context)
 *
 * Tool name:  holistic_bundle
 * Input:      { chart_id?: string, include_graph?: boolean }
 * Output:     {
 *               positions, signals, domain_links, resonance, graph_edges?,
 *               grounding_status: 'SCAFFOLD',
 *               b11_floor_passed: boolean,
 *               provenance_envelope
 *             }
 *
 * Grounding status notice: ALL signals in this bundle carry:
 *   rule_id: null, grounding_status: 'UNGROUNDED'
 *   grounding_note: 'Scaffold pass — awaiting WS-3 rule_base'
 * This is a scaffold bundle. The l2-bodha-grounded session (after tag
 * ws3-rule-base-complete) re-derives with real rule IDs.
 *
 * Wiring: registerHolisticBundleRetrievalTool(server) in server.ts
 * Note: bo_2-8.ts (holistic_bundle via sidecar) remains registered in parallel.
 *
 * BRAHMA-BO-2-9 / l2-bodha-scaffold
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB pool ────────────────────────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool | null {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) return null
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Native canonical chart ─────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

// ── Types ──────────────────────────────────────────────────────────────────────

interface PositionRow {
  fact_subject: string
  graha: string
  sign: string
  nakshatra: string
  nakshatra_pada: number
  house: number
  sidereal_longitude: number
  ayanamsha: string
}

interface SignalRow {
  signal_id: string
  signal_text: string
  domain: string
  valence: string
  strength_score: number | null
  confidence: number | null
  rule_id: null                    // Always null at scaffold pass
  grounding_status: 'UNGROUNDED'  // Always UNGROUNDED at scaffold pass
}

interface DomainLinkRow {
  link_id: string
  source_domain: string
  target_domain: string
  link_type: string
  strength: number | null
  direction: string
  valence: string
  key_finding: string
  msr_anchors: string[]
}

interface ResonanceRow {
  pattern_id: string
  element_text: string
  domains_primary: string[]
  resonance_type: string
  strength: number
  net_resonance: string
}

interface GraphEdgeRow {
  edge_id: string
  source_node: string
  target_node: string
  edge_type: string
  weight: number
  domain: string
}

interface BundleResult {
  positions:     PositionRow[]
  signals:       SignalRow[]
  domain_links:  DomainLinkRow[]
  resonance:     ResonanceRow[]
  graph_edges?:  GraphEdgeRow[]
  grounding_status: 'SCAFFOLD'
  b11_floor_passed: boolean
  provenance_envelope: {
    chart_id:            string
    queried_at:          string
    source:              string
    layer_coverage:      string[]
    position_count:      number
    signal_count:        number
    domain_link_count:   number
    resonance_count:     number
    graph_edge_count:    number
    grounding_status:    'SCAFFOLD'
    grounding_note:      string
    rule_id_all_null:    boolean
    b11_floor_passed:    boolean
    subsystems_errored:  string[]
  }
}

// ── Subsystem fetchers ─────────────────────────────────────────────────────────

async function fetchPositions(
  client: pg.PoolClient,
  chartId: string,
): Promise<PositionRow[]> {
  const result = await client.query<{ fact_subject: string; fact_value: Record<string, unknown> }>(
    `SELECT fact_subject, fact_value
     FROM chart_facts
     WHERE chart_id = $1
       AND fact_category = 'ganita.positions'
       AND fact_subject LIKE '%_lahiri'
     ORDER BY fact_subject
     LIMIT 20`,
    [chartId],
  )
  return result.rows.map(r => ({
    fact_subject:       r.fact_subject,
    graha:              String(r.fact_value['graha'] ?? ''),
    sign:               String(r.fact_value['sign'] ?? ''),
    nakshatra:          String(r.fact_value['nakshatra'] ?? ''),
    nakshatra_pada:     Number(r.fact_value['nakshatra_pada'] ?? 0),
    house:              Number(r.fact_value['house'] ?? 0),
    sidereal_longitude: Number(r.fact_value['sidereal_longitude'] ?? 0),
    ayanamsha:          String(r.fact_value['ayanamsha'] ?? 'lahiri'),
  }))
}

async function fetchSignals(
  client: pg.PoolClient,
  chartId: string,
  limit = 573,
): Promise<SignalRow[]> {
  const result = await client.query<{ fact_subject: string; fact_value: Record<string, unknown> }>(
    `SELECT fact_subject, fact_value
     FROM chart_facts
     WHERE chart_id = $1
       AND fact_category = 'bodha.signals'
     ORDER BY fact_subject
     LIMIT $2`,
    [chartId, limit],
  )
  return result.rows.map(r => ({
    signal_id:     r.fact_subject,
    signal_text:   String(r.fact_value['signal_text'] ?? r.fact_value['signal_name'] ?? ''),
    domain:        String(r.fact_value['domain'] ?? 'unknown'),
    valence:       String(r.fact_value['valence'] ?? 'context-dependent'),
    strength_score:r.fact_value['strength_score'] != null ? Number(r.fact_value['strength_score']) : null,
    confidence:    r.fact_value['confidence'] != null ? Number(r.fact_value['confidence']) : null,
    rule_id:       null,           // Hardcoded null — scaffold pass requirement
    grounding_status: 'UNGROUNDED' as const,
  }))
}

async function fetchDomainLinks(
  client: pg.PoolClient,
  chartId: string,
): Promise<DomainLinkRow[]> {
  const result = await client.query<{ fact_subject: string; fact_value: Record<string, unknown> }>(
    `SELECT fact_subject, fact_value
     FROM chart_facts
     WHERE chart_id = $1
       AND fact_category = 'bodha.domain_links'
     ORDER BY fact_subject`,
    [chartId],
  )
  return result.rows.map(r => ({
    link_id:       r.fact_subject,
    source_domain: String(r.fact_value['source_domain'] ?? ''),
    target_domain: String(r.fact_value['target_domain'] ?? ''),
    link_type:     String(r.fact_value['link_type'] ?? 'feeds'),
    strength:      r.fact_value['strength'] != null ? Number(r.fact_value['strength']) : null,
    direction:     String(r.fact_value['direction'] ?? 'row→col'),
    valence:       String(r.fact_value['valence'] ?? 'mixed'),
    key_finding:   String(r.fact_value['key_finding'] ?? ''),
    msr_anchors:   Array.isArray(r.fact_value['msr_anchors'])
      ? (r.fact_value['msr_anchors'] as string[])
      : [],
  }))
}

async function fetchResonance(
  client: pg.PoolClient,
  chartId: string,
): Promise<ResonanceRow[]> {
  const result = await client.query<{ fact_subject: string; fact_value: Record<string, unknown> }>(
    `SELECT fact_subject, fact_value
     FROM chart_facts
     WHERE chart_id = $1
       AND fact_category = 'bodha.resonance'
     ORDER BY fact_subject`,
    [chartId],
  )
  return result.rows.map(r => ({
    pattern_id:      r.fact_subject,
    element_text:    String(r.fact_value['element_text'] ?? ''),
    domains_primary: Array.isArray(r.fact_value['domains_primary'])
      ? (r.fact_value['domains_primary'] as string[])
      : [],
    resonance_type:  String(r.fact_value['resonance_type'] ?? 'neutral'),
    strength:        Number(r.fact_value['strength'] ?? 0.5),
    net_resonance:   String(r.fact_value['net_resonance'] ?? ''),
  }))
}

async function fetchGraphEdges(
  client: pg.PoolClient,
  chartId: string,
): Promise<GraphEdgeRow[]> {
  const result = await client.query<{ fact_subject: string; fact_value: Record<string, unknown> }>(
    `SELECT fact_subject, fact_value
     FROM chart_facts
     WHERE chart_id = $1
       AND fact_category = 'bodha.graph'
     ORDER BY fact_subject
     LIMIT 110`,
    [chartId],
  )
  return result.rows.map(r => ({
    edge_id:     r.fact_subject,
    source_node: String(r.fact_value['source_node'] ?? ''),
    target_node: String(r.fact_value['target_node'] ?? ''),
    edge_type:   String(r.fact_value['edge_type'] ?? ''),
    weight:      Number(r.fact_value['weight'] ?? 0.7),
    domain:      String(r.fact_value['domain'] ?? 'chart'),
  }))
}

// ── Tool registration ──────────────────────────────────────────────────────────

export function registerHolisticBundleRetrievalTool(server: McpServer): void {
  server.tool(
    'holistic_bundle_chart_facts',
    {
      chart_id: z.string().uuid().optional().describe(
        'Chart UUID. Defaults to native canonical chart if omitted.'
      ),
      include_graph: z.boolean().optional().default(false).describe(
        'Include bodha.graph (CGM edge set) in the bundle. Default: false.'
      ),
    },
    async ({ chart_id, include_graph = false }) => {
      const targetChartId = chart_id ?? NATIVE_CHART_ID
      const queriedAt = new Date().toISOString()
      const pool = getPool()

      // Static scaffold bundle when DB is unavailable
      if (!pool) {
        const scaffoldBundle: BundleResult = {
          positions:    [],
          signals:      [],
          domain_links: [],
          resonance:    [],
          grounding_status: 'SCAFFOLD',
          b11_floor_passed: false,
          provenance_envelope: {
            chart_id:           targetChartId,
            queried_at:         queriedAt,
            source:             'chart_facts (DATABASE_UNAVAILABLE)',
            layer_coverage:     ['L1-ganita', 'L2-bodha'],
            position_count:     0,
            signal_count:       0,
            domain_link_count:  0,
            resonance_count:    0,
            graph_edge_count:   0,
            grounding_status:   'SCAFFOLD',
            grounding_note:     'Scaffold pass — all signals UNGROUNDED; awaiting WS-3 rule_base',
            rule_id_all_null:   true,
            b11_floor_passed:   false,
            subsystems_errored: ['DATABASE_UNAVAILABLE'],
          },
        }
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify(scaffoldBundle, null, 2),
          }],
        }
      }

      let client: pg.PoolClient | null = null
      const subsystems_errored: string[] = []

      try {
        client = await pool.connect()

        // Fetch all subsystems with per-subsystem error isolation
        let positions: PositionRow[] = []
        let signals: SignalRow[] = []
        let domain_links: DomainLinkRow[] = []
        let resonance: ResonanceRow[] = []
        let graph_edges: GraphEdgeRow[] = []

        try {
          positions = await fetchPositions(client, targetChartId)
        } catch (e) {
          subsystems_errored.push(`ganita.positions: ${e instanceof Error ? e.message : String(e)}`)
        }

        try {
          signals = await fetchSignals(client, targetChartId)
        } catch (e) {
          subsystems_errored.push(`bodha.signals: ${e instanceof Error ? e.message : String(e)}`)
        }

        try {
          domain_links = await fetchDomainLinks(client, targetChartId)
        } catch (e) {
          subsystems_errored.push(`bodha.domain_links: ${e instanceof Error ? e.message : String(e)}`)
        }

        try {
          resonance = await fetchResonance(client, targetChartId)
        } catch (e) {
          subsystems_errored.push(`bodha.resonance: ${e instanceof Error ? e.message : String(e)}`)
        }

        if (include_graph) {
          try {
            graph_edges = await fetchGraphEdges(client, targetChartId)
          } catch (e) {
            subsystems_errored.push(`bodha.graph: ${e instanceof Error ? e.message : String(e)}`)
          }
        }

        // B.11 floor: signals present AND domain_links present AND positions present
        const b11_floor_passed =
          signals.length > 0 &&
          domain_links.length > 0 &&
          positions.length > 0

        // Verify all signals are UNGROUNDED (scaffold integrity check)
        const rule_id_all_null = signals.every(s => s.rule_id === null)

        const bundle: BundleResult = {
          positions,
          signals,
          domain_links,
          resonance,
          ...(include_graph ? { graph_edges } : {}),
          grounding_status: 'SCAFFOLD',
          b11_floor_passed,
          provenance_envelope: {
            chart_id:           targetChartId,
            queried_at:         queriedAt,
            source:             'chart_facts',
            layer_coverage:     ['L1-ganita', 'L2-bodha.signals', 'L2-bodha.domain_links', 'L2-bodha.resonance'],
            position_count:     positions.length,
            signal_count:       signals.length,
            domain_link_count:  domain_links.length,
            resonance_count:    resonance.length,
            graph_edge_count:   graph_edges.length,
            grounding_status:   'SCAFFOLD',
            grounding_note:     'Scaffold pass — all signals UNGROUNDED (rule_id=null); l2-bodha-grounded session re-derives post ws3-rule-base-complete tag',
            rule_id_all_null,
            b11_floor_passed,
            subsystems_errored,
          },
        }

        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify(bundle, null, 2),
          }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              status: 'ERROR',
              error: msg,
              chart_id: targetChartId,
              grounding_status: 'SCAFFOLD',
              b11_floor_passed: false,
            }, null, 2),
          }],
        }
      } finally {
        if (client) client.release()
      }
    }
  )
}
