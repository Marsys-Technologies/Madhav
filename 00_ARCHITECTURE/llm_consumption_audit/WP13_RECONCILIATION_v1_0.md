---
artifact: WP13_RECONCILIATION
version: 1.0
status: CURRENT
produced_by: RECONCILIATION agent (ND-W1.1 binding gate)
date: "2026-07-12"
gate: ND-W1.1 (WP-1.3 coverage reconciliation)
denominator: 295 (wp_coverage.jsonl where wp=="WP-1.3")
verdict: PASS
unreconciled_count: 0
---

# WP-1.3 Coverage Reconciliation — ND-W1.1 Binding Gate

**Gate (native, binding):** at WP-1.3 CLOSE, mechanically diff the UNION of sub-lanes a–i's
finding IDs against the full WP-1.3 slice of `deliverables/wp_coverage.jsonl` (295 findings).
Every ID must end in **exactly one** disposition — verified-fixed by a named sub-lane, or
explicitly re-dispositioned WITH a reason. **WP-1.3 does not close with an unreconciled remainder.**

## Method
- **Denominator:** every record in `deliverables/wp_coverage.jsonl` with `wp=="WP-1.3"` →
  **295 findings confirmed** (275 `F-####` + 20 `F-L10-###`). All 295 join cleanly to
  `deliverables/findings.jsonl` (0 orphans).
- **Mapping:** each finding is joined to its `findings.jsonl` record (summary / `failure_class` /
  locus) and assigned ONE disposition by ROOT CAUSE — a sub-lane that fixed a root cause covers all
  findings of that cause (mapped by failure-class + description, not only literally-cited IDs).
  The `F-L10-###` findings use the explicit §5 disposition table in `REMEDIATION_RUN_LEDGER_v1_0.md`.
- **Sub-lanes (WP-1.3 a–i)** and the in-wave sibling lanes that closed WP-1.3-slice root causes:
  - **(a)** 13 computed-but-unserved assets served (`45a27834`; §5 table) — cdlm/cgm/gestalt,
    ka_avadhi/darshana/convergence/taranga/obstruction, ph_sankrama, ga_medical/vastu/yoga_firings.
  - **(b,c)** `query_dasha_periods` honors `system_id` + requested windows (`1764d2b1`;
    F-0354/0471/0485; 8 systems / ~437k dark rows).
  - **(d)** `lel_query` serves 57 life events (`22816856`; F-L10-021).
  - **(e)** temporal-windows serving half — honor+echo date params, honest-empty (`036a5cea`); full
    acceptance is **PENDING-W3** (needs WP-2.1 writer activation-dates, R-45).
  - **(f)** `query_chart_facts` filters + pagination + 6 ayanamshas (`15710eb6`).
  - **(g)** `msr_sql` projection param (`22816856`; LCA-7).
  - **(h)** dead-registry purge + help regen + F-WP17-1 park + phantom drops + m8 counts (`bb8610ea`).
  - **(i)** apex/assess dedup + verdict_skeleton serving fixes (`efc9ba52`; LCA-11, R-40).
  - **sibling WP-1.2α/β (in-wave):** ranked-surface hydration + salience/attribution (`1dce804a`) and
    domain discrimination + new/corrected domains moksha/education/character + bhava→domain
    un-collapse + F-0756 (`97d6fe9c`). These closed a large block of WP-1.3-slice `failure_class`
    findings whose root cause was ranking/domain, not a distinct 1.3 tool.
  - **WP-1.7 (in-wave):** whitelist resolution — registered `cgm_graph_walk`→`traverse_chart_graph`
    etc., supporting the (a)/(h) reachability fixes for the dead-tool (`failure_class 0`) block.

