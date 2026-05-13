---
artifact: CONTROL_PANEL_FEATURE_PROPOSAL_v0_1.md
canonical_id: CONTROL_PANEL_FEATURE_PROPOSAL
version: 0.1
status: SUPERSEDED
superseded_by: 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
superseded_at: 2026-05-13
superseded_reason: >
  Native reshaped scope significantly during the same brainstorm session:
  (a) renamed to AIOps; (b) dropped MVP framing — full-blown feature;
  (c) added MARSYS stack (6th, cross-provider); (d) added live catalog
  discovery from provider portals with per-call-type spec filtering;
  (e) eval/smoke/checkpoint allow cross-stack picks; (f) folded into a
  single autonomous-execution feature branch (Claude Code with bypass
  flags) rather than a parallel governance workstream;
  (g) Phase 2 + Phase 3 visibility added (adapter layer + /consume overhaul).
  All of the above is captured in AIOPS_MASTER_PLAN_v1_0.md and the
  six phase briefs under 00_ARCHITECTURE/aiops/phase_briefs/.
authored_at: 2026-05-13
authored_by: Cowork brainstorm session (Opus 4.7)
predecessor: none (new feature)
related:
  - OBSERVATORY_PLAN_v1_0.md (sealed v2.0.0 — sibling, not superseded)
  - platform/src/lib/models/registry.ts (existing STACK_ROUTING — primary integration anchor)
changelog:
  - v0.1 (2026-05-13): initial proposal authored from brainstorm
  - v0.1-SUPERSEDED (2026-05-13): scope expanded; superseded by AIOPS_MASTER_PLAN_v1_0
---

# LLM Operations Center — Control Panel Feature Proposal v0.1

## §0 — TL;DR

The user-facing feature is "configure which LLM models run each part of the pipeline, test them, override their params, and view the result alongside the existing cost/usage Observatory." The *bones* are already in the codebase: `platform/src/lib/models/registry.ts` declares five stacks (`nim | anthropic | gemini | gpt | deepseek`), five call types (`synthesis | planner_deep | planner_fast | context_assembly | worker`), and a full `STACK_ROUTING` table with primary + fallback per (stack, call_type). What's missing is (a) the **runtime mutability layer** (DB-backed overrides on top of the static table), (b) the **UI** (a sibling tab to the Observatory), (c) a **model-test probe**, (d) first-class treatment of **eval / smoke / checkpoint** as call types, and (e) per-(stack, call_type) **override of `max_tokens`, `temperature`, `thinkingBudget`**.

Total work: ~3 to 5 phased sub-sessions on a single feature branch. No core architecture change; the registry remains the source of truth for which models *exist* and what they cost — the new system layers *runtime selection* over it.

---

## §1 — Naming proposal

The current "Observatory" name is too narrow once the area also houses configuration. Five candidates, ranked by my read of fit:

| Rank | Name | Why | Why-not |
|---|---|---|---|
| 1 | **LLM Operations Center** | Plain, accurate, two tabs read naturally ("Control Panel" + "Observatory") | Slightly corporate |
| 2 | **Mission Control** | Evocative, vehicle metaphor — pilot configures + monitors | Less precise about what it controls |
| 3 | **Stack Console** | Matches the existing `ModelStack` taxonomy in the code | Loses the "monitoring" half |
| 4 | **LLM Studio** | Friendly, design-tool feel | Implies authoring/creation, not config |
| 5 | **Engine Room** | Backstage-of-the-pipeline metaphor | Cute but vague |

**My pick: "LLM Operations Center"** with two tabs:

- **Control Panel** — stack + model + param configuration (new in this feature)
- **Observatory** — usage, cost, anomalies, reconciliation (existing — unchanged)

A third tab is plausible later: **Predictions Ledger** (for the prospective prediction log per `MACRO_PLAN §Cross-cutting workstreams`). Not in scope here, but the IA should anticipate it.

Routing implication: today the route is `/observatory` under the `(super-admin)` group. The shortest non-breaking move is to keep `/observatory` as the analytics URL (no link rot) and add `/control-panel` as a sibling, with both wrapped by a new tab container at `/llm-ops` (or whatever the native picks). The "Operations Center" landing page can default-redirect to `/observatory` so existing bookmarks continue to work.

Final name and URL slug are open decisions — see §13.

---

## §2 — What already exists (ground truth)

