# Lane 2 — Evidence-Sufficiency shard 2-b6

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point scale), §4 (9-class taxonomy).
Mode: P-12 evidence-plan-then-acquire, deployed MCP connector (read-only).
Charts: A = `482012f1-710e-4a25-994a-93821f5871aa` (native Abhisek) · B = `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan).
Batch: D8, D9, E1, E2 × {narrow, broad} × {A, B} = 16 instances.

## Cross-cutting evidence-plane facts (apply to every row below)

- **assess_wealth / assess_career / get_domain_reading / get_signals / get_temporal_windows all prepend the SAME whole-chart `orientation_context` digest** (msr_signal_count 13364, 15 yoga / 22 dosha, weakest_graha Mercury, `top_signals: []` ALWAYS EMPTY, and an `UNATTRIBUTED` entity holding 299 signals as the #1 entity_profile). This is the R-44 / R-37 anchor pattern rediscovered: the single highest-ranked "entity" on every orientation is `UNATTRIBUTED` with 299 signals — DROWNED (class 7).
- **assess_wealth trim (BOTH charts):** `judgment_flags: ["response_still_over_40kb_budget_after_full_trim"]`; every `verdict_skeleton.top_10_composite[].summary` ends `…[truncated for budget]` (house/lord/citation detail cut mid-field); `trim_report` = "full trim_report omitted to fit budget". **trim_seen = TRUE.** Class 6 (UNUSABLE FORM) + class 5 (dishonest — advertises 10 signals but each is unreadable).
- **get_temporal_windows (chart A):** `activations: [], activation_count: 0, predicates: [], signal_id_refs: []` for the default forward year — EMPTY SHELL (class 4). No time-indexed evidence for any wealth/karma question via this tool.
- **phala_outlook (chart A):** 5 anchors total, domains = transition×4 + career×1. **NO wealth anchor, NO retirement anchor.** Horizon fixed 12 months. So no forward volatility/magnitude timing for wealth exists on the predictive surface either.
- **assess_wealth `content.activating_dasha`:** `activations_total_count: 0` — no dasha activation ties wealth signals to time. Volatility axis has no temporal substrate.
- **get_domain_reading(wealth) form:** returns `question_lenses` whose `ranked_signals` are **raw signal_id UUIDs + salience only, no text** (`signal_id_refs_total: 2003, signal_id_refs_capped: true`); text requires a chained drill to `query_signals`. Class 6 (IDs without text).
- **INCONSISTENT count (class 3):** orientation digest reports `msr_signal_count = 13364`; `get_chart_quality` scorecard reports `msr_signal_count = 66836` for the same chart/build. Two surfaces, same quantity, different value.
- **No wealth-magnitude quantum exists anywhere.** `get_chart_quality` returns a build-integrity scorecard (verification %, orphan-ref %), not a wealth level. assess_wealth returns a yoga list + convergence scores, never a magnitude estimate. E1 "magnitude" has no computed target concept — the consumer must translate "Dhana yogas present" → "magnitude" himself.
- Both charts A and B are structurally identical in served shape (assess_wealth B and kala_life_arc B verified parallel); yoga *content* differs (A: 15 yogas incl Anapha/Yuga/Sasa; B: 13 yogas, weakest_graha Saturn). Verdicts below therefore match per-variant across charts.

---

## D8 — retirement character

**Evidence plan (acharya krama):** (1) later-life dasha sequence (60s+, ~2044+) → `kala_life_arc_get` parvas + `get_dashas` future window; (2) 10th-house cessation / karma-nivritti + 12th-house withdrawal signals → `get_domain_reading(career)`, chart_facts 10th/12th; (3) time-indexed later-life windows → `get_temporal_windows`, `phala_outlook`.

**Acquired:** `kala_life_arc_get` (A) = 50 parvas, 1984→2054, incl. retirement-era: Rahu 2041-44 (peak), Jupiter 2044-47 (building), Saturn 2047-50 (peak), Mercury 2050-53, Ketu 2053-54 — each with `parva_quality` + `avg_effective_score` (chart-specific) but `theme_keywords` that are **canned per dasha-planet** (Jupiter always = expansion/wisdom/abundance; Saturn always = discipline/responsibility/delay), NOT derived from this native's karma houses. Overlapping parvas (e.g. parva 8 "Saturn 1991-2010" co-exists with parvas 7/9/10) muddy the arc. `phala_outlook` / `get_temporal_windows` give nothing at retirement horizon (12-mo cap / empty). No tool models "retirement" as a concept.

**Class-9 improvisations:** taxonomy→life-language translation "late-life parvas ⇒ retirement" (system has no retirement concept); method choice (which of MD/AD parva granularities is "retirement"); the generic per-planet keywords must be re-grounded to THIS chart by hand.

- **narrow (A,B):** INSUFFICIENT — a pointed "when/how does he retire, what is its character" needs 10th-cessation + 12th-withdrawal + karma read that no surface supplies; only generic dasha-keyword arcs are reachable.
- **broad (A,B):** SUFFICIENT-WITH-GAPS — the later-life parva quality/score arc supports a hedged "character of the later years" read, but with the generic-keyword + overlapping-parva caveats stated openly.

## D9 — parallel-income patterns

**Evidence plan:** (1) 11th/labha bhava — lord, occupants, aspects → `get_domain_reading(wealth)` labha lens, `query_chart_facts` 11th house; (2) multiple-income yogas (e.g. multiple 2nd/11th linkages, Rahu in 11th) → `assess_wealth` yoga list; (3) timing of secondary streams → dasha/temporal.

**Acquired:** No surface addresses "parallel / multiple income streams." `get_domain_reading(wealth)` exposes only `lens_count: 2` (`question_type: property` + one other) — no labha/income-stream lens. `assess_wealth` yoga list is undifferentiated (does not separate 11th-house gains from 2nd-house savings). To reach the 11th lord/occupants one must drop to raw `query_chart_facts` and improvise the whole "parallel income" synthesis with no governing method.

**Class-9 improvisations:** silent decomposition ("parallel income" → 11th-house strength + secondary-income yogas + concurrent-dasha overlap, none of which the system names); taxonomy translation (no "income stream" primitive exists); conflict adjudication if raw facts drilled.

- **narrow (A,B):** INSUFFICIENT — a specific "does he run parallel income streams, of what kind" has no reachable governed surface; only raw 11th-house facts via drill + full improvisation.
- **broad (A,B):** INSUFFICIENT — even the broad "income diversification character" cannot be composed at acharya grade from the wealth yoga list alone; the labha axis is not surfaced separately. (Not UNANSWERABLE-BY-DESIGN: 11th-house data exists in chart_facts — it is a retrieval/serving gap, class 1/8.)

## E1 — wealth magnitude [anchor]

**Evidence plan:** (1) Dhana yogas + their strength → `assess_wealth` verdict_skeleton; (2) 2nd/11th lord dignity + dhana-karaka (Jupiter) strength → chart_facts / ganita_strength; (3) any computed wealth-level/magnitude score → `get_chart_quality`, assess_wealth verdict; (4) activating dasha for magnitude timing.

**Acquired:** `assess_wealth` (A) top_10 = Dhana/nabhasa yogas (Yuga, Anapha, Kedara, Sasa, Shoola, Vasi, Gola) + kala_sarpa config rows; `house_analysis` (property lens), `karaka_analysis` (career×wealth cdlm linkage 2003 shared signals). **But every yoga summary is truncated mid-field** (`value_text=Anapha Yoga | classical_citations=[…]…[truncated for budget]` — cannot see which houses/lords form it), `activating_dasha` empty, and **no magnitude figure is computed anywhere** (get_chart_quality = build scorecard, not wealth level). Consumer must (class 9) translate "these yogas present" → a magnitude band with no governed scale.

**Class-9 improvisations:** taxonomy→life-language (yoga presence ⇒ magnitude band — no wealth-level primitive); method choice (which yogas dominate magnitude when summaries are truncated); papering over truncated yoga internals.

- **narrow (A,B):** INSUFFICIENT — "how much wealth / what magnitude" needs either a computed level or fully-readable dhana-yoga internals; the magnitude concept is uncomputed and the yoga detail is trim-truncated (class 6). Anchor R-class rediscovered.
- **broad (A,B):** SUFFICIENT-WITH-GAPS — presence of named Dhana yogas (Anapha etc. on A) + wealth convergence score supports a qualitative "materially prosperous, above-average" read, but the exact-magnitude gap and truncated yoga internals must be disclosed, not papered over.

## E2 — income / retention / volatility decomposition

**Evidence plan:** (1) income axis → 11th/labha strength; (2) retention axis → 2nd-house/dhana + savings/6th-8th loss balance; (3) volatility axis → dasha-by-dasha wealth trajectory + transit windows → `get_temporal_windows`, `phala_outlook`, `kala_life_arc`, `activating_dasha`.

**Acquired:** The system has NO decomposition primitive — `assess_wealth` returns one undifferentiated yoga list; income (11th) vs retention (2nd) is not separated on any served surface; **the volatility axis has NO temporal substrate reachable** (`get_temporal_windows` activations=[] EMPTY SHELL, `phala_outlook` has no wealth anchor, `activating_dasha` total_count=0). Consumer must silently split the question into 3 sub-questions and hand-map each to surfaces that mostly return nothing.

**Class-9 improvisations:** silent question decomposition (one question → income/retention/volatility, a split the system never performs); method choice per axis; adjudicating an empty temporal surface against a static yoga list.

- **narrow (A,B):** INSUFFICIENT — all three axes under-served; volatility has zero temporal evidence (class 4), income/retention not separable (class 1/8).
- **broad (A,B):** INSUFFICIENT — even a hedged 3-axis character read cannot honestly cover volatility (no time series) or separate income from retention; a composed answer would fabricate the missing axes.

---

## Rediscovered anchors (audit-of-the-audit)
- **R-44 / R-37 (DROWNED, class 7):** `UNATTRIBUTED` = top entity_profile with 299 signals on every orientation digest; `top_signals: []` always empty.
- **R-44c-class (UNUSABLE, class 6) + trim:** assess_wealth over-40kb even after full trim; verdict summaries truncated mid-field.
- **kala_activation EMPTY (R-45 class, class 4):** get_temporal_windows returns 0 activations forward-year.

trim_seen = TRUE (assess_wealth both charts).

---

## Addendum — independent re-acquisition pass (converges with above; adds receipts)

Independent P-12 re-run confirmed every verdict above. Additional receipts captured:

- **event_anchors (A, 2026–2033):** 4 anchors served (career, transition×2, health) — **NO wealth anchor, NO retirement anchor**; ALL magnitude="minor", ALL confidence=0.322 (identical-value wall). `dedup.duplicates_removed: 191`, note: "191 duplicate anchor row(s) collapsed at the TS serving boundary … true fix belongs in the Python ph_nimitta writer; out of scope for this TS-estate lane." Chart B: same shape, no wealth anchor, `duplicates_removed: 193`, several anchors also tied at 0.322. → class 7 DROWNED + class 5 honest self-described defect. Reinforces E1/E2/D8: predictive surface has no wealth-magnitude or wealth-volatility anchor at all.
- **assess_career (A):** structuredContent = **1.26 MB** (1,259,590 bytes), text suppressed to 107 bytes. Extreme un-budgeted structured dump (class 6, R-44c analog) — magnitude beyond even assess_wealth's 220 KB.
- **assess_wealth.varga_analysis (A):** only a drill-pointer note ("Varga refinement (D9/D10/D6) available via chart_facts_query with divisional_chart filter", `drill_uri: marsys://tool/L1/chart_facts_query`) — D9 (dhana varga) / D10 not served inside the wealth verdict. Class 4 EMPTY SHELL + class 9 undocumented chained call. Directly starves E1/D9 (the divisional wealth read must be hand-assembled).
- **assess_wealth.karaka_analysis (A):** returns CDLM domain×domain linkage cells (career×wealth shared_signal_count=2003; relationship×wealth 1929) — **NOT the dhana-karaka (Jupiter) / 2L / 11L dossier**. Mislabeled surface + Mercury-standard depth gap: no karaka strength/avastha/dispositor dossier reaches the consumer for the wealth verdict.
- **get_signals(wealth, A):** signals DO resolve to `signal_headline_text`/`signal_summary_text` (good, unlike domain-reading lenses), but top-7 share identical salience **0.4888** and are all pan-domain nabhasa yogas (5 domains each), then descriptive trivia (kala_sarpa=none, aspect house4=1, ashtakavarga bindu=2) at salience 2.3. `provenance.signature_tier`: chart_defining=1.6%, supporting=83.3% — the wealth top-K is "supporting" trivia, not chart-defining dhana findings. class 7 DROWNED reconfirmed.
- **get_signals provenance honesty (positive):** `defect_001` = RESOLVED (0/10 orphan constituent_facts on chart A) — an honest, but **expiring** receipt (`expires_on: 2026-07-13`).

Verdicts unchanged: D8 narrow INSUFFICIENT / broad SUFFICIENT-WITH-GAPS; D9 narrow+broad INSUFFICIENT; E1 narrow INSUFFICIENT (anchor) / broad SUFFICIENT-WITH-GAPS; E2 narrow+broad INSUFFICIENT. Both charts identical in served shape.
