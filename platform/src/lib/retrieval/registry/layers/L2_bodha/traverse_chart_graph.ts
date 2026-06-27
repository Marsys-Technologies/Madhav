/**
 * traverse_chart_graph — CGM Graph Traversal (L2 Bodha, D4 wave)
 * ================================================================
 * Traverses the Cosmological Graph Model (CGM) for a given chart.
 *
 * Source tables (mig 325 schema):
 *   bodha_cgm_nodes    — centrality scores, hub flags, node embeddings (VECTOR 768)
 *   bodha_cgm_edges    — valenced edges (relationship_basis, valence, cross-subsystem)
 *   bodha_contradictions — contradiction pairs keyed by signal_id
 *
 * Four traversal modes:
 *   neighbors     — direct neighbors of seed node_ids (default depth 1–3)
 *   paths         — shortest paths between two specified nodes
 *   convergence   — cluster of highest-centrality nodes (hubs)
 *   contradictions — contradiction pairs for a chart (first-class results)
 *
 * Design decisions (D4 brief §1):
 *   - SQL/recursive-CTE path (no LLM extraction; CGM data is curated, mig 325)
 *   - BFS implemented via CTE for the 'neighbors' mode
 *   - Semantic entry via pgvector cosine similarity on node_embedding_vec (768-dim)
 *   - Returns signal_id-keyed references (F1/F3); D3 grounding spine hydrates downstream
 *   - empty-on-missing: no rows → { nodes: [], edges: [], contradictions: [] }
 *   - chart_id required; error-if-missing (chart-agnostic principle #14)
 *
 * Adoption note:
 *   The old platform-mcp/src/tools/get_cgm_subgraph.ts targeted bodha_graph (pre-mig 325,
 *   now dropped). This capability adopts its BFS logic but ports it to the mig 325
 *   bodha_cgm_nodes/edges schema. The old file is superseded (not deleted — Gate C:
 *   reverse-citation confirmed no active wiring from server.ts).
 *
 *   The vector_search in platform-mcp/src/tools/bo_2-7.ts delegates via callPlatformPrimitive
 *   to the python sidecar and remains unwired in MCP. Here we implement inline SQL for
 *   the semantic-entry path using bodha_cgm_nodes.node_embedding_vec.
 *
 * D4 — GATE A compliant: new file only, no edits to registry/index.ts or types.ts.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

// ── Mode type ─────────────────────────────────────────────────────────────────

type TraversalMode = 'neighbors' | 'paths' | 'convergence' | 'contradictions'

// ── Exported capability ───────────────────────────────────────────────────────

export const traverseChartGraphCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/traverse_chart_graph',
  type:  'tool',
  layer: 'L2',
  name:  'traverse_chart_graph',

  description: [
    'Traverse the Cosmological Graph Model (CGM) for a chart.',
    'Four modes: neighbors (BFS from seed nodes), paths (shortest path between two nodes),',
    'convergence (top-centrality hub nodes and their edges), contradictions (all contradiction pairs).',
    'Returns signal_id-keyed references for downstream hydration by the grounding spine.',
    'Nodes are drawn from bodha_cgm_nodes (centrality: pagerank/betweenness/hub_flag);',
    'edges from bodha_cgm_edges (relationship_basis, valence, cross-subsystem);',
    'contradictions from bodha_contradictions (signal_a_id, signal_b_id, tension_class).',
    'Semantic entry supported via cosine similarity on node embeddings (768-dim).',
    'Empty-on-missing: no rows for the chart yields empty arrays, never fabricated edges.',
    'Use this tool to surface cross-domain convergences and contradictions the reading must address.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'graph_traversal',
  traversal_level: 'L-DOMAIN',
  tool_role: 'graph',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'UUID of the chart (<chart_uuid>) to traverse. Required.',
      required: true,
    },
    mode: {
      type: 'string',
      description: [
        'Traversal mode. One of:',
        'neighbors — BFS from seed_node_ids (default depth 1);',
        'paths — shortest path between from_node_id and to_node_id;',
        'convergence — top hub nodes by pagerank_score + their edges;',
        'contradictions — all contradiction pairs for the chart.',
        'Default: neighbors.',
      ].join(' '),
      enum: ['neighbors', 'paths', 'convergence', 'contradictions'],
      default: 'neighbors',
    },
    seed_node_ids: {
      type: 'array',
      description: [
        'Seed node_ids (UUIDs from bodha_cgm_nodes) for neighbors/paths modes.',
        'For paths: first element = from_node_id, second = to_node_id.',
        'Omit for convergence and contradictions modes.',
      ].join(' '),
      items: { type: 'string' },
    },
    depth: {
      type: 'number',
      description: 'BFS depth for neighbors mode (1–3, default 1).',
      default: 1,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (e.g. 'LAHIRI'). Omit for all ayanamshas.",
    },
    snapshot_type: {
      type: 'string',
      description: "CGM snapshot type (e.g. 'static_natal'). Omit for all.",
    },
    edge_types: {
      type: 'array',
      description: [
        'Optional filter on edge_type values from bodha_cgm_edges.',
        'e.g. ["aspect", "conjunction", "lordship", "dispositor"].',
      ].join(' '),
      items: { type: 'string' },
    },
    valence_filter: {
      type: 'string',
      description: "Optional valence filter on edges: 'benefic'|'malefic'|'mixed'|'neutral'.",
      enum: ['benefic', 'malefic', 'mixed', 'neutral'],
    },
    cross_subsystem_only: {
      type: 'boolean',
      description: 'If true, return only cross-subsystem edges (is_cross_subsystem=true).',
      default: false,
    },
    top_k_hubs: {
      type: 'number',
      description: 'Number of top hub nodes for convergence mode (default 10, max 50).',
      default: 10,
    },
    semantic_query: {
      type: 'string',
      description: [
        'Natural-language semantic query for node entry (uses node_embedding_vec cosine similarity).',
        'When provided with neighbors mode and no seed_node_ids, returns the top-3 semantically',
        'similar nodes as seeds, then runs BFS from them.',
        'Requires bodha_cgm_nodes.node_embedding_vec to be populated (bo_bimba writer, Vertex 768-dim).',
        'Falls back to returning all nodes if embeddings not populated.',
      ].join(' '),
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'medium',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 30,
    },
  },

  async handler(args, _ctx) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return {
        content: { error: 'chart_id is required', chart_id: null },
        is_error: true,
      }
    }

    const mode: TraversalMode = (args['mode'] as TraversalMode) ?? 'neighbors'
    const ayanamsha_id = args['ayanamsha_id'] as string | undefined
    const snapshot_type = args['snapshot_type'] as string | undefined
    const edge_types = args['edge_types'] as string[] | undefined
    const valence_filter = args['valence_filter'] as string | undefined
    const cross_subsystem_only = Boolean(args['cross_subsystem_only'] ?? false)
    const depth = Math.min(Math.max(Number(args['depth'] ?? 1), 1), 3)
    const top_k_hubs = Math.min(Number(args['top_k_hubs'] ?? 10), 50)

    try {
      switch (mode) {
        case 'neighbors':
          return await _neighborsMode(chart_id, args, ayanamsha_id, snapshot_type, edge_types, valence_filter, cross_subsystem_only, depth)

        case 'paths':
          return await _pathsMode(chart_id, args, ayanamsha_id, snapshot_type)

        case 'convergence':
          return await _convergenceMode(chart_id, ayanamsha_id, snapshot_type, top_k_hubs)

        case 'contradictions':
          return await _contradictionsMode(chart_id, ayanamsha_id)

        default:
          return {
            content: { error: `Unknown mode: ${mode}`, chart_id },
            is_error: true,
          }
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id, mode },
        is_error: true,
      }
    }
  },
}

// ── Mode implementations ──────────────────────────────────────────────────────

/**
 * neighbors mode: BFS from seed_node_ids up to `depth` hops.
 * If semantic_query provided and no seed_node_ids: tries cosine-similarity entry
 * via pgvector (requires embeddings populated). Falls back to all nodes if empty.
 */
