# Shard 9a — bhava-8 (chart 71aa)

node_key: bhava:8:71aa
node_id: 9578f0ee-d352-4cd4-9380-c749c80a7f46
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## STRUCTURAL axis only (consumption=KNOWN LCA-1 dead; leverage=KNOWN LCA-2 broken — not re-probed)

### Recipe SQL (verbatim)
```sql
WITH nbr AS (SELECT ... FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND (e.from_node_id='9578f0ee-d352-4cd4-9380-c749c80a7f46' OR e.to_node_id='9578f0ee-d352-4cd4-9380-c749c80a7f46'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, ...;
```
### Verbatim result
```
edge_count=0  edge_types=null  cited=null  msr_backed=null  temporal_populated=null  dispositor_edges=null
```
Neighbor node types query → [] (empty). Node existence confirmed: (bhava, subject "8").

## Grades
- edge_count: 0
- reaches_dispositor: false
- reaches_bhava_lordship: false (0 edges — lord graha not reached)
- reaches_yoga: false (no node_type='yoga' in graph)
- reaches_temporal_hook: false
- citation_ratio: n/a  · msr_backed_ratio: n/a
- structural_verdict: ISOLATED

## Findings
1. [class 1 UNREACHABLE / class 4 EMPTY SHELL, HIGH] Bhava-8 node isolated: 0 edges. The 8th house (longevity, mrityu, transformation) node reaches nothing — no occupants, no lord, no aspects. Part of the chart-wide pattern: 60 bhava nodes, 0 edges total. Evidence: edge_count=0.
2. [class 4 EMPTY SHELL, MEDIUM] reaches_yoga structurally impossible — no yoga node type in bodha_cgm_nodes.
