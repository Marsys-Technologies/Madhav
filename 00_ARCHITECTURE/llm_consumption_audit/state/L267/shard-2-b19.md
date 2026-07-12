# Lane 2 shard-2-b19 — Group L (Meta & whole-chart), L1–L4 × 2 variants × 2 charts

Charter §7.3 4-point scale. Deployed MCP (read-only). Charts:
- A = `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek)
- B = `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan)

## Cross-cutting envelope observations (apply to all rows)
- **Inert pagination / un-budgeted dumps:** every envelope returns `pagination:{offset:0,limit:0,total:null,next_cursor:null}` while large bodies are shipped: `kala_life_arc_get` ~34KB, `query_chart_facts(bhava)` ~115KB. No disclosed cap, no "more available" flag. Charter §7.1(3) budget-proportionality FAIL → class 6 candidate. **trim_seen = true** (undisclosed budgeting).
- **Text-channel stub:** `get_signals`, `query_chart_facts` return `content[0].text = "[large payload — see structuredContent; text duplicate suppressed per S3 serialization-tax fix]"` (95 bytes). A consumer reading the MCP text channel (the documented channel) gets a stub; real data only in `structuredContent`. Undocumented second-channel requirement → class 9 / class 6.
- **UNATTRIBUTED wall (R-44 rediscovery):** `get_chart_orientation`/`get_signals` top entity_profile = `UNATTRIBUTED`, signal_count 299 (A) / 298 (B), aggregate_score 64.6 (A) / 84.8 (B) — one bucket dwarfs every attributed graha (next entity aggregate <1.1). Class 7 DROWNED + unattributable.
- **contradiction_count = 0** on BOTH charts, in the digest AND in every `convergence_domains[].contradiction_count`. No chart has zero tensions — universal-zero = EMPTY SHELL (class 4). Directly kills L3.
- **Identical-score wall (tail):** `synth_tail_divergence_get` returns all tail signals at `computed_salience:0.575, salience_pctl:0`, all `dosha_label` — a flat wall, no discrimination.

## L1 — whole-life arc narrative
**Evidence plan (acharya needs, in order):** (1) structural anchor → `get_chart_orientation`; (2) the temporal arc itself → `kala_life_arc_get` (parva-by-parva daśā spine with narratives); (3) synthesis overlay → `synth_chart_brief_get` (maha brief); (4) timing texture → `get_dashas`/`kala_windows_get`.
**Acquired:** `kala_life_arc_get` (A 34KB / B 33KB) returns ordered parvas with `parva_quality`, `theme_keywords`, and per-parva `narrative.summary`. `synth_chart_brief_get`: `topics_covered:38`, domains career/family/transition/education/progeny/rel…, `calibration_mode:STRUCTURAL`. This IS a genuine whole-life-arc surface — the daśā spine is fully present and ordered.
**Gaps:** narratives are templated ("consolidating phase marked by expansion, wisdom. 901 high-convergence windows in this span") — the arc is daśā-only; no varga/transit texture woven in, and `high_convergence_count` is raw count trivia surfaced as narrative. Depth doctrine (Mercury-standard dossier) not met.
**Class 9:** LLM must translate `high_convergence_count`/`avg_effective_score` taxonomy → life-language (no governed mapping).
**Verdict:** narrow = SUFFICIENT-WITH-GAPS (arc composable, templated depth). broad = SUFFICIENT-WITH-GAPS (composable but cross-domain integration is LLM-improvised over a daśā skeleton).

## L2 — five strongest + five weakest promises ranked
**Evidence plan:** (1) ranked strengths → `get_chart_orientation.top_signals` + `ganita_yogas_get`; (2) full ranked signal set → `get_signals`; (3) weak side → `get_chart_quality.weakest_graha`, doshas, tail; (4) attribution → constituent_facts.
**Acquired:** `get_chart_orientation.top_signals` populated (salience-ranked) BUT top bucket is UNATTRIBUTED(299). `get_signals` default returns orientation digest with `top_signals: []` (empty in the signals tool itself — EMPTY-SHELL-ish; the ranked list only appears via orientation). Weakness side: only a single scalar `weakest_graha` (Mercury / Saturn) — no *five weakest* anything. There is **no "promise" surface** and no bipolar strongest↔weakest ranked list.
**Gaps:** "five weakest promises ranked" has no served surface — one weakest_graha ≠ five ranked weak promises. Strong side is drowned by the UNATTRIBUTED wall (class 7) and identical-salience walls.
**Class 9:** LLM must (a) *define* "promise" (yoga? bhāva kāraka? bhāvat-bhāvam?), (b) invert strengths to synthesize "weaknesses," (c) pick the ranking metric — all ungoverned.
**Verdict:** narrow = SUFFICIENT-WITH-GAPS (strongest composable from top_signals+yogas; weakest thin). broad = INSUFFICIENT (proper 5+5 ranked-with-attribution not composable; weak pole unserved, strong pole drowned).

## L3 — central tension / contradiction
**Evidence plan:** (1) system's own contradiction detector → orientation `contradiction_count` + per-domain; (2) divergent/opposing forces → `synth_tail_divergence_get`, `get_cgm_subgraph`; (3) free-form adjudication → `judgment_query`.
**Acquired:** `contradiction_count = 0` everywhere on both charts (EMPTY SHELL, class 4). `synth_tail_divergence_get` returns a flat 0.575/pctl-0 dosha wall — not "tensions," just low-salience doshas, no polarity. `judgment_query` **rejects** the whole-chart question: `{"ok":false,"error":"either domain or bhava is required"}` — the NL judgment interface cannot take a chart-level tension query.
**Class 9:** to answer at all, LLM must self-adjudicate benefic↔malefic juxtapositions and *manually decompose* the whole-chart question into per-domain judgment_query calls (silent decomposition + conflict adjudication — both ungoverned).
**Verdict:** narrow = INSUFFICIENT. broad = INSUFFICIENT. The one surface that answers it (contradiction machinery) is an empty shell; answer would be fabricated.

## L4 — notable ABSENCES (negative knowledge)
**Evidence plan:** (1) any negative-knowledge surface? scan orientation/quality; (2) absence flags → `query_chart_facts` (`absent_prerequisite_flag`); (3) anomalies → `bodha_discoveries_get`.
**Acquired:** No curated "notable absences" surface exists. `query_chart_facts(bhava)` carries a mechanical `absent_prerequisite_flag:"true"` on isolated special points (e.g. AGASTYA_SPHUTA longitude null) — narrow point-absence, not "missing yogas / empty houses / unfulfilled kārakas." `weakest_graha` is the only near-negative scalar. `bodha_discoveries` `distributional_anomaly` present but `non_obviousness_score:1, consequence_score:1` (R-37 trivia scoring). Negative knowledge is architecturally not computed as a served surface — the system emits only *present* signals.
**Class 9:** LLM must self-generate the full canonical checklist (all yogas/houses/kārakas an acharya weighs) and diff against present signals — ungoverned method + taxonomy→life-language.
**Root cause:** data-plane / UNREACHABLE-BY-NONEXISTENCE (charter §2.1) — curated absence surface never computed. Not UNANSWERABLE-BY-DESIGN (absences ARE in Jyotish scope).
**Verdict:** narrow = INSUFFICIENT. broad = INSUFFICIENT.