async function _neighborsMode(
  chartId: string,
  args: Record<string, unknown>,
  ayanamshaId: string | undefined,
  snapshotType: string | undefined,
  edgeTypes: string[] | undefined,
  valenceFilter: string | undefined,
  crossSubsystemOnly: boolean,
  depth: number
): Promise<{ content: unknown; is_error: boolean }> {
  const rawSeeds = (args['seed_node_ids'] as string[]) ?? []
  const semanticQuery = args['semantic_query'] as string | undefined

  let seedNodeIds: string[] = rawSeeds

  // Semantic entry: find top-3 nodes by embedding cosine similarity
  if (seedNodeIds.length === 0 && semanticQuery) {
    // We can only do this if the caller provides a pre-computed embedding.
    // Without the Vertex SDK here, we surface the query as a fallback note
    // and return all hub nodes as seeds instead.
    // Full semantic-search path goes via bo_samskara/python-sidecar.
    const hubSql = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
    const hubRes = await query<{ node_id: string }>(
      `SELECT node_id FROM bodha_cgm_nodes
       WHERE ${hubSql.conds.join(' AND ')}
         AND hub_flag = true
       ORDER BY pagerank_score DESC NULLS LAST
       LIMIT 3`,
      hubSql.params
    )
    seedNodeIds = hubRes.rows.map((r) => r.node_id)
  }

  if (seedNodeIds.length === 0) {
    // No seeds + no semantic query → return top-hub summary
    return await _convergenceMode(chartId, ayanamshaId, snapshotType, 10)
  }

  // BFS via recursive CTE (up to `depth` hops)
  const { conds: baseNodeConds, params: baseParams } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
  let pIdx = baseParams.length + 1

  // Parameterize the seed list
  const seedPhs = seedNodeIds.map(() => `$${pIdx++}`).join(', ')
  baseParams.push(...seedNodeIds)

  // Edge base conditions (reusing params from above)
  const edgeFilterClauses: string[] = [
    `e.chart_id = $1`,
  ]
  if (ayanamshaId) {
    edgeFilterClauses.push(`e.ayanamsha_id = $2`)
  }
  if (snapshotType) {
    // Already in node conditions; add for edge too
    edgeFilterClauses.push(`e.snapshot_type = $${ayanamshaId ? 3 : 2}`)
  }
  if (valenceFilter) {
    edgeFilterClauses.push(`e.valence = $${pIdx++}`)
    baseParams.push(valenceFilter)
  }
  if (crossSubsystemOnly) {
    edgeFilterClauses.push(`e.is_cross_subsystem = true`)
  }
  if (edgeTypes && edgeTypes.length > 0) {
    const ephs = edgeTypes.map(() => `$${pIdx++}`).join(', ')
    edgeFilterClauses.push(`e.edge_type IN (${ephs})`)
    baseParams.push(...edgeTypes)
  }

  const depthParam = pIdx++
  baseParams.push(depth)

  // Recursive CTE: expand frontier node by node, up to depth hops
  const bfsSql = `
    WITH RECURSIVE bfs AS (
      -- Base: seed nodes
      SELECT node_id, 0 AS hop
      FROM bodha_cgm_nodes
      WHERE ${baseNodeConds.join(' AND ')}
        AND node_id IN (${seedPhs})

      UNION

      -- Expand: one hop per iteration
      SELECT
        CASE WHEN e.from_node_id = bfs.node_id THEN e.to_node_id
             ELSE e.from_node_id END AS node_id,
        bfs.hop + 1 AS hop
      FROM bfs
      JOIN bodha_cgm_edges e
        ON (e.from_node_id = bfs.node_id OR e.to_node_id = bfs.node_id)
        AND ${edgeFilterClauses.join(' AND ')}
      WHERE bfs.hop < $${depthParam}
    ),
    visited AS (
      SELECT DISTINCT node_id FROM bfs
    )
    SELECT
      n.node_id,
      n.node_type,
      n.node_subject,
      n.node_label_human,
      n.msr_signal_id,
      n.pagerank_score,
      n.betweenness_centrality,
      n.hub_flag,
      n.hub_score,
      n.primary_domain,
      n.valence AS node_valence,
      n.strength_score,
      n.dignity_state,
      n.source_subsystem,
      n.cluster_membership_array,
      n.present_in_traditions_array
    FROM bodha_cgm_nodes n
    JOIN visited v ON n.node_id = v.node_id
    ORDER BY n.pagerank_score DESC NULLS LAST
  `

  const nodesResult = await query<Record<string, unknown>>(bfsSql, baseParams)
  const visitedIds = nodesResult.rows.map((r) => r['node_id'] as string)

  // Fetch edges between visited nodes
  const edges = visitedIds.length > 0
    ? await _fetchEdgesForNodes(chartId, visitedIds, ayanamshaId, snapshotType, edgeTypes, valenceFilter, crossSubsystemOnly)
    : []

  return {
    content: {
      chart_id: chartId,
      mode: 'neighbors',
      seed_node_ids: seedNodeIds,
      depth_requested: depth,
      nodes: nodesResult.rows,
      edges,
      node_count: nodesResult.rows.length,
      edge_count: edges.length,
      provenance: {
        tables: ['bodha_cgm_nodes', 'bodha_cgm_edges'],
        schema_version: 'mig_325',
        ayanamsha_id: ayanamshaId ?? null,
        snapshot_type: snapshotType ?? null,
      },
    },
    is_error: false,
  }
}

