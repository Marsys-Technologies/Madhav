# Ω7 — Dark-Corpus Report (Elevation Campaign v2.1, Stream γ · PŪRṆA)

*Generated 2026-07-25T07:51:42.908789Z · target chart `482012f1-710e-4a25-994a-93821f5871aa` (native — Abhisek Mohanty)*

> **What this measures.** Of every concept the instrument *computes and stores non-empty* for this chart in a flagship domain, how many were **never surfaced** across a fresh execution of the FROZEN dark-corpus replay set (naive + narrow + expert phrasings) through the sealed evaluator harness. This is the direct measurement of the native's ~20% unknown-unknown. **Target: zero.** A dark concept = computed, non-empty, and still not served.

## Headline

| Domain | Served (non-empty) | Dark | Bright | Coverage | Replay runs |
|---|---|---|---|---|---|
| **wealth** | 12,450 | **11,755** | 695 | 5.58% | 21/21 |
| **career** | 12,455 | **11,400** | 1,055 | 8.47% | 21/21 |

The dark count is an **upper bound** (see method): composed-reading tools emit prose that may carry a concept's substance without its fact_id/token, so true coverage is ≥ reported. Even so, the signal is unambiguous — a naive→expert answer corpus surfaces only a few percent of what the instrument holds. The number is honest and is meant to trend toward zero across campaign iterations.

## Wealth — dark-corpus breakdown

- **Served universe (non-empty for this chart):** 12,450
- **Dark:** 11,755  ( tool-never-called 1,351 · substance-absent 10,404 )
- **Bright (surfaced ≥1×):** 695  (5.58% coverage)
- **Replay coverage:** 21/21 questions ran with ≥1 live chart-tool call.
- **Tools the corpus actually called:** Bash, ToolSearch, assess_wealth, chart_snapshot, ganita_chart_facts_get, ganita_dasha_lord_capability_get, ganita_dasha_periods_get, ganita_dashas_get, ganita_positions_get, ganita_special_lagnas_get, ganita_strength_get, ganita_structural_get, ganita_yoga_firings_get, graha_portrait, judgment_query, phala_outlook_get, reading_notes_get

**Dark by layer:**  l1=10,360 · l2=1,277 · l3=77 · l4=24 · l5=17

**Dark by serving tool (top 12):**

| serving tool | dark concepts |
|---|---|
| `ganita_chart_facts_get` | 10,328 |
| `bodha_signals_get` | 1,227 |
| `ganita_dashas_get` | 40 |
| `ganita_positions_get` | 32 |
| `bodha_graph_traverse_get` | 22 |
| `kala_windows_get` | 20 |
| `mimamsa_insight_get` | 14 |
| `bodha_graph_subgraph_get` | 10 |
| `phala_anchors_get` | 9 |
| `bodha_discoveries_get` | 7 |
| `kala_yoga_activation_get` | 6 |
| `gochara_forecast_get` | 5 |

**Dark by concept family (top 15) — the actionable slice:**

| concept family | dark |
|---|---|
| `l1.fact` | 10,328 |
| `l2.msr_signal_type` | 1,195 |
| `l3.dasha_level` | 32 |
| `l1.varga` | 32 |
| `l2.msr_signal_class` | 19 |
| `l2.cgm_edge_relclass` | 11 |
| `l2.cgm_edge_type` | 10 |
| `l3.kala_avadhi_quality` | 10 |
| `l4.phala_anchor_event` | 8 |
| `l3.dasha_system` | 8 |
| `l2.msr_signature_class` | 7 |
| `l2.cgm_node_type` | 7 |
| `l2.msr_tradition` | 6 |
| `l3.kala_activation_sig` | 6 |
| `l5.insight_type` | 6 |

Full dark + bright concept_id lists: `DARK_CORPUS_wealth_482012f1_concepts_v1_0.json`

## Career — dark-corpus breakdown

