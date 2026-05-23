---
artifact: MCPT_V32_OPTIMIZATION_PLAN_v3.md
version: 3.0
status: PROPOSED
project: MCP Transformation
phase: v3.2 — Quality Tightening (post-MCPT v3.1 + v3.3 close)
supersedes: outputs/mcp_optimization_plan.md (v1), outputs/mcp_optimization_plan_v2.md (v2)
author: Claude Opus 4.7 (Cowork planning session)
ground_truth_basis: filesystem audit 2026-05-23 of feature/main HEAD
---

# MCPT v3.2 — Quality Tightening (Implementation-Grade Plan, grounded in the real repo)

## Why this is v3, not a refinement of v2

v1 and v2 were written before the Cowork session had access to the actual repo. With access, every load-bearing assumption in those plans was either wrong or already done. v3 starts from filesystem ground truth.

### What's already done (was in v2 — delete from scope)

| v2 task | Actual state |
|---|---|
| Apply migrations 073-076 | **APPLIED** 2026-05-22 17:06 UTC. See `00_ARCHITECTURE/MCPT_POST_DEPLOY_MIGRATIONS_20260522T170527Z.log` |
| v3.3 backfills (KP, Tajaka, Shadbala, Ashtakavarga) | **CLOSED** per `00_ARCHITECTURE/MCPT_V33_CLOSE.md`. 2,717 rows across 27 chart_facts categories, 9/9 v3.3 scope passed |
| `chart_facts.divisional_chart` column + index | **EXISTS** in `platform/migrations/014_chart_facts.sql` and `029_chart_facts_indexes.sql` |
| `audience_tier` mechanism | **EXISTS** — `mcp_api_keys` table per-key tier; propagated via `X-MCP-Audience-Tier` header |
| Tool-name aliasing infrastructure | **EXISTS** — `MCP_TO_RETRIEVAL_TOOL` in `platform/src/lib/mcp/primitives_registry.ts:47-59` (5 renames) |
| Deprecating synthesis tools | **CORRECTLY REJECTED** in v2. `holistic_bundle` + `multi_school_bundle` are MCPT v3.1 first-class tools used by external Claude clients. Web `/consume` uses its own in-process path, not MCP HTTP |

### What's actually broken or missing (the real v3 scope)

1. **Stale lies in tool descriptions.** `data_coverage.ts:35-36` says "KP, Tajaka, Shadbala, Ashtakavarga categories are pending v3.3 backfill" — false. The `data_note: "Apply migrations 073-076 and run nightly audit"` returned by `tool_health` is also false.
2. **`data_source_expected` table exists but is empty.** Seed at `00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql` was never loaded. `data_coverage` returns nothing useful.
3. **No nightly audit job exists.** No Cloud Scheduler entry, no Cloud Run job, no refresher for `data_source_expected.actual_rows`.
4. **Description builder used by only 1 of 21 tools.** `description_builder.ts` is used by `query_chart_facts`. The other 20 have inline hand-rolled descriptions that diverge in style, coverage-hint discipline, and enum-source discipline.
5. **Double-encoding is real.** Every tool independently does `JSON.stringify(envelope, null, 2)` and returns it in a single `text` field. 21 call sites, no shared helper.
6. **`query_chart_facts` doesn't expose `divisional_chart` filter.** The DB has the column + index; the tool schema doesn't expose it. So a D9-only query pulls all divisionals.
7. **No `categories: string[]` batching** on `query_chart_facts`. Pulling 5 categories = 5 round-trips.
8. **No `chart_summary` super-endpoint** for the "wide-by-default" pattern.
9. **Trace persists retrieval-side names, not MCP-facing names.** `query_trace_steps.step_name` stores `chart_facts_query` not `query_chart_facts`. `get_trace(trace_id_from_list_recent_queries)` works because the dispatcher also stores `mcp_tool` in `payload.items[0]`, but `query_summary` is just `"chart_facts_query call"` with no params.
10. **No bench harness.** `platform/tests/load/k6/` contains only `.gitkeep`. `tests/perf/` has 3 markdown reports (some explicitly say "sidecar wasn't running").
11. **No accuracy harness for synthesis output.** `platform/tests/synthesis/` has 11 structural tests but no golden output corpus. Latest `eval-results/answer_eval_*.json` (2026-05-11) shows **0/14 passing** on layer coverage, B11, citations — there's a real measurable failing baseline.
12. **No cross-scenario equivalence test.** The MCP/agentic path and the web `/consume` in-process path produce different orchestrations; nothing verifies they reach the same factual claims.
13. **No routing eval.** `planner_golden_set.json` exists for planner tool-recall but not for first-tool-choice on the MCP surface.
14. **`acharya` tier referenced in code/docs but DB enum has only `client` + `super_admin`.** `data_coverage.ts:56-69` gates on `'client' || 'public_redacted'` — undefined behavior if `'acharya'` is ever set.
15. **`suggested_followups` field exists on the envelope but is always empty.** No table, no algorithm, no inline implementation.
16. **kp_significator 7/9 residual.** Upstream FORENSIC §4.3 source gap; 5 houses absent. Documented in `MCPT_V33_CLOSE.md` as RESIDUAL not blocker.

---

## Part A — Architectural Constraints (from the real repo, not invented)

### A.1 Repo layout

- **Root**: `/Users/Dev/Vibe-Coding/Apps/Madhav/`
- **MCP server (TS, Express, Node 20)**: `platform-mcp/` → Cloud Run `amjis-mcp` (asia-south1)
- **Web portal (Next.js)**: `platform/src/`
- **Python sidecar (panchang/muhurat)**: `platform/python-sidecar/`
- **Migrations**: `platform/migrations/` (canonical, next ID 115) + `platform/supabase/migrations/` (frozen-but-active, next ID 083)
- **DB**: Postgres on Cloud SQL `amjis-postgres` (asia-south1), 109 prod tables as of 2026-05-22

### A.2 Consumer scenarios (corrected from v2)

The MCP server has fewer scenarios than v2 assumed because the web `/consume` chat **does not call MCP HTTP** — it calls retrieval primitives directly via `executeMCPTool` → `getTool()` in-process.

| Scenario | Real consumer | Synthesis tools | Fact tools |
|---|---|---|---|
| **MCP / agentic (external)** | Claude Code, Claude Desktop, Cowork — over HTTP to `amjis-mcp.run.app` | **available, primary for "interpret X"-style asks** | available |
| **Web `/consume`** | Browser → Next.js `api/chat/consume/route.ts` → in-process `executeMCPTool` | does NOT use MCP `holistic_bundle`; has its own server-side synthesis loop | uses `getTool()` registry |
| **MCP `/api/mcp/bundles/[name]` SSE** | External MCP clients reach this via `platform-mcp` server when calling `holistic_bundle` | yes — implements the bundle | yes via `/api/mcp/primitives/[tool]` |

