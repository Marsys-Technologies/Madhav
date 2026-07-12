# Shard 9a — bhava-9 (chart 71aa)

node_key: bhava:9:71aa
node_id: a2120036-c6ae-4084-944b-3714e0ffc5fe
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## STRUCTURAL axis only (consumption=KNOWN LCA-1 dead; leverage=KNOWN LCA-2 broken — not re-probed)

### Recipe SQL (verbatim)
```sql
WITH nbr AS (SELECT ... FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND (e.from_node_id='a2120036-c6ae-4084-944b-3714e0ffc5fe' OR e.to_node_id='a2120036-c6ae-4084-944b-3714e0ffc5fe'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, ...;
```
### Verbatim result
```
edge_count=0  edge_types=null  cited=null  msr_backed=null  temporal_populated=null  dispositor_edges=null
```
Neighbor node types query → [] (empty). Node existence confirmed: (bhava, subject "9").

## Grades
- edge_count: 0
- reaches_dispositor: false
- reaches_bhava_lordship: false (0 edges)
- reaches_yoga: false (no yoga node type)
- reaches_temporal_hook: false
- citation_ratio: n/a  · msr_backed_ratio: n/a
- structural_verdict: ISOLATED

## Findings
1. [class 1 UNREACHABLE / class 4 EMPTY SHELL, HIGH] Bhava-9 node isolated: 0 edges. The 9th house (dharma, fortune, father, guru) node reaches nothing. Chart-wide pattern: 60 bhava nodes, 0 edges. Evidence: edge_count=0; chart-wide bhava total_edges_touching=0.
2. [class 4 EMPTY SHELL, MEDIUM] reaches_yoga structurally impossible — no yoga node type in graph.
