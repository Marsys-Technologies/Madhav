# shard-9b-parivartana_per_varga

Lane: 9b. Charts: A=482012f1, B=1c826d5a.

## Exact SQL run
5-cell recipe (charter §4) with `<CAT>`=`parivartana_per_varga` + chart_facts count + per-fact fan-out probe.

## Verbatim results
- chart_facts: A=214, B=194.
- cell1: A=214, B=194.
- cell2 tiers: `supporting` only (both charts).
- cell3 attribution: A=214/214, B=194/194 (100%).
- cell4 domains: `career|wealth|relationship` (single distinct value).
- cell5 by type: `parivartana=214` (A), `parivartana=194` (B).
- Fan-out probe: each fact → exactly 1 signal (1:1). No duplication.

## 5-cell verdicts
1. Consumed YES — 1:1 chart_facts→signal (every parivartana fact promoted to a signal, indiscriminate). 2. Salience: ALL at `supporting` — no discrimination between a rasi (D1) mutual exchange (classically major) and an obscure high-varga exchange (trivia). 3. Attribution: 100% — SOUND. 4. Domain: uniform `career|wealth|relationship` for all 194–214 signals regardless of which bhavas actually exchange. 5. Emergence: 194–214 signals, undifferentiated.

## design_correctness_verdict: WEAK

## Findings
- F1 (class 7 DROWNED, MED): indiscriminate 1:1 ingestion — every one of 214/194 parivartana facts across all vargas becomes a signal at the identical `supporting` tier, so a chart-defining D1 parivartana is indistinguishable from a D60 micro-exchange. Rationale (§7.4 metric 2/3): family-collapse into one flat tier means an acharya-grade consumer cannot find the decisive exchanges among ~200 co-tied rows. Evidence: cell1=214/194 = chart_facts exactly; per-fact signal count=1; single distinct tier=`supporting`.
- F2 (class 2 WRONG, LOW): all 194–214 signals carry the identical `career|wealth|relationship` domain array irrespective of the exchanging bhavas — a parivartana between (e.g.) 3rd/6th lords is domain-mapped identically to a 2nd/11th exchange, so domain-filtered retrieval cannot discriminate.
