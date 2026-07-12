# Shard 9b — graha_avastha_jagradadi_per_varga

**Shard id:** `9b-graha_avastha_jagradadi_per_varga`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_jagradadi_per_varga'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 45.
- cell1: Abhisek 5, Abhinandan 5 → CONSUMED.
- cell2 salience: both `supporting=5`.
- cell3 attribution: both 5/5 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES (but see funnel narrowing).
2. Salience: all `supporting` — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: mono `character|career`.
5. Emergence: only 5 signals from 45 chart_facts rows → 40 rows do not surface as distinct signals.

## design_correctness_verdict: SOUND (with funnel-narrowing note)
Salience/attribution clean. The 45→5 narrowing means most per-varga jagradadi facts collapse into few signals; not a design failure per se (varga detail reasonably compressed) but noted.

## Findings
- **F1 (class 1 UNREACHABLE — funnel narrowing) — LOW.** 45 chart_facts rows yield only 5 MSR signals per chart; the bulk of per-varga jagradadi detail does not emerge as retrievable signals. Evidence: chart_facts=45 vs cell1=5. Repro: chart_facts COUNT vs 5-cell recipe. Suspected layer: ingestion-design.
- **F2 (class 2 domain mis-mapping) — MED (shared).** Mono `character|career`.
