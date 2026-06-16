---
title: Ustad — Phase O Observatory: Claude Code Session Prompts
status: WORKING_AID
not_a_canonical_artifact: true
purpose: Self-contained prompts for Claude Code (in Antigravity IDE) to execute every session of Phase O — LLM Cost & Usage Observatory build.
authored: 2026-05-02
session_count: 30
canonical_phase_plan: 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (will be created by S0.1)
---

# Ustad — Phase O Observatory: Claude Code Session Prompts

## How to use this file

This file is a working aid, not a governance artifact. It contains one prompt per Phase O session (30 total). Paste a prompt into Claude Code in Antigravity IDE to execute that session.

Architecture: every session past S0.1 runs in its own git worktree (its own filesystem checkout) on its own sub-branch cut from the umbrella branch `feature/phase-o-observatory`. This is the only way to run multiple Claude Code sessions in parallel without them stomping on each other's working directory or git refs. S0.1 is the sequential gate session and runs in the main working directory.

1. Run the **One-time umbrella setup** below before starting any session (skip if already done).
2. Run **S0.1** first in the main working directory `/Users/Dev/Vibe-Coding/Apps/Madhav`.
3. After S0.1 closes and merges, run the **Worktree spawn helper** for each subsequent session, open a new Antigravity window pointed at that worktree, and paste the session prompt.
4. When a session closes successfully, run the **Worktree teardown** block at the end of that session's prompt.

## One-time umbrella setup
(Skip if `feature/phase-o-observatory` already exists.)
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main
git checkout -b feature/phase-o-observatory
git push -u origin feature/phase-o-observatory
```

## Worktree spawn helper (run before every session past S0.1)
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout feature/phase-o-observatory
git pull
SESSION_ID=ustad-s1-1-schema   # change per session — see mapping (format: ustad-s{phase}-{seq}-{slug})
git worktree add "../Madhav-${SESSION_ID}" -b "feature/phase-o-observatory/${SESSION_ID}" feature/phase-o-observatory
```
Then open a new Antigravity IDE window pointed at `/Users/Dev/Vibe-Coding/Apps/Madhav-${SESSION_ID}` and paste the session prompt.

## Worktree architecture
Every parallel Phase O session has its own git worktree, branch, and Antigravity IDE window. Sessions cannot interfere with each other's git state, working tree, or filesystem. S0.1 is the sequential gate exception — runs in the main working directory and commits directly to `feature/phase-o-observatory`. When a session closes successfully, its sub-branch merges back to the umbrella, the worktree is removed, and the sub-branch is deleted (locally and remotely). Cleanup commands are at the bottom of each session prompt.

---

## Phase O.0 — Governance Bootstrap

### USTAD_S0_1 — Phase O Plan Artifact

```
Ustad — Execute Session USTAD_S0_1 — Phase O Observatory Governance Bootstrap.

# Branch
git checkout feature/phase-o-observatory
git pull

# Required reading (read in this order before any work)
1. CLAUDE.md
2. 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
3. 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md (sections relevant to platform + cross-cutting workstreams)
4. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md (Cross-cutting workstreams + Ethical Framework + Scope Boundary sections)
5. 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md (skim for the structural shape of a phase plan)
6. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
7. 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md (sections C.1–C.6 and K)
8. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
9. 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
10. 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
11. 00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md
12. .geminirules and .gemini/project_state.md

# Session-open handshake
Emit a SESSION_OPEN block per the template. Cowork thread name: phase-o-s0-1-governance-bootstrap. Validate with platform/scripts/governance/schema_validator.py before proceeding.

# Scope
may_touch:
  - 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (CREATE)
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json (UPDATE — register OBSERVATORY_PLAN)
  - 00_ARCHITECTURE/manifest_overrides.yaml (UPDATE if needed for mirror pair declarations)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (UPDATE — add Phase O concurrent workstream block)
  - .geminirules (UPDATE — adapted-parity mirror)
  - .gemini/project_state.md (UPDATE — adapted-parity mirror)
  - 00_ARCHITECTURE/SESSION_LOG.md (APPEND — atomic open+body+close entry)

must_not_touch:
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - platform/**
  - All other 00_ARCHITECTURE/** files not listed in may_touch
  - 06_LEARNING_LAYER/** (does not yet exist; out of scope)

# Dependencies
None. This is the gate session for Phase O.

# Deliverable
Author 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md as a versioned, frontmatter-bearing canonical artifact with:
- Frontmatter: canonical_id=OBSERVATORY_PLAN, version=1.0.0, status=CURRENT, authored_session=S0.1, authored_date=2026-05-02
- §1 Mission and ethical framing (probabilistic, calibrated, auditable; super-admin observability over LLM spend)
- §2 Architecture: two-layer ledger (telemetry + reconciliation). Telemetry layer captures every call with computed cost from versioned pricing table. Reconciliation layer pulls authoritative numbers from each provider's admin/billing API and records variance. Per-request inference responses do NOT return cost — cost is computed; reconciliation backstops authority.
- §3 Data model: 5 tables — llm_usage_events, llm_pricing_versions, llm_provider_cost_reports, llm_cost_reconciliation, llm_budget_rules — with full column lists, indices, and key relationships.
- §4 Provider integration matrix for Anthropic, OpenAI, Gemini, DeepSeek, NIM. For each: per-request capture mechanism, authoritative reconciliation source, lag, gotchas (cache token semantics, reasoning tokens, etc.).
- §5 Sub-phases O.0–O.4 with full session matrices (S0.1 through S4.6, ~30 sessions). For each session: ID, title, may_touch globs, must_not_touch globs, dependencies, deliverable summary, acceptance criteria summary.
- §6 Parallelization discipline: file-tree partitioning (sessions touch disjoint subtrees), registry-update funneling (only specific sessions touch CAPABILITY_MANIFEST.json), mirror-update funneling (only governance sessions trigger MP.1/MP.2 mirror).
- §7 Wall-clock projection at 4-way and 8-way concurrency.
- §8 Phase O acceptance criteria for close.
- §9 Risks and mitigations.
- §10 Open decisions deferred to native (storage layer choice, retention policy, etc.).

Update 00_ARCHITECTURE/CAPABILITY_MANIFEST.json to register OBSERVATORY_PLAN as a canonical artifact (canonical_id, path, version, status). If OBSERVATORY_PLAN has mirror counterparts, declare the mirror pair in manifest_overrides.yaml.

Update 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2 with a Phase O block: "Concurrent workstream Phase O — Observatory active since 2026-05-02; gate session S0.1 closed; next sessions parallel-safe per OBSERVATORY_PLAN §5."

Mirror to .geminirules and .gemini/project_state.md (adapted parity, not byte-identical) — note Phase O active and that L4 Discovery work continues unaffected.

# Acceptance criteria
- OBSERVATORY_PLAN_v1_0.md exists and frontmatter validates against schema_validator.py
- CAPABILITY_MANIFEST.json includes OBSERVATORY_PLAN entry; drift_detector.py exits 0
- CURRENT_STATE_v1_0.md updated with Phase O block
- Mirror updates propagated; mirror_enforcer.py exits 0
- SESSION_OPEN and SESSION_CLOSE blocks both emitted and validated
- SESSION_LOG.md entry appended atomically (open+body+close in one entry)
- All commits on feature/phase-o-observatory
- Final answer in chat reports: commit SHA(s), file paths created/modified, drift+mirror+schema check exit codes

# Close
Emit SESSION_CLOSE per template. Append SESSION_LOG entry atomically. Commit and report.
```

---

## Phase O.1 — Telemetry + Overview Dashboard (the MVP)

### USTAD_S1_1 — Schema migrations

```
Ustad — Execute Session USTAD_S1_1 — Observatory Schema Migrations.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-1-schema on branch feature/phase-o-observatory/s1-1-schema.
Verify before starting:
  pwd                          # must end in Madhav-s1-1-schema
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-1-schema
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§3 Data model)
3. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
4. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
5. 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
6. platform/db/migrations/ (existing migrations — match the project's migration style and naming)
7. platform/src/lib/db/schema/ (existing schema files — match conventions)

# Session-open handshake
Cowork thread: ustad-s1-1-schema. Emit and validate.

# Scope
may_touch:
  - platform/db/migrations/*observatory*
  - platform/src/lib/db/schema/observatory.ts
  - platform/src/lib/db/seed/observatory_pricing/**
  - platform/src/lib/db/__tests__/observatory_*.test.ts
must_not_touch:
  - All other platform/** files
  - 00_ARCHITECTURE/** (except SESSION_LOG.md append at close)
  - 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**

# Dependencies
S0.1 must be closed and merged.

# Deliverable
Create migration(s) and schema file for the 5 tables defined in OBSERVATORY_PLAN §3:

1. llm_usage_events — per-call telemetry. Columns: event_id (uuid pk), conversation_id, conversation_name, prompt_id, parent_prompt_id (nullable, fk self), user_id, provider (enum: anthropic|openai|gemini|deepseek|nim), model, pipeline_stage (enum: classify|compose|retrieve|synthesize|audit|other), prompt_text, response_text, system_prompt, parameters (jsonb), input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, computed_cost_usd (numeric(12,6)), pricing_version_id (fk), latency_ms, status (enum: success|error|timeout), error_code, provider_request_id, started_at, finished_at, feature_flag_state (jsonb), client_ip_hash, created_at. Indices on (started_at), (provider, model), (conversation_id), (user_id), (pipeline_stage).

2. llm_pricing_versions — versioned price book. Columns: pricing_version_id (uuid pk), provider, model, token_class (enum: input|output|cache_read|cache_write|reasoning), price_per_million_usd (numeric), effective_from (timestamp), effective_to (timestamp nullable), source_url, recorded_at. Index on (provider, model, effective_from desc).

3. llm_provider_cost_reports — raw daily pulls from admin APIs. Columns: report_id (uuid pk), provider, model nullable, time_bucket_start, time_bucket_end, workspace_id nullable, authoritative_cost_usd (numeric), authoritative_input_tokens, authoritative_output_tokens, raw_payload (jsonb), pulled_at. Index on (provider, time_bucket_start).

4. llm_cost_reconciliation — match between events and reports. Columns: reconciliation_id (uuid pk), reconciliation_date (date), provider, model nullable, computed_total_usd, authoritative_total_usd, variance_usd, variance_pct, event_count, status (enum: matched|variance_within_tolerance|variance_alert|missing_authoritative), notes, reconciled_at. Index on (reconciliation_date, provider).

5. llm_budget_rules — budget thresholds. Columns: budget_rule_id (uuid pk), name, scope (enum: total|provider|model|pipeline_stage), scope_value nullable, period (enum: daily|weekly|monthly), amount_usd (numeric), alert_thresholds (jsonb — array of {pct, channel}), created_by_user_id, active boolean, created_at, updated_at.

Seed pricing table v1 with current published rates as of 2026-05-02 for: Anthropic (Opus 4.6, Sonnet 4.6, Haiku 4.5 — all token classes); OpenAI (GPT-5 family, o-series — input, output, cached, reasoning); Gemini (2.5 Pro, 2.5 Flash); DeepSeek (V3 chat, R1); NIM (Llama-3 405B and other commonly-served models). Cite source_url for each price row.

Provide an idempotent seed script at platform/src/lib/db/seed/observatory_pricing/seed_v1.ts.

Write tests covering: migration up creates all 5 tables with correct columns and indices; migration down cleanly reverses; seed script is idempotent (running twice does not duplicate rows).

# Acceptance criteria
- Migration files created and run cleanly up + down on a fresh test db
- Schema file exports types matching every column
- Seed script runs idempotently
- Tests pass
- drift_detector.py and schema_validator.py exit 0
- SESSION_CLOSE validates; SESSION_LOG entry appended

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-1-schema"
  git push
  git worktree remove "../Madhav-s1-1-schema"
  git branch -d "feature/phase-o-observatory/s1-1-schema"
  git push origin --delete "feature/phase-o-observatory/s1-1-schema"

# Close
Standard close per template. Report commit SHA, migration filenames, and test pass count.
```