Read on the project at the time of writing; cited so the plan doesn't drift into fantasy.

**`platform/src/lib/models/registry.ts`** is the single source of truth and already implements most of the data model the user described:

- `ModelStack = 'nim' | 'anthropic' | 'gemini' | 'gpt' | 'deepseek'` — the user's "stacks" exactly
- `CallType = 'synthesis' | 'planner_deep' | 'planner_fast' | 'context_assembly' | 'worker'` — five pipeline call types
- `STACK_ROUTING: Record<ModelStack, Record<CallType, { primary: string; fallback: string }>>` — the user's "synthesize + synthesize backup, planner + planner backup" structure, generalized to every call type
- `MODELS` array with per-model `maxOutputTokens`, `costPer1MInput/Output`, `capabilities`, `reasoningMode`, `role`
- `DEFAULT_STACK_ID = 'gemini'` (switched from `'nim'` 2026-05-10 when NIM Nemotron endpoint degraded)
- `getStackModel(stack, callType)`, `getPrimaryModel(...)`, `getFallbackModel(...)` — runtime accessors
- `stackPicker()` — UI-ready array for a selector component

**`platform/src/lib/models/resolver.ts`** maps a model ID to an AI-SDK `LanguageModel` and applies provider-specific options:

- `deepseekProviderOptions(modelId, mode)` — thinking on/off
- `googleProviderOptions(modelId)` — safety filters disabled (required for Jyotish content); `thinkingConfig.thinkingBudget = 32_768`

**Provider observability wrappers** at `platform/src/lib/llm/providers/{nim,deepseek,gemini,anthropic,openai}_observed.ts` — every LLM call already flows through observability (this is what feeds the Observatory). The control panel inherits this for free.

**Observatory UI**: lives at `platform/src/app/(super-admin)/observatory/page.tsx` with auth via `_guard.ts` + `AuthGate.tsx`. Component library at `platform/src/lib/components/observatory/` includes `FiltersBar`, `KpiTilesRow`, `EventSidePanel`, `StackBreakdownCards`, charting helpers, etc. Dark theme, branded post-redesign (OBS-UX-S1/S2/S3/S4 closed 2026-05-06).

**Pricing seed**: `platform/src/lib/db/seed/observatory_pricing/seed_v1.ts` — model pricing rows seeded into DB; the Observatory joins audit events to pricing by `model_name` (with the `'google'→'gemini'` normalization fix from 2026-05-08).

**Smoke test script**: `platform/scripts/observatory/smoke_test.ts` already exists for the Observatory's reconciliation flow — the *concept* of a probe is established; this feature generalizes it.

**Constraint memory**: per the user's standing rule, **Anthropic stack is banned by default** (cost). Default = Gemini, fallback = DeepSeek. The Control Panel must respect this — Anthropic stack should be selectable but guarded behind an "Are you sure? This costs money" confirmation.

---

## §3 — Functional scope

The Control Panel exposes the following surfaces. Each is a discrete piece of work; together they are the feature.

### §3.1 — Stack picker (global default)

A top-of-page selector that sets the *default* stack the app uses for every new conversation. Five buttons (NIM / Gemini / DeepSeek / GPT / Anthropic), each rendered as a card showing: stack label, synthesis model, synthesis context window, estimated cost per query (computed from current params × pricing seed). The active default is highlighted; an inline confirmation modal fires when the user switches to a paid stack.

**Backend behavior:** this writes to a new `llm_stack_config` DB row (one row per `scope`; for v1 the only scope is `global`). The runtime path that today reads `DEFAULT_STACK_ID` from the registry will read this row instead (registry remains the fallback if the DB row is missing).

### §3.2 — Per-call-type model selection (primary + backup)

For the active stack, render five rows (one per `CallType`), each showing two dropdowns: **Primary** and **Backup**. Dropdowns are populated by filtering `MODELS` to the active stack's provider (or to any provider, depending on §13 Q3 decision — see §3.2.a). When the user changes a dropdown, the override is saved to `llm_stack_routing_override` (keyed by `(scope, stack, call_type)`).

The runtime accessors (`getPrimaryModel`, `getFallbackModel`) gain a thin wrapper that first checks the override table, then falls back to the static `STACK_ROUTING`.

