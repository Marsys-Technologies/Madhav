# shard-9b-aspect_received_by_special_point

**Shard id:** aspect_received_by_special_point (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `aspect_received_by_special_point`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 470 (Abhisek `482012f1`) / 429 (Abhinandan `1c826d5a`)
- cell1 (signals): 470 / 429
- cell2_salience: `supporting=470` / `supporting=429`
- cell5_type: `composite_state=470` / `composite_state=429`
- cell3_attr: 470/470 / 429/429
- cell4_domains: `character|career` (both)

## 5-cell verdicts
1. Consumed? YES — 1:1 (every fact → one signal).
2. Salience: 100% flat `supporting` across 470/429 rows.
3. Attribution: full — SOUND on this axis.
4. Domain: fixed `character|career` for all rows.
5. Emergence: 1:1 explosion, no narrowing.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but 470/429 signals per chart are 1:1 with facts and IDENTICAL in salience (`supporting`), type (`composite_state`), and domain (`character|career`). Smaller than the per_varga floods but the same undifferentiated 1:1 ingestion pattern; borderline DROWNED and fixed-domain.

## Findings
- **F1 (class 7 DROWNED, MED):** 470/429 signals/chart, all `supporting`/`composite_state`/`character|career` — no discrimination among aspects received by special points (Gulika, Mandi, etc.). Rationale (CHARTER §7.4): identical-score wall across the entire category defeats top-K selection. Evidence: cell1=470/429, cell2=`supporting=470`/`supporting=429`.
- **F2 (class 2 WRONG, LOW):** fixed `character|career` domain regardless of which special point / bhava. Evidence: cell4=`character|career` both charts.