### USTAD_S1_2 — LLMClient instrumentation shim

```
Ustad — Execute Session USTAD_S1_2 — LLMClient Instrumentation Shim.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-2-llmclient-shim on branch feature/phase-o-observatory/s1-2-llmclient-shim.
Verify before starting:
  pwd                          # must end in Madhav-s1-2-llmclient-shim
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-2-llmclient-shim
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§2 architecture, §3 data model)
3. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
4. platform/src/lib/llm/ (existing LLM client code — read all of it; understand the abstraction in place today)
5. platform/src/lib/db/schema/observatory.ts (from S1.1)

# Session-open handshake
Cowork thread: ustad-s1-2-llmclient-shim.

# Scope
may_touch:
  - platform/src/lib/llm/observability/**
  - platform/src/lib/llm/types/observatory.ts
  - platform/src/lib/llm/observability/__tests__/**
must_not_touch:
  - platform/src/lib/llm/providers/** (those are S1.4–S1.8)
  - All UI files
  - Migration / schema files (frozen after S1.1)

# Dependencies
S1.1 closed and merged.

# Deliverable
Build an observability shim that wraps every outbound LLM call and writes an llm_usage_events row. Files:

- platform/src/lib/llm/observability/types.ts — TypeScript types: ObservedLLMRequest (provider, model, prompt_text, system_prompt, parameters, conversation_id, conversation_name, prompt_id, parent_prompt_id, user_id, pipeline_stage), ObservedLLMResponse (response_text, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, provider_request_id, status, error_code, started_at, finished_at), TokenUsage, ProviderName, PipelineStage.

- platform/src/lib/llm/observability/observe.ts — exported function `observe<T>(request: ObservedLLMRequest, providerCall: () => Promise<ProviderRawResponse<T>>): Promise<{ response: T; observation: PersistedObservation }>`. Captures timing, normalizes provider response into ObservedLLMResponse, computes cost from current pricing version, persists to llm_usage_events, returns both the original response and the persisted observation row. For streaming, exports `observeStream` that accumulates token counts from the final usage chunk.

- platform/src/lib/llm/observability/cost.ts — `computeCost(provider, model, tokens, pricingVersionId)` resolves the active pricing version row(s) and computes input + output + cache + reasoning totals. Returns { computed_cost_usd, pricing_version_id }. Pricing version selection: pick the row where started_at falls between effective_from and (effective_to ?? infinity).

- platform/src/lib/llm/observability/redaction.ts — redaction policy. Default: full capture for super-admin observability. Hooks for future PII redaction (truncate, hash-only, off). Make the policy a function so it's swappable per environment.

- platform/src/lib/llm/observability/persist.ts — DB writer. Transactional insert into llm_usage_events. Handles both success and error paths (errored calls still persist with status=error and error_code).

- Tests in __tests__/: cost computation across all token classes; pricing version resolution at boundary timestamps; redaction policy default behavior; observe() wraps a mock provider call correctly; observeStream accumulates correctly; failure modes persist with status=error.

# Acceptance criteria
- All files created with full TypeScript types
- Test coverage ≥90% on observe.ts and cost.ts
- All tests pass
- No imports of provider-specific SDKs (this is provider-agnostic)
- SESSION_CLOSE validates

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-2-llmclient-shim"
  git push
  git worktree remove "../Madhav-s1-2-llmclient-shim"
  git branch -d "feature/phase-o-observatory/s1-2-llmclient-shim"
  git push origin --delete "feature/phase-o-observatory/s1-2-llmclient-shim"

# Close
Standard close. Report commit SHA, test count, coverage report.
```

### USTAD_S1_3 — Backend API for dashboard

```
Ustad — Execute Session USTAD_S1_3 — Observatory Backend API.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-3-backend-api on branch feature/phase-o-observatory/s1-3-backend-api.
Verify before starting:
  pwd                          # must end in Madhav-s1-3-backend-api
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-3-backend-api
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 dashboard UX, §3 data model)
3. platform/src/lib/db/schema/observatory.ts
4. platform/src/lib/llm/observability/types.ts
5. platform/src/app/api/admin/ (existing admin API patterns — match auth, error handling, response shapes)

# Session-open handshake
Cowork thread: ustad-s1-3-backend-api.

# Scope
may_touch:
  - platform/src/app/api/admin/observatory/**
  - platform/src/lib/observatory/queries.ts
  - platform/src/lib/observatory/__tests__/queries.test.ts
must_not_touch:
  - UI files (platform/src/lib/components/**, platform/src/app/(super-admin)/**)
  - LLM provider files
  - Schema/migration files

# Dependencies
S1.1 closed and merged.

# Deliverable
Build five GET endpoints under /api/admin/observatory, all gated by super-admin auth and the MARSYS_FLAG_OBSERVATORY_ENABLED feature flag (which S1.9 will introduce; for this session, gate on the env var directly with a TODO for the flag wiring):

1. GET /api/admin/observatory/summary?from=&to=&compare_to_previous=true|false&[filters]
   Returns: { total_cost_usd, total_requests, total_input_tokens, total_output_tokens, total_cache_tokens, avg_cost_per_request, p50_latency_ms, p95_latency_ms, reconciliation_variance_pct, reconciliation_through_date }. With compare_to_previous=true, also returns *_delta fields.

2. GET /api/admin/observatory/timeseries?from=&to=&granularity=hour|day|week&dimension=provider|model|pipeline_stage&[filters]
   Returns: { buckets: [{ time, series: { [dim_value]: cost_usd }}] }.

3. GET /api/admin/observatory/breakdowns?from=&to=&dimension=provider|model|pipeline_stage|conversation
   Returns: { rows: [{ dim_value, cost_usd, request_count, input_tokens, output_tokens, cache_tokens, avg_latency_ms }] } sorted by cost_usd desc.

4. GET /api/admin/observatory/events?from=&to=&[filters]&limit=&cursor=
   Cursor-paginated list of llm_usage_events rows. Filters: provider[], model[], pipeline_stage[], conversation_id, user_id, status, min_cost, max_cost, min_latency, max_latency, search (matches prompt_text or response_text).

5. GET /api/admin/observatory/event/[id]
   Full event detail including prompt_text, response_text, system_prompt, parameters, raw_provider_payload (from a join — if you need a raw_payload column on events, propose it; otherwise document that S1.4–S1.8 will need to populate a separate llm_provider_raw_responses table — surface this as an open decision rather than silently changing schema).

All queries push filters to SQL, never do post-fetch filtering of large result sets. Date-range queries use the (started_at) index.

Write integration tests using a test database with seeded llm_usage_events fixtures.

Define an OpenAPI schema document at platform/src/app/api/admin/observatory/openapi.yaml describing all five endpoints (response shapes, filter params, error codes). The frontend sessions (S1.9–S1.12) will consume this.

# Acceptance criteria
- All five endpoints implemented with full TypeScript types
- OpenAPI spec exists and is consistent with implementation
- Integration tests pass with realistic fixtures (≥100 event rows across providers/models)
- Auth gate refuses non-super-admin
- All queries use indices (verify with EXPLAIN on a few representative queries; report findings)
- SESSION_CLOSE validates

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-3-backend-api"
  git push
  git worktree remove "../Madhav-s1-3-backend-api"
  git branch -d "feature/phase-o-observatory/s1-3-backend-api"
  git push origin --delete "feature/phase-o-observatory/s1-3-backend-api"

# Close
Standard close. Report commit SHA, endpoint list, test pass count.
```

### USTAD_S1_4 — Anthropic provider adapter

