# shard-9b-aspect_matrix_summary

**Shard id:** aspect_matrix_summary (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `aspect_matrix_summary`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 60 / 60
- cell1 (signals): 25 / 25
- cell2_salience: `supporting=25` (both)
- cell5_type: `composite_state=25` (both)
- cell3_attr: 25/25 (both)
- cell4_domains: `character|career` (both)

## 5-cell verdicts
1. Consumed? YES (25/chart).
2. Salience: all `supporting` — proportionate for a summary/roll-up.
3. Attribution: 25/25 — SOUND.
4. Domain: fixed `character|career` — under-mapped for a whole-chart aspect matrix (spans all domains).
5. Emergence: 60 facts → 25 signals, `composite_state`.

## design_correctness_verdict: WEAK
Consumed, attributed, proportionate salience; but an aspect-matrix SUMMARY (chart-wide) collapsed to a fixed `character|career` domain pair is under-mapped — it should touch all domains it summarizes.

## Findings
- **F1 (class 2 WRONG, LOW):** aspect_matrix_summary fixed to `character|career` despite being a whole-chart aspect roll-up. Evidence: cell4=`character|career`, 25/25.