**§3.2.a — Cross-stack mixing question.** The user described stacks as cohesive bundles ("when NIM is selected, the synthesis model is one of three NIM-suitable models"). The cleanest implementation pins each call type's models to the active stack's provider. But it's possible the user wants to mix — e.g., use NIM's Nemotron for synthesis but Gemini Flash Lite for the worker. This is a real decision; flagged in §13.

### §3.3 — Param overrides (max_tokens, temperature, thinkingBudget)

For each call type, an "Advanced" disclosure exposes per-call-type override fields:

- `max_output_tokens` (default = `MODELS[id].maxOutputTokens`)
- `temperature` (default = strategy-defined; see `single_model_strategy.ts`)
- `thinkingBudget` (Gemini + DeepSeek only; default per provider options)
- `top_p` / `top_k` (optional, advanced) — open question per §13
- `timeout_ms` — useful for catching slow models early

Each field shows: the current default, the override value (if set), and a "Reset to default" link. The override is per `(scope, stack, call_type, param_name)` row in `llm_param_override`.

### §3.4 — Test-the-model probe ("Test" button)

Next to each primary + backup dropdown is a **Test** button. Clicking it:

1. Opens an inline panel below the row.
2. Sends a small probe payload to the selected model via a new endpoint: `POST /api/admin/control-panel/probe`.
3. Streams the response back, showing: latency, tokens in/out, USD cost, finishReason, the actual text (truncated to ~300 chars).
4. Reports PASS / FAIL with a clear error message on FAIL (HTTP code, body, redacted of secrets).

The probe payload should be:
- For `synthesis` / `context_assembly`: a small Jyotish-flavored prompt that exercises the L2.5 corpus ingest pattern at miniature scale (e.g. "Given MSR signal SIG.MSR.014 ... summarize in two sentences").
- For `planner_*`: a small structured-JSON output request (the model emits `{ "step": 1, "tool": "msr_lookup" }`).
- For `worker`: a one-shot summarization request.
- For new `eval` / `smoke` / `checkpoint` types (§3.6): the standard prompt that the actual eval harness uses, at min-token size.

The probe endpoint reuses the existing observed provider wrappers, so probe calls show up in the Observatory as a distinct `pipeline_stage = 'probe'` — they're real LLM calls billed at real prices, just labeled.

### §3.5 — Stack-level "Run smoke test" button

A bigger button at the top of each stack card: **Run smoke test for this stack**. This sequentially probes every call type's primary AND fallback (10 probes for a 5-call-type stack) and renders a green/red grid. Latency tolerable since this is on-demand and admin-only.

### §3.6 — Extend `CallType` to first-class eval / smoke / checkpoint

Today, eval scripts (`platform/scripts/eval/`), smoke tests (`platform/scripts/observatory/smoke_test.ts`), and checkpoint evals (`platform/scripts/checkpoint/`) all pick their own model via env var or hardcoded constant. This feature folds them into the same configuration surface:

```ts
export type CallType =
  | 'synthesis'
  | 'planner_deep'
  | 'planner_fast'
  | 'context_assembly'
  | 'worker'
  | 'eval_judge'       // NEW — model that grades answer eval outputs
  | 'eval_generator'   // NEW — model that generates eval prompts (rare; some evals are static)
  | 'smoke_synth'      // NEW — synthesis-class smoke test
  | 'checkpoint_4_5'   // NEW — Phase 6 checkpoint 4.5 (planner mid-flight verify)
  | 'checkpoint_5_5'   // NEW — Phase 6 checkpoint 5.5 (context assembly mid-flight verify)
  | 'checkpoint_8_5'   // NEW — Phase 6 checkpoint 8.5 (synthesis post-hoc verify)
```

For each new CallType the `STACK_ROUTING` table gets corresponding entries; the eval/smoke scripts gain a thin "read model from STACK_ROUTING" line in place of their current hardcoded model name. This is a strictly additive refactor — no behavior change unless the user actively edits the override.

The Control Panel renders these in a separate **Quality & Verification** section below the main pipeline call-type rows, so the UI doesn't mix runtime calls with offline tool calls.

### §3.7 — Model health badge (live status)

Each model dropdown entry shows a health pip: green (probe within last 24h passed), yellow (probe stale), red (last probe failed), gray (never probed). Sourced from a new `llm_model_health` table keyed by `model_id`, written by the probe endpoint and a nightly cron. This gives the user the visual signal "this model is actually responding right now" without requiring them to click Test on each.

