# Shard 9a STRUCTURAL — node_key `graha:Mercury:f75a`

- node_id: `0f82de96-86e3-41b8-ad64-56c629b44a04`
- chart_id: `1c826d5a-41cb-4450-b4dc-59d440e5f75a`

## Query 1 — edge recipe
Result (verbatim): edge_count=`23` · edge_types=`argala,aspect,dispositor` · cited=`23/23` · msr_backed=`16/23`

## Query 2 — neighbor node types + temporal hook
Result (verbatim): neighbor_types=`graha` · temporal=`0/23`

## Grades
- reaches_dispositor: **true**
- reaches_bhava_lordship: **false**
- reaches_yoga: **false**
- reaches_temporal_hook: **false**
- citation_ratio: `23/23`
- msr_backed_ratio: `16/23`
- structural_verdict: **THIN** (1 of 4)

Note: this directly instantiates the plan's own probe question ("does Mercury's node reach its dispositor chain, its yogas, its bhava lords, its temporal hooks?"). Answer: dispositor YES; yogas NO; bhava lords NO; temporal hooks NO.

## Findings
- F1 (class 1 UNREACHABLE, high): Mercury reaches no `bhava` node; bhava-lordship unreachable. Evidence: neighbor_types=`graha` only over 23 edges.
- F2 (class 1 UNREACHABLE, high): Mercury reaches no yoga; yogas not first-class nodes.
- F3 (class 4 EMPTY SHELL, high): temporal hooks absent — `0/23` edges carry active_dasha_periods_jsonb.