```
Ustad — Execute Session USTAD_S1_4 — Anthropic Provider Adapter.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-4-anthropic on branch feature/phase-o-observatory/s1-4-anthropic.
Verify before starting:
  pwd                          # must end in Madhav-s1-4-anthropic
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-4-anthropic
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 Anthropic row in provider matrix)
3. platform/src/lib/llm/observability/observe.ts and types.ts
4. platform/src/lib/llm/providers/anthropic*.ts (existing Anthropic client — read fully)
5. Anthropic Messages API docs for usage block schema (input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens)

# Session-open handshake
Cowork thread: ustad-s1-4-anthropic.

# Scope
may_touch:
  - platform/src/lib/llm/providers/anthropic_observed.ts
  - platform/src/lib/llm/providers/__tests__/anthropic_observed.test.ts
must_not_touch:
  - All other provider files
  - observability/** files (frozen after S1.2)
  - Schema/migration files

# Dependencies
S1.2 closed and merged. (S1.1 transitively required.)

# Deliverable
Create an Anthropic adapter that wraps the existing Anthropic client and routes every call through the observe() shim from S1.2.

Key requirements:
- Handle non-streaming responses: extract usage.input_tokens, usage.output_tokens, usage.cache_creation_input_tokens (→ cache_write_tokens), usage.cache_read_input_tokens (→ cache_read_tokens).
- Handle streaming responses: the final message_delta event carries usage; accumulate it. Do not block streaming consumers — observation persistence runs after stream completes (use a then-chain on stream end).
- Capture provider_request_id from the response headers (request-id).
- Map errors: 400/401/403 → status=error with error_code from response body; 429 → status=error error_code=rate_limited; 5xx → status=error error_code=server_error; timeout → status=timeout.
- The adapter exposes the same API surface as the existing Anthropic client so callers swap with no code change. If today's call sites are e.g. anthropicClient.messages.create(...), the observed adapter exposes the same.

Tests:
- Mock the Anthropic SDK and verify observe() is called with correct request fields.
- Verify usage extraction for: standard message, message with cache, streaming message.
- Verify error mapping for each error class.
- Verify the adapter's API matches the underlying client (compile-time + runtime).

# Acceptance criteria
- Adapter file builds cleanly
- All tests pass
- No regression in existing Anthropic call sites (run existing Anthropic-dependent tests if any)
- SESSION_CLOSE validates

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-4-anthropic"
  git push
  git worktree remove "../Madhav-s1-4-anthropic"
  git branch -d "feature/phase-o-observatory/s1-4-anthropic"
  git push origin --delete "feature/phase-o-observatory/s1-4-anthropic"

# Close
Standard close.
```

### USTAD_S1_5 — OpenAI provider adapter

```
Ustad — Execute Session USTAD_S1_5 — OpenAI Provider Adapter.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-5-openai on branch feature/phase-o-observatory/s1-5-openai.
Verify before starting:
  pwd                          # must end in Madhav-s1-5-openai
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-5-openai
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 OpenAI row)
3. platform/src/lib/llm/observability/observe.ts
4. platform/src/lib/llm/providers/openai*.ts
5. OpenAI Chat Completions and Responses API docs for usage schema (prompt_tokens, completion_tokens, prompt_tokens_details.cached_tokens, completion_tokens_details.reasoning_tokens)

# Session-open handshake
Cowork thread: ustad-s1-5-openai.

# Scope
may_touch:
  - platform/src/lib/llm/providers/openai_observed.ts
  - platform/src/lib/llm/providers/__tests__/openai_observed.test.ts
must_not_touch: same exclusions as S1.4

# Dependencies
S1.2 closed and merged.

# Deliverable
OpenAI adapter wrapping both Chat Completions and Responses APIs.

- Extract usage: prompt_tokens → input_tokens, completion_tokens → output_tokens, prompt_tokens_details.cached_tokens → cache_read_tokens, completion_tokens_details.reasoning_tokens → reasoning_tokens. (OpenAI does not currently expose cache_write tokens.)
- Streaming: final chunk carries usage when stream_options.include_usage=true; ensure the adapter always sets this flag.
- provider_request_id from x-request-id header.
- Error mapping: 400/401/403/404 → error with error_code; 429 → rate_limited; 5xx → server_error; timeout → timeout.

Tests parallel S1.4: standard call, streaming with usage, cached tokens path, reasoning tokens path (o-series), error mapping, API surface compat.

# Acceptance criteria
Same shape as S1.4. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-5-openai"
  git push
  git worktree remove "../Madhav-s1-5-openai"
  git branch -d "feature/phase-o-observatory/s1-5-openai"
  git push origin --delete "feature/phase-o-observatory/s1-5-openai"

# Close
Standard close.
```

### USTAD_S1_6 — Gemini provider adapter

```
Ustad — Execute Session USTAD_S1_6 — Gemini Provider Adapter.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-6-gemini on branch feature/phase-o-observatory/s1-6-gemini.
Verify before starting:
  pwd                          # must end in Madhav-s1-6-gemini
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-6-gemini
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 Gemini row)
3. platform/src/lib/llm/observability/observe.ts
4. platform/src/lib/llm/providers/gemini*.ts (if exists; otherwise this is a fresh adapter)
5. Gemini API docs for usageMetadata (promptTokenCount, candidatesTokenCount, thoughtsTokenCount, cachedContentTokenCount)

# Session-open handshake
Cowork thread: ustad-s1-6-gemini.

# Scope
may_touch:
  - platform/src/lib/llm/providers/gemini_observed.ts
  - platform/src/lib/llm/providers/__tests__/gemini_observed.test.ts
must_not_touch: same exclusions

# Dependencies
S1.2 closed and merged.

# Deliverable
Gemini adapter:
- Extract: promptTokenCount → input_tokens, candidatesTokenCount → output_tokens, thoughtsTokenCount → reasoning_tokens, cachedContentTokenCount → cache_read_tokens.
- Streaming via generateContentStream — final chunk has usageMetadata.
- provider_request_id: Gemini does not return one consistently; capture x-goog-api-client + a generated client-side correlation id, persist as provider_request_id.
- Error mapping for Google API errors.

Tests parallel S1.4/S1.5.

# Acceptance criteria
Same shape. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-6-gemini"
  git push
  git worktree remove "../Madhav-s1-6-gemini"
  git branch -d "feature/phase-o-observatory/s1-6-gemini"
  git push origin --delete "feature/phase-o-observatory/s1-6-gemini"

# Close
Standard close.
```

### USTAD_S1_7 — DeepSeek provider adapter

```
Ustad — Execute Session USTAD_S1_7 — DeepSeek Provider Adapter.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-7-deepseek on branch feature/phase-o-observatory/s1-7-deepseek.
Verify before starting:
  pwd                          # must end in Madhav-s1-7-deepseek
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-7-deepseek
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 DeepSeek row)
3. platform/src/lib/llm/observability/observe.ts
4. platform/src/lib/llm/providers/deepseek*.ts (if exists)
5. DeepSeek API docs (OpenAI-compatible Chat Completions; usage extension fields prompt_cache_hit_tokens and prompt_cache_miss_tokens)

# Session-open handshake
Cowork thread: ustad-s1-7-deepseek.

# Scope
may_touch:
  - platform/src/lib/llm/providers/deepseek_observed.ts
  - platform/src/lib/llm/providers/__tests__/deepseek_observed.test.ts
must_not_touch: same exclusions

# Dependencies
S1.2 closed and merged.

# Deliverable
DeepSeek adapter (OpenAI-compatible interface):
- usage.prompt_tokens → input_tokens, usage.completion_tokens → output_tokens
- usage.prompt_cache_hit_tokens → cache_read_tokens
- usage.prompt_cache_miss_tokens → captured but does not map to a token class column (note: this is the "non-cached portion of input"; the existing input_tokens already covers total). Document the semantic clearly in the adapter file's header comment.
- DeepSeek does not expose reasoning tokens for V3; for R1 reasoning content lives in a separate field but is not separately token-counted by the API. Capture if/when API support arrives.

Tests parallel prior adapters.

# Acceptance criteria
Same shape. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-7-deepseek"
  git push
  git worktree remove "../Madhav-s1-7-deepseek"
  git branch -d "feature/phase-o-observatory/s1-7-deepseek"
  git push origin --delete "feature/phase-o-observatory/s1-7-deepseek"

# Close
Standard close.
```

### USTAD_S1_8 — NIM provider adapter

```
Ustad — Execute Session USTAD_S1_8 — NVIDIA NIM Provider Adapter.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-8-nim on branch feature/phase-o-observatory/s1-8-nim.
Verify before starting:
  pwd                          # must end in Madhav-s1-8-nim
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-8-nim
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 NIM row)
3. platform/src/lib/llm/observability/observe.ts
4. NVIDIA NIM / NGC API docs (OpenAI-compatible Chat Completions surface)

# Session-open handshake
Cowork thread: ustad-s1-8-nim.

# Scope
may_touch:
  - platform/src/lib/llm/providers/nim_observed.ts
  - platform/src/lib/llm/providers/__tests__/nim_observed.test.ts
must_not_touch: same exclusions

# Dependencies
S1.2 closed and merged.

# Deliverable
NIM adapter — OpenAI-compatible. Same extraction as S1.5 minus cache and reasoning fields (NIM endpoints typically don't expose them). Document model-by-model what NIM-hosted models you expect to use (e.g., Llama-3 70B/405B, DeepSeek hosted via NIM, Qwen variants).

Tests cover standard and streaming.

# Acceptance criteria
Same shape. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-8-nim"
  git push
  git worktree remove "../Madhav-s1-8-nim"
  git branch -d "feature/phase-o-observatory/s1-8-nim"
  git push origin --delete "feature/phase-o-observatory/s1-8-nim"

# Close
Standard close.
```

### USTAD_S1_9 — Frontend scaffold

