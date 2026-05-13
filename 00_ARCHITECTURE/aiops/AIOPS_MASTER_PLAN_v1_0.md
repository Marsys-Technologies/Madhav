---
artifact: AIOPS_MASTER_PLAN_v1_0.md
canonical_id: AIOPS_MASTER_PLAN
version: 1.0
status: AWAITING_NATIVE_GO
phase: AIOps-CP (Control Panel)
authored_at: 2026-05-13
authored_by: Cowork brainstorm session (Opus 4.7)
supersedes: 00_ARCHITECTURE/CONTROL_PANEL_FEATURE_PROPOSAL_v0_1.md
related:
  - 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
  - 00_ARCHITECTURE/aiops/phase_briefs/PHASE_CP_0_BRIEF.md … PHASE_CP_5_BRIEF.md
  - 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md (sealed v2.0.0 sibling)
  - platform/src/lib/models/registry.ts (primary integration anchor)
trigger_protocol: >
  Native approves this plan, then copies
  00_ARCHITECTURE/aiops/phase_briefs/PHASE_CP_0_BRIEF.md
  to project root as CLAUDECODE_BRIEF.md and triggers Claude Code with
  --dangerously-skip-permissions. The harness then executes
  PHASE_CP_0 → PHASE_CP_5 sequentially with no further native involvement
  until the final cutover acceptance gate at the end of PHASE_CP_5.
changelog:
  - v1.0 (2026-05-13): initial master plan covering all of Phase 1 (Control Panel);
    Phase 2 (Adapter Layer) and Phase 3 (Consume UI Overhaul) previewed in §15.
---

# AIOps — Artificial Intelligence Operations Center
## Master Plan v1.0 — Phase 1: Control Panel

---

## §0 — TL;DR

AIOps is a new top-level area in the Madhav portal that gives the super-admin
end-to-end control over every LLM call the system makes. It contains two tabs:

- **Control Panel** (new in this Phase 1 build) — configure which model serves
  every pipeline call type, on every stack; override token / param caps;
  probe-test any model; manage MARSYS (a 6th custom stack with cross-provider
  model selection); manage eval / smoke / checkpoint model choices across
  any stack.
- **Observatory** (existing, unchanged) — usage, cost, anomalies, reconciliation.

The bones of the data model live already in `platform/src/lib/models/registry.ts`
(`STACK_ROUTING`, `CallType`, `ModelStack`). Phase 1 wraps that static table
with: (a) a live provider-catalog discovery layer, (b) per-call-type spec
filters (mandatory + preferred), (c) a 6th MARSYS stack with cross-provider
mixing, (d) DB-backed overrides, (e) the full UI, (f) a probe endpoint,
(g) extension of `CallType` to first-class eval / smoke / checkpoint, and
(h) audit + health + accessibility polish.

This document is the comprehensive design. Execution is split across six
self-contained phase briefs (CP.0 → CP.5) under
`00_ARCHITECTURE/aiops/phase_briefs/`, each runnable by Claude Code in a
single autonomous session with `--dangerously-skip-permissions`. Native
involvement is bracketed at two points only: (i) the "go" decision on this
master plan, and (ii) the final cutover acceptance at end of CP.5.

---

## §1 — Naming

**Name:** AIOps — Artificial Intelligence Operations Center
**Short:** AIOps
**Top-level route:** `/aiops`
**Tabs:**
- `/aiops/control` — Control Panel (new)
- `/aiops/observatory` — Observatory (existing analytics; preserved at `/observatory` via alias so bookmarks survive)

A third future tab — **Predictions Ledger** — is anticipated for the
prospective-prediction logging substrate (per `MACRO_PLAN §Cross-cutting
workstreams`) but is **not** in Phase 1.

---

## §2 — Design philosophy

Three principles guide every decision in this plan:

1. **The registry stays code-managed.** `platform/src/lib/models/registry.ts`
   remains the structural source of truth for what models exist and what
   they cost. The Control Panel does not edit the registry; it only chooses
   *among* registry entries (augmented with whatever the provider's live
   catalog returns).

2. **Runtime selection layers cleanly on top.** A new
   `runtime_config.ts` resolves the effective model and effective params with
   a strict priority chain: per-request override → user localStorage →
   DB-backed AIOps override → static registry default. Every existing call
   site migrates from "read STACK_ROUTING directly" to "call
   getEffectiveModel/Param" — a small, mechanical refactor.

