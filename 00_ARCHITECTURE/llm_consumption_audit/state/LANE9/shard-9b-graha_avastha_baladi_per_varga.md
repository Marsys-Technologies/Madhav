# Shard 9b — graha_avastha_baladi_per_varga

**Shard id:** `9b-graha_avastha_baladi_per_varga`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_baladi_per_varga'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 1305.
- cell1: Abhisek 551, Abhinandan 696 → CONSUMED.
- cell2 salience: Abhisek `background=168, supporting=383`; Abhinandan `background=173, supporting=523`.
- cell3 attribution: Abhisek 551/551, Abhinandan 696/696 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: ALL `supporting`/`background` — correctly de-weighted for per-varga granular detail. PASS.
3. Attribution: 100%. PASS.
4. Domain: mono `character|career` (default).
5. Emergence: very high volume (551–696 signals from ONE fact_category), all composite_state.

## design_correctness_verdict: SOUND
Per-cell this is the model calibration: full attribution, salience correctly held at supporting/background for granular per-varga avastha. Note (not a per-category defect): the raw volume (551–696 signals) is a top-line drowning contributor at the aggregate MSR surface — logged as context, not a cell-level defect here.

## Findings
- **F1 (class 7 DROWNED — volume context) — LOW.** 551–696 signals emerge from this single fact_category; individually de-weighted but contributes to aggregate MSR bulk. Evidence: cell1 551/696. Suspected layer: ingestion-design (bo_laksana emitting one signal per per-varga fact row).
- **F2 (class 2 domain mis-mapping) — MED (shared).** Mono `character|career`. Evidence: cell4.
