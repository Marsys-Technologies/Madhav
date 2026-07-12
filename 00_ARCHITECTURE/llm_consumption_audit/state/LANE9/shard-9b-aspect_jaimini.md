# shard-9b-aspect_jaimini

**Shard id:** aspect_jaimini (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
The proven 9b 5-cell recipe (CHARTER §4 / brief §4), with `<CAT>` = `aspect_jaimini`, over both charts `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek) and `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan). Plus denominator: `SELECT COUNT(*) FROM chart_facts WHERE fact_category='aspect_jaimini' AND chart_id IN (...)`.

## Verbatim results
- chart_facts denominator: 540 (Abhisek), 540 (Abhinandan)
- cell1 (signals): 60 / 60
- cell2_salience: `supporting=60` (both charts)
- cell5_type: `composite_state=60` (both charts)
- cell3_attr: 60/60 (both charts) — 100% non-empty constituent_facts_array
- cell4_domains: `character|career` (both charts)

## 5-cell verdicts
1. Consumed by bo_laksana? YES (60 signals/chart).
2. Salience class: entirely `supporting` — proportionate for aspect data (low-decision-weight, not inflated).
3. Entity attribution: 60/60 attributed — SOUND.
4. Domain mapping: fixed `character|career` for all 60 — over-narrow default; Jaimini rasi-drishti bears on relationship/wealth (arudha padas) too, never surfaces there.
5. Emergence: 540 facts → 60 signals, all `composite_state`.

## design_correctness_verdict: WEAK
Consumed and fully attributed with proportionate (supporting) salience, but domain mapping collapses to a fixed `character|career` default regardless of which rasi-aspect it is — a KP-4-style narrowing that keeps Jaimini aspects out of relationship/wealth-domain queries.

## Findings
- **F1 (class 2 WRONG / class-1 consequence, LOW):** all 60 aspect_jaimini signals fixed-mapped to `character|career`; rasi-drishti relevant to relationship/wealth can never surface under those domain filters. Evidence: cell4_domains = `character|career` (both charts), 60/60 rows.
