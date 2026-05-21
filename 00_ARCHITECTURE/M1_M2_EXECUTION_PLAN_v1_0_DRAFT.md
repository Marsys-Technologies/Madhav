---
artifact: M1_M2_EXECUTION_PLAN_v1_0_DRAFT
canonical_id: M1_M2_EXECUTION_PLAN
version: 1.0-DRAFT
status: DRAFT_PLANNING
authored_by: Claude (Cowork) 2026-04-29
authored_for: Native review + multi-stream parallel kickoff
parent_plan: 00_ARCHITECTURE/M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT.md (the strategic plan)
relationship_to_parent: |
  The master plan defines WHAT M2 closure requires. This execution plan
  defines HOW to execute it under the native's stated constraints:
  parallel long-running sessions, minimal user interference, generous
  token/compute budget. This document is the operating manual.
target_branch: redesign/r0-foundation

operating_constraints:
  - Parallel execution: 4–6 concurrent Claude Code sessions
  - Long-running: each session runs to completion without check-ins
  - Minimal user interference: native kicks off, monitors closing summaries, gates only at hard sync points
  - Generous compute: each brief embeds full diagnostics, tests, deploy, verification, and rollback
  - Disjoint file scopes per brief — must_not_touch boundaries enforce parallel safety
intended_disposition: |
  Promotes to CURRENT after native review of §3 Autonomous Brief Contract
  and §6 Wave Dispatch. After promotion, this document is the reference
  for every M2 implementation session through M2 close.
---

# M1/M2 Execution Plan v1.0 (DRAFT)

## §0 — Operating constraints

Per native directive 2026-04-29:

1. **Parallel** — 4–6 concurrent Claude Code sessions, each in its own terminal tab on the same `redesign/r0-foundation` branch.
2. **Long-running, autonomous** — each session runs end-to-end. No questions back to the native mid-session except for genuine, unrecoverable blockers.
3. **Minimal user interference** — native role is: (a) kickoff each brief with the prepared prompt, (b) read closing summaries when sessions complete, (c) decide cross-stream sync gates when those rare moments arrive.
4. **Generous compute** — embed full diagnostics, tests, deploy + verification, rollback paths inside every brief. No "user will catch this in review" handoffs.

This document is the operating manual. The companion `M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT.md` is the strategic plan (what + why); this is the tactical plan (how + when + by whom).

## §1 — Stream architecture

Six parallel streams, allocated by file-system domain. The disjoint `must_not_touch` boundaries make concurrent execution safe — no two streams ever edit the same file in the same wave.

| Stream | Domain | Path scope | Sequential within stream | Parallel-safe vs other streams |
|---|---|---|---|---|
| **A** | Backend / Python sidecar / ETL | `platform/python-sidecar/**`, `platform/migrations/**`, `platform/scripts/**` | Yes | Yes — owns all Python |
| **B** | TypeScript retrieval tools | `platform/src/lib/retrieve/**`, `platform/src/lib/router/**` (read-only after 11C_b) | Yes | Yes — owns retrieval-side TS |
| **C** | Discovery / corpus expansion | `035_DISCOVERY_LAYER/REGISTERS/**`, JSON outputs only | Yes | Yes — owns corpus content |
| **D** | Synthesis / orchestration | `platform/src/lib/bundle/**`, `platform/src/lib/synthesis/**`, new `per_tool_planner.ts` | Yes | Yes — owns orchestration TS |
| **E** | Observability + schema | `platform/migrations/**` (new), `platform/python-sidecar/pipeline/writers/audit_*.py`, `platform/src/lib/audit/**` | Yes | Yes — touches schema once |
| **F** | Integrity + eval + close | `platform/python-sidecar/rag/eval/**`, integrity probe scripts, M2_CLOSE_BASELINE artifact | Yes | Sequential — runs last |

**Critical rule:** Stream A's migrations and Stream E's migrations do not overlap. Stream A migrates `msr_signals`, `chart_facts`. Stream E migrates `audit_events`, `query_plans`. Both can run concurrent because they touch different tables; but the migration filenames must not collide. Migration numbering convention: Stream A uses 022–025; Stream E uses 026–027.

## §2 — Brief catalog (the full list)

Eighteen briefs total. Numbered by stream + sequence within stream. Each brief is one Claude Code session.

### Stream A (Backend / ETL)

| # | Brief | Scope summary | Effort | Predecessor |
|---|---|---|---|---|
| A1 | `M2_PHASE_ALPHA` | 4 audits: chart_facts schema, msr_signals columns, classifier output on factual queries, FORENSIC § coverage matrix | 1 session | None |
| A2 | `M2_A1_MSR_ETL` | Add signal_type, temporal_activation, valence, classical_source, falsifier, supporting_rules, rpt_deep_dive, entities_involved, v6_ids_consumed columns to msr_signals; re-ingest | 1 day | A1 |
| A3 | `M2_A2_CHART_FACTS_ETL` | Extend chart_facts ETL to cover all FORENSIC §1–§27 sections; target 1,800–2,500 rows | 2 days | A1 |
| A4 | `M2_A_MINOR` | Consolidated: M2-A.3 Vimshottari sub-period extension + M2-A.4 pada column + M2-A.5 chalit dual-house | 1 day | A1 |
| A5 | `M2_B1_CGM_FULL_EDGES` | CGM edge expansion 126 → ~339 across all 15 source edge types (YOGA_MEMBERSHIP, OWNERSHIP, TENANCY, GRAHA_ASPECT, etc.) | 2 days | None |
| A6 | `M2_B2_CHUNKER_COMPLETION` | UCN H3 sub-section chunker upgrade; cgm_node UCN merge; LEL period summaries + chronic patterns chunked | 1.5 days | None |

