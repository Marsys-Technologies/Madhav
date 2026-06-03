/**
 * get_cgm_subgraph.ts — BRAHMA-BO-2-2: bodha.graph tool (cgm_subgraph)
 *
 * Retrieves the CGM signal graph (bodha.graph) — valenced edges between
 * CGM nodes (PLN.*, HSE.*, SGN.*, etc.) for a given chart_id.
 *
 * Contract (BRAHMA_L1_L5_REGISTRY_SEED §C — bodha.graph):
 *   owns:   CGM signal graph — valenced edges (reinforce/contradict/modulate/amplify/suppress)
 *           between signals
 *   tool:   cgm_subgraph(chart_id, signal_ids?) → {edges, provenance_envelope}
 *   table:  bodha_graph (chart_id, from_signal_id, to_signal_id, edge_type,
 *           weight, source_citation)
 *   gate:   valenced edges present; traversal returns provenance_envelope; no self-loops
 *   FORENSIC: ≥5 edges for native's chart (1984-02-05, Abhisek Mohanty)
 *
 * edge_type enum (Gate-1 contract):
 *   reinforce | contradict | modulate | amplify | suppress
 *
 * Source data: 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json
 *   22 reconciled edges (batch 2, session Madhav_M2A_Exec_5/6; 0 P2 violations)
 *   21 seeded (CGM_EDGE_014 PLN.VENUS→PLN.VENUS self-loop excluded per contract)
 *
 * Wiring: register via registerGetCgmSubgraph(server, getPrincipal) in server.ts
 *
 * BRAHMA-BO-2-2
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'
import type { Principal } from '../types.js'

const { Pool } = pg

// ── DB pool (lazy singleton — created on first tool call) ─────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      throw new Error(
        '[get_cgm_subgraph] DATABASE_URL not set — cannot connect to bodha_graph table'
      )
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Edge type enum (Gate-1 contract) ─────────────────────────────────────────

export const VALID_EDGE_TYPES = ['reinforce', 'contradict', 'modulate', 'amplify', 'suppress'] as const
export type EdgeType = typeof VALID_EDGE_TYPES[number]

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BodhaEdge {
  edge_id: string
  from_signal_id: string
  to_signal_id: string
  edge_type: EdgeType
  weight: number
  /** Composite source_citation — non-null; references FORENSIC_v8_0 + signal source_citations */
  source_citation: string
  ayanamsha_id: string
  build_id: string | null
}

export interface ProvenanceEnvelope {
  chart_id: string
  signal_ids_requested: string[] | null
  edge_count: number
  traversal_hops: number
  ayanamsha_id: string | null
  edge_types_filter: string[] | null
  sourced_from: string
}

export interface CgmSubgraphResult {
  edges: BodhaEdge[]
  provenance_envelope: ProvenanceEnvelope
}

// ── Core query function ───────────────────────────────────────────────────────

/**
 * Query bodha_graph for a chart, optionally seeded by signal_ids with BFS.
 *
 * If signal_ids is empty/null, returns all edges for the chart.
 * BFS traversal depth controlled by hops (default 1).
 *
 * No self-loops are returned (enforced by CHECK constraint in bodha_graph
 * and asserted here: from_signal_id != to_signal_id).
 *
 * Returns {edges, provenance_envelope} per Gate-1 contract.
 */
