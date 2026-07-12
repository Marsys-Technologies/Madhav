# shard-9b-dosha_label  (R-42 anchor re-derivation)

**Shard id:** 9b-dosha_label
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
1. Standard 5-cell recipe on fact_category='dosha_label' → returned `[]` (ZERO rows).
2. Baseline: `SELECT count(*) FROM chart_facts WHERE fact_category='dosha_label' ...` → 110 / 110.
3. Collateral (R-42): counts over `signal_type_class='dosha'` signals and their constituent-fact resolvability.

## Verbatim results
- chart_facts baseline: 110 (Abhisek) / 110 (Abhinandan)
- cell1 signals resolving to dosha_label: **0 / 0** (query returned empty result set)
- Collateral: 220 `signal_type_class='dosha'` signals exist (both charts). Their constituent_facts_array: min_card=1, max_card=1, empty_attr=0 → every dosha signal cites exactly ONE fact_id.
- Distinct fact_ids cited across all 220 dosha signals: **10** (each reused 22×).
- Of those 10 cited fact_ids, **0 resolve to any chart_facts row** (`refs_resolving_to_chart_facts=0`). Sample cited id `e2b47b2c6d457725` → `SELECT ... FROM chart_facts WHERE fact_id='e2b47b2c6d457725'` returned empty.

## Cell verdicts
1. Consumed: **NO** — 110 dosha_label facts per chart, 0 MSR signals ingest them
2. Salience: n/a (not consumed)
3. Attribution: dosha signals ARE non-empty but cite 10 phantom fact_ids that resolve to nothing (broken referential integrity, violates §N.5 / B.3)
4. Domains: n/a
5. Emergence: dosha_label → 0 signals; the 220 dosha-class signals derive from a fabricated 10-fact stub, not from chart_facts

## design_correctness_verdict: NOT_CONSUMED
The entire `dosha_label` fact_category (110 facts/chart) is invisible to MSR. Separately, the 220 dosha-type signals that DO exist are attributed to only 10 distinct fact_ids (R-42 collapse), and none of those 10 resolve to chart_facts (referential break) — so doshas are simultaneously un-ingested at source AND mis-attributed at the signal layer.

## Findings
- summary: dosha_label fact_category (110 facts/chart) is entirely un-ingested by bo_laksana — 0 MSR signals resolve to it despite the facts existing in chart_facts. failure_class 1 (UNREACHABLE-by-omission-from-MSR / funnel narrowing). severity HIGH. evidence: 5-cell recipe returned `[]`; chart_facts count=110/110.
- summary: All 220 signal_type_class='dosha' signals cite only 10 distinct fact_ids (22× reuse each), and 0/10 resolve to any chart_facts.fact_id — R-42 dosha attribution collapse plus a referential-integrity break violating §N.5. failure_class 2 (WRONG) / cross-logged 6 (UNUSABLE FORM). severity HIGH. evidence: distinct_fids=10, total_refs=220, refs_resolving_to_chart_facts=0; sample id `e2b47b2c6d457725` absent from chart_facts.
