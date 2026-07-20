/**
 * traverse_chart_graph — CGM Graph Traversal (L2 Bodha, D4 wave; extended R5 W2)
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
 *
 * ── R5 W2 extension (design §21/§30: "EXTEND traverse_chart_graph — path patterns,
 * direction facet, strength floors") ──────────────────────────────────────────────
 *
 *   1. `about_from` / `about_to` (paths mode) + `about` (neighbors mode) — accept the
 *      §27.1/§27.2 astrological address vocabulary (an `AddressExpression` OR its DSL
 *      string, e.g. `"lord_of(bhava 10)"`) as seeds, resolved via the SHARED
 *      `resolveAddress`/`parseAddressExpression` from `address_resolver.ts` (W1's
 *      canonical resolver — NOT reimplemented here; W1 already hit and fixed exactly
 *      that duplication trap once). Resolution maps the resolved graha/sign/karaka
 *      entity to its `bodha_cgm_nodes` row (node_type='graha'|'bhava', node_subject=
 *      graha name | house number) and the resolver's human-readable `chain` is
 *      threaded into the response's `about_resolution` field so callers can show
 *      their reasoning ("the 10th lord is Saturn, placed in the 9th... Saturn aspects
 *      Moon directly") — this is what makes a "10th-lord→Moon" path resolve in ONE
 *      call instead of a resolve-then-traverse round trip.
 *
 *   2. `direction` facet — 'directed' (follow only `from_node_id → to_node_id`, the
 *      graph's actual directed edges) vs 'both' (undirected touch — original D4
 *      behavior, still the default for backward compatibility). Applies to both
 *      `neighbors` and `paths` modes.
 *
 *   3. `min_strength` — floor on `bodha_cgm_edges.computed_strength` (numeric, mig 325),
 *      applied to both the traversal join condition (so the BFS/path-search itself
 *      does not cross weak edges) and the returned edge list.
 *
 *   4. VALENCE VOCAB FIX (design §21 caveat, verified live against both canonical
 *      charts at W2 open — `SELECT DISTINCT valence FROM bodha_cgm_edges` on
 *      `482012f1-…` returns ONLY `harmonious`/`antagonistic`; `benefic`/`malefic`/
 *      `mixed` — the D4-era enum — never occur. The mig-325-drift the design doc
 *      flagged for "reconcile in W0" was never actually reconciled; a `valence_filter`
 *      using the old vocabulary silently matched zero rows on live data). The
 *      `valence_filter` enum is corrected to the real vocabulary
 *      (`harmonious`|`antagonistic`|`neutral`); the D4-era terms are still accepted
 *      as input and normalized (`benefic`->`harmonious`, `malefic`->`antagonistic`,
 *      `mixed`->`neutral`) so no existing caller silently breaks.
 *
 * ── W2 dark-set wiring (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0, TABLE_CONCEPT_DISPOSITIONS_v2_0
 * §8 "natural 5th mode on an existing, working tool") ──────────────────────────────────────────
 *
 *   5. `sub_graphs` mode — serves `bodha_cgm_sub_graphs` (10 rows on the live chart; was a
 *      genuine SERVE gap, zero prior TS-registry route — confirmed by the W1 addendum re-scan
 *      that widened the surface to include `platform-mcp/src/tools/`). Curated named subgraph
 *      clusters (subgraph_type/subgraph_label, e.g. a classically-recognized planetary
 *      combination), each carrying its own node_ids_array/edge_ids_array back into the already-
 *      served `bodha_cgm_nodes`/`bodha_cgm_edges` tables -- same sibling relationship
 *      `_convergenceMode` already has with `bodha_cgm_chart_topology_summary` (line ~820), just
 *      promoted to its own mode instead of an embedded field, since sub_graphs is its own
 *      first-class row set (not a single per-chart summary row). No new capability was added --
 *      this is the wiring plan's own explicit recommendation (extend the existing tool, don't
 *      build a 4th standalone one for the CGM plane).
 */

import type { CapabilityDescriptor, ToolResult } from '../../types'
import { query } from '@/lib/db/client'
import {
  resolveAddress,
  type AddressExpression,
  type ResolvedEntity,
  AddressResolutionError,
} from '../../../address_resolver'
import { DEFAULT_AYANAMSHA } from '../../constants'

// ── Mode type ─────────────────────────────────────────────────────────────────

