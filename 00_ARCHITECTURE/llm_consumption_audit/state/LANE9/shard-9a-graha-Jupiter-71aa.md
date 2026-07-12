# Shard 9a — graha-Jupiter (chart 71aa)

node_key: graha:Jupiter:71aa
node_id: ba83069a-bb93-4d29-a2f5-9db50840c251
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## STRUCTURAL axis only (consumption=KNOWN LCA-1 dead; leverage=KNOWN LCA-2 broken — not re-probed)

### Recipe SQL (verbatim)
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.citation_ref,e.underlying_msr_signal_ids_array,e.active_dasha_periods_jsonb
  FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND (e.from_node_id='ba83069a-bb93-4d29-a2f5-9db50840c251' OR e.to_node_id='ba83069a-bb93-4d29-a2f5-9db50840c251'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types, ...;
```
### Verbatim result
```
edge_count=23  edge_types=argala,aspect,dispositor  cited=23/23  msr_backed=16/23  temporal_populated=0  dispositor_edges=1
```
Neighbor node types query → [{"node_type":"graha"}]  (ONLY graha neighbors — no bhava, no domain, no yoga).

## Grades
- edge_count: 23
- reaches_dispositor: true (dispositor_edges=1; edge_type 'dispositor' present)
- reaches_bhava_lordship: false (neighbors are graha-only; graph has NO graha->bhava lordship edges)
- reaches_yoga: false (no node_type='yoga' in graph)
- reaches_temporal_hook: false (active_dasha_periods_jsonb populated on 0/23 edges; no temporal edge_type — edge_types are argala/aspect/dispositor)
- citation_ratio: 23/23
- msr_backed_ratio: 16/23
- structural_verdict: THIN (reaches exactly 1 of 4 — dispositor only)

## Findings
1. [class 4 EMPTY SHELL, HIGH] Graha nodes reach ONLY other grahas. Jupiter's 23-edge neighborhood spans argala/aspect/dispositor to graha nodes exclusively — no edge reaches any bhava node (graha->bhava lordship is not modelled). Combined with all 60 bhava nodes being edge-isolated, the CGM cannot answer "which bhavas does Jupiter own/occupy/aspect" via graph traversal. Evidence: neighbor node types = graha only; reaches_bhava_lordship=false.
2. [class 4 EMPTY SHELL, MEDIUM] No temporal hook on any edge: active_dasha_periods_jsonb populated on 0/23 edges and no temporal edge_type — the graph carries no MD/AD/PD activation dimension (corroborates G-6: no temporal/multi-hop chain integration). Evidence: temporal_populated=0.
3. [class 4 EMPTY SHELL, MEDIUM] reaches_yoga structurally impossible — no yoga node type; Jupiter's yoga memberships cannot be reached as graph neighbors.
4. [class 6 UNUSABLE FORM, LOW] msr_backed 16/23: 7 of 23 edges carry no underlying_msr_signal_ids_array, though all 23 carry a citation_ref (cited 23/23) — partial derivation-ledger backing.
