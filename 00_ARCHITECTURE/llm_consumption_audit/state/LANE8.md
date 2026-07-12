# LANE 8 — LLM Consumption Audit (20-Dossier Depth Audit)

<!-- RESUME: LANE8 complete — dossiers_audited=20 of 20 -->

**Lane:** LANE8
**dossiers_total:** 20
**dossiers_audited:** 20
**findings_count:** 140
**avg_completeness:** 73.5%
**total_held_but_not_received:** 114 facets

## Rollup

### Verdict spread (20 dossiers)

| verdict | count |
|---|---|
| SYNTHESIZABLE | 1 |
| PARTIAL | 19 |
| UNCOMPOSABLE | 0 |

### Headline finding

Across all 20 per-graha/per-lagna dossiers (both charts `482012f1` "71aa" and `f75a`), **114 facets are held in the DB but not received over the wire** — the dominant failure class is **held-but-not-received (failure_class 1)**: the data exists and is computed, but the CONCEPT_RETRIEVABILITY_MATRIX channel is `served-only-by-down-pipeline` (or, for transits, `truly-unreachable`), so a consuming LLM has no surgical MCP path to it.

The single most recurrent defect is the **R-45 structural×temporal convergence asset** — "which of a graha's yogas/promises are temporally ripe (recent past + near future)". It is held in `kala_convergence` (6484 rows for 71aa; ~2959 rows for f75a) and `bodha_convergence`, but the entire `kala_*` / `bodha_convergence` family is `served-only-by-down-pipeline`. This anchor (R-45) is **rediscovered independently in 15 of the 20 dossiers**. Two further systemic patterns: **yoga participation** (facet 41) and **dosha participation** (facet 42) held in `bodha_msr_signals` / `brahma_dosha_catalog` but likewise down-pipeline-only; and the **transit-now / double-transit** facets (Jupiter-f75a) which are `truly-unreachable` from `bg_transit_engine`.

### Per-dossier table

| dossier | verdict | HIGH/CRIT findings |
|---|---|---|
| Sun-71aa | PARTIAL | 3 (yoga F00801, dosha F00821, convergence F01021/R-45) |
| Moon-71aa | PARTIAL | 1 (convergence F01022/R-45) |
| Mars-71aa | PARTIAL | 3 (yoga f41, dosha f42, convergence f52/R-45) |
| Mercury-71aa | PARTIAL | 1 (convergence f52/R-45) |
| Jupiter-71aa | PARTIAL | 1 (convergence F01025/R-45) |
| Venus-71aa | PARTIAL | 2 (convergence f52/R-45, 7-facet data-plane nonexistence) |
| Saturn-71aa | PARTIAL | 1 (convergence R-45) |
| Rahu-71aa | PARTIAL | 1 (convergence F01028/R-45) |
| Ketu-71aa | PARTIAL | 4 (yoga f41, dosha f42, convergence f52/R-45, remedial f56) |
| Lagna-71aa | PARTIAL | 1 (convergence F01030/R-45) |
| Sun-f75a | PARTIAL | 1 (convergence F01031/R-45) |
| Moon-f75a | PARTIAL | 2 (dasha-quality F45/F00892, convergence F52/F01032) |
| Mars-f75a | PARTIAL | 1 (convergence F01053/R-45) |
| Mercury-f75a | PARTIAL | 1 (convergence f52/R-45) |
| Jupiter-f75a | PARTIAL | 3 (convergence f52/R-45, transit-now f47, double-transit f49) |
| Venus-f75a | PARTIAL | 1 (convergence R-45) |
| Saturn-f75a | PARTIAL | 0 |
| Rahu-f75a | PARTIAL | 0 |
| Ketu-f75a | PARTIAL | 0 |
| Lagna-f75a | SYNTHESIZABLE | 0 |

(Verdict spread: 1 SYNTHESIZABLE, 19 PARTIAL, 0 UNCOMPOSABLE. Shard detail per dossier under `state/LANE8/shard-<dossier>.md`.)

## HIGH / CRITICAL findings (verbatim evidence)

