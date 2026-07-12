# Shard 9a — bhava-7 (chart 71aa)

node_key: bhava:7:71aa
node_id: 567c4a83-a9ea-4142-a0d5-6cab846a4fe8
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## STRUCTURAL axis (only axis run this shard; consumption=KNOWN LCA-1 dead, leverage=KNOWN LCA-2 broken — not re-probed)

### Recipe SQL (verbatim)
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array,e.active_dasha_periods_jsonb
  FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND (e.from_node_id='567c4a83-a9ea-4142-a0d5-6cab846a4fe8' OR e.to_node_id='567c4a83-a9ea-4142-a0d5-6cab846a4fe8'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, ... dispositor_edges ...;
```
### Verbatim result
```
edge_count=0  edge_types=null  cited=null  msr_backed=null  temporal_populated=null  dispositor_edges=null
```
Neighbor node types query → [] (empty; no neighbors).

Corroborating chart-wide query (verbatim result):
```
node_type=bhava  nodes=60  total_edges_touching=0
node_type=domain nodes=35  total_edges_touching=15
node_type=graha  nodes=45  total_edges_touching=1053
```
Node existence confirmed: node_id resolves to (bhava, subject "7") in bodha_cgm_nodes — the node EXISTS but is edge-isolated.

## Grades
- edge_count: 0
- reaches_dispositor: false
- reaches_bhava_lordship: false (bhava's lord graha NOT reached — 0 edges)
- reaches_yoga: false (bodha_cgm_nodes has NO node_type='yoga' — yogas are not first-class graph nodes)
- reaches_temporal_hook: false
- citation_ratio: n/a (0 edges)
- msr_backed_ratio: n/a (0 edges)
- structural_verdict: ISOLATED

## Findings
1. [class 1 UNREACHABLE / class 4 EMPTY SHELL, HIGH] Bhava-7 node is fully isolated: 0 edges. A consuming LLM cannot traverse from the 7th-house node to its occupants, lord, aspects received, or arudha — the entire structural neighborhood a bhava synthesis requires (brief §3.1) is absent. This is not a per-node accident: chart-wide, ALL 60 bhava nodes have total_edges_touching=0 while grahas hold 1053. The CGM models graha-graha relations only; bhava nodes are parked orphans. Evidence: edge_count=0; chart-wide bhava total_edges_touching=0.
2. [class 4 EMPTY SHELL, MEDIUM] reaches_yoga structurally impossible — no node_type='yoga' exists in bodha_cgm_nodes (distinct node_types = domain, graha, bhava). Yogas are not first-class graph nodes for any node in this chart.
