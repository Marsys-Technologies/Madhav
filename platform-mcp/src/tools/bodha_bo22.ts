/**
 * bodha_bo22.ts — BRAHMA-BO-2-2: cgm_subgraph tool
 *
 * Retrieves the CGM signal graph (bodha.graph) — valenced edges between
 * CGM nodes (PLN.*, HSE.*, SGN.*, etc.) for a given chart_id.
 *
 * Contract (BRAHMA_L1_L5_REGISTRY_SEED §C — bodha.graph):
 *   owns:   CGM signal graph — valenced edges (reinforce/contradict/modulate/…)
 *           between signals
 *   tool:   cgm_subgraph(chart_id, signal_ids?) → edges with provenance
 *   table:  bodha_graph (chart_id, from_signal_id, to_signal_id, edge_type,
 *           weight, source_citation)
 *   gate:   valenced edges present; traversal returns provenance; no self-loops
 *   FORENSIC: ≥5 edges for native's chart (1984-02-05, Abhisek Mohanty)
 *
 * Source data: 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json
 *   22 reconciled edges (batch 2, session Madhav_M2A_Exec_5/6; 0 P2 violations)
 *   21 seeded (CGM_EDGE_014 PLN.VENUS→PLN.VENUS self-loop excluded per contract)
 *
 * Wiring: register via registerBodhaGraphTool(server) in server.ts
 *
 * BRAHMA-BO-2-2
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB pool (lazy singleton — created on first tool call) ─────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      throw new Error(
        '[bodha_bo22] DATABASE_URL not set — cannot connect to bodha_graph table'
      )
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BodhaEdge {
  edge_id: string
  from_signal_id: string
  to_signal_id: string
  edge_type: string
  weight: number
  source_citation: string
  ayanamsha_id: string
  build_id: string | null
}

export interface CgmSubgraphResult {
  chart_id: string
  signal_ids_requested: string[] | null
  edge_count: number
  edges: BodhaEdge[]
  traversal_hops: number
}

// ── Core query function ───────────────────────────────────────────────────────

/**
 * Query bodha_graph for a chart, optionally seeded by signal_ids with BFS.
 *
 * If signal_ids is empty/null, returns all edges for the chart.
 * BFS traversal depth controlled by hops (default 1).
 *
 * No self-loops are returned (enforced by CHECK constraint in bodha_graph).
 */
export async function queryCgmSubgraph(
  chartId: string,
  opts: {
    signalIds?: string[]
    edgeTypes?: string[]
    hops?: number
    ayanamshaId?: string
  } = {}
): Promise<CgmSubgraphResult> {
  const { signalIds, edgeTypes, hops = 1, ayanamshaId } = opts
  const pool = getPool()
  const client = await pool.connect()

  try {
    // Build base conditions
    const baseConds: string[] = ['chart_id = $1']
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
      let visitedNodes = new Set<string>(signalIds)
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

      // Final fetch: all edges touching any visited node
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

    const edges: BodhaEdge[] = rows.map((r) => ({
      edge_id: r.edge_id as string,
      from_signal_id: r.from_signal_id as string,
      to_signal_id: r.to_signal_id as string,
      edge_type: r.edge_type as string,
      weight: typeof r.weight === 'string' ? parseFloat(r.weight) : (r.weight as number),
      source_citation: r.source_citation as string,
      ayanamsha_id: r.ayanamsha_id as string,
      build_id: (r.build_id as string | null) ?? null,
    }))

    return {
      chart_id: chartId,
      signal_ids_requested: signalIds ?? null,
      edge_count: edges.length,
      edges,
      traversal_hops: hops,
    }
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
      'UUID of the chart to query. Must be a valid chart UUID from the charts table.'
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
    .array(
      z.enum([
        'DISPOSITED_BY',
        'NAKSHATRA_LORD_IS',
        'ASPECTS_3RD',
        'ASPECTS_4TH',
        'ASPECTS_8TH',
        'REINFORCES',
        'CONTRADICTS',
        'MODULATES',
      ])
    )
    .optional()
    .describe(
      'Optional filter on edge types. ' +
        'DISPOSITED_BY = sign-lord chain; ' +
        'NAKSHATRA_LORD_IS = nakshatra-lord relationship; ' +
        'ASPECTS_3RD/4TH/8TH = special graha aspects; ' +
        'REINFORCES/CONTRADICTS/MODULATES = valenced signal relationships.'
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
 * Example:
 *   import { registerBodhaGraphTool } from './tools/bodha_bo22.js'
 *   registerBodhaGraphTool(server)
 */
export function registerBodhaGraphTool(server: McpServer): void {
  server.tool(
    TOOL_NAME,
    'Retrieve the CGM signal graph (bodha.graph) — valenced edges between CGM nodes ' +
      '(PLN.*, HSE.*, SGN.*, etc.) for a given chart. ' +
      'Edges types: DISPOSITED_BY (sign-lord chain), NAKSHATRA_LORD_IS (nakshatra lord), ' +
      'ASPECTS_3RD/4TH/8TH (special graha aspects), REINFORCES/CONTRADICTS/MODULATES. ' +
      'All edges carry source_citation back to FORENSIC_v8_0. ' +
      'Use signal_ids to seed a BFS traversal across the planetary relationship graph. ' +
      'No self-loops are returned (contract constraint). ' +
      'Source: 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json (22 reconciled edges, batch 2). ' +
      'BRAHMA-BO-2-2 | bodha.graph contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      try {
        const result = await queryCgmSubgraph(input.chart_id, {
          signalIds: input.signal_ids,
          edgeTypes: input.edge_types as string[] | undefined,
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