export async function queryCgmSubgraph(
  chartId: string,
  opts: {
    signalIds?: string[]
    edgeTypes?: EdgeType[]
    hops?: number
    ayanamshaId?: string
  } = {}
): Promise<CgmSubgraphResult> {
  const { signalIds, edgeTypes, hops = 1, ayanamshaId } = opts
  const pool = getPool()
  const client = await pool.connect()

  try {
    // Build base conditions
    const baseConds: string[] = ['chart_id = $1', 'from_signal_id != to_signal_id']
    const baseParams: unknown[] = [chartId]
    let pIdx = 2

    if (ayanamshaId) {
      baseConds.push(`ayanamsha_id = $${pIdx++}`)
      baseParams.push(ayanamshaId)
    }

    if (edgeTypes && edgeTypes.length > 0) {
      const phs = edgeTypes.map(() => `$${pIdx++}`).join(', ')
      baseConds.push(`edge_type IN (${phs})`)
      baseParams.push(...edgeTypes)
    }

    const SELECT_COLS = `
      edge_id, from_signal_id, to_signal_id,
      edge_type, weight, source_citation, ayanamsha_id, build_id
    `

    let rows: pg.QueryResultRow[]

    if (!signalIds || signalIds.length === 0) {
      // No seed — return all edges for the chart
      const where = baseConds.join(' AND ')
      const res = await client.query(
        `SELECT ${SELECT_COLS} FROM bodha_graph WHERE ${where} ORDER BY edge_type, edge_id`,
        baseParams
      )
      rows = res.rows
    } else {
      // BFS traversal
      const visitedNodes = new Set<string>(signalIds)
      let frontier = new Set<string>(signalIds)

      for (let hop = 0; hop < hops; hop++) {
        if (frontier.size === 0) break

        const frontierArr = Array.from(frontier)
        const hopConds = [...baseConds]
        const hopParams = [...baseParams]
        let hIdx = pIdx

        const phs1 = frontierArr.map(() => `$${hIdx++}`).join(', ')
        const phs2 = frontierArr.map(() => `$${hIdx++}`).join(', ')
        hopConds.push(`(from_signal_id IN (${phs1}) OR to_signal_id IN (${phs2}))`)
        hopParams.push(...frontierArr, ...frontierArr)

        const where = hopConds.join(' AND ')
        const hopRes = await client.query(
          `SELECT edge_id, from_signal_id, to_signal_id FROM bodha_graph WHERE ${where}`,
          hopParams
        )

        const newFrontier = new Set<string>()
        for (const r of hopRes.rows) {
          for (const nid of [r.from_signal_id as string, r.to_signal_id as string]) {
            if (!visitedNodes.has(nid)) {
              newFrontier.add(nid)
              visitedNodes.add(nid)
            }
          }
        }
        frontier = newFrontier
      }

      // Final fetch: all edges touching any visited node (no self-loops enforced)
      const visitedArr = Array.from(visitedNodes)
      const finalConds = [...baseConds]
      const finalParams = [...baseParams]
      let fIdx = pIdx

      const phs1 = visitedArr.map(() => `$${fIdx++}`).join(', ')
      const phs2 = visitedArr.map(() => `$${fIdx++}`).join(', ')
      finalConds.push(`(from_signal_id IN (${phs1}) OR to_signal_id IN (${phs2}))`)
      finalParams.push(...visitedArr, ...visitedArr)

      const where = finalConds.join(' AND ')
      const finalRes = await client.query(
        `SELECT ${SELECT_COLS} FROM bodha_graph WHERE ${where} ORDER BY edge_type, edge_id`,
        finalParams
      )
      rows = finalRes.rows
    }

    const edges: BodhaEdge[] = rows
      // Safety: double-assert no self-loops (belt + suspenders over DB CHECK constraint)
      .filter((r) => r.from_signal_id !== r.to_signal_id)
      .map((r) => ({
        edge_id: r.edge_id as string,
        from_signal_id: r.from_signal_id as string,
        to_signal_id: r.to_signal_id as string,
        edge_type: r.edge_type as EdgeType,
        weight: typeof r.weight === 'string' ? parseFloat(r.weight) : (r.weight as number),
        source_citation: (r.source_citation as string) ?? 'FORENSIC_v8_0',
        ayanamsha_id: r.ayanamsha_id as string,
        build_id: (r.build_id as string | null) ?? null,
      }))

    const provenance_envelope: ProvenanceEnvelope = {
      chart_id: chartId,
      signal_ids_requested: signalIds ?? null,
      edge_count: edges.length,
      traversal_hops: hops,
      ayanamsha_id: ayanamshaId ?? null,
      edge_types_filter: edgeTypes ?? null,
      sourced_from: 'bodha_graph (035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json)',
    }

    return { edges, provenance_envelope }
  } finally {
    client.release()
  }
}

