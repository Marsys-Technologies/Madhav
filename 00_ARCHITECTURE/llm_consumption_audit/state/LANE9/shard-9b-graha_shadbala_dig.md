# Shard 9b — graha_shadbala_dig

shard_id: 9b-graha_shadbala_dig
charts: Abhisek 482012f1 · Abhinandan 1c826d5a

## Exact SQL: proven 9b 5-cell recipe, <CAT>=graha_shadbala_dig.

## Verbatim results
chart_facts baseline: Abhisek=45, Abhinandan=45.
- cell1: Abhinandan=40, Abhisek=40
- cell2_salience: Abhinandan `background=10, major=29, supporting=1`; Abhisek `background=2, major=35, supporting=3`
- cell3_attr: `40/40` both
- cell4_domains: BOTH `character|career`
- cell5_type: `composite_state=40` both

## 5-cell verdicts
1. Consumed? YES (40).
2. Salience: **major-heavy** (Abhisek major=35/40) — intermediate sub-component inflation.
3. Attribution: 100% non-empty — sound.
4. Domains: character|career only — narrow.
5. Emergence: composite_state.

## design_correctness_verdict: WEAK

## Findings
- **Dig-bala (directional strength sub-component) inflated to 'major'.** Abhisek 35/40 signals at `major`. Dig bala is one arithmetic input to shadbala_total; promoting it to major duplicates the strength story alongside the 5 other sub-components. failure_class=7 (DROWNED). severity=MED. suspected layer: ranking. evidence: cell2 Abhisek `major=35, supporting=3, background=2`.
- **Domain mono-map character|career.** failure_class=2 (WRONG). severity=LOW. evidence: cell4 both = `character|career`.
