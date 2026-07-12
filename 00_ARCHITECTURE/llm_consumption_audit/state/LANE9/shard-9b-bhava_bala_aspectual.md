# shard-9b-bhava_bala_aspectual

**Shard id:** bhava_bala_aspectual (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `bhava_bala_aspectual`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 60 / 60
- cell1 (signals): 15 (Abhisek `482012f1`) / 11 (Abhinandan `1c826d5a`)
- cell2_salience: `supporting=15` / `supporting=11`
- cell5_type: `composite_state=15` / `composite_state=11`
- cell3_attr: 15/15 / 11/11
- cell4_domains: `character|career` (both)

## 5-cell verdicts
1. Consumed? YES (partial — 15/11 signals from 60 facts, so ~75-82% of bhava-aspectual-bala facts do NOT emerge as signals).
2. Salience: flat `supporting`.
3. Attribution: full — SOUND on this axis.
4. Domain: fixed `character|career` — but bhava_bala is per-bhava: 2nd-house aspectual strength → wealth, 7th → relationship, 6th → health. Collapsed to `character|career`.
5. Emergence: 60 facts → 15/11 signals — most bhava aspectual-strength facts are NOT ingested.

## design_correctness_verdict: WEAK
Consumed but only partially (15/60, 11/60 emerge), flat salience, and domain-collapsed to `character|career` so that per-bhava strength (2nd=wealth, 7th=relationship, etc.) cannot surface in the matching domain query.

## Findings
- **F1 (class 1 UNREACHABLE-by-omission, MED):** only 15/60 (Abhisek) and 11/60 (Abhinandan) bhava_bala_aspectual facts emerge as MSR signals — the majority of per-bhava aspectual-strength facts are not ingested. Evidence: cell1=15/11 vs chart_facts=60/60.
- **F2 (class 2 WRONG, LOW):** fixed `character|career` domain hides wealth/relationship/health bhava strengths. Evidence: cell4=`character|career`.
