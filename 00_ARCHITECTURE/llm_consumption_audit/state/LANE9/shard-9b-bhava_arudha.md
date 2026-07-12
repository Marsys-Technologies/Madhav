# shard-9b-bhava_arudha

**Shard id:** bhava_arudha (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `bhava_arudha`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 210 / 210
- cell1 (signals): 123 (Abhisek `482012f1`) / 120 (Abhinandan `1c826d5a`)
- cell2_salience: `supporting=123` / `supporting=120`
- cell5_type: `karaka_alignment=123` / `karaka_alignment=120`
- cell3_attr: 123/123 / 120/120
- cell4_domains: `character|relationship` (both)

## 5-cell verdicts
1. Consumed? YES.
2. Salience: flat `supporting`. Arudha Lagna (AL) is a primary perception/status axis — uniformly demoting all arudhas to supporting is a mild deflation.
3. Attribution: full — SOUND.
4. Domain: fixed `character|relationship` — but arudhas are bhava-specific: A2 (dhana arudha) = wealth, A10 (rajya arudha) = career, A11 (labha arudha) = gains. Collapsing all to `character|relationship` means wealth/career arudhas can never surface in wealth/career queries (KP-4 pattern).
5. Emergence: 210 facts → ~120 signals.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but two defects: (a) domain fixed to `character|relationship` regardless of which bhava's arudha, so A2/A10/A11 wealth/career significations are domain-unreachable; (b) type `karaka_alignment` is an odd class for arudha padas (arudha is a reflection-point technique, not karaka alignment) — possible mis-typing.

## Findings
- **F1 (class 1 UNREACHABLE / class 2 WRONG, MED):** all bhava_arudha signals fixed to `character|relationship`; wealth-arudha (A2/A11) and career-arudha (A10) cannot surface under wealth/career domain filters. Evidence: cell4=`character|relationship` for all 123/120 rows.
- **F2 (class 2 WRONG, LOW):** arudha padas typed `signal_type_class=karaka_alignment`, a semantically mismatched class. Evidence: cell5=`karaka_alignment=123/120`.
