# shard-9b-tajik_hadda_lord

**shard_id:** 9b-tajik_hadda_lord
**lane:** 9b (MSR ingestion coverage + fidelity)
**charts:** 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## SQL run
5-cell recipe (charter-provided) with `f.fact_category = 'tajik_hadda_lord'`, plus chart_facts denominator count.

## Verbatim results
- chart_facts rows: 2400 (both charts)
- cell1 (consumed): Abhisek=285, Abhinandan=285
- cell2_salience: both `supporting=285`
- cell5_type: both `annual=285`
- cell3_attr: 285/285 both charts (100% attributed)
- cell4_domains: both `character|relationship` (single invariant value)

## 5-cell verdicts
1. Consumed by bo_laksana? YES (285 signals/chart, from 2400 chart_facts rows — heavy narrowing but substantial ingestion).
2. Salience: uniformly `supporting` — proportionate for annual/Tajik minutiae.
3. Attribution: 285/285 non-empty & resolvable — PASS (no R-44a defect).
4. Domain mapping: **INVARIANT** — 100% of 285 signals map to `character|relationship`. Tajik hadda (term/bound) lords in the varshaphala are strength/dignity indicators; a blanket `character|relationship` tag prevents these from surfacing under wealth/health/career-domain queries.
5. Emergence: 285 `annual` signals/chart, single type-class.

## design_correctness_verdict: WEAK
Consumed with perfect attribution and proportionate salience, but domain mapping is a fixed per-category default (KP-4-pattern generalization) — un-findable in any non-character/relationship domain query.

## Findings
- **F1 (class 2 WRONG / domain mis-map):** All 285 tajik_hadda_lord signals per chart are mapped to the identical `character|relationship` domain tuple regardless of the underlying hadda-lord's significations. Suspected layer: L-writer (bo_laksana domain-assignment). Severity: MED. Evidence: cell4 = `character|relationship` (only distinct value), cell1 = 285. Dedupe: KP-4-class (default-domain) pattern.