3. **Provider-specific quirks belong in a future adapter layer (Phase 2).**
   This means Phase 1 must NOT bake provider-specific assumptions into call
   sites. Where today there's a `if (provider === 'deepseek')` branch, it
   stays — but no new ones are added by Phase 1. Phase 2's adapter layer
   centralizes them.

---

## §3 — Stacks

Six stacks in v1.0:

| ID | Label | Provider(s) | Notes |
|---|---|---|---|
| `nim` | NIM Stack | `nvidia` | Free tier; live catalog discovery via NVIDIA NIM models endpoint |
| `gemini` | Gemini Stack | `google` | Current default; live catalog via Google AI Studio models endpoint |
| `deepseek` | DeepSeek Stack | `deepseek` | Native DeepSeek API; live catalog via DeepSeek models endpoint |
| `gpt` | GPT Stack | `openai` | Live catalog via OpenAI models endpoint |
| `anthropic` | Anthropic Stack | `anthropic` | Gated behind cost-confirmation modal per standing native preference |
| `marsys` | **MARSYS Stack** (NEW) | *any* | Custom cross-provider mix; dropdown shows ALL models matching the call-type spec |

`MARSYS` is the named, persistent expression of "I want this specific model
from this provider for synthesis, that specific model from that provider for
the worker." When selected as the active stack, each call-type dropdown shows
*every* model in the catalog matching the call type's spec — not filtered to
a single provider.

---

## §4 — Call types

Phase 1 extends the existing `CallType` taxonomy to cover all LLM call sites
across the codebase, not just the runtime pipeline.

| Call type | Used by | Cross-stack picks allowed? |
|---|---|---|
| `synthesis` | Runtime pipeline final answer | No (locked to active stack except MARSYS) |
| `planner_deep` | Runtime pipeline planner for multi-domain queries | No |
| `planner_fast` | Runtime pipeline planner for single-domain queries | No |
| `context_assembly` | Runtime pipeline post-retrieval compression | No |
| `worker` | Title gen, history summarization | No |
| **`eval_judge`** (NEW) | `answer:eval`, `planner:eval` scripts — grades outputs | **Yes** (free choice across all stacks) |
| **`eval_generator`** (NEW) | Eval scripts that generate prompts dynamically | **Yes** |
| **`smoke_synth`** (NEW) | `platform/scripts/observatory/smoke_test.ts` and successors | **Yes** |
| **`checkpoint_4_5`** (NEW) | Phase 6 checkpoint 4.5 (planner mid-flight verify) | **Yes** |
| **`checkpoint_5_5`** (NEW) | Phase 6 checkpoint 5.5 (context assembly mid-flight verify) | **Yes** |
| **`checkpoint_8_5`** (NEW) | Phase 6 checkpoint 8.5 (synthesis post-hoc verify) | **Yes** |

The rationale for the asymmetry: a stack is a cohesive bundle for the *runtime
pipeline* (consistent provider, consistent reasoning style, consistent context
window math). Eval and verification are different — they want the *best
available judge* regardless of which stack is on duty. That's why
eval/smoke/checkpoint always pick from the full catalog.

---

## §5 — Live catalog discovery

This is the major new requirement vs. v0.1. Each stack's available models are
fetched from the provider's official catalog endpoint, augmented with
internal metadata (context window, parameter size, capabilities, cost),
filtered by per-call-type spec, and presented in the dropdown.

### §5.1 — Provider catalog endpoints

| Stack | Endpoint | Auth | Response shape (relevant fields) |
|---|---|---|---|
| `nim` | `GET https://integrate.api.nvidia.com/v1/models` | `Bearer NVIDIA_NIM_API_KEY` | `{ data: [{ id, owned_by, ... }] }` |
| `gemini` | `GET https://generativelanguage.googleapis.com/v1beta/models` | `?key=GOOGLE_API_KEY` | `{ models: [{ name, inputTokenLimit, outputTokenLimit, supportedGenerationMethods, ... }] }` |
| `deepseek` | `GET https://api.deepseek.com/models` | `Bearer DEEPSEEK_API_KEY` | `{ data: [{ id, owned_by, ... }] }` |
| `gpt` | `GET https://api.openai.com/v1/models` | `Bearer OPENAI_API_KEY` | `{ data: [{ id, created, owned_by, ... }] }` |
| `anthropic` | `GET https://api.anthropic.com/v1/models` | `x-api-key`, `anthropic-version` | `{ data: [{ id, display_name, ... }] }` |

Most of these endpoints return only the model **ID**; they don't expose
context window or parameter count. The catalog service therefore *augments*
each entry with:

1. **Registry override** — if the model_id is in `MODELS`, use the registered
   metadata (this is the canonical source for known-good entries).
