---
status: OPEN
session_id: AIOPS_CP_1
phase: CP.1
phase_name: "DB migrations + catalog discovery + runtime_config + read-only UI"
next_session: AIOPS_CP_2
authored_at: 2026-05-13
authored_by: AIOPS_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CP_1
## AIOps Phase 1, Step 1 — Foundation layer

---

## §0 — Executor orientation

CP.1 builds the foundation: five DB tables, the live catalog discovery
service, the per-call-type specs, the runtime_config resolver, the MARSYS
stack registration, the CallType taxonomy extension, and a **read-only**
Control Panel UI that displays the current state without allowing edits.

All write functionality lands in CP.2.

The umbrella feature flag `AIOPS_OVERRIDES_ENABLED` is **created and set to
`false`** in this phase. With the flag false, the system behaves identically
to today.

Read `00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md` in full.
Read `00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md §3, §4, §5, §7, §8`.

---

## §1 — Mandatory reads

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md (full)
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md (full)
4.  platform/src/lib/models/registry.ts (existing taxonomy)
5.  platform/src/lib/models/resolver.ts (existing provider-options pattern)
6.  platform/src/lib/db/schema/observatory.ts (table conventions)
7.  platform/supabase/migrations/  — list the latest migration number
8.  platform/src/lib/config/feature_flags.ts (where the flag lands)
9.  platform/src/lib/llm/providers/{nim,deepseek,gemini,openai,anthropic}_observed.ts
    (existing provider clients — reuse their HTTP machinery)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/aiops/**                      # primary work
platform/src/lib/models/registry.ts            # extend CallType, ModelStack, STACK_ROUTING
platform/src/lib/models/runtime_config.ts      # NEW
platform/src/lib/config/feature_flags.ts       # add AIOPS_OVERRIDES_ENABLED
platform/src/lib/db/schema/aiops.ts            # NEW
platform/supabase/migrations/**                # 5 new migrations
platform/src/app/(super-admin)/aiops/control/page.tsx   # replace stub with read-only UI
platform/src/lib/components/aiops/**           # new components
platform/src/app/api/admin/aiops/state/route.ts          # GET only (read-only API)
platform/src/app/api/admin/aiops/_guard.ts               # mirror observatory _guard pattern
platform/src/app/api/admin/aiops/_parse.ts               # zod schemas, request parsing
CLAUDECODE_BRIEF.md
```

### must_not_touch
(same as CP.0 plus: `platform/src/app/api/admin/observatory/**`,
`platform/src/lib/components/observatory/**`)

---

## §3 — Work plan

### 3.1 — Feature flag

Add to `platform/src/lib/config/feature_flags.ts`:
```ts
export const AIOPS_OVERRIDES_ENABLED =
  process.env.AIOPS_OVERRIDES_ENABLED === 'true'
```
Default: `false`. Flipped in CP.5.

### 3.2 — Registry extensions

Edit `platform/src/lib/models/registry.ts`:

1. Extend `CallType`:
   ```ts
   export type CallType =
     | 'synthesis'
     | 'planner_deep'
     | 'planner_fast'
     | 'context_assembly'
     | 'worker'
     | 'eval_judge'
     | 'eval_generator'
     | 'smoke_synth'
     | 'checkpoint_4_5'
     | 'checkpoint_5_5'
     | 'checkpoint_8_5'
   ```

2. Extend `ModelStack`:
   ```ts
   export type ModelStack = 'nim' | 'anthropic' | 'gemini' | 'gpt' | 'deepseek' | 'marsys'
   ```

3. Extend `STACK_LABEL` + `STACK_PRIMARY_PROVIDER` with the MARSYS entries:
   ```ts
   marsys: 'MARSYS Stack',
   // STACK_PRIMARY_PROVIDER['marsys'] — not applicable; comment-only
   ```

4. Extend `STACK_ROUTING` per Execution Rule R13:
   - For each of the 5 existing stacks, add the 6 new call-type rows
     (`eval_judge`, `eval_generator`, `smoke_synth`, `checkpoint_4_5/5_5/8_5`)
     using the seed values in R13.
   - Add a complete `STACK_ROUTING['marsys']` block with safe defaults:
     synthesis → `gemini-2.5-pro` / `deepseek-v4-pro`; planner_deep →
     `gemini-2.5-flash` / `deepseek-v4-pro`; planner_fast →
     `gemini-2.5-flash-lite` / `gemini-2.5-flash`; context_assembly →
     `gemini-2.5-flash` / `gemini-2.5-pro`; worker →
     `gemini-2.5-flash-lite` / `gpt-4.1-nano`; eval/smoke/checkpoint per R13.

5. Add `stackPicker()` MARSYS handling (the function already iterates stacks;
   confirm MARSYS appears with synthesisContextWindow from `gemini-2.5-pro`).

### 3.3 — DB migrations

Create five additive migrations, numbered sequentially after the latest in
`platform/supabase/migrations/`:

```
00XX_aiops_stack_config.sql
00XX_aiops_routing_override.sql
00XX_aiops_param_override.sql
00XX_aiops_model_health.sql
00XX_aiops_config_audit.sql
00XX_aiops_catalog_snapshot.sql
```

(That's six migrations; one per table.) Schema per AIOPS_MASTER_PLAN §8.
Each migration has matching up + down SQL.

Seed migration: a 7th migration `00XX_aiops_seed.sql` that:
- Inserts `llm_stack_config(scope='global', active_stack='gemini', updated_by='system')`
- Inserts `llm_stack_routing_override` rows for the MARSYS stack only (every
  call type × primary/fallback from §3.2.4). Other stacks remain empty
  (resolver falls back to registry).

After authoring, run:
```bash
cd platform
npx supabase db reset --local   # apply all migrations on the local test DB
# Confirm all tables exist:
psql $LOCAL_TEST_DATABASE_URL -c "\dt llm_*"
```

All six tables should appear.

### 3.4 — Catalog discovery service

Create the directory tree under `platform/src/lib/aiops/catalog/` per
AIOPS_MASTER_PLAN §5.2.

Implement per-provider fetchers:

- `fetcher_nim.ts` — `GET https://integrate.api.nvidia.com/v1/models` with
  `Bearer ${NVIDIA_NIM_API_KEY}`. Parse `{ data: [{ id, owned_by }] }`.
- `fetcher_gemini.ts` — `GET https://generativelanguage.googleapis.com/v1beta/models?key=${GOOGLE_API_KEY}`.
  Parse `{ models: [{ name, inputTokenLimit, outputTokenLimit, supportedGenerationMethods }] }`.
  Strip the `models/` prefix from `name`.
- `fetcher_deepseek.ts` — `GET https://api.deepseek.com/models` with
  `Bearer ${DEEPSEEK_API_KEY}`.
- `fetcher_openai.ts` — `GET https://api.openai.com/v1/models` with
  `Bearer ${OPENAI_API_KEY}`. Filter to `gpt-*` models in the response (the
  endpoint returns embeddings + Whisper + DALL-E too).
- `fetcher_anthropic.ts` — `GET https://api.anthropic.com/v1/models` with
  `x-api-key: ${ANTHROPIC_API_KEY}`, `anthropic-version: 2023-06-01`.

Each fetcher:
- Times out at 15s.
- Returns `{ status: 'ok' | 'auth_fail' | 'timeout' | 'error', models: CatalogEntry[], raw: any, fetched_at: string }`.
- Redacts API keys from any logged error.

Implement `augment.ts`:
- Takes raw entries from a fetcher.
- For each entry: if `model_id` is in `MODELS` from registry → use registered metadata.
  Else: look up `platform/src/lib/aiops/catalog/metadata/<provider>.json` for the entry.
  Else: mark `[METADATA_PENDING]` with `contextWindow=null`, `paramCount=null`.

Implement `cache.ts`:
- In-memory cache keyed by provider, TTL 6h.
- On cache miss → call fetcher → on success update cache + write to
  `llm_catalog_snapshot` row.
- On fetcher failure → return last-known-good from cache or from
  `llm_catalog_snapshot`, with `stale: true`.

Create curated `metadata/<provider>.json` for each of the 5 providers,
seeded with known-good entries from the existing registry plus a few
plausible new ones. For NIM specifically, include entries for
`deepseek-ai/deepseek-v4-pro` (in case it comes back online), GLM-style
models, and the active Nemotron variants.

### 3.5 — Call-type specs

Create `platform/src/lib/aiops/specs/call_type_specs.ts` per
AIOPS_MASTER_PLAN §5.3 — full `CALL_TYPE_SPECS` constant.

Implement a helper:
```ts
export function filterCatalogForCallType(
  entries: CatalogEntry[],
  callType: CallType,
): CatalogEntry[]
```
Filters by mandatory; sorts by preferred + secondary.

### 3.6 — runtime_config.ts

Create `platform/src/lib/models/runtime_config.ts` per AIOPS_MASTER_PLAN §7.1.

- `getEffectiveStack(req?: Request): Promise<ModelStack>`
- `getEffectiveModel(stack, callType, role, req?): Promise<string>`
- `getEffectiveParam<T>(stack, callType, paramName, fallback, req?): Promise<T>`
- `invalidateRuntimeConfigCache(): void`

Internal:
- 60s in-memory cache with manual invalidation.
- DB queries via the existing Drizzle/pg connection.
- When `AIOPS_OVERRIDES_ENABLED=false`, ALL functions short-circuit to the
  registry — DB is not consulted. This preserves byte-identical behavior
  during CP.1–CP.4.

Tests in `platform/src/lib/models/__tests__/runtime_config.test.ts`:
- Resolver priority order (per-request → user → DB → registry) — at least 8 cases.
- Flag-off behavior is identical to registry.
- Cache TTL + invalidation correctness.

### 3.7 — DB schema (Drizzle / typed access)

Create `platform/src/lib/db/schema/aiops.ts` with Drizzle table definitions
matching the SQL migrations from §3.3. Export from
`platform/src/lib/db/schema/index.ts`.

### 3.8 — Read-only API

Create `platform/src/app/api/admin/aiops/_guard.ts` — copy of observatory's.

Create `platform/src/app/api/admin/aiops/state/route.ts`:
- `GET` only.
- Returns:
  ```ts
  {
    active_stack: ModelStack,
    effective_routing: Record<ModelStack, Record<CallType, { primary, fallback }>>,
    effective_params: Record<ModelStack, Record<CallType, Record<string, unknown>>>,
    health_summary: Record<string /* model_id */, 'pass' | 'fail' | 'stale' | 'never_probed'>,
    audit_summary: { count: number, latest_at: string | null }
  }
  ```

Tests under `__tests__/`. Auth gate: 401 for non-super-admin; 200 with state for super-admin.

### 3.9 — Read-only Control Panel UI

Replace the CP.0 stub at `platform/src/app/(super-admin)/aiops/control/page.tsx`
with a read-only state view:

- Stack picker row (6 cards including MARSYS) — selected state derived from
  `active_stack`; clicks are noop (write lands in CP.2; show a tooltip
  "Selection editable in CP.2").
- For the selected stack: render the pipeline call type rows (5) with the
  current primary + fallback model IDs as plain text (no dropdown yet).
- Quality & Verification section with the 6 cross-stack call types as plain text.
- Right rail: "Recent Changes" empty state ("No edits yet — write side lands in CP.2");
  "Health Status" empty state ("Health probes start in CP.4").

New components under `platform/src/lib/components/aiops/`:
- `StackPickerCards.tsx` — 6 cards, derived from `stackPicker()` + MARSYS handling.
- `CallTypeRow.tsx` — read-only row (label + primary + fallback + spec note).
- `EmptyRightRail.tsx` — placeholder for Recent Changes + Health.

All styled via existing Tailwind tokens; no new colors / fonts.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CP1.1 | `grep "AIOPS_OVERRIDES_ENABLED" platform/src/lib/config/feature_flags.ts` | match |
| AC.CP1.2 | `grep "'marsys'" platform/src/lib/models/registry.ts` | ≥2 matches (type + STACK_ROUTING) |
| AC.CP1.3 | `grep "'eval_judge'" platform/src/lib/models/registry.ts` | match |
| AC.CP1.4 | `ls platform/supabase/migrations/*aiops*.sql \| wc -l` | ≥6 |
| AC.CP1.5 | `psql $LOCAL_TEST_DATABASE_URL -c "\dt llm_stack_config llm_stack_routing_override llm_param_override llm_model_health llm_config_audit llm_catalog_snapshot"` | all 6 tables present |
| AC.CP1.6 | `test -f platform/src/lib/aiops/catalog/fetcher_nim.ts` | exit 0 (and 4 more fetchers) |
| AC.CP1.7 | `test -f platform/src/lib/aiops/specs/call_type_specs.ts` | exit 0 |
| AC.CP1.8 | `test -f platform/src/lib/models/runtime_config.ts` | exit 0 |
| AC.CP1.9 | `cd platform && npm run test -- runtime_config` | all pass, ≥8 cases |
| AC.CP1.10 | `cd platform && npm run test -- catalog` | all pass, ≥5 cases per fetcher (mocked) |
| AC.CP1.11 | `curl -s http://localhost:3000/api/admin/aiops/state -H "Cookie: <super-admin-cookie>"` | 200 + valid JSON shape |
| AC.CP1.12 | `cd platform && npm run typecheck` | exit 0 |
| AC.CP1.13 | `cd platform && npm run lint` | exit 0 |
| AC.CP1.14 | `cd platform && npm run test -- --run` | full suite exit 0 |
| AC.CP1.15 | Flag-off identity: with `AIOPS_OVERRIDES_ENABLED=false`, `getEffectiveModel('gemini','synthesis','primary')` === `STACK_ROUTING['gemini']['synthesis'].primary` | test asserts equality |
| AC.CP1.16 | scope-violation grep | SCOPE_OK |

---

## §5 — Test minimums

- runtime_config resolver: ≥12 tests.
- catalog fetcher modules: ≥5 tests each (mocked HTTP) = ≥25 total.
- spec filtering: ≥10 tests (mandatory + preferred edge cases).
- read-only API endpoint: ≥4 tests (auth, shape, MARSYS surfacing, empty-DB fallthrough).

Total new tests ≥ 51. Pre-existing suite must still pass.

---

## §6 — Session close

Standard procedure per R4 + R5:

1. Final commit message:
   ```
   feat(aiops-CP.1): foundation — schema, catalog, runtime_config, read-only UI

   - 6 new DB tables + Drizzle schema + seed migration
   - CallType extended with eval/smoke/checkpoint (6 new types)
   - ModelStack extended with MARSYS (6th stack with cross-provider routing)
   - Live catalog fetchers for 5 providers + augmentation + 6h cache
   - CALL_TYPE_SPECS with mandatory + preferred filtering
   - runtime_config.ts resolver (per-request → user → DB → registry)
   - GET /api/admin/aiops/state read-only endpoint
   - Read-only Control Panel UI at /aiops/control
   - Feature flag AIOPS_OVERRIDES_ENABLED (default false; flag-off is identity)
   - ≥51 new tests; full suite green

   AC summary: 16/16 PASS
   ```

2. Rotate CLAUDECODE_BRIEF.md → contents of `PHASE_CP_2_BRIEF.md`.

3. Report `[AIOPS-CLOSE] phase=CP.1 status=CLOSED next_phase=CP.2`.

---

## §7 — BAIL OUT triggers (CP.1 specific)

- Migration apply fails on the local DB (schema conflict, syntax error).
- Any provider's catalog endpoint structure changed and the fetcher cannot be
  written without guessing — BAIL OUT and let the native confirm the
  endpoint shape.
- runtime_config tests reveal a logical inconsistency in the priority order
  documented in AIOPS_MASTER_PLAN §7.1.
- `STACK_ROUTING['marsys']` cannot be added because of an unrelated type
  constraint somewhere in the codebase.

---

*End of PHASE_CP_1_BRIEF.md*