```
Ustad — Execute Session USTAD_S1_9 — Observatory Frontend Scaffold.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-9-frontend-scaffold on branch feature/phase-o-observatory/s1-9-frontend-scaffold.
Verify before starting:
  pwd                          # must end in Madhav-s1-9-frontend-scaffold
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-9-frontend-scaffold
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 dashboard UX)
3. platform/src/app/(super-admin)/ (existing super-admin routes — match patterns for auth, layout, navigation)
4. platform/src/lib/config/feature_flags.ts (existing flag pattern from Phase 11A)
5. platform/src/app/api/admin/observatory/openapi.yaml (from S1.3)

# Session-open handshake
Cowork thread: ustad-s1-9-frontend-scaffold.

# Scope
may_touch:
  - platform/src/app/(super-admin)/observatory/layout.tsx
  - platform/src/app/(super-admin)/observatory/page.tsx (skeleton only — wiring is S1.13)
  - platform/src/app/(super-admin)/observatory/events/page.tsx (skeleton)
  - platform/src/app/(super-admin)/observatory/budgets/page.tsx (skeleton — Phase O.3 fills in)
  - platform/src/lib/components/observatory/Layout.tsx (sidebar + top bar shell)
  - platform/src/lib/components/observatory/AuthGate.tsx
  - platform/src/lib/config/feature_flags.ts (ADD MARSYS_FLAG_OBSERVATORY_ENABLED, default false)
  - platform/src/lib/api-clients/observatory.ts (typed client wrapping the openapi schema)
must_not_touch:
  - platform/src/lib/components/observatory/{kpi,filters,charts,events}/** (those are S1.10–S1.12)
  - Backend API files
  - LLM provider files

# Dependencies
S0.1 closed (for plan reference) and S1.3 closed (for OpenAPI contract). S1.3 implementation does not need to be merged for the OpenAPI file — the contract alone is enough.

# Deliverable
- Add MARSYS_FLAG_OBSERVATORY_ENABLED to feature_flags.ts (default false; env var MARSYS_FLAG_OBSERVATORY_ENABLED=true to enable). Match existing flag style.
- Create the /(super-admin)/observatory route. AuthGate component verifies the user is super-admin and the flag is enabled; otherwise renders a clear "Observatory disabled or unauthorized" message.
- Layout component: top bar with title "LLM Observatory", date range picker placeholder (real impl in S1.10), reload button, settings menu. Sidebar with sections "Overview", "Events", "Budgets", "Insights" (links to respective pages, with stubs for pages that don't exist yet).
- Skeleton pages: Overview (placeholder div), Events (placeholder), Budgets (placeholder).
- Typed API client at lib/api-clients/observatory.ts generated from or hand-written against the OpenAPI schema. All five endpoints typed.
- Tests for AuthGate (passes for super-admin + flag on; refuses otherwise).

# Acceptance criteria
- Route renders for super-admin with flag on
- Refuses for non-super-admin or flag off
- API client compiles and matches OpenAPI types
- No actual data display yet (that's S1.10–S1.12)
- SESSION_CLOSE validates

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-9-frontend-scaffold"
  git push
  git worktree remove "../Madhav-s1-9-frontend-scaffold"
  git branch -d "feature/phase-o-observatory/s1-9-frontend-scaffold"
  git push origin --delete "feature/phase-o-observatory/s1-9-frontend-scaffold"

# Close
Standard close.
```

### USTAD_S1_10 — KPI tiles + Filters bar

```
Ustad — Execute Session USTAD_S1_10 — KPI Tiles + Filters Bar.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-10-kpi-filters on branch feature/phase-o-observatory/s1-10-kpi-filters.
Verify before starting:
  pwd                          # must end in Madhav-s1-10-kpi-filters
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-10-kpi-filters
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 dashboard UX — KPI tiles and filters subsections)
3. platform/src/lib/components/observatory/Layout.tsx (from S1.9)
4. platform/src/lib/api-clients/observatory.ts (from S1.9)

# Session-open handshake
Cowork thread: ustad-s1-10-kpi-filters.

# Scope
may_touch:
  - platform/src/lib/components/observatory/kpi/**
  - platform/src/lib/components/observatory/filters/**
  - platform/src/lib/components/observatory/__tests__/{kpi,filters}/**
must_not_touch:
  - charts/**, events/** (other components)
  - layout, page wiring (S1.13 owns wiring)
  - API and backend files

# Dependencies
S1.9 closed and merged.

# Deliverable
KPI tiles row component:
- Six tiles in a row: Total cost, Requests, Total tokens (with stacked sparkline showing input/output/cache split), Avg cost / request, p50 / p95 latency (combined tile), Reconciliation variance (% with hover for last reconciled timestamp).
- Each tile shows the period value, period-over-period delta (green for cost decrease, red for increase — invert sign convention for "lower is better" metrics).
- Loading skeleton while data fetches.
- Error state with retry.
- Tile values come from /api/admin/observatory/summary; the component takes the typed response as a prop (parent fetches; the component is presentational).

Filters bar component:
- Date range picker with presets (Today, 7d, 30d, 90d, MTD, Last month, Custom). Custom opens a calendar dual-input.
- Compare-to-previous-period toggle.
- Multi-select dropdowns for Provider, Model, Pipeline stage, Status. Auto-populated from the current dataset (calls a /breakdowns endpoint to enumerate distinct values, or accepts a static list via prop for now).
- Free-text search box for conversation/prompt.
- "Clear all" button.
- Filter state is serialized to URL query params (so any view is shareable). Use a reducer pattern (filters reducer + URL sync hook).

Tests:
- KPI tile renders all states (loading, error, success, with deltas).
- Filters bar URL serialization round-trips.
- Date range presets compute correct ranges.

# Acceptance criteria
Components render in isolation (storybook stories or simple mount tests). Tests pass. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-10-kpi-filters"
  git push
  git worktree remove "../Madhav-s1-10-kpi-filters"
  git branch -d "feature/phase-o-observatory/s1-10-kpi-filters"
  git push origin --delete "feature/phase-o-observatory/s1-10-kpi-filters"

# Close
Standard close.
```

### USTAD_S1_11 — Charts

```
Ustad — Execute Session USTAD_S1_11 — Observatory Charts.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-11-charts on branch feature/phase-o-observatory/s1-11-charts.
Verify before starting:
  pwd                          # must end in Madhav-s1-11-charts
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-11-charts
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 charts subsection)
3. platform/src/lib/components/ (existing chart library used elsewhere — match it; if none, propose a single addition with rationale)

# Session-open handshake
Cowork thread: ustad-s1-11-charts.

# Scope
may_touch:
  - platform/src/lib/components/observatory/charts/**
  - platform/src/lib/components/observatory/__tests__/charts/**
must_not_touch: kpi/**, filters/**, events/**, layout, wiring, API

# Dependencies
S1.9 closed and merged.

# Deliverable
Four chart components, all consuming /timeseries or /breakdowns response shapes:

1. CostOverTimeByProvider — stacked area chart, x=time bucket, y=cost USD, series=provider.
2. CostOverTimeByPipelineStage — stacked area, series=pipeline_stage. This is the most insight-rich chart; make it visually prominent.
3. CostByModel — horizontal bar, sorted desc, top 15 + "Other" rollup.
4. CacheSavings — bar chart by provider showing (cost without cache − cost with cache). Computed on the client from /breakdowns response.

Each chart: loading skeleton, empty state ("No data in this range"), error state with retry, hover tooltip with formatted values, click-through to a filtered drill-down (emits an event that S1.13 wires to the events page).

Use a single charting library (recharts or chart.js — match what the project already uses; if neither, use recharts and add it as a dep with an entry in package.json deltas).

Tests:
- Each chart renders with realistic fixtures
- Empty state displays for empty data
- Tooltip formatter outputs correct strings (e.g., "$1,234.56 — Anthropic — May 2")

# Acceptance criteria
Components render in isolation. Tests pass. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-11-charts"
  git push
  git worktree remove "../Madhav-s1-11-charts"
  git branch -d "feature/phase-o-observatory/s1-11-charts"
  git push origin --delete "feature/phase-o-observatory/s1-11-charts"

# Close
Standard close.
```

### USTAD_S1_12 — Drill-down event explorer + side panel

```
Ustad — Execute Session USTAD_S1_12 — Event Explorer + Side Panel.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-12-events on branch feature/phase-o-observatory/s1-12-events.
Verify before starting:
  pwd                          # must end in Madhav-s1-12-events
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-12-events
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 drill-down subsection)
3. platform/src/lib/components/observatory/Layout.tsx
4. platform/src/lib/api-clients/observatory.ts

# Session-open handshake
Cowork thread: ustad-s1-12-events.

# Scope
may_touch:
  - platform/src/lib/components/observatory/events/**
  - platform/src/lib/components/observatory/__tests__/events/**
must_not_touch: kpi/**, filters/**, charts/**, layout, wiring, API

# Dependencies
S1.9 closed and merged.

# Deliverable
1. EventTable — virtualized table over /api/admin/observatory/events. Columns (toggleable): timestamp, conversation, prompt_id, provider, model, pipeline_stage, in_tokens, out_tokens, cache_tokens, cost, latency, status. Default columns: timestamp, conversation, provider, model, in/out, cost, latency, status. Sortable on cost, latency, timestamp. Cursor pagination — "Load more" button. Selecting a row opens the side panel.

2. EventSidePanel — three tabs:
   - Prompt: full prompt_text, system_prompt, parameters (formatted JSON tree).
   - Response: full response_text, finish reason, status.
   - Raw: provider_request_id, raw provider payload (if available; otherwise show "raw payload not captured for this event").
   Side panel also shows a "Conversation thread" mini-list at the bottom — siblings of this event in the same conversation_id, ordered by started_at, each clickable to switch context.

3. Column-visibility persistence in localStorage.

Tests: virtualization sanity check (renders only visible rows for 10k row fixture), side panel tabs switch correctly, conversation-thread mini-list resolves siblings.

# Acceptance criteria
Components render in isolation with realistic fixtures. Tests pass. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-12-events"
  git push
  git worktree remove "../Madhav-s1-12-events"
  git branch -d "feature/phase-o-observatory/s1-12-events"
  git push origin --delete "feature/phase-o-observatory/s1-12-events"

# Close
Standard close.
```