**Implication for the plan:** the "tier-aware routing" idea from v2 is still right but the gradient is narrower. The two real audiences for tool descriptions are (a) Claude-style agentic clients hitting MCP HTTP and (b) ops/super-admin clients hitting the same endpoint. Web `/consume` is out of scope for description tuning because it doesn't read MCP descriptions.

### A.3 Governance constraints (binding)

From `CLAUDE.md` v4.0 amended 2026-05-23 and `.geminirules`:

- **SESSION_OPEN handshake** declaring `may_touch` + `must_not_touch` globs (validated by `platform/scripts/governance/schema_validator.py`). Sub-agents must comply.
- **Mirror discipline MP.1**: CLAUDE.md ↔ .geminirules must stay in sync if any architectural change is made (`mirror_enforcer.py` exits non-zero on desync; opens `DIS.class.mirror_desync` entries).
- **No `git add -A`** — stage specific files only.
- **Co-Authored-By trailer** on every commit: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` (the conductor sub-agents will use this).
- **File-placement**: any new root file must consult `00_ARCHITECTURE/ROOT_FILE_POLICY.md`. New plans go in `Plans/` (this file is there).
- **Migration ledger**: every applied migration appends a row to `MIGRATIONS_APPLIED_LOG.md` in the same commit.
- **Merge train**: PRs document order in `MERGE_TRAIN_ORDER_v1_0.md`.
- **CI gate**: `.github/workflows/ci.yml` (Ganga Quality Gate) — typecheck, unit tests, planner-regression, ICR PR gate, coverage gate. Hard-required.

### A.4 Test/CI surface to reuse, not rebuild

- **Vitest** for `*.test.ts` in `platform/` and `platform-mcp/`. Config: `platform/vitest.config.ts` + `platform-mcp/vitest.config.ts`.
- **Playwright** for E2E + visual under `platform/tests/e2e/` and `platform/tests/visual/`. Use this for visual smoke — **do not add Chrome MCP**, Playwright is already wired.
- **CI workflows**: `.github/workflows/ci.yml` (mandatory) + `chat-v2-ci.yml` (15 stages, advisory) + `chat-v2-smoke.yml` (smoke gated by secrets).
- **Eval driver**: `platform/scripts/answer_eval.ts` (hits `/api/chat/consume`) + `platform/tests/eval/planner_*.ts` (planner regression). Use answer_eval as the accuracy baseline.

---

## Part B — Phased Plan (10 phases, real file paths and commands)

Each phase has: goal · sub-agents · concrete files · acceptance · gate · rollback. Sub-agent templates in Part E.

### Phase 0 — Bootstrap & Governance Compliance

**Goal:** worktree, SESSION_OPEN handshake, baseline measurement, no code changes.

**Sub-agent:** `v32-s0-bootstrap` (single)

**Tasks:**
- `git worktree add ../Madhav-mcpt-v32 -b feature/mcpt-v32-quality-tightening`
- Tag baseline: `git tag mcpt-v32-baseline && git push origin mcpt-v32-baseline`
- Author SESSION_OPEN handshake declaring:
  - `may_touch`: `platform-mcp/**`, `platform/src/lib/mcp/**`, `platform/src/app/api/mcp/**`, `platform/scripts/governance/**` (read-only validation only), `Plans/**`, `MIGRATIONS_APPLIED_LOG.md`, `00_ARCHITECTURE/perf_system_seeds/**`, `bench/**`, `accuracy/**`, `platform-mcp/test/**`, `platform/tests/synthesis/**` (additive only).
  - `must_not_touch`: `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `04_REMEDIAL_CODEX/**`, `06_LEARNING_LAYER/**`, anything matching `99_ARCHIVE/**`, `CLAUDE.md` and `.geminirules` (only via mirror-enforced PR-end sync, not within phases).
  - Validate via: `python platform/scripts/governance/schema_validator.py`
- Verify tooling: `gh auth status`, `gcloud auth list`, `gcloud config get-value project` (expect `madhav-astrology`).
- Run baseline tests: `cd platform-mcp && npm test 2>&1 | tee ../bench/mcp_test_baseline.log` and `cd platform && npm test 2>&1 | tee ../bench/platform_test_baseline.log` — capture pass/fail state. Do not fix anything; this is observation.
- Build `bench/scenarios/` skeleton (empty YAMLs to be filled in Phase 8) so later phases have a path to write to.
- Initialize `.conductor-state.json` in the worktree root with phase queue (Part D.1).
- Open PR draft: `gh pr create --base main --head feature/mcpt-v32-quality-tightening --draft --title "[MCPT-v3.2] Bootstrap" --body "Phase 0 only. SESSION_OPEN attached."`.

**Acceptance:**
- Worktree exists; branch pushed.
- SESSION_OPEN validated, attached to PR.
- Baseline test logs committed.
- `.conductor-state.json` initialized with `current_phase: 1`.
- CI green on the branch.

**Rollback:** `git worktree remove ../Madhav-mcpt-v32; git tag -d mcpt-v32-baseline; git push origin :mcpt-v32-baseline`.

---

### Phase 1 — Stale-lies Elimination (immediate accuracy win)

**Goal:** stop the MCP from telling consumers untrue things about its own data state.

**Sub-agents (parallel — disjoint files):**

- `v32-s1a-data_coverage-description` — rewrite `platform-mcp/src/tools/data_coverage.ts:33-48` to remove the "v3.3 backfill pending" sentence. Replace with current truth: "Returns expected vs actual row counts per category. Categories backfilled through MCPT v3.3 (KP, Tajaka, Shadbala, Ashtakavarga, Upagraha, Bhava-Bala) return populated counts. Residuals tracked in `mcp_audit_findings`."
- `v32-s1b-tool_health-data_note` — find and remove the `data_note: "Apply migrations 073-076 and run nightly audit"` fallback in the platform's `/api/mcp/health/...` handlers. Stop claiming pending state when none exists.
- `v32-s1c-supabase-076-seed-comment` — update the seed file at `00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql` lines 54-57 comments to remove the stale warning text.
- `v32-s1d-audit-other-descriptions` — sweep all 21 tool descriptions in `platform-mcp/src/tools/*.ts` for any claim about row counts, backfill state, or pending work. Cross-reference against `MCPT_V33_CLOSE.md` truth. Produce a diff report `Plans/MCPT_V32_DESCRIPTION_AUDIT.md` and fix every false claim.

**Acceptance:**
- `grep -r "pending v3.3 backfill" platform-mcp/ platform/` returns zero matches.
- `grep -r "Apply migrations 073-076" platform/` returns zero matches.
- All 21 tool descriptions reviewed; audit report committed.

**Gate:** lint clean + tests pass + accuracy-diff shows no semantic change (these are description-only edits; `accuracy/diff.json` should report `verdict: pass`).

**Rollback:** revert the four PRs.

---

### Phase 2 — Envelope Standardization (kills double-encoding)

**Goal:** single shared envelope serializer; stop emitting `JSON.stringify(envelope, null, 2)` from every tool.

**Sub-agents (sequential — 2a creates the helper, 2b migrates):**

- `v32-s2a-envelope-helper` — create `platform-mcp/src/tools/_envelope.ts` exporting:
  - `okResult(envelope): { content: [{type, text}], isError?: boolean }`
  - `errorResult(envelope): { content, isError: true }`
  - Behavior: pretty-print only when `process.env.MCP_VERBOSE === 'true'`; otherwise compact. Always passes through the envelope's `ok` flag for `isError` derivation.
  - Unit tests in `platform-mcp/test/_envelope.test.ts`.

- `v32-s2b-tool-migration` — migrate all 21 tool files to call `okResult(envelope)` / `errorResult(envelope)` in place of inline stringify. Files (21):
  - `tools/holistic_bundle_tool.ts`, `multi_school_bundle_tool.ts`, `query_chart_facts.ts`, `query_signals.ts`, `query_dasha_periods.ts`, `query_panchanga.ts`, `query_ephemeris.ts`, `query_transit_event.ts`, `lel_query.ts`, `vector_search.ts`, `get_cgm_subgraph.ts`, `cross_school_lookup.ts`, `read_asset.ts`, `read_classical_text.ts`, `get_trace.ts`, `list_recent_queries.ts`, `tool_health.ts`, `data_coverage.ts`, `log_prediction.ts`, `record_outcome.ts`, `flag_disagreement.ts`.

**Acceptance:**
- `grep -rn "JSON.stringify(envelope" platform-mcp/src/tools/` returns zero hits (excluding `_envelope.ts`).
- All `platform-mcp/test/` tests pass.
- Snapshot test: response shape parses to identical object across all 21 tools, before/after.
- Token-byte snapshot: average response bytes drop ≥30% on multi-row tools (`query_chart_facts`, `query_signals`, `vector_search`) when `MCP_VERBOSE=false`.

**Gate:** snapshot equality + ≥30% byte reduction + zero accuracy regression.

**Rollback:** revert PRs (2 commits).

---

### Phase 3 — Description Standardization (1-of-21 → 21-of-21 builder)

**Goal:** every tool description goes through `description_builder.ts`. Uniform format, coverage hint, enum source.

**Sub-agent:** `v32-s3-descriptions-builder-migration` (single — touches all 21 tools but consistently)

**Tasks:**
- Extend `platform-mcp/src/tools/description_builder.ts` to handle tools without enum sources (most tools).
- Add params: `{ baseDescription, enumSource?, coverageHint?, examples?, tier_note? }`.
- Add a lint rule in `platform-mcp/test/tool_descriptions.test.ts`: every registered tool's description must start with a single disambiguator sentence ("What it does: ..." or "FIRST CALL when ..."); must contain a "When to prefer:" section; total length ≤ 1200 chars.
- Migrate all 20 hand-rolled descriptions to use the builder.
- Sync the description corpus to `Plans/MCPT_V32_TOOL_CATALOG.md` for human review.

**Acceptance:**
- All 21 tools use `buildToolDescription`.
- Lint passes; CI green.
- Routing eval (Phase 9) baseline captured pre-migration; post-migration shows ≥0pp regression (we just want consistency here; the eval improvement is from Phase 6).

**Gate:** lint + tests + accuracy diff clean.

**Rollback:** revert single PR.

---

### Phase 4 — Schema Enrichments (divisional filter + categories[] + chart_summary)

**Goal:** wide-by-default with safe narrowing for irrelevance pruning.

**Sub-agents (parallel — 4a/4b independent; 4c depends on both):**

- `v32-s4a-divisional-filter` — add `divisional_chart` (optional string, enum from DB) to `QueryChartFactsInputSchema` in `platform-mcp/src/tools/query_chart_facts.ts:66-74`. Pass through `callPlatformPrimitive('query_chart_facts', ...)`. Update `platform/src/lib/retrieve/chart_facts_query.ts` to push the filter into the SQL `WHERE` clause. The index already exists from migration 014 + 029.

- `v32-s4b-categories-batching` — replace `category: z.string()` with a discriminated union: either `category: z.string()` (singular, backward-compatible) or `categories: z.array(z.string())`. Handler builds the SQL `IN (...)` when array form is used. Response groups results by category in `result.rows_by_category`.

- `v32-s4c-chart-summary` — new MCP tool `chart_summary` in `platform-mcp/src/tools/chart_summary.ts`. Input: `{ chart_id?: string (defaults to native), divisional_charts?: string[] (defaults to D1+D9+D10), include_categories?: string[], exclude_categories?: string[] }`. Internally calls `query_chart_facts` with the categories array, plus targeted calls to assemble the canonical 50-fact bundle (birth_metadata, planet, house for requested divisionals, yoga across all divisionals, arudha, current vimshottari MD/AD/PD, key sensitive_points). Registered in `platform-mcp/src/server.ts` between `holistic_bundle` and `query_chart_facts`.

**Acceptance:**
- 4a: `query_chart_facts({category:"planet", divisional_chart:"D9"})` returns only D9 rows.
- 4b: `query_chart_facts({categories:["planet","house","yoga"]})` returns rows grouped by category, single round-trip.
- 4c: `chart_summary({divisional_charts:["D1","D9","D10"]})` returns ≥50 fact rows in one call; integration test asserts fixture parity vs current `query_chart_facts` row-by-row.
- New tool `chart_summary` appears in `list_tools` for all audience tiers.

**Gate:** the bench scenario "interpret D9" (Part C.1) completes in ≤2 round-trips using `chart_summary`, vs ≥5 with `query_chart_facts` alone.

**Rollback:** revert 4c PR first; 4a/4b are additive and safe to keep.

---

### Phase 5 — Trace Alignment & `query_summary` Population

**Goal:** `list_recent_queries` returns MCP-facing names and rich summaries; `get_trace(name)` works without translation.

**Sub-agents:**

- `v32-s5a-trace-name-canonicalization` — update `platform/src/app/api/mcp/primitives/[tool]/route.ts:211-241` (`traceEmitter.emitStep`). Currently writes `step_name: retrievalToolName`. Change to write **both** an MCP-facing field (`mcp_tool`) and the retrieval field — and update the trace consumer at `platform-mcp/src/tools/list_recent_queries.ts` to prefer `mcp_tool` when present. Backfill migration `116_trace_mcp_tool_column.sql` adds the column to `query_trace_steps` and populates from `payload->>'mcp_tool'` for historical rows.

- `v32-s5b-query-summary-population` — change `query_summary` from `"chart_facts_query call"` to canonical param representation: `"query_chart_facts(category=planet, divisional_chart=D9, limit=50)"`. Implementation in `platform/src/lib/mcp/trace_summary.ts` (new file).

**Acceptance:**
- `list_recent_queries` returns `tool: "query_chart_facts"` not `"chart_facts_query"`.
- `get_trace(trace_id)` resolves traces by either MCP-facing or retrieval-side name.
- Sample 20 trace rows: `query_summary` contains parameter representation for all of them.

**Gate:** integration test that calls `list_recent_queries` → picks first trace → calls `get_trace` with the returned tool name → succeeds.

**Rollback:** the migration is additive (new column). Revert PR; column stays harmlessly.

---

### Phase 6 — Tier-Aware Description Rendering + `acharya` Tier Resolution

**Goal:** the description Claude sees in `list_tools` varies by `audience_tier`. Resolve the `acharya` tier inconsistency.

**Sub-agents:**

- `v32-s6a-acharya-enum-decision` — read the codebase audit (which paths reference 'acharya'? `data_coverage.ts:48, 56`, others) and the DB enum (`mcp_api_keys.audience_tier`). Two paths:
  - (A) Add `'acharya'` to the DB enum (migration 117), update enum docs, keep current code.
  - (B) Remove `'acharya'` from code and docs; collapse to `client + super_admin`.
  - Decision criteria: is there a real consumer that should be `'acharya'` (e.g. external acharya reviewers per R.M3D.1)? Per `CLAUDE.md` §M acharya review is part of accuracy validation. **Recommend path A** — add to enum, since the accuracy-review use case is documented.
  - Sub-agent produces a decision memo `Plans/MCPT_V32_ACHARYA_TIER_DECISION.md` for human sign-off, then implements.

- `v32-s6b-tier-aware-list-tools` — in `platform-mcp/src/server.ts`, when handling MCP `list_tools` requests, vary the tool ordering and description per `audience_tier`:
  - `client`: hide `data_coverage`, `tool_health`, `log_prediction`, `record_outcome`, `flag_disagreement` (already tier-gated at handler — also hide from catalog).
  - `acharya`: full catalog with `holistic_bundle` and `multi_school_bundle` annotated `"Acharya-review-grade synthesis. Use to verify the fact layer."`.
  - `super_admin`: full catalog, no annotations, all ops tools visible.
  - **Default ordering for agentic clients (Claude Code, etc.)**: `chart_summary` first, then surgical fact tools, then synthesis tools, then ops. Synthesis description appended with: `"Server-side synthesized — prefer chart_summary + your own synthesis unless you specifically want a pre-baked render."`
  - Implementation: a `getCatalogForTier(tier)` function that runs after tool registration and rewrites the in-memory `server._registeredTools` map (or equivalent SDK API).

**Acceptance:**
- `list_tools` response varies by `X-MCP-Audience-Tier` header.
- Snapshot tests for each tier × catalog combination.
- Holistic_bundle and multi_school_bundle output **byte-equal** for the same call across tiers (we're varying only the description in list_tools, not the handler behavior).

**Gate:** snapshot tests + zero handler-behavior regression.

**Rollback:** revert; default tier-blind behavior was the prior state.

---

### Phase 7 — Data Coverage Backbone (seed load + nightly audit)

**Goal:** `data_coverage` actually returns numbers. `tool_health` actually returns metrics.

**Sub-agents (sequential — 7a loads seed, 7b/7c after):**

- `v32-s7a-seed-load** — apply `00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql` to staging then prod. Append entry to `MIGRATIONS_APPLIED_LOG.md` (this is seed-data, not schema; document accordingly under a new "Seed Loads" section). Verify: `SELECT COUNT(*) FROM data_source_expected` returns 23.

- `v32-s7b-nightly-audit-job** — create a Cloud Run job `amjis-mcp-audit` (asia-south1) that:
  - Connects to the DB.
  - For each row in `data_source_expected`, runs `SELECT COUNT(*) FROM <table> WHERE <category-pred>` and updates `actual_rows`.
  - Refreshes the 4 materialized views from migration 082.
  - Emits per-row diff to `mcp_audit_findings`.
  - Wired via Cloud Scheduler: `0 3 * * *` (asia-south1 timezone, so 3:00 AM IST).
  - `gcloud run jobs create amjis-mcp-audit ...`; `gcloud scheduler jobs create http nightly-mcp-audit --schedule="0 3 * * *" --uri="$(gcloud run jobs describe amjis-mcp-audit --format='value(status.url)')/run" --http-method=POST --oidc-service-account-email=audit@madhav-astrology.iam.gserviceaccount.com`.

- `v32-s7c-handlers-truth** — update the platform's `/api/mcp/health/coverage` handler to return real numbers (it already reads `data_source_expected` — the gap was just the empty table). Update `tool_health` handler to read the MVs from migration 082 and stop returning the `data_note` fallback.

**Acceptance:**
- `SELECT COUNT(*) FROM data_source_expected` ≥ 23 rows.
- `gcloud scheduler jobs describe nightly-mcp-audit` → ENABLED.
- `data_coverage` returns numeric `actual_rows` for every active category.
- `tool_health` returns non-null `call_count_24h`, `error_rate`, `avg_latency_ms` for all 21 tools (run after the first scheduled audit, or by manually triggering: `gcloud run jobs execute amjis-mcp-audit`).

**Gate:** zero-null assertion across both ops tools.

**Rollback:** `gcloud scheduler jobs pause nightly-mcp-audit`; revert handler PRs (handlers fall back to the data_note path — this is intentional safety).

---

### Phase 8 — Bench & Accuracy Harness (built from scratch)

**Goal:** machine-checkable performance and accuracy diffs on every PR.

**Sub-agents (parallel):**

- `v32-s8a-bench-harness** — create `platform-mcp/test/bench/`:
  - `bench/scenarios/canonical_d9_workflow.yaml` (mcp_agentic tier, calls `chart_summary` + 1 follow-up).
  - `bench/scenarios/holistic_d9.yaml` (mcp_agentic tier, calls `holistic_bundle`).
  - `bench/scenarios/portal_synthesis_floor.yaml` (super_admin tier, calls `query_chart_facts` x5 mimicking pre-refactor pattern).
  - `bench/run.ts` — vitest-driven scenario runner. Records `round_trips`, `response_bytes`, `wall_time_ms` per scenario.
  - `bench/diff.ts` — compares head `bench/<sha>.json` vs `bench/baseline.json`, emits `bench/diff.json` per the schema in Part C.2.
  - npm scripts: `npm run bench:capture`, `npm run bench:diff`.
  - Wire to CI via a new `.github/workflows/mcp-bench.yml` (triggered on PR touching `platform-mcp/**` or `platform/src/lib/mcp/**`).

- `v32-s8b-accuracy-harness** — create `platform-mcp/test/accuracy/`:
  - `accuracy/fixtures/abhisek-mohanty-golden.json` — full chart_facts snapshot, regenerated from current DB state via `npm run accuracy:regenerate-golden` (manual, requires human sign-off).
  - `accuracy/run.ts` — calls every fact tool against the fixture; diffs row-by-row vs golden.
  - `accuracy/cross_scenario.ts` — implementation per Part C.3.
  - `accuracy/diff.ts` — emits `accuracy/diff.json` per the schema in Part C.2.
  - npm scripts: `npm run accuracy:capture`, `npm run accuracy:diff`, `npm run accuracy:regenerate-golden`.
  - Wire to CI same workflow as bench.

**Acceptance:**
- `npm run bench:capture` produces `bench/<sha>.json` with all 3 scenarios.
- `npm run accuracy:capture` produces `accuracy/<sha>.json` with all 3 checks.
- CI workflow runs both on every PR; PR body includes the diff tables (use `gh pr comment` from the CI job).
- For the Phase 0 baseline tag, `npm run bench:diff -- --baseline mcpt-v32-baseline` reports `verdict: pass` (no change yet).

**Gate:** both harnesses functional + wired to CI.

**Rollback:** keep — harnesses are pure-additive infrastructure.

---

### Phase 9 — Cross-Scenario Equivalence + Routing Eval

**Goal:** prove the agentic and non-agentic synthesis paths agree on factual claims; prove the routing improvements are real.

**Sub-agents (parallel):**

- `v32-s9a-cross-scenario-equivalence** — implement `platform-mcp/test/accuracy/cross_scenario.ts` per Part C.3:
  - Path A (mcp_agentic): mocked Claude calls `chart_summary` + optional follow-ups; collect factual claims via deterministic extractor.
  - Path B (in-process consume path): invoke `executeMCPTool` directly with the same fixture; collect factual claims from the synthesized output via the same extractor.
  - Compare claim sets; require 100% factual agreement (interpretive prose differences allowed).
  - Output: `accuracy/cross_scenario.json`.

- `v32-s9b-routing-eval** — create `evals/mcp-routing/`:
  - `prompts.json` — 30 representative prompts (Adapt 25 from `planner_golden_set.json` + 5 new MCP-surface specific).
  - For each: `{prompt, audience_tier, gold_first_tool, acceptable_alternatives}`.
  - Runner: invokes the MCP server with each prompt via a Haiku-based test driver; records first tool call.
  - Eval gate: ≥80% gold-or-acceptable under `super_admin` tier; ≥15pp improvement vs Phase 0 baseline.

**Acceptance:**
- Cross-scenario equivalence test passes (100% factual agreement).
- Routing eval shows ≥15pp improvement.
- Both wired into the bench/accuracy CI workflow.

**Gate:** both pass on fixture chart.

**Rollback:** these are tests; failures don't roll back anything, they signal we missed a regression in earlier phases.

---

### Phase 10 — Final Verification, Mirror Sync, Prod Promotion

**Goal:** all gates green; mirror discipline maintained; staged → prod.

**Sub-agent:** `v32-s10-final-verify`

**Tasks:**

10.1 **Full test sweep**: `cd platform-mcp && npm test`, `cd platform && npm test`, `npm run eval:planner-regression`. All green.

10.2 **Bench + accuracy final**: run both harnesses against the final commit. Commit `bench/final.json`, `accuracy/final.json`, `bench/diff.md`, `accuracy/diff.md`.

10.3 **Cross-scenario equivalence final**: 100% factual agreement.

10.4 **Mirror sync** (MP.1 discipline): if any architectural change was made (e.g. tier-aware routing in Phase 6 adds a §M.N entry, or new chart_summary tool documented in §M tool catalog), update both `CLAUDE.md` and `.geminirules` in the same commit. Run `python platform/scripts/governance/mirror_enforcer.py` — must exit 0.

10.5 **Migration ledger update**: append rows to `MIGRATIONS_APPLIED_LOG.md` for any migrations applied in Phase 5 (116_trace_mcp_tool_column.sql) and Phase 6 (117_audience_tier_acharya_enum.sql if path A was chosen) and Phase 7 (seed load).

10.6 **Visual smoke** (Playwright): if Phase 4 added `chart_summary` to any UI surface, run the affected Playwright specs under `platform/tests/visual/` and `platform/tests/e2e/chat-v2/__visuals__/`. If no UI affected, document N/A in PR.

10.7 **Staging deploy**: `gcloud builds submit --config=cloudbuild.yaml --substitutions=_TAG=mcpt-v32-staging`. Verify staging URL is healthy: `curl -sS https://<staging-url>/health`.

10.8 **Re-run bench + accuracy + cross-scenario against staging** via env-overridden harness: `MCP_BASE_URL=https://<staging-url> npm run bench:capture && npm run accuracy:capture`.

10.9 **Stop and post a Phase 10 summary** to the PR via `gh pr comment` with staging URL, bench diff table, accuracy diff table, cross-scenario verdict. **Drop the `.conductor-approve-prod` tripwire required from the human.**

10.10 **On approval**: promote staging → prod via Cloud Run traffic split. Tag `mcpt-v32-prod`. Open a 7-day observation window issue via `gh issue create --title "[MCPT-v3.2] Post-prod observation 7-day window" --label "observation"`.

**Acceptance per Part F.**

---

## Part C — Harness Specifications (concrete)

### C.1 Bench scenarios

```yaml
# platform-mcp/test/bench/scenarios/canonical_d9_workflow.yaml
name: canonical_d9_workflow
description: Agentic D9 interpretation. Single chart_summary + 1 follow-up.
audience_tier: super_admin
mcp_base_url: ${MCP_BASE_URL:-http://localhost:8080}
steps:
  - tool: chart_summary
    args: { divisional_charts: ["D1","D9","D10"] }
  - tool: query_chart_facts
    args: { category: aspect, divisional_chart: D9 }
metrics: [round_trips, response_bytes, wall_time_ms]
```

```yaml
# platform-mcp/test/bench/scenarios/portal_synthesis_floor.yaml
name: portal_synthesis_floor
description: Pre-refactor pattern — 5 separate query_chart_facts calls. Floor.
audience_tier: super_admin
steps:
  - tool: query_chart_facts
    args: { category: birth_metadata }
  - tool: query_chart_facts
    args: { category: planet }
  - tool: query_chart_facts
    args: { category: house }
  - tool: query_chart_facts
    args: { category: yoga }
  - tool: query_chart_facts
    args: { category: arudha }
metrics: [round_trips, response_bytes, wall_time_ms]
```

### C.2 Diff JSON schemas

```json
// bench/diff.json
{
  "head_sha": "abc1234",
  "baseline_sha": "mcpt-v32-baseline",
  "scenarios": {
    "canonical_d9_workflow": {
      "baseline": { "round_trips": 5, "response_bytes": 28400, "wall_time_ms": 1850 },
      "head":     { "round_trips": 1, "response_bytes":  8200, "wall_time_ms":  410 },
      "delta_pct": { "round_trips": -80, "response_bytes": -71, "wall_time_ms": -78 }
    }
  },
  "verdict": "pass",
  "regressions": []
}
```

```json
// accuracy/diff.json
{
  "fixture": "abhisek-mohanty",
  "checks": {
    "golden_snapshot": {
      "expected_rows": 2717,
      "actual_rows":   2717,
      "added": [], "removed": [], "changed": []
    },
    "cross_scenario_equivalence": {
      "factual_claim_agreement_pct": 100,
      "disagreements": []
    }
  },
  "verdict": "pass",
  "regressions": []
}
```

**Merge gate:** `accuracy.verdict != "pass"` → block merge regardless of `bench`. `bench.verdict != "pass"` with accuracy pass → conductor records explicit acknowledgment, opens follow-up issue, still merges.

### C.3 Cross-scenario equivalence implementation

```ts
// platform-mcp/test/accuracy/cross_scenario.ts
import { mcpClient } from './mcp_client_for_tests'
import { executeMCPTool } from '../../../platform/src/lib/synthesis/mcp_tool_executor'
import { extractClaims, diffClaims, ClaimSet } from './claim_extractor'

const FIXTURE = 'abhisek-mohanty'

export async function runCrossScenario(): Promise<{
  agreement_pct: number, disagreements: Array<{path: string, a: any, b: any}>
}> {
  // Path A: MCP HTTP, agentic style
  const client = mcpClient({ audience_tier: 'super_admin' })
  const summary = await client.callTool('chart_summary', {
    divisional_charts: ['D1','D9','D10']
  })
  const claimsA = extractClaims(summary)

  // Path B: in-process executeMCPTool, replays the consume route's tool invocations
  const queryPlan = buildConsumePlanForFixture(FIXTURE)
  const resultsB = await Promise.all(queryPlan.tools.map(t =>
    executeMCPTool(t, { queryPlan })
  ))
  const claimsB = extractClaims(mergeResults(resultsB))

  return diffClaims(claimsA, claimsB)
}

// claim_extractor.ts: regex+grammar extractor (deterministic, no LLM)
// Pulls: planet_placements, yogas, karakas, dasha_periods, arudha_houses
```

### C.4 Routing eval format

```json
// evals/mcp-routing/prompts.json
[
  {
    "id": "d9_interpretation_001",
    "prompt": "Give me my D9 chart",
    "audience_tier": "super_admin",
    "gold_first_tool": "chart_summary",
    "acceptable_alternatives": ["query_chart_facts"]
  },
  {
    "id": "shadbala_single",
    "prompt": "What is Saturn's shadbala?",
    "audience_tier": "super_admin",
    "gold_first_tool": "query_chart_facts",
    "acceptable_alternatives": []
  }
]
```

Runner harness invokes Haiku via Anthropic SDK with the MCP catalog from `list_tools`, records first tool call.

### C.5 Description lint rule

In `platform-mcp/test/tool_descriptions.test.ts`, add:

```ts
import { CATALOG } from '../src/server'  // exports registered tools
test('every description starts with a disambiguator sentence', () => {
  for (const tool of CATALOG) {
    const first = tool.description.split('. ')[0]
    expect(first).toMatch(/^(What it does|FIRST CALL when|Returns)/)
    expect(tool.description.length).toBeLessThanOrEqual(1200)
    expect(tool.description).toMatch(/When to prefer/)
  }
})
```

---

## Part D — Conductor Operational Spec

### D.1 `.conductor-state.json` (at worktree root)

```json
{
  "version": 1,
  "started_at": "2026-05-23T15:30:00Z",
  "branch": "feature/mcpt-v32-quality-tightening",
  "current_phase": 1,
  "phases": [
    {"id": 0, "status": "completed", "pr_url": "...", "gate_artifact": "bench/mcp_test_baseline.log"},
    {"id": 1, "status": "in_progress", "sub_agents": [
      {"id": "v32-s1a-data_coverage-description", "status": "completed", "pr_url": "..."},
      {"id": "v32-s1b-tool_health-data_note", "status": "in_progress"}
    ]}
  ],
  "escalations": [],
  "human_gates_pending": []
}
```

Conductor MUST commit this file after every state change. On context reset, new conductor reads it and resumes.

### D.2 Sub-agent prompt template

```
You are sub-agent <ID> for MCPT v3.2 Quality Tightening.

PHASE: <N> — <name>
TASK: <one-line>
GLOBAL PLAN: Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md (read your phase section verbatim)

REPO: /Users/Dev/Vibe-Coding/Apps/Madhav (you may be in a worktree off main; check `git branch`)

YOUR DELIVERABLE
- Implement on branch `feature/mcpt-v32-quality-tightening`.
- Author commits with trailer `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`.
- Do NOT use `git add -A` — stage specific files.
- Respect `must_not_touch` globs from the SESSION_OPEN handshake at .conductor-state.json.
- Run tests: `cd platform-mcp && npm test` AND `cd platform && npm test` (whichever are affected).
- Run bench: `cd platform-mcp && npm run bench:capture && npm run bench:diff` (Phase 8+ only).
- Run accuracy: `cd platform-mcp && npm run accuracy:capture && npm run accuracy:diff` (Phase 8+ only).
- Open PR:
  gh pr create --base feature/mcpt-v32-quality-tightening --head <your-branch> \
    --title "[MCPT-v3.2][phase-<N>] <task summary>" \
    --body-file PR_BODY.md

PR_BODY.md MUST INCLUDE
- ## Scope
- ## Files touched (no `git add -A` paths)
- ## Acceptance criteria (from plan, checked off)
- ## Bench diff table (paste from bench/diff.md)
- ## Accuracy diff table (paste from accuracy/diff.md)
- ## Risks
- ## Rollback command
- ## Mirror impact (does this require CLAUDE.md/.geminirules sync?)

CORE RULES (NON-NEGOTIABLE)
1. Accuracy > Performance. If accuracy/diff.json shows ANY regression, do not open the PR — escalate.
2. Never deprecate a tool. holistic_bundle + multi_school_bundle stay; Phase 6 only varies their description per audience_tier.
3. Bench/accuracy diffs are mandatory on every PR.
4. Default wide on responses; narrow only for irrelevance pruning.

ESCALATION
- Blocked > 30 min or > 50 tool calls → write status to .conductor-state.json, return status="blocked".
- Accuracy regression you cannot resolve → return status="accuracy_regression" with diff details.

GO.
```

### D.3 Tripwires (drop in worktree root)

- `.conductor-pause` → finish current sub-agent, await removal.
- `.conductor-abort` → STOP immediately, no merges in-flight.
- `.conductor-approve-prod` → Phase 10 prod promotion approved.

### D.4 Conductor decision logic

After every sub-agent return:
```
IF status == "completed" AND PR exists:
  Review PR diff.
  IF acceptance met AND bench.verdict == "pass" AND accuracy.verdict == "pass":
    gh pr merge <PR> --squash --auto
  ELIF accuracy.verdict == "regress":
    ESCALATE. STOP. Surface to human via TaskCreate("ESCALATION: accuracy regression in <PR>").
  ELIF bench.verdict == "regress" AND accuracy clean:
    Add explicit acknowledgment to PR body. Open follow-up issue. Merge with --auto.
  ELSE:
    Spawn fix sub-agent with diff details.

IF status == "blocked" OR "accuracy_regression":
  ESCALATE.

IF all sub-agents in phase done:
  Run phase gate command.
  Commit gate artifacts.
  Advance to next phase OR escalate.
```

---

## Part E — Setup & Conductor Prompts (paste-ready)

### E.1 Setup Prompt (paste on `main` in Claude Code in Antigravity)

```
You are setting up the worktree for MCPT v3.2 Quality Tightening. STOP at the end — do not begin implementation.

1. Verify clean state:
   cd /Users/Dev/Vibe-Coding/Apps/Madhav
   git status --porcelain   # must be empty
   git rev-parse --abbrev-ref HEAD  # must be 'main'
   If not, abort and report.

2. Pull latest:
   git pull --ff-only origin main

3. Verify Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md is checked into main. If not, copy it from the file the user provided into Plans/, commit, push:
   git add Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md
   git commit -m "docs: MCPT v3.2 optimization plan" --trailer "Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   git push origin main

4. Tag baseline:
   git tag mcpt-v32-baseline
   git push origin mcpt-v32-baseline

5. Create worktree + branch:
   git worktree add ../Madhav-mcpt-v32 -b feature/mcpt-v32-quality-tightening
   cd ../Madhav-mcpt-v32
   git push -u origin feature/mcpt-v32-quality-tightening

6. Verify tooling:
   gh auth status
   gcloud auth list
   gcloud config get-value project   # expect madhav-astrology

7. Run baseline tests (do not fix anything, just observe):
   cd platform-mcp && npm install && npm test 2>&1 | tee /tmp/mcp_baseline.log
   cd ../platform && npm install && npm test 2>&1 | tee /tmp/platform_baseline.log

8. Validate SESSION_OPEN governance is in place:
   python platform/scripts/governance/schema_validator.py

9. Kick CI:
   gh workflow run ci.yml --ref feature/mcpt-v32-quality-tightening
   gh run watch

10. Print absolute path of worktree and STOP. Tell the user:
    "Worktree ready at <path>. Switch into it and paste the autonomous conductor prompt from Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md Part E.2."
```

### E.2 Autonomous Conductor Prompt (paste in worktree with `claude --dangerously-skip-permissions`)

```
You are the CONDUCTOR for MCPT v3.2 Quality Tightening.

GLOBAL PLAN
- Read Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md end-to-end before doing anything.
- Treat that file as ground truth. Disagreement → escalate, don't deviate.

YOUR ROLE
- Spawn sub-agents (one per phase task). Review their PRs.
- Hold only the plan, current phase, and gate state in your context.
- PERSIST state to .conductor-state.json after every change. If context resets, new conductor reads the file and resumes.

CORE RULES (NON-NEGOTIABLE)
1. Accuracy > Performance, always. accuracy/diff.json verdict != pass → STOP, escalate.
2. Never deprecate a tool. Synthesis stays.
3. Every PR has bench/diff.md AND accuracy/diff.md.
4. Default wide on responses.
5. Respect SESSION_OPEN must_not_touch globs at all times.
6. Every commit gets the Co-Authored-By trailer.
7. No `git add -A`.

PERMISSIONS
- Running with --dangerously-skip-permissions. Use freely for gh, gcloud, git, npm, vitest, playwright.
- Do NOT: deploy to prod without .conductor-approve-prod tripwire; force-push; destructive SQL on prod; touch must_not_touch globs.

TRIPWIRES (check every loop)
- .conductor-pause → finish current sub-agent, await removal.
- .conductor-abort → STOP immediately, no merges.
- .conductor-approve-prod → Phase 10 prod promotion approved.

EXECUTION LOOP
For each phase 0 → 10:
  1. Read phase section.
  2. Initialize sub-agent entries in .conductor-state.json; commit.
  3. For each sub-agent (parallelize disjoint ones):
     - Spawn via Task tool using the template in Part D.2.
     - Wait. Apply decision logic from Part D.4.
     - Update state after every change.
  4. Run phase gate. Commit artifacts. Advance or escalate.

PHASE 10 PROD GATE — SPECIAL
- After 10.7 staging deploy, STOP. Post summary to PR via `gh pr comment`.
- Poll for .conductor-approve-prod every 60s.
- Once present: promote prod via cloud run traffic split. Tag mcpt-v32-prod. Open observation issue.

MIRROR DISCIPLINE
- After any architectural change (Phase 4c, 6a, 6b are candidates), run `python platform/scripts/governance/mirror_enforcer.py`. If it exits non-zero, spawn a mirror-sync sub-agent before merging the phase.

START HERE
1. Read .conductor-state.json. If current_phase > 0, resume.
2. Else, begin Phase 0.

GO.
```

---

## Part F — Acceptance Criteria (Done = Done)

- [ ] Phase 0: worktree, SESSION_OPEN, baselines committed.
- [ ] Phase 1: zero false claims in tool descriptions.
- [ ] Phase 2: no `JSON.stringify(envelope` outside `_envelope.ts`; ≥30% byte reduction on multi-row tools.
- [ ] Phase 3: all 21 tools use `buildToolDescription`; lint passes.
- [ ] Phase 4: `divisional_chart`, `categories[]`, `chart_summary` shipped; canonical D9 workflow ≤ 2 round-trips.
- [ ] Phase 5: trace tool-name aligned; `get_trace(mcp_name)` works; query_summary has real params.
- [ ] Phase 6: tier-aware list_tools; acharya tier resolved; synthesis output byte-equal across tiers.
- [ ] Phase 7: `data_source_expected` seeded; nightly audit job running; data_coverage + tool_health return real numbers.
- [ ] Phase 8: bench + accuracy harness functional and wired to CI.
- [ ] Phase 9: cross-scenario equivalence = 100% factual agreement; routing eval +15pp.
- [ ] Phase 10: full sweep green; mirror sync clean; staging healthy; human approved; prod tagged.

---

## Part G — Risks & Rollback

| Risk | Mitigation | Rollback |
|---|---|---|
| Phase 2 envelope change parses differently in a client | snapshot tests pre/post; `MCP_VERBOSE=true` returns old shape | revert PR; centralized helper preserves both modes |
| Phase 4 `chart_summary` returns wrong fact set | reference-chart parity vs `query_chart_facts` row-by-row in CI | revert tool registration in `server.ts` |
| Phase 5 migration 116 breaks query_trace_steps queries | additive column only; backfill from payload JSON | column is nullable; harmless if reverted |
| Phase 6 tier-aware list_tools breaks existing client | default tier = `super_admin` behavior preserved when header missing | revert |
| Phase 7 nightly audit job hammers DB | rate-limited, runs at 3 AM IST during low traffic | `gcloud scheduler jobs pause` |
| Phase 8 bench introduces flakiness in CI | bench is on separate workflow, advisory not required for first 2 weeks | mark workflow as `continue-on-error` |
| Phase 9 cross-scenario reveals genuine factual divergence | this is the test working — STOP, surface, do not paper over | freeze refactor, investigate the divergence |
| Mirror desync breaks CLAUDE.md ↔ .geminirules | mirror_enforcer.py exits 0 required in Phase 10.4 | spawn mirror-sync sub-agent, re-run |

---

## Part H — What I Deliberately Did NOT Plan

- **Adding `acharya` to DB enum** is in scope (Phase 6a) but with a decision memo. If the human picks path B (drop `acharya` from code), Phase 6a's other tasks shift accordingly.
- **`kp_significator` 7/9 residual** — upstream FORENSIC source gap, not a v3.2 concern. Document under `Plans/MCPT_V32_RESIDUALS.md` and defer.
- **Touching `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`** — explicitly must_not_touch. These are content layers governed by other macro-phases.
- **Chat-V2 (R11) work** — separate active arc, not in this scope.
- **M5 macro-phase content** — that's the next arc after this one.
- **Chrome MCP for visual smoke** — Playwright is already wired and used. Adding Chrome MCP is gratuitous.
- **A separate Excalidraw architecture diagram** — there's already a diagram in the v2 plan + the chat history; not needed for execution.

---

## Appendix — Predicted File Layout After v3.2

```
platform-mcp/
├── src/
│   ├── tools/
│   │   ├── _envelope.ts                    # NEW — Phase 2
│   │   ├── description_builder.ts          # extended — Phase 3
│   │   ├── chart_summary.ts                # NEW — Phase 4
│   │   ├── query_chart_facts.ts            # modified — Phase 4
│   │   └── (all 21 tools migrated to _envelope + builder)
│   └── server.ts                           # modified — Phase 4 + 6
└── test/
    ├── _envelope.test.ts                   # NEW — Phase 2
    ├── tool_descriptions.test.ts           # extended — Phase 3
    ├── bench/                              # NEW — Phase 8
    │   ├── scenarios/*.yaml
    │   ├── run.ts
    │   ├── diff.ts
    │   ├── baseline.json (Phase 0)
    │   └── final.json (Phase 10)
    └── accuracy/                           # NEW — Phase 8
        ├── fixtures/abhisek-mohanty-golden.json
        ├── run.ts
        ├── cross_scenario.ts               # Phase 9
        ├── claim_extractor.ts              # Phase 9
        ├── diff.ts
        ├── baseline.json
        └── final.json

platform/
├── src/
│   ├── lib/mcp/
│   │   ├── primitives_registry.ts          # unchanged — already correct
│   │   └── trace_summary.ts                # NEW — Phase 5
│   ├── app/api/mcp/
│   │   └── primitives/[tool]/route.ts      # modified — Phase 5 (trace name)
│   └── lib/synthesis/
│       └── mcp_tool_executor.ts            # unchanged (Phase 9 calls it)
├── migrations/
│   └── 116_trace_mcp_tool_column.sql       # NEW — Phase 5
├── supabase/migrations/
│   └── 083_audience_tier_acharya_enum.sql  # NEW — Phase 6a (path A)
└── tests/
    └── (unchanged; bench + accuracy live under platform-mcp/test/)

00_ARCHITECTURE/perf_system_seeds/
└── data_source_expected_seed.sql           # loaded — Phase 7

Plans/
├── MCPT_V32_OPTIMIZATION_PLAN_v3.md        # this file
├── MCPT_V32_DESCRIPTION_AUDIT.md           # Phase 1
├── MCPT_V32_ACHARYA_TIER_DECISION.md       # Phase 6a
├── MCPT_V32_TOOL_CATALOG.md                # Phase 3
└── MCPT_V32_RESIDUALS.md                   # Phase 10

evals/mcp-routing/                          # NEW — Phase 9
├── prompts.json
└── runner.ts

.github/workflows/
└── mcp-bench.yml                           # NEW — Phase 8

MIGRATIONS_APPLIED_LOG.md                   # appended — Phase 5, 6a, 7
CLAUDE.md                                   # synced — Phase 10.4 if any §M update
.geminirules                                # synced — Phase 10.4 if any §M update
```
