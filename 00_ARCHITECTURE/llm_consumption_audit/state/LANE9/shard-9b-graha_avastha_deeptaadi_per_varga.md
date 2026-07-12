# Shard 9b — graha_avastha_deeptaadi_per_varga

**Shard id:** `9b-graha_avastha_deeptaadi_per_varga`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_deeptaadi_per_varga'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 1305.
- cell1: Abhisek 589, Abhinandan 601 → CONSUMED.
- cell2 salience: Abhisek `background=184, supporting=405`; Abhinandan `background=185, supporting=416`.
- cell3 attribution: Abhisek 589/589, Abhinandan 601/601 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: ALL `supporting`/`background` — correctly de-weighted. PASS.
3. Attribution: 100%. PASS.
4. Domain: mono `character|career`.
5. Emergence: 589–601 signals, all composite_state.

## design_correctness_verdict: SOUND
Per-varga deeptaadi correctly held at supporting/background with full attribution — model calibration mirroring baladi_per_varga. High raw volume noted as aggregate-drowning context only.

## Findings
- **F1 (class 7 DROWNED — volume context) — LOW.** 589–601 signals from one fact_category; individually de-weighted. Evidence: cell1. Suspected layer: ingestion-design.
- **F2 (class 2 domain mis-mapping) — MED (shared).** Mono `character|career`. Evidence: cell4.