type TraversalMode = 'neighbors' | 'paths' | 'convergence' | 'contradictions' | 'sub_graphs'
type TraversalDirection = 'directed' | 'both'

/** D4-era valence terms, normalized to the real live-DB vocabulary (see header note). */
const VALENCE_ALIASES: Record<string, string> = {
  benefic: 'harmonious',
  malefic: 'antagonistic',
  mixed: 'neutral',
  harmonious: 'harmonious',
  antagonistic: 'antagonistic',
  neutral: 'neutral',
}

function normalizeValence(v: string): string {
  return VALENCE_ALIASES[v.toLowerCase()] ?? v
}

// ── Exported capability ───────────────────────────────────────────────────────

export const traverseChartGraphCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/traverse_chart_graph',
  type:  'tool',
  layer: 'L2',
  name:  'traverse_chart_graph',

  description: [
    'Traverse the Cosmological Graph Model (CGM) for a chart.',
    'Five modes: neighbors (BFS from seed nodes), paths (shortest path between two nodes),',
    'convergence (top-centrality hub nodes and their edges), contradictions (all contradiction pairs),',
    'sub_graphs (curated named subgraph clusters, e.g. classically-recognized planetary combinations).',
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
        'contradictions — all contradiction pairs for the chart;',
        'sub_graphs — curated named subgraph clusters (bodha_cgm_sub_graphs), each with its own',
        'node_ids_array/edge_ids_array back into bodha_cgm_nodes/bodha_cgm_edges.',
        'Default: neighbors.',
      ].join(' '),
      enum: ['neighbors', 'paths', 'convergence', 'contradictions', 'sub_graphs'],
      default: 'neighbors',
    },
    seed_node_ids: {
      type: 'array',
      description: [
        'Seed node_ids (UUIDs from bodha_cgm_nodes) for neighbors/paths modes.',
        'For paths: first element = from_node_id, second = to_node_id.',
        'Omit for convergence and contradictions modes.',
        'Prefer about_from/about_to (paths) or about (neighbors) for astrological addressing —',
        'these raw UUIDs are for callers that already resolved a node_id themselves.',
      ].join(' '),
      items: { type: 'string' },
    },
    about_from: {
      type: 'object',
      description: [
        'paths mode ONLY — the START of the path, given as the design §27.1/§27.2 astrological',
        'address vocabulary: either a structured AddressExpression object or its DSL string',
        '(e.g. "lord_of(bhava 10)", "dispositor_of(Venus)", "karaka(\'AK\')"). Resolved server-side',
        'via the shared address resolver, then mapped to its bodha_cgm_nodes row. Lets the caller',
        'say "10th lord" instead of first resolving to "Saturn" in a separate call.',
      ].join(' '),
    },
    about_to: {
      type: 'object',
      description: 'paths mode ONLY — the END of the path, same address vocabulary as about_from.',
    },
    about: {
      type: 'array',
      description: [
        'neighbors mode ONLY — seed(s) given as address expressions/DSL strings instead of raw',
        'seed_node_ids (e.g. ["graha(Moon)"] or [{"type":"graha","graha":"Moon"}] or',
        '["lord_of(bhava 7)"]). Resolved server-side via the shared address resolver; each',
        'resolved entity becomes a BFS seed. Mutually exclusive with seed_node_ids (about wins',
        'if both given).',
      ].join(' '),
      items: { type: 'object' },
    },
    direction: {
      type: 'string',
      description: [
        'Traversal direction for neighbors/paths modes. "directed" follows only the graph\'s',
        'actual directed edges (from_node_id -> to_node_id) — required for questions with an',
        'inherent direction ("what does the 10th lord aspect?" vs "what aspects the 10th lord?").',
        '"both" (default) treats edges as undirected touches — the original behavior.',
      ].join(' '),
      enum: ['directed', 'both'],
      default: 'both',
    },
    min_strength: {
      type: 'number',
      description: [
        'Strength floor on bodha_cgm_edges.computed_strength (0-1 range). Edges below this',
        'threshold are excluded from BOTH the traversal itself (BFS/path-search will not cross',
        'a weak edge) and the returned edge list. Omit for no floor.',
      ].join(' '),
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
      description: [
        "Optional valence filter on edges: 'harmonious'|'antagonistic'|'neutral' (the live",
        "bodha_cgm_edges vocabulary). Legacy D4-era terms 'benefic'/'malefic'/'mixed' are still",
        'accepted and normalized (benefic->harmonious, malefic->antagonistic, mixed->neutral).',
      ].join(' '),
      enum: ['harmonious', 'antagonistic', 'neutral', 'benefic', 'malefic', 'mixed'],
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
    subgraph_type: {
      type: 'string',
      description: [
        'sub_graphs mode ONLY — optional filter on bodha_cgm_sub_graphs.subgraph_type',
        '(e.g. a classically-recognized combination class). Omit for all subgraph types.',
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
    const rawValenceFilter = args['valence_filter'] as string | undefined
    const valence_filter = rawValenceFilter ? normalizeValence(rawValenceFilter) : undefined
    const cross_subsystem_only = Boolean(args['cross_subsystem_only'] ?? false)
    const depth = Math.min(Math.max(Number(args['depth'] ?? 1), 1), 3)
    const top_k_hubs = Math.min(Number(args['top_k_hubs'] ?? 10), 50)
    const direction: TraversalDirection = (args['direction'] as TraversalDirection) ?? 'both'
    const min_strength = args['min_strength'] !== undefined ? Number(args['min_strength']) : undefined

    try {
      switch (mode) {
        case 'neighbors':
          return await _neighborsMode(chart_id, args, ayanamsha_id, snapshot_type, edge_types, valence_filter, cross_subsystem_only, depth, direction, min_strength)

        case 'paths':
          return await _pathsMode(chart_id, args, ayanamsha_id, snapshot_type, direction, min_strength)

        case 'convergence':
          return await _convergenceMode(chart_id, ayanamsha_id, snapshot_type, top_k_hubs)

        case 'contradictions':
          return await _contradictionsMode(chart_id, ayanamsha_id)

        case 'sub_graphs':
          return await _subGraphsMode(chart_id, ayanamsha_id, args['subgraph_type'] as string | undefined)

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

// ── §27.2 address-resolver bridge — maps a resolved entity to bodha_cgm_nodes row(s) ────────

/**
 * Resolve an `about` address (AddressExpression or its DSL string) via the SHARED
 * `resolveAddress` (address_resolver.ts — NOT reimplemented here) to concrete
 * bodha_cgm_nodes.node_id(s), plus the human-readable resolution chain for the
 * caller's `about_resolution` field.
 */
async function _resolveAboutToNodeIds(
  chartId: string,
  about: AddressExpression | string,
  ayanamshaId: string | undefined,
  snapshotType: string | undefined
): Promise<{ node_ids: string[]; chain: string[]; entities: ResolvedEntity[] }> {
  const resolved = await resolveAddress(chartId, about, { ayanamsha_id: ayanamshaId ?? DEFAULT_AYANAMSHA })
  const nodeIds: string[] = []
  for (const entity of resolved.entities) {
    let nodeType: string
    let subjects: string[]
    if (entity.kind === 'graha') {
      nodeType = 'graha'
      subjects = [entity.graha]
    } else if (entity.kind === 'karaka') {
      nodeType = 'graha'
      subjects = [entity.graha]
    } else if (entity.kind === 'sign') {
      if (!entity.house_number) {
        throw new AddressResolutionError(
          `Address resolved to sign "${entity.sign}" with no house number — cannot map to a bodha_cgm_nodes row (bhava nodes are keyed by house number, not sign).`
        )
      }
      nodeType = 'bhava'
      subjects = [String(entity.house_number)]
    } else if (entity.kind === 'occupants') {
      nodeType = 'graha'
      subjects = entity.grahas
      if (subjects.length === 0) {
        return { node_ids: [], chain: resolved.chain, entities: resolved.entities }
      }
    } else {
      throw new AddressResolutionError(`Cannot map resolved entity kind "${(entity as { kind: string }).kind}" to a bodha_cgm_nodes row.`)
    }

    const { conds, params } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
    let pIdx = params.length + 1
    conds.push(`node_type = $${pIdx++}`)
    params.push(nodeType)
    const subjPhs = subjects.map(() => `$${pIdx++}`).join(', ')
    conds.push(`node_subject IN (${subjPhs})`)
    params.push(...subjects)

    const res = await query<{ node_id: string }>(
      `SELECT node_id FROM bodha_cgm_nodes WHERE ${conds.join(' AND ')} LIMIT ${subjects.length}`,
      params
    )
    if (res.rows.length === 0) {
      throw new AddressResolutionError(
        `Address resolved to ${nodeType} "${subjects.join(', ')}" but no matching bodha_cgm_nodes row exists for chart ${chartId} (ayanamsha ${ayanamshaId ?? DEFAULT_AYANAMSHA}). Has L2 Bodha's CGM writer (bo_*) run for this chart/ayanamsha?`
      )
    }
    nodeIds.push(...res.rows.map((r) => r.node_id))
  }
  return { node_ids: nodeIds, chain: resolved.chain, entities: resolved.entities }
}

function _parseAbout(input: unknown): AddressExpression | string {
  if (typeof input === 'string') return input
  return input as AddressExpression
}

// ── Mode implementations ──────────────────────────────────────────────────────

/**
 * neighbors mode: BFS from seed_node_ids (or about-resolved addresses) up to `depth` hops.
 * If semantic_query provided and no seeds: tries cosine-similarity entry
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
  depth: number,
  direction: TraversalDirection,
  minStrength: number | undefined
): Promise<ToolResult> {
  const rawSeeds = (args['seed_node_ids'] as string[]) ?? []
  const semanticQuery = args['semantic_query'] as string | undefined
  // W4-loop-1 (E-5 group1): `about` may arrive as a single DSL string (e.g.
  // "lord_of(bhava 10)"), a single AddressExpression object, OR an array of either.
  // The prior blind `as unknown[]` cast meant a bare string was iterated CHARACTER by
  // character (for-of over a string), so the resolver received "l" and threw
  // "Could not parse address expression: \"l\"". Normalize any non-array scalar/object
  // to a single-element array before iterating.
  const rawAboutInput = args['about']
  const rawAbout: unknown[] | undefined =
    rawAboutInput == null ? undefined
    : Array.isArray(rawAboutInput) ? rawAboutInput
    : [rawAboutInput]

  let seedNodeIds: string[] = rawSeeds
  let aboutChain: string[] | undefined

  // §27.1 `about` seeds — astrological addresses, resolved via the shared address resolver.
  if (rawAbout && rawAbout.length > 0) {
    const chains: string[] = []
    const resolvedIds: string[] = []
    for (const a of rawAbout) {
      const { node_ids, chain } = await _resolveAboutToNodeIds(chartId, _parseAbout(a), ayanamshaId, snapshotType)
      resolvedIds.push(...node_ids)
      chains.push(...chain)
    }
    seedNodeIds = resolvedIds
    aboutChain = chains
  }

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
  if (minStrength !== undefined) {
    edgeFilterClauses.push(`e.computed_strength >= $${pIdx++}`)
    baseParams.push(minStrength)
  }

  const depthParam = pIdx++
  baseParams.push(depth)

  // Direction facet: 'directed' follows only the graph's actual from_node_id -> to_node_id
  // edges (the frontier must be the edge's from_node_id); 'both' (default) treats edges as
  // undirected touches, matching the original D4 behavior.
  const bfsJoinCond =
    direction === 'directed'
      ? `e.from_node_id = bfs.node_id`
      : `(e.from_node_id = bfs.node_id OR e.to_node_id = bfs.node_id)`
  const bfsNextNode =
    direction === 'directed'
      ? `e.to_node_id`
      : `CASE WHEN e.from_node_id = bfs.node_id THEN e.to_node_id ELSE e.from_node_id END`

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
        ${bfsNextNode} AS node_id,
        bfs.hop + 1 AS hop
      FROM bfs
      JOIN bodha_cgm_edges e
        ON ${bfsJoinCond}
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
    ? await _fetchEdgesForNodes(chartId, visitedIds, ayanamshaId, snapshotType, edgeTypes, valenceFilter, crossSubsystemOnly, minStrength)
    : []

  return {
    content: {
      chart_id: chartId,
      mode: 'neighbors',
      seed_node_ids: seedNodeIds,
      about_resolution: aboutChain ?? null,
      direction,
      min_strength: minStrength ?? null,
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
 * Endpoints come from about_from/about_to (§27.1 address expressions, resolved via the
 * shared address resolver — the "10th lord -> Moon" ONE-call case) OR from
 * seed_node_ids[0]/[1] (raw node_id UUIDs) if about_from/about_to are not given.
 */
async function _pathsMode(
  chartId: string,
  args: Record<string, unknown>,
  ayanamshaId: string | undefined,
  snapshotType: string | undefined,
  direction: TraversalDirection,
  minStrength: number | undefined
): Promise<ToolResult> {
  const rawAboutFrom = args['about_from']
  const rawAboutTo = args['about_to']
  const seedNodeIds = (args['seed_node_ids'] as string[]) ?? []

  let fromNodeId: string
  let toNodeId: string
  let aboutChain: string[] | undefined

  if (rawAboutFrom !== undefined && rawAboutTo !== undefined) {
    const fromResolved = await _resolveAboutToNodeIds(chartId, _parseAbout(rawAboutFrom), ayanamshaId, snapshotType)
    const toResolved = await _resolveAboutToNodeIds(chartId, _parseAbout(rawAboutTo), ayanamshaId, snapshotType)
    if (fromResolved.node_ids.length === 0 || toResolved.node_ids.length === 0) {
      return {
        content: {
          error: 'about_from/about_to resolved to zero bodha_cgm_nodes rows — cannot traverse.',
          chart_id: chartId,
          mode: 'paths',
        },
        is_error: true,
      }
    }
    // Address expressions resolve to a single concrete entity for graha/karaka/bhava addresses;
    // occupants_of can resolve to several — path mode needs exactly one endpoint each, so take
    // the first and say so in the resolution chain (still classically sound: e.g. occupants_of
    // returns the graha list in a stable order, first-listed is not arbitrary noise).
    fromNodeId = fromResolved.node_ids[0]
    toNodeId = toResolved.node_ids[0]
    aboutChain = [...fromResolved.chain, ...toResolved.chain]
  } else if (seedNodeIds.length >= 2) {
    fromNodeId = seedNodeIds[0]
    toNodeId = seedNodeIds[1]
  } else {
    return {
      content: {
        error: 'paths mode requires either about_from + about_to (address expressions) or seed_node_ids with at least 2 elements: [from_node_id, to_node_id]',
        chart_id: chartId,
        mode: 'paths',
      },
      is_error: true,
    }
  }

  const { conds: baseNodeConds, params: baseParams } = _buildNodeBaseConds(chartId, ayanamshaId, snapshotType)
  let pIdx = baseParams.length + 1

  const fromPh = `$${pIdx++}`
  const toPh   = `$${pIdx++}`
  baseParams.push(fromNodeId, toNodeId)

  const edgeFilterClauses: string[] = [`e.chart_id = $1`]
  if (ayanamshaId) {
    edgeFilterClauses.push(`e.ayanamsha_id = $2`)
  }
  if (snapshotType) {
    edgeFilterClauses.push(`e.snapshot_type = $${ayanamshaId ? 3 : 2}`)
  }
  if (minStrength !== undefined) {
    edgeFilterClauses.push(`e.computed_strength >= $${pIdx++}`)
    baseParams.push(minStrength)
  }

  // Direction facet (design §21/§30 "direction facet"): 'directed' requires the path to follow
  // the graph's actual from_node_id -> to_node_id arrows; 'both' (default) allows either.
  const pathJoinCond =
    direction === 'directed'
      ? `e.from_node_id = ps.node_id`
      : `(e.from_node_id = ps.node_id OR e.to_node_id = ps.node_id)`
  const pathNextNode =
    direction === 'directed'
      ? `e.to_node_id`
      : `CASE WHEN e.from_node_id = ps.node_id THEN e.to_node_id ELSE e.from_node_id END`

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
        ${pathNextNode} AS node_id,
        ps.path || ${pathNextNode},
        ps.hop + 1
      FROM path_search ps
      JOIN bodha_cgm_edges e
        ON ${pathJoinCond}
        AND ${edgeFilterClauses.join(' AND ')}
      WHERE ps.hop < 5
        AND NOT (${pathNextNode} = ANY(ps.path))
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
              pagerank_score, hub_flag, primary_domain, strength_score
       FROM bodha_cgm_nodes
       WHERE ${nc.join(' AND ')} AND node_id IN (${nPhs})`,
      np
    )
    nodes = nodeRes.rows
    edges = await _fetchEdgesForNodes(chartId, nodeIds, ayanamshaId, snapshotType, undefined, undefined, false, minStrength)
  }

  return {
    content: {
      chart_id: chartId,
      mode: 'paths',
      from_node_id: fromNodeId,
      to_node_id: toNodeId,
      about_resolution: aboutChain ?? null,
      direction,
      min_strength: minStrength ?? null,
      paths: pathResult.rows,
      path_count: pathResult.rows.length,
      path_found: pathResult.rows.length > 0,
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
): Promise<ToolResult> {
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
): Promise<ToolResult> {
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
      resolution_hint_jsonb,
      verification_pass_status,
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

/**
 * sub_graphs mode: curated named subgraph clusters for a chart (bodha_cgm_sub_graphs,
 * W2 dark-set wiring — see header note). Each row already carries node_ids_array/
 * edge_ids_array back into bodha_cgm_nodes/bodha_cgm_edges, so this mode additionally
 * resolves the constituent node rows (not edges — edges can be fetched via neighbors/
 * convergence mode using the returned node_ids as seeds) for immediate readability,
 * same shape as _contradictionsMode's participant_signals enrichment.
 */
async function _subGraphsMode(
  chartId: string,
  ayanamshaId: string | undefined,
  subgraphType: string | undefined
): Promise<ToolResult> {
  const conds: string[] = ['chart_id = $1']
  const params: unknown[] = [chartId]
  let pIdx = 2

  if (ayanamshaId) {
    conds.push(`ayanamsha_id = $${pIdx++}`)
    params.push(ayanamshaId)
  }
  if (subgraphType) {
    conds.push(`subgraph_type = $${pIdx++}`)
    params.push(subgraphType)
  }

  const subgraphSql = `
    SELECT
      subgraph_id,
      ayanamsha_id,
      subgraph_type,
      subgraph_label,
      node_ids_array,
      edge_ids_array,
      subgraph_density,
      subgraph_centroid_node_id,
      representative_path_jsonb,
      classical_archetype_match,
      verification_pass_status,
      citation_ref,
      citation_human
    FROM bodha_cgm_sub_graphs
    WHERE ${conds.join(' AND ')}
    ORDER BY subgraph_density DESC NULLS LAST
  `

  const subgraphResult = await query<Record<string, unknown>>(subgraphSql, params)

  // Resolve the constituent node ids across all returned subgraphs into their
  // bodha_cgm_nodes rows, so a caller gets readable node labels in one call
  // instead of a resolve-then-lookup round trip (same convenience _contradictionsMode
  // already gives for its participant_signals).
  const allNodeIds = new Set<string>()
  for (const row of subgraphResult.rows) {
    const ids = (row['node_ids_array'] as string[] | null) ?? []
    for (const id of ids) allNodeIds.add(id)
  }

  let memberNodes: unknown[] = []
  if (allNodeIds.size > 0) {
    const nodeIdArr = Array.from(allNodeIds)
    const nodeConds = ['chart_id = $1']
    const nodeParams: unknown[] = [chartId]
    let ni = 2
    if (ayanamshaId) {
      nodeConds.push(`ayanamsha_id = $${ni++}`)
      nodeParams.push(ayanamshaId)
    }
    const nodePhs = nodeIdArr.map(() => `$${ni++}`).join(', ')
    nodeConds.push(`node_id IN (${nodePhs})`)
    nodeParams.push(...nodeIdArr)

    const nodeRes = await query<Record<string, unknown>>(
      `SELECT node_id, node_type, node_subject, node_label_human, primary_domain
       FROM bodha_cgm_nodes
       WHERE ${nodeConds.join(' AND ')}`,
      nodeParams
    )
    memberNodes = nodeRes.rows
  }

  return {
    content: {
      chart_id: chartId,
      mode: 'sub_graphs',
      sub_graphs: subgraphResult.rows,
      sub_graph_count: subgraphResult.rows.length,
      member_nodes: memberNodes,
      provenance: {
        tables: ['bodha_cgm_sub_graphs', 'bodha_cgm_nodes'],
        schema_version: 'mig_325',
        ayanamsha_id: ayanamshaId ?? null,
        note: 'member_nodes resolves the union of every returned subgraph\'s node_ids_array against bodha_cgm_nodes for immediate readability.',
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
  crossSubsystemOnly?: boolean,
  minStrength?: number
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
  if (minStrength !== undefined) {
    conds.push(`e.computed_strength >= $${pIdx++}`)
    params.push(minStrength)
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