All findings below are **failure_class 1 (held-but-not-received)** unless noted.

### Sun-71aa

1. **[HIGH]** Sun yoga participation (F00801) held-but-not-received: full yoga catalog majority served-only-by-down-pipeline, not surgically wire-reachable.
   - Evidence: `CONCEPT_RETRIEVABILITY_MATRIX bodha_msr_signals channel split {reachable-surgical:32, served-only-by-down-pipeline:83}; yoga-family membership majority 'served-only-by-down-pipeline'`

2. **[HIGH]** Sun dosha participation (F00821) held-but-not-received: per-chart dosha membership unreachable over wire.
   - Evidence: `brahma_dosha_catalog channel 'served-only-by-down-pipeline'; bodha_contradictions channel 'truly-unreachable'`

3. **[HIGH]** Sun structural×temporal convergence / ripeness (F01021, R-45 anchor) held-but-not-received.
   - Evidence: `kala_convergence + kala_activation channel 'served-only-by-down-pipeline'; which of Sun's promises are temporally ripe is computed but not wire-served (R-45 rediscovered)`

### Moon-71aa

4. **[HIGH]** Structural×temporal convergence (R-45) for Moon is held in `kala_convergence` (6484 rows) but sealed behind `served-only-by-down-pipeline` — a consuming LLM cannot retrieve which of Moon's yogas/promises are temporally ripe.
   - Evidence: `facet 52 / F01022; kala_convergence channel=served-only-by-down-pipeline; DB holds 6484 convergence rows for chart 482012f1. Anchor R-45 instantiation.`

### Mars-71aa

5. **[HIGH]** Yoga participation (facet 41 — every yoga Mars constitutes) held in `bodha_msr_signals` but served only by the down-pipeline; no surgical yoga-membership-by-graha tool, so a consuming LLM cannot receive the Mercury-standard core of Mars's dossier.
   - Evidence: `bodha_msr_signals has 4281 Mars-referencing rows; matrix marks 83/115 families for that table as 'served-only-by-down-pipeline'; wire_reachable(surgical)=false`

6. **[HIGH]** Dosha participation (facet 42 — full L0 dosha catalog) served only via MSR/`brahma_dosha_catalog` down-pipeline; only scattered `chart_facts` dosha subjects are surgical.
   - Evidence: `brahma_dosha_catalog + bodha_msr_signals channel='served-only-by-down-pipeline'; chart_facts holds only isolated dosha subjects e.g. mahendra_dosha`

7. **[HIGH]** Structural×temporal convergence (facet 52, R-45 anchor) — which of Mars's yogas/promises are temporally ripe — held in `kala_convergence`/`kala_activation` but not wire-reachable surgically.
   - Evidence: `kala_convergence + kala_activation channel='served-only-by-down-pipeline'; R-45 anchor rediscovered`

### Mercury-71aa

8. **[HIGH]** Facet 52 structural×temporal convergence (R-45) held but served-only-by-down-pipeline — no surgical path to ask which of Mercury's promises are temporally ripe.
   - Evidence: `bodha_convergence=30 rows + kala_convergence=6484 rows for 71aa; matrix channel 'served-only-by-down-pipeline'; rediscovers R-45 anchor`

### Jupiter-71aa

9. **[HIGH]** Structural×temporal convergence (facet 52, F01025) held but UNREACHABLE — `kala_convergence` holds 6484 rows for the chart yet the whole family is served-only-by-down-pipeline with no surgical MCP tool fronting it; rediscovers R-45.
   - Evidence: `matrix: kala_convergence -> 'served-only-by-down-pipeline'; DB: SELECT count(*) FROM kala_convergence WHERE chart_id='482012f1-...' = 6484. Doctrine names this exact facet ('which of its yogas/promises are temporally ripe, recent past + near future — the R-45 asset').`

### Venus-71aa

10. **[HIGH]** Venus structural×temporal convergence (facet 52, R-45 asset) held as 6,484 `kala_convergence` windows but channel is served-only-by-down-pipeline — no surgical wire path serves which Venus yogas are temporally ripe.
    - Evidence: `kala_convergence count=6484 for 482012f1; matrix channel=served-only-by-down-pipeline for kala_convergence families`