### Stream B (TypeScript retrieval tools)

| # | Brief | Scope summary | Effort | Predecessor |
|---|---|---|---|---|
| B1 | `M2_C6_VECTOR_SEARCH_FILTER` | Add doc_type[] + layer filter to vector_search.ts; classifier prompt update; tests | ½ day | None |
| B2 | `M2_C234_BUNDLE` | Consolidated: kp_query + saham_query + divisional_query (3 small tools, no DB schema change) | 1.5 days | A3 |
| B3 | `M2_C1_CHART_FACTS_QUERY` | The big one: chart_facts_query parametric tool — shadbala/BAV/SAV/KP/saham/divisional/aspects | 1.5 days | A3 |
| B4 | `M2_C5_TEMPORAL_EXTENSION` | Extend temporal tool: dasha_chain + sade_sati_status + ephemeris_range + eclipses_in + retrograde_stations_in | 1 day | A4 |
| B5 | `M2_D234_BUNDLE` | Consolidated: domain_report_query + remedial_codex_query + timeline_query (3 L3/L4/L5 tools) | 1.5 days | None |

### Stream C (Discovery sessions — Gemini-led)

| # | Brief | Scope summary | Effort | Predecessor |
|---|---|---|---|---|
| C1 | `M2_B3_CLUSTER_RECLUSTER` | Re-cluster MSR with target ≥80% signal coverage; 25–35 clusters | 1 day (discovery session) | None |
| C2 | `M2_B4_PATTERN_EXPANSION` | Expand patterns 22 → 70+ across dasha epochs | 3 days (discovery sessions) | None |
| C3 | `M2_B5_RES_CON_EXPANSION` | Expand resonances 12 → 24+; contradictions 8 → 20+ | 2 days (discovery sessions) | None |

### Stream D (Synthesis / orchestration)

| # | Brief | Scope summary | Effort | Predecessor |
|---|---|---|---|---|
| D1 | `M2_D1_COMPOSITION_RULES` | Add remedialRule + domainReportRule + timelineRule to composition_rules.ts | 1 day | B5 |
| D2 | `M2_D7_PER_TOOL_PLANNER` | New plan_per_tool pipeline stage; Haiku-driven per-tool query planning | 3 days | A2 + A3 + B3 + A5 |

### Stream E (Observability + schema)

| # | Brief | Scope summary | Effort | Predecessor |
|---|---|---|---|---|
| E1 | `M2_D56_OBSERVABILITY` | Consolidated: audit_events + query_plans tables (migrations 026 + 027); writer wiring; backfill + verification | 1 day | None |

### Stream F (Integrity + eval + close)

| # | Brief | Scope summary | Effort | Predecessor |
|---|---|---|---|---|
| F1 | `M2_E1_PROVENANCE_AUDIT` | 3 audits: MSR→FORENSIC (≥95%), UCN→MSR (≥90%), CGM SUPPORTS→MSR (≥95%) | 1 day | A2 + A3 + A5 |
| F2 | `M2_E2_EVAL_HARNESS` | B.9 eval harness: golden 50-query set + golden_router_queries; Recall@K, Precision@K, MRR; A/B framework | 1 day | All A + B + D2 |
| F3 | `M2_E34_CLOSE` | Consolidated: B.10 red-team + thin UI + handoff + PROSPECTIVE_PREDICTION_LOG scaffold + M2_CLOSE_BASELINE artifact | 1 day | F1 + F2 |

**Total: 18 briefs across 6 streams. Estimated 25–28 working sessions of compute. With 4–6 parallel streams and discovery sessions running concurrently, calendar time is ~12–18 days.**

## §3 — Autonomous brief contract

Every M2-execution brief MUST include the following sections to qualify for autonomous long-running execution:

### §3.1 — Pre-flight self-diagnostics (mandatory)

Before any code change or DB write, the brief verifies:

1. **Branch state.** `git branch --show-current` returns `redesign/r0-foundation`. If not, halt with clear error.
2. **Working tree state.** `git status` shows expected baseline (only files this brief is allowed to touch are modified). If unexpected modifications, halt.
3. **DB connectivity.** Auth Proxy reachable on `127.0.0.1:5433`. If not, the brief starts the proxy via `bash platform/scripts/start_db_proxy.sh &` and waits up to 30s.
4. **Predecessor state.** If this brief depends on a prior brief, verify that prior brief's deliverable is in place. Examples:
   - "Predecessor M2_A1 must be COMPLETE: verify by `SELECT signal_type FROM msr_signals LIMIT 1` returns non-NULL."
   - "Predecessor A1 audits must exist: verify by `test -f 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md`."
5. **Test runner state.** `npm test --silent --reporter=summary 2>&1 | tail -5` shows pre-existing baseline (e.g., 9 known failures). If higher, halt — something has regressed since last brief.
6. **Schema baseline.** Query the relevant tables: confirm row counts match expected pre-state from the parent's closing summary.

If ANY pre-flight check fails, the brief halts immediately with: a 5-line halt summary naming the failed check + suggested remediation. No "best-effort" continuation.

### §3.2 — Implementation (the actual work)