2. **Curated metadata file** — `platform/src/lib/aiops/catalog/metadata/<provider>.json`
   carries context-window + param-size + cost for models we know about but
   may not have promoted into the registry yet (e.g., NIM's GLM 5.1,
   nemotron variants, new DeepSeek versions).
3. **Probe-derived** — if the model has never been seen, mark it `unknown`
   for context window / params; the Control Panel marks it
   `[METADATA_PENDING]` and offers a "Probe this model" button to discover
   what we can.

### §5.2 — Catalog service implementation

```
platform/src/lib/aiops/catalog/
├── types.ts                 # CatalogEntry, CatalogFetchResult, ProviderQuirks
├── fetcher.ts               # async fetchProviderCatalog(provider) → CatalogEntry[]
├── fetcher_nim.ts           # NIM-specific HTTP + parsing
├── fetcher_gemini.ts
├── fetcher_deepseek.ts
├── fetcher_openai.ts
├── fetcher_anthropic.ts
├── augment.ts               # merge fetched entries with registry + metadata files
├── cache.ts                 # 6h TTL in-memory + DB-backed catalog snapshot
├── metadata/
│   ├── nim.json
│   ├── gemini.json
│   ├── deepseek.json
│   ├── openai.json
│   └── anthropic.json
└── index.ts                 # exports getCatalog(provider) + getCrossProviderCatalog()
```

Refresh policy: lazy on read, with a 6-hour TTL; force-refresh button in the
Control Panel for the impatient. A nightly cron pre-warms the cache.

### §5.3 — Per-call-type spec filtering

Each call type declares a spec — mandatory and preferred — that filters the
catalog entries before rendering in the dropdown.

```ts
// platform/src/lib/aiops/specs/call_type_specs.ts
export interface CallTypeSpec {
  mandatory: {
    minInputTokens?: number     // ≥ value (e.g., 1_000_000)
    capabilities?: Capability[] // required capabilities
    roleIn?: ModelRole[]        // role must be one of these
  }
  preferred: {
    sortBy: 'params_desc' | 'cost_asc' | 'latency_asc' | 'context_desc'
    secondarySortBy?: 'params_desc' | 'cost_asc' | 'latency_asc' | 'context_desc'
  }
  notes?: string                // human-readable spec note for the UI ("≥1M context window required")
}

export const CALL_TYPE_SPECS: Record<CallType, CallTypeSpec> = {
  synthesis: {
    mandatory: { minInputTokens: 1_000_000, roleIn: ['synthesis', 'both'] },
    preferred: { sortBy: 'params_desc' },
    notes: 'Mandatory ≥1M context (Whole-Chart-Read); preferred highest parameter count.',
  },
  context_assembly: {
    mandatory: { minInputTokens: 1_000_000 },
    preferred: { sortBy: 'cost_asc' },
    notes: 'Mandatory ≥1M context; preferred low cost (this stage is called once per query).',
  },
  planner_deep: {
    mandatory: { capabilities: ['tool-use'] },
    preferred: { sortBy: 'params_desc', secondarySortBy: 'latency_asc' },
    notes: 'Mandatory tool-use; preferred deep reasoning at acceptable latency.',
  },
  planner_fast: {
    mandatory: { capabilities: ['tool-use'] },
    preferred: { sortBy: 'latency_asc', secondarySortBy: 'cost_asc' },
    notes: 'Mandatory tool-use; preferred lowest latency.',
  },
  worker: {
    mandatory: {},
    preferred: { sortBy: 'cost_asc' },
    notes: 'Cheapest model that responds; latency secondary.',
  },
  eval_judge: {
    mandatory: { minInputTokens: 200_000 },
    preferred: { sortBy: 'params_desc' },
    notes: '≥200K context to ingest synthesis output + ground truth; highest reasoning capacity.',
  },
  eval_generator: {
    mandatory: {},
    preferred: { sortBy: 'params_desc' },
    notes: 'Used to generate eval prompts; reasoning quality matters more than cost.',
  },
  smoke_synth: {
    mandatory: { minInputTokens: 1_000_000 },
    preferred: { sortBy: 'cost_asc' },
    notes: 'Same context floor as synthesis; should be cheap (run frequently).',
  },
  checkpoint_4_5: {
    mandatory: {},
    preferred: { sortBy: 'cost_asc' },
    notes: 'Mid-flight planner verification; speed and cost matter.',
  },
  checkpoint_5_5: {
    mandatory: { minInputTokens: 200_000 },
    preferred: { sortBy: 'cost_asc' },
    notes: '≥200K context to inspect assembled bundle; cheap.',
  },
  checkpoint_8_5: {
    mandatory: { minInputTokens: 200_000 },
    preferred: { sortBy: 'params_desc' },
    notes: 'Post-hoc synthesis verification; deeper reasoning useful.',
  },
}
```

