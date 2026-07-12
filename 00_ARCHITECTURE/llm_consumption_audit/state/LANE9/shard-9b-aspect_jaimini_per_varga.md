# shard-9b-aspect_jaimini_per_varga

**Shard id:** aspect_jaimini_per_varga (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `aspect_jaimini_per_varga`, both charts. Plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: 15660 (Abhisek), 15660 (Abhinandan)
- cell1 (signals): 15660 / 15660
- cell2_salience: `supporting=15660` (both charts)
- cell5_type: `composite_state=15660` (both charts)
- cell3_attr: 15660/15660 (both charts)
- cell4_domains: `career|relationship|spirituality` (both charts)

## 5-cell verdicts
1. Consumed? YES — but 1:1 (15,660 facts → 15,660 signals per chart).
2. Salience: 100% `supporting` — utterly flat; no discrimination across 15,660 rows.
3. Entity attribution: 15660/15660 attributed (technically SOUND on this axis).
4. Domain mapping: fixed `career|relationship|spirituality` for all 15,660 — identical for every row.
5. Emergence: catastrophic 1:1 explosion — one fact_category alone emits 15,660 undifferentiated signals.

## design_correctness_verdict: BROKEN
A single fact_category floods MSR with 15,660 signals per chart that are IDENTICAL in salience (`supporting`), type (`composite_state`), and domain (`career|relationship|spirituality`). No consuming LLM can find or rank any individual per-varga Jaimini aspect within this wall — the data is present and attributed but un-findable and un-synthesizable at scale.

## Findings
- **F1 (class 7 DROWNED, CRITICAL):** 15,660 signals/chart from one fact_category, all at identical `supporting` tier / `composite_state` type / `career|relationship|spirituality` domain. Genuine signal is buried under a 15.6k-row indistinguishable wall. Evidence: cell1=15660, cell2=`supporting=15660`, cell5=`composite_state=15660`, cell4 single value.
- **F2 (class 8 UN-SYNTHESIZABLE AT SCALE, HIGH):** indiscriminate 1:1 fact→signal ingestion (15660 facts → 15660 signals) with zero salience differentiation defeats any top-K composition; the funnel does not narrow, it floods.
