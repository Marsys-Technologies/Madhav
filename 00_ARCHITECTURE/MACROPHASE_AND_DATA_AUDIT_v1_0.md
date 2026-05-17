---
artifact: MACROPHASE_AND_DATA_AUDIT_v1_0.md
canonical_id: MACROPHASE_AND_DATA_AUDIT
version: 1.0
status: CURRENT
authored_by: Claude (Cowork session — native-requested cross-cutting audit)
authored_at: 2026-05-17
session_role: cross-cutting audit (not a phase-execution session)
session_scope_class: read-only audit; no source-of-truth artifacts mutated
audit_method:
  doc:    "CLAUDE.md, CURRENT_STATE, MACRO_PLAN, ROOT_FILE_POLICY, GCS_LAYOUT, ONGOING_HYGIENE, CAPABILITY_MANIFEST"
  repo:   "git log + greps over platform/src/lib/{pipeline,retrieve,tools,schools,trace,audit,observatory}/ + migrations/"
  closes: "M2_CLOSE, M3_CLOSE, M4_CLOSE, M5_CLOSE, M8_CLOSE, M9_CLOSE plus M3B/M4A/B/C/M5C/D sub-phase closes"
  live:   "Cloud Run prod URL HTTP 401 (auth-gated, alive) — direct Cloud SQL probe NOT executed from sandbox (see §H)"
  evidence_floor: "Every claim in §B–§F carries a file path + line range or a M-CLOSE sealing block citation"
governing_policy:
  - "B.1 — Facts/Interpretation separation (this is interpretation: layer L0 governance)"
  - "B.3 — Derivation ledger (each finding cites its evidence)"
  - "B.10 — No fabricated computation"
  - "B.11 — Whole-Chart-Read discipline (analogue here: whole-system read before findings)"
  - "ROOT_FILE_POLICY — placed under 00_ARCHITECTURE/, not the project root"
audience:
  primary: "Abhisek Mohanty (native)"
  secondary: "Future Claude sessions doing M6 entry / pipeline rework / data-asset migrations"
purpose: >
  Single-document audit of where the MARSYS-JIS project actually stands, sliced four ways:
  (1) macrophase state M1–M10 — what is closed, in-flight, gated; (2) data-asset placement —
  what lives on GCP and what does not; (3) pipeline coverage — which tools the LLM-first
  planner can actually reach and which canonical assets are stranded; (4) SLA / retrieval
  health — what we can prove from observatory + audit telemetry. Closes with a prioritized
  remediation plan suitable for direct conversion into next-session execution briefs.
changelog:
  - v1.0 (2026-05-17): Initial audit, authored cross-session. State as of CURRENT_STATE
    changelog v5.16 (M9 CLOSED 2026-05-14, M10 INCOMING gated on acharya panel ≥3).
---

# MARSYS-JIS — Macrophase + Data Asset Audit v1.0

> "State as of 2026-05-17 — M9 just closed, M10 is gated on the acharya panel, M6 is the elephant in the room."

---

## §A — Scope, method, and what this audit is and is not

This audit answers four questions the native asked:

1. Between M1 and M10, what is completed, what is partially completed, what is left behind?
2. Are all data assets from these macrophases mirrored to the appropriate GCP storage?
3. Is the query pipeline efficiently and effectively leveraging those assets?
4. Are the retrieval mechanisms firing per SLA and providing the right context for the synthesis LLM?

**Method.** Forensic reading of (a) every M-CLOSE sealing artifact, (b) the active phase plan, (c) CAPABILITY_MANIFEST.json (160 entries; fingerprint at 2026-05-14T16:09:09Z), (d) GCS_LAYOUT_v1_0.md, (e) the pipeline code (`platform/src/lib/pipeline/`, `retrieve/`, `tools/`, `schools/`, `trace/`), (f) every relevant migration in `platform/migrations/` and `platform/supabase/migrations/`, and (g) the most recent committed answer-evaluation result (`platform/scripts/eval/results_gemini_baseline_20260511.json`).

**What this audit is NOT.** It is not a live production probe. The sandbox cannot reach Cloud SQL (no `gcloud`, no `cloud-sql-proxy`, no Application Default Credentials), and Terminal access on the user's machine is at tier "click" — keyboard input is blocked. Live row counts, current latency P50/P95/P99, and 7-day audit_events snapshots are therefore inferred from the most recent M-CLOSE artifacts (which captured live state at close) and the most recent committed eval log. §H names the live-probe items deferred to a follow-up session brief.

**Authoritative state pointer.** Per CLAUDE.md §F, the canonical state is `CURRENT_STATE_v1_0.md §2`. At audit time the §2 YAML block reads `active_macro_phase: M6` (line 3279), while the changelog v5.16 entry at the top of the same file says M9 CLOSED 2026-05-14 and M10 INCOMING. This is the first finding (F.GOV.1, §F.3).

---

## §B — Macrophase state matrix (M1–M10)

Per `MACRO_PLAN_v2_0.md §"The ten macro-phases"` + the M-CLOSE sealing artifacts. Times are absolute; cite §C of CLAUDE.md if a date looks wrong.