These specs themselves are *config*, not hardcoded — stored in `call_type_specs.ts`
and editable via PR, not via the UI (in v1.0). The UI exposes the spec note
inline ("≥1M context window required") so the super-admin understands why
the dropdown is filtered.

### §5.4 — Dropdown ordering

Within a dropdown:
1. **Group by provider** (NIM, Gemini, DeepSeek, GPT, Anthropic).
2. Within each provider, **sort by the call-type's preferred sort key**.
3. Pin the current registry-default model to the top with a "default" badge.
4. Show a `[METADATA_PENDING]` row at the bottom for newly-discovered models
   that haven't been augmented yet.

For MARSYS stack: skip the provider-grouping; one flat sorted list across all
providers, with provider tags inline.

For eval / smoke / checkpoint: same as MARSYS (cross-provider, flat sorted list).

---

## §6 — Information architecture (UI map)

```
AIOps                                      /aiops             (new shell)
├── Control Panel                           /aiops/control     (new)
│   ├── Stack Picker                         (6 cards: NIM, Gemini, DeepSeek, GPT, Anthropic, MARSYS)
│   │   └─ Each card: synth model, ctx window, est cost/query, health, "View usage" link
│   ├── [Selected Stack]
│   │   ├── Pipeline Call Types
│   │   │   ├── synthesis           primary‹dropdown› + backup‹dropdown› + [Test] + ▾Advanced
│   │   │   ├── planner_deep        primary + backup + Test + Advanced
│   │   │   ├── planner_fast        primary + backup + Test + Advanced
│   │   │   ├── context_assembly    primary + backup + Test + Advanced
│   │   │   └── worker              primary + backup + Test + Advanced
│   │   ├── ╭─ Stack Smoke Test ────────────╮
│   │   │   │  [Run smoke test for this stack] │
│   │   │   │  Probes 5 call types × 2 roles = 10 probes; renders grid │
│   │   │   ╰────────────────────────────────╯
│   │   └── Quality & Verification           (eval + smoke + checkpoint, cross-stack)
│   │       ├── eval_judge          primary + backup + Test  [shows all providers]
│   │       ├── eval_generator      primary + backup + Test  [shows all providers]
│   │       ├── smoke_synth         primary + backup + Test  [shows all providers]
│   │       └── checkpoint_4_5/5_5/8_5  primary + backup + Test
│   ├── Right rail: Recent Changes  (last 20, one-click revert)
│   └── Right rail: Health Status   (every model's last probe)
└── Observatory                              /aiops/observatory (alias /observatory)
    ├── (unchanged)
    └── StackBreakdownCards gain a "Configure" pencil → deep-link to /aiops/control
```

A second "Custom" mode within the per-stack view is not in v1.0 because MARSYS
*is* that custom mode, as a first-class stack.

---

## §7 — Runtime pipeline integration

### §7.1 — The new resolver

```
platform/src/lib/models/runtime_config.ts
```

Public API:
```ts
export async function getEffectiveStack(req?: Request): Promise<ModelStack>
export async function getEffectiveModel(
  stack: ModelStack,
  callType: CallType,
  role: 'primary' | 'fallback',
  req?: Request,
): Promise<string>
export async function getEffectiveParam<T = unknown>(
  stack: ModelStack,
  callType: CallType,
  paramName: 'max_output_tokens' | 'temperature' | 'thinkingBudget' | 'timeout_ms',
  fallback: T,
  req?: Request,
): Promise<T>
export function invalidateRuntimeConfigCache(): void  // called by Control Panel writes
```

Resolution priority (top wins):
1. **Per-request header** — `x-aiops-stack`, `x-aiops-model-<callType>-<role>`, `x-aiops-param-<...>` — used by the probe endpoint and integration tests.
2. **User localStorage** — existing per-user stack override at `/consume`.
3. **DB override** — `llm_stack_config` (stack) + `llm_stack_routing_override` (model) + `llm_param_override` (params).
4. **Static `STACK_ROUTING` registry** — ultimate fallback.

In-memory cache: 60s TTL, busted by `invalidateRuntimeConfigCache()` which the
Control Panel calls after every write.

### §7.2 — Call-site migration

