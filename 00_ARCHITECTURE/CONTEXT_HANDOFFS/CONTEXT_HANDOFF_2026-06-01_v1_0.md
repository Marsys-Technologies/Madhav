---
artifact: CONTEXT_HANDOFF_2026-06-01_v1_0.md
purpose: "Self-contained context document for handoff to a fresh Claude conversation. Covers PyJHora implementation plan, current and legacy system architecture, three serving channels (legacy / agentic-loop / MCP), tooling strategy, and standing constraints."
version: 1.0
authored_at: 2026-06-01
authored_by: cowork-planner
audience: a new Claude conversation that has zero prior session context
how_to_use: paste this entire file at the start of a new chat. The reader should treat it as ground truth for "where the project is right now."
read_in_combination_with:
  - CLAUDE.md (project root)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md
---

# MARSYS-JIS · Context Handoff · 2026-06-01

This document brings a fresh conversation up to speed on the MARSYS-JIS project as of 2026-06-01. It is exhaustive on purpose: a new chat with no prior context should be able to act competently after reading it. Where details would balloon, this document points at the canonical artifact that holds them.

## 1 · Project, native, mission

MARSYS-JIS is an LLM-operated Jyotish (Vedic astrology) instrument that produces deterministic chart facts, layered synthesis, and time-indexed predictions for any native. The original native is Abhisek Mohanty (born 1984-02-05, 10:43 IST, Bhubaneswar). The project has since generalised to any guest, so single-native shortcuts are being removed.

The product is a research instrument, not a fortune-telling product. Every output must be a *computed fact* — no narrative, no opinion, no judgement (the prime directive). Interpretation, when it exists at all, happens only at the serving layer and only from facts that already exist in the data layer.

Quality bar: an independent acharya should reach one of "this is my own level," "this is above me," or "this reveals things I wouldn't have seen on first pass." Nothing less.

## 2 · System architecture in one breath

The system has four logical halves: a **build half** (produces facts and stores them) and a **serve half** (queries those facts and presents them), connected by Postgres + GCS, surrounded by an **observation half** (build telemetry + QA), governed by a **standing-constraints half** (human gates, banned models, no JH parity).

```
                       BUILD HALF                                 SERVE HALF
                                                                                                                
intake → orchestrator → engine → writers → facts → ─── queried by ─── → 3 channels
  Stage 1-2              PyJHora   L1..L5    chart_facts                  ├─ Legacy /consume pipeline
                                              + GCS JSONL                 ├─ R11 Claude-style chat (agentic)
                                                                          └─ amjis-mcp (Antigravity / external)
                                                                                                                
                       OBSERVATION HALF                          STANDING CONSTRAINTS HALF
SSE → Yantra Chitra cockpit                                      no JH parity oracle anywhere
build_events table                                               no Anthropic models in production
Pariksha QA swarm on build_complete                              PR-to-main is human-gated
                                                                 no auto prod deploy or DB ops
                                                                 Cowork plans only; Antigravity executes
```

The remainder of this document walks each half.

## 3 · Build half · intake → engine → facts

### 3.1 Stages 1 and 2 — Aapti (आप्ति · identity capture) + Prarambha (प्रारम्भ · build kickoff)

A guest arrives at `/clients/new` (Next.js form) and submits birth details. The form posts to `/api/clients/create`, which does natural-key dedupe (preventing the duplicate-chart problem surfaced 2026-05-31) and writes a `charts` row to Postgres with a `chart_id` UUID. The dashboard then surfaces a Build button at `/clients/<id>/build`. Clicking Build enqueues a Cloud Tasks message (OIDC-signed) that triggers the `marsys-build-pipeline-job` Cloud Run Job in `asia-south1`.

Implementation: Next.js (App Router, TS), Postgres (Cloud SQL, `db-custom-1-3840` ZONAL + PITR), Cloud Tasks queue `marsys-build-queue`, Cloud Run Job orchestrator. The orchestrator currently has *no watchdog* — stuck builds accumulate, which is tracked under BUILD_TIMEOUT_HARDENING (see §11).

### 3.2 Engine — PyJHora (replacing `natal_engine/`)

The engine is the substrate that turns the birth event into chart facts.

**Current (deprecating).** `platform/python-sidecar/natal_engine/` — a pyswisseph-based Python package built in BRIEF_1_1. Modules: `positions`, `houses`, `dignities`, `vargas`, `dashas`, `panchanga`, `sensitive_points`, `l25_builder`. It calls Swiss Ephemeris (pyswisseph 2.10.3.2) under the hood. `forensic_writer.py` currently ships as a 23-line stub returning 0 rows — a known gap.

**New (this PR will land).** PyJHora is a Python port of Jagannatha Hora's calculation logic. It replaces `natal_engine/` *entirely* in a single PR. There is no parallel run, no feature flag, no spike. The implementation brief is at `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md` and is summarised in §8 of this handoff.

The rationale for the switch is simple. PyJHora *is* the JH logic. The native trusts JH's calculation set. Trying to verify PyJHora against an external JH oracle is therefore tautological — PyJHora is the source of truth by construction. Verification reduces to *internal consistency* (row counts, schema, structural invariants, layer-completion gates, determinism), which is a much stronger contract than any oracle parity check.

### 3.3 Data layer — L1 through L5 with 28 assets

