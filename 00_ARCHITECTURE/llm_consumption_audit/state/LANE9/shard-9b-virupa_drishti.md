# shard-9b-virupa_drishti

**shard_id:** 9b-virupa_drishti
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'virupa_drishti'`.

## Verbatim results
- chart_facts rows: 5510 (both charts; 2755/chart)
- cell1: Abhisek=2755, Abhinandan=2755
- cell2_salience: both `supporting=2755`
- cell5_type: both `composite_state=2755`
- cell3_attr: 2755/2755 both (100%)
- cell4_domains: both `character|career` (invariant)

## 5-cell verdicts
1. Consumed? YES — total ingestion (2755/chart = every chart_facts row).
2. Salience: uniform `supporting` — proportionate per row, but 2755 identical-tier signals/chart is a DROWNED-risk mass on any ranked/listed surface (identical-score wall, §7.4 metric 2).
3. Attribution: 100% resolvable — PASS.
4. Domain: **INVARIANT** `character|career`. Virupa drishti (aspect strength in virupas) governs aspect effects on ALL houses/domains; blanket `character|career` is over-broad-yet-narrow default.
5. Emergence: 2755 `composite_state` signals/chart — single largest per-category signal population in this shard.

## design_correctness_verdict: WEAK
Fully consumed and attributed; but 2755 signals all at the same `supporting` tier and all mapped to the same `character|career` domain constitute an identical-score wall (drowning) plus a domain mis-map. The aspect-strength data is present and attributed but not FINDABLE — it forms an undifferentiated wall.

## Findings
- **F1 (class 7 DROWNED / identical-score wall):** 2755 virupa_drishti signals/chart, all `supporting`, all `character|career` — no discrimination among 2755 rows. Per §7.4 metric 2, a wall of co-tied identical-tier rows the ranker cannot separate. Rationale inline: an acharya distinguishes a full 60-virupa Saturn aspect on the Moon from a 7-virupa trivial aspect; the flat `supporting` tier erases that. Suspected layer: ranking (signature_tier) + form. Severity: MED. Evidence: cell2 `supporting=2755`; cell1 2755.
- **F2 (class 2 / domain mis-map):** 2755/2755 → invariant `character|career`. Severity: LOW. Evidence: cell4 single value.