11. **[HIGH]** Data-plane nonexistence for 7 canonical Venus facets: mrityu-bhaga (R-47 anchor), neecha-bhanga, kartari, Sarvatobhadra vedha, 22nd-drekkana/64th-navamsa, pushkara, declination/kranti — never computed.
    - Evidence: `chart_facts %mrityu_bhaga%=0, neecha=0, kartari=0, vedha/sarvatobhadra=0, drekkana/khareshwara/64navamsa=0, pushkara=0, kranti/declination/shara=0`

### Saturn-71aa

12. **[HIGH]** R-45 structural×temporal convergence (facet 52) held in `kala_convergence`/`bodha_convergence` but channel is served-only-by-down-pipeline — the flagship Saturn temporal-ripeness/sade-sati-adjacency asset is not wire-reachable to a consuming LLM.
    - Evidence: `matrix {"table_name":"kala_convergence","channel":"served-only-by-down-pipeline"} (33 families) + bodha_convergence (29, sod); DB holds kala_convergence rows for chart 482012f1. Relates to anchor R-45.`

### Rahu-71aa

13. **[HIGH]** F01028 structural×temporal convergence (R-45 asset): held in `kala_convergence` (6484 rows) but the entire `kala_*` family is served-only-by-down-pipeline — no surgical MCP tool fronts Rahu's temporally-ripe promises for a consuming LLM.
    - Evidence: `kala_convergence WHERE chart_id=482012f1 → 6484 rows; matrix channel for kala_convergence = 'served-only-by-down-pipeline'`

### Ketu-71aa

14. **[HIGH]** Ketu yoga participation (facet 41) held as 1571 signals in `bodha_msr_signals` but only served-only-by-down-pipeline; no surgical MCP path for a consuming LLM to retrieve Ketu's yoga membership.
    - Evidence: `matrix: bodha_msr_signals channel served-only-by-down-pipeline (83 families); DB bodha_msr Ketu signals = 1571.`

15. **[HIGH]** Ketu dosha participation (facet 42) reachable only via down-pipeline (`bodha_msr_signals` + `brahma_dosha_catalog`).
    - Evidence: `matrix: bodha_msr_signals served-only-by-down-pipeline; brahma_dosha_catalog served-only-by-down-pipeline.`

16. **[HIGH]** Structural×temporal convergence for Ketu (facet 52, R-45 anchor) held in `kala_convergence` (6484 rows) but served-only-by-down-pipeline — the R-45 asset is not wire-reachable.
    - Evidence: `matrix: kala_convergence channel served-only-by-down-pipeline; DB kala_convergence rows for chart = 6484.`

17. **[HIGH]** Ketu remedial mapping (facet 56) held in `bodha_rm_remedy_prescriptions` (135 rows) but served-only-by-down-pipeline; whether served remedial priority reflects Ketu's afflictions is unverifiable over wire.
    - Evidence: `matrix: bodha_rm_remedy_prescriptions served-only-by-down-pipeline; DB rm_remedy Ketu-chart rows = 135.`

### Lagna-71aa

18. **[HIGH]** Structural×temporal convergence (R-45 asset) for the Lagna held (`kala_convergence`/`bodha_convergence`/`kala_activation`) but not wire-reachable — served-only-by-down-pipeline; the raw `convergence_count` is reachable via `chart_facts` but the temporally-ripe promise-ripeness dossier is not.
    - Evidence: `matrix: all kala_convergence & bodha_convergence family_keys = 'served-only-by-down-pipeline'; facet F01030 held_in_db=TRUE, wire_reachable=FALSE. Re-confirms anchor R-45 (dedupe: not a new register row).`

### Sun-f75a