## Disposition legend
- **REMEDIATED-PENDING-W4** — root cause fixed + verifier-CONFIRMED by a named lane; full CLOSED at the W4 re-audit.
- **PENDING-W3** — serving honored, but full acceptance needs WP-2.1 writer data (temporal / activation-date findings; the (e) lane + R-45).
- **PENDING-W2** — needs a W2 writer: empty-shell / data-plane-absent / unmodeled-concept / NULL-column / narration-pending.
- **W1-FOLLOWUP** — genuine WP-1.3 serving residual, not yet fixed (populated-but-unserved asset with no writer needed; (a) NEXT-PASS live-compute wrappers + serving-bugs; synthesis-assessor gap).
- **PARKED** (`parked_pending_native_review`) — genuine design question, held for native.
- **UNRECONCILED** — no disposition (gate FAILS if non-empty).

## Summary block

| Disposition | Count |
|---|---|
| REMEDIATED-PENDING-W4 | 96 |
| PENDING-W3 | 44 |
| PENDING-W2 | 131 |
| W1-FOLLOWUP | 23 |
| PARKED | 1 |
| **TOTAL** | **295** |

**REMEDIATED-PENDING-W4 by lane:**

| Lane | Count |
|---|---|
| (a) | 40 |
| (sibling WP-1.2β, in-wave) | 26 |
| (i) | 14 |
| (b,c) | 8 |
| (d) | 5 |
| (sibling WP-1.2α/β, in-wave) | 2 |
| (f) | 1 |

**UNRECONCILED count: 0 → GATE VERDICT: PASS**

## Per-finding reconciliation (all 295)