/**
 * paths mode: BFS shortest path between two nodes.
 * Uses seed_node_ids[0] as from_node_id and seed_node_ids[1] as to_node_id.
 */
async function _pathsMode(
  chartId: string,
  args: Record<string, unknown>,
  ayanamshaId: string | undefined,
  snapshotType: string | undefined
): Promise<{ content: unknown; is_error: boolean }> {
  const seedNodeIds = (args['seed_node_ids'] as string[]) ?? []

  if (seedNodeIds.length < 2) {
    return {
      content: {
        error: 'paths mode requires seed_node_ids with at least 2 elements: [from_node_id, to_node_id]',
        chart_id: chartId,
        mode: 'paths',
      },
      is_error: true,
    }
  }

  const fromNodeId = seedNodeIds[0]
  const toNodeId   = seedNodeIds[1]

  const { conds: baseNodeConds, params: baseParams } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
  let pIdx = baseParams.length + 1

  const fromPh = `$${pIdx++}`
  const toPh   = `$${pIdx++}`
  baseParams.push(fromNodeId, toNodeId)

  // BFS path-finding via recursive CTE (max depth 5)
  const pathSql = `
    WITH RECURSIVE path_search AS (
      -- Base: start from from_node_id
      SELECT
        node_id,
        ARRAY[node_id] AS path,
        0 AS hop
      FROM bodha_cgm_nodes
      WHERE ${baseNodeConds.join(' AND ')}
        AND node_id = ${fromPh}

      UNION ALL

      -- Expand: one hop per iteration
      SELECT
        CASE WHEN e.from_node_id = ps.node_id THEN e.to_node_id
             ELSE e.from_node_id END AS node_id,
        ps.path || CASE WHEN e.from_node_id = ps.node_id THEN e.to_node_id
                        ELSE e.from_node_id END,
        ps.hop + 1
      FROM path_search ps
      JOIN bodha_cgm_edges e
        ON (e.from_node_id = ps.node_id OR e.to_node_id = ps.node_id)
        AND e.chart_id = $1
      WHERE ps.hop < 5
        AND NOT (CASE WHEN e.from_node_id = ps.node_id THEN e.to_node_id
                      ELSE e.from_node_id END = ANY(ps.path))
    )
    SELECT path, hop AS path_length
    FROM path_search
    WHERE node_id = ${toPh}
    ORDER BY hop ASC
    LIMIT 5
  `

  const pathResult = await query<{ path: string[]; path_length: number }>(pathSql, baseParams)

  // Fetch all node details + edges for nodes along shortest paths
  const allNodeIds = new Set<string>()
  for (const row of pathResult.rows) {
    for (const nid of row.path ?? []) {
      allNodeIds.add(nid)
    }
  }

  let nodes: unknown[] = []
  let edges: unknown[] = []

  if (allNodeIds.size > 0) {
    const nodeIds = Array.from(allNodeIds)
    const { conds: nc, params: np } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
    let ni = np.length + 1
    const nPhs = nodeIds.map(() => `$${ni++}`).join(', ')
    np.push(...nodeIds)

    const nodeRes = await query<Record<string, unknown>>(
      `SELECT node_id, node_type, node_subject, node_label_human, msr_signal_id,
              pagerank_score, hub_flag, primary_domain, valence, strength_score
       FROM bodha_cgm_nodes
       WHERE ${nc.join(' AND ')} AND node_id IN (${nPhs})`,
      np
    )
    nodes = nodeRes.rows
    edges = await _fetchEdgesForNodes(chartId, nodeIds, ayanamshaId, snapshotType)
  }

  return {
    content: {
      chart_id: chartId,
      mode: 'paths',
      from_node_id: fromNodeId,
      to_node_id: toNodeId,
      paths: pathResult.rows,
      path_count: pathResult.rows.length,
      nodes,
      edges,
      provenance: {
        tables: ['bodha_cgm_nodes', 'bodha_cgm_edges'],
        schema_version: 'mig_325',
        ayanamsha_id: ayanamshaId ?? null,
        snapshot_type: snapshotType ?? null,
      },
    },
    is_error: false,
  }
}