The build pipeline produces 28 data assets distributed across five layers. Each asset is computed by a writer, lands in the `chart_facts` table partitioned by `ayanamsha_id`, and has its provenance written to GCS JSONL (content-addressed, diffable).

**L1 · Adhara (आधार) — Foundation.** Eight writers × five ayanamshas. Deterministic. Verified by row count, NOT NULL, FK, and structural invariants such as Lagna ↔ House-1 sign consistency and Rahu ↔ Ketu 180° apart. Assets include A1 Pratyaksha (the forensic core — currently a stub, primary target of the PyJHora arc), A2 Panchanga (73,414 rows, 1900–2100), A4 Graha Sthana (planet positions, 9 grahas), A5 Bhava Vibhaga (houses + cusps), A6 Varga Chakra (D1..D60), A7 Dasha Krama (Vimshottari + Jaimini Chara + Yogini + Kalachakra), Dignities (6-fold dignity assessment), and Sensitive Points (Gulika, Mandi, Arudha Pada, upagrahas).

**L2.5 · Sambandha (सम्बन्ध) — Synthesis.** Five canonical holistic structures, each built per ayanamsha by `l25_builder` reading L1 outputs only. A9 MSR (Lakshana Kosha, exactly 573 signals, every signal must have a non-null `source_citation` pointing at FORENSIC or LEL — MSR grounding was the focus of the GISMCP campaign). UCN (Sangam, unified contextual narrative). A11 CDLM (Anubandha Mandala, cross-domain linkage matrix, each cell references an MSR signal id). A10 CGM (Karana Jala, a graph DAG whose endpoint ids must resolve to MSR). A12 RM (Upaya Kosha, remedies; each `affliction_signal_id` is an FK into MSR).

**L3 · Sutra (सूत्र) — Meta-thread.** Temporal and structural cross-cuts. A14 Kala Yoga (cycles → dasha period FK), A15 Bandha (sources A1, A7, A14), Sade Sati window, Vedha + Bhrigu Bindu (obstruction + sensitive point), Phase-locked anchors (time-sync grid that LEL events hook into), A20 Tajik Varsha (Muntha, computed with the MSR.377 corrected formula from the M5 Coverage Campaign).

**L4 · Vyavahara (व्यवहार) — Prescriptive.** Six META synthesis layers shipped in the Multi-Ayanamsha Deterministic Build (2026-05-30): META-α (Lattice), META-β (Pattern catalog), META-γ (Divergence ledger — captures school disagreements), META-δ (Negative space — absences as signals), META-ε (Derivation trail — auditability spine). All five are live.

**L5 · Lattice (कालजाल) — Temporal envelope.** UTEE (Unified Temporal Event Envelope), BRIDGE (vedha ↔ anchor interactions, an L3 ↔ L4 cross-thread), `timeline_query` retrieval surface (~160 retrieval tools route here), and per-varsha digests. The `timeline_query` tool is healthy at the routing layer but the L5 timeline table is empty; bootstrap is queued as an operator action.

The 28-asset DAG with 27 edges is seeded by migration 158 in `build_dependencies`. Build order is enforced by `build_steps.depends_on` and verified post-fact by Pariksha's layer-completion gate (L1 must finish before L2.5 starts, and so on).

### 3.4 Five ayanamshas in parallel

Every per-ayanamsha writer runs across five sidereal calibrations in parallel: `lahiri`, `true_chitra`, `kp`, `raman`, `surya_siddhanta`. The PyJHora ayanamsha setting is a global variable per process, so parallelism uses `multiprocessing.Pool(5)` with `spawn` start-method — one subprocess per ayanamsha, clean state per worker. Migrations 140–153 (Multi-Ayanamsha build) ship the partition scheme.

### 3.5 chart_facts and GCS provenance

The data plane is Postgres `chart_facts` partitioned by `ayanamsha_id`, keyed by `(chart_id uuid, build_id, asset_id, ayanamsha_id, ...)`. Each writer also writes a JSONL provenance file to `gs://marsys-provenance/L1/<build_id>/<writer>.jsonl` (or `L2_5/`, `L3/` — note the layer-prefix scheme, not git-style paths). The JSONL is the diffable audit trail. The Postgres rows are the system of record.

Across 19 core tables, `chart_id` has been backfilled as a uniform `uuid` (Platform Modernization v1.2, sealed 2026-05-29, tag `platform-modernization-v1-2-complete @ 790673a0`). Partitions 121/122/124 (`query_trace_steps` etc.) are still blocked on `chart_id` being 100% NULL — that gap unblocks only after the deterministic engine starts writing per-chart rows, which is the natural sequel to the PyJHora arc.

## 4 · Observation half · SSE, cockpit, Pariksha

### 4.1 SSE telemetry and Yantra Chitra cockpit

