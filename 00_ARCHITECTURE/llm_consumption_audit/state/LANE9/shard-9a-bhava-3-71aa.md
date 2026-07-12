# Lane 9a STRUCTURAL shard — bhava:3:71aa

node_key: bhava:3:71aa
node_id: e103d91a-502d-46af-bff4-65226e9e701b
node_type: bhava   node_subject: 3
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## Recipe SQL (verbatim, uuid-cast)
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array
  FROM bodha_cgm_edges e
  WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
    AND (e.from_node_id='e103d91a-502d-46af-bff4-65226e9e701b'::uuid OR e.to_node_id='e103d91a-502d-46af-bff4-65226e9e701b'::uuid))
SELECT (SELECT COUNT(*) FROM nbr) edge_count,
  (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```

## Verbatim result
edge_count = 0 | edge_types = NULL | cited = NULL (0/0) | msr_backed = NULL (0/0)

Neighbor node_types query returned: (empty set — node participates in no edge).

## Corroborating systemic query (verbatim result)
Per-node-type edge participation for this chart:
- bhava:  total_nodes=60, nodes_with_edges=0
- domain: total_nodes=35, nodes_with_edges=15
- graha:  total_nodes=45, nodes_with_edges=45

Node existence CONFIRMED in bodha_cgm_nodes (node_type='bhava', node_subject='3').

## Structural grades (brief §3 structural axis)
- reaches_dispositor:       false (0 edges)
- reaches_bhava_lordship:   false (no edge to lord graha; node is isolated)
- reaches_yoga:             false (no yoga edge; also bodha_cgm_nodes has NO node_type='yoga' — structural finding class per brief)
- reaches_temporal_hook:    false (no temporal/dasha edge)
- citation_ratio:           0/0 (no edges to cite)
- msr_backed_ratio:         0/0 (no edges to back)
- edge_count:               0
- structural_verdict:       ISOLATED

## Findings
[F1] class=1 UNREACHABLE (severity=high). Bhava-3 node is fully isolated: 0 edges.
A consuming LLM traversing from this bhava node reaches NO occupants, NO lord graha,
NO aspects, NO arudha, NO dispositor, NO yoga, NO temporal hook. The protocol's bhava
completeness requirement (occupants / lord / aspects-received / arudha, Appendix B §B-VI.40)
is categorically unmet. Evidence: edge_count=0; verbatim recipe result above.
Systemic: ALL 60 bhava nodes have 0 edges (0/60) while grahas are fully wired (45/45),
so this is a whole-stratum EMPTY-SHELL (class 4) condition, not a per-node gap — the bhava
node layer was registered in bodha_cgm_nodes but never wired into bodha_cgm_edges.

## Completion marker
STATUS: COMPLETE