### §3.8 — "View in Observatory" deep links

Every stack card has a "See cost & usage for this stack" link that hops to `/observatory` pre-filtered to that stack. Conversely, the Observatory's `StackBreakdownCards` gain a small "Configure" pencil icon that hops back to `/control-panel?stack=<id>`. This is the bridge between the two tabs.

### §3.9 — Audit + history

Every config change is appended to `llm_config_audit` with `(timestamp, actor_user_id, before_value, after_value, scope, key)`. A "Recent changes" sidebar lists the last 20 changes; clicking one offers a one-click "Revert this change" action. This is the safety net for misconfigurations.

---

## §4 — Information architecture (UI map)

```
LLM Operations Center             /llm-ops
├── Control Panel                 /llm-ops/control       (new)
│   ├── Stack Picker               (cards: NIM, Gemini, DeepSeek, GPT, Anthropic)
│   ├── [Selected Stack]
│   │   ├── Pipeline Call Types
│   │   │   ├── synthesis            primary + backup + Test + Advanced
│   │   │   ├── planner_deep         primary + backup + Test + Advanced
│   │   │   ├── planner_fast         primary + backup + Test + Advanced
│   │   │   ├── context_assembly     primary + backup + Test + Advanced
│   │   │   └── worker               primary + backup + Test + Advanced
│   │   └── Quality & Verification
│   │       ├── eval_judge           primary + backup + Test
│   │       ├── eval_generator       primary + backup + Test
│   │       ├── smoke_synth          primary + backup + Test
│   │       └── checkpoint_4_5/5_5/8_5  primary + backup + Test
│   ├── Recent Changes (right rail; last 20)
│   └── Health Status (badges throughout)
└── Observatory                   /llm-ops/observatory   (current observatory; URL-preserved alias /observatory)
    ├── (unchanged — KPI tiles, charts, anomaly, reconciliation, etc.)
    └── New "Configure" pencil on StackBreakdownCards → deep link to Control Panel
```

The tab strip at `/llm-ops` is a thin wrapper. The two child routes do all the work. This keeps the existing `/observatory` URLs functional via redirect or alias.

---

## §5 — Pipeline integration (how runtime sees the config)

This is the make-or-break part. The Control Panel is useless if the query pipeline still reads the static `STACK_ROUTING` table.

**Today's path** (simplified — needs verification when actual integration starts):

1. User submits query at `/consume`.
2. Route handler at `/api/chat/consume/route.ts` calls the synthesis orchestrator.
3. The orchestrator calls `getPrimaryModel(stack, callType)` for each pipeline stage.
4. The stack is currently sourced from `DEFAULT_STACK_ID` or a localStorage override (per-user, not super-admin-set).

**Proposed path:**