Every direct reader of `STACK_ROUTING[...]` or `getPrimaryModel(...)`/`getFallbackModel(...)`
becomes a reader of `getEffectiveModel(...)`. This is a mechanical change
covering ~10-20 files. Phase CP.3 contains the migration; the resolver and
DB layer ship before the migration so that during CP.1+CP.2 the system behaves
identically to today, gated by `AIOPS_OVERRIDES_ENABLED=false`.

### §7.3 — MARSYS stack support at runtime

When `stack='marsys'`, `STACK_ROUTING['marsys']` doesn't exist (because the
selection is dynamic). The resolver falls through to the DB override table.
If a MARSYS user has not set an override, the system falls back to the
provider implied by the chosen model — i.e., MARSYS is fully resolved by the
DB layer; the static registry has no MARSYS row.

To prevent footgun on first activation, MARSYS pre-seeds its rows in
`llm_stack_routing_override` at migration time, with sensible defaults
(synthesis = `gemini-2.5-pro` per call-type spec preferred sort).

---

## §8 — Data model

Five new tables, all under `platform/supabase/migrations/`. The schema uses
the `llm_*` prefix consistent with the existing observability schema.

```sql
CREATE TABLE llm_stack_config (
  scope            text PRIMARY KEY,           -- 'global' for v1.0
  active_stack     text NOT NULL,              -- 'nim' | 'gemini' | 'deepseek' | 'gpt' | 'anthropic' | 'marsys'
  updated_at       timestamptz NOT NULL DEFAULT now(),
  updated_by       text NOT NULL
);

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

CREATE TABLE llm_param_override (
  scope            text NOT NULL,
  stack            text NOT NULL,
  call_type        text NOT NULL,
  param_name       text NOT NULL,
  param_value      jsonb NOT NULL,
  updated_at       timestamptz NOT NULL DEFAULT now(),
  updated_by       text NOT NULL,
  PRIMARY KEY (scope, stack, call_type, param_name)
);

CREATE TABLE llm_model_health (
  model_id         text PRIMARY KEY,
  status           text NOT NULL,             -- 'pass' | 'fail' | 'stale' | 'never_probed'
  latency_ms       int,
  last_probe_at    timestamptz,
  last_error       text,
  last_probed_by   text
);

CREATE TABLE llm_config_audit (
  id               bigserial PRIMARY KEY,
  occurred_at      timestamptz NOT NULL DEFAULT now(),
  actor_user_id    text NOT NULL,
  action           text NOT NULL,             -- 'set_stack' | 'set_routing' | 'set_param' | 'reset_param' | 'probe' | 'revert'
  scope            text,
  stack            text,
  call_type        text,
  param_name       text,
  before_value     jsonb,
  after_value      jsonb,
  notes            text
);

-- Provider catalog snapshot (for offline view + drift detection)
CREATE TABLE llm_catalog_snapshot (
  provider         text NOT NULL,
  model_id         text NOT NULL,
  fetched_at       timestamptz NOT NULL DEFAULT now(),
  raw_payload      jsonb NOT NULL,
  augmented        jsonb NOT NULL,             -- with context window, params, etc.
  PRIMARY KEY (provider, model_id, fetched_at)
);
```

Migration is fully additive. Rollback is `DROP TABLE`.

---

## §9 — API surface