| Phase | Title | Status | Sealing artifact | Closed on | Key residuals |
|---|---|---|---|---|---|
| M1 | Corpus Completeness | **CLOSED** | implicit (no `M1_CLOSE_v1_0.md` file; closure declared in `MACRO_PLAN_v2_0.md §M1` and CURRENT_STATE narrative) | 2026-04-19 via GAP_RESOLUTION_SESSION + CLOSURE_AUDIT_PASS | none (eight exit-state items all ✓; v3.0 MSR @ 499 signals later superseded by M9's v5.0 @ 573 signals) |
| M2 | Corpus Activation | **CLOSED** | `00_ARCHITECTURE/M2_CLOSE_v1_0.md` v1.0 | 2026-05-01 at KARN-W8-R2-M2-CLOSE | none load-bearing — Audit 1 MSR→FORENSIC 98.99% PASS; Audit 2 UCN→MSR 95.52% PASS; IS.8 9-axis RT PASS |
| M3 | Temporal Animation / Discovery Layer | **CLOSED** | `00_ARCHITECTURE/M3_CLOSE_v1_0.md` v1.0 | 2026-05-01 at M3-W4-D2-M3-CLOSE | Chara/Narayana dasha computers `needs_verification` per DIS.010/011/012 N3 deferrals; Sthana + Drik shadbala tagged `[EXTERNAL_COMPUTATION_REQUIRED]` |
| M4 | Empirical Calibration | **CLOSED** | `06_LEARNING_LAYER/M4_CLOSE_v1_0.md` v1.0 | 2026-05-02 at M4-D-S1 | CF.LL7.1 = CLOSED_PARALLEL (M5 re-emit pending); R.LL1TPA.1 = FINAL_NOT_REACHABLE (Gemini gap); R.LL3.1/2/3 carry to M5 retrieval pipeline; per-edge LL.2 promotion carries M5+ |
| M5 | Probabilistic Model | **CLOSED** | `06_LEARNING_LAYER/M5_CLOSE_v1_0.md` v1.0 | 2026-05-14 at M5-E-S2 | LL.8 ACTIVE; LL.9 SCAFFOLD; PPL volume = 20 predictions (≥ 20 gate met). Six carry-forwards CF.M5D.1–6 all dispositioned. Bayesian framing in `predictive.ts` v3.0 |
| M6 | Prospective Testing | **NOT STARTED — TIME-GATED** | none | n/a | CW.PPL min-volume gate 50 predictions @ ≥6 mo horizon — currently 20 logged at M5 close. Earliest mechanically reachable: ~late 2026 (per project memory `project_current_phase_state.md`: "TIME-GATED ~2026-11-14"). No phase-plan authored. |
| M7 | Population Extension | **NOT STARTED — BLOCKED** | none | n/a | Entry requires (a) M6 closed AND (b) ethical/consent workflow operational. Neither condition met. No phase-plan; no IRB-style scaffolding. |
| M8 | Classical Text Cross-Reference | **CLOSED** | `08_CLASSICAL_CROSS_REFERENCE/M8_CLOSE_v1_0.md` v1.0 | 2026-05-14 at M8-H-S1 | CF.M8.1 Brihat Samhita 12 chunks not embedded (Vertex 20k limit); CF.M8.2 Jaimini DIS.010/011 N3-deferred; CF.M8.6 attribution coverage 76/543 signals (carry-forward expansion needed); CF.M8.7 PipelinePlanInputJsonSchema NIM-compat — classical_grounding not in §5 JSON schema yet |
| M9 | Multi-School Triangulation | **CLOSED** | `09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md` v1.0 | 2026-05-14 at M9-E-S1 | CF.M9.1 [VARSHA_KUNDALI_PENDING] (Tajika needs 2026 solar return via Swiss Ephemeris); CF.M9.2 [TRANSIT_DATA_PENDING] (BNN needs live 2026-05-14 transit positions); DB_SEED_DEFERRED + GCS_UPLOAD_DEFERRED (proxy unavailable at close); **runtime wiring incomplete — see F.PIPE.1 §F.4** |
| M10 | LLM-Acharya Interface | **NOT STARTED — GATED** | none | n/a | Entry condition: M9 CLOSED (MET) AND acharya panel ≥3 recruited (UNMET — no recruitment work in repo). LL.10 fine-tune corpus not assembled. Publication venue not selected. |

**Read-through.** Seven of ten macrophases sealed (M1–M5, M8–M9). Two waiting on real-world clock (M6 = elapsed time for prediction windows to close) or human inputs (M7 = consent infrastructure + cohort; M10 = acharya recruitment). Zero phases "stuck" technically — but a fair amount of in-phase carry-forward debt has accumulated and is concentrated in three places: (i) classical attribution coverage 76/543 signals (M8), (ii) M9 runtime wiring (§F.4), and (iii) M5 deferred re-runs that depend on Gemini access never restored.

A more visual rendering of the same matrix is at the end of this section. See `MACRO_PLAN_v2_0.md §"The ten macro-phases"` for the full per-phase exit-state inventory.

```
M1 ✅ ── M2 ✅ ── M3 ✅ ── M4 ✅ ── M5 ✅ ─┬─ M6 ⏳ (time-gated, 30/50 predictions short)
                                          ├─ M8 ✅ ── M9 ✅ ── M10 🚪 (acharya panel ≥3)
                                          └─ M7 🚪 (M6 + consent infra)
```

---

## §C — Data-asset placement matrix

Three axes per asset: (a) does the canonical artifact exist on disk per `CAPABILITY_MANIFEST.json`? (b) is the GCS mirror declared in `GCS_LAYOUT_v1_0.md`? (c) is there evidence it was actually uploaded? Empty cells mean the answer is no.

### §C.1 — L1 facts layer

| Asset | canonical_id | On disk | GCS path declared | GCS upload confirmed | Notes |
|---|---|---|---|---|---|
| FORENSIC chart v8.0 | `FORENSIC` | ✅ `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | ✅ `gs://madhav-marsys-sources/L1/facts/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | uncertain — manifest has no `gcs_uri` field (F.GOV.2) | Authoritative chart |
| Life Event Log v1.2 | `LEL` | ✅ `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | ✅ `gs://madhav-marsys-sources/L1/facts/LIFE_EVENT_LOG_v1_2.md` | uncertain (same) | 36 events + 5 period summaries + 6 chronic patterns |
| SADE_SATI_CYCLES_ALL | `SADE_SATI_CYCLES_ALL` | ✅ `01_FACTS_LAYER/SADE_SATI_CYCLES_ALL.md` | ✅ `gs://madhav-marsys-sources/L1/facts/` | uncertain | |
| EXTERNAL_COMPUTATION_SPEC v2.0 | `EXTERNAL_COMPUTATION_SPEC_v2_0` | ✅ | ✅ same path family | uncertain | |
| CGP_AUDIT v1.0 | `CGP_AUDIT_v1_0` | ✅ | ✅ same path family | uncertain | |
| **Ephemeris** EPHEMERIS_MONTHLY_1900_2100.csv | none | ❌ **not generated** | declared in GCS_LAYOUT as `L1/ephemeris/` | ❌ GAP.L1.01 — sync skips non-existent | **F.DATA.1** |
| **Ephemeris** ECLIPSES_1900_2100.csv | none | ❌ | declared | ❌ | F.DATA.1 |
| **Ephemeris** RETROGRADES_1900_2100.csv | none | ❌ | declared | ❌ | F.DATA.1 |
| EVENT_CHART_STATES v1.0 | `EVENT_CHART_STATES_v1_0` | ✅ `01_FACTS_LAYER/SOURCES/` | ✅ `L1/sources/` | uncertain | |
| JHORA_TRANSCRIPTION_v8_0_SOURCE | `JHORA_TRANSCRIPTION_v8_0_SOURCE` | ✅ | ✅ | uncertain | |
| **L1 Postgres tables** — ephemeris_daily, eclipses, retrogrades, sade_sati_phases, chart_facts | n/a | n/a | n/a | migration files present (015, 016, 017, 014, 029) | Live-probe required to confirm row counts |

### §C.2 — L2.5 holistic synthesis layer

| Asset | canonical_id | Manifest version | GCS path | Notes |
|---|---|---|---|---|
| Master Signal Register | `MSR` | **v5.0 / 573 signals** (M9-A added 30 Yogini + Tajika signals on top of M8-F's v4.0 / 543) | `gs://madhav-marsys-sources/L2_5/MSR_v5_0.md` (M9-A added) | Manifest path field still points to `MSR_v5_0.md` ✅. Earlier manifest pointer fixes in canonical-id frontmatter project memory `project_canonical_id_fix.md`. |
| Unified Composite Narrative | `UCN` | v4.1 | `gs://madhav-marsys-sources/L2_5/UCN_v4_0.md` | filename version drift — see F.GOV.3 |
| Cross-Domain Linkage Matrix | `CDLM` | v1.3 (M4-D-P1 patch landed) | `gs://madhav-marsys-sources/L2_5/CDLM_v1_1.md` | filename version drift — see F.GOV.3 |
| Resonance Matrix | `RM` | v2.2 | `gs://madhav-marsys-sources/L2_5/RM_v2_0.md` | filename version drift |
| Chart Graph Model | `CGM` | v9.1 | `gs://madhav-marsys-sources/L2_5/CGM_v9_0.md` | filename version drift |
| Red Team L2.5 | `RED_TEAM_L2_5_v1_0` | 1.0 | `L2_5/RED_TEAM_L2_5_v1_0.md` | |

### §C.3 — L3 discovery + domain reports

Discovery registers (PATTERN, RESONANCE, CONTRADICTION, CLUSTER) plus INDEX.json — all declared `gs://madhav-marsys-sources/L3/registers/`. Nine L3 Domain Reports at v1.1+ all on local disk; not declared in GCS_LAYOUT (this is by design — domain reports are read from local Postgres tables, not GCS).

### §C.4 — L8 classical corpus (M8 product)

Per the `M8_CLOSE` AC ledger and `gs://madhav-marsys-sources/L8/`:

| Tier | Texts | Chunks | Embedded | GCS confirmed |
|---|---|---|---|---|
| Tier 1 | BPHS, Phaladeepika | 1032 + 926 = 1958 | 100% | ✅ `L8/classical_texts/tier1/` |
| Tier 2 | Saravali, Uttara Kalamrita, Jaimini Sutra | 796 + 239 + 181 = 1216 | 100% | ✅ `L8/classical_texts/tier2/` |
| Tier 3 | Prashna Marga, Hora Sara, KP Vols.1-4, Brihat Jataka, Brihat Samhita | 758 + 295 + 1646 + 520 + 757 = 3976 | 100% except Brihat Samhita 98.4% (12 chunks > Vertex 20k limit — **CF.M8.1**) | ✅ `L8/classical_texts/tier3/` |
| Tier 4 | Bhrigu Nandi Nadi, Chandra Kala Nadi, Dhruva Nadi sampler | 391 + 658 + 150 = 1199 | 100% | ✅ `L8/nadi_bnn/` |
| **Total** | **13 texts** | **8349 chunks** | 99.86% | ✅ |
| **Attribution** | 420 rows in `classical_attributions` (confirms: 21, contradicts: 8, extends: 10, partial: 64, silent: 317) | covers **76 of 573 signals** — **CF.M8.6** | n/a | `L8/registries/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.{md,json}` |

### §C.5 — L9 multi-school triangulation (M9 product)

Per `M9_CLOSE` AC ledger + `gs://madhav-marsys-sources/L9/`:

| Asset | Path | Upload status |
|---|---|---|
| Per-school analyses (7 files: parashari, jaimini, tajika, kp, nadi, bnn, yogini) | `L9/school_analyses/<school>_analysis.json` | **DEFERRED — GCS_UPLOAD_DEFERRED at M9-C-S1 / M9-D-S1 / M9-E-S1 due to proxy unavailable** |
| `convergence_scores.json` | `L9/convergence/convergence_scores.json` | **DEFERRED** |
| `school_disagreement_register.json` | `L9/convergence/school_disagreement_register.json` | **DEFERRED** |
| Postgres tables `school_signal_coverage`, `school_analysis_runs`, `convergence_scores`, `school_disagreements` (migrations 057–060) | live | **DB_SEED_DEFERRED at M9-A-S1 and M9-C-S1** — schema present, rows defined in scripts but never written |

This is **F.DATA.2** — M9 produced 5 of its primary outputs but neither the JSONs nor the DB rows actually shipped. The analysis ran in memory only.

### §C.6 — L6 learning layer (M4 + M5 product)

| Asset | Path | GCS? |
|---|---|---|
| LL.1 signal-weight calibration tables | `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/` | not in GCS_LAYOUT (per §C.6 of GCS_LAYOUT: "L5 / 06_LEARNING_LAYER/ is not included in this bucket in Phase 14A. Learning Layer sync scope is a separate decision.") |
| LL.2 graph edge weights | `06_LEARNING_LAYER/` shadow files | not in GCS |
| DBN topology + params | `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md`, `prior_spec_v1_0.md`, `dbn_params_v1_0.json` | not in GCS |
| Held-out validation | `06_LEARNING_LAYER/dbn/held_out_validation_v1_0.json` (5 events, mean_lift 1.145, beat_fraction 5/5) | not in GCS |
| LL.7 discovery prior (native-only mode) | `06_LEARNING_LAYER/signal_weights/shadow/ll7_discovery_prior_v1_0.json` | not in GCS |
| LL.8 ACTIVE parameter register | `06_LEARNING_LAYER/dbn/parameter_register.json` | not in GCS |

This is **F.DATA.3** — Phase 14A explicitly excluded L6, but the entire calibration substrate is now production-relevant (M5 closed, predictive.ts v3.0 reads dbn_params for posterior framing). Recovery requires a re-establishment of L6 ownership in the GCS plan, or an explicit decision that L6 stays disk-local indefinitely.

---

## §D — Pipeline coverage matrix

The query pipeline emits stages classify → compose_bundle → plan_per_tool → tool_fetch (×N) → synthesis → audit (per `platform/src/lib/trace/types.ts` STAGE_FROM_STEP_NAME and `consume/route.ts`). The **planner's** view of available tools is in `RETRIEVAL_CAPABILITY_SPEC` (`platform/src/lib/router/retrieval_capability_spec.ts`). The **runtime's** view of available tools is `RETRIEVAL_TOOLS` (`platform/src/lib/retrieve/index.ts`). These two registries are not in sync. The trace UI has a third registry (`ALL_21_RETRIEVAL_TOOLS` in `platform/src/lib/trace/types.ts`) which is also out of sync.

### §D.1 — Tool-registry drift (the headline pipeline finding)

| Tool | In `RETRIEVAL_TOOLS` (runtime — getTool dispatches here) | In `RETRIEVAL_CAPABILITY_SPEC` (planner sees this) | In `ALL_21_RETRIEVAL_TOOLS` (trace UI sub-rows) | Notes |
|---|:---:|:---:|:---:|---|
| msr_sql … timeline_query (18 base tools) | ✅ | ✅ | ✅ | The well-formed 18-tool baseline. |
| query_signal_state | ✅ | ❌ | ✅ | Planner cannot ask for it; trace UI shows it dimmed when not fired. |
| query_kp_ruling_planets | ✅ | ❌ | ✅ | Same. |
| query_varshaphala | ✅ | ❌ | ✅ | Same. |
| lel_query | ✅ | ❌ | ❌ | **The worst case** — runtime has it, trace UI doesn't know it exists, planner never selects it. |
| classical_text_search (Tool 25, M8) | ✅ | ✅ | ❌ | Planner + runtime aligned; trace UI sub-tool list out of date. |
| classical_attribution_lookup (Tool 26, M8) | ✅ | ✅ | ❌ | Same. |
| multi_school_signal_lookup (Tool 27, M9) | ❌ | ❌ | ❌ | **Implemented in `platform/src/lib/tools/`, registered in `CLASSICAL_TOOL_REGISTRY` constant — but no `RetrievalTool` wrapper in `platform/src/lib/retrieve/`. `consume/route.ts:619` does `getTool(toolName)` over `RETRIEVAL_TOOLS` and would return undefined; line 622 silently drops the tool. M9 close declared this PASS but the wiring lacks the wrapper pattern M8 used. F.PIPE.1.** |
| convergence_score_lookup (Tool 28, M9) | ❌ | ❌ | ❌ | Same diagnosis. F.PIPE.1. |

### §D.2 — Where each canonical asset surfaces

Tracing each L1/L2.5/L3/L8/L9 asset to the retrieval tool that exposes it:

| Asset | Retrieval tool | Coverage status |
|---|---|---|
| FORENSIC chart values | `chart_facts_query` (L1 chart_facts table) | ✅ planner + runtime |
| L1 ephemeris (dasha, transits, eclipses, retrogrades, Sade Sati) | `temporal` (660K-row ephemeris_daily + sidecars) | ✅ planner + runtime |
| KP sublord substrate | `query_kp_ruling_planets` | ⚠️ runtime-only (planner blind) |
| Varshaphala 78-year series | `query_varshaphala` | ⚠️ runtime-only |
| Signal state (lit/dormant/ripening at date) | `query_signal_state` | ⚠️ runtime-only |
| Life Event Log v1.2 | `lel_query` (M5-A) | ⚠️ **runtime-only AND trace-UI-blind** — planner cannot ground predictive responses in LEL events. The only path to LEL today is via the synthesis prompt template `predictive.ts` v3.0 calibration disclosure (n=37) which inlines the data. |
| MSR 573 signals | `msr_sql` | ✅ |
| Pattern / Resonance / Contradiction / Cluster | `pattern_register` / `resonance_register` / `contradiction_register` / `cluster_atlas` | ✅ |
| CGM 9.1 graph | `cgm_graph_walk` | ✅ |
| Domain reports (career, relationships, health, etc.) | `domain_report_query` | ✅ |
| Remedial codex | `remedial_codex_query` | ✅ |
| Timeline | `timeline_query` | ✅ |
| MSR cross-chart aggregation | `query_msr_aggregate` | ✅ (cross_native use) |
| Vector semantic search | `vector_search` | ✅ |
| Manifest meta-queries | `manifest_query` | ✅ |
| Divisional chart dignity | `divisional_query`, `cross_varga_dignity_query` | ✅ |
| Saham points | `saham_query` | ✅ |
| **L8 classical corpus** (BPHS, Phaladeepika, Saravali, etc.) | `classical_text_search`, `classical_attribution_lookup` | ✅ planner + runtime (M8-G wired correctly) |
| **L9 multi-school** (7-school analyses + convergence) | `multi_school_signal_lookup`, `convergence_score_lookup` | ❌ **not callable** — F.PIPE.1 |
| **LL.1 production weights** (signal-weight calibration) | applied inside `msr_sql` ranking | ✅ wired per PIV closeout 77f1cae "apply LL.1 production weights to MSR retrieval ranking" |
| **LL.7 discovery prior** | embedded as a relevance modifier inside discovery tools (?) | ⚠️ unverified — needs source-code read in `pattern_register.ts` etc. |
| **DBN posterior framing** | output-side via `predictive.ts` synthesis template | ✅ wired for predictive queries; needs `dbn_params_v1_0.json` to be present at runtime |

### §D.3 — Query-class coverage

Every QueryClass declared in `pipeline/types.ts` QueryClassEnum must have at least one tool that can fire for it. Verified from `consume/route.ts`:

| QueryClass | Tools selected by planner (golden examples) | Verdict |
|---|---|---|
| factual | msr_sql, chart_facts_query | ✅ |
| interpretive | msr_sql, cgm_graph_walk, pattern_register, resonance_register, contradiction_register | ✅ |
| predictive | temporal, msr_sql, **lel_query expected, not in planner catalog** | ⚠️ Predictive queries miss life-event grounding |
| discovery | pattern_register, resonance_register, contradiction_register, cluster_atlas, vector_search | ✅ |
| holistic | wide bundle — msr_sql + cgm_graph_walk + pattern/resonance + contradiction + cluster + domain_report_query | ✅ |
| cross_native | query_msr_aggregate, manifest_query | ✅ |
| classical_grounding (M8) | classical_text_search, classical_attribution_lookup | ✅ |
| multi_school_triangulation (M9) | multi_school_signal_lookup, convergence_score_lookup | ❌ **planner can classify it but cannot dispatch the tools — silent drop at `getTool` returning undefined.** |

---

## §E — Retrieval SLA and synthesis health

### §E.1 — Telemetry that exists

The observatory + trace stack is, on paper, comprehensive. Per migrations 020, 026, 032, 038, 040, 041, 042, 044, 045:

| Surface | What it captures | Where |
|---|---|---|
| `query_trace_steps` | per-step timing (latency_ms, started_at, completed_at), status, parallel_group, data_summary, payload, step_type ∈ {deterministic, llm, sql, vector, gcs} | migration 020 + 040 + 064 |
| `audit_events` | per-query: query_id, query_class, latency_ms, audit_status, audit_warnings, disclosure_tier, b10_compliant, b11_compliant | 026 + 045 (Gate II.5) |
| `llm_call_log` + `llm_usage_events` | per-LLM-call cost and token detail; decision_alternatives; prompt_template_id+version; FK to `llm_pricing_versions` | 032 + 038 + 040 |
| `tool_execution_log` | per-tool: raw_result_count, kept_result_count, dropped_items, kept_items, tool_input_payload, tool_output_summary, error_class | 034 + 040 + 042 |
| `context_assembly_item_log` | per-item rank, status ∈ {INCLUDED, TRUNCATED, DROPPED}, drop_reason ∈ {BUDGET_EXCEEDED, DEDUP, RELEVANCE_FLOOR} | 035 + 040 |
| `synthesis_quality_scorecard` | per-query checkpoint scores | 040 |
| `prediction_calibration` | per-prediction calibration evidence | 039 |
| `query_baseline_stats` mat view | aggregate baseline | 040 |
| `query_trace_steps_user_id` | enforces user attribution on every trace step | 064 (most recent migration) |

This is a complete instrumentation surface.

### §E.2 — Telemetry actually used

This audit could not pull live Postgres counts. Two pieces of evidence:

**(a) Project Ganga answer-evaluation baseline 2026-05-11** (`platform/scripts/eval/results_gemini_baseline_20260511.json` + `.log`). The 15-query golden set run against `https://amjis-web-938361928218.asia-south1.run.app` produced:

- **Queries run: 5 / 15 (10 SKIPPED — "fetch failed")** → 67% of the eval surface timed out or errored at fetch.
- Pass rate on the 5 that ran: 4 / 5 (80%).
- On passes: avg `layer_coverage = 73%`, `B10 = 100%`, `B11 = 80%`, `citations = 80%`, `calibration = 74%`.
- The 24-fixture aggregate from the same file: `mean_keyword_recall 0.7993`, `mean_signal_recall 0.8542`, `mean_synthesis 0.6808`, `mean_weighted 0.7231`.
- GQ-001 [factual] outright FAILED — 0% citations, 0% B11, 100% B10 on a factual query is a tooling fault, not a content fault.

The 10-of-15 skip rate is a hard SLA finding even if the 5 successful queries look good. Either production retrieval is timing out for entire query classes, or the golden eval client is racing against streaming responses. Both are F.SLA.1 candidates and both are remediable. Note that this baseline predates the AIOps Phase 2 + 3 merges (2026-05-14) and the Chat V2 ship (2026-05-16) — so the current state may be better, worse, or the same. Live re-run required.

**(b) M-CLOSE artifacts** captured live state at close. The most useful number: M8-E-S1 attribution engine ran 510 signals × 10 texts in 4 parallel workers with Vertex AI text-embedding-004 (768-dim) — embedding throughput was sufficient for the workload (no rate-limit errors recorded). M8-D-S1 noted 12 of 757 Brihat Samhita chunks exceeded Vertex 20k token batch limit (CF.M8.1, 1.6% loss).

### §E.3 — What can be said about latency and SLA without a live probe

Per `consume/route.ts` line 854–871 the trace emits stage-level latency rollups (`plannerLatencyMs`, `composeBundleMs`, `toolFetchMs`, etc.) on every query. Per migration 064 every trace step carries `user_id` — this is the enforcement column added in the most recent migration. Per `audit_events.latency_ms` (migration 026) the per-query end-to-end is recorded.

This is enough plumbing to answer "what is our P50/P95/P99 per stage?" with a single SQL query. That query has not been run (see §H).

### §E.4 — Where the synthesis LLM may be context-starved

Working from §D.2:

1. **LEL not available to planner.** Predictive queries that should ground "your last career inflection was 2008-06-09, Saturn dasha" cannot do so via the LLM-first planner. The synthesis template inlines aggregate stats (n=37 training events) but cannot cite specific events. **F.SYNTH.1**.
2. **M9 multi-school context never reaches synthesis.** Any query the planner classifies as `multi_school_triangulation` gets a silent drop on the tool fetch. Synthesis proceeds with whatever non-M9 tools fired. **F.SYNTH.2** (consequence of F.PIPE.1).
3. **Signal state, KP ruling planets, Varshaphala — runtime-only.** If the planner deems them relevant via heuristics it can't actually request them (they're not in `RETRIEVAL_CAPABILITY_SPEC`). The synthesis context is then missing for any query that needed temporal precision beyond `temporal`'s scope.
4. **L1 ephemeris coverage gaps** (GAP.L1.01 — ephemeris CSVs not generated). If `temporal` tool falls back to live computation it may still work; if it expects pre-materialized CSVs, queries hit a blind spot.
5. **L6 learning-layer artifacts disk-local only.** If Cloud Run cold-starts on a revision that doesn't bundle `dbn_params_v1_0.json` and `parameter_register.json`, the predictive synthesis template still emits the Bayesian framing but with `[CALIBRATION_REQUIRED]` markers — an output-quality regression that won't be caught by audit_events (because B.10 marker emission is treated as compliant).

---

## §F — Findings, ranked by impact

Severity ladder: **BLOCKER** (M-phase exit invalid until fixed) · **HIGH** (production correctness or user-facing quality affected) · **MEDIUM** (efficiency, observability, or governance hygiene affected) · **LOW** (cosmetic, audit-only).

### F.PIPE.1 — M9 tools not wired to runtime dispatch (HIGH)

**Evidence.** `platform/src/lib/tools/multi_school_signal_lookup.ts` and `convergence_score_lookup.ts` exist and are tested (`platform/tests/schools/multi_school_tools.test.ts` — 17 tests passing per M9-D-S1 AC ledger). They are exported via `CLASSICAL_TOOL_REGISTRY` in `platform/src/lib/tools/index.ts`. **They are not in `platform/src/lib/retrieve/index.ts → RETRIEVAL_TOOLS`** — the registry `consume/route.ts:619` actually dispatches against. They are also not in `RETRIEVAL_CAPABILITY_SPEC`. M8 tools 25+26 use a wrapper file pattern (`platform/src/lib/retrieve/classical_text_search_tool.ts` and `classical_attribution_lookup_tool.ts`); M9 has no equivalent wrappers.

**Effect.** Any query the planner classifies as `multi_school_triangulation` (a valid QueryClass per `consume/route.ts:460`) emits tool calls that fail silently — `getTool()` returns undefined and `route.ts:622` returns null without an `step_error` event. The bundle is missing M9 data; synthesis proceeds context-starved.

**M9_CLOSE assessment.** AC.M9D.10 declared "tools/index.ts STUB→ACTIVE for both tools 27+28" PASS. The PASS reflects the bare-function implementations and the CLASSICAL_TOOL_REGISTRY export. It does not test runtime reachability through `getTool` — that gap is what this audit catches.

### F.GOV.1 — CURRENT_STATE §2 YAML block stale (HIGH)

**Evidence.** `CURRENT_STATE_v1_0.md` line 3279 reads `active_macro_phase: M6` and `active_macro_phase_status: incoming`. The same file's changelog v5.16 (line 57) declares M9 CLOSED 2026-05-14 and M10 INCOMING. §1 of the same file says "§2 is the canonical machine-readable state block… The two must agree."

**Effect.** Any tooling that reads the YAML block (`drift_detector.py`, `schema_validator.py`'s `validate_current_state()`) is reading stale state. A session asking "where are we?" via the §2 block will be told M6, not M10-INCOMING — and may pre-build for the wrong phase.

**Likely root cause.** M8, M9 changelog entries (v5.4 through v5.16) updated only the changelog body, not the §2 YAML fields. Step 15 governance baseline says §2 is authoritative — the closes after M5 stopped honoring this.

### F.SLA.1 — 67% golden-eval fetch-skip rate at 2026-05-11 baseline (HIGH)

**Evidence.** `platform/scripts/eval/answer_eval_gemini_baseline_20260511.log` — 10 of 15 golden queries SKIPPED ("fetch failed"). Aggregate from `results_gemini_baseline_20260511.json`: `mean_synthesis 0.6808`, `mean_weighted 0.7231`. Multiple categories affected: factual (GQ-002, 003), interpretive (GQ-004), holistic (GQ-007, 008, 009), discovery (GQ-012), predictive (GQ-013, 014, 015).

**Effect.** Either production retrieval is exceeding the eval client's timeout for entire query classes, or there is a streaming-race bug specific to the eval harness. Project Ganga `project_ganga_baseline.md` memory shows this baseline was followed by remediation work (Pipeline Gap Plan, Gate II.5, PIV) but no committed re-baseline exists since. State may have improved — needs re-measurement.

### F.DATA.1 — L1 ephemeris CSVs declared in GCS_LAYOUT but never generated (MEDIUM)

**Evidence.** `GCS_LAYOUT_v1_0.md` line 60: `EPHEMERIS_MONTHLY_1900_2100.csv ← coverage gap GAP.L1.01 (not yet generated)`. Two siblings same status. The note at line 124 says "sync script skips non-existent files."

**Effect.** The `temporal` tool either falls back to live Swiss Ephemeris computation (acceptable, slower) or has a blind spot for date ranges outside its in-memory tables. Unverified which.

### F.DATA.2 — M9 outputs DB_SEED_DEFERRED and GCS_UPLOAD_DEFERRED (MEDIUM, gates M10)

**Evidence.** `CURRENT_STATE_v1_0.md` v5.12, v5.14, v5.16 carry forwards "DB_SEED_DEFERRED" and "GCS_UPLOAD_DEFERRED" — the M9-A, M9-C, M9-D, and M9-E artifacts all noted proxy unavailable at session time. The Python scripts exist (`platform/scripts/m9/`), the SQL is parameterized, but the writes never executed.

**Effect.** Even once F.PIPE.1 is fixed, `convergence_score_lookup` and `multi_school_signal_lookup` will return empty results if the rows aren't in `school_signal_coverage`, `school_analysis_runs`, `convergence_scores`, `school_disagreements`. The JSON fallback path in `convergence_score_lookup` (per M9-D-S1 AC.M9D.6) saves the convergence read but not the per-signal coverage read. M10 entry condition is technically M9 CLOSED + acharya panel ≥ 3 — this gap may not block M10 entry but it will block M10 evaluation.

### F.GOV.2 — Manifest entries do not carry gcs_uri (MEDIUM)

**Evidence.** All 160 entries in `CAPABILITY_MANIFEST.json` lack a `gcs_uri` field. `GCS_LAYOUT_v1_0.md` §"Transition Status" specifies: "CAPABILITY_MANIFEST.json entries for CURRENT assets now carry both `path` (local filesystem) and `gcs_uri` fields, with `status: TRANSITIONAL`. The platform runtime still reads from local paths until Phase 14C cuts over to GCS reads. The transition flips `TRANSITIONAL → CURRENT` and removes the local-path dependency."

**Effect.** The manifest does not document where in GCS each asset lives. Cross-check happens only via the human-readable GCS_LAYOUT_v1_0.md. Sessions asking "is asset X mirrored?" cannot answer programmatically.

### F.DATA.3 — L6 learning-layer artifacts excluded from GCS_LAYOUT (MEDIUM)

**Evidence.** `GCS_LAYOUT_v1_0.md` line 128: "L5 (`06_LEARNING_LAYER/`) is not included in this bucket in Phase 14A. Learning Layer sync scope is a separate decision." That decision is not surfaced anywhere in the repo. M5 is now closed; the LL.1 production weights, DBN params, LL.7 discovery prior, and LL.8 parameter register are all production-relevant.

**Effect.** Cloud Run revisions built from `git` carry these files, but the GCS plan does not name them as durable assets. If a session needs to re-run M5 analysis from a different revision/branch, the materialized state lives only in working trees.

### F.SYNTH.1 — LEL not callable by planner (MEDIUM)

**Evidence.** `platform/src/lib/retrieve/lel_query.ts` exists and is registered in `RETRIEVAL_TOOLS` (per `lib/retrieve/index.ts` line 53 import + line 88 registration). It is NOT in `RETRIEVAL_CAPABILITY_SPEC` and NOT in `ALL_21_RETRIEVAL_TOOLS`. The M5-A close ledger declared LEL retrieval gap fixed by adding `lel_query.ts`. The fix was implemented; the integration into the planner's catalog was not.

**Effect.** Predictive queries that should ground responses in the user's actual life events cannot pull them. Synthesis quality on questions like "given my career history, what does the next 6 months hold?" is artificially degraded.

### F.GOV.3 — Manifest path field uses old filename for versioned L2.5 artifacts (LOW)

**Evidence.** Manifest entries have `version: 4.1` but `path: 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md`. Same for CDLM (version 1.3, path `CDLM_v1_1.md`), RM (version 2.2, path `RM_v2_0.md`), CGM (version 9.1, path `CGM_v9_0.md`).

**Effect.** Per project memory `project_canonical_id_fix.md` (2026-05-12, commit 046b593), `bundle_hydrator` resolves L2.5 assets by canonical_id (not path), so this drift does not break retrieval. It does mean any tool consulting `path` directly would 404. Cosmetic but worth tightening in a hygiene pass.

### F.PIPE.2 — Three trace-UI registries disagree (LOW)

**Evidence.** `ALL_21_RETRIEVAL_TOOLS` in `trace/types.ts` has 21 entries, missing `lel_query` and the 4 M8/M9 tools. The constant name is `ALL_21_RETRIEVAL_TOOLS` but the actual runtime registry has 24 tools.

**Effect.** Trace UI sub-row rendering doesn't show classical or M9 sub-tools, even when they fire (M8) or when they would have fired (M9). Cosmetic; UI completeness only.

### F.M8.6 — Classical attribution coverage 76 / 573 signals (carry-forward, MEDIUM)

**Evidence.** `M8_CLOSE` §carry-forwards: "CF.M8.6 (attribution coverage expansion — 76/543 attributed)." After M9-A added 30 signals (Yogini + Tajika) without expanding attribution, coverage dropped to 76/573 = 13.3%. The attribution engine runs `platform/scripts/run_attribution_pass.py` and was last invoked at M8-E-S1 against the 510 signals available then.

**Effect.** `classical_attribution_lookup` returns "silent" for 86.7% of MSR signals. The classical-grounding QueryClass works for queries that happen to hit the 76 covered signals but is sparse elsewhere.

---

## §G — Prioritized remediation plan

Each item is sized as a single-session brief that can be authored by a CLAUDECODE_BRIEF executor or a Cowork session. Sequencing reflects dependencies + blast radius.

### Sprint 0 — Governance hygiene (1 session, 2–4 hours)

**G.0.1 — Fix CURRENT_STATE §2 YAML block.** Update lines 3279–3322 of `CURRENT_STATE_v1_0.md` to reflect M9 CLOSED, M10 INCOMING, gated on acharya panel. Run `schema_validator.py validate_current_state()` to confirm parse-clean. Closes **F.GOV.1**. *(Half-session.)*

**G.0.2 — Add `gcs_uri` field to manifest for every L1/L2.5/L8/L9 asset that has a declared GCS path.** Authoring is mechanical: walk `GCS_LAYOUT_v1_0.md` §Layout, cross-reference each canonical_id in `CAPABILITY_MANIFEST.json`, add the matching `gcs_uri` field per the Phase 14A "TRANSITIONAL" pattern. Closes **F.GOV.2**. *(Half-session.)*

### Sprint 1 — M9 runtime wiring (1 session)

**G.1.1 — Wire M9 tools through to the LLM-first planner.** Mirror the M8 wrapper pattern: create `platform/src/lib/retrieve/multi_school_signal_lookup_tool.ts` and `convergence_score_lookup_tool.ts` exporting a `tool: RetrievalTool` object. Register both in `platform/src/lib/retrieve/index.ts → RETRIEVAL_TOOLS`. Add their entries to `platform/src/lib/router/retrieval_capability_spec.ts → RETRIEVAL_CAPABILITY_SPEC` (after `classical_attribution_lookup`). Add to `ALL_21_RETRIEVAL_TOOLS` in `trace/types.ts` (rename constant to `ALL_RETRIEVAL_TOOLS` — drop the numeric tag). Write 4–6 integration tests asserting the planner can select these tools given a `multi_school_triangulation` classified query, and that `consume/route.ts` dispatches them via `getTool()`. Closes **F.PIPE.1** and partially **F.SYNTH.2**. *(Full session.)*

### Sprint 2 — M9 data deferred-write (1 session, requires local proxy)

**G.2.1 — Run M9 deferred DB seeds + GCS uploads.** Spin `platform/scripts/start_db_proxy.sh`. Execute `platform/scripts/m9/run_multi_school_analysis.py` with the `--write-db` flag (or equivalent — check the script). Execute the convergence + disagreement persistence scripts. Upload 7 per-school JSONs + `convergence_scores.json` + `school_disagreement_register.json` to `gs://madhav-marsys-sources/L9/`. Closes **F.DATA.2**. Native pre-requisite: local gcloud authenticated to `madhav-astrology`. *(Half-session; mostly automation.)*

### Sprint 3 — LEL integration (1 session)

**G.3.1 — Surface lel_query to the planner.** Add `lel_query` entry to `RETRIEVAL_CAPABILITY_SPEC` with optimal_patterns covering: "career history grounded prediction", "anchor a signal to past events", "domain-specific event timeline". Add to `ALL_21_RETRIEVAL_TOOLS`. Update PLANNER_PROMPT golden set with 2–3 predictive queries that should select `lel_query` (extend GT.030–GT.046). Confirm `consume/route.ts:toolStepType()` returns the right step_type ('sql' likely). Verify the planner-golden-set regression eval still passes. Closes **F.SYNTH.1**. *(Full session.)*

### Sprint 4 — SLA re-baseline (1 session, requires prod auth)

**G.4.1 — Re-run answer:eval against current production.** Pre-req: `mint_session_cookie.ts` (per memory `reference_madhav_infra_paths.md`) to obtain a `__session` cookie. Run `npm run answer:eval` against the 15-fixture golden set + the 24-fixture extended set. Commit the new baseline as `platform/scripts/eval/results_gemini_baseline_20260517.json`. Compare the fetch-skip rate against 10/15 from 2026-05-11. If still high, debug as a streaming/timeout fault in the eval harness; if low, the recent Chat V2 + AIOps + Gate II.5 work fixed it implicitly. Closes or quantifies **F.SLA.1**. *(Full session.)*

### Sprint 5 — Pipeline SLA telemetry rollup (1 session)

**G.5.1 — Author `platform/scripts/observatory/sla_rollup.sql` and `sla_rollup.py`.** Compute per-stage P50/P95/P99 over the last 7 days from `query_trace_steps`; report by `step_name`; surface tool-level latency from `tool_execution_log`; correlate against `audit_events.audit_status`. Commit + run + commit the resulting `SLA_BASELINE_2026_05_17.md` report at `00_ARCHITECTURE/eval/`. This is the missing piece: the telemetry exists (§E.1) but no one's reading it routinely. *(Full session.)*

### Sprint 6 — L6 GCS scope decision + ephemeris generation (1 session)

**G.6.1 — Author `LL_GCS_DECISION_v1_0.md`.** Either (a) extend `gs://madhav-marsys-sources/` with an `L6/` prefix mirroring DBN params + LL.1 weights + LL.7 prior + LL.8 register, OR (b) declare L6 deliberately disk-local and document the implication. Update `GCS_LAYOUT_v1_0.md` to v1.2 with the decision. Closes **F.DATA.3**.

**G.6.2 — Generate ephemeris CSVs.** Run `platform/scripts/ephemeris/generate_*.py` (or author them if missing) to produce `EPHEMERIS_MONTHLY_1900_2100.csv`, `ECLIPSES_1900_2100.csv`, `RETROGRADES_1900_2100.csv`. Upload to `gs://madhav-marsys-sources/L1/ephemeris/`. Closes **F.DATA.1**. *(Half-session each.)*

### Sprint 7 — Classical attribution expansion (multi-session campaign)

**G.7.1 — Re-run attribution pass against full MSR v5.0.** Update `platform/scripts/run_attribution_pass.py` to read 573 signals instead of 510; re-execute against 13 classical texts. Expected order-of-magnitude: ~4 hours wall-clock with 4 parallel workers per M8-E-S1 throughput. Update `CLASSICAL_ATTRIBUTION_REGISTRY` to reflect new totals. Partially closes **F.M8.6** depending on how many new signals find classical hits. *(Single execution session + a follow-up to assess the deltas.)*

### Sprint 8 — Optional governance polish

**G.8.1 — Fix L2.5 manifest path drift.** Rename `path:` fields to match actual filenames for UCN, CDLM, RM, CGM. Either rename the files (preserving canonical_id) or accept the cosmetic drift in a documented hygiene note. Closes **F.GOV.3**. *(Quarter-session.)*

### Recommended sequence

```
G.0.1 + G.0.2 (governance)
        ↓
G.1.1 (M9 wiring) ─┐
        ↓         │
G.2.1 (M9 data)   │
        ↓         ↓
G.3.1 (LEL) ──→ G.5.1 (SLA telemetry) ──→ G.4.1 (re-baseline)
                ↓
        G.6.1 + G.6.2 (L6 + ephemeris)
                ↓
        G.7.1 (classical attribution campaign)
                ↓
        G.8.1 (manifest polish)
```

Sprints 0–3 unblock M10 (acharya panel + multi-school workflows actually function). Sprints 4–5 give the M6 prediction-window evaluation surface a measurement floor. Sprints 6–8 close residual data debt.

---

## §H — Known limits of this audit

1. **No live Postgres probe.** Sandbox cannot reach Cloud SQL (no gcloud, no proxy, no ADC); Terminal grant is "click" tier, blocking keyboard input. Row counts, recent audit_events freshness, P50/P95/P99 per stage, and tool_execution_log error rates are inferred from M-CLOSE artifacts (live state at close) and the 2026-05-11 eval log. **G.5.1 is the remediation that closes this gap.**
2. **No live GCS object listing.** Cannot enumerate actual objects in `gs://madhav-marsys-sources/` or `gs://madhav-marsys-build-artifacts/` to confirm uploads. GCS upload status in §C is sourced from M-CLOSE AC ledgers ("PASS — uploaded to GCS") plus the GCS_LAYOUT declaration.
3. **No live Cloud Run config probe.** Did not query `gcloud run services describe amjis-web` for the current revision and env vars. Revision identifiers are sourced from project memory entries (most recently `amjis-web-00156-bj9` per `project_chat_v2_workstream.md` 2026-05-17 ship).
4. **`predictive.ts` v3.0 contents not re-read in this audit.** The synthesis prompt template's actual treatment of LEL data via inline-stats vs tool-call is inferred from M5-E-S1 commit messages, not from current source. If the template was updated post-M5 close, §E.4 finding (1) may need adjusting.
5. **LL.7 discovery prior integration in `pattern_register.ts` etc. is unverified.** §D.2 marks this ⚠️. A 30-minute code read in a follow-up session would resolve.
6. **Audit produced cross-session; no SESSION_LOG seal.** Per CLAUDE.md §H this is not a well-formed phase session — it is a cross-cutting read-only audit. No SESSION_OPEN handshake was issued; no `red_team_due` was incremented. Native may choose to treat this artifact as a discovery-class doc (parallel-safe) or as a Cowork "shadow" session whose findings convert into phase work via the §G briefs.

---

## §I — One-paragraph executive readout (for tomorrow morning)

The MARSYS-JIS instrument is technically further along than the §2 state pointer says. Seven of ten macrophases are sealed (M1–M5, M8, M9). M9 closed in a single calendar day on 2026-05-14 with 95 tests, 573 MSR signals, 5/5 domains showing HIGH inter-school convergence, and a full 7-engine simulation against the native's chart. **But M9's plumbing is not finished**: the two tools that expose 7-school analysis and convergence scores to the production pipeline are implemented and tested, but never registered in the runtime tool registry the planner dispatches against. The pipeline silently drops them. Separately, life-event grounding (`lel_query`) suffers the same fate — implemented at M5-A, never advertised to the planner. The data-asset story is dual: L1/L2.5/L3/L8 are mostly mirrored to GCS; L6 (calibration substrate) was explicitly excluded from GCS in Phase 14A and that decision was never revisited as M5 closed; L9 outputs are sitting in the python script's memory because the proxy was down at close. A live re-run of answer-eval is overdue — the most recent baseline (2026-05-11) had a 67% fetch-skip rate, which either reflects a real production regression or a streaming-race bug in the eval harness. **Eight surgical sessions, ordered in §G, would close the loop and unblock M10.**

---

*End of MACROPHASE_AND_DATA_AUDIT_v1_0.md. Authored 2026-05-17 by a Cowork audit session. Successor: native review + selection of which §G sprints to schedule. No mirror pair declared (this is a single-author audit; if promoted to canonical, MP.1 mirror to `.geminirules` to be authored at first execution session.)*