### USTAD_S1_13 — Wiring + e2e integration

```
Ustad — Execute Session USTAD_S1_13 — Observatory MVP Wiring + Smoke Test.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s1-13-wiring on branch feature/phase-o-observatory/s1-13-wiring.
Verify before starting:
  pwd                          # must end in Madhav-s1-13-wiring
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s1-13-wiring
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 full)
3. ALL of: platform/src/lib/components/observatory/{kpi,filters,charts,events}/**, platform/src/app/api/admin/observatory/**
4. Existing smoke test scripts (e.g., platform/scripts/cutover-stage1-smoke.ts referenced in CLAUDE.md Phase 11A)

# Session-open handshake
Cowork thread: ustad-s1-13-wiring.

# Scope
may_touch:
  - platform/src/app/(super-admin)/observatory/page.tsx (compose all components — Overview page)
  - platform/src/app/(super-admin)/observatory/events/page.tsx (compose EventTable + EventSidePanel)
  - platform/scripts/observatory_smoke.ts
  - platform/src/app/(super-admin)/observatory/__tests__/integration/**
must_not_touch:
  - Component internals (kpi, filters, charts, events directories)
  - API internals
  - Schema/migration files

# Dependencies
ALL of S1.1–S1.12 closed and merged.

# Deliverable
- Overview page composes: Layout > FiltersBar > KPITilesRow > [CostOverTimeByProvider, CostOverTimeByPipelineStage, CostByModel, CacheSavings] > LeaderboardCards (top conversations / top prompts / top errors — small list components inline if not yet built).
- Events page composes Layout > FiltersBar > EventTable > EventSidePanel.
- Smoke script platform/scripts/observatory_smoke.ts: starts a test server, hits all five API endpoints with a known-good fixture, verifies response shapes match OpenAPI, fails loudly on mismatch. Add npm script "observatory:smoke" that runs it.
- E2E test: log in as super-admin with flag on → load Overview → assert KPI tiles populate → apply a date range filter → assert URL updates and KPIs refresh → click into an event → assert side panel opens with full data.

# Acceptance criteria
- Both pages render end-to-end against a seeded test database
- npm run observatory:smoke passes
- E2E test passes
- Phase O.1 acceptance from OBSERVATORY_PLAN §8 satisfied
- SESSION_CLOSE validates; SESSION_LOG entry notes "Phase O.1 MVP closed"

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s1-13-wiring"
  git push
  git worktree remove "../Madhav-s1-13-wiring"
  git branch -d "feature/phase-o-observatory/s1-13-wiring"
  git push origin --delete "feature/phase-o-observatory/s1-13-wiring"

# Close
Standard close. Mark Phase O.1 complete in CURRENT_STATE_v1_0.md (this is one of the few non-S0.1 sessions allowed to update CURRENT_STATE — declare it explicitly in the session-open scope and the must_not_touch exclusion is lifted only for that file).
```

---

## Phase O.2 — Reconciliation

### USTAD_S2_1 — Reconciliation framework

```
Ustad — Execute Session USTAD_S2_1 — Reconciliation Framework.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s2-1-reconciliation-framework on branch feature/phase-o-observatory/s2-1-reconciliation-framework.
Verify before starting:
  pwd                          # must end in Madhav-s2-1-reconciliation-framework
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s2-1-reconciliation-framework
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§2 architecture, §4 reconciliation banner)
3. platform/src/lib/db/schema/observatory.ts
4. Existing cron infrastructure in the project (find it; match patterns)

# Session-open handshake
Cowork thread: ustad-s2-1-reconciliation-framework.

# Scope
may_touch:
  - platform/src/lib/observatory/reconciliation/{runner,base,types,store}.ts
  - platform/src/lib/observatory/reconciliation/__tests__/**
  - platform/scripts/cron/observatory_reconcile.ts (cron entrypoint)
must_not_touch:
  - Provider-specific reconcilers (anthropic.ts, openai.ts, gemini.ts — those are S2.2/2.3/2.4)
  - UI files

# Dependencies
Phase O.1 closed (S1.13 merged).

# Deliverable
- types.ts: BaseReconciler interface — { provider: ProviderName; pull(date: Date): Promise<ProviderCostReportRow[]>; reconcile(date: Date): Promise<ReconciliationResult> }.
- base.ts: AbstractReconciler with shared logic — fetches llm_usage_events for the date, computes computed_total per (provider, model), expects subclass to provide pull(), then writes llm_provider_cost_reports rows + llm_cost_reconciliation row (status: matched if variance_pct < 1%, variance_within_tolerance if < 5%, variance_alert otherwise; missing_authoritative if pull returned empty).
- runner.ts: RunReconciliation(reconcilers: BaseReconciler[], date: Date) — orchestrator, runs all reconcilers in parallel, aggregates results, logs.
- store.ts: persistence helpers writing llm_provider_cost_reports and llm_cost_reconciliation rows transactionally.
- Cron entrypoint: platform/scripts/cron/observatory_reconcile.ts runs nightly at 03:00 local for the prior day's date. Configurable via env (RECONCILIATION_HOUR, RECONCILIATION_TZ). Idempotent — re-running for the same date deletes existing reconciliation rows for that (date, provider) and re-writes.

Tests:
- AbstractReconciler with a mock pull() correctly computes variance and persists.
- Tolerance band classification (matched / within / alert) tested at boundaries.
- Idempotency on re-run.

# Acceptance criteria
- Framework testable with mock providers
- Runner can be invoked manually via npm script "observatory:reconcile -- --date=YYYY-MM-DD"
- SESSION_CLOSE validates

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s2-1-reconciliation-framework"
  git push
  git worktree remove "../Madhav-s2-1-reconciliation-framework"
  git branch -d "feature/phase-o-observatory/s2-1-reconciliation-framework"
  git push origin --delete "feature/phase-o-observatory/s2-1-reconciliation-framework"

# Close
Standard close.
```

### USTAD_S2_2 — Anthropic reconciler

```
Ustad — Execute Session USTAD_S2_2 — Anthropic Cost & Usage Reconciler.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s2-2-anthropic-reconciler on branch feature/phase-o-observatory/s2-2-anthropic-reconciler.
Verify before starting:
  pwd                          # must end in Madhav-s2-2-anthropic-reconciler
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s2-2-anthropic-reconciler
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 Anthropic row)
3. platform/src/lib/observatory/reconciliation/base.ts (from S2.1)
4. Anthropic Admin API docs: organizations/usage_report/messages and organizations/cost_report endpoints

# Session-open handshake
Cowork thread: ustad-s2-2-anthropic-reconciler.

# Scope
may_touch:
  - platform/src/lib/observatory/reconciliation/anthropic.ts
  - platform/src/lib/observatory/reconciliation/__tests__/anthropic.test.ts
  - Environment variable additions in .env.example for ANTHROPIC_ADMIN_API_KEY (do not put a real key)
must_not_touch:
  - Other reconcilers
  - Framework files (frozen after S2.1)

# Dependencies
S2.1 closed and merged.

# Deliverable
AnthropicReconciler extends AbstractReconciler. pull(date) calls:
- /v1/organizations/cost_report with date range = single day, grouped by model and workspace (if applicable).
- /v1/organizations/usage_report/messages for token corroboration.

Map response to ProviderCostReportRow[]: { provider: "anthropic", model, time_bucket_start, time_bucket_end, workspace_id, authoritative_cost_usd, authoritative_input_tokens, authoritative_output_tokens, raw_payload }.

Auth: ANTHROPIC_ADMIN_API_KEY (not the per-request inference key — the org admin key with usage_report scope).

Document the API lag (typically several hours) and recommend running reconciliation no earlier than 06:00 next-day to allow Anthropic's aggregation to settle.

Tests: mock the admin API responses and verify mapping; verify error handling (missing key, 403, rate limited, partial data).

# Acceptance criteria
- Reconciler runs end-to-end against a recorded fixture
- npm run observatory:reconcile -- --date=YYYY-MM-DD --provider=anthropic completes
- SESSION_CLOSE validates

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s2-2-anthropic-reconciler"
  git push
  git worktree remove "../Madhav-s2-2-anthropic-reconciler"
  git branch -d "feature/phase-o-observatory/s2-2-anthropic-reconciler"
  git push origin --delete "feature/phase-o-observatory/s2-2-anthropic-reconciler"

# Close
Standard close.
```

### USTAD_S2_3 — OpenAI reconciler

```
Ustad — Execute Session USTAD_S2_3 — OpenAI Costs & Usage Reconciler.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s2-3-openai-reconciler on branch feature/phase-o-observatory/s2-3-openai-reconciler.
Verify before starting:
  pwd                          # must end in Madhav-s2-3-openai-reconciler
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s2-3-openai-reconciler
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 OpenAI row)
3. platform/src/lib/observatory/reconciliation/base.ts
4. OpenAI Admin API docs: /v1/organization/usage/* and /v1/organization/costs

# Session-open handshake
Cowork thread: ustad-s2-3-openai-reconciler.

# Scope
may_touch:
  - platform/src/lib/observatory/reconciliation/openai.ts
  - platform/src/lib/observatory/reconciliation/__tests__/openai.test.ts
  - .env.example for OPENAI_ADMIN_API_KEY
must_not_touch: same as S2.2

# Dependencies
S2.1 closed.

# Deliverable
OpenAIReconciler. pull(date) calls /v1/organization/costs (bucketed daily, grouped by line_item which corresponds to model). Token corroboration via /v1/organization/usage/completions. Map to ProviderCostReportRow[].

Auth: OPENAI_ADMIN_API_KEY (org admin scope).

Tests as for S2.2.

# Acceptance criteria
Same shape. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s2-3-openai-reconciler"
  git push
  git worktree remove "../Madhav-s2-3-openai-reconciler"
  git branch -d "feature/phase-o-observatory/s2-3-openai-reconciler"
  git push origin --delete "feature/phase-o-observatory/s2-3-openai-reconciler"

# Close
Standard close.
```

