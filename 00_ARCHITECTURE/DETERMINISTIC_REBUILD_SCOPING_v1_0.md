---
artifact: DETERMINISTIC_REBUILD_SCOPING_v1_0.md
document: Deterministic L2.5 Rebuild — Comprehensive Scoping Document
status: SCOPING (Cowork-authored; no implementation; carry to next session)
version: 1.0
date: 2026-05-29
authored_by: Claude (Cowork) — synthesis of conversation history, on-disk plans, codebase audit
intended_for: Next Cowork or Claude Code session opening on this workstream cold
self_containment: This document embeds the essential content so the receiving session does NOT need to explore, grep, or guess. Every load-bearing claim cites the file it came from.
expose_to_chat: false
---

# Deterministic L2.5 Rebuild — Comprehensive Scoping Document

> **Read order for the receiving session:** §0 → §1 → §2 → §3 → §4 → §5 → §6 → §7 → §8 → §9 → §10 → §11.
> §0 is the one-paragraph orientation. §1–§4 are the history and "as-is" state. §5–§7 are the proposed
> architecture. §8 is the design forks that must be resolved before implementation. §9 is governance
> and adjacencies. §10 is execution pattern. §11 is success criteria + references.

---

## §0 — One-paragraph orientation

The MARSYS-JIS platform's data layer is **structurally contaminated** — the supposedly factual synthesis assets (MSR, UCN, CDLM, CGM, RM) are not derived from a deterministic engine but were authored by an older system that applied **threshold-filtered, model-judged authoring**. The Platform Modernization arc that sealed 2026-05-27 + the v1.1 + v1.2 operator cleanup passes (sealed 2026-05-29 at HEAD `790673a0`, tag `platform-modernization-v1-2-complete`) **prepared the platform for a deterministic rebuild but did not execute it** — schema is keyed, FK columns added, partition scaffolding proven on the time-series tables that don't depend on engine output, multi-tenant authz live, the natal engine code exists and passes JH-parity tests against the user's JH oracle fixture. **What is not done: the engine has never been invoked against the user's birth data to produce live artifacts.** The `chart_id` column on `chart_facts` and `l25_msr_signals` is 100% NULL because nothing has written per-chart rows yet. This document scopes the workstream that closes that gap: invoke the engine end-to-end, replace the FORENSIC-markdown-extraction pipeline with engine outputs, regenerate L2.5 with the "keep all signals with computed coefficient" discipline (no threshold drop), validate against the frozen older corpus, cut over atomically. **Status: not yet started; two design forks must be resolved first (§8).**

---

## §1 — Project identity + native context