All under `/api/admin/aiops/`, super-admin-gated:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/state` | Active stack + full effective routing + param overrides + health snapshot |
| `PUT` | `/stack` | Set global active stack |
| `GET` | `/routing/:stack` | Effective routing for one stack |
| `PUT` | `/routing/:stack/:call_type` | Save routing override (primary + fallback) |
| `DELETE` | `/routing/:stack/:call_type` | Reset routing to registry default |
| `GET` | `/params/:stack/:call_type` | Effective params |
| `PUT` | `/params/:stack/:call_type/:param` | Save param override |
| `DELETE` | `/params/:stack/:call_type/:param` | Reset param |
| `GET` | `/catalog/:provider` | Live provider catalog (cached 6h) |
| `POST` | `/catalog/refresh/:provider` | Force-refresh that provider's catalog |
| `POST` | `/probe` | `{ stack, call_type, role }` → run single probe |
| `POST` | `/smoke/:stack` | Probe every call type × role for a stack |
| `GET` | `/health` | Full health table (optional `?model_id=` filter) |
| `GET` | `/audit` | Last N config changes |
| `POST` | `/audit/:id/revert` | Revert a past change |

Probe and smoke calls flow through the existing observed provider wrappers,
so they appear in the Observatory as `pipeline_stage='aiops_probe'` or
`'aiops_smoke'`.

---

## §10 — Six-phase execution arc

Each phase produces a committed, working, mergeable increment, gated only
by automated acceptance criteria.

| Phase | Scope | Brief file |
|---|---|---|
| **CP.0** | Naming, branch, IA shell, stub routes | `phase_briefs/PHASE_CP_0_BRIEF.md` |
| **CP.1** | DB migrations, catalog discovery service, spec definitions, runtime_config resolver, MARSYS stack support, registry CallType extensions, read-only Control Panel UI | `phase_briefs/PHASE_CP_1_BRIEF.md` |
| **CP.2** | Write-side endpoints, full UI (stack picker, dropdowns with spec filtering, param editor, MARSYS UI, eval/smoke/checkpoint cross-stack UI), probe endpoint, single-probe + stack-smoke buttons | `phase_briefs/PHASE_CP_2_BRIEF.md` |
| **CP.3** | Call-site migration to runtime_config, eval/smoke/checkpoint script wiring, bidirectional Observatory deep-links, cache invalidation flow | `phase_briefs/PHASE_CP_3_BRIEF.md` |
| **CP.4** | Health badges everywhere, audit log right-rail with revert, accessibility pass, brand discipline pass, visual regression | `phase_briefs/PHASE_CP_4_BRIEF.md` |
| **CP.5** | Final integration smoke tests, flag flip, 48h monitoring window, flag removal scheduled, native-acceptance gate | `phase_briefs/PHASE_CP_5_BRIEF.md` |

Each brief is fully self-contained and concludes by rewriting the root
`CLAUDECODE_BRIEF.md` to point at the next phase. See `AIOPS_EXECUTION_RULES_v1_0.md`
for the autonomous-execution mechanics.

---

## §11 — Branch + git discipline

**Branch:** `feature/aiops-control-panel`, cut from `main`.
**Worktree (optional):** `git worktree add ../madhav-aiops feature/aiops-control-panel`.
**Commits:** one logical commit per phase, signed with `feat(aiops-CP.N):` prefix.
**No rebase mid-branch** — preserve the per-phase history.
**Merge strategy:** single PR at the end of CP.5 (squash or rebase per project convention).

### Scope boundaries (apply to every phase)

```yaml
may_touch:
  - platform/src/app/(super-admin)/aiops/**           # new shell + child routes
  - platform/src/app/api/admin/aiops/**                # new endpoints
  - platform/src/lib/aiops/**                          # new service code
  - platform/src/lib/models/**                         # extending CallType + adding runtime_config.ts + adding MARSYS
  - platform/src/lib/components/aiops/**               # new component dir
  - platform/src/lib/components/observatory/**         # CP.3 only: adding "Configure" pencil
  - platform/supabase/migrations/**                    # additive migrations only
  - platform/src/lib/config/feature_flags.ts           # adding AIOPS_OVERRIDES_ENABLED
  - platform/scripts/eval/**                           # CP.3 only: wire to runtime_config
  - platform/scripts/observatory/smoke_test.ts         # CP.3 only: wire to runtime_config
  - platform/scripts/checkpoint/**                     # CP.3 only: wire to runtime_config
  - platform/src/app/observatory/**                    # CP.0 only: alias setup
  - 00_ARCHITECTURE/aiops/**                           # docs + brief updates
  - CLAUDECODE_BRIEF.md                                # session-handoff updates

must_not_touch:
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
  - 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
  - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  - 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md           # sealed; sibling reads only
  - platform/src/app/api/admin/observatory/**          # Observatory backend untouched
```

---

## §12 — Definition of done (entire Phase 1)

The whole Phase 1 is **DONE** when, after CP.5 closes:

- [ ] All six phase briefs are CLOSED.
- [ ] Branch `feature/aiops-control-panel` has one logical commit per phase.
- [ ] All migrations are applied; all five tables exist with seed data.
- [ ] The Control Panel renders at `/aiops/control` and the Observatory renders at `/aiops/observatory` and `/observatory`.
- [ ] All five pipeline call types render with primary + backup + Test + Advanced for every stack including MARSYS.
- [ ] All eval / smoke / checkpoint call types render with cross-stack model selection.
- [ ] Per-call-type spec filtering is in force; dropdowns show only matching models from live catalogs.
- [ ] The Test button on every dropdown returns pass / latency / cost in under 30s for any model that supports the call type.
- [ ] The stack-smoke button runs all 10 probes for a stack and returns a grid.
- [ ] The Recent Changes right rail shows the last 20 edits with one-click revert.
- [ ] Every model row shows a green/yellow/red/gray health pip.
- [ ] Bidirectional deep links between Control Panel and Observatory work both ways.
- [ ] `AIOPS_OVERRIDES_ENABLED=true` in production.
- [ ] 48-hour Observatory window post-flip shows no cost/usage regressions.
- [ ] Accessibility audit passes WCAG 2.1 AA.
- [ ] Brand audit confirms no new colors or fonts introduced.
- [ ] Native gives final acceptance.

---

## §13 — Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Live catalog fetch fails or rate-limits | MED | 6h TTL cache + force-refresh button + graceful degradation to last-known-good snapshot in `llm_catalog_snapshot` |
| Provider API key missing → catalog endpoint 401 | MED | Health card on Control Panel landing shows per-provider auth status; redact key from error messages |
| Super-admin selects a model that doesn't exist in catalog | LOW | Save still works but health pip turns gray; first probe attempt surfaces the API error inline |
| Cost surprise on Anthropic stack switch | HIGH | Confirmation modal showing estimated $/query before save; per standing native rule, Anthropic stays deselectable but not forbidden |
| Probe call inflates Observatory cost dashboard | LOW | All probe calls tagged `pipeline_stage='aiops_probe'`; default Observatory filters exclude probe rows |
| Cache stale → user expects new model, gets old | LOW | 60s TTL + invalidation event; visible "config updated, taking effect within 1 minute" toast on save |
| `AIOPS_OVERRIDES_ENABLED=true` flip breaks production pipeline | HIGH | Flag default false through CP.1–CP.4; flip in CP.5 only after stack-smoke passes on all 6 stacks; 48h monitoring window with rollback prepared |
| Phase 2 adapter layer conflicts with Phase 1 decisions | MED | Phase 1 must not bake provider-specific logic into call sites; resolver returns model_id only, not provider quirks |
| `must_not_touch` violation across boundaries | HIGH | Every phase brief includes the same scope-boundary block; close-script greps for forbidden paths |
| Test failures during autonomous run halt progress | MED | Each phase has a `BAIL_OUT_PROTOCOL` in its brief — abort, write a status note to CLAUDECODE_BRIEF, and stop. Native picks up from there |

---

## §14 — Forward compatibility with Phase 2 + Phase 3

Per native's elaboration of the roadmap:

### Phase 2 — Model-aware Adapter Layer

**Goal:** A single abstract "execute this query against the selected model"
interface that internally dispatches to model-specific prompt formatting,
provider-specific options, output parsing quirks (DeepSeek `<think>` blocks,
Gemini reasoning UIMessage parts, Anthropic system blocks, OpenAI structured
outputs, NIM OpenAI-compat semantics).

**Phase 1 commitments to keep Phase 2 clean:**

- `getEffectiveModel()` returns `model_id: string` only. Provider-specific
  configuration stays in `resolver.ts` (existing) — *not* in `runtime_config.ts`.
- No new call-site `if (provider === ...)` branches are introduced by Phase 1.
- Probe payloads are abstract (prompt text + role-appropriate output schema);
  the existing `resolveModel()` already handles per-provider request shaping.
- Param overrides in `llm_param_override` use generic keys
  (`max_output_tokens`, `temperature`, `thinkingBudget`, `timeout_ms`) —
  Phase 2 can extend with provider-specific keys without schema migration.
- Catalog augmentation metadata files include a `quirks` field reserved for
  Phase 2 use (`{ reasoning_via: 'native' | 'markers' | 'none'; system_block_required: bool; ... }`).

### Phase 3 — `/consume` UI Overhaul

**Goal:** Address the accumulated UI bugs in the chat consume surface;
align it with the new AIOps configuration system; modernize.

**Phase 1 commitments to keep Phase 3 clean:**

- The user-level stack override in localStorage stays in place (existing
  behavior); the new DB-backed global default does not override per-user
  preference. Phase 3 may decide to expose stack selection in the consume UI
  itself, on top of what Phase 1 builds.
- The consume route's call-site reading model IDs goes through
  `getEffectiveModel()` in Phase 1's CP.3, so Phase 3 doesn't need to
  re-plumb the routing layer.
- All consume-related observability (audit events, model_id capture in
  events table) continues to flow through the same observed providers,
  so the Observatory keeps working through Phase 3.

A separate `AIOPS_PHASE_2_MASTER_PLAN_v1_0.md` and `AIOPS_PHASE_3_MASTER_PLAN_v1_0.md`
will be authored when those phases are ready to start. They are explicitly
out of scope for this branch.

---

## §15 — Trigger protocol

When this master plan is approved:

1. Native copies `00_ARCHITECTURE/aiops/phase_briefs/PHASE_CP_0_BRIEF.md`
   to project root as `CLAUDECODE_BRIEF.md`, overwriting the current
   (status: COMPLETE) file.
2. Native triggers Claude Code with bypass + dangerously-skip-permissions.
3. Claude Code reads the brief, executes CP.0, commits, then rewrites
   `CLAUDECODE_BRIEF.md` with the contents of `PHASE_CP_1_BRIEF.md` (and
   leaves status: OPEN). Session closes.
4. Native triggers Claude Code again with the same flags.
5. Claude Code reads, executes CP.1, commits, rewrites CLAUDECODE_BRIEF
   for CP.2. Session closes.
6. … (repeat through CP.5)
7. At CP.5 close, the brief is overwritten to `status: COMPLETE` with a
   "ready for native acceptance" note. Native does the final review +
   flag flip.

Optionally, the native can launch each session with a single command:
```bash
claude-code --dangerously-skip-permissions \
  --bypass-permissions \
  --message "Read CLAUDECODE_BRIEF.md and execute it."
```

If a session hits a BAIL_OUT condition (unrecoverable test failure,
ambiguity that needs native shaping), it halts and writes the failure
mode into CLAUDECODE_BRIEF with `status: HALTED`. Native investigates
and rewrites the brief to resume.

---

## §16 — Open questions resolved (for native confirmation)

| # | Question (from v0.1 §13) | v1.0 resolution |
|---|---|---|
| Q1 | Name + URL slug | **AIOps**, `/aiops`, two tabs `/aiops/control` + `/aiops/observatory` (alias `/observatory` preserved) |
| Q2 | Global only or per-user scope | Global only for v1.0; `scope` column anticipates future per-user |
| Q3 | Mixed-provider configs | No mixing inside the 5 official stacks; **MARSYS** is the 6th stack and IS the mixed-provider mode |
| Q4 | Smoke-test required before save | No hard gate; visible warning if smoke is stale or failed |
| Q5 | Component library | Reuse Observatory primitives (no new dependency) |
| Q6 | Eval judge model: per stack or global | **Cross-stack — eval/smoke/checkpoint pick from full catalog** |
| Q7 | Probe prompts hardcoded or editable | Hardcoded for v1.0; future: JSON-editable file (Phase 2 contender) |
| Q8 | Health-check cron cadence | Nightly |
| Q9 | Parallel workstream or folded | Folded — single branch, autonomous execution via bypass-permissions Claude Code |
| Q10 | Branch name | `feature/aiops-control-panel` |
| Q11 (NEW) | Live catalog discovery from provider portals | **Yes** — six fetcher modules + curated metadata + 6h cache + force-refresh |
| Q12 (NEW) | Per-call-type spec filtering | **Yes** — CALL_TYPE_SPECS table with mandatory + preferred + UI note |
| Q13 (NEW) | MARSYS stack registration | **Yes** — `ModelStack` extended; dropdowns flatten across providers in MARSYS mode |
| Q14 (NEW) | Phase 2 + Phase 3 visibility | Acknowledged; §14 lists Phase 1 commitments that keep Phase 2 + Phase 3 unblocked |

---

## §17 — Native acceptance checklist (review before approving "go")

- [ ] Name "AIOps" + URL `/aiops` is right
- [ ] Six stacks (NIM, Gemini, DeepSeek, GPT, Anthropic, MARSYS) is the right set
- [ ] Eleven call types (5 pipeline + 6 quality/verification) is the right set
- [ ] Per-call-type specs in §5.3 match my intent (especially synthesis ≥1M + params desc)
- [ ] Branch name `feature/aiops-control-panel` is acceptable
- [ ] Six-phase split (CP.0 → CP.5) is acceptable
- [ ] Autonomous execution via bypass-permissions Claude Code is what I want
- [ ] Native acceptance is at the end of CP.5 only (no mid-arc check-ins required by the plan)
- [ ] Phase 2 (adapter) + Phase 3 (consume UI) acknowledgement in §14 captures my intent
- [ ] No M5 or 01_FACTS_LAYER / 06_LEARNING_LAYER touchpoints — confirmed
- [ ] I have read at least one phase brief (recommended: CP.0 + CP.1) and confirm the execution detail is sufficient

When the boxes are checked, native gives "go" and the trigger protocol in §15 runs.

---

*End of AIOPS_MASTER_PLAN_v1_0.md*
*Awaiting native acceptance for trigger.*