### USTAD_S2_4 — Gemini Cloud Billing reconciler

```
Ustad — Execute Session USTAD_S2_4 — Gemini / Vertex AI Cloud Billing Reconciler.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s2-4-gemini-reconciler on branch feature/phase-o-observatory/s2-4-gemini-reconciler.
Verify before starting:
  pwd                          # must end in Madhav-s2-4-gemini-reconciler
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s2-4-gemini-reconciler
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 Gemini row)
3. Google Cloud Billing BigQuery export schema docs (services.id, sku.description, cost, usage.amount)

# Session-open handshake
Cowork thread: ustad-s2-4-gemini-reconciler.

# Scope
may_touch:
  - platform/src/lib/observatory/reconciliation/gemini.ts
  - platform/src/lib/observatory/reconciliation/__tests__/gemini.test.ts
  - .env.example for GCP_BILLING_PROJECT_ID, GCP_BILLING_DATASET, GCP_SERVICE_ACCOUNT_JSON path
must_not_touch: same

# Dependencies
S2.1 closed. User must have configured Cloud Billing BigQuery export — document this prerequisite at the top of the file.

# Deliverable
GeminiReconciler. pull(date) runs a parameterized BigQuery SQL query against the billing export dataset, filtering for service.description LIKE 'Vertex AI%' or service.id matching Vertex AI/Generative Language SKUs, grouped by sku/model, for the given date. Use @google-cloud/bigquery client. Auth via service account JSON.

Note the 24–48h lag and recommend running with --date=today-2 by default. Document this in the file header and surface in the OBSERVATORY_PLAN matrix entry as needed (do NOT modify the plan in this session — surface as a note in chat output for the next governance session).

Tests: mock bigquery client; verify SQL query construction and result mapping.

# Acceptance criteria
Same shape. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s2-4-gemini-reconciler"
  git push
  git worktree remove "../Madhav-s2-4-gemini-reconciler"
  git branch -d "feature/phase-o-observatory/s2-4-gemini-reconciler"
  git push origin --delete "feature/phase-o-observatory/s2-4-gemini-reconciler"

# Close
Standard close.
```

### USTAD_S2_5 — DeepSeek + NIM manual-reconciliation UI

```
Ustad — Execute Session USTAD_S2_5 — Manual Reconciliation Upload UI (DeepSeek + NIM).

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s2-5-manual-reconciliation on branch feature/phase-o-observatory/s2-5-manual-reconciliation.
Verify before starting:
  pwd                          # must end in Madhav-s2-5-manual-reconciliation
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s2-5-manual-reconciliation
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 DeepSeek + NIM rows)
3. platform/src/lib/components/observatory/Layout.tsx
4. platform/src/app/api/admin/observatory/openapi.yaml

# Session-open handshake
Cowork thread: ustad-s2-5-manual-reconciliation.

# Scope
may_touch:
  - platform/src/lib/components/observatory/manual_reconciliation/**
  - platform/src/app/api/admin/observatory/manual_reconciliation/route.ts (POST endpoint)
  - platform/src/app/(super-admin)/observatory/reconciliation/page.tsx
  - platform/src/lib/observatory/reconciliation/manual.ts
must_not_touch:
  - Auto-reconciler files
  - Framework

# Dependencies
S2.1 closed.

# Deliverable
- UI page /(super-admin)/observatory/reconciliation lets the admin upload a CSV with columns: provider, model, date, cost_usd, input_tokens?, output_tokens?, source_url?. Validates schema, shows a preview with row count, total cost, date range, then "Confirm upload".
- POST /api/admin/observatory/manual_reconciliation accepts the CSV (multipart/form-data), validates, and writes llm_provider_cost_reports + llm_cost_reconciliation rows for each (date, provider, model) row.
- Reconciliation page also lists past manual uploads with timestamps and uploader user_id.

Tests: CSV parser handles malformed rows gracefully; idempotent re-upload (warns on duplicate (date, provider, model)); auth gate refuses non-super-admin.

# Acceptance criteria
End-to-end CSV upload writes rows correctly. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s2-5-manual-reconciliation"
  git push
  git worktree remove "../Madhav-s2-5-manual-reconciliation"
  git branch -d "feature/phase-o-observatory/s2-5-manual-reconciliation"
  git push origin --delete "feature/phase-o-observatory/s2-5-manual-reconciliation"

# Close
Standard close.
```

### USTAD_S2_6 — Reconciliation banner UI

```
Ustad — Execute Session USTAD_S2_6 — Reconciliation Banner.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s2-6-reconciliation-banner on branch feature/phase-o-observatory/s2-6-reconciliation-banner.
Verify before starting:
  pwd                          # must end in Madhav-s2-6-reconciliation-banner
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s2-6-reconciliation-banner
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 reconciliation banner)
3. platform/src/lib/components/observatory/ (existing layout)

# Session-open handshake
Cowork thread: ustad-s2-6-reconciliation-banner.

# Scope
may_touch:
  - platform/src/lib/components/observatory/reconciliation_banner/**
  - platform/src/app/(super-admin)/observatory/page.tsx (insert banner above KPI row — narrow scope edit)
  - platform/src/app/api/admin/observatory/reconciliation_status/route.ts (GET endpoint)
must_not_touch:
  - All other components and APIs

# Dependencies
S2.1 closed and at least one of S2.2/S2.3/S2.4/S2.5 closed.

# Deliverable
- GET /reconciliation_status returns: { reconciled_through: { [provider]: ISO date }, latest_variance: { [provider]: { variance_pct, variance_usd, status } }, manual_reconciliation_required: ProviderName[] }.
- Banner component: green check + "All providers reconciled through {date}" if all matched/within tolerance; yellow warning + "Variance alert: {providers}" if any variance_alert; gray + "Pending reconciliation for {date}" if missing_authoritative.
- Hover state shows per-provider detail.

# Acceptance criteria
Banner renders all states. SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s2-6-reconciliation-banner"
  git push
  git worktree remove "../Madhav-s2-6-reconciliation-banner"
  git branch -d "feature/phase-o-observatory/s2-6-reconciliation-banner"
  git push origin --delete "feature/phase-o-observatory/s2-6-reconciliation-banner"

# Close
Standard close. Mark Phase O.2 complete in CURRENT_STATE_v1_0.md (allowed exception, declare in scope at session open).
```

---

## Phase O.3 — Budgets, Alerts, Exports

### USTAD_S3_1 — Budget rules schema + API

```
Ustad — Execute Session USTAD_S3_1 — Budget Rules Schema + API.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s3-1-budgets-schema-api on branch feature/phase-o-observatory/s3-1-budgets-schema-api.
Verify before starting:
  pwd                          # must end in Madhav-s3-1-budgets-schema-api
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s3-1-budgets-schema-api
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 budgets)
3. platform/src/lib/db/schema/observatory.ts (llm_budget_rules table from S1.1)

# Session-open handshake
Cowork thread: ustad-s3-1-budgets-schema-api.

# Scope
may_touch:
  - platform/db/migrations/*budget_alerts* (new migration: llm_alerts table — alert events fired)
  - platform/src/lib/db/schema/observatory.ts (extend exports for new table)
  - platform/src/app/api/admin/observatory/budgets/**
  - platform/src/lib/observatory/budgets/**
must_not_touch:
  - Alert evaluator (S3.2)
  - UI (S3.3)
  - Export (S3.4)

# Dependencies
Phase O.2 closed.

# Deliverable
- Migration for llm_alerts table: alert_id (uuid pk), budget_rule_id (fk), fired_at, period_start, period_end, threshold_pct, actual_pct, actual_amount_usd, scope_summary (string), delivered_channels (jsonb), status (enum: fired|acknowledged|resolved). Index on (budget_rule_id, fired_at desc).
- CRUD API: POST/GET/PATCH/DELETE /api/admin/observatory/budgets.
- GET /api/admin/observatory/budgets/:id/status returns current period spend vs amount, percent consumed, projected end-of-period spend.
- GET /api/admin/observatory/alerts returns recent alerts with filtering by date range and status.

Tests: CRUD round-trips, status computation correctness across (total / provider / model / pipeline_stage) scopes.

# Acceptance criteria
SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s3-1-budgets-schema-api"
  git push
  git worktree remove "../Madhav-s3-1-budgets-schema-api"
  git branch -d "feature/phase-o-observatory/s3-1-budgets-schema-api"
  git push origin --delete "feature/phase-o-observatory/s3-1-budgets-schema-api"

# Close
Standard close.
```

### USTAD_S3_2 — Alert evaluator

