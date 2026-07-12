# Shard 9a STRUCTURAL — node_key `graha:Moon:f75a`

- node_id: `5b27c22b-cdea-4809-a5c2-4baed6c938ae`
- chart_id: `1c826d5a-41cb-4450-b4dc-59d440e5f75a`

## Query 1 — edge recipe
Result (verbatim): edge_count=`23` · edge_types=`argala,aspect,dispositor,dosha_domain` · cited=`23/23` · msr_backed=`19/23`

## Query 2 — neighbor node types + temporal hook
Result (verbatim): neighbor_types=`domain,graha` · temporal=`0/23`

## Grades
- reaches_dispositor: **true**
- reaches_bhava_lordship: **false** (neighbors are `graha` + `domain`; no `bhava` node)
- reaches_yoga: **false**
- reaches_temporal_hook: **false**
- citation_ratio: `23/23`
- msr_backed_ratio: `19/23`
- structural_verdict: **THIN** (1 of 4)

Note: Moon is the only sampled graha reaching a non-graha neighbor (`domain` via `dosha_domain` edge) — still not `bhava`, so bhava-lordship remains unreachable.

## Findings
- F1 (class 1 UNREACHABLE, high): Moon reaches no `bhava` node; bhava-lordship unreachable. Evidence: neighbor_types=`domain,graha` — no `bhava`.
- F2 (class 1 UNREACHABLE, high): Moon reaches no yoga; yogas not first-class nodes.
- F3 (class 4 EMPTY SHELL, high): temporal hooks absent — `0/23` edges carry active_dasha_periods_jsonb.