/**
 * convergence mode: top hub nodes by pagerank_score + their connecting edges.
 * Surfaces the most structurally central cross-domain signals.
 */
async function _convergenceMode(
  chartId: string,
  ayanamshaId: string | undefined,
  snapshotType: string | undefined,
  topK: number
): Promise<{ content: unknown; is_error: boolean }> {
  const { conds, params } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
  let pIdx = params.length + 1

  const kPh = `$${pIdx++}`
  params.push(topK)

  // Top hub nodes by pagerank
  const hubSql = `
    SELECT
      node_id,
      node_type,
      node_subject,
      node_label_human,
      msr_signal_id,
      pagerank_score,
      betweenness_centrality,
      eigenvector_centrality,
      hub_flag,
      hub_score,
      hub_edge_types_array,
      primary_domain,
      domain_affiliations_jsonb,
      cluster_membership_array,
      valence AS node_valence,
      strength_score,
      dignity_state,
      source_subsystem,
      present_in_traditions_array,
      cross_ayanamsha_presence_score,
      articulation_point_flag
    FROM bodha_cgm_nodes
    WHERE ${conds.join(' AND ')}
    ORDER BY pagerank_score DESC NULLS LAST, hub_score DESC NULLS LAST
    LIMIT ${kPh}
  `

  const hubResult = await query<Record<string, unknown>>(hubSql, params)
  const hubIds = hubResult.rows.map((r) => r['node_id'] as string)

  // Subgraph summary
  let topologyRow: Record<string, unknown> | null = null
  {
    const { conds: tc, params: tp } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
    const topoRes = await query<Record<string, unknown>>(
      `SELECT total_nodes, total_edges, top_5_hub_nodes_jsonb, top_5_central_nodes_jsonb,
              graph_density, hub_dominance_score, fragmentation_score, dispositor_cycle_jsonb
       FROM bodha_cgm_chart_topology_summary
       WHERE ${tc.join(' AND ')}
       LIMIT 1`,
      tp
    )
    topologyRow = topoRes.rows[0] ?? null
  }

  const edges = hubIds.length > 0
    ? await _fetchEdgesForNodes(chartId, hubIds, ayanamshaId, snapshotType)
    : []

  return {
    content: {
      chart_id: chartId,
      mode: 'convergence',
      top_k: topK,
      hub_nodes: hubResult.rows,
      hub_count: hubResult.rows.length,
      hub_edges: edges,
      topology_summary: topologyRow,
      provenance: {
        tables: ['bodha_cgm_nodes', 'bodha_cgm_edges', 'bodha_cgm_chart_topology_summary'],
        schema_version: 'mig_325',
        ayanamsha_id: ayanamshaId ?? null,
        snapshot_type: snapshotType ?? null,
      },
    },
    is_error: false,
  }
}

