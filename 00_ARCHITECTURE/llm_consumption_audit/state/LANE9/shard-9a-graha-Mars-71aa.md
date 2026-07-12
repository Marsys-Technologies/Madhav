# Shard 9a — graha-Mars (chart 71aa)

node_key: graha:Mars:71aa
node_id: 0b45e52d-3675-446e-86bd-b3fe46c640e9
chart_id: 482012f1-710e-4a25-994a-93821f5871aa

## STRUCTURAL axis only (consumption=KNOWN LCA-1 dead; leverage=KNOWN LCA-2 broken — not re-probed)

### Recipe SQL (verbatim)
```sql
WITH nbr AS (SELECT ... FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND (e.from_node_id='0b45e52d-3675-446e-86bd-b3fe46c640e9' OR e.to_node_id='0b45e52d-3675-446e-86bd-b3fe46c640e9'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, ...;
```
### Verbatim result
```
edge_count=23  edge_types=argala,aspect,dispositor  cited=23/23  msr_backed=16/23  temporal_populated=0  dispositor_edges=2
```
Neighbor node types query → [{"node_type":"graha"}]  (graha-only).

## Grades
- edge_count: 23
- reaches_dispositor: true (dispositor_edges=2)
- reaches_bhava_lordship: false (graha-only neighbors)
- reaches_yoga: false (no yoga node type)
- reaches_temporal_hook: false (0/23 temporal-populated; no temporal edge_type)
- citation_ratio: 23/23
- msr_backed_ratio: 16/23
- structural_verdict: THIN (reaches 1 of 4 — dispositor only)

## Findings
1. [class 4 EMPTY SHELL, HIGH] Mars's 23-edge neighborhood reaches grahas only; no bhava-lordship edges despite Mars owning 2 bhavas from Aries lagna (1st & 8th). The graph cannot express Mars->bhava ownership. Evidence: neighbor node types = graha only.
2. [class 4 EMPTY SHELL, MEDIUM] No temporal hook: 0/23 edges populate active_dasha_periods_jsonb. Evidence: temporal_populated=0.
3. [class 4 EMPTY SHELL, MEDIUM] reaches_yoga impossible — no yoga node type in graph.
4. [class 6 UNUSABLE FORM, LOW] msr_backed 16/23: 7 edges lack MSR backing though all cited (23/23).
