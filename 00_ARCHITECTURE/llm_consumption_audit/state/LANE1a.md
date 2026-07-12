---
lane: "1a"
title: "Tool census — channel + synthesizability spread"
status: CURRENT
generated: 2026-07-12
source: llm_consumption_audit / WIRE state (lane A = 1a+4)
---

# LANE 1a — Tool Census: Channel Reachability + First-Contact Synthesizability

## Census totals

- **Tools probed:** 127

### By channel

| Channel | Count | Meaning |
|---|---|---|
| served-only-by-down-pipeline | 109 | Reachable *only* via `ask_madhav` full pipeline, which is broken per LCA-2. Not in the surgical whitelist. |
| reachable-surgical | 17 | In the surgical primitive whitelist; directly probeable. |
| dead | 1 | Neither surgical nor served by any live pipeline path (DEAD-19 / LCA-1 dispatch failure). |

### By first-contact synthesizability

| Grade | Count |
|---|---|
| not-probed | 109 |
| FAIL | 6 |
| PARTIAL | 5 |
| PASS | 7 |

The 109 not-probed tools are exactly the served-only-by-down-pipeline set: because the only path is the LCA-2-broken `ask_madhav` full pipeline, no payload is returned to grade, so synthesizability is **un-probeable on first contact**.

## Dominant failure mode

The census is overwhelmingly gated by a **single structural choke point**: the surgical whitelist admits only 17 reachable tools, and everything else (109 tools) is reachable only through `ask_madhav` — which is down (LCA-2). Every such tool returns:

```
HTTP 400 {"ok":false,"error":{"class":"validation",
  "message":"Tool not in surgical whitelist: <tool>",
  "remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are: ..."}}
```

This yields a wall of **failure class 1** (served-only-by-down-pipeline, whitelist rejection) findings — the bulk of the lane.

## Highest-value casualties (HIGH severity, class 1)

- **Domain assessors unreachable surgically** — `apex_career_assess`, `apex_health_assess`, `apex_marriage_assess`, `apex_wealth_assess` (the four highest-value per-domain verdict surfaces) are all full-pipeline-only. None of the four is surgically consultable.
- **Duplicate assessor family** — `assess_career` / `assess_health` / `assess_marriage` / `assess_wealth` parallel the `apex_*_assess` family: two tool families for the same four domains (INCONSISTENT / dedup smell, class-3 candidate); neither family reachable surgically.
- **B.11 Whole-Chart-Read entry blocked** — `bodha_chart_digest_get` (the natural first-contact whole-chart digest) is down-pipeline-only.
- **Self-description blocked** — `asset_registry_all`, `asset_registry_l0`, `catalog_assets_all`, `catalog_assets_l0`, `catalog_assets_list`: the system cannot enumerate its own asset inventory over the surgical channel (Charter §2.1 source-2 census blocked).
- **Bodha reader surfaces down-pipeline-only** — `bodha_discoveries_get`, `bodha_domain_reading_get`, `bodha_graph_subgraph_get`, `bodha_graph_traverse_get`, `bodha_quality_get`, `bodha_remedies_get`, `bodha_remedies_search`, `bodha_signals_get`.

## Namespace-divergence batch (class 1, HIGH)

A whole family of `ganita_*` / compute aliases is absent from the whitelist while a **functional twin under a parallel `query_*` name IS admitted** — a registry / MCP-contract coherence gap that yields 100% first-contact FAIL for the alias names:

| Excluded alias (down-pipeline only) | Whitelisted twin |
|---|---|
| `compute_natal_positions`, `ephemeris_cache_year`, `ganita_natal_positions_compute`, `ganita_positions_get` | `query_ephemeris` |
| `ganita_dasha_periods_get`, `ganita_dashas_get` | `query_dasha_periods` |
| `ganita_chart_facts_get` | `query_chart_facts` (itself defective per LCA-3) |
| `find_verses_about` | `read_classical_text` / `vector_search` |
| `ganita_condition_get` | *(no twin — condition/avastha surface has no surgical path at all)* |
| `ganita_nakshatra_get` | *(no direct twin — folds into `query_chart_facts` / `query_panchanga`)* |
| `chart_snapshot` | *(no whitelisted aggregate twin)* |

The whitelist enumerates `query_*` names only; none of the 11 assigned alias names are present.

## Dispatch-failure casualty (class 1, HIGH)

- `get_cgm_subgraph` **passes** the surgical whitelist but every call fails at dispatch — it fronts the DEAD-19 `cgm_graph_walk` (LCA-1); no payload is ever produced. This is the single tool counted in the `dead` channel bucket.

## Cross-lane notes

- `query_chart_facts` is the surgical substitute for `ganita_chart_facts_get`, but is itself **defective per LCA-3** — see LANE4 (dishonest receipts) and LANE3 (cross-path quantity divergence).
- The remediation string that accompanies every class-1 rejection points onward at `ask_madhav`, which is broken (LCA-2), and mis-advertises DEAD-19 tools as live — see the LANE4 class-5 finding on `bodha_chart_digest_get`.

## Bottom line

**~86% of the tool surface (109/127) is unreachable and un-gradeable on the surgical channel**, gated behind a broken full pipeline; 1 more (`get_cgm_subgraph`) is whitelisted-but-dead. Only 7 tools verified PASS on first contact. The whitelist is the single highest-leverage remediation surface.
</content>
</invoke>
