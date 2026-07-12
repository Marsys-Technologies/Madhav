# Shard 9a — graha-Ketu (chart 71aa)

node_key: graha:Ketu:71aa
node_id: 2d25a5ea-5edc-4720-a212-566c2c54f1d7
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## STRUCTURAL axis only (consumption=KNOWN LCA-1 dead; leverage=KNOWN LCA-2 broken — not re-probed)

### Recipe SQL (verbatim)
```sql
WITH nbr AS (SELECT ... FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND (e.from_node_id='2d25a5ea-5edc-4720-a212-566c2c54f1d7' OR e.to_node_id='2d25a5ea-5edc-4720-a212-566c2c54f1d7'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, ...;
```
### Verbatim result
```
edge_count=24  edge_types=argala,aspect,dispositor  cited=24/24  msr_backed=16/24  temporal_populated=0  dispositor_edges=1
```
Neighbor node types query → [{"node_type":"graha"}]  (graha-only).

## Grades
- edge_count: 24
- reaches_dispositor: true (dispositor_edges=1)
- reaches_bhava_lordship: false (graha-only neighbors; no graha->bhava edges)
- reaches_yoga: false (no yoga node type)
- reaches_temporal_hook: false (0/24 edges temporal-populated; no temporal edge_type)
- citation_ratio: 24/24
- msr_backed_ratio: 16/24
- structural_verdict: THIN (reaches 1 of 4 — dispositor only)

## Findings
1. [class 4 EMPTY SHELL, HIGH] Ketu's 24-edge neighborhood reaches grahas only — no bhava, no yoga, no temporal. Same graha-only topology as Jupiter/Mars. Evidence: neighbor node types = graha only.
2. [class 4 EMPTY SHELL, MEDIUM] No temporal hook: 0/24 edges populate active_dasha_periods_jsonb. Evidence: temporal_populated=0.
3. [class 4 EMPTY SHELL, MEDIUM] reaches_yoga impossible — no yoga node type. Note: for a chhaya-graha (nodal) Ketu, yoga/dosha membership (e.g. Ketu-driven combinations) is exactly the context most needed and it is unreachable via graph.
4. [class 6 UNUSABLE FORM, LOW] msr_backed 16/24: 8 edges lack MSR-signal backing though all cited (24/24).