This is the brief-specific work. Must be:
- Atomic where possible (one schema change + one writer change + one re-ingest)
- Test-protected (tests written or updated alongside code; tests run before deploy)
- Idempotent where possible (re-running shouldn't damage state)

### §3.3 — Embedded verification (mandatory)

Each AC has explicit, machine-checkable verification:

- DB row counts via SQL probe.
- File existence via `test -f`.
- Test pass via `npm test` exit code + count comparison vs baseline.
- Deploy verification via `gcloud run revisions list` + a smoke query against the live URL.

If any AC verification fails, the brief either:
- Self-rolls-back (revert via git, re-deploy prior revision, restore DB from staging if a swap_to_live failed), OR
- Halts with a CLEAR_FAIL summary (suggested when rollback is risky)

### §3.4 — Closing summary (mandatory)

Standardized format every brief emits:

```
SESSION CLOSE — <brief_id> — <ISO timestamp>

ACs result:
  AC.1: <PASS|FAIL> — <one-line evidence>
  AC.2: ...

Files modified:
  <path>: <one-line change>

DB changes:
  <table>: <row count before> → <row count after>

Cloud Run revisions:
  <service>: <prior revision> → <new revision>

Tests:
  Before: <X passed / Y failed>
  After: <X' passed / Y' failed>
  Delta: <new failures count>

Halt-and-report cases (if any):
  <none | 1-2 paragraph description>

Brief status: <COMPLETE | HALTED_AT_AC.N | ROLLED_BACK>
Next brief in stream: <brief_id> (or "stream complete")
```

### §3.5 — Halt conditions (mandatory)

Each brief must explicitly enumerate halt conditions. The native is interrupted ONLY for these:

- Pre-flight check failures (§3.1)
- Schema corruption risk
- DB swap_to_live safety gate trip
- Test count regression > 5 new failures
- Cloud Build failure (after one auto-retry)
- Cloud Run deploy failure
- A required external service unavailable (Vertex AI, sidecar, Auth Proxy)

Anything else — including ambiguity in code — the brief makes its best-justified call within scope, documents it in closing summary, and continues. The native's review of the closing summary catches it post-hoc rather than mid-session.

## §4 — Cross-stream synchronization points

Five sync points across all 18 briefs. These are the only moments when streams must coordinate.

### Sync 1 — Post-A1 (Phase α completion)

**When:** After A1 closes.
**Why:** A1's `M1_M2_ACTIVATION_MATRIX.md` and the four audit results are inputs to A2, A3, A4. Until A1 lands, we don't know exactly what's in `chart_facts` or which msr_signals columns exist.
**What:** The native reads A1's closing summary and confirms (or amends) A2, A3, A4 scope based on findings. May add Phase α follow-ups (e.g., "the FORENSIC § coverage audit found §16 Aspects has zero rows in chart_facts — add an A3.5 brief").
**Native interaction:** ~10 minutes reading the A1 summary + a brief Cowork message confirming or amending downstream wave.

### Sync 2 — Post-A2 + A3 (ETL wave complete)

**When:** A2 + A3 both close.
**Why:** B3 (chart_facts_query) and F1 (provenance audit) depend on A2 + A3 being live in DB.
**What:** Native confirms ingest counts match expectations. If A2 produced unexpectedly few/many `signal_type` values, native calls it.
**Native interaction:** ~5 minutes.

### Sync 3 — Post-Wave-2 deploy convergence

**When:** Multiple Wave-2 briefs deploy in close succession.
**Why:** Cloud Run revisions stack; the last `cloud_build_submit.sh` is the live revision and carries cumulative changes. If two streams deploy within minutes of each other, the last one wins and CARRIES the prior one's changes (because both are on r0-foundation).
**What:** No coordination needed — Cloud Run handles atomically. But the native confirms that the final revision serves all the changes. A simple `gcloud run revisions list` + smoke query confirms.
**Native interaction:** ~5 minutes.

### Sync 4 — Pre-D2 (per-tool planner)

**When:** D2 (per-tool planner) is ready to launch.
**Why:** D2 depends on A2 + A3 + B3 + A5 all being live (the planner needs rich data + tools to plan against). Launching D2 prematurely would plan against thin data and produce skewed eval baselines.
**What:** Native confirms all four predecessors are COMPLETE before kicking D2.
**Native interaction:** ~5 minutes.

### Sync 5 — Pre-F3 (M2 close)

**When:** F1 (integrity audit) and F2 (eval harness) both close.
**Why:** F3 is the M2 close gate. Native must confirm all 10 quality bar criteria from the master plan §1 pass before F3 seals M2.
**What:** Native reviews F1 + F2 outputs against the §1 quality bar. If any criterion fails, F3 halts and the native decides: fix-in-scope (small) or formal-defer-to-M3 (with sign-off documented).
**Native interaction:** ~30 minutes — the most substantive sync.

## §5 — Conflict resolution policy

When two streams' work would touch the same file, the rule:

1. **Disjoint paths by design.** The streams are scoped to enforce no overlap. If a brief proposes to touch a path another stream owns, the brief author halts and the native arbitrates (very rare).
2. **Migration numbering.** Stream A uses 022–025; Stream E uses 026–027. If a stream needs more numbers, it claims the next available range and updates this document.
3. **CAPABILITY_MANIFEST.json updates.** Multiple streams may add entries (Stream A adds chart_facts category enum extensions, Stream B adds new tool entries). The convention: each brief that adds entries does so via append-only edits to the manifest, sorted alphabetically by canonical_id. The mirror-enforcer governance check catches collisions.
4. **Test-failure baseline.** Each brief inherits the baseline from the prior brief in its stream. If a brief raises the failure count above baseline, that's a regression; brief halts.
5. **Concurrent deploys.** Cloud Run handles atomically; last-deployed wins. Both streams' code is on r0-foundation, so any deploy carries everything committed. No coordination needed.

## §6 — Wave dispatch

Five waves. Each wave is a set of briefs that can launch simultaneously. The native kicks off each brief in its wave, then waits for the wave to complete before kicking off the next wave. (Within a wave, briefs run truly parallel; sessions are independent.)

### Wave 1 — Foundation + independents (Day 1)

**4 briefs in parallel:**

- **A1** — `M2_PHASE_ALPHA` — the four audits (1 session)
- **B1** — `M2_C6_VECTOR_SEARCH_FILTER` — F2.2, no DB dependency (½ day)
- **E1** — `M2_D56_OBSERVABILITY` — audit_events + query_plans tables (1 day)
- **C1** — `M2_B3_CLUSTER_RECLUSTER` — discovery session (1 day)

These four have no inter-dependencies. They land in 1 day max.

After Wave 1: Sync 1 (native confirms A1 findings).

### Wave 2 — ETL + corpus + small tools (Days 2–4)

**6 briefs in parallel:**

- **A2** — `M2_A1_MSR_ETL` — depends on A1 ✓
- **A3** — `M2_A2_CHART_FACTS_ETL` — depends on A1 ✓
- **A5** — `M2_B1_CGM_FULL_EDGES` — independent
- **A6** — `M2_B2_CHUNKER_COMPLETION` — independent
- **C2** — `M2_B4_PATTERN_EXPANSION` — independent (discovery)
- **C3** — `M2_B5_RES_CON_EXPANSION` — independent (discovery)

After Wave 2: Sync 2 (native confirms A2 + A3 ingest counts).

### Wave 3 — Tool surface + composition (Days 5–8)

**5 briefs in parallel:**

- **A4** — `M2_A_MINOR` — Vimshottari + pada + chalit
- **B2** — `M2_C234_BUNDLE` — kp_query + saham_query + divisional_query (depends on A3 ✓)
- **B3** — `M2_C1_CHART_FACTS_QUERY` — depends on A3 ✓
- **B4** — `M2_C5_TEMPORAL_EXTENSION` — depends on A4 (need it to land first) — **OR** start after A4 closes
- **B5** — `M2_D234_BUNDLE` — L3/L4/L5 tools, independent

After Wave 3: Sync 3 (native confirms deploy convergence).

### Wave 4 — Orchestration + integrity (Days 9–11)

**3 briefs in parallel:**

- **D1** — `M2_D1_COMPOSITION_RULES` — depends on B5 ✓
- **D2** — `M2_D7_PER_TOOL_PLANNER` — depends on A2 + A3 + B3 + A5 ✓ (Sync 4)
- **F1** — `M2_E1_PROVENANCE_AUDIT` — depends on A2 + A3 + A5 ✓

After Wave 4: Sync 4 already happened pre-D2; no extra sync.

### Wave 5 — Eval + close (Days 12–13)

**2 briefs sequential:**

- **F2** — `M2_E2_EVAL_HARNESS` — depends on all A + B + D2 ✓
- **F3** — `M2_E34_CLOSE` — depends on F1 + F2 ✓ (Sync 5)

After Wave 5: M2 closed. Native opens M3.

## §7 — Per-stream brief detail (catalog)

This section lists each brief's scope-summary, key ACs, predecessor, may_touch, must_not_touch, halt conditions. Used as the reference when expanding a brief into its full CLAUDECODE_BRIEF artifact at kickoff time.

### A1 — `M2_PHASE_ALPHA`

**Scope.** Four audits run in one session. Outputs: `M1_M2_ACTIVATION_MATRIX.md` + a probe-results file.

Audits:
1. `chart_facts` schema introspection (`\d chart_facts` + category breakdown + 5 sample rows).
2. `msr_signals` column inventory (`\d msr_signals` + which source MSR fields exist).
3. Classifier output audit on factual queries (sample 10 recent `query_class='factual'` traces from `query_trace_steps`; check if `planets[]` is populated, `tools_authorized` includes msr_sql).
4. FORENSIC §1–§27 vs database round-trip — for each section, confirm structured table representation + rag_chunks representation + retrieval tool + coverage %.

**Key ACs.** All four audits documented. Activation matrix written. No source code modified.

**may_touch.** `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md` (CREATE), `00_ARCHITECTURE/BRIEFS/M2_PHASE_ALPHA_RESULTS_<date>.txt` (CREATE), `platform/scripts/retrieval_diagnostic_probes.sql` (extend with chart_facts intro + classifier audit probes).

**must_not_touch.** All source code. All migrations. All other briefs. UI/UX scope.

**Halt conditions.** Auth Proxy unreachable; DB authentication failure.

**Effort.** 1 session.

---

### A2 — `M2_A1_MSR_ETL`

**Scope.** Add columns to `msr_signals` that source has but ETL drops. Re-run MSR ingest with full preservation.

Columns to add (verified by A1 inventory): likely `signal_type`, `temporal_activation`, `valence`, `classical_source`, `falsifier`, `supporting_rules`, `rpt_deep_dive`, `entities_involved`, `v6_ids_consumed`, `prior_id`. Final list adapts to A1 findings.

**Key ACs.**
- Migration 022 adds the columns.
- Re-ingest preserves source values.
- PROBE 2 (signal_type × temporal_activation) returns populated breakdown.
- ≥90% of signals have non-NULL classical_source.
- ≥80% of signals have non-NULL falsifier.
- Tests pass at baseline.
- No new failures.

**may_touch.** `platform/migrations/022_msr_signals_full_columns.sql` (CREATE), `platform/python-sidecar/pipeline/extractors/msr_extractor.py` (extend), `platform/python-sidecar/pipeline/writers/msr_signals_writer.py` (extend INSERT to cover new columns), `platform/python-sidecar/tests/extractors/test_msr_extractor.py` (extend).

**must_not_touch.** Other extractors. TypeScript tools. UI/UX. Other migrations.

**Halt conditions.** Source MSR file missing fields the brief expects. Migration apply failure. swap_to_live safety gate trips.

**Effort.** 1 day.

**Predecessor.** A1 COMPLETE.

---

### A3 — `M2_A2_CHART_FACTS_ETL`

**Scope.** Extend `chart_facts` ETL to cover all FORENSIC sections per A1's coverage matrix. Likely additions: §6 Shadbala (6-component table + JH ranking), §7 BAV (84 cells) + SAV (12 cells), §4 KP cusps (36 entries), §12.2 36 Sahams, §3 D2–D60 placements, §11.3 Yogi/Avayogi, §13 Arudhas, §14 Navatara, §15 Panchang, §16 Aspects matrix, §22 Varshphal, §24 Longevity, §26 Yogas register.

**Key ACs.**
- Migration 023 if column additions needed (e.g., adding `bindu` column for ashtakavarga rows).
- chart_facts row count rises from 589 to ≥1,800.
- Every numbered FORENSIC § that contains FACT-class data has corresponding rows.
- PROBE 9 returns clean category breakdown spanning ≥15 distinct categories.
- Tests pass at baseline.

**may_touch.** `platform/migrations/023_chart_facts_extension.sql` (CREATE if needed), `platform/python-sidecar/pipeline/extractors/forensic_extractor.py` (extend), `platform/python-sidecar/pipeline/writers/chart_facts_writer.py` (extend), tests.

**must_not_touch.** msr_signals work. Other migrations. TypeScript.

**Halt conditions.** Source FORENSIC structure differs from A1 audit's matrix. Migration failure. swap safety gate.

**Effort.** 2 days.

**Predecessor.** A1 COMPLETE.

---

### A4 — `M2_A_MINOR`

**Scope.** Three small extensions consolidated.

- **M2-A.3 Vimshottari sub-period.** Sidecar `/dasha_chain(date)` returning all 5 levels (MD/AD/PD/SD/PD2).
- **M2-A.4 Pada column.** Ensure `nakshatra_pada` is a column on chart_facts placement rows.
- **M2-A.5 Bhava chalit dual-house.** Ensure both `rashi_house` and `chalit_house` are exposed per planet.

**Key ACs.**
- `/dasha_chain` endpoint returns 5 levels for any date 1900–2100.
- chart_facts placement rows have non-NULL nakshatra_pada (1–4) for all 9 planets + Lagna.
- chart_facts placement rows have both rashi_house and chalit_house non-NULL.

**may_touch.** Sidecar dasha module, forensic_extractor.py, chart_facts_writer.py if column additions needed, tests.

**must_not_touch.** Other Stream A briefs' files (no overlap).

**Halt conditions.** Sidecar Vimshottari computation returns wrong values for known test date.

**Effort.** 1 day.

**Predecessor.** A1.

---

### A5 — `M2_B1_CGM_FULL_EDGES`

**Scope.** Expand `l25_cgm_edges` from 126 to ~339 by computing/ingesting all 15 source edge types.

Edge types to add (per CGM v9.0 source declaration): GRAHA_ASPECT, BHAV_ASPECT, JAIMINI_ASPECT, OWNERSHIP, TENANCY, EXALT_DEBIL_AFFINITY, KARAKA_ROLE, **YOGA_MEMBERSHIP** (highest priority), DASHA_ACTIVATION, DIVISIONAL_CONFIRMATION, COMBUST_WAR, KAKSHYA_ZONE, SAHAM_COMPOSITION.

Each edge type's spec is in CGM v9.0 source. The `cgm_extractor.py` needs to compute these from existing node properties (not re-author from scratch).

**Key ACs.**
- `SELECT edge_type, COUNT(*) FROM l25_cgm_edges WHERE status='valid' GROUP BY edge_type` returns ≥10 edge types each non-zero.
- Total valid edges ≥ 320.
- YOGA_MEMBERSHIP edges ≥ 60.
- No edge has source_node_id or target_node_id missing from l25_cgm_nodes.
- Pipeline tests pass.

**may_touch.** `cgm_extractor.py` (significant extension), tests.

**must_not_touch.** Other extractors. Migrations. TypeScript.

**Halt conditions.** Edge computation requires data not in l25_cgm_nodes (e.g., needs aspect angles that aren't in node properties). In that case, halt and report the gap — extend l25_cgm_nodes properties separately as a follow-up brief.

**Effort.** 2 days.

**Predecessor.** None.

---

### A6 — `M2_B2_CHUNKER_COMPLETION`

**Scope.** Three chunker improvements.
- `ucn_section.py` extended to emit H3 sub-section chunks (target: 25 → ~134 ucn_section chunks).
- `cgm_node.py` extended to ALSO chunk UCN section nodes from l25_cgm_nodes (target: 234 → ~369 cgm_node chunks).
- New `lel_chunker.py` for LEL period summaries (5) and chronic patterns (6).

**Key ACs.**
- rag_chunks count rises from 1,005 to ≥1,250.
- ucn_section count ≥ 100.
- cgm_node count ≥ 350.
- lel_period + lel_chronic doc_types appear with counts ≥5 and ≥6 respectively.
- Embeddings 1:1 with chunks.

**may_touch.** `ucn_section.py`, `cgm_node.py`, new `lel_chunker.py`, `chunkers/__init__.py`, pipeline/main.py wiring, tests.

**must_not_touch.** Other chunkers. Migrations. TypeScript.

**Halt conditions.** UCN H3 parser produces wrong section IDs.

**Effort.** 1.5 days.

**Predecessor.** None.

---

### B1 — `M2_C6_VECTOR_SEARCH_FILTER`

**Scope.** F2.2 from the productivity plan.
- Add `doc_type[]` and `layer` filter parameters to `vector_search.ts`.
- Update router prompt so classifier emits doc_type filter per query class.
- Tests for filter behavior.

**Key ACs.**
- factual query → vector_search returns layer=L1 only.
- interpretive query → returns mixed L1+L2.5.
- discovery query → includes domain_report.
- Tests pass.

**may_touch.** `platform/src/lib/retrieve/vector_search.ts`, `vector_search` types, `platform/src/lib/router/prompt.ts` (filter guidance addition only), tests.

**must_not_touch.** Other retrieve tools. Other router files. Backend.

**Halt conditions.** None.

**Effort.** ½ day.

**Predecessor.** None.

---

### B2 — `M2_C234_BUNDLE`

**Scope.** Three small TypeScript tools, consolidated for atomicity.
- `kp_query` — queries chart_facts where category='kp_cusp'; returns Star Lord / Sub Lord / Sub-Sub Lord per cusp.
- `saham_query` — queries chart_facts where category='saham'; returns 36 sahams with longitude/nakshatra/sign/house/meaning.
- `divisional_query` — queries chart_facts where category='divisional'; returns per-varga per-planet placements.

All three depend on chart_facts having the right categories (post-A3).

**Key ACs.**
- Each tool fires correctly with expected return shape.
- Each tool is registered in CAPABILITY_MANIFEST.
- Classifier prompt knows when to authorize each.
- Tests for all three.

**may_touch.** `platform/src/lib/retrieve/kp_query.ts` (CREATE), `saham_query.ts` (CREATE), `divisional_query.ts` (CREATE), `index.ts` (export), classifier prompt + tests.

**must_not_touch.** Other tools. Backend. UI.

**Halt conditions.** chart_facts doesn't have the expected categories per A3 closing summary.

**Effort.** 1.5 days.

**Predecessor.** A3 COMPLETE.

---

### B3 — `M2_C1_CHART_FACTS_QUERY`

**Scope.** The big new tool. Parameterized over chart_facts.

Parameters:
- `category` (enum: placement, shadbala, ashtakavarga_bav, ashtakavarga_sav, kp_cusp, saham, divisional, aspect, longevity, yoga, ...).
- `planet?`, `house?`, `sign?`, `nakshatra?`, `pada?`.
- `rank_by?` (e.g., 'shadbala_total', 'bindu', 'strength').
- `limit?`.

Returns structured rows. The classifier learns to use this tool for any quantitative chart query.

**Key ACs.**
- "Rank my planets by Shadbala" → returns 7-planet ranking from JH-authoritative.
- "What is the BAV of my Mars in Capricorn?" → returns specific bindu count.
- "What is my Saham Vivaha?" → returns the row.
- Tests cover at least 10 query patterns.

**may_touch.** `platform/src/lib/retrieve/chart_facts_query.ts` (CREATE), `index.ts`, classifier prompt + tests.

**must_not_touch.** Other tools. Backend.

**Halt conditions.** chart_facts categories don't match expected schema.

**Effort.** 1.5 days.

**Predecessor.** A3 COMPLETE.

---

### B4 — `M2_C5_TEMPORAL_EXTENSION`

**Scope.** Five new endpoints on the temporal tool / sidecar.

- `dasha_chain(date)` — full 5-level Vimshottari (depends on A4).
- `sade_sati_status(date)` — current phase from sade_sati_phases.
- `ephemeris_range(start, end, planets[])` — date-window queries.
- `eclipses_in(start, end)` — from eclipses table.
- `retrograde_stations_in(start, end, planet?)` — from retrogrades table.

Plus: investigate the 300s timeout signature noted in PROBE 8. Q7 verification showed temporal at 10ms — confirm that's the steady state.

**Key ACs.**
- All 5 endpoints respond within 2s.
- temporal latency p95 over a sample of 10 queries ≤ 5s.
- Tests for each endpoint.

**may_touch.** Sidecar Python code (extend dasha module, add endpoints), `temporal.ts` (call new endpoints), tests.

**must_not_touch.** Other tools.

**Halt conditions.** Sidecar hits genuine timeout > 30s on any new endpoint.

**Effort.** 1 day.

**Predecessor.** A4.

---

### B5 — `M2_D234_BUNDLE`

**Scope.** Three new L3/L4/L5 tools.

- `domain_report_query` — queries rag_chunks with `doc_type='domain_report'`, filters by `plan.domains`.
- `remedial_codex_query` — queries rag_chunks with `doc_type='l4_remedial'` (need to add doc_type via chunker).
- `timeline_query` — queries rag_chunks with `doc_type='l5_timeline'`.

For L4 and L5, the chunkers need to first ingest those files into rag_chunks. May require an A6+ follow-on or just inline chunker addition in this brief.

**Key ACs.**
- domain_report_query returns L3 content for domain queries.
- remedial_codex_query returns L4 content for remedial queries.
- timeline_query returns L5 content for time-windowed queries.
- Each tool registered in CAPABILITY_MANIFEST.
- Tests.

**may_touch.** 3 new TypeScript tool files, classifier prompt (add tool guidance), if needed: 2 new chunkers (`l4_remedial.py`, `l5_timeline.py`) + pipeline/main.py wiring + tests.

**must_not_touch.** Other tools. Other extractors.

**Halt conditions.** L4/L5 source files have unexpected structure (e.g., not chunkable cleanly at H2/H3).

**Effort.** 1.5 days.

**Predecessor.** None.

---

### C1 — `M2_B3_CLUSTER_RECLUSTER`

**Scope.** Discovery session (Gemini-led). Re-cluster MSR signals targeting ≥80% coverage. Generate 25–35 new clusters.

**Key ACs.**
- Σ cluster_size_n ≥ 400.
- Every domain has ≥ 2 clusters.
- Every planet has ≥ 1 cluster.
- New CLUSTER_ATLAS_v1_1.json committed.
- Two-pass protocol followed (Gemini propose → Claude review → reconciliation).

**may_touch.** `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json` (CREATE; supersedes v1_0), corresponding .md, register manifest update.

**must_not_touch.** Other registers. Code.

**Halt conditions.** Two-pass disagreement unresolved.

**Effort.** 1 day.

**Predecessor.** None.

---

### C2 — `M2_B4_PATTERN_EXPANSION`

**Scope.** Multiple discovery sessions. Expand patterns 22 → 70+. Cover Mercury MD remainder, Saturn MD, Ketu MD, cross-dasha, chronic-pattern.

**Key ACs.**
- ≥70 patterns total in PATTERN_REGISTER_v1_1.json.
- Every domain has ≥5 patterns.
- ≥50% are forward_looking with verification windows.
- Each pattern declares AK/AmK function.
- Two-pass protocol followed for each.

**may_touch.** `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_1.json` (CREATE), corresponding .md.

**must_not_touch.** Other registers. Code.

**Halt conditions.** Source ground-truth conflicts.

**Effort.** 3 days (multiple discovery sessions).

**Predecessor.** None.

---

### C3 — `M2_B5_RES_CON_EXPANSION`

**Scope.** Discovery sessions. Resonances 12 → 24+; contradictions 8 → 20+.

**Key ACs.**
- Resonances ≥ 24/36 domain-pair coverage.
- Contradictions ≥ 20.
- All 4 contradiction_class values have ≥ 5 each.
- Two-pass protocol.

**may_touch.** `RESONANCE_REGISTER_v1_1.json`, `CONTRADICTION_REGISTER_v1_1.json` (CREATE), .md.

**must_not_touch.** Other registers. Code.

**Halt conditions.** Two-pass unresolved.

**Effort.** 2 days.

**Predecessor.** None.

---

### D1 — `M2_D1_COMPOSITION_RULES`

**Scope.** Add three composition rules to `composition_rules.ts`.

- `remedialRule` — fires for `query_class='remedial'`, adds REMEDIAL_CODEX entries.
- `domainReportRule` — fires when `plan.domains.length > 0`, adds matching REPORT_* canonical_ids.
- `timelineRule` — fires when `forward_looking=true` and `time_window` is set, adds 05_TEMPORAL_ENGINES entries.

**Key ACs.**
- Three rules added in order in COMPOSITION_RULES.
- Each rule has its own test in __tests__/composition_rules.test.ts.
- Existing rules unchanged.
- npm test passes baseline.

**may_touch.** `composition_rules.ts`, tests.

**must_not_touch.** rule_composer.ts. Other bundle files.

**Halt conditions.** Test failures unrelated to additions.

**Effort.** 1 day.

**Predecessor.** B5 (the L3/L4/L5 tools must exist for the rules to be useful).

---

### D2 — `M2_D7_PER_TOOL_PLANNER`

**Scope.** New pipeline stage `plan_per_tool` between `compose_bundle` and `retrieve(parallel)`.

- New file `platform/src/lib/router/per_tool_planner.ts`.
- For each authorized tool, calls Haiku in parallel with a tool-specific prompt template.
- Output: `{ tool_name → toolSpecificParams }` overriding plan defaults.
- Includes prompt templates for each of 17 tools (10 existing + 7 new).
- Trace step `plan_per_tool` written.

**Key ACs.**
- Pipeline stage runs in production.
- Per-tool parameter overrides land in trace.
- A/B test ready (compare classifier-only vs per-tool planner via eval harness in F2).

**may_touch.** `platform/src/lib/router/per_tool_planner.ts` (CREATE), `consume/route.ts` (wire stage), schemas, tests, classifier types.

**must_not_touch.** Existing classifier code. Retrieve tools.

**Halt conditions.** Haiku call latency > 1s; cost spike > $0.05/query.

**Effort.** 3 days.

**Predecessor.** A2 + A3 + B3 + A5 ALL COMPLETE (Sync 4 gate).

---

### E1 — `M2_D56_OBSERVABILITY`

**Scope.** Two missing tables.

- Migration 026: `audit_events` table per the audit-writer's design (find by grep — the writer code exists; the table may have been intended via a migration that was never applied).
- Migration 027: `query_plans` table flat-mirroring QueryPlan schema.
- Wire writers if needed (likely the writers exist; we just need the tables and to confirm wiring fires).
- Backfill from query_trace_steps.payload where possible.

**Key ACs.**
- `audit_events` and `query_plans` both exist in DB.
- After 5 fresh queries, both tables have 5 rows.
- PROBE 6 + PROBE 7 return clean breakdowns.

**may_touch.** Migrations 026 + 027, audit_writer.ts/audit_writer.py if wiring is broken, tests.

**must_not_touch.** Existing queries, existing tools.

**Halt conditions.** Migration apply failure. Existing rows in some other table conflict.

**Effort.** 1 day.

**Predecessor.** None.

---

### F1 — `M2_E1_PROVENANCE_AUDIT`

**Scope.** Three audits.

1. MSR → FORENSIC traceability: of 499 MSR signals, % with valid v6_ids_consumed → FORENSIC fact. Target ≥95%.
2. UCN → MSR traceability: % UCN paragraphs citing specific MSR signal IDs. Target ≥90%.
3. CGM SUPPORTS → MSR: % SUPPORTS edges deriving from named MSR signal. Target ≥95%.

Output: `M2_PROVENANCE_AUDIT_RESULTS.md`.

**Key ACs.**
- Three audits run.
- Results documented with sub-target rows listed.
- If any below target: FAIL flagged but doesn't halt close.

**may_touch.** New audit script files, output md.

**must_not_touch.** Source data.

**Effort.** 1 day.

**Predecessor.** A2 + A3 + A5 COMPLETE.

---

### F2 — `M2_E2_EVAL_HARNESS`

**Scope.** B.9 per PHASE_B_PLAN.

- Eval harness consumes `golden.jsonl` (50 queries) + `golden_router_queries.json` (20).
- Computes Recall@K, Precision@K, MRR per query.
- Per-tool zero_result_rate, per-doc_type retrieval coverage.
- A/B framework: classifier-only vs classifier+per-tool-planner.

**Key ACs.**
- Harness runs end-to-end against the 50-query set.
- Per-query metrics output.
- Aggregate metrics: Recall@5 ≥ 0.70, Precision@5 ≥ 0.60, MRR ≥ 0.55.

**may_touch.** `platform/python-sidecar/rag/eval/run_eval.py` (extend), output reports.

**must_not_touch.** Tools. Classifier.

**Halt conditions.** Aggregate metrics below target — FAIL flagged but doesn't halt close.

**Effort.** 1 day.

**Predecessor.** All A + B + D2 COMPLETE.

---

### F3 — `M2_E34_CLOSE`

**Scope.** B.10 + the M2-close obligations.

- Final red-team probes (cadence-fired per ONGOING_HYGIENE_POLICIES §H).
- Thin validation UI (per PHASE_B_PLAN §G B.10).
- `07_PROSPECTIVE_TESTING/PROSPECTIVE_PREDICTION_LOG_v1_0.md` scaffolded (per MACRO_PLAN §3.9 line 511).
- `M2_CLOSE_BASELINE_v1_0.md` artifact created.
- CURRENT_STATE updated with `active_macro_phase: M3`.
- Re-verify all 10 quality bar criteria from master plan §1.

**Key ACs.**
- Red-team passes.
- Thin UI deployed.
- PROSPECTIVE_PREDICTION_LOG scaffold exists.
- Close baseline artifact exists with all 10 quality bar checks PASS or formally documented exception.
- CURRENT_STATE updated.

**may_touch.** New artifacts, CURRENT_STATE, possibly thin UI new files (if not in scope of the UI/UX stream).

**must_not_touch.** UI/UX scope (if R-redesign owns the validation UI surface).

**Halt conditions.** Quality bar criterion fails without exception path.

**Effort.** 1 day.

**Predecessor.** F1 + F2 COMPLETE (Sync 5 gate).

## §8 — Native interaction protocol (the "minimal interference" contract)

The native's role across the 18 briefs:

### Per-brief actions (~3–5 min per brief)

1. **Kickoff.** Open a terminal tab, navigate to the working directory, paste the prepared kickoff prompt for the brief. The kickoff prompt is a 4–5 line block this document provides per brief.
2. **Closing summary.** When the brief reports COMPLETE in the terminal, the native scans the standardized closing summary (§3.4) for ~30 seconds. If everything looks normal: move on. If a halt-and-report flag fires: address.

### Per-wave actions (~10–30 min per wave)

1. **Wave dispatch.** When prior wave's all briefs report COMPLETE, the native kicks off the next wave. Briefs in a wave launch as fast as the native can paste — no gating between them.
2. **Sync 1 (post-A1).** ~10 min reading the activation matrix.
3. **Sync 2 (post-A2 + A3).** ~5 min confirming ingest counts.
4. **Sync 4 (pre-D2).** ~5 min confirming all four predecessors COMPLETE.
5. **Sync 5 (pre-F3).** ~30 min reviewing F1 + F2 outputs against the §1 quality bar.

### Total native time across all 18 briefs: ~3 hours over 12–18 calendar days.

Compare to single-stream sequential: ~5–6 weeks.

## §9 — Quality bar at M2 close (mirrors master plan §1)

When M2 closes, all 10 hold simultaneously:

1. Source-to-tool coverage = 100%
2. ETL preserves every source field
3. Quantitative substrate is structured
4. L2.5 graph is complete (≥320 valid edges, ≥10 edge types)
5. Classifier is L1-aware (per-tool planner active)
6. Synthesis cites authentically (classical_source from MSR)
7. Provenance audit passes (≥95% / ≥90% / ≥95%)
8. Eval harness exists and runs (Recall@5 ≥ 0.70)
9. Observability is live (audit_events + query_plans tables populated)
10. Red-team passes M2 final

Each criterion has a specific brief that delivers it. F3 verifies all 10.

## §10 — Risk register

| Risk | Mitigation |
|---|---|
| A brief discovers an unexpected gap that grows scope mid-session | Halt-and-report; native triages; possibly spawn follow-up brief in same wave |
| Two streams' deploys race | Last-deploy wins; both sets of changes carried; no real risk because both run on r0-foundation |
| Discovery session two-pass disagreement | Brief halts with disagreement summary; native arbitrates |
| Per-tool planner cost spike | Cap Haiku token budget per call; fall back to classifier-only if cost > $0.05/query |
| Eval metrics below target | F2 flags FAIL but doesn't halt close; native decides defer-to-M3 or fix-in-scope |
| UI/UX stream collides on a file | Add the file to UI/UX stream's must_not_touch; very rare given scope hygiene |
| Auth Proxy unavailable mid-session | Brief halts at pre-flight §3.1.3; native restarts proxy |

## §11 — Open decisions for native review

Same as master plan §13, plus:

- **D8.** Stream parallelism — confirm 4–6 concurrent streams. If less (e.g., 2 max), waves serialize and timeline doubles.
- **D9.** Discovery session bandwidth — Stream C requires ~3 days of discovery sessions. Native time investment per session is real (Gemini proposes, Claude reviews, native sometimes arbitrates). Confirm appetite.
- **D10.** Promotion path — does this execution plan promote to CURRENT after native review, supplanting the master plan? Or both stay (master = strategic, execution = tactical)?

---

*End of M1_M2_EXECUTION_PLAN_v1_0_DRAFT. Wave 1 briefs follow as separate artifacts in `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_*`.*