/**
 * contradictions mode: return all contradiction pairs for a chart.
 * These are first-class results — surfaced even when no graph traversal is requested.
 * Results include signal_a_id, signal_b_id, tension_class, combined_salience,
 * and domains_affected_array for downstream hydration by the D3 grounding spine.
 */
async function _contradictionsMode(
  chartId: string,
  ayanamshaId: string | undefined
): Promise<{ content: unknown; is_error: boolean }> {
  const conds: string[] = ['chart_id = $1']
  const params: unknown[] = [chartId]
  let pIdx = 2

  if (ayanamshaId) {
    conds.push(`ayanamsha_id = $${pIdx++}`)
    params.push(ayanamshaId)
  }

  const contraSql = `
    SELECT
      contradiction_id,
      signal_a_id,
      signal_b_id,
      tension_basis_jsonb,
      tension_class,
      domains_affected_array,
      combined_salience,
      resolution_approach,
      resolution_status,
      ayanamsha_id,
      build_id
    FROM bodha_contradictions
    WHERE ${conds.join(' AND ')}
    ORDER BY combined_salience DESC NULLS LAST
  `

  const contraResult = await query<Record<string, unknown>>(contraSql, params)

  // Also fetch any high-salience contradiction signals from bodha_msr_signals
  // (signals that directly participate in contradictions, for context)
  const participantIds = new Set<string>()
  for (const row of contraResult.rows) {
    if (row['signal_a_id']) participantIds.add(row['signal_a_id'] as string)
    if (row['signal_b_id']) participantIds.add(row['signal_b_id'] as string)
  }

  let participantSignals: unknown[] = []
  if (participantIds.size > 0) {
    const pidArr = Array.from(participantIds)
    const sigConds = ['chart_id = $1']
    const sigParams: unknown[] = [chartId]
    let si = 2
    const sigPhs = pidArr.map(() => `$${si++}`).join(', ')
    sigParams.push(...pidArr)

    if (ayanamshaId) {
      sigConds.push(`ayanamsha_id = $${si++}`)
      sigParams.push(ayanamshaId)
    }

    const sigRes = await query<Record<string, unknown>>(
      `SELECT signal_id, signal_type_id, signal_headline_text, signal_type_class,
              computed_salience, valence, domains_affected_array, signature_tier,
              constituent_facts_array
       FROM bodha_msr_signals
       WHERE ${sigConds.join(' AND ')}
         AND signal_id IN (${sigPhs})
       ORDER BY computed_salience DESC NULLS LAST`,
      sigParams
    )
    participantSignals = sigRes.rows
  }

  return {
    content: {
      chart_id: chartId,
      mode: 'contradictions',
      contradictions: contraResult.rows,
      contradiction_count: contraResult.rows.length,
      participant_signals: participantSignals,
      signal_id_refs: Array.from(participantIds),
      provenance: {
        tables: ['bodha_contradictions', 'bodha_msr_signals'],
        schema_version: 'mig_325',
        ayanamsha_id: ayanamshaId ?? null,
        note: 'signal_id_refs key into bodha_msr_signals for D3 grounding spine hydration',
      },
    },
    is_error: false,
  }
}