- **Served universe (non-empty for this chart):** 12,455
- **Dark:** 11,400  ( tool-never-called 1,369 · substance-absent 10,031 )
- **Bright (surfaced ≥1×):** 1,055  (8.47% coverage)
- **Replay coverage:** 21/21 questions ran with ≥1 live chart-tool call.
- **Tools the corpus actually called:** assess_career, assess_career (jq-extracted from saved file), bodha_domain_reading_get, bodha_mechanisms_get, ganita_chart_facts_get, ganita_dasha_lord_capability_get, ganita_dasha_periods_get, ganita_positions_get, ganita_sade_sati_get, ganita_strength_get, ganita_structural_get, ganita_yoga_firings_get, graha_portrait, judgment_query, kala_life_arc_get, kala_windows_get, query, synth_tail_divergence_get

**Dark by layer:**  l1=10,006 · l2=1,276 · l3=75 · l4=25 · l5=18

**Dark by serving tool (top 12):**

| serving tool | dark concepts |
|---|---|
| `ganita_chart_facts_get` | 9,974 |
| `bodha_signals_get` | 1,227 |
| `ganita_dashas_get` | 41 |
| `ganita_positions_get` | 32 |
| `bodha_graph_traverse_get` | 22 |
| `kala_windows_get` | 18 |
| `mimamsa_insight_get` | 15 |
| `bodha_graph_subgraph_get` | 10 |
| `phala_anchors_get` | 10 |
| `bodha_discoveries_get` | 7 |
| `kala_yoga_activation_get` | 6 |
| `gochara_forecast_get` | 5 |

**Dark by concept family (top 15) — the actionable slice:**

| concept family | dark |
|---|---|
| `l1.fact` | 9,974 |
| `l2.msr_signal_type` | 1,195 |
| `l3.dasha_level` | 32 |
| `l1.varga` | 32 |
| `l2.msr_signal_class` | 19 |
| `l2.cgm_edge_relclass` | 11 |
| `l2.cgm_edge_type` | 10 |
| `l3.dasha_system` | 9 |
| `l3.kala_avadhi_quality` | 9 |
| `l4.phala_anchor_event` | 8 |
| `l2.msr_signature_class` | 7 |
| `l2.cgm_node_type` | 7 |
| `l2.msr_tradition` | 6 |
| `l3.kala_activation_sig` | 6 |
| `l5.insight_type` | 6 |

Full dark + bright concept_id lists: `DARK_CORPUS_career_482012f1_concepts_v1_0.json`

## Method (faithful to the sealed evaluator harness)

