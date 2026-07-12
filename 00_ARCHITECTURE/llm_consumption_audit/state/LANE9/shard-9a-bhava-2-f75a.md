# Lane 9a STRUCTURAL shard — node_key `bhava:2:f75a`

- node_id: `c3726751-91c7-4d68-892a-9d690711d23d`
- node_type: `bhava`  node_subject: `2`
- chart_id: `1c826d5a-41cb-4450-b4dc-59d440e5f75a`
- axis: STRUCTURAL only (consumption axis = KNOWN fixed LCA-1; leverage axis = KNOWN fixed LCA-2 — not re-probed)

## Verbatim SQL — neighborhood recipe

```sql
WITH nbr AS (
  SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array
  FROM bodha_cgm_edges e
  WHERE e.chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a'
    AND (e.from_node_id='c3726751-91c7-4d68-892a-9d690711d23d' OR e.to_node_id='c3726751-91c7-4d68-892a-9d690711d23d'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, ...;
```

## Verbatim result

```
edge_count = 0
edge_types = NULL
cited      = 0/0
msr_backed = 0/0
dasha_edges= 0
neighbor node_types = (none — 0 edges)
```

Corroborating chart-level queries (verbatim):
```
bodha_cgm_edges  WHERE chart_id=…f75a  ->  523 edges
bodha_cgm_nodes  WHERE chart_id=…f75a  ->  140 nodes
node c3726751-91c7-4d68-892a-9d690711d23d exists in bodha_cgm_nodes  ->  1 (chart …f75a, node_type=bhava, node_subject=2)
edges touching c3726751-91c7-4d68-892a-9d690711d23d (any chart)      ->  0
```

Node-type participation census (verbatim, this chart):
```
node_type | nodes_of_type | nodes_with_edges
bhava     | 60            | 0
domain    | 35            | 15
graha     | 45            | 45
```
No node_type ILIKE '%yoga%' exists (0 rows) — yogas are not first-class graph nodes.

## Grades (STRUCTURAL axis)

| gate | value | evidence |
|---|---|---|
| edge_count | 0 | recipe COUNT(*) = 0 |
| reaches_dispositor | false | no edge_type='dispositor' (no edges at all) |
| reaches_bhava_lordship | false | bhava's lord graha not reached — 0 edges to any graha node |
| reaches_yoga | false | no yoga node type in graph AND 0 edges |
| reaches_temporal_hook | false | 0 edges with active_dasha_periods_jsonb / temporal edge_type |
| citation_ratio | 0/0 | recipe cited = 0/0 |
| msr_backed_ratio | 0/0 | recipe msr_backed = 0/0 |

**structural_verdict: ISOLATED** (0 edges — reaches 0 of 4 grade dimensions).

## Findings

### F1 — Bhava node fully ISOLATED from CGM edge graph (systemic)
- summary: bhava `2` exists as a first-class CGM node but participates in ZERO edges; no dispositor / lordship / yoga / temporal relationship is reachable from or to it via graph walk.
- failure_class: 1 (UNREACHABLE) — node exists in bodha_cgm_nodes, no edge serves any of its relationships.
- severity: high — bhava is the core interpretive frame; a graph-walking consumer starting at or targeting any bhava returns an empty neighborhood.
- evidence: recipe edge_count=0; census shows bhava 60 nodes / 0 with edges vs graha 45/45; domain 15/35.
- reproducible call: mcp__postgres__query with the recipe SQL above (verbatim).
- suspected layer: L-writer (CGM graph builder — bo_karanajala/bo_sangati edge emission omits bhava endpoints) / data plane.
- dedupe: relates to LCA structural axis; distinct from LCA-1 (consumption) and LCA-2 (leverage) which are KNOWN-fixed. New structural row.

### F2 — Yoga not a first-class graph node (systemic, structural)
- summary: bodha_cgm_nodes holds only node_type ∈ {bhava, domain, graha}; no yoga node exists, so reaches_yoga is structurally unsatisfiable for every node.
- failure_class: 4 (EMPTY SHELL) — the graph advertises structural completeness but the yoga relationship stage has no node/edge representation.
- severity: medium — yoga membership is a mandatory depth facet (Charter §1 depth axis) yet absent from the graph substrate.
- evidence: SELECT DISTINCT node_type WHERE node_type ILIKE '%yoga%' -> 0 rows; only bhava/domain/graha present.
- suspected layer: architecture (graph schema omits yoga as first-class node).
- dedupe: brief §3 pre-declares this as an expected structural finding; logged per node for coverage.