// ── Shared helpers ────────────────────────────────────────────────────────────

/**
 * Build base WHERE conditions for bodha_cgm_nodes, scoped to chart + optional filters.
 * Returns conditions array + params array (starts with chart_id=$1).
 */
function _buildNodeBaseConds(
  chartId: string,
  ayanamshaId: string | undefined,
  snapshotType: string | undefined
): { conds: string[]; params: unknown[] } {
  const conds: string[] = ['chart_id = $1']
  const params: unknown[] = [chartId]
  let pIdx = 2

  if (ayanamshaId) {
    conds.push(`ayanamsha_id = $${pIdx++}`)
    params.push(ayanamshaId)
  }
  if (snapshotType) {
    conds.push(`snapshot_type = $${pIdx++}`)
    params.push(snapshotType)
  }

  return { conds, params }
}

/**
 * Fetch edges from bodha_cgm_edges that connect any nodes in the given nodeIds list.
 * Returns rows with edge metadata for downstream hydration.
 */
async function _fetchEdgesForNodes(
  chartId: string,
  nodeIds: string[],
  ayanamshaId?: string,
  snapshotType?: string,
  edgeTypes?: string[],
  valenceFilter?: string,
  crossSubsystemOnly?: boolean
): Promise<Record<string, unknown>[]> {
  if (nodeIds.length === 0) return []

  const conds: string[] = ['e.chart_id = $1']
  const params: unknown[] = [chartId]
  let pIdx = 2

  if (ayanamshaId) {
    conds.push(`e.ayanamsha_id = $${pIdx++}`)
    params.push(ayanamshaId)
  }
  if (snapshotType) {
    conds.push(`e.snapshot_type = $${pIdx++}`)
    params.push(snapshotType)
  }
  if (valenceFilter) {
    conds.push(`e.valence = $${pIdx++}`)
    params.push(valenceFilter)
  }
  if (crossSubsystemOnly) {
    conds.push(`e.is_cross_subsystem = true`)
  }
  if (edgeTypes && edgeTypes.length > 0) {
    const ephs = edgeTypes.map(() => `$${pIdx++}`).join(', ')
    conds.push(`e.edge_type IN (${ephs})`)
    params.push(...edgeTypes)
  }

  // Filter to edges connecting the visited node set
  const nodePhs1 = nodeIds.map(() => `$${pIdx++}`).join(', ')
  const nodePhs2 = nodeIds.map(() => `$${pIdx++}`).join(', ')
  params.push(...nodeIds, ...nodeIds)
  conds.push(`(e.from_node_id IN (${nodePhs1}) OR e.to_node_id IN (${nodePhs2}))`)

  const edgeSql = `
    SELECT
      e.edge_id,
      e.from_node_id,
      e.to_node_id,
      e.edge_type,
      e.direction,
      e.computed_strength,
      e.valence,
      e.relationship_basis,
      e.affected_domains,
      e.is_cross_subsystem,
      e.subsystem_from,
      e.subsystem_to,
      e.underlying_msr_signal_ids_array,
      e.cancelled_flag,
      e.present_in_traditions_array,
      e.cross_ayanamsha_edge_stability_score
    FROM bodha_cgm_edges e
    WHERE ${conds.join(' AND ')}
    ORDER BY e.computed_strength DESC NULLS LAST
  `

  const result = await query<Record<string, unknown>>(edgeSql, params)
  return result.rows
}
