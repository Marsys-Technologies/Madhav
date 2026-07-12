# Shard 9b — fact_category: bhava_significance_link

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='bhava_significance_link' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=5220, B=5220
- cell1: A=5220, B=5220
- cell2_salience: A=`supporting=5220`, B=`supporting=5220`
- cell5_type: A=`composite_state=5220`, B=`composite_state=5220`
- cell3_attr: A=`5220/5220`, B=`5220/5220`
- cell4_domains: A=`career|relationship|wealth`, B=`career|relationship|wealth`

## Five-cell verdicts
1. Consumed? YES — fully (1:1, 5220 cf → 5220 signals).
2. Salience: 100% `supporting` — 5220 rows undifferentiated.
3. Attribution: 100% (5220/5220).
4. Domain: `career|relationship|wealth` (broader than the bhava_bala family, but still one fixed triple for all 5220 rows).
5. Emergence: 5220 cf → 5220 signals, all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 7 DROWNED, HIGH):** a single fact_category emits **5220 MSR signals per chart, all at the identical `supporting` tier** (cell1=5220, cell2=`supporting=5220`). This is a duplication/flood wall by CHARTER §7.4 metric 2 (identical-tier wall) — bhava_significance_link alone is a multiple of the entire rest of this shard combined, and no top-K discrimination exists within it. Any ranked surface fed by MSR is at severe risk of being swamped by bhava_significance_link rows. Rationale for exceeding acharya tolerance (§7.4 amendment): 5220 co-tied rows cannot be read; an acharya weighs a handful of significator links, not five thousand at one flat weight.
- **F2 (class 2 WRONG / domain mono-triple, MED):** all 5220 rows carry the same `career|relationship|wealth` triple (cell4) regardless of which houses the significance-link connects — health/spirituality/education significator links are absent from the domain tags, so those domains cannot retrieve their own significators.

completion: DONE
