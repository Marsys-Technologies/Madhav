---
status: OPEN
session_id: AIOPS_CP_2
phase: CP.2
phase_name: "Write side + probe + spec-filtered dropdowns + MARSYS UI + cross-stack UI"
next_session: AIOPS_CP_3
authored_at: 2026-05-13
authored_by: AIOPS_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CP_2
## AIOps Phase 1, Step 2 — Full interactive Control Panel

---

## §0 — Executor orientation

CP.2 builds the entire interactive Control Panel UI plus all write
endpoints plus the probe endpoint. After CP.2 closes, the Control Panel is
visually and functionally complete EXCEPT for: the call-site migration
(CP.3), the audit-rail revert button (CP.4 polish), and the production flag
flip (CP.5).

Read `00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md` and
`AIOPS_MASTER_PLAN_v1_0.md §6, §9` in full.

---

## §1 — Mandatory reads

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4.  platform/src/lib/models/registry.ts
5.  platform/src/lib/models/runtime_config.ts                     # written in CP.1
6.  platform/src/lib/aiops/catalog/index.ts                       # written in CP.1
7.  platform/src/lib/aiops/specs/call_type_specs.ts               # written in CP.1
8.  platform/src/lib/db/schema/aiops.ts                           # written in CP.1
9.  platform/src/lib/components/observatory/filters/MultiSelect.tsx (existing pattern to reuse)
10. platform/src/lib/components/observatory/events/EventSidePanel.tsx (slide-over reuse)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/aiops/**                       # probe service, dropdown adapter
platform/src/app/api/admin/aiops/**             # all write endpoints + probe + smoke
platform/src/app/(super-admin)/aiops/control/page.tsx
platform/src/lib/components/aiops/**            # all new components for CP.2 UI
CLAUDECODE_BRIEF.md
```

### must_not_touch
(same as CP.1; in particular do NOT migrate call sites yet — that's CP.3)

---

## §3 — Work plan

### 3.1 — Write API endpoints

Implement per AIOPS_MASTER_PLAN §9:

- `PUT /api/admin/aiops/stack` — sets active stack; writes `llm_stack_config` + audit row + cache-bust.
- `PUT /api/admin/aiops/routing/[stack]/[call_type]` — sets routing override.
- `DELETE /api/admin/aiops/routing/[stack]/[call_type]` — resets to registry.
- `PUT /api/admin/aiops/params/[stack]/[call_type]/[param]` — sets param override.
- `DELETE /api/admin/aiops/params/[stack]/[call_type]/[param]` — resets param.
- `GET /api/admin/aiops/catalog/[provider]` — live catalog (cached 6h).
- `POST /api/admin/aiops/catalog/refresh/[provider]` — force-refresh.
- `GET /api/admin/aiops/audit?limit=20` — recent changes.

Every write endpoint:
- Validates input with zod (define schemas in `platform/src/app/api/admin/aiops/_parse.ts`).
- Verifies the new value is sensible: model_id exists in the augmented catalog;
  call_type is recognized; param_value matches the expected type for that param_name.
- Writes an `llm_config_audit` row in the same transaction as the write.
- Calls `invalidateRuntimeConfigCache()` after the transaction commits.
- Returns the new effective state for the affected (stack, call_type).

Tests in `__tests__/` per endpoint: ≥3 cases each (valid update, invalid input,
auth failure).

### 3.2 — Probe service

Create `platform/src/lib/aiops/probe/`:

- `prompts.ts` — per-call-type probe prompts (hardcoded). For synthesis-class
  probes use a small Jyotish-flavored example; for planner probes ask for a
  structured JSON tool plan; for worker probes ask for a one-sentence
  summary.
- `runner.ts` — `runProbe({ stack, callType, role, modelOverride? }): Promise<ProbeResult>`.
  Internally calls `resolveModel(modelId)` then `streamText` with the
  call-type-appropriate prompt and timeout. Captures: token counts,
  latency, USD cost (from MODELS metadata), output text (truncated to
  300 chars), `finishReason`, error if any.
- `types.ts` — `ProbeResult`, `ProbeOptions`.

Probe calls go through the existing observed provider wrappers so they
appear in the Observatory with `pipeline_stage='aiops_probe'`.

### 3.3 — Probe + smoke endpoints

- `POST /api/admin/aiops/probe` — body `{ stack, call_type, role }` →
  ProbeResult. Streams the model output to the client (server-sent events
  pattern matching the rest of the codebase).
- `POST /api/admin/aiops/smoke/[stack]` — runs probe for every
  (call_type × role) pair for the stack. Returns
  `{ results: ProbeResult[], all_pass: boolean, summary: {...} }`.
  For the MARSYS stack: probes only what the user has explicitly set in DB
  overrides (no fallback to registry defaults for MARSYS).

### 3.4 — Spec-filtered model dropdown

Create `platform/src/lib/components/aiops/ModelDropdown.tsx`:

Props:
- `stack: ModelStack`
- `callType: CallType`
- `role: 'primary' | 'fallback'`
- `value: string` (current model_id)
- `onChange: (modelId: string) => void`

Internal behavior:
- Calls `GET /api/admin/aiops/catalog/<provider>` for the stack's primary
  provider (or all 5 providers if stack === 'marsys' or callType is
  eval/smoke/checkpoint).
- Applies `filterCatalogForCallType(entries, callType)` from CP.1.
- Groups by provider (except MARSYS / eval / smoke / checkpoint — flat list).
- Sorts per spec preferred sort key.
- Pins registry-default to top with "default" badge.
- Shows `[METADATA_PENDING]` entries at bottom.
- Renders health pip next to each entry (gray initially, populated by CP.4
  health cron).
- Shows the spec note ("≥1M context required") as a subdued caption.
- "Refresh catalog" icon button that calls
  `POST /api/admin/aiops/catalog/refresh/<provider>`.

### 3.5 — Param-override row

Create `platform/src/lib/components/aiops/ParamOverrideRow.tsx`:

For each (stack, call_type), an Advanced disclosure expands four rows:
`max_output_tokens`, `temperature`, `thinkingBudget`, `timeout_ms`.

Each row shows: param name | default value (from registry / provider options
defaults) | current override (or "(default)") | input field | reset link.

On change → debounced 500ms → PUT to
`/api/admin/aiops/params/[stack]/[call_type]/[param]`.

### 3.6 — Test probe inline panel

Create `platform/src/lib/components/aiops/TestProbeInline.tsx`:

A collapsible region beneath each (stack, call_type) row. When the Test
button is clicked, it expands and:
1. Calls `POST /api/admin/aiops/probe` with `{ stack, call_type, role }`.
2. Streams the response.
3. Shows: status (running → pass/fail), latency, tokens in/out, cost,
   `finishReason`, output text (truncated to 300 chars), error if any.
4. After completion, the dropdown's health pip updates to green/red.

### 3.7 — Stack-level smoke test

Create `platform/src/lib/components/aiops/StackSmokeButton.tsx`:

Big button on each stack card. Clicking it:
1. POSTs to `/api/admin/aiops/smoke/<stack>`.
2. Renders a 5×2 grid (5 call types × {primary, fallback}) with each cell
   showing pass/fail/running.
3. On completion, surfaces a summary: "9/10 PASS — DeepSeek V4 Pro
   synthesis primary timed out."

### 3.8 — Full Control Panel page

Replace the CP.1 read-only page with the full interactive layout per
AIOPS_MASTER_PLAN §6:

- Top: stack picker (6 cards, all clickable, with cost-confirmation modal for
  paid stacks per Risk register).
- Below: selected stack's call type rows (5 pipeline + 6 quality/verification).
  Each row has ModelDropdown × 2 (primary + fallback), Test buttons, and
  the Advanced disclosure with ParamOverrideRow.
- Stack smoke button between the two row groups.
- Right rail: Recent Changes (live data from `/api/admin/aiops/audit`).
  Revert button is a no-op visual only in CP.2 (real revert lands in CP.4).

For the MARSYS card: same UI but dropdowns are unrestricted (the
ModelDropdown logic handles this; MARSYS card just passes `stack='marsys'`).

For the Quality & Verification section: each row passes `stack='marsys'`
internally to ModelDropdown OR a dedicated `crossStack=true` flag — choose
the cleanest implementation. Either way, the dropdown shows models across
all 5 providers (NIM, Gemini, DeepSeek, GPT, Anthropic).

### 3.9 — Cost-confirmation modal

Create `platform/src/lib/components/aiops/CostConfirmDialog.tsx`:

Triggered when switching to a stack whose synthesis primary cost ≥ a
threshold (e.g., > $1.00 per 1M input tokens). Shows estimated cost per
query at current params; requires explicit click-through.

Per native standing rule (Anthropic banned by default), Anthropic always
triggers this modal regardless of pricing threshold.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CP2.1 | All 8 write endpoints exist + tests | `npm run test -- aiops` ≥24 endpoint cases pass |
| AC.CP2.2 | Probe endpoint streams + returns ProbeResult shape | E2E test passes |
| AC.CP2.3 | Smoke endpoint runs 10 probes for one stack | E2E test on `nim` stack returns 10 results |
| AC.CP2.4 | ModelDropdown filters per spec | Test asserts synthesis dropdown shows only models with `maxInputTokens >= 1_000_000` |
| AC.CP2.5 | MARSYS card shows all providers flat | Snapshot test of dropdown contents |
| AC.CP2.6 | Quality & Verification rows show cross-stack catalog | Snapshot test |
| AC.CP2.7 | Switching to Anthropic stack triggers CostConfirmDialog | UI test |
| AC.CP2.8 | Param override round-trips | Integration test: set → read → assert |
| AC.CP2.9 | Audit row written for every config change | Integration test counts audit rows before/after |
| AC.CP2.10 | Catalog force-refresh updates the cache | Integration test with mock HTTP |
| AC.CP2.11 | `npm run typecheck` | exit 0 |
| AC.CP2.12 | `npm run lint` | exit 0 |
| AC.CP2.13 | Full test suite green | exit 0 |
| AC.CP2.14 | scope-violation grep | SCOPE_OK |
| AC.CP2.15 | Manual smoke (logged in close): stack switch + routing change + probe button each work end-to-end on local dev | Captured in commit body |

---

## §5 — Test minimums

- Write endpoints: ≥24 cases (3 per endpoint × 8 endpoints).
- Probe + smoke: ≥10 cases.
- ModelDropdown: ≥8 cases (spec filter, sort, MARSYS flat-list, pending badge).
- ParamOverrideRow: ≥6 cases (debounce, reset, validation).
- CostConfirmDialog: ≥4 cases (trigger threshold, Anthropic always, dismiss, confirm).

Total ≥ 52 new tests.

---

## §6 — Session close

Standard. Final commit `feat(aiops-CP.2): full interactive Control Panel + probes`.
Rotate CLAUDECODE_BRIEF.md → PHASE_CP_3_BRIEF.md.

---

## §7 — BAIL OUT triggers (CP.2 specific)

- Probe endpoint hangs on a particular provider (timeout not respected).
- Streaming pattern in this codebase differs from what the brief assumes — if
  the existing `/consume` SSE machinery isn't reusable for probe streaming,
  BAIL OUT and let native decide.
- A live provider catalog returns 401 for all five providers (env var
  configuration issue) — write the catalog handlers anyway but BAIL on AC.CP2.4
  because the dropdown will be empty.

---

*End of PHASE_CP_2_BRIEF.md*