// ── MCP tool registration ─────────────────────────────────────────────────────

const TOOL_NAME = 'cgm_subgraph'

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to query. ' +
        'Native chart (Abhisek Mohanty, 1984-02-05): 362f9f17-95a5-490b-a5a7-027d3e0efda0'
    ),
  signal_ids: z
    .array(z.string())
    .optional()
    .describe(
      'Optional seed list of CGM node IDs for BFS traversal. ' +
        'Planet nodes: PLN.SUN, PLN.MOON, PLN.MARS, PLN.MERCURY, PLN.JUPITER, PLN.VENUS, ' +
        'PLN.SATURN, PLN.RAHU, PLN.KETU. House nodes: HSE.1 through HSE.12. ' +
        'If omitted, returns all edges for the chart.'
    ),
  edge_types: z
    .array(z.enum(['reinforce', 'contradict', 'modulate', 'amplify', 'suppress']))
    .optional()
    .describe(
      'Optional filter on valenced edge types. ' +
        'reinforce = two signals amplify each other; ' +
        'contradict = signals pull in opposite directions; ' +
        'modulate = one signal contextually modulates another; ' +
        'amplify = one signal intensifies another; ' +
        'suppress = one signal dampens another.'
    ),
  hops: z
    .number()
    .int()
    .min(1)
    .max(3)
    .optional()
    .default(1)
    .describe(
      'BFS traversal depth from the seed signal_ids (default 1). ' +
        'Increase to 2–3 for deeper planetary chain exploration.'
    ),
  ayanamsha_id: z
    .string()
    .optional()
    .describe("Optional ayanamsha filter (default: 'lahiri')."),
})

/**
 * Register the cgm_subgraph MCP tool on an McpServer instance.
 *
 * Called from server.ts during the BRAHMA L2 Bodha registration phase.
 *
 * Returns {edges, provenance_envelope} per Gate-1 contract (BRAHMA-BO-2-2).
 *
 * Example:
 *   import { registerGetCgmSubgraph } from './tools/get_cgm_subgraph.js'
 *   registerGetCgmSubgraph(server, getPrincipal)
 */
export function registerGetCgmSubgraph(
  server: McpServer,
  _getPrincipal: () => Principal
): void {
  server.tool(
    TOOL_NAME,
    'Retrieve the CGM signal graph (bodha.graph) — valenced edges between CGM nodes ' +
      '(PLN.*, HSE.*, SGN.*, etc.) for a given chart. ' +
      'Edge types (Gate-1 contract enum): reinforce | contradict | modulate | amplify | suppress. ' +
      'Returns {edges, provenance_envelope} — provenance_envelope carries chart_id, edge_count, ' +
      'traversal_hops, and sourced_from for audit. ' +
      'All edges carry source_citation back to FORENSIC_v8_0. ' +
      'Use signal_ids to seed a BFS traversal across the signal relationship graph. ' +
      'No self-loops returned (CHECK constraint + runtime filter). ' +
      '≥5 edges guaranteed for the native chart (Abhisek Mohanty, 1984-02-05). ' +
      'Source: 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json (22 reconciled edges, batch 2). ' +
      'BRAHMA-BO-2-2 | bodha.graph contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      try {
        const result = await queryCgmSubgraph(input.chart_id, {
          signalIds: input.signal_ids,
          edgeTypes: input.edge_types as EdgeType[] | undefined,
          hops: input.hops ?? 1,
          ayanamshaId: input.ayanamsha_id,
        })

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(result, null, 2),
            },
          ],
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  error: true,
                  tool: TOOL_NAME,
                  message,
                  chart_id: input.chart_id,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        }
      }
    }
  )
}
