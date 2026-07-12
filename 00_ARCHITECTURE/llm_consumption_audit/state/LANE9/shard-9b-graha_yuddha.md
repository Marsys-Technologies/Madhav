# shard-9b-graha_yuddha

Lane: 9b MSR ingestion. Charts: Abhisek `482012f1`, Abhinandan `1c826d5a`.

## Reproducible call
9b 5-cell recipe with `<CAT>='graha_yuddha'`. chart_facts denominator: `SELECT ... COUNT(*) FROM chart_facts WHERE fact_category='graha_yuddha' AND chart_id IN (...)` → **1c826d5a=15, 482012f1=0 (no row returned)**.

## Verbatim results
- cell1: 1c826d5a=**15**, 482012f1=**(no rows — 0)**
- cell2_salience: 1c826d5a="supporting=15"
- cell5_type: 1c826d5a="composite_state=15"
- cell3_attr: 1c826d5a="15/15"
- cell4_domains: 1c826d5a="character|career"

## 5-cell verdicts
1. Consumed? **YES for 1c826d5a (15 signals)**. For 482012f1: **chart_facts has 0 graha_yuddha rows** — no planetary war exists in Abhisek's chart, so absence is UNREACHABLE-BY-NONEXISTENCE (legitimate: no fact to ingest), NOT a funnel-narrowing omission. MSR correctly ingests where the condition is present.
2. Salience: all 15 at **supporting** tier (1c826d5a). A lost graha yuddha (planetary war) can be a materially weakening condition; blanket supporting tier arguably slightly under-salience for a war involving a functional benefic/lord, but supporting is defensible and shows no inflation.
3. Attribution: **100%** (15/15). PASS.
4. Domain: uniform "character|career" — graha yuddha affects whatever the losing graha signifies, so a fixed character|career under-serves domain-filtered queries (systemic default).
5. Emergence: composite_state, 15 signals (1:1 with the 15 facts on 1c826d5a).

## design_correctness_verdict: SOUND
For the chart where the condition exists (1c826d5a), graha_yuddha is consumed 1:1, fully attributed, at a non-inflated supporting tier. Abhisek's zero is correct nonexistence, not an ingestion gap. Only the systemic character|career domain default applies as a minor note.

## Findings
- **F1 (class 2 WRONG, LOW):** graha_yuddha (1c826d5a) uniformly mapped to character|career; a planetary war on a domain-specific lord cannot surface under that domain's filter. Evidence: cell4="character|career", 15/15 signals. Minor participant in the shard-wide domain-default pattern; severity LOW because the count is small and character is partially defensible for a graha-condition.