| finding_id | class | sev | disposition | sub-lane / reason |
|---|---|---|---|---|
| F-0113 | c0 | HIGH | REMEDIATED-PENDING-W4 | (a)+(h)/(1.7): dead surgical tool resurrected — cdlm/cgm serving tools added ((a) query_cdlm_summary/query_cgm_paths/motifs) + registry/whitelist cleanup ((h)/WP-1.7 cgm_graph_walk->traverse_chart_graph) |
| F-0115 | c0 | HIGH | REMEDIATED-PENDING-W4 | (a)+(h)/(1.7): dead surgical tool resurrected — cdlm/cgm serving tools added ((a) query_cdlm_summary/query_cgm_paths/motifs) + registry/whitelist cleanup ((h)/WP-1.7 cgm_graph_walk->traverse_chart_graph) |
| F-0117 | c0 | HIGH | REMEDIATED-PENDING-W4 | (a)+(h)/(1.7): dead surgical tool resurrected — cdlm/cgm serving tools added ((a) query_cdlm_summary/query_cgm_paths/motifs) + registry/whitelist cleanup ((h)/WP-1.7 cgm_graph_walk->traverse_chart_graph) |
| F-0119 | c0 | HIGH | REMEDIATED-PENDING-W4 | (a)+(h)/(1.7): dead surgical tool resurrected — cdlm/cgm serving tools added ((a) query_cdlm_summary/query_cgm_paths/motifs) + registry/whitelist cleanup ((h)/WP-1.7 cgm_graph_walk->traverse_chart_graph) |
| F-0120 | c0 | HIGH | REMEDIATED-PENDING-W4 | (a)+(h)/(1.7): dead surgical tool resurrected — cdlm/cgm serving tools added ((a) query_cdlm_summary/query_cgm_paths/motifs) + registry/whitelist cleanup ((h)/WP-1.7 cgm_graph_walk->traverse_chart_graph) |
| F-0124 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0129 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0130 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0131 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0136 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0137 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0141 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0143 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0144 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0145 | c1 | HIGH | W1-FOLLOWUP | kala_jivana_parva 100-yr parva narratives — asset not among the served-13 in (a); serving residual (next-pass lane) |
| F-0146 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0147 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0149 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0150 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0151 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0152 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0153 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0155 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0156 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0157 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0160 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) get_yoga_firings exposes ga_yoga_firings — yoga participation now wire-reachable (was served-only-by-down-pipeline) |
| F-0161 | c1 | HIGH | W1-FOLLOWUP | per-chart dosha-membership surgical exposure not added this wave (served only via MSR/brahma_dosha_catalog down-pipeline) — serving residual |
| F-0163 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0164 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) get_yoga_firings exposes ga_yoga_firings — yoga participation now wire-reachable (was served-only-by-down-pipeline) |
| F-0165 | c1 | HIGH | W1-FOLLOWUP | per-chart dosha-membership surgical exposure not added this wave (served only via MSR/brahma_dosha_catalog down-pipeline) — serving residual |
| F-0167 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_convergence_windows exposes kala_convergence (6484 rows) to the surgical wire; underlying activation-date ripeness (R-45) matures at WP-2.1/W2 |
| F-0168 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0169 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0171 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0172 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0173 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) get_yoga_firings exposes ga_yoga_firings — yoga participation now wire-reachable (was served-only-by-down-pipeline) |
| F-0174 | c1 | HIGH | W1-FOLLOWUP | per-chart dosha-membership surgical exposure not added this wave (served only via MSR/brahma_dosha_catalog down-pipeline) — serving residual |
| F-0175 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0176 | c1 | HIGH | W1-FOLLOWUP | populated-but-unserved asset (real rows in DB, NOT among the served-13 in (a)) — genuine WP-1.3 serving residual; needs a surgical retrieval tool (next-pass lane), no writer required |
| F-0178 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0179 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0180 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0181 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0182 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0183 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0184 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS ka_gochara / live-transit search sidecar (F-L10-011) — transit engine computes it but no MCP tool serves it yet; serving residual |
| F-0185 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS ka_gochara / live-transit search sidecar (F-L10-011) — transit engine computes it but no MCP tool serves it yet; serving residual |
| F-0186 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) surgical surface added over the held asset (query_dasha_dossier[ka_avadhi] / query_convergence_windows[ka_sangam] / query_temporal_view[ka_darshana] / query_obstruction_periods[ka_vighnakara] / query_activation_waveform[ka_taranga] / query_cgm_paths / query_cdlm_summary / query_chart_gestalt) — now wire-reachable (§5 table) |
| F-0190 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0194 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_convergence_windows exposes kala_convergence (6484 rows) to the surgical wire; underlying activation-date ripeness (R-45) matures at WP-2.1/W2 |
| F-0398 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0399 | c4 | MED | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0400 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0402 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0403 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0404 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0406 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0416 | c4 | MEDIUM | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0421 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0427 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0429 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0431 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0432 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0436 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0440 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0443 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0444 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0446 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0449 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0451 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0452 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0455 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0457 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0459 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0461 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0463 | c1 | LOW | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0464 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0465 | c1 | LOW | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0466 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0468 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0470 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0471 | c1 | CRITICAL | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0474 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0475 | c1 | CRITICAL | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0476 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0477 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0478 | c1 | CRITICAL | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0479 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0481 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0485 | c1 | CRITICAL | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0486 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0487 | c1 | CRITICAL | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0488 | c1 | CRITICAL | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0489 | c1 | HIGH | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0490 | c1 | HIGH | REMEDIATED-PENDING-W4 | (b,c) query_dasha_periods honors system_id + requested windows (F-0354/0471/0485); 8 systems / 437k dark rows unlocked |
| F-0492 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0493 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0494 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0495 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0496 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0500 | c1 | HIGH | W1-FOLLOWUP | no apex/synthesized assessor for vidya/spirituality/education — synthesis-layer gap (WP-1.4 synthesis scope), not a W1-serving lane |
| F-0503 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0507 | c4 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0511 | c4 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0516 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2α/β, in-wave) ranked-surface hydration + salience/attribution fix — empty top_signals / content now populated (LCA-9b/LCA-18c) |
| F-0519 | c4 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0525 | c4 | HIGH | REMEDIATED-PENDING-W4 | (a) query_convergence_windows exposes kala_convergence (6484 rows) to the surgical wire; underlying activation-date ripeness (R-45) matures at WP-2.1/W2 |
| F-0526 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0528 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0531 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0533 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0535 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0536 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0538 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0539 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0541 | c1 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0543 | c1 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0545 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0549 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0564 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0569 | c4 | MEDIUM | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0573 | c1 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0576 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0579 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0582 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0583 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0584 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0586 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0587 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0591 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0592 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0596 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0597 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0598 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0599 | c1 | MED | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0600 | c1 | MED | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0601 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0603 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0607 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0608 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0610 | c4 | MED | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0611 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0612 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0613 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0615 | c1 | MED | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0616 | c1 | MED | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0623 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0624 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0627 | c4 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0628 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0630 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0632 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0633 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0635 | c4 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0636 | c1 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0637 | c1 | MED | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0638 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0641 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0642 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0643 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0645 | c4 | MED | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0647 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0650 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0658 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0660 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0662 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0663 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0665 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0668 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0669 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0670 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0671 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0672 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0673 | c1 | HIGH | REMEDIATED-PENDING-W4 | (f) query_chart_facts filters/pagination fix (LCA-3): varga rows exist in DB but tool returned facts:[] with nonzero returned_count — serving/filter bug addressed |
| F-0675 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0677 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0678 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0679 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0682 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0684 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0685 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0686 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0687 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0688 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0689 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0691 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0692 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0693 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0695 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0698 | c4 | HIGH | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0699 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0701 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0704 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0705 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0706 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0708 | c4 | MED | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0716 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0720 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0721 | c4 | MEDIUM | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0723 | c4 | LOW | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0725 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0726 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0727 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0731 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0732 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0733 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0734 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0735 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0737 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0741 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0744 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0746 | c1 | MEDIUM | W1-FOLLOWUP | foreign/relocation reading composable from raw bhava data but no named domain — serving-layer domain-taxonomy extension not scoped this wave |
| F-0747 | c1 | MEDIUM | W1-FOLLOWUP | foreign/relocation reading composable from raw bhava data but no named domain — serving-layer domain-taxonomy extension not scoped this wave |
| F-0751 | c1 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0752 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0753 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0754 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0767 | c4 | MEDIUM | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0769 | c4 | MEDIUM | REMEDIATED-PENDING-W4 | (i) apex/assess dedup + verdict_skeleton serving fix (LCA-11,R-40): restored params, lord bucket 0->42 parivartana, karaka/starvation fixed |
| F-0777 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0784 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0787 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0789 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0791 | c1 | MEDIUM | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0792 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0797 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0798 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0799 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0800 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0801 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0807 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0809 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0810 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0812 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0814 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0822 | c4 | HIGH | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0823 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0826 | c4 | MEDIUM | PENDING-W3 | (e) temporal-windows serving-half honors+echoes date params + honest-empty disclosure; full acceptance re-runs post-W3 with WP-2.1 writer activation-dates (R-45) |
| F-0830 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS ka_gochara / live-transit search sidecar (F-L10-011) — transit engine computes it but no MCP tool serves it yet; serving residual |
| F-0832 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS ka_gochara / live-transit search sidecar (F-L10-011) — transit engine computes it but no MCP tool serves it yet; serving residual |
| F-0833 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0834 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS ka_gochara / live-transit search sidecar (F-L10-011) — transit engine computes it but no MCP tool serves it yet; serving residual |
| F-0835 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0837 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0838 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0839 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0840 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0841 | c4 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0843 | c1 | LOW | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0844 | c1 | MEDIUM | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0845 | c1 | LOW | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0848 | c1 | LOW | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0849 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0850 | c1 | LOW | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0851 | c1 | MEDIUM | REMEDIATED-PENDING-W4 | (d) lel_query serves life_events (F-L10-021); LEL firewall opened |
| F-0852 | c1 | LOW | REMEDIATED-PENDING-W4 | (d) lel_query serves life_events (F-L10-021); LEL firewall opened |
| F-0853 | c1 | MEDIUM | REMEDIATED-PENDING-W4 | (d) lel_query serves life_events (F-L10-021); LEL firewall opened |
| F-0854 | c1 | LOW | REMEDIATED-PENDING-W4 | (d) lel_query serves life_events (F-L10-021); LEL firewall opened |
| F-0861 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0862 | c4 | MEDIUM | REMEDIATED-PENDING-W4 | (sibling WP-1.2α/β, in-wave) ranked-surface hydration + salience/attribution fix — empty top_signals / content now populated (LCA-9b/LCA-18c) |
| F-0864 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0867 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0870 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0872 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0875 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0876 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0878 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0881 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0882 | c1 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0890 | c4 | HIGH | PENDING-W2 | data-plane/writer gap or unmodeled-concept (unreachable-by-nonexistence / empty writer table / NULL columns / narration pending) — needs a W2 writer (WP-2.1/2.2/L5); not a serving fix |
| F-0911 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0912 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0916 | c4 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0939 | c1 | MEDIUM | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-0942 | c1 | HIGH | REMEDIATED-PENDING-W4 | (sibling WP-1.2β, in-wave) domain discrimination + new/corrected domains (moksha 4-8-12, education/vidya, character/buddhi, bhava→domain un-collapse, F-0756); 0% UNATTRIBUTED |
| F-L10-002 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) get_vastu_directions [ga_vastu, SERVE 40/40] |
| F-L10-003 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) get_yoga_firings [ga_yoga_firings, SERVE 50/56] |
| F-L10-004 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_cdlm_summary [bodha_cdlm_chart_summary, SERVE 5/5] |
| F-L10-005 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_cgm_motifs [bodha_cgm_motifs, SERVE 0/6; native 0 = known LCA-6/WP-2.2] |
| F-L10-006 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_cgm_paths [bodha_cgm_paths, SERVE 45/45] |
| F-L10-007 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_chart_gestalt [bo_chart_gestalt, SERVE 5/5] |
| F-L10-009 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_dasha_dossier [ka_avadhi, SERVE 1571/1585] |
| F-L10-010 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS: ka_dasha_kala live-compute wrapper (dasha-adjacent) — not yet served |
| F-L10-011 | c1 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS: ka_gochara live transit search sidecar — not yet served |
| F-L10-012 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_temporal_view un-stubbed [ka_kala_darshana, SERVE 750/750] |
| F-L10-014 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_convergence_windows whitelist-exposed [ka_sangam, SERVE 6484/2959] |
| F-L10-015 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_activation_waveform [ka_taranga, SERVE aggregate-default, drill-refuses 79k] |
| F-L10-016 | c1 | HIGH | PARKED | ka_tulana two-chart compare — no single-chart table; genuine DESIGN question (parked_pending_native_review) |
| F-L10-020 | c1 | HIGH | PENDING-W2 | ka_yojaka predicates — overlaps (e) windows-engine; activation dates NULL (WP-2.1 R-45) |
| F-L10-021 | c4 | CRITICAL | REMEDIATED-PENDING-W4 | (d) lel_query serves 57 life events [lel_events, 57/0] |
| F-L10-022 | c4 | HIGH | PENDING-W2 | mi_abhilekha — mimamsa_journal empty (writer, WP-2.2/L5) |
| F-L10-024 | c4 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS serving-bug: ph_pratikara/phala_mitigation rows EXIST 602/638, tool returns empty |
| F-L10-025 | c4 | HIGH | W1-FOLLOWUP | (a) NEXT-PASS serving-bug: ph_rectification rows EXIST 185, serving fix needed |
| F-L10-026 | c4 | HIGH | PENDING-W2 | ph_rectification non-discrim — scorer/algo defect (0/36 events), writer/L5 not serving |
| F-L10-027 | c1 | HIGH | REMEDIATED-PENDING-W4 | (a) query_spillover_cascades whitelist-exposed [ph_sankrama, SERVE 635/1265] |

---

*Reconciliation produced 2026-07-12 for the ND-W1.1 binding gate. Read-only against `deliverables/wp_coverage.jsonl`, `deliverables/findings.jsonl`, `REMEDIATION_RUN_LEDGER_v1_0.md` (§3 sub-lane records, §4 follow-ups, §5 27-asset table), and `git log main..integration/w1-serving-plane`. Every one of the 295 WP-1.3 findings carries exactly one disposition; 0 unreconciled → PASS.*