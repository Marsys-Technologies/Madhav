# shard-9b-virodha_argala_natal_matrix

**shard_id:** 9b-virodha_argala_natal_matrix
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'virodha_argala_natal_matrix'`.

## Verbatim results
- chart_facts rows: 41760 (both charts; ~20880/chart)
- cell1: Abhisek=170, Abhinandan=159
- cell2_salience: both `supporting`
- cell5_type: both `composite_state`
- cell3_attr: 170/170 (Abhisek), 159/159 (Abhinandan) — 100%
- cell4_domains: both `character|relationship` (invariant)

## 5-cell verdicts
1. Consumed? YES but with EXTREME narrowing — 41760 chart_facts rows collapse to ~170 signals/chart (~0.8%). Virodha-argala (counter-obstruction) is inherently a large pairwise matrix, so aggressive selection is expected; but the 99%+ narrowing warrants noting as a funnel finding.
2. Salience: uniform `supporting` — proportionate given the matrix's supporting-evidence nature.
3. Attribution: 100% resolvable — PASS.
4. Domain: **INVARIANT** `character|relationship`. Argala/virodha-argala modulate the results of ALL bhavas (wealth, career, health), so a blanket relationship tag is over-narrow.
5. Emergence: 170/159 `composite_state` signals/chart.

## design_correctness_verdict: WEAK
Consumed and fully attributed, proportionate salience; defects are (a) the invariant relationship-only domain (argala affects all houses) and (b) note of the ~99% funnel narrowing from a 41760-row matrix — the selection logic is opaque and un-disclosed to the consumer.

## Findings
- **F1 (class 2 / domain mis-map):** 170/159 signals → invariant `character|relationship`; virodha-argala modulates every bhava, not only relationships. Suspected layer: L-writer. Severity: MED. Evidence: cell4 single value; cell1 170/159.
- **F2 (class 1 funnel-narrowing, informational):** 41760 chart_facts → ~170 signals/chart (~0.8% surfaced), no disclosed selection criterion. Suspected layer: L-writer ingestion selection. Severity: LOW (matrix expected to be large; flagged for consolidation to judge whether high-value argala pairs are among the dropped 99%).