```
Ustad — Execute Session USTAD_S3_2 — Budget Alert Evaluator.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s3-2-alert-evaluator on branch feature/phase-o-observatory/s3-2-alert-evaluator.
Verify before starting:
  pwd                          # must end in Madhav-s3-2-alert-evaluator
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s3-2-alert-evaluator
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 budgets)
3. platform/src/lib/observatory/budgets/ (from S3.1)
4. Existing email/webhook delivery code in the project

# Session-open handshake
Cowork thread: ustad-s3-2-alert-evaluator.

# Scope
may_touch:
  - platform/src/lib/observatory/alerts/**
  - platform/scripts/cron/observatory_alert_evaluator.ts
must_not_touch:
  - Budget CRUD/UI/Schema
  - Other observatory subsystems

# Dependencies
S3.1 closed.

# Deliverable
- Cron job runs every 15 minutes. For each active budget rule, computes current period spend, checks each alert_threshold (e.g., 50%, 80%, 100%), fires alert if threshold crossed and not already fired in this period (dedup against llm_alerts).
- Delivery channels: email (SES or existing email infra), Slack webhook (per-rule webhook URL), generic webhook.
- Each fired alert writes a row to llm_alerts with delivered_channels.
- Idempotency: a (budget_rule_id, period, threshold_pct) tuple fires once per period.

Tests: threshold crossing detection (mock current-spend lookup), dedup across runs, channel delivery (mock transport), period rollover resets dedup state.

# Acceptance criteria
SESSION_CLOSE validates. End-to-end test fires a mock alert through mock email + Slack delivery.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s3-2-alert-evaluator"
  git push
  git worktree remove "../Madhav-s3-2-alert-evaluator"
  git branch -d "feature/phase-o-observatory/s3-2-alert-evaluator"
  git push origin --delete "feature/phase-o-observatory/s3-2-alert-evaluator"

# Close
Standard close.
```

### USTAD_S3_3 — Budgets UI

```
Ustad — Execute Session USTAD_S3_3 — Budgets UI.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s3-3-budgets-ui on branch feature/phase-o-observatory/s3-3-budgets-ui.
Verify before starting:
  pwd                          # must end in Madhav-s3-3-budgets-ui
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s3-3-budgets-ui
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 budgets)
3. platform/src/app/(super-admin)/observatory/budgets/page.tsx (skeleton from S1.9)

# Session-open handshake
Cowork thread: ustad-s3-3-budgets-ui.

# Scope
may_touch:
  - platform/src/lib/components/observatory/budgets/**
  - platform/src/app/(super-admin)/observatory/budgets/page.tsx (full implementation)
must_not_touch:
  - Backend, schema, alert evaluator

# Dependencies
S3.1 closed.

# Deliverable
- Budget list view: shows all rules with name, scope, period, amount, current consumption (progress bar), status (under/at/over budget).
- Rule editor (modal or side panel): name, scope dropdown (total/provider/model/pipeline_stage), scope_value picker, period dropdown, amount input, alert thresholds editor (add/remove threshold rows: pct + channel + channel-specific config like webhook URL or email address).
- Alert log view: paginated table of recent alerts with filters by rule, date range, status. Click row shows alert detail.
- Validation: amount > 0, at least one threshold, threshold pcts unique within a rule.

Tests: form validation, rule create/edit/delete flows, alert log filtering.

# Acceptance criteria
SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s3-3-budgets-ui"
  git push
  git worktree remove "../Madhav-s3-3-budgets-ui"
  git branch -d "feature/phase-o-observatory/s3-3-budgets-ui"
  git push origin --delete "feature/phase-o-observatory/s3-3-budgets-ui"

# Close
Standard close.
```

### USTAD_S3_4 — Export endpoints + UI

```
Ustad — Execute Session USTAD_S3_4 — CSV/JSON Export.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s3-4-export on branch feature/phase-o-observatory/s3-4-export.
Verify before starting:
  pwd                          # must end in Madhav-s3-4-export
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s3-4-export
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§4 exports)
3. platform/src/app/api/admin/observatory/ (existing endpoints)

# Session-open handshake
Cowork thread: ustad-s3-4-export.

# Scope
may_touch:
  - platform/src/app/api/admin/observatory/export/**
  - platform/src/lib/components/observatory/export/**
  - platform/src/lib/components/observatory/{filters,events}/**: only insertion of an "Export" button into existing toolbars; do not modify other internals.
must_not_touch:
  - All other observatory files

# Dependencies
Phase O.1 closed (events API exists).

# Deliverable
- GET /api/admin/observatory/export/events?format=csv|json&[same filters as /events] streams a download. Streams (no full materialization in memory) for large ranges.
- GET /api/admin/observatory/export/summary?format=csv|json returns the summary numbers.
- Export button in FiltersBar (currently filtering scope). Dropdown: CSV / JSON. Triggers download via signed short-lived URL or direct streamed response.

Tests: streaming behavior with large fixtures (10k rows); CSV escaping correctness; JSON shape matches OpenAPI.

# Acceptance criteria
SESSION_CLOSE validates. Mark Phase O.3 complete in CURRENT_STATE_v1_0.md.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s3-4-export"
  git push
  git worktree remove "../Madhav-s3-4-export"
  git branch -d "feature/phase-o-observatory/s3-4-export"
  git push origin --delete "feature/phase-o-observatory/s3-4-export"

# Close
Standard close.
```

---

## Phase O.4 — Insights

### USTAD_S4_1 — Cache effectiveness

```
Ustad — Execute Session USTAD_S4_1 — Cache Effectiveness Analytics.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s4-1-cache-effectiveness on branch feature/phase-o-observatory/s4-1-cache-effectiveness.
Verify before starting:
  pwd                          # must end in Madhav-s4-1-cache-effectiveness
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s4-1-cache-effectiveness
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§5 insights — cache effectiveness)
3. platform/src/lib/db/schema/observatory.ts
4. platform/src/lib/components/observatory/{kpi,charts}/**

# Session-open handshake
Cowork thread: ustad-s4-1-cache-effectiveness.

# Scope
may_touch:
  - platform/src/lib/observatory/insights/cache.ts
  - platform/src/app/api/admin/observatory/insights/cache/route.ts
  - platform/src/lib/components/observatory/insights/CacheEffectiveness.tsx
  - platform/src/app/(super-admin)/observatory/insights/page.tsx (NEW page or extend existing if any)
must_not_touch:
  - Phase O.1/O.2/O.3 files

# Dependencies
Phase O.1 closed.

# Deliverable
- Backend: GET /api/admin/observatory/insights/cache?from=&to= returns: per-provider cache hit rate (cache_read_tokens / (input_tokens + cache_read_tokens)), dollars saved (computed as cache_read_tokens × difference between cached and uncached price), top 10 candidate prompts by uncached input_tokens that share a prefix (heuristic: group by first 200 chars hash of prompt_text, count occurrences; recommend caching for groups with ≥5 occurrences).
- Frontend: card with 3 metrics (hit rate, dollars saved, top recommendations table).

Tests: dollar-saved math correctness; recommendation grouping correctness on a fixture.

# Acceptance criteria
SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s4-1-cache-effectiveness"
  git push
  git worktree remove "../Madhav-s4-1-cache-effectiveness"
  git branch -d "feature/phase-o-observatory/s4-1-cache-effectiveness"
  git push origin --delete "feature/phase-o-observatory/s4-1-cache-effectiveness"

# Close
Standard close.
```

### USTAD_S4_2 — Cost per quality

```
Ustad — Execute Session USTAD_S4_2 — Cost-per-Quality Analytics.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s4-2-cost-per-quality on branch feature/phase-o-observatory/s4-2-cost-per-quality.
Verify before starting:
  pwd                          # must end in Madhav-s4-2-cost-per-quality
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s4-2-cost-per-quality
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§5 insights — cost-per-quality)
3. Existing audit-stage code that emits quality scores. If no quality score is currently captured, this session must first surface that as a blocker and propose a minimal capture path (extend llm_usage_events with a quality_score nullable column via a small migration). Decide in-session and proceed.

# Session-open handshake
Cowork thread: ustad-s4-2-cost-per-quality.

# Scope
may_touch:
  - platform/src/lib/observatory/insights/quality.ts
  - platform/src/app/api/admin/observatory/insights/quality/route.ts
  - platform/src/lib/components/observatory/insights/CostPerQuality.tsx
  - If quality_score column is added: platform/db/migrations/*quality_score*, platform/src/lib/db/schema/observatory.ts (single-column extension)
must_not_touch: most other files

# Dependencies
Phase O.1 closed.

# Deliverable
- Backend computes cost / quality_score per (provider, model, pipeline_stage). Excludes events with null quality_score.
- Frontend: scatter plot of model spend vs avg quality, with model labels; sortable table of (provider, model, avg quality, total cost, cost per accepted output where accepted = quality_score ≥ threshold).

# Acceptance criteria
SESSION_CLOSE validates. If schema change was made, drift_detector.py exits 0 after.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s4-2-cost-per-quality"
  git push
  git worktree remove "../Madhav-s4-2-cost-per-quality"
  git branch -d "feature/phase-o-observatory/s4-2-cost-per-quality"
  git push origin --delete "feature/phase-o-observatory/s4-2-cost-per-quality"

# Close
Standard close.
```

### USTAD_S4_3 — Conversation cost arc

```
Ustad — Execute Session USTAD_S4_3 — Per-Conversation Cost Arc.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s4-3-cost-arc on branch feature/phase-o-observatory/s4-3-cost-arc.
Verify before starting:
  pwd                          # must end in Madhav-s4-3-cost-arc
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s4-3-cost-arc
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§5 insights — conversation cost arc)
3. platform/src/lib/components/observatory/events/**

# Session-open handshake
Cowork thread: ustad-s4-3-cost-arc.

# Scope
may_touch:
  - platform/src/app/api/admin/observatory/conversation/[id]/timeline/route.ts
  - platform/src/lib/components/observatory/insights/ConversationCostArc.tsx
  - Insertion point in EventSidePanel (a single function call addition, not internal restructure)
must_not_touch: most others

# Dependencies
Phase O.1 closed.

# Deliverable
- Backend: GET /api/admin/observatory/conversation/[id]/timeline returns ordered list of events with cumulative_cost field added, plus stage-by-stage breakdown.
- Frontend: ConversationCostArc shows a horizontal stacked bar timeline — each event a segment colored by pipeline_stage, width proportional to cost. Hover shows per-event detail. Cumulative cost line above the bars.
- Wire the chart into EventSidePanel as a fourth tab "Conversation arc" (the panel currently has Prompt/Response/Raw — add this as a fourth, not replacing).

# Acceptance criteria
SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s4-3-cost-arc"
  git push
  git worktree remove "../Madhav-s4-3-cost-arc"
  git branch -d "feature/phase-o-observatory/s4-3-cost-arc"
  git push origin --delete "feature/phase-o-observatory/s4-3-cost-arc"

# Close
Standard close.
```

