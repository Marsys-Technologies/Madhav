# shard-9b-yoga_label

**shard_id:** 9b-yoga_label
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'yoga_label'` → returned `[]` (no rows).
chart_facts denominator: 75 total.

## Verbatim results
- chart_facts rows: 75 (both charts)
- cell1 (consumed): **0 signals for both charts** (empty result set)
- cells 2–5: N/A

## 5-cell verdicts
1. Consumed by bo_laksana? **NO** — 75 chart_facts rows exist, 0 MSR signals resolve to `yoga_label`.
2–5: not applicable.

## design_correctness_verdict: NOT_CONSUMED
Funnel-narrowing / omission-from-MSR for a HIGH-value category.

## Findings
- **F1 (class 1 UNREACHABLE-by-omission-from-MSR):** yoga_label (75 chart_facts rows) produces zero bodha_msr_signals whose constituent_facts_array resolves to this category. Yogas are the single most chart-defining structure in Jyotish; if the named-yoga LABEL fact_category is not ingested, the human-readable yoga name may not reach any LLM consumer via MSR. CAVEAT (blind-shard limitation): MSR does contain `signal_type_class=yoga` signals sourced from OTHER fact_categories (e.g. a yoga-membership/participant category outside this 12-category shard) — so yoga PRESENCE may still be conveyed even though the `yoga_label` category specifically is not. The conductor must cross-check at merge whether yoga names/labels reach consumers through the yoga-typed signals; if the label text is only in `yoga_label` and that category is un-ingested, this is HIGH severity. Suspected layer: L-writer (bo_laksana ingestion selection). Severity: MED-HIGH (pending conductor cross-check of yoga-label reachability via other categories). Evidence: cell1 empty; chart_facts 75. Dedupe: funnel-narrowing / ingestion-omission (R-44 family); relates to whether yoga naming is findable.