**Project:** MARSYS-JIS — an LLM-operated Jyotish (Vedic astrology) research instrument.
**Native (subject, first chart):** Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, India (lat 20.233333°, lon 85.833333°).
**Project mission** (CLAUDE.md §A): "Build an LLM-operated Jyotish instrument that reads the chart with acharya-grade depth; surfaces patterns and contradictions across layers no individual astrologer could hold in working memory; makes time-indexed, probabilistic, calibrated predictions testable against lived reality and correctable from outcomes. Then extend the method beyond this native so the instrument becomes a research tool for astrology as a discipline."
**Acharya-grade quality standard** (CLAUDE.md §J): an independent senior Jyotish acharya reviewing the corpus should reach one of "this is my own level / this is above my level / this reveals things I wouldn't have seen on first pass." Nothing less.
**Now multi-tenant:** the platform has been refactored along two axes: multi-**guest** (login accounts; role `super_admin` or `guest`) and multi-**chart** (subjects whose charts are built; one guest can own many charts). The second tenant (the native's own chart rebuilt under the new architecture) is live alongside the legacy first tenant — they coexist on the production DB. See `project_multitenant_refactor_decisions.md` in conversation memory.

---

## §2 — Full history (how we got here)

### §2.1 — The older system (pre-modernization authoring discipline)

Until ~mid-May 2026, all synthesis assets were authored by Claude sessions reading FORENSIC + classical references + the user's life event log, with the following discipline:

- **Threshold-filtered signal authoring.** MSR pattern extraction passes (M9-A-S1 in ~2026-05-14 was the last) wrote signals into `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` *only when* the authoring session deemed strength_score ≥ ~0.5 and confidence ≥ ~0.6. Sub-threshold signals were never written to the file at all. **The drop happened at the authoring stage, invisibly, and is the single most consequential contamination** (per `MSR_UCN_CONTAMINATION_AUDIT_v1_0.md` §0).
- **Hand-assigned scores.** Each `SIG.MSR.NNN` carries `strength_score`, `confidence`, `valence`, `domains_affected` — all assigned by the authoring model, not computed. The YAML-with-derivation-ledger form makes them look computed; they are not.
- **Pre-filtered signal pool ⇒ silent drop of weak/wide-orb/single-source patterns.** Every observable configuration *should* be a row with a strength column; instead only the "strong enough to write down" ones exist.
- **Interpretive claims inside "fact" fields.** `signal_name` carries claims ("Sasha Mahapurusha Yoga — Saturn Exalted in 7H Kendra" implies "this is a Yoga that grants Mahapurusha qualities") rather than neutral structural descriptors.
- **UCN is interpretation-by-design but mislabelled.** UCN (`UCN_v4_0.md`, 102 numbered subsections across Parts I–X+, 1,802 lines) is a model-authored narrative reading of the chart — acharya-grade as a reading, but used as upstream input to retrieval, which means panelist models read pre-loaded conclusions rather than re-deriving from positions.
- **Query-time threshold filtering on top of authoring-time threshold filtering.** `platform/src/lib/retrieve/msr_sql.ts` carried `CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`, `LL1_PRODUCTION_WEIGHTS` constants that further filtered MSR retrievals before returning to the model — dropping already-curated signals again at query time.

This is the system the rebuild replaces.

### §2.2 — Platform Modernization arc (sealed 2026-05-27 @ `ab7e1a95`)

A five-batch autonomous Conductor program (one orchestrator + parallel sub-agents in three worktrees, per-batch re-kicks, zero human approval gates) that shipped:

- **The natal engine code itself.** `platform/python-sidecar/natal_engine/` — pure-Python, no LLM imports (enforced by `test_no_llm.py`), Swiss Ephemeris + classical rule tables. Public API: `compute_chart(inputs, engine_version, ayanamsha_id) -> dict` returning a `CHART_OUTPUT_SCHEMA`-validated dict that can be appended as one JSONL line. Default engine version: `natal_engine/0.2.0-jh-parity`. Default ayanamsha: `jh_true_chitra` (pinned to JH's 23°37′09.78″). Submodules: `ascendant.py`, `ayanamsha_registry.py`, `dashas.py`, `dignities.py`, `houses.py`, `panchanga.py`, `positions.py`, `provenance.py`, `schema.py`, `sensitive_points.py`, `vargas.py`. Determinism contract: same inputs + engine_version + ayanamsha_id ⇒ byte-identical output.
- **JH-parity test battery.** `tests/test_jh_parity.py` validates engine output against `fixtures/jh_oracle.json` — your full JH export (datetime 1984-02-05T10:43:00+05:30, ayanamsha "Lahiri (Chitrapaksha True)" = 23.619383°, ascendant + 9 grahas + vargas D1/D9/D10/etc + dashas). The engine passes parity at G1 hard-gate level (residual ≤8″ on inner planets when run with Swiss Ephemeris files present).
- **The L1→L2.5 deterministic builder.** `natal_engine/l25_builder/build.py` — takes a `chart_output` dict + an operator-assigned `chart_id` and emits row-shaped dicts for the L2.5 stores. Determinism contract: same chart_output (modulo `provenance.computed_at_iso`) + same chart_id ⇒ byte-identical canonical-JSONL. **Crucial caveat from its own docstring:** *"Tested by `tests/test_l25_builder.py` (structural acceptance only — never runs a model)."* The builder produces in-memory rows; **a loader to write them to Postgres tables does not exist yet**.
- **The L1.5 runtime layer** (built during MCP Transformation v3.x, 2026-05-22). `chart_facts` table (2,717 rows × 27 categories, extracted from FORENSIC v8.0 markdown → `gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` → DB by `pipeline/writers/chart_facts_writer.py`). `rag_chunks` table (4,589 chunks: BPHS 1,615 + Jaimini 404 + KP 2,237 + Tajaka 333; chunked + Vertex AI 768-dim embedded). `school_convergence_index` materialized view (574 rows). **None of this was computed by the engine** — it's structured-extraction from hand-authored markdown.
- **Multi-tenant data plane.** `chart_grants` ACL table, `owner_id` + `subject_name` columns on `charts`, row-level security on `charts`, role rename `client` → `guest` on `profiles`, `chart_id` UUID FK columns added to `chart_facts` + `l25_*` tables (currently NULL — see §3.4).
- **Multi-tenant UI plane.** Cockpit (`platform/src/app/cockpit/` — command-center, activity, health, interventions, plan, registry, sessions, parallel). Per-chart pages (`platform/src/app/clients/[id]/` — build, consult, consume (PARTIAL rename in progress), panchang, timeline). Command Center surfaces runtime feature-flag toggles to super-admin.
- **The de-judgment in `msr_sql.ts`.** Wave-3 unit `3.dejudge` (commit `7f85b87c`) stripped `CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`, `LL1_PRODUCTION_WEIGHTS` from query-time filtering — model now receives all signals from the file with their coefficients, no sub-threshold drop at retrieval. **This fixes the retrieval-side threshold; the authoring-side threshold (the deeper problem) remains.**
- **Infrastructure substrate** — `marsys-build-pipeline-job` Cloud Run Job (the orchestrator that will eventually drive the engine end-to-end; exists, not wired to the engine), Memorystore Redis `amjis-cache`, Cloud Tasks queue `amjis-build-queue`, edge LB + Cloud CDN + Cloud Armor at `34.13.127.199`, monitoring dashboards + SLOs (alerts partial — channel created, log-based metrics not yet emitted).
- **Eight hard gates GREEN at seal:** `naming_ci`, `jh_oracle_pinned`, `G1_jh_parity`, `G2_authz_live`, `G3_contract`, `G4_no_native_lit`, `G5b_onfinish`, `G6_tool_coverage`. 223/223 tests green.

**Sealing artifacts:** `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md` + `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md` (0 class-1, 3 class-2, 4 class-3 dispositioned).

### §2.3 — Operator cleanup v1.1 (closed-with-deferrals 2026-05-28 @ `5464919e`)

Nine phases closed: D infra terraform (cloud_tasks/memorystore/scheduler/edge/iam), E `BUILD_TRIGGER_ENABLED=true`, G `amjis-db-password` v1→v2, H tracker retired, I depth-selector locked, **J1–J4 Cloud SQL → `db-custom-2-4096` + REGIONAL HA + PITR**, K doc+git+CI hygiene, M final verify+tag+report.

**Deferred:** Phase C tail (migrations 086–090 + 118 + 119 — 086 was authored against a greenfield `charts(chart_id PK)` shape vs prod's legacy `charts(id UUID PK, birth_date, birth_time)`); Phase F live `answer:eval`; full Phase J5 partitions.

### §2.4 — v1.2 follow-on patch (sealed 2026-05-29 @ `790673a0`, tag `platform-modernization-v1-2-complete`)

**Closed:**
- **Phase A:** All 8 deferred migrations applied to prod with smoke between each — `086_0` (the new charts-alignment keystone — adds `chart_id` as a secondary unique key alongside legacy `id`) + `086`+`087`+`088`+`089` (L2.5 chart_id+ayanamsha keying) + `118` (build_events) + `119` (calibration stamps) + `090` (IRREVERSIBLE `audience_tier` column drop after dual-policy C1 grep PASS). Two inline patches required at runtime: `chart_id TEXT→UUID` on 086-088 FK columns + staging mirrors (the migration authors assumed text keys; prod is UUID); `data_source_expected` shape guards on 086+088 (live table is Wave-3+ tool-coverage shape).
- **Phase B:** Migration `123` partitions `query_trace_steps` by RANGE(created_at) monthly — 11,631 rows across 14 partitions, atomic swap, archive preserved.
- **Phase F:** `answer:eval` v1.1 baseline LIVE (was STUBBED) — eval_run `ac44c3cd…`, 9.6 min wall clock, 11/15 queries, **layer_cov=31%, b10=95%, b11=29%**. F.3 regression check `TIE_BY_STUB` → PASS. *The 29% B.11 holistic-read floor compliance is the strongest quality signal in the baseline; it tells you the model is consulting L2.5 holistic content on under a third of queries.*
- **Phase J3':** REGIONAL HA failover test — 22.5 s op time / 39 s end-to-end (chat HTTP 200 throughout). HA proven.
- **Phase J4':** PITR clone to T-25min queryable + torn down clean. PITR proven.
- **Phase H' (cost right-sizing):** Cloud SQL `db-custom-2-4096 REGIONAL` → `db-custom-1-3840 ZONAL + PITR`. Savings ~$120-150/month while internal (scale back up when opening publicly).
- **Phase R residuals:** R3 (amjis-web → `amjis-web-runtime` least-priv SA, rev 00430-g8l); R4 (3 missing secrets backfilled to inventory); R5 (4 CI gates added).

**Deferred to v1.3 / v1.3.5:**
- **Migrations 121, 122, 124** — partition `chart_facts` (HASH by chart_id, 8 buckets), `l25_msr_signals` (HASH by chart_id, 8 buckets), `mcp_predictions` (RANGE monthly). **BLOCKED on `chart_id` 100% NULL on chart_facts + l25_msr_signals** + FK constraints on mcp_predictions. **This is the same dependency this Deterministic Rebuild resolves.**
- **R1+R2 monitoring alerts/SLOs** — email channel created but live apply blocked on log-based metrics not yet emitted + amjis-web monitoring service not yet registered.
- **Phase L engine hygiene** — D1 dignity table population + ayanamsha residual tighten (7.62″ → <1″ via SE_SIDM_USER pin at JH's 23°37′09.78″).

**Closing report:** `00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_V1_2_REPORT_v1_0.md`.

### §2.5 — The user's stated discipline (load-bearing, must respect)

From conversation memory + native directives:

1. **JH (Jagannatha Hora) is the sole formula authority** — Tier-3 too. Validate-once vs JH report; the natal engine's correctness is determined by parity with JH, not by re-deriving the formulas. The `jh_oracle.json` fixture is the parity oracle.
2. **No LLM in the compute path.** Enforced by `tests/test_no_llm.py`. Compute is pure Python + Swiss Ephemeris + classical rule tables.
3. **GCP-only deployment.**
4. **Anthropic / Claude API is banned for runtime calls unless the native explicitly asks** (cost). Default Gemini, fallback DeepSeek; cheap flash for non-critical, Gemini Pro / DeepSeek v4 Pro for critical. *This applies to runtime calls inside the platform — it does NOT prevent Claude Code as the implementation executor.*
5. **Executor = Claude Code in Google Antigravity IDE,** NOT the CLI. Briefs/prompts must embed all git+terminal commands for paste; no separate terminal steps required from the native.
6. **Cowork = planning only.** All implementation goes to Claude Code. Every Cowork output must be a pasteable prompt or a committed `.md` brief — never chat bullet points the native has to translate manually.
7. **PR-to-main is human-gated.** Per-session commits autonomous; merges, prod deploy, prod DB ops, secret/flag flips are human gates. Each conversation/stream owns its branch; never modify another stream's branch (cherry-pick-to-main to recover contamination).
8. **Parallel executors need worktrees.** 3+ parallel Antigravity sessions can't share one checkout. Pre-create `git worktree add` per stream before opening windows.
9. **Verify state from CURRENT_STATE + git log, not CLAUDE.md §F.** The §F "you are here" line is frozen/stale.
10. **The user is preparing to scale to ~10 internal users** for the next several months, then open publicly later. Infra is sized for low-intensity internal use (db-custom-1-3840 ZONAL + PITR); scale back UP before public open.

---

## §3 — Current architecture (as-is, post v1.2)

### §3.1 — Layer model

| Layer | What it holds | On disk now | Status |
|---|---|---|---|
| **L1 Facts** | FORENSIC v8.0 (markdown — 30 H2 sections, 79 H3, 1,938 lines), LEL v1.7 (57 events + 5 period summaries + 8 chronic patterns) | `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`, `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | FORENSIC: hand-authored; LEL: native-disclosed |
| **L1.5 Runtime** | `chart_facts` (2,717 rows × 27 categories), `rag_chunks` (4,589 chunks), `school_convergence_index` MV (574 rows), `l25_msr_signals` (added in 086; **chart_id 100% NULL**) | Postgres on `amjis-postgres` | chart_facts + rag_chunks: built MCPT 2026-05-22 via structured extraction (NOT engine-computed) |
| **L2.5 Synthesis** | MSR v5.1 (573 signals), UCN v4.1 (102 subsections), CDLM v1.3 (81 cells = 9×9), RM v2.2 (33 resonances), CGM v9.1 (284 nodes / 339 edges / 22 reconciled) | `025_HOLISTIC_SYNTHESIS/*.md` | All older-system threshold-filtered authoring (M9-A-S1 / ~2026-05-14 last expansion). DAR P5-S20 (2026-05-25) added derivation_ledger grounding; no new signals. Surgical fixes only since (MSR.377 + MSR.387). |

### §3.2 — Current data flow (what runs at query time)

```
[user query @ /api/chat/consult or /api/chat/consume]
        ↓
[planner reads L2.5 hand-authored MSR/UCN/CDLM/RM/CGM .md files]
        ↓
[retrieval tools query L1.5 — chart_facts, rag_chunks, school_convergence_index]
        ↓
[de-judged msr_sql.ts returns ALL signals (no threshold drop) from the 573-row file]
        ↓
[synthesizer composes answer from retrieval bundle + planner-selected L2.5 subsections]
        ↓
[answer streamed to user]
```

### §3.3 — What is built but NOT wired in production

The natal engine + l25_builder code exist but are not invoked in any production code path:

- `grep -rn "from natal_engine\|import natal_engine" platform-mcp platform/src` returns **zero** matches. Nothing in the production codebase imports the engine.
- `natal_engine.compute_chart()` exists; nothing calls it.
- `l25_builder/build.py` exists; its docstring explicitly says *"never runs a model"* — only structural acceptance tests touch it.
- `marsys-build-pipeline-job` Cloud Run Job exists; its handler invokes the current YAML-extraction pipeline, NOT the engine.

### §3.4 — The `chart_id` NULL gap (the visible blocker)

Migrations 086–089 added `chart_id UUID` FK columns to `chart_facts`, `l25_msr_signals`, and sibling L2.5 tables. **Every one of those columns is currently 100% NULL** because nothing has written per-chart rows yet. This blocks:

- Migration **121** (chart_facts HASH partition by chart_id, 8 buckets) — partitioning on all-NULL key is meaningless
- Migration **122** (l25_msr_signals HASH partition by chart_id, 8 buckets) — same
- Migration **124** (mcp_predictions RANGE monthly) — FK constraint issue (separate cause but same workstream context)
- Per-chart query filtering on L1.5 / L2.5 tables (multi-tenant data plane built but data layer is still single-native-shaped)

**The unblock is the engine writing per-chart rows.** That is exactly this workstream's scope.

### §3.5 — Infrastructure state

- **Cloud SQL:** `amjis-postgres` on `db-custom-1-3840 ZONAL + PITR` (right-sized for internal; scale back up before public open).
- **Cloud Run services:** `amjis-web` (revision 00430-g8l on `amjis-web-runtime` least-priv SA), `amjis-sidecar`, `amjis-mcp`. All on rotated `amjis-db-password` v2.
- **Cloud Run Job:** `marsys-build-pipeline-job` — orchestrator for the build pipeline (currently runs YAML extraction; would be re-wired to run the engine).
- **Cloud Tasks:** `amjis-build-queue` — backs the per-chart Rebuild button (now live via `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true`).
- **Memorystore Redis:** `amjis-cache` at `10.42.0.3:6379`.
- **Edge:** HTTPS LB at `34.13.127.199`, Cloud CDN, Cloud Armor.
- **Build feature flag live:** `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true` — the cockpit Rebuild button enqueues into Cloud Tasks → invokes Cloud Run Job. End-to-end works for the YAML-extraction pipeline.

### §3.6 — Asset counts (current)

| Asset | Count | Provenance |
|---|---|---|
| FORENSIC v8.0 H2 sections | 30 | Hand-authored markdown |
| FORENSIC v8.0 H3 subsections | 79 | Hand-authored markdown |
| LEL v1.7 events | 57 | Native disclosure (46 prior + 10 at M5-A-S1) |
| LEL v1.7 period summaries | 5 | Native disclosure |
| LEL v1.7 chronic patterns | 8 | Native disclosure (6 prior + 2 at M5-A-S1) |
| chart_facts rows | 2,717 | FORENSIC markdown → YAML → DB (MCPT 2026-05-22) |
| chart_facts categories | 27 | Defined by `CHART_FACTS_SCHEMA_v1_0.json` in GCS |
| rag_chunks (classical) | 4,589 | BPHS 1,615 + Jaimini 404 + KP 2,237 + Tajaka 333; Vertex AI 768-dim embeddings |
| school_convergence_index MV | 574 | One row per MSR signal + 1 padding |
| MSR v5.1 signals | 573 | Older-system threshold-filtered authoring (last expansion M9-A-S1 ~2026-05-14) |
| UCN v4.1 subsections | 102 | Older-system narrative authoring |
| CDLM v1.3 cells | 81 (9×9 matrix) | Older-system matrix authoring |
| RM v2.2 resonances | 33 | Older-system resonance authoring |
| CGM v9.1 nodes / edges | 284 / 339 | Older-system graph authoring |

---

## §4 — Why the rebuild — the four contamination findings

From `MSR_UCN_CONTAMINATION_AUDIT_v1_0.md` §0 (verbatim): *"The factual base is contaminated, but not primarily by Anthropic-flavoured bias. It is contaminated by a deeper, structural issue: **MSR presents model judgment in the costume of data.** Hand-authored scores, a silently pre-filtered signal pool, in-line deliberation, interpretive claims inside 'fact' fields, and at least one authoring error that reached production all live inside a register whose YAML-with-derivation-ledger form makes them look computed."*

**Contamination C1 — opinion-scores-as-data.** Every `strength_score` and `confidence` field in MSR was assigned by the authoring model, not computed from inputs. The audit's prescription: split the coefficient into `{deterministic_strength, verification_certainty, computed_salience}`, where `deterministic_strength` is computed (orb-tightness × shadbala × dignity), `verification_certainty` is computed (source corroboration count), and `computed_salience` is the third decomposed value from a versioned formula.

**Contamination C2 — silent drop.** The signal pool was pre-filtered at authoring time. The native's instinct ("never drop data; keep coefficient instead of gating") is the correct fix. **Every observable configuration becomes a row, including weak / wide-orb / single-source ones. Strength becomes a column, not a gate.**

**Contamination C3 — in-line deliberation.** MSR signal bodies contain `supporting_rules`, `falsifier`, narrative `signal_name` claims — model deliberation captured as if it were data. The audit's prescription: structured `configuration` field (not prose), neutral structural `signal_name` descriptors, `constituent_facts[]` as fact_id references, `classical_sources[]` as canonical citations. Meaning becomes serve-time.

**Contamination C4 — interpretive prose in "fact" fields.** Same surface as C3 from a slightly different angle; same fix.

**Plus: at least one authoring error reached production** (DIS.013 — MSR.377 Muntha Libra 7H was wrong; resolved via direct rewrite, but the path that allowed it to exist is structural — hand authoring with no engine check).

---

## §5 — Proposed architecture (target state)

Reference: `DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md` (DRAFT 2026-05-27, on disk).

### §5.1 — The one-paragraph target

Every data asset becomes a **pure deterministic projection** of the JH-equivalent fact base, carrying **computed** values only — including a **computed salience** column on the synthesis layers. No model-authored prose, scores, names-as-claims, or curation survives in the data layer. **All interpretation (meaning, valence-for-this-native) moves to serve-time**, produced by the LLM panel reading T0 (classical) + the deterministic data layer. The current corpus is **frozen and archived** as a model-attributed reference, then the live canonical files are **replaced** by their deterministic regenerations after each passes the JH validation gate. Build order is forced: **fact engine → structural facts → signal/graph projections → serve-time synthesis.**

### §5.2 — The salience discipline (the load-bearing rule)

> *The salience **formula** is authored once, versioned, and committed as code/config. The salience **value** on every row is **computed** from deterministic inputs — never assigned by a model. Same chart + same `salience_formula_version` ⇒ identical salience, reproducibly, across all models.*

**Permitted salience inputs (all deterministic):** computed strength (aspect-orb tightness, shadbala of involved planet(s), dignity state), classical-source-corroboration count, divisional-corroboration count, dasha-activation proximity (is an involved planet's mahadasha/antardasha current or imminent), house-weight (kendra/trikona/dusthana — itself a deterministic classification), ashtakavarga bindu support.

**Forbidden in salience:** "how much this matters for this life," benefic/malefic-*for-native*, domain-importance opinion. These are serve-time interpretation, never a stored column.

### §5.3 — Per-asset rebuild specification

| Asset | Rebuild discipline |
|---|---|
| **FORENSIC (L1)** | Regenerated as the rendered view of the engine JSONL. Pure facts. Structure/IDs (MET.*, PLN.*, HSE.* …) preserved so existing tools/citations hold. Oracle: JH transcription. Already mostly fact. |
| **Structural fact layer (T1 expansion — NEW, feeds everything above)** | Aspect matrix, dispositor chains, cross-varga strength, yoga-presence booleans, nakshatra/KP sub-lord chains, proximity/criticality metrics, shadbala (+sub-scores), ashtakavarga (full matrices), vimshopaka, Tajaka predicates. All into `chart_facts` with `tier:T1, deterministic:true`. This layer **is** the deterministic-strength input for §2.3–§2.5 salience. |
| **MSR** | Every observable configuration gets a row — including weak, wide-orb, single-source ones. Strength is a **column, not a gate** (closes C2). Each row: `{signal_id, chart_id, configuration (structured, not prose), constituent_facts[], classical_sources[], deterministic_strength, verification_certainty, computed_salience, domains_affected (deterministic mapping via fact→domain table, not opinion), provenance:{engine_version, salience_formula_version, ...}}`. **Removed:** hand-assigned scores, names-as-claims, deliberation-in-fields, interpretive prose. Names become neutral structural descriptors; meaning is serve-time. |
| **CDLM** | Edges = computable shared factors between signals/configurations: shared planet, shared house, shared karaka, shared dasha-activation-window, mutual aspect. Each edge carries a **computed linkage-strength**. **Removed:** "this linkage means X across domains" narrative → serve-time. |
| **CGM** | Nodes = planets/houses/signs/configurations; edges = **computable structural relations**: aspect, dispositor, lordship, karaka, conjunction, parivartana. Each edge typed + weighted by computed strength. **Removed:** causal-outcome edges → serve-time. CGM stops being a *causal* model and becomes a *structural* graph. |
| **UCN** | No deterministic narrative equivalent. Replaced by a **computed signature digest**: top configurations by computed salience, system-convergence counts, dominant / weakest planets by shadbala, strongest yogas by computed strength, dasha-context — all salience-ranked, zero prose. Synthesized "argument of the chart" becomes a **serve-time output**. Old UCN → frozen archive. |
| **RM** | `computed_weakness (from shadbala/dignity/ashtakavarga) → classical_remedy` mapping table. Remedy prioritization → serve-time. |
| **LEL** | Unchanged in shape — native-disclosed event log. The rebuild does NOT regenerate LEL. (Future: LEL re-fit decision under JH dasha dates is a separate open item.) |

### §5.4 — Build order (forced dependency chain)

0. **JH fact engine + ayanamsha Phase-0 gate** — `oracle_map`, per-section ayanamsha, JSONL schema. *Status: code built, parity tests pass.*
1. **Structural fact layer (T1 derivations)** → `chart_facts`. *Status: NOT WIRED — current chart_facts comes from YAML extraction, not engine.*
2. **Signal enumeration (MSR) + CDLM/CGM projections + RM lookup + UCN digest**, all consuming §5.2 salience formula. *Status: not started.*
3. **Loader + renderer (JSONL → DB + JSONL → L1.md)**, read-compat verified. *Status: not started.*
4. **Archive freeze + cutover.** *Status: not started.*
5. **Serve-time synthesis layer + DAG runner wiring 0–4 into one-command build.** *Status: not started.*

`salience_formula_version` and `engine_version` are stamped on every row at every level.

### §5.5 — Projected counts after rebuild

| Asset | Current | Projected post-rebuild | Drivers |
|---|---|---|---|
| chart_facts rows | 2,717 | 4,000–6,000 (rough projection) | Engine outputs more granular per-entity per-divisional values than markdown summaries |
| MSR signals | 573 | **800–1,500** (rough projection) | (a) every pattern, no threshold drop; (b) FORENSIC v8.0 new sections §24/§25/§26/§6.6-6.8/§12.1-12.2 not fully harvested by M9-A-S1; (c) yogas register §26 alone has 100+ untapped |
| UCN | 102 subsections | Replaced by computed digest (no count comparable) | Narrative replaced by deterministic ranking |
| CDLM | 81 cells | Stays at 81 | Matrix is structurally 9×9; cell density grows |
| RM | 33 resonances | 50–80 (rough projection) | More strong-chart-nodes surface as MSR expands |
| CGM | 284 nodes / 339 edges | Grows with FORENSIC entity coverage | Already grew 234→284 in v9.1; further FORENSIC additions yield more |

**These are projections, not commitments.** True counts only known after execution.

---

## §6 — Archive + replace (corpus disposition + cutover)

1. **Freeze** the current FORENSIC/MSR/UCN/CDLM/CGM/RM as an immutable, version-tagged archive labelled `provenance: model_attributed`, `authoring_model: Claude/Anthropic`. Retained as (a) the judge-layer / serve-time **divergence-dividend** reference, (b) human acharya reading.
2. **Build new deterministic layer in parallel** (isolated namespace / `build_id`), never mutating canonical until validated.
3. **Per-asset JH/oracle gate must pass** before that asset's canonical file is replaced.
4. **Replace** live canonical files with deterministic regenerations; loader projects JSONL → existing Postgres schema unchanged (existing retrieval tools keep working); renderer projects JSONL → L1.md. Enumerate FK dependents before any DB swap.
5. **Version-bump** affected canonical surfaces + CLAUDE.md / PROJECT_ARCHITECTURE on cutover.

---

## §7 — Serve-time synthesis layer (where interpretation now lives)

All meaning-making is regenerated per query by the LLM panel reading **T0 (classical, from `rag_chunks`) + the deterministic data layer (T1, from `chart_facts` + L2.5 deterministic tables)**. The panel produces: signal valence-for-native, cross-domain narrative, the chart "argument" (old-UCN function), remedy prioritization.

Divergence between the live panel reading and the frozen archived synthesis is a **logged research output** (DISAGREEMENT_REGISTER candidate). This is the *research instrument* function — the platform becomes able to discover where deterministic + classical-corroborated readings diverge from a particular model's reading.

B.11 holistic-read is satisfied from T1, not from stored T2.

---

## §8 — Open design forks (resolve BEFORE implementation scope)

These are real, native-approval-gated decisions. Per `DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md` they remain open. The implementation campaign cannot start until they are answered.

### §8.1 — Fork 1: Upper-layer boundary

**Question:** Does L1.5 (the runtime serialization layer) survive the rebuild, or is everything served direct from L1?

**Option A — Keep L1.5.** Engine writes JSONL; loader projects JSONL → Postgres tables (`chart_facts`, `l25_msr_signals`, etc.); existing retrieval tools (MCP 40 tools, portal 51 tools) keep working unchanged because they query the same tables. Renderer projects JSONL → L1.md for the canonical reading surface.
- *Pro:* Zero change to retrieval surface. Existing tests pass. Minimal cutover risk.
- *Con:* Two serializations to maintain (JSONL + DB).

**Option B — Direct L1 → L2.5, retire L1.5.** Engine outputs the deterministic L2.5 directly; retrieval tools query the engine outputs directly (e.g., from JSONL on GCS or a new schema).
- *Pro:* Cleaner conceptually. Single canonical surface.
- *Con:* Every retrieval tool has to be reworked. MCP + portal tool contract changes. High blast radius.

**Cowork recommendation:** **Option A** — the L1.5 runtime serialization is a feature, not a bug; it decouples the engine from retrieval-tool stability. The engine becomes the authoring source of L1.5 instead of YAML extraction being the source, but the table shape stays the same. Existing tests survive.

### §8.2 — Fork 2: Old-corpus disposition

**Question:** What happens to the existing MSR/UCN/CDLM/RM/CGM files after the deterministic versions are validated?

**Option A — Supersede.** Replace the canonical files; old versions move to `99_ARCHIVE/` with `status: SUPERSEDED, provenance: model_attributed, authoring_model: Claude/Anthropic`.
- *Pro:* Clean. Single source of truth.
- *Con:* Loses the "model_attributed reference" for the divergence-dividend / research function.

**Option B — Archive + parallel.** New deterministic versions become canonical; old versions stay in `99_ARCHIVE/` and are loaded by the *judge layer only* (never the panelist) for divergence detection.
- *Pro:* Preserves the research-instrument function. Captures the divergence dividend.
- *Con:* Two corpora. More governance discipline required.

**Cowork recommendation:** **Option B** — the divergence dividend is one of the project's stated research goals (CLAUDE.md §A: "extend the method beyond this native so the instrument becomes a research tool for astrology as a discipline"). The old corpus is the artifact that lets you measure "what did the deterministic reading add / drop vs the acharya-grade narrative reading."

### §8.3 — Additional open items (carry-forward from spec)

- **Canonical JSONL schema + `oracle_map`** — next deliverable; everything keys off it.
- **Salience formula v1 definition + unit tests** — the §5.2 discipline made concrete.
- **DAG-runner design** — ~25 nodes; custom lightweight, content-addressed à la DVC.
- **LEL re-fit decision under JH dasha dates** — downstream of §4 review R1.

---

## §9 — Governance + adjacencies

### §9.1 — Architectural principles (CLAUDE.md §I — non-negotiable)

The rebuild must honor:

- **B.1 — Facts/Interpretation separation.** Facts live at L1; derivations at the L1/L2.5 boundary with explicit ledger; interpretations at L2.5+ only. *The rebuild deepens this: everything stored becomes fact-or-deterministic-derivation; interpretation moves to serve-time.*
- **B.3 — Derivation-ledger mandate.** Every L2.5+ claim carries a `DERIVATION_LEDGER` entry listing the specific L1 fact IDs it consumes. *The rebuild satisfies this by construction — every L2.5 row carries `constituent_facts[]` referencing fact_ids.*
- **B.8 — Versioning discipline.** Every canonical artifact carries frontmatter `version`, `status`, and a changelog. Registries must not disagree. *The rebuild must version-bump every affected canonical surface at cutover (§6 step 5).*
- **B.10 — No fabricated computation.** If a computation requires a specialist tool and the value is not already in L1, the session marks it `[EXTERNAL_COMPUTATION_REQUIRED]` with exact spec. *The rebuild closes this by construction — the engine IS the computation, no markers needed.*
- **B.11 — Whole-Chart-Read discipline.** Every query routes through L2.5 Holistic Synthesis first, surfaces cross-domain signals via the Cross-Domain Linkage Matrix, then produces its domain-specific answer. *The rebuild keeps B.11 — but now satisfied from T1 deterministic data rather than T2 stored synthesis.*

### §9.2 — Hard gates that must remain green

All 8 hard gates at the modernization seal:

| Gate | What it checks |
|---|---|
| `naming_ci` | Naming convention lint passes (77-violation baseline, deferred drawdown) |
| `jh_oracle_pinned` | `jh_oracle.json` fixture is pinned and unchanged at compute time |
| `G1_jh_parity` | natal_engine output matches JH oracle within tolerance |
| `G2_authz_live` | Per-chart authorization gate enforced at every endpoint |
| `G3_contract` | Tool contract (Zod schemas) unified across portal + MCP |
| `G4_no_native_lit` | No `NATIVE_CHART_ID` literal anywhere in production code |
| `G5b_onfinish` | `onFinish` parity across all adapters (persistence/prediction/log writes) |
| `G6_tool_coverage` | Every tool has data_dependency declared; every asset has a tool that exposes it |

The rebuild must keep all 8 green through every batch.

### §9.3 — Session-open + session-close discipline

Per CLAUDE.md §G + §H:

- Every session begins with a `session_open` handshake declaring `may_touch` and `must_not_touch` globs (`must_not_touch` empty fails validation). Validated by `platform/scripts/governance/schema_validator.py`.
- Every session ends with a `session_close` checklist. Validated atomically; only after validation passes does `SESSION_LOG.md` get appended.
- Red-team cadence (CLAUDE.md §M / MACRO_PLAN §IS.8): every third session OR every macro-phase close OR every 12 months. Failure to discharge halts close.

### §9.4 — Drift / lint / schema enforcement

- `platform/scripts/governance/drift_detector.py` — defaults to manifest mode (`*_USE_MANIFEST=true`); reads from `CAPABILITY_MANIFEST.json`. Must stay green.
- `platform/scripts/governance/naming_lint.py` — 77-violation baseline maintained; no new violations.
- `platform/scripts/governance/schema_validator.py` — session-open + session-close handshakes pass.

### §9.5 — Adjacent systems (rebuild must not break these)

- **MCP server (`amjis-mcp`).** 40 tools — including `query_chart_facts`, `query_signal_state`, `cross_school_lookup`, `holistic_bundle`, `multi_school_bundle`, `query_dasha_periods`, `query_panchanga`, `query_remedial_mantras`, etc. Tier-conditioned via API key + audience_tier (super_admin / acharya / client). All tools must keep working post-cutover.
- **Portal retrieval tools.** 51 tools — channel:both means many tools have both portal + MCP exposures via shared contract. Same data shape requirement.
- **answer:eval baseline.** `b11=29%, b10=95%, layer_cov=31%` (v1.1, 2026-05-29). Post-rebuild eval must NOT regress; expect b11 + layer_cov to improve materially because retrieval will surface richer L2.5 content.
- **Cockpit + per-chart pages.** All client-facing. Build button live. Must keep working.
- **Both tenants queryable** — legacy chart + new-architecture chart. Already validated in v1.2 prod smoke. Rebuild must preserve.

### §9.6 — Things explicitly out of scope for this workstream

- **LEL regeneration.** LEL is native-disclosed event log; engine doesn't author life events.
- **Multi-tenant UI refinements.** Cockpit + per-chart pages are live and adequate.
- **Public open / scale-up.** Separate workstream; current footprint sized for internal-only.
- **M5-A backlog** (LL.8/LL.9 scaffold, CDLM confirm, MSR reconciliation against planner expectations, LL.2 per-edge campaign, PPL cadence plan, JH scheduling). Concurrent workstream; resumes after rebuild lands.
- **M6 prospective testing** — paused for the modernization detour. Resumes after rebuild lands (because rebuild substantially reshapes what M6's prospective tests would be testing against).
- **R1+R2 monitoring alerts/SLOs apply** — small (~30-60 min) operational work; can land in any small future session.
- **Phase L engine hygiene** (D1 dignity table + ayanamsha residual tighten) — *may overlap with rebuild* since the engine has to be in shape for parity tests; reasonable to fold into the rebuild's Phase-0 (JH gate) work.

---

## §10 — Execution pattern (based on what worked for the modernization arc)

### §10.1 — Topology

The modernization arc validated **one Conductor orchestrator + parallel sub-agents in pre-created git worktrees + per-batch re-kicks**. Recommend the same:

- **Conductor session** in repo root — coordinates, halts, cherry-picks.
- **3+ worktrees** pre-created (e.g., `../MadhavRebuildEngine`, `../MadhavRebuildL25`, `../MadhavRebuildCutover`). Sub-agents work in isolation, no FS contention.
- **Per-batch re-kicks** — context budget per Conductor chat is ~20 sub-agents; native re-pastes the kickoff to start the next batch.
- **Halt-on-red + auto-rollback** — no human approval gates between phases; safety lives in automated rails (staging-first migrations, post-deploy smoke, default-off flags, hard ordering gates).

### §10.2 — Strangler / parallel-build pattern (per spec §3)

1. **Build new deterministic layer in parallel** (isolated namespace / `build_id`), never mutating canonical until validated.
2. **Per-asset JH/oracle gate** must pass before that asset's canonical file is replaced.
3. **Atomic swap** at cutover — rename old → `*_pre_rebuild_archive`, new → live. Keep archive for one green production day before drop.
4. **Cherry-pick to main on green.** Cherry-picks must be cleanly isolated — Conductor commits should touch only the workstream's scope.

### §10.3 — Wave / batch structure (proposed)

Forced by the build-order dependency chain (§5.4):

| Batch | Scope | Deliverables |
|---|---|---|
| **Batch 0 — Foundations** | Resolve §8 design forks. Author canonical JSONL schema + `oracle_map`. Define salience formula v1 + unit tests. DAG-runner skeleton. | Design decisions committed. Schema spec. Salience formula. |
| **Batch 1 — Engine wiring** | Wire `natal_engine.compute_chart()` into `marsys-build-pipeline-job`. Cloud Storage JSONL output. Engine runs end-to-end against native birth data. | Cloud Run Job emits chart_output JSONL on a Build click. |
| **Batch 2 — L1.5 cutover** | Loader projects engine JSONL → `chart_facts` table (replacing YAML extraction). Validate parity vs current 2,717 rows. Add new rows from engine's finer granularity. | chart_facts populated FROM engine; chart_id finally non-NULL. |
| **Batch 3 — Structural fact layer (T1)** | Per `STRUCTURAL_FACT_LAYER_SPEC_v1_0.md`: aspect matrix, dispositor chains, shadbala sub-scores, ashtakavarga matrices, etc. Into chart_facts with `tier:T1`. | T1 rows in chart_facts; salience inputs ready. |
| **Batch 4 — L2.5 enumeration (MSR + CDLM + CGM + RM)** | `l25_builder.build()` wired and run. Every signal becomes a row. Computed coefficient. Validate vs frozen old MSR (every old signal reappears + sub-threshold + new from FORENSIC v8 additions). | l25_msr_signals populated with chart_id keying. Projected 800-1,500 signals. |
| **Batch 5 — UCN replacement + archive freeze** | UCN replaced by computed signature digest. Old MSR/UCN/CDLM/CGM/RM frozen to `99_ARCHIVE/` with `provenance: model_attributed`. | New computed digest live. Old corpus archived. |
| **Batch 6 — Migration unblock + cutover validation** | Migrations 121 (chart_facts HASH partition), 122 (l25_msr_signals HASH partition), 124 (mcp_predictions RANGE) finally apply now that chart_id is populated. Full smoke. answer:eval baseline re-run. | Partitions live. b11 + layer_cov improved. Cutover validated. |
| **Batch 7 — Seal + close** | Red-team pass per IS.8(b). Version bumps on every affected canonical surface (CLAUDE.md, PROJECT_ARCHITECTURE, CANONICAL_ARTIFACTS). Final tag. Close report. | Seal artifact. CURRENT_STATE updated. |

Estimated total: 7-10 wall-clock days at the modernization arc's pace.

### §10.4 — Operational discipline (lessons from modernization + v1.2)

- **Live-schema verification before migration author.** v1.2's two inline patches (chart_id TEXT→UUID + data_source_expected shape guards) happened because migration authors didn't have a live view of production schema. Add a session-open step: dump `\d+ <table>` for every table the session will touch. Catches drift early.
- **Sub-agent stalls — inline fallback.** During modernization, 3 sub-agents stalled mid-run (runtime watchdog flakiness). Salvage by inspection of partial commits or tight-prompt retry. For long-poles, inline execution in the orchestrator is the right fallback.
- **autonomous sessions ship-but-don't-mount pattern.** Sub-agents author component+API+test then claim done, skipping the integration-mount. Briefs need "manual click-through reaches the new behavior" as a hard AC; integration tests must mount parent context, not inject props.
- **Brief amendment requires fresh prompt.** Executor follows the prompt's explicit step list, not the amended brief; new scope silently dropped unless you re-issue the prompt.
- **Gate check_commands need unique markers.** Anchor to a unique status field (e.g. `rebuild_batch_3_status: CLOSED`), never a loose regex.

---

## §11 — Success criteria + references

### §11.1 — Definition of done

The rebuild is complete when ALL of these are true:

1. `natal_engine.compute_chart()` runs end-to-end against the native birth data via `marsys-build-pipeline-job` and emits validated JSONL on a Build button click.
2. `chart_facts` is populated FROM engine output (not YAML); `chart_id` is non-NULL on every row; row count ≥ current 2,717 (projected 4,000-6,000).
3. `l25_msr_signals` is populated with `chart_id` keying; MSR signal count grows from 573 to the engine's "keep all with coefficient" total (projected 800-1,500).
4. Every L2.5 row carries `{deterministic_strength, verification_certainty, computed_salience, salience_formula_version, engine_version}` in provenance.
5. UCN replaced by computed signature digest (no narrative prose in the data layer).
6. CDLM, CGM, RM regenerated from engine outputs.
7. Migrations 121 (chart_facts HASH partition), 122 (l25_msr_signals HASH partition), 124 (mcp_predictions RANGE) successfully applied — they unblock now that chart_id is populated.
8. Old MSR/UCN/CDLM/CGM/RM files frozen to `99_ARCHIVE/` with `provenance: model_attributed`.
9. All 8 hard gates remain GREEN.
10. answer:eval baseline re-run shows b11 + layer_cov materially improved over v1.1's `b11=29%, layer_cov=31%`.
11. Both tenants (legacy + new-architecture) remain queryable end-to-end.
12. CLAUDE.md + PROJECT_ARCHITECTURE + CANONICAL_ARTIFACTS version-bumped to reflect the new canonical layer.
13. Red-team pass per IS.8(b) with 0 class-1 findings.
14. Final tag pushed; close-out report committed.

### §11.2 — Authoritative on-disk references (the receiving session should read these)

**Plans + spec:**
- `00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md` — the target spec (DRAFT, 2026-05-27)
- `00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md` — the architectural decision foundation
- `00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md` — T1 build specification
- `00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md` — the findings that motivated the rebuild
- `00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md` — multi-chart build platform
- `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md` — tech-debt + two-pipeline cleanup

**Engine code:**
- `platform/python-sidecar/natal_engine/__init__.py` — `compute_chart()` entry point
- `platform/python-sidecar/natal_engine/l25_builder/build.py` — L1→L2.5 deterministic transform
- `platform/python-sidecar/natal_engine/ayanamsha_registry.py` — three-ayanamsha isolation
- `platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` — JH parity oracle
- `platform/python-sidecar/natal_engine/tests/test_jh_parity.py` — parity test battery
- `platform/python-sidecar/pipeline/writers/chart_facts_writer.py` — current YAML→DB writer (to be replaced)

**Current data assets (the things being rebuilt):**
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — L1 facts
- `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — LEL (unchanged by rebuild)
- `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` — 573-signal MSR
- `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` — narrative UCN
- `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` — 81-cell matrix
- `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` — resonance map
- `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` — chart graph

**Governance + state:**
- `CLAUDE.md` — master instructions
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — canonical-path single source of truth
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — "you are here" pointer
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` — session protocol
- `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` — hygiene rule set

**Modernization arc closure:**
- `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_PLAN_v1_0.md` (v1.2)
- `00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_V1_2_REPORT_v1_0.md`

### §11.3 — Critical conversation-history context (not on disk)

- The native confirmed on 2026-05-27 that the deterministic data-layer rebuild is the right direction.
- The native rejected the older system's "drop sub-threshold signals" discipline explicitly: *"we will not drop everything, we will keep a coefficient next to each MSR signal."*
- Cost evaluation (2026-05-28): Cloud SQL right-sized to `db-custom-1-3840 ZONAL + PITR` for internal-only use; scale back to `db-custom-2-4096 + REGIONAL` before public open.
- Native preferences (memory):
  - JH is sole formula authority (Tier-3 too)
  - No LLM in compute path
  - GCP-only deployment
  - Anthropic API banned for runtime calls (Gemini default, DeepSeek fallback)
  - Claude Code in Antigravity IDE is the executor
  - Cowork = planning only

### §11.4 — Recommended first session of the workstream

**Session type: Cowork (planning).**

**Goal:** Resolve §8 design forks; commit decisions; author kickoff prompt for Batch 0.

**Inputs:** This document + the on-disk spec (`DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md`).

**Deliverables:**
1. Native-confirmed answers to §8.1 and §8.2 (record in this doc + the spec).
2. Author `00_ARCHITECTURE/CONDUCTOR/rebuild/DETERMINISTIC_REBUILD_PLAN_v1_0.md` — the executable plan (analogue to `OPERATOR_CLEANUP_PLAN_v1_0.md`).
3. Author `00_ARCHITECTURE/CONDUCTOR/rebuild/DETERMINISTIC_REBUILD_KICKOFF.md` — the paste-into-Claude-Code prompt for Batch 0.
4. Pre-create the worktrees (`git worktree add` × 3).

**Next session after that** is the Batch 0 execution in Claude Code (Antigravity IDE).

---

*End of DETERMINISTIC_REBUILD_SCOPING_v1_0.md — 2026-05-29 — Cowork-authored; native sign-off required on §8 design forks before implementation starts.*