### USTAD_S4_4 — Pricing diff alerter

```
Ustad — Execute Session USTAD_S4_4 — Pricing Diff Alerter.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s4-4-pricing-diff on branch feature/phase-o-observatory/s4-4-pricing-diff.
Verify before starting:
  pwd                          # must end in Madhav-s4-4-pricing-diff
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s4-4-pricing-diff
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§5 insights — pricing diff)
3. platform/src/lib/db/seed/observatory_pricing/seed_v1.ts (from S1.1)

# Session-open handshake
Cowork thread: ustad-s4-4-pricing-diff.

# Scope
may_touch:
  - platform/src/lib/observatory/pricing_diff/**
  - platform/scripts/cron/observatory_pricing_diff.ts
  - platform/src/lib/components/observatory/insights/PricingDiff.tsx
must_not_touch: most others

# Dependencies
Phase O.1 closed.

# Deliverable
- Cron job (weekly): for each (provider, model) tuple, fetches the provider's published pricing page (Anthropic /pricing, OpenAI /api/pricing, etc.), extracts current rates with a per-provider parser, diffs against current llm_pricing_versions row.
- On detected change: writes a new pricing_versions row with effective_from = today, effective_to of the prior row set to today; writes a pricing_change_event into a new lightweight llm_pricing_changes table (or as an llm_alert with a "pricing_change" type — propose and decide in-session, document choice).
- Frontend: PricingDiff card in insights page lists recent pricing changes with delta and projected monthly cost impact (computed from last-30-day usage at new vs old rates).

Tests: parser correctness against recorded HTML fixtures; diff detection correctness; impact projection math.

# Acceptance criteria
SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s4-4-pricing-diff"
  git push
  git worktree remove "../Madhav-s4-4-pricing-diff"
  git branch -d "feature/phase-o-observatory/s4-4-pricing-diff"
  git push origin --delete "feature/phase-o-observatory/s4-4-pricing-diff"

# Close
Standard close.
```

### USTAD_S4_5 — Replay & re-cost engine

```
Ustad — Execute Session USTAD_S4_5 — Replay & Re-cost Engine.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s4-5-replay-recost on branch feature/phase-o-observatory/s4-5-replay-recost.
Verify before starting:
  pwd                          # must end in Madhav-s4-5-replay-recost
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s4-5-replay-recost
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§5 insights — replay & re-cost)
3. platform/src/lib/observatory/cost.ts (cost computation)

# Session-open handshake
Cowork thread: ustad-s4-5-replay-recost.

# Scope
may_touch:
  - platform/src/lib/observatory/replay/**
  - platform/src/app/api/admin/observatory/replay/route.ts (POST)
  - platform/src/lib/components/observatory/insights/Replay.tsx
must_not_touch: most others

# Dependencies
Phase O.1 closed.

# Deliverable
Two modes:

Mode 1 — Re-cost (no real provider call): given a date range and a target (provider, model), computes what the period would have cost if every event had been routed to that target. Uses captured token counts as-is. Pure math; no API calls.

Mode 2 — Replay (real provider call, optional, gated): given a list of event_ids and a target (provider, model), re-issues the captured prompts to the target provider and persists new events with a "replay_of" linkage. Requires explicit confirmation in the UI ("This will issue N real API calls and incur cost ~$X"). Disabled by default behind a feature flag MARSYS_FLAG_OBSERVATORY_REPLAY_ENABLED.

Frontend: comparison table — current vs hypothetical (provider, model). Mode toggle clearly distinguishes pure math from real-call.

Tests: re-cost math; replay event linkage; gate enforcement.

# Acceptance criteria
SESSION_CLOSE validates.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s4-5-replay-recost"
  git push
  git worktree remove "../Madhav-s4-5-replay-recost"
  git branch -d "feature/phase-o-observatory/s4-5-replay-recost"
  git push origin --delete "feature/phase-o-observatory/s4-5-replay-recost"

# Close
Standard close.
```

### USTAD_S4_6 — Anomaly detection

```
Ustad — Execute Session USTAD_S4_6 — Anomaly Detection Job.

# Worktree
You are running in worktree /Users/Dev/Vibe-Coding/Apps/Madhav-s4-6-anomaly on branch feature/phase-o-observatory/s4-6-anomaly.
Verify before starting:
  pwd                          # must end in Madhav-s4-6-anomaly
  git rev-parse --show-toplevel
  git branch --show-current    # must be feature/phase-o-observatory/s4-6-anomaly
If verification fails, STOP — do not switch branches inside the worktree.
Refresh from umbrella's latest tip:
  git fetch origin
  git rebase origin/feature/phase-o-observatory

# Required reading
1. CLAUDE.md
2. 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (§5 insights — anomaly)
3. platform/src/lib/observatory/ (existing analytics)

# Session-open handshake
Cowork thread: ustad-s4-6-anomaly.

# Scope
may_touch:
  - platform/src/lib/observatory/anomaly/**
  - platform/scripts/cron/observatory_anomaly.ts
  - platform/src/lib/components/observatory/insights/Anomalies.tsx
  - platform/src/app/api/admin/observatory/insights/anomalies/route.ts
must_not_touch: most others

# Dependencies
Phase O.1 closed. Phase O.2 desirable (reconciled costs reduce false positives) but not required.

# Deliverable
Cron (hourly). For each metric — daily cost per provider, daily cost per pipeline_stage, p95 latency per provider, cache hit rate per provider — computes a 28-day rolling baseline (mean + stddev) and flags days where today's value is more than 2.5 stddev from the mean. Persists anomaly rows to a new lightweight table or to llm_alerts with type="anomaly".

Frontend Anomalies card on insights page lists this week's anomalies, severity, drill-through to the events that drove them.

Tests: baseline math, anomaly threshold detection, deduplication of repeated daily fires.

# Acceptance criteria
SESSION_CLOSE validates. Mark Phase O.4 complete in CURRENT_STATE_v1_0.md. Phase O acceptance criteria from OBSERVATORY_PLAN §8 verified end-to-end.

# Worktree teardown (run after SESSION_CLOSE validates and merge to umbrella succeeds)
Instruct the user to run from the main working directory:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/phase-o-observatory
  git pull
  git merge --no-ff "feature/phase-o-observatory/s4-6-anomaly"
  git push
  git worktree remove "../Madhav-s4-6-anomaly"
  git branch -d "feature/phase-o-observatory/s4-6-anomaly"
  git push origin --delete "feature/phase-o-observatory/s4-6-anomaly"

# Close
Standard close. This is the last Phase O session — emit a Phase O close summary in chat reporting all 30 sessions' commit SHAs.
```

---

## Quick reference — session matrix

| ID | Phase | Title | Depends on | Parallel-safe with |
|---|---|---|---|---|
| S0.1 | O.0 | Plan artifact | — | — (sequential gate) |
| S1.1 | O.1 | Schema migrations | S0.1 | S1.2, S1.9 |
| S1.2 | O.1 | LLMClient shim | S0.1 | S1.1, S1.9 |
| S1.3 | O.1 | Backend API | S1.1 | S1.4–S1.8, S1.10–S1.12 |
| S1.4 | O.1 | Anthropic adapter | S1.2 | All other O.1 except S1.13 |
| S1.5 | O.1 | OpenAI adapter | S1.2 | All other O.1 except S1.13 |
| S1.6 | O.1 | Gemini adapter | S1.2 | All other O.1 except S1.13 |
| S1.7 | O.1 | DeepSeek adapter | S1.2 | All other O.1 except S1.13 |
| S1.8 | O.1 | NIM adapter | S1.2 | All other O.1 except S1.13 |
| S1.9 | O.1 | Frontend scaffold | S0.1 + S1.3 contract | S1.1, S1.2 |
| S1.10 | O.1 | KPI tiles + filters | S1.9 | S1.11, S1.12 |
| S1.11 | O.1 | Charts | S1.9 | S1.10, S1.12 |
| S1.12 | O.1 | Event explorer | S1.9 | S1.10, S1.11 |
| S1.13 | O.1 | Wiring + smoke | All S1.x | — (final gate) |
| S2.1 | O.2 | Reconciliation framework | O.1 close | — |
| S2.2 | O.2 | Anthropic reconciler | S2.1 | S2.3, S2.4, S2.5, S2.6 |
| S2.3 | O.2 | OpenAI reconciler | S2.1 | S2.2, S2.4, S2.5, S2.6 |
| S2.4 | O.2 | Gemini reconciler | S2.1 | S2.2, S2.3, S2.5, S2.6 |
| S2.5 | O.2 | Manual reconciliation UI | S2.1 | S2.2, S2.3, S2.4, S2.6 |
| S2.6 | O.2 | Reconciliation banner | S2.1 + any one of S2.2–S2.5 | S2.2–S2.5 |
| S3.1 | O.3 | Budget schema + API | O.2 close | S3.4 |
| S3.2 | O.3 | Alert evaluator | S3.1 | S3.3 |
| S3.3 | O.3 | Budgets UI | S3.1 | S3.2 |
| S3.4 | O.3 | Export | O.1 close | S3.1 (technically) |
| S4.1 | O.4 | Cache effectiveness | O.1 close | All other O.4 |
| S4.2 | O.4 | Cost-per-quality | O.1 close | All other O.4 |
| S4.3 | O.4 | Conversation cost arc | O.1 close | All other O.4 |
| S4.4 | O.4 | Pricing diff alerter | O.1 close | All other O.4 |
| S4.5 | O.4 | Replay & re-cost | O.1 close | All other O.4 |
| S4.6 | O.4 | Anomaly detection | O.1 close | All other O.4 |

End of file.