Every writer emits `build_events` rows (stage, asset, status, timestamp) which the cockpit consumes via an `EventSource` connection to `/api/events`. The cockpit (`Yantra Chitra`, React) renders a `LiveDependencyGraph` with a `ProgressRing` per asset, plus a Pariksha pass/fail pill once the build closes. Visual contract: obsidian (#08070a) background, gold (#d4a648) accents, Cormorant Garamond serif headings, Inter sans body, JetBrains Mono for telemetry.

Resume protocol: every Drashta walk step writes a checkpoint to `resume_state.yaml`. If a session breaks (auth expires, network drops), the next invocation reads the checkpoint and continues from CP-N rather than restarting.

### 4.2 Pariksha — autonomous QA + remediation swarm

Pariksha (परीक्षा · examination) is a per-build QA swarm that fires automatically when a new `charts` row is created. It is not a feature flag, not a manual command — it activates as part of the standard chart-build flow.

Roster: six **Drashta** watchers (Aapti-Drashta for Stage 1, Yantra-Drashta for Stages 2 + 6, Tantra-Drashta for Stages 3-5 row counts, Sambandha-Drashta for DAG ordering, Pramana-Drashta for the post-build internal-consistency battery, plus a front-end Drashta walking the portal as a guest). Three meta agents: **Pratisamhita** (reconciles + ranks issues across watchers), **Vaidya** (fix agents — PR-only by default, may auto-merge ≤30 LoC single-file fixes under operator authorization), and **Naya-Pariksha** (re-runs after each Vaidya PR merges to close the loop).

Pramana's internal-consistency battery — the one oracle that matters — has six categories and zero external dependence. (1) Row counts versus `EXPECTED_ROW_COUNTS.yaml` per asset × ayanamsha. (2) Schema compliance: NOT NULL, FK, CHECK, enum membership. (3) Structural invariants per asset: Lagna ↔ House-1 sign, Rahu ↔ Ketu 180°, Vimshottari mahadashas summing to 120 years, MSR exactly 573 signals, CGM forming a DAG. (4) Cross-asset referential integrity: CDLM cell ids resolve to MSR signal ids, RM affliction ids resolve to MSR, A15 Bandha sources resolve to A1/A7/A14, and so on. (5) Layer-completion gate verifying that L1 actually finished before L2.5 started. (6) Determinism — rebuilding produces byte-identical row hashes.

There is *no* Category 7. Pariksha never compares against Jagannatha Hora, against the JHORA_TRANSCRIPTION source, against FORENSIC v8.0 as a parity oracle, or against any external reference. That directive is permanent.

Pariksha master plan is at `00_ARCHITECTURE/PARIKSHA/PARIKSHA_MASTER_PLAN_v1_0.md`. The Pramana brief is at `00_ARCHITECTURE/PARIKSHA/briefs/PRAMANA_DRASHTA_v1_0.md`. Per-build artifacts live under `builds/<chart_id>/` and are git-ignored except for the final REPORT.md when the operator wants persistent audit.

A real Pariksha run on the native chart (chart `362f9f17-95a5-490b-a5a7-027d3e0efda0`) found five gaps that frame the current arc: forensic_writer is a stub, D1 vargas have an off-by-one, the `preferred_name` column was missing on `charts`, a BUILD_TASK_AUTH_BYPASS environment variable was leaking past production, and the legacy cockpit UI was still rendering. The PyJHora arc closes the first two; the others are separate hygiene PRs.

## 5 · Serve half · three channels into the same fact store

The fact store (`chart_facts` + L1..L5 derived assets + GCS JSONL provenance + the ~160 retrieval-tool registry) is consumed by three serving channels. They are independent code paths, share the data layer, and have different audiences and trust models. Understanding the three together is essential — they are sometimes confused for one another.

### 5.1 Channel 1 — Legacy `/consume` query pipeline (still in production)

This is the original MARSYS query path that the public chat UI on the portal sits on. Request lands at `/api/consume/v2/route` (Next.js Route Handler). The route executes a fixed five-stage pipeline:

1. **B.11 floor** — a mandatory Whole-Chart-Read context block is pre-assembled deterministically. Every query, no matter how narrow, sees the entire chart's holistic synthesis (MSR + UCN + CDLM + CGM + RM) before downstream stages run. This is principle B.11 in `PROJECT_ARCHITECTURE_v2_2.md`.
2. **Planner** — a server-side LLM call to a planner model (Gemini Pro or DeepSeek Pro by default; Anthropic banned). The planner reads `PLANNER_PROMPT_v2_x.md` (currently v2.7+ with R-NRM.1, R-PA, R-PCI, R-NRM rules), the user query, and the B.11 floor, then emits a `tool_plan` JSON enumerating which retrieval tools to call with what arguments.
3. **Deterministic retrieval execution** — the route runs each planned tool from the portal `RETRIEVAL_TOOLS` registry (51 tools as of 2026-05-25 after the Universal Parity Campaign). No LLM in the execution path; every tool is a typed function over Postgres / GCS / pgvector. Stage name in `query_trace_steps`: `compose_bundle`.
4. **Synthesis** — a second LLM call (synthesis model, again non-Anthropic) reads the retrieved bundles and emits the final answer with GFM footnote citations (`[^N]`) that resolve to MSR signal ids via `enrichCitations` (shipped in R7).
5. **Persistence** — answer + bundle + trace persisted to Postgres for replay and `answer:eval` evaluation.

This channel is what powers the existing `/consume` chat surface and the `Classic Marsys` setting in the cockpit's SettingsDropdown. It is not deprecated — it still serves real traffic.

### 5.2 Channel 2 — R11 Claude-style chat with bounded agentic loop (the new modern surface)

This is the assistant-ui-based chat surface shipped through the Chat V2 arc (R6 through R11.G, 2026-05-18 to 2026-05-24). It is the `Claude-style chat` setting in the cockpit. Default flag `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` is now true; the surface is the new default for new chats.

The architecture differs from the legacy pipeline in three ways. First, **no server-side planner LLM** — the model itself is in the loop, deciding which tool to call next. Second, **bounded agentic loop** — `lib/providers/agentic_loop.ts` is a generic engine with `MAX_ITERATIONS = 8`. The model calls a tool, sees the result, calls another, until it stops or hits the cap. Third, **provider-agnostic capability adapter substrate** — `lib/providers/adapter.ts`, `lib/providers/dispatcher.ts`, and per-provider `adapter.ts`+`manifest.ts` for Anthropic, Google, OpenAI, DeepSeek, and NVIDIA. Each adapter implements `chat()`, `stream()`, `thinking()`, `cache()`, and `loop()`.

The B.11 floor is *still* enforced. It pre-executes deterministically before the loop enters — the model never has the option to skip the Whole-Chart-Read. The loop only chooses among the *remaining* tools (planner-authorised subset). Primitives tagged `surgical: true` are not exposed to the loop at all.

Per-provider features shipped: smooth-stream (rate-target ~30-50 cps), pre-token thinking indicator, extended-thinking auto-collapse, adaptive thinking budgets (`thinking.effort` / `thinkingBudget` / polyfill), Anthropic 4-breakpoint `cache_control`, Gemini `cachedContent`, OpenAI/DeepSeek cache telemetry. Per-phase flags: `R11B_LOOK_AND_FEEL` (true, baked), `R11C_STREAMING_THINKING`, `R11D_PROMPT_CACHING` (D.1 PROMPT_LAYOUT live, D.2 ANTHROPIC_CACHE live, D.3 GEMINI_CACHE deferred), `R11E_AGENTIC_TOOLS` (E.1-E.4 *all five providers* live `=true` after R11.F shipped via PR #156).

R11.F bounded loop (merge `07e49964` + hotfixes `853c561e`/`2a4e3c55`, revision `amjis-web-00390-csz`, 2026-05-24) is the load-bearing piece. It wired three breaks from the R11.A-E baseline: route.ts was passing `tools:[]` (no tools available to model), adapter `chat()` was omitting tools from `streamText()` (model couldn't call tools even if listed), and the adapter dispatch path skipped `onFinish` (no persistence). All three are now fixed across every provider. Operator runs a per-provider flag flip; all five live since 2026-05-24.

Visual contract: Claude.ai-style typography (Cormorant serif heads, Inter body, JetBrains Mono code), bubble-less assistant messages, 768px reading column, hover-reveal action bar, inline citations with URL click-out (the side panel `CitationSidePanel` was retired in R11.B). Brand colours still Marsys.

Active workstream tail (R11.F-RES-1/2/3 captured as `V1_3_AUDIT_QUEUE` CF.V13.5–7): (1) Lifecycle tab counts only deterministic-stage tool calls, not agentic-loop calls — operator infers loop execution from response content + Cloud Run DEBUG logs. (2) GitHub Actions has no `pull_request:` trigger; three consecutive failed deploys in late R11 were preventable with PR-level CI. (3) When triaging adapter-shared SDK base bugs, grep ALL adapters before patching.

### 5.3 Channel 3 — MCP server (`amjis-mcp` sidecar) for external + dev consumption

`amjis-mcp` is a Cloud Run sidecar in `asia-south1` that exposes 40 MCP tools over the Model Context Protocol. It is the channel that Claude Code (running in Google Antigravity IDE) consumes for development work, and that any future external integration would consume.

Auth: API key bound to a Firebase UID + an `audience_tier` (super_admin / acharya / client). Migrations 070 and 071 set up `mcp_api_keys`, `mcp_predictions`, `mcp_disagreements`. After the GISMCP Remediation (PR merged 2026-05-26), all 40 MCP tools are registered unconditionally — the prior tier gate that hid 14 ops tools (`tool_health`, `data_coverage`, `log_prediction`, `record_outcome`, `flag_disagreement`) from non-super_admin keys is removed. Tier still controls retrieval-layer filtering at instrument-meta level, but tool availability is uniform.

Tools fall into four shapes. **End-to-end** (1 tool): `ask_madhav` — full query → planner → retrieval → synthesis path equivalent to Channel 1, returning a full answer with citations. **Plan-introspection** (2): `plan_query` (returns the tool plan without executing), `execute_plan` (executes a supplied plan). **Surgical primitives** (10): tagged `surgical: true`, never exposed to Channel 2's agentic loop, including reads against MSR, UCN, CDLM, CGM, RM, dasha, vargas, panchanga, ephemeris, classical texts. **Observability + writes** (5+): `read_asset`, `get_trace`, `list_recent_queries`, `log_prediction`, `record_outcome`, `flag_disagreement`. The MCP Tool Audit Remediation v2 (2026-05-26) brought all 40 tools to 100% pass on Audit 4c via two PRs: `fix/mcp-schema-compat` (`ee498f34`, backward-compat Zod aliases for 7 tools whose schemas regressed) and `fix/mcp-data-quality` (`a94b5caf`, 55 planet category rows seeded, signal confidence state-derived, mantras filter regex-anchored).

The MCP Transformation arc (`MCPT_CLOSE_v1_0.md`, COMPLETE 2026-05-22) shipped the substantive content underneath: 2,717 `chart_facts` rows across 27 categories, 4,589 `rag_chunks` indexing BPHS + Jaimini Sutram + KP Reader + Tajaka Neelakanthi, all 573 MSR signals fully grounded with `source_citation`, 574 `school_convergence_index` rows, and 5 auto-loaded resources (`chart-snapshot`, classical-text resources, etc.). Migrations 072–080 ship those tables.

Five resources auto-load on every MCP connect: `chart-snapshot` (live native chart facts), the four classical-text resources. Three audience tiers control what tier-conditioned house-rules block ships with the response.

Native pre-merge operator action items live in `OPERATOR_ACTIONS_PENDING.md` and `MCP_WORKSTREAM_COMPLETE.md`. Phase MCP-5 (OAuth) is deferred per brief §7.5.

### 5.4 Tabular comparison

| Aspect | Legacy `/consume` | R11 Claude-style chat | `amjis-mcp` |
|---|---|---|---|
| Surface | `/consume` page, Classic Marsys toggle | `/consume` page, Claude-style chat toggle (default) | external MCP clients, primarily Claude Code in Antigravity |
| Planner | server-side LLM call | none — model is the planner via agentic loop | both modes exposed (`ask_madhav` end-to-end, `execute_plan` for caller-supplied plans) |
| Tool count | 51 RETRIEVAL_TOOLS | subset of 51 (loop-eligible, non-surgical) | 40 (instrument-meta-tagged subset) |
| LLM provider | Gemini / DeepSeek (Anthropic banned) | per-provider via 5 adapters (Anthropic banned in prod) | none in tools; consumer picks |
| B.11 floor | enforced in pipeline | pre-executed before loop entry | enforced in `ask_madhav` only |
| Authentication | `__session` cookie (web sessions) | `__session` cookie | API key bound to Firebase UID + audience tier |
| Channel status | LIVE, not deprecated | LIVE, default | LIVE |
| Code path | `platform/web/src/app/api/consume/v2/route.ts` legacy path | same route, `useAdapter()` branch | `platform-mcp/src/server.ts` |
| Persistence | answer + bundle + trace | same persistence + agentic-loop iteration log | `mcp_predictions`, `mcp_disagreements` for write tools |

## 6 · Tooling strategy

The fact store is queried through *one* retrieval-tool registry that lives in the portal route. Both Channels 1 and 2 (legacy + agentic-loop) read directly from that registry. Channel 3 (MCP) reads a *normalized projection* of the same registry, governed by the `INTERFACE_NORMALIZATION_REGISTER v1.0` and the planner-prompt rule R-NRM.1.

This single-registry architecture is the outcome of the **Universal Parity Campaign** (FULLY COMPLETE 2026-05-25, 34 sessions across UDA-Q/0/1/2/3/4): portal grew from 36 to 51 RETRIEVAL_TOOLS, MCP grew from 26 to 40 tools, and the boundary between portal-only and MCP-shared tools is now declared in `CAPABILITY_MANIFEST.json`. 15 tools are tagged `channel: both`; the others are portal-only.

The tool registry has six logical families. (a) **MSR-store reads** — `query_signal_state`, `query_signal_bundle`, `vector_search` over MSR signals. (b) **L2.5 graph reads** — `get_cgm_subgraph`, `query_cdlm_cell`, `query_remedial_mantras`. (c) **L1 chart_facts reads** — `query_ephemeris`, `query_panchanga` (with the Phase-4C enrichment field groups: `special_yogas`, `choghadiya`, `hora`, `inauspicious`, `auspicious`), `query_jaimini_chara_dasha`, `query_tara_balam`, `query_chandra_balam`. (d) **Classical-text retrieval** — `read_classical_text`, `cross_school_lookup`, `multi_school_bundle`, `holistic_bundle` (all R-NRM-normalized). (e) **L5 temporal lattice** — `timeline_query` (healthy at routing layer, awaiting L5 bootstrap). (f) **Observability + writes** — `tool_health`, `data_coverage`, `log_prediction`, `record_outcome`, `flag_disagreement`.

Determinism is non-negotiable. No tool calls an LLM. Every tool is a typed function over Postgres / GCS / pgvector. If an answer feels like it needed a model, the model lives upstream (in the planner or the loop), never inside a tool.

The PyJHora arc does not change this registry. It changes the *upstream writer layer* that populates `chart_facts`. The tools that read `chart_facts` continue to work without modification once non-zero rows start landing.

## 7 · Standing constraints — read these every session

These are durable preferences. They override any reasoning chain that tries to relax them.

**No JH parity oracle, anywhere.** Per the native's standing directive (memory hook `[[no-jh-parity-anywhere]]`), Jagannatha Hora parity is not a verification surface. Not in code, not in briefs, not in tests, not in fixtures, not in planning artifacts. Files still present (`test_jh_parity.py`, `jh_oracle.json`, `jh_oracle_loader.py`, `jh_oracle_schema.json` under `natal_engine/`, plus ~40 grep hits in `00_ARCHITECTURE/`) are *cleanup targets*, not authoritative references. The PyJHora arc deletes the `natal_engine/` ones; governance-doc references are a follow-on cleanup arc.

**No Anthropic models in production.** Per the native's standing directive (memory hook `[[llm-model-selection]]`), the Anthropic API is banned for cost reasons unless the native explicitly asks for it. Default planner: Gemini Pro. Fallback: DeepSeek v4 Pro. Cheap-flash variants for non-critical paths. Any brief that hardcodes Anthropic gets flagged. The Channel 2 adapter substrate *includes* Anthropic (the substrate is provider-agnostic), but the production flag flips are all non-Anthropic.

**Cowork plans; Antigravity executes.** Per memory hook `[[cowork-vs-antigravity-split]]`, this chat (Cowork) does planning, monitoring, briefing, and authoring only. All implementation goes to Claude Code running inside Google Antigravity IDE. Every output from this chat must be a pasteable prompt or a committed `.md` brief — never chat-only bullet lists the user has to translate.

**PR-to-main is human-gated.** Per-session commits are autonomous. Merges, production deploys, production DB ops, secret rotations, and flag flips are all human gates. Each conversation owns its branch; cross-branch contamination is recovered via cherry-pick to main, never via rebase-on-another-branch.

**Verify state from CURRENT_STATE + git, not CLAUDE.md §F.** The "you are here" block in CLAUDE.md §F drifts. The authoritative state pointer is `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` plus `git log`. Linear "Wave N" narratives in old docs mislead because the project has many parallel streams running concurrently.

**Verification is internal consistency.** Row counts versus spec, schema compliance (NOT NULL, FK, CHECK, enum), structural invariants per asset, cross-asset FK integrity, layer-completion gates, determinism. Six categories. No category 7, ever.

**Other lessons worth remembering.** `NEXT_PUBLIC_*` env vars are build-time baked — gcloud env-var updates have zero effect on the running client bundle. `deploy-cloudrun@v2` merges env vars — removing a line from `deploy.yml` does not remove the running var. Grep-presence is not compile-success after a `-X theirs` merge; always run `tsc --noEmit` + `pytest`. Never `rm` based on filename alone; diff content first (numbered migrations renumber at merge time). Idempotency guards must check the *actual write target*, not a sibling. `pyswisseph` Sripati `'S'` returns sandhis, not madhyas. Gemini drops closing tags in XML-like output — write tolerant parsers.

## 8 · PyJHora implementation plan (full)

The plan is captured in `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md`. This section is the executive summary. The fresh conversation should read the full brief before any code touches.

### 8.1 Locked decisions (do not re-negotiate)

Engine: PyJHora. Install: `pip install PyJHora` direct, no fork. PyQt6 dependency: tolerated at install, never imported at runtime — fallback ladder is `QT_QPA_PLATFORM=offscreen` env var, then lazy-import only the calculation submodules (`from jhora.panchanga import drik` rather than `import jhora`). Replace `natal_engine/`: yes, in this PR, no parallel run, no feature flag. License check: skipped, native's call. Spike: skipped, empirical discovery happens inside the adapter unit tests. Verification oracle: internal consistency only.

### 8.2 Seven phases of the arc

**Phase 1 — Dependency in place.** Pin the PyJHora version, edit `requirements.txt`, modify the python-sidecar `Dockerfile`. Acceptance: `docker build` succeeds and `python -c "from jhora.panchanga import drik; print(drik.__file__)"` prints a path inside the container.

**Phase 2 — Adapter layer.** Create `platform/python-sidecar/pyjhora_adapter/` with twelve modules: `_ayanamsha.py`, `_isolation.py`, `positions.py`, `houses.py`, `dignities.py`, `vargas.py`, `dashas.py`, `panchanga.py`, `strength.py`, `sensitive_points.py`, `yogas.py`, `transits.py`, `reconciliation.py`. Every adapter function is mypy-strict typed and returns plain Python primitives or TypedDicts — never PyJHora's internal classes. Numerics are integer arc-seconds or `Decimal`, never bare floats. One PyJHora function per adapter function. Localised Devanagari strings get normalised to canonical IAST inside the adapter. Where PyJHora's docstring lies about return shape, the adapter test asserts the *observed* shape.

**Phase 3 — Multi-ayanamsha parallelism.** `_isolation.py` exposes a `per_ayanamsha(fn, jd_ut, **kwargs)` helper that uses `multiprocessing.Pool(5)` with `spawn` start-method. Every writer calls this once and gets five results. Test: `planet_positions` for all five ayanamshas in parallel, asserting the Sun's sidereal longitude differs between them by the expected ayanamsha delta (arithmetic only, no oracle).

**Phase 4 — Writer rewiring.** Every L1 writer in `platform/python-sidecar/pipeline/writers/` replaces `from natal_engine.* import ...` with `from pyjhora_adapter.* import ...`. Targets: `forensic_writer.py` (currently the stub — primary target), `panchanga_writer.py`, `positions_writer.py`, `houses_writer.py`, `dignities_writer.py`, `vargas_writer.py`, `dashas_writer.py`, `sensitive_points_writer.py`, `l25_builder.py`. Pattern: call `per_ayanamsha(fn, jd_ut)`, build rows with `chart_id` + `build_id` + `ayanamsha_id` keys, upsert to `chart_facts`. Idempotency guard verifies the actual write target.

**Phase 5 — Delete `natal_engine/`.** After every writer compiles against the adapter and every test passes, `git rm -r platform/python-sidecar/natal_engine/`. Hard delete. No deprecation window. This also catches the four JH-parity artifacts (`test_jh_parity.py`, `jh_oracle.json`, `jh_oracle_loader.py`, `jh_oracle_schema.json`). `grep -rn "natal_engine" platform/ src/` must return zero. `grep -rn "jh_parity\|jh_oracle\|JHORA_TRANSCRIPTION" platform/ src/` must return zero in code paths (governance audit-trail hits in `00_ARCHITECTURE/` are allowed and queued for separate cleanup).

**Phase 6 — Architecture-doc refresh.** Update `PORTAL_NORTH_STAR_ARCHITECTURE.md`, `PLATFORM_REBUILD_ARCHITECTURE.md`, `PLATFORM_MODERNIZATION_*.md`, and `CURRENT_STATE_v1_0.md` to describe PyJHora-direct architecture and drop the lingering `pyswisseph + natal_engine + PyJHora` framing. Edits are minimal — the architecture *intent* was always PyJHora; this realigns docs with what is actually shipping.

**Phase 7 — End-to-end native chart.** Start the Cloud SQL Auth Proxy locally, mint a `__session` cookie, post to `/api/builds/start` with the native chart_id `362f9f17-95a5-490b-a5a7-027d3e0efda0`, wait for `build_complete`, query `chart_facts` and assert non-zero rows per `(asset_id × ayanamsha_id)`. The `forensic_writer` no longer returns the 0-row stub.

### 8.3 Eight acceptance criteria

The PR is mergeable when all eight pass: docker build green, adapter pytest green, overall pytest green, zero `natal_engine` references, zero `jh_parity` / `jh_oracle` references in code paths, end-to-end native run with non-zero counts everywhere, determinism (rebuild produces identical row-payload md5), PR description documents the pinned PyJHora version + headless-import strategy + architecture doc diff.

### 8.4 Failure modes the executor should plan for

PyQt6 init failing headlessly — fallback ladder above. Localised Devanagari names — normalise inside adapter. Docstring-lies about return shape — test the observed shape, document it. Ayanamsha deltas not matching expected arithmetic — PyJHora is authoritative; verification is *internal arithmetic only*, not an oracle. Writer producing zero rows after rewire — hard fail, surface to cockpit, do not silently skip. `multiprocessing.Pool` deadlocking — switch start-method to `spawn`.

### 8.5 Out of scope (explicit non-goals)

JH-parity oracle of any kind. Spike of any kind. License check. Schema migrations. Frontend changes. Pariksha integration (handled in a follow-on PR). Governance-doc cleanup of legacy natal_engine + jh-parity references (separate cleanup arc). JSONL → FORENSIC-schema markdown renderer (R7 in the FACT_ENGINE review, deferred). L1.md regeneration — `chart_facts` DB rows are the source of truth.

### 8.6 Execution sequence for the Antigravity executor

Twelve steps: branch off `feature/pyjhora-direct-engine`, Phase 1 (deps), Phase 2 (adapter scaffolding), Phase 3 (isolation), positions + houses + tests, dignities + vargas + dashas + tests, panchanga + strength + sensitive_points + yogas + tests, Phase 4 (writer rewire — one writer at a time, test each), Phase 5 (delete `natal_engine/` only after every writer passes), Phase 7 (native chart e2e), Phase 6 (arch docs minimal diff), open PR with the 8-row AC checklist. Halt at PR-to-main.

### 8.7 What was rejected from the prior FACT_ENGINE review

`00_ARCHITECTURE/FACT_ENGINE_BRIEF_REVIEW_v1_0.md` (2026-05-27) proposed eight amendments to an earlier brief that has since been deleted. R1 (use `JHORA_TRANSCRIPTION_v8_0_SOURCE.md` as the primary oracle) was rejected — it is still a JH-parity gate, contradicting `[[no-jh-parity-anywhere]]`. R2 (triangulation is not independent on the ayanamsha axis), R3 (Tier-3 is single-oracle), R4 (isolation explicit), R5 (multi-chart golden set), R6 (input contract generalises beyond IST), R7 (renderer is a second projection), and R8 (ephemeris source asserted per run + per-section ayanamsha config table) are folded into the implementation brief as relevant.

## 9 · Worktree, branch, and execution layout

For parallel autonomous sessions, the project uses git worktrees so each Antigravity window owns a separate checkout (memory hook `[[parallel-sessions-need-worktrees]]`). For the PyJHora arc, a single worktree suffices.

Useful paths: `start_db_proxy.sh` lives at `platform/scripts/start_db_proxy.sh`, runs on port 5433. GCP project `madhav-astrology`, region `asia-south1`. Cloud Run services: `amjis-web` (Next.js portal), `amjis-sidecar` (python-sidecar with PyJHora), `amjis-mcp` (MCP sidecar). The deploy workflow `.github/workflows/deploy.yml` has `deploy-web`, `deploy-sidecar`, and `deploy-mcp` jobs. `/api/health` is auth-gated. `mint_session_cookie.ts` emits `__session` cookies for local testing.

Open PR + branch convention: per-arc feature branches, `feature/<arc-name>`, opened via `gh pr create`. Halt at PR open. Native reviews and merges from the GitHub UI or via `gh pr merge`.

## 10 · The build orchestrator's known gap

`marsys-build-pipeline-job` in Cloud Run has no watchdog (memory hook `[[build-orchestrator-no-watchdog]]`). 32 stuck builds accumulated over 39 hours and were surfaced on 2026-05-31. A one-shot cleanup ran (`UPDATE builds SET status='cancelled', cancelled_at=NOW()` where stuck). `BUILD_TIMEOUT_HARDENING` brief is open. Schema gotchas to know: `build_steps.status` CHECK constraint allows `queued / running / complete / failed / skipped` (NOT `cancelled` or `pending`); `builds.cancelled_at` exists; `cancel_reason` does not exist.

The PyJHora arc does not address the watchdog gap. That is a separate concurrent workstream.

## 11 · Open operator actions (high priority)

These are blocking items the next conversation should be aware of and that gate further work. The authoritative tracking file is `00_ARCHITECTURE/OPERATOR_ACTIONS_PENDING.md`.

(a) **Multi-Ayanamsha build operator queue** — apply migrations 140–153 to production, run ACC1 `answer:eval` after the build job, run ACC3 IS.8(b) native red-team, run ACC4/ACC5 smoke tests post-deploy, trigger the native chart build. Until done, M6-A-S1 cannot open.

(b) **Platform Modernization v1.3 partition scaffolding** — migrations 121/122/124 for `query_trace_steps` partitions are BLOCKED on `chart_id` being 100% NULL in those tables. Unblocks only after the new engine writes per-chart rows — i.e. after the PyJHora arc lands and a build runs end-to-end.

(c) **MCP Transformation post-merge** — migrations 072–080 need to be applied. (Status unconfirmed in governance docs after CLOSEOUT-2026-05-22; verify against prod DB schema for tables `mcp_bundle_cache`, `mcp_audit_findings`, `mcp_predictions`, `data_source_expected`, `multi_school_stances`, `school_convergence_index`.)

(d) **Phase 4B prereq for Phase 4C SQL cache layer** — sunrise derivation + MEAN_NODE rebuild remains a prerequisite for `query_panchanga`'s SQL cache layer. Not a blocker for Wave 1 close — 4C is engine-direct in production.

(e) **CF.V13.2 — bootstrap manifests auto-registration** — UDA-4 claimed it was fixed but the verification commit is missing. Resolution criteria documented in `V1_3_AUDIT_QUEUE_v1_0.md` CF.V13.2.

## 12 · Key file paths the new conversation will need

Governance and architecture: `CLAUDE.md` (root); `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`; `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`; `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md`; `00_ARCHITECTURE/MACRO_PLAN_v2_0.md`; `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`; `00_ARCHITECTURE/V1_3_AUDIT_QUEUE_v1_0.md`; `00_ARCHITECTURE/OPERATOR_ACTIONS_PENDING.md`.

The PyJHora arc: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md` (this PR); `00_ARCHITECTURE/FACT_ENGINE_BRIEF_REVIEW_v1_0.md` (the review whose R1 is rejected, R2-R8 folded in).

Pariksha: `00_ARCHITECTURE/PARIKSHA/PARIKSHA_MASTER_PLAN_v1_0.md`; `00_ARCHITECTURE/PARIKSHA/briefs/PRAMANA_DRASHTA_v1_0.md`; `00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml`; `00_ARCHITECTURE/PARIKSHA/ASSET_REGISTRY.md`.

Channels: `platform/web/src/app/api/consume/v2/route.ts` (legacy + R11 entry point); `lib/providers/agentic_loop.ts` + `lib/providers/dispatcher.ts` + `lib/providers/adapter.ts` + per-provider adapters (R11); `platform-mcp/src/server.ts` (MCP).

Engine (deprecating): `platform/python-sidecar/natal_engine/`. Engine (new): `platform/python-sidecar/pyjhora_adapter/` (to be created).

Build orchestrator: `platform/python-sidecar/pipeline/` (the writers + dispatcher); the Cloud Run Job is `marsys-build-pipeline-job`.

Cockpit: `src/components/cockpit/` (Yantra Chitra v2 components shipped in the build E2E arc).

## 13 · How to act in the next conversation

Re-read `CLAUDE.md` and `CURRENT_STATE_v1_0.md` first. Verify state from git, not from CLAUDE.md §F. Read the PyJHora implementation brief end-to-end before any code edit. Honor the standing constraints in §7. Use Cowork to plan and author; use Antigravity to implement.

If the user asks you to start the PyJHora work, the next action is to paste the Antigravity kickoff prompt from the bottom of `CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md` into a new Claude Code chat in the Antigravity IDE. Do not author a new brief. Do not run a spike. Do not propose a JH-parity test.

If the user asks for status, read `CURRENT_STATE_v1_0.md §2` (the canonical state block) and the latest entries in `SESSION_LOG.md`, then summarise — never recite the frozen "you are here" block from CLAUDE.md §F.

If the user asks to change architecture, surface the change as an amendment proposal first and wait for explicit approval before any artifact mutation. Versioning discipline is in `PROJECT_ARCHITECTURE_v2_2.md §B`.

If the user asks for the visual diagram of the pipeline rendered in the previous conversation, the title was `marsys_chart_build_pipeline_l1_l5` (an SVG show_widget). Re-render with the same title if you need to refresh it.

## 14 · Footer

This handoff is point-in-time as of 2026-06-01. The project moves fast — re-verify any claim about "current" state against `CURRENT_STATE_v1_0.md` and `git log` before acting on it.

CLAUDE.md is at v4.9. CURRENT_STATE is at v5.65. Main HEAD as of authoring is post-Multi-Ayanamsha Build close (2026-05-30) and post Pariksha P0 PR #183.

*End of CONTEXT_HANDOFF_2026-06-01_v1_0.md.*