19. **[HIGH]** Sun's structural×temporal convergence (R-45 asset: which yogas/promises are temporally ripe) held in `kala_convergence`/`kala_taranga` but marked served-only-by-down-pipeline — no MCP tool surfaces it, so the dossier cannot answer the core time-indexed-prediction question.
    - Evidence: `F01031; matrix: kala_convergence channel=served-only-by-down-pipeline; DB holds convergence_count in chart_facts (reachable) but the R-45 ripeness asset lives in kala_convergence (unreachable). Cognate to anchor R-45.`

### Moon-f75a

20. **[HIGH]** Dasha-quality context (dignity/house of each running lord from Moon and vice versa) held only in `kala_*` down-pipeline tables, unreachable to a consuming LLM.
    - Evidence: `facet F45 (F00892) 'Dasha-quality context: dignity/house of each running lord FROM this graha and vice versa'; backing kala_darshana/kala_avadhi channel=served-only-by-down-pipeline per matrix`

21. **[HIGH]** Structural×temporal convergence (R-45 asset: which of Moon's yogas/promises are temporally ripe, recent past + near future) served only by `kala_convergence` down-pipeline.
    - Evidence: `facet F52 (F01032); kala_convergence channel=served-only-by-down-pipeline; chart_facts convergence_count only a partial substitute — the windowed R-45 asset is not wire-reachable`

### Mars-f75a

22. **[HIGH]** Structural×temporal convergence for Mars (yoga/promise temporal ripeness, past+near-future) held only in `kala_convergence`/`bodha_convergence`, served-only-by-down-pipeline — no surgical wire path; the depth-axis-named core facet is unreachable (R-45).
    - Evidence: `facet F01053; matrix: kala_convergence/bodha_convergence channel='served-only-by-down-pipeline'; DB holds kala_convergence rows for chart. Extends anchor R-45.`

### Mercury-f75a

23. **[HIGH]** Facet 52 structural×temporal convergence (R-45 asset) held in `kala_convergence` but not wire-reachable — held-but-not-received.
    - Evidence: `kala_convergence holds 2959 rows for chart f75a, but matrix channel='served-only-by-down-pipeline' — no surgical MCP path serves the convergence to a consuming LLM. Rediscovers R-45 (temporal convergence EMPTY-SHELL-to-consumer).`

### Jupiter-f75a

24. **[HIGH]** Structural×temporal convergence (R-45) for Jupiter held in `kala_convergence`/`bodha_convergence` but served only into the downstream pipeline, not over the wire.
    - Evidence: `facet 52 verbatim: 'Structural×temporal convergence: which of its yogas/promises are temporally ripe, recent past + near future (the R-45 asset)'. kala_convergence n=2959, bodha_convergence n=30 for chart f75a; matrix channel=served-only-by-down-pipeline. This is the R-37/R-45 anchor class.`

25. **[HIGH]** Live transit position of Jupiter (transit-now) computed by the transit engine but no MCP tool serves it.
    - Evidence: `facet 47 verbatim: 'Transit now: sign/house from natal Moon and Lagna, gochara quality + vedha points, murthi at ingress; ashtakavarga bindu filter in transited sign'. Backing bg_transit_engine; matrix channel=truly-unreachable.`

26. **[HIGH]** Double-transit (Saturn+Jupiter) participation on natal points unreachable via wire.
    - Evidence: `facet 49 verbatim: 'Double-transit (Saturn+Jupiter) participation on natal points'. Backing bg_transit_engine; matrix channel=truly-unreachable.`

### Venus-f75a

27. **[HIGH]** Venus structural×temporal convergence (R-45 asset) held in `kala_convergence` but wire-unreachable.
    - Evidence: `kala_convergence holds 2959 rows for chart f75a; matrix channel=served-only-by-down-pipeline — no reachable-surgical path. (R-45 rediscovered.)`

---

*LANE8 depth audit — 20/20 dossiers audited; 140 findings total; 27 HIGH/CRIT surfaced above; 114 held-but-not-received facets; avg completeness 73.5%. Dominant systemic defect: R-45 structural×temporal convergence held in `kala_convergence`/`bodha_convergence` but served-only-by-down-pipeline (rediscovered in 15 dossiers). Transit-now / double-transit facets are `truly-unreachable`.*