Fresh general-purpose sub-agent per replay question, sealed-harness system framing (SEALED_EVALUATOR_HARNESS_v1_0.md #1): no charter text, no EL vocabulary, no concept names, no mention of dossier/Lane-Omega. One user turn per run; the agent chose its own tools. A methodologically-neutral tool-access + transcript-capture instruction was appended (plumbing only) — see deviations.

**Matching rule.** Faithful to the harness grader: each served concept maps to one serving tool + sample fact_ids + a distinguishing concept token. A concept is BRIGHT iff, across the UNION of all replay transcripts, its serving tool was actually called AND (one of its sample fact_ids appears verbatim in that tool's raw result OR its distinguishing token appears in that result). Else DARK. Two dark sub-reasons: tool_never_called (serving tool absent from the entire corpus) and substance_absent (tool called but concept substance never surfaced).

**Bias direction.** Conservative toward OVER-reporting dark: fact_id evidence is only 3 samples per concept, and composed-reading tools (assess_*, judgment_query) emit prose that may carry a concept's substance without its fact_id or exact token. So the true bright set is >= reported; the dark count is an UPPER bound. This matches Omega-7's intent (silent omission is a build failure — err toward flagging, not hiding).

## Deviations from the sealed harness (declared, per §0 no-silent-omission)

- No Agent-SDK transcript interceptor was available, so each consumer wrote its own tool-call log (tool, arguments, result_raw verbatim) to a file rather than the harness capturing it externally. The capture instruction reveals nothing about what is measured (no concept/dossier vocabulary).
- A neutral tool-access note (the chart tools are under mcp__marsys-jis-direct__ and need no auth) was appended after an early run (DC-W-09 first attempt) failed by confusing the auth-gated claude.ai MARSYS-JIS connector with the working direct namespace. Note names a spread of example tools, not a routing hint.
- Second chart 1c826d5a NOT executed (time budget) — see coverage.chart_1c826d5a_status.

## Coverage / what is NOT covered

- **chart_482012f1_status:** EXECUTED (both flagship domains)
- **chart_1c826d5a_status:** NOT EXECUTED — time budget; queued for next Omega-7 iteration

---

# ADDENDUM (2026-07-28) — Post-PARIŚODHANA re-measurement, both charts

*Appended, not a rewrite of the section above, which stands as the historical pre-campaign record. This addendum answers PARIŚODHANA B2 sub-problem #3: re-run the dark-corpus measurement against the current deployed head (all PARIŚODHANA PRs merged, amjis-web/amjis-mcp redeployed and confirmed current as of this session) and close the never-run chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` gap flagged in `PARISHODHANA_RECONCILIATION_v1_0.md` item T1-2.*

## What was run, honestly

**Step 1 — denominator regeneration: DONE, against a live DB.** A working Postgres connection was available this session (`127.0.0.1:5433/amjis` via the Cloud SQL Auth Proxy already running locally). `platform/scripts/census/generate_completeness_accounting.mjs` (unmodified) was executed live against both canonical charts, both domains:

| domain | chart | served (regenerated) | served (stale, 2026-07-25) | delta |
|---|---|---|---|---|
| wealth | 482012f1 | 12,450 | 12,450 | 0 |
| career | 482012f1 | 12,455 | 12,455 | 0 |
| wealth | 1c826d5a | 12,203 | 12,203 (existed, never consumed) | 0 |
| career | 1c826d5a | 12,207 | 12,207 (existed, never consumed) | 0 |

The served-universe denominator is **unchanged** for all four (domain, chart) pairs. This is expected and is itself a useful confirmation: PARIŚODHANA's B1/B2 fixes were serving-layer/registry changes (e.g. Ω8 floor-wiring into `registry_data.ts`), not L1–L5 data-pipeline rebuilds, so the underlying computed/stored substance for each chart should not have moved, and it didn't. One honest side-finding from the regeneration: the freshly-computed `COMPLETENESS_ACCOUNTING_SUMMARY_v1_0.json` now reports `evidence_ok:false` / `pass:false` for all four accountings (11–19 `unresolved_served_count` rows each, reason `value_not_found_in_db`) where the stale 2026-07-25 summary reported `pass:true`. This is a small (<0.15% of rows) resolver-evidence gap, not a served-count regression — flagged here per no-silent-omission, not fixed (out of this task's measurement-only scope). Updated accounting files are committed alongside this addendum.

**Step 2 — sealed-harness replay: SAMPLED, not full 21/21, on BOTH charts.** Cost/time budget did not permit the full 84-run matrix (21 wealth + 21 career questions × 2 charts). **5 of 21 questions per domain were run, per chart — a 24% sample, stratified across phrasing bands (2 naive + 2 narrow + 1 expert)**: `DC-W-01, DC-W-05` (naive), `DC-W-09, DC-W-13` (narrow), `DC-W-16` (expert); `DC-C-01, DC-C-05` (naive), `DC-C-09, DC-C-13` (narrow), `DC-C-16` (expert). This is **20 fresh general-purpose sub-agent runs total** (5 questions × 2 domains × 2 charts), each a new agent instance with no memory of the others, given the sealed-harness persona from `SEALED_EVALUATOR_HARNESS_v1_0.md` §1 verbatim as its task framing (chart tools under `mcp__marsys-jis-direct__*`, one user question, answer directly, then write its own tool-call log). **This is NOT a 21/21 replay and is not reported as one anywhere below.**

Declared deviation beyond the original run's own list: the consumer here is Claude Code's `general-purpose` subagent given the sealed persona as task instructions, not a raw system-prompt override (no interceptor for that exists in this harness) — the same structural deviation the original run already declared for its own consumers. All 20 raw transcripts are committed at `evals/omega7/harness_runs_remeasure_482012f1/` and `evals/omega7/harness_runs_remeasure_1c826d5a/` (`DC-{W,C}-{01,05,09,13,16}.json`). One transcript (`DC-C-05.json`, chart 482012f1) had a minor trailing-JSON glitch; the sealed matcher's own regex-recovery fallback ingested it without modification (logged as `INFO: regex-recovered`).

**Step 3 — scoring: `evals/omega7/build_report.py` and `evals/omega7/darkcorpus_match.py`, BOTH UNMODIFIED.** `build_report.py` is hard-coded to `chart8 = '482012f1'` (line 119) — it cannot target the second chart without a code edit, which is out of scope for a measurement session. It was run as-is against the primary chart to confirm reproducibility (numbers below match its stdout exactly). For chart `1c826d5a`, `darkcorpus_match.py` — the actual sealed grader `build_report.py` calls internally, and itself a generic `(accounting_path, run_glob, dump_path)` CLI, not chart-specific — was invoked directly with that chart's accounting file, exactly per its own documented interface. Neither sealed file was edited.

## Headline — new numbers, both charts, sample-based

| Domain | Chart | Served | Bright | Dark | Coverage | Replay sample |
|---|---|---|---|---|---|---|
| wealth | 482012f1 | 12,450 | 89 | 12,361 | **0.71%** | 5/21 |
| career | 482012f1 | 12,455 | 125 | 12,330 | **1.00%** | 5/21 |
| wealth | 1c826d5a | 12,203 | 80 | 12,123 | **0.66%** | 5/21 |
| career | 1c826d5a | 12,207 | 363 | 11,844 | **2.97%** | 5/21 |

Chart `1c826d5a` now has its **first-ever** dark-corpus measurement on record — the gap named in `PARISHODHANA_RECONCILIATION_v1_0.md` T1-2 / A8's "Second chart coverage" row is closed for this sample size. There is no prior baseline for this chart to compare against; these four numbers stand on their own.

## The comparison that actually matters: same 5 questions, before vs. after deploy

The 5.58%/8.47% baseline in the section above was measured over a **full 21/21** replay; a 5-question sample will structurally always score lower than a 21-question union run, because `bright` accumulates across the *union* of every transcript in the corpus — that is a sample-size artifact, not evidence about the deploy. To isolate the actual pre/post-deploy effect, the sealed matcher was re-run on chart 482012f1 over the **exact same 5 question IDs**, using the *original, archived, pre-deploy* transcripts already committed at `evals/omega7/harness_runs/`:

| Domain | Same 5 IDs, pre-deploy transcripts | Same 5 IDs, post-deploy transcripts (this session) | Full 21/21, pre-deploy (stale baseline) |
|---|---|---|---|
| wealth | bright 506 / 4.06% | bright 89 / 0.71% | bright 695 / 5.58% |
| career | bright 1,048 / 8.41% | bright 125 / 1.00% | bright 1,055 / 8.47% |

Read at face value this looks like a large regression. **It almost certainly is not one, and reporting it as one would be dishonest** — the mechanism is visible in the transcripts themselves, not inferred: the pre-deploy DC-W-01 transcript called `ganita_chart_facts_get` directly (a raw L1-fact-dump tool whose results carry literal `fact_id`s the matcher can string-match), while this session's fresh DC-W-01 agent answered the same question via `assess_wealth` / `judgment_query` / `bodha_domain_reading_get` — composed, prose-synthesizing tools that (per the harness's own declared bias direction) can carry a concept's substance without its exact fact_id or token ever appearing verbatim in the result. The pre/post-deploy same-5-question drop tracks almost exactly with the old-run's heavy `ganita_chart_facts_get` usage (1,044–1,048 of its bright hits are `l1.fact` concepts from that one tool) versus this session's agents leaning on synthesis tools instead. Since PARIŚODHANA's own commits this cycle (`f9ee52b5` "substance-inline reading digest for assess_wealth/assess_career", `a854ca3c` T5 "compact dossier receipt") specifically enriched those composed tools' prose, a fresh agent now has less need to call the raw fact-dump tool to get a complete-sounding answer — which is a plausible improvement in what the *user* actually receives, even as it mechanically depresses this harness's literal fact_id/token-matching score. **This tension — richer prose vs. matchable literal tokens — is exactly the harness's own documented upper-bound bias (§Method, "Bias direction"), now visibly larger post-deploy than it was pre-deploy.** Disentangling "genuinely fewer concepts surfaced" from "same or more substance, harder for a mechanical string-matcher to detect" requires either a full 21/21 re-run on both tool-choice regimes or a substance-level (not token-level) grader — neither of which this session performed. This session does **not** conclude the deploy regressed coverage; it reports the honest, mechanically-measured number and names the confound.

## What this addendum does NOT claim

- Not a 21/21 replay on either chart — 5/21 per domain per chart, stratified, disclosed above.
- Not a verdict on whether PARIŚODHANA improved or regressed dark-corpus coverage — the same-5-question comparison surfaces a large raw-score swing with a plausible non-regression explanation (tool-choice, not substance), but this session did not run enough volume or a substance-level grader to adjudicate it either way.
- Not a fix — no code, registry, or served-tool changes were made in this session. `evals/omega7/darkcorpus_match.py`, `evals/omega7/build_report.py`, and the replay-set question list were run unmodified.

## Reproduce

```
DATABASE_URL=... node platform/scripts/census/generate_completeness_accounting.mjs
python3 evals/omega7/build_report.py evals/omega7/harness_runs_remeasure_482012f1 00_ARCHITECTURE/llm_consumption_audit/capability_map <out_dir>   # chart 482012f1, matches table above
python3 evals/omega7/darkcorpus_match.py 00_ARCHITECTURE/llm_consumption_audit/capability_map/COMPLETENESS_ACCOUNTING_wealth_1c826d5a_v1_0.json "evals/omega7/harness_runs_remeasure_1c826d5a/DC-W-*.json" <dump.json>   # chart 1c826d5a wealth
python3 evals/omega7/darkcorpus_match.py 00_ARCHITECTURE/llm_consumption_audit/capability_map/COMPLETENESS_ACCOUNTING_career_1c826d5a_v1_0.json "evals/omega7/harness_runs_remeasure_1c826d5a/DC-C-*.json" <dump.json>   # chart 1c826d5a career
```

Raw transcripts: `evals/omega7/harness_runs_remeasure_482012f1/DC-{W,C}-{01,05,09,13,16}.json`, `evals/omega7/harness_runs_remeasure_1c826d5a/DC-{W,C}-{01,05,09,13,16}.json` (20 files, committed). Concept dumps: `DARK_CORPUS_{wealth,career}_{482012f1,1c826d5a}_concepts_REMEASURE_2026_07_28_v1_0.json` (this addendum's own dumps — the original `DARK_CORPUS_{wealth,career}_482012f1_concepts_v1_0.json` files referenced above are untouched). Regenerated denominator: `COMPLETENESS_ACCOUNTING_*_v1_0.json` + `COMPLETENESS_ACCOUNTING_SUMMARY_v1_0.json` (updated in place; served counts unchanged, `generated_at` and evidence-resolution detail refreshed against the live DB).