1. Introduce `lib/models/runtime_config.ts` exposing `getEffectiveStack()` and `getEffectiveModel(stack, callType)`.
2. These functions resolve in this priority order:
   - **Per-request override** (a header / cookie / explicit prop, used for testing and the probe endpoint)
   - **User-level localStorage stack** (existing per-user override for /consume)
   - **DB-backed `llm_stack_config` global default** (the Control Panel's main lever)
   - **Static `STACK_ROUTING` registry value** (the ultimate fallback)
3. Every call site that today reads `STACK_ROUTING[stack][callType]` is migrated to call `getEffectiveModel(stack, callType)` instead. This is a small, mechanical refactor.
4. Param overrides (max_tokens, temperature, thinkingBudget) resolve identically: `getEffectiveParam(stack, callType, 'max_output_tokens')`.

**Caching.** The DB lookup is on every call site, but configs change rarely. Wrap `getEffectiveStack` and `getEffectiveModel` in a 60-second in-memory cache keyed by scope. The Control Panel emits a cache-bust event (header or pub/sub) when it writes, so changes appear within the cache TTL or instantly.

**Concurrency.** Two super-admins editing simultaneously: last-write-wins, but `llm_config_audit` shows the full sequence so nothing is lost. Acceptable for an admin-only tool.

**Feature flag.** The whole runtime override layer rolls out behind `CONTROL_PANEL_OVERRIDES_ENABLED` (default `false`). When false, the existing static-table behavior is byte-identical. We flip the flag after smoke tests confirm zero regressions.

---

## §6 — Data model

Five new tables (Postgres, via `supabase/migrations/`). Names use the existing `llm_*` prefix convention from the observability schema.

```sql
-- One row per scope. v1 has only one scope: 'global'. Future: 'per-user' rows.
CREATE TABLE llm_stack_config (
  scope            text PRIMARY KEY,             -- 'global' for v1
  active_stack     text NOT NULL,                -- 'nim' | 'gemini' | ...
  updated_at       timestamptz NOT NULL DEFAULT now(),
  updated_by       text NOT NULL                 -- user_id of the super-admin who set it
);

-- Per-(scope, stack, call_type) override of which model serves that role.
CREATE TABLE llm_stack_routing_override (
  scope            text NOT NULL,
  stack            text NOT NULL,
  call_type        text NOT NULL,
  primary_model    text NOT NULL,
  fallback_model   text NOT NULL,
  updated_at       timestamptz NOT NULL DEFAULT now(),
  updated_by       text NOT NULL,
  PRIMARY KEY (scope, stack, call_type)
);

-- Per-(scope, stack, call_type, param_name) override of a tunable param.
CREATE TABLE llm_param_override (
  scope            text NOT NULL,
  stack            text NOT NULL,
  call_type        text NOT NULL,
  param_name       text NOT NULL,   -- 'max_output_tokens' | 'temperature' | 'thinkingBudget' | 'timeout_ms'
  param_value      jsonb NOT NULL,  -- jsonb so numbers, strings, booleans all fit
  updated_at       timestamptz NOT NULL DEFAULT now(),
  updated_by       text NOT NULL,
  PRIMARY KEY (scope, stack, call_type, param_name)
);

-- Latest health probe result per model.
CREATE TABLE llm_model_health (
  model_id         text PRIMARY KEY,
  status           text NOT NULL,   -- 'pass' | 'fail' | 'stale'
  latency_ms       int,
  last_probe_at    timestamptz NOT NULL,
  last_error       text,            -- redacted error body on fail
  last_probed_by   text             -- 'manual:<user_id>' | 'cron'
);

-- Append-only audit of every config change.
CREATE TABLE llm_config_audit (
  id               bigserial PRIMARY KEY,
  occurred_at      timestamptz NOT NULL DEFAULT now(),
  actor_user_id    text NOT NULL,
  action           text NOT NULL,   -- 'set_stack' | 'set_routing' | 'set_param' | 'reset_param' | 'probe' | 'revert'
  scope            text,
  stack            text,
  call_type        text,
  param_name       text,
  before_value     jsonb,
  after_value      jsonb,
  notes            text
);
```

Migration runs additively — no existing tables touched. Rollback is a single `DROP TABLE` per new table.

---

## §7 — API surface

New endpoints under `/api/admin/control-panel/`, all super-admin-gated via the same `_guard.ts` pattern the Observatory uses.

| Method | Path | Body / Query | Purpose |
|---|---|---|---|
| `GET` | `/stack` | — | Returns active stack + full effective routing + param overrides (rendered table view) |
| `PUT` | `/stack` | `{ active_stack }` | Sets the global active stack; writes `llm_stack_config` + `llm_config_audit` row |
| `GET` | `/routing/:stack` | — | Returns the effective (override OR registry) routing for one stack |
| `PUT` | `/routing/:stack/:call_type` | `{ primary, fallback }` | Saves one routing override row |
| `DELETE` | `/routing/:stack/:call_type` | — | Removes override, reverting to registry default |
| `GET` | `/params/:stack/:call_type` | — | Effective params for one (stack, call_type) |
| `PUT` | `/params/:stack/:call_type/:param` | `{ value }` | Saves one param override |
| `DELETE` | `/params/:stack/:call_type/:param` | — | Resets that param to default |
| `POST` | `/probe` | `{ stack, call_type, role: 'primary'|'fallback' }` | Runs probe; returns `{ pass, latency_ms, tokens, cost_usd, output_preview, error? }` |
| `POST` | `/smoke/:stack` | — | Runs all probes for one stack; returns `{ results: [...], all_pass: boolean }` |
| `GET` | `/health` | `?model_id=...` (optional) | Health table (filtered if model_id given) |
| `GET` | `/audit` | `?limit=20&offset=0` | Recent config changes for the right-rail history |
| `POST` | `/audit/:id/revert` | — | One-click revert of a past change |

Every endpoint emits a `pipeline_stage='control_panel'` audit event into the existing observability pipeline so the Observatory can show "config edits" as a row type alongside queries and reconciliations.

---

## §8 — Design system reuse

The user explicitly asked that the existing portal design system be preserved. The Observatory post-redesign sets the visual language: dark theme, branded cards, KPI tiles, badge pills. The Control Panel reuses:

| Existing component | Reused as |
|---|---|
| `KpiTilesRow` | Top-of-page "Default Stack" + "Models Healthy" + "Last Change" tiles |
| `StackBreakdownCards` | Adapted as the stack picker cards (with selected-state styling) |
| `FiltersBar` | Right-rail filter on the audit log |
| `EventSidePanel` | Detail view when a probe is clicked (reuses the slide-over) |
| `VarianceBadge` / `CostTooltip` | Cost-delta annotation when switching between models |
| `EmptyObservatoryState` | Adapted for "No overrides yet — using registry defaults" empty state |
| Dark theme tokens | Inherit from current Tailwind config / CSS vars |

Net-new components (small):

- `ModelDropdown` — provider-grouped, with health pip + cost annotation
- `TestProbeInline` — collapsible result panel with streaming output
- `ParamOverrideRow` — single-row editor with default-vs-override toggle
- `RevertConfirmDialog` — confirmation modal for "Revert to this past config"

All built with the same primitives the Observatory uses (shadcn-style or local — open question per §13 Q5). The design-handoff skill can be used to spec these cleanly before any TSX is written.

**Brand discipline.** Per the brand-guidelines skill, the Operations Center inherits the existing Madhav portal palette and typography — no introduction of new colors or fonts. The dark-theme variables defined for the Observatory redesign are the reference.

---

## §9 — Acceptance criteria (per phase)

### Phase CP.0 — Naming + IA + branch
- AC.CP0.1 — Native approves name + URL slug + tab structure
- AC.CP0.2 — Branch `feature/llm-ops-control-panel` created off main
- AC.CP0.3 — Stub routes wired (empty pages render under the new shell)

### Phase CP.1 — Data layer + read-only UI
- AC.CP1.1 — Five migrations applied; all tables present and verified by query
- AC.CP1.2 — `runtime_config.ts` resolves with correct priority order (per-request → user → DB → registry) — unit-tested
- AC.CP1.3 — Control Panel renders the active stack and the full effective routing table, *read-only* (no edit yet)
- AC.CP1.4 — Feature flag `CONTROL_PANEL_OVERRIDES_ENABLED` exists, default false; with flag off the pipeline is byte-identical to today
- AC.CP1.5 — Unit tests for `runtime_config.ts` resolver priority + cache invalidation

### Phase CP.2 — Write-side + probe
- AC.CP2.1 — All `PUT`/`DELETE` endpoints implemented + tested
- AC.CP2.2 — Stack picker UI lets super-admin switch active stack; saves to DB; reflected in next query within 60s (cache TTL) or immediately (cache bust)
- AC.CP2.3 — Per-call-type routing override editor saves and round-trips correctly
- AC.CP2.4 — Param override editor handles max_tokens / temperature / thinkingBudget / timeout_ms
- AC.CP2.5 — Probe endpoint returns pass/fail/latency/tokens/cost; reuses existing observed wrappers; events show up in Observatory under `pipeline_stage='probe'`
- AC.CP2.6 — Smoke-test-stack button works end-to-end; 5 call types × 2 roles = 10 probes complete

### Phase CP.3 — CallType extension (eval / smoke / checkpoint)
- AC.CP3.1 — `CallType` taxonomy extended with the seven new types; `STACK_ROUTING` table updated for each stack
- AC.CP3.2 — Eval scripts (`answer:eval`, `planner:eval`) read their judge/generator model from `getEffectiveModel('current_stack', 'eval_judge')` instead of hardcoded constant
- AC.CP3.3 — Smoke test script reads model from `getEffectiveModel(stack, 'smoke_synth')`
- AC.CP3.4 — Phase 6 checkpoints 4.5 / 5.5 / 8.5 read their models from `getEffectiveModel(stack, 'checkpoint_X_Y')`
- AC.CP3.5 — Quality & Verification UI section added below pipeline call types

### Phase CP.4 — Health badges + audit + IA polish
- AC.CP4.1 — Health badges live on every model dropdown row, refreshed by both manual probe and a nightly cron
- AC.CP4.2 — Audit right-rail shows last 20 changes; one-click revert works and is itself audited
- AC.CP4.3 — Observatory's `StackBreakdownCards` gains a "Configure" pencil deep-link
- AC.CP4.4 — Control Panel's stack cards gain a "View usage" link to Observatory pre-filtered
- AC.CP4.5 — Empty states, loading states, error states all match Observatory's polish bar
- AC.CP4.6 — Accessibility review via the `design:accessibility-review` skill: keyboard nav, color contrast, ARIA on dropdowns

### Phase CP.5 — Cutover
- AC.CP5.1 — Native runs smoke tests on three stacks, confirms expected behavior
- AC.CP5.2 — `CONTROL_PANEL_OVERRIDES_ENABLED=true` flipped in production
- AC.CP5.3 — Monitoring confirms no regressions in Observatory cost/usage numbers for 48 hours post-flip
- AC.CP5.4 — Feature flag removal scheduled for 2 weeks after cutover (per Phase 11B pattern)

---

## §10 — Phasing recommendation

Five sub-sessions on `feature/llm-ops-control-panel`:

| Phase | Scope | Estimated tool-call budget |
|---|---|---|
| CP.0 | Naming, IA, branch, stub routes | Small (1 session) |
| CP.1 | Migrations + `runtime_config.ts` + read-only UI | Medium |
| CP.2 | Write endpoints + stack picker + routing/param editors + probe | Large |
| CP.3 | CallType extension + eval/smoke/checkpoint wiring | Medium |
| CP.4 | Health badges + audit + bidirectional Observatory links + a11y | Medium |
| CP.5 | Cutover + flag flip + monitoring window | Small |

Each phase produces a working, mergeable increment. CP.0 → CP.1 → CP.2 is the minimum viable feature; CP.3 → CP.4 → CP.5 are polish. The native can ship after CP.2 if they want and add the rest later.

Per CLAUDE.md §M cadence (closed-artifact-per-session, every-third-session red-team), CP.3 close is the natural red-team trigger.

---

## §11 — Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Stale cache serves wrong model after config change | MED | 60s TTL + cache-bust event on write; document this in the UI ("changes live within 1 min") |
| Super-admin foot-gun: select a model that doesn't exist or is degraded | HIGH | Dropdown filters out `role: 'planner'` for synthesis; health pips visible inline; smoke test must pass before save (optional gate) |
| Cost surprise: super-admin flips to Anthropic stack and burns credits | HIGH | Confirmation modal with "this costs ~$X per query at current params" before save; per the user's standing rule, Anthropic stack stays banned by default |
| Pipeline regression from the runtime_config refactor | HIGH | Feature flag gates the entire override layer; static-table path preserved as fallback; 48-hour Observatory monitoring window post-flip |
| Probe calls inflate cost dashboards | LOW | Probes tagged `pipeline_stage='probe'`; Observatory filters can exclude them from the main cost view by default |
| Mixed-stack mode (§3.2.a) introduces edge cases | MED | Decide in §13 Q3 before CP.1; if mixed mode is yes, ensure provider-options resolution (DeepSeek thinking, Gemini safety) keys off the model's provider, not the active stack |
| OBSERVATORY_PLAN §14 has overlapping items | LOW | Read §14 at CP.0 start; if any item overlaps, mark this proposal as superseding/aligning |

---

## §12 — What this proposal explicitly does NOT include

To keep scope tight:

- Per-user (not just global) stack overrides — possible future scope; the `scope` column anticipates it.
- Programmatic stack-switching via CLI / scripts — only the UI surface in v1.
- A/B testing infrastructure ("send 10% of queries to NIM, 90% to Gemini") — beyond v1; would require a new table.
- A "stack recommender" that suggests configs based on query type — a future Learning Layer hook.
- Editing the registry from the UI (adding a brand-new model entry) — registry stays code-managed; UI selects among entries that exist.
- Predictions Ledger tab (Phase O+1 territory, flagged but not built here).
- Renaming or restructuring the existing Observatory beyond adding the bidirectional deep-link pencil.

---

## §13 — Decision points needing native input

These are the questions where my best guess is documented but the native should choose explicitly before CP.1 starts. The answers shape the implementation; getting them up front prevents rework.

| # | Question | My default | Why I picked it |
|---|---|---|---|
| Q1 | Final name and URL slug? | "LLM Operations Center" at `/llm-ops`; existing `/observatory` aliased | Plain, two-tab IA fits naturally |
| Q2 | Scope: global only, or per-user? | Global only for v1 | Simpler, matches super-admin gating |
| Q3 | Can a config mix providers (NIM synthesis + Gemini worker)? | Yes, allow mixing; default UX pins to one stack but offers a "Custom" mode | Maximum flexibility; provider options key off model's provider, not the stack |
| Q4 | Smoke-test must pass before save? | Optional warning, not a hard gate | Don't block experimentation; surface the risk visibly |
| Q5 | Component library: shadcn/ui or current local primitives? | Match Observatory's existing primitives | Brand discipline; no new dependency |
| Q6 | Eval-judge model: pinned per stack, or one global default? | Per stack (so each stack self-tests with its own family) | Lets you compare like-with-like |
| Q7 | Probe prompts: hardcoded set, or editable from UI? | Hardcoded v1, JSON-editable file v2 | Faster ship, fewer abuse vectors |
| Q8 | Health-check cron cadence? | Nightly | Cheap, enough freshness for a manually-set system |
| Q9 | Should this feature land under M5 governance, or as a parallel workstream like Phase O? | **Parallel workstream**, analogous to Phase O | This is platform infrastructure, not chart-domain work; M5 sessions should not touch `platform/src/**` |
| Q10 | Branch name? | `feature/llm-ops-control-panel` | Conventional, descriptive |

---

## §14 — Branch + commit plan

**Branch:** `feature/llm-ops-control-panel`, cut from `main` after this proposal is approved.

**Worktree (optional but recommended for parallel work):**
```bash
git worktree add ../madhav-control-panel feature/llm-ops-control-panel
```

**Scope boundaries:**

```yaml
may_touch:
  - platform/src/app/(super-admin)/observatory/**   # adding sibling routes, pencil deep-link
  - platform/src/app/(super-admin)/control/**       # new directory
  - platform/src/app/(super-admin)/llm-ops/**       # new tab shell
  - platform/src/app/api/admin/control-panel/**     # new endpoints
  - platform/src/lib/models/**                      # adding runtime_config.ts + extending CallType
  - platform/src/lib/components/control-panel/**    # new component dir
  - platform/src/lib/observatory/**                 # only for adding "Configure" pencil
  - platform/supabase/migrations/**                 # five new additive migrations
  - platform/src/lib/config/feature_flags.ts        # adding CONTROL_PANEL_OVERRIDES_ENABLED
  - platform/scripts/eval/**                        # CP.3 only: wire to runtime_config
  - platform/scripts/observatory/smoke_test.ts      # CP.3 only: wire to runtime_config
  - platform/scripts/checkpoint/**                   # CP.3 only: wire to runtime_config
  - 00_ARCHITECTURE/CONTROL_PANEL_*.md              # this proposal + future plan/close docs

must_not_touch:
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**                           # M5 sessions own this
  - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
  - 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
  - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  - 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md       # sealed; sibling reads only
```

**Commit cadence:** one logical commit per phase (CP.0 → CP.5), squash-merged or rebase-merged per the project's existing convention. Phase O's pattern (umbrella branch, AC-by-AC progression, single PR at the end) is the model.

**LLM stack discipline** for any inference code added in this feature (eval scripts, probes that need a default): per the user's standing rule, default to Gemini, fallback to DeepSeek. Anthropic stack code paths are present but gated behind the cost-confirmation modal.

---

## §15 — Open questions for the brainstorm response

Two questions worth pulling to the top because they shape everything:

1. **Is "LLM Operations Center" the right name, or do you want something different?** I listed five candidates — happy to brainstorm more if none feel right.
2. **Do you want this to ship as a parallel workstream (like Phase O Observatory was) or folded into M5 governance?** My recommendation is parallel. It's infrastructure, not chart work, and M5 has hard `must_not_touch: platform/src/**` scope.

Everything else in §13 is a real decision but won't block kicking off the work.

---

*End of CONTROL_PANEL_FEATURE_PROPOSAL_v0_1.md*
*Authored 2026-05-13 in a Cowork brainstorm session by Opus 4.7. Awaiting native shaping + NAP.CTRL.1.*
