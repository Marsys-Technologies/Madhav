# AI Console, BYOK, and User-Directed Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every active Madhav user a secure AI Console for validated provider keys, named four-role configurations, and administrator-authorized local CLIs, then route Paripraśna, authenticated backend work, and MCP through that user's explicit default or conversation choice without silent fallback.

**Architecture:** Add an encrypted, user-owned AI configuration data plane and one server-only routing resolver. Provider and CLI adapters implement a common role-execution contract; the resolver turns `Default` or an explicit conversation choice into a safe immutable routing snapshot plus non-serializable execution handles for Synthesizer, Planner, Deep Planner, and Worker. AI Console and the Paripraśna picker read only safe catalog projections. Existing shared-key stack routing remains behind the local cutover flag until acceptance, but it is never used as a fallback when BYOK routing is enabled.

**Tech Stack:** Next.js 16.2 App Router, React 19, TypeScript, PostgreSQL via `pg`, Node `crypto` AES-256-GCM, Vercel AI SDK 6 provider factories, fixed-command local CLI subprocesses, React Query, Zod, Vitest, Testing Library, Playwright, existing Madhav/Paripraśna CSS tokens and AppShell components.

**Spec:** `docs/superpowers/specs/2026-09-27-ai-console-byok-routing-design.md`

## Global Constraints

- Implement behind `MARSYS_FLAG_AI_CONSOLE_BYOK` and `NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK`; default both to `false`. Flag-off behavior remains byte-compatible until local cutover.
- Read the relevant installed Next.js 16 guides under `node_modules/next/dist/docs/` before writing App Router, route-handler, or caching code.
- Create migration `1071_ai_console_byok_routing.sql` only if `npm run migration:next` still returns `1071`; otherwise use the returned free number and update this plan's path references in the implementation commit.
- Use the `create-migration` skill for the migration and dispatch the required `migration-guard` reviewer after the file exists.
- Never persist, return, snapshot, audit, trace, or log plaintext credentials, wrapped keys, nonces, tags, CLI auth material, full provider error bodies, prompts, or completions from validation probes.
- Keep decryption and executable routing types in `server-only` modules. Client/API types contain identifiers, masks, validation state, and safe metadata only.
- Exactly four roles exist: `synthesizer`, `planner`, `deep_planner`, `worker`. Do not add Inspector anywhere.
- A transient retry may repeat the same exact execution target. It may not switch provider, connection, model, configuration, CLI, or role assignment.
- `Default` is a live pointer. Explicit direct/CLI choices stay pinned. Named custom configurations are live references, while every submitted question stores an immutable safe resolved snapshot.
- AI Console contains exactly Provider connections, Custom configurations, and Local CLIs. A default radio/action lives on usable model/configuration rows; there is no fourth Default section.
- Reuse `AppShell`, `.pp-root` tokens, Paripraśna picker/sheet behavior, typography, gold hairlines, ink surfaces, focus rings, reduced-motion behavior, and 8-point rhythm. Preserve the compact composer and do not create a generic settings-dashboard visual language.
- Local CLI execution uses fixed allowlisted executable/argument arrays, stdin for model input, `shell: false`, a fresh isolated temporary directory, a stripped environment, hard timeout/output/concurrency limits, and cancellation. Never append user-supplied shell arguments.
- Subscription-backed CLI sharing stays local-only unless a separately recorded provider-terms approval enables it. Public deployment must fail closed for CLI use.
- Do not import, delete, rotate, or reveal existing environment keys. After acceptance, user-facing routes must prove they no longer read them.

## Review Focus

- Credential isolation, encryption key rotation, redaction, ownership checks, and dependency-safe deletion.
- Exactly-one default semantics, live `Default`, pinned explicit choices, atomic configuration versioning, and immutable per-question snapshots.
- No hidden use of `DEFAULT_STACK_ID`, `getEffectiveModel`, environment credentials, cross-provider fallback, or legacy retry wrappers on a BYOK-enabled user path.
- Role fidelity across direct models, custom configurations, CLIs, native Paripraśna, background/user-bound work, and MCP's external-synthesis exception.
- MCP returns evidence and accountability only; it must not call or report Madhav synthesis.
- AI Console/Paripraśna visual parity, keyboard use, mobile sheets, screen-reader status, visible focus, and fixed composer geometry.
- Honest qualification: mocked provider/CLI tests are not real-key or real-subscription acceptance.

---

## File Map

### Persistence and core contracts

| File | Action | Responsibility |
|---|---|---|
| `migrations/1071_ai_console_byok_routing.sql` | Create | Add encrypted connections, discovered models, named configurations/roles, defaults, CLI state/grants/catalog, conversation selections, turn snapshots, and safe audit events |
| `src/lib/ai-console/types.ts` | Create | Shared safe provider, role, choice, status, catalog, and snapshot types |
| `src/lib/ai-console/errors.ts` | Create | Stable configuration/validation/execution error codes and safe normalization |
| `src/lib/ai-console/crypto.ts` | Create | Versioned envelope encryption, keyed fingerprinting, masking, and redaction |
| `src/lib/ai-console/repository.ts` | Create | User-scoped persistence and atomic transactions |
| `src/lib/ai-console/audit.ts` | Create | Safe user configuration audit writer |
| `src/lib/admin/audit.ts` | Modify | Add per-user CLI grant/revoke actions |
| `src/lib/config/feature_flags.ts` | Modify | Register `AI_CONSOLE_BYOK` |

### Provider validation and execution

| File | Action | Responsibility |
|---|---|---|
| `src/lib/ai-console/providers/types.ts` | Create | Discovery/probe/provider execution contracts |
| `src/lib/ai-console/providers/catalog-policy.ts` | Create | Text-model compatibility and four-role policy |
| `src/lib/ai-console/providers/openai-compatible.ts` | Create | Shared authenticated catalog/probe factory for OpenAI, xAI, DeepSeek, Kimi, OpenRouter |
| `src/lib/ai-console/providers/anthropic.ts` | Create | Anthropic discovery, probe, and model factory |
| `src/lib/ai-console/providers/google.ts` | Create | Gemini discovery, probe, and model factory |
| `src/lib/ai-console/providers/index.ts` | Create | Closed seven-provider registry |
| `src/lib/ai-console/execution/types.ts` | Create | Server-only role executor and safe descriptor contracts |
| `src/lib/ai-console/execution/provider-executor.ts` | Create | Per-request provider model execution using decrypted BYOK credentials |
| `src/lib/ai-console/execution/cli-executor.ts` | Create | Fixed-command CLI generation and tool-loop bridge |
| `src/lib/ai-console/execution/index.ts` | Create | Executor factory and same-target retry policy |
| `src/lib/adapters/types.ts` | Modify | Accept an injected runtime model binding without exposing secrets |
| `src/lib/adapters/raw.ts` | Modify | Prefer the injected runtime binding over registry/environment resolution |
| `src/lib/adapters/dispatcher.ts` | Modify | Map xAI/Kimi/OpenRouter to the OpenAI-compatible adapter family |
| `src/lib/models/registry.ts` | Modify | Expand provider vocabulary only; do not hard-code discovered BYOK catalogs |

### Routing, APIs, and CLI governance

| File | Action | Responsibility |
|---|---|---|
| `src/lib/ai-console/routing.ts` | Create | Resolve defaults, explicit choices, configurations, grants, and safe snapshots |
| `src/lib/ai-console/validation.ts` | Create | Orchestrate connection validation states and catalog persistence |
| `src/lib/ai-console/revalidation.ts` | Create | Cache/schedule periodic checks and react to runtime auth/model failures |
| `src/lib/ai-console/cli/types.ts` | Create | CLI IDs, statuses, model catalog, and safe result types |
| `src/lib/ai-console/cli/registry.ts` | Create | Closed Codex/Claude Code/Gemini-Antigravity/Kimi Code command definitions |
| `src/lib/ai-console/cli/runner.ts` | Create | Hardened spawn wrapper with timeout, output, env, temp-dir, and concurrency guards |
| `src/lib/ai-console/cli/validation.ts` | Create | Installed/version/auth/noninteractive/model-discovery validation sequence |
| `src/app/api/ai-console/route.ts` | Create | Safe aggregate AI Console state |
| `src/app/api/ai-console/connections/route.ts` | Create | List/create named provider connections |
| `src/app/api/ai-console/connections/[id]/route.ts` | Create | Rename, replace credential, dependency preview, delete |
| `src/app/api/ai-console/connections/[id]/validate/route.ts` | Create | Explicit validation/revalidation |
| `src/app/api/ai-console/configurations/route.ts` | Create | List/create complete named four-role configurations |
| `src/app/api/ai-console/configurations/[id]/route.ts` | Create | Rename/edit/version/duplicate/delete configuration |
| `src/app/api/ai-console/default/route.ts` | Create | Atomically set one exact user default |
| `src/app/api/ai-console/clis/route.ts` | Create | List only granted CLI states/models |
| `src/app/api/ai-console/clis/[cliId]/validate/route.ts` | Create | Validate one authorized local CLI |
| `src/app/api/admin/cron/revalidate-ai-connections/route.ts` | Create | Authenticated background revalidation entry point |
| `src/app/api/admin/users/[id]/ai-cli-grants/route.ts` | Create | Super-admin list/grant/revoke per CLI |
| `src/app/api/conversations/[id]/ai-selection/route.ts` | Create | Read/update server-persisted `Default` or explicit conversation choice |

### AI Console and admin UI

| File | Action | Responsibility |
|---|---|---|
| `src/app/ai-console/layout.tsx` | Create | Active-user AppShell gate and breadcrumb |
| `src/app/ai-console/page.tsx` | Create | Server entry for AI Console |
| `src/components/ai-console/AIConsole.tsx` | Create | Three-section client shell and query invalidation |
| `src/components/ai-console/ProviderConnectionsSection.tsx` | Create | Named key entry, masked status, catalogs, test/delete/default controls |
| `src/components/ai-console/CustomConfigurationsSection.tsx` | Create | Named four-role configuration editor and rows |
| `src/components/ai-console/LocalClisSection.tsx` | Create | Granted CLI status, validation, models, and default controls |
| `src/components/ai-console/AiChoiceRadio.tsx` | Create | Shared exact-choice default control |
| `src/components/ai-console/ai-console.css` | Create | Minimal layout rules built on `.pp-root` tokens |
| `src/components/shared/AppShellRail.tsx` | Modify | Insert AI Console after Cockpit for super-admins and after Panchang for guests |
| `src/components/shared/MobileNavSheet.tsx` | Modify | Mirror responsive AI Console navigation |
| `src/components/nav/role-gates.ts` | Modify | Add active-user AI Console nav descriptor and tests |
| `src/components/admin/AdminClient.tsx` | Modify | Add AI Access tab |
| `src/components/admin/AiAccessTab.tsx` | Create | Per-user, per-CLI grant matrix |
| `src/components/admin/types.ts` | Modify | Add safe CLI grant view types |

### Paripraśna, pipeline, MCP, and observability

| File | Action | Responsibility |
|---|---|---|
| `src/components/pariprashna/composer/AiChoicePicker.tsx` | Create | Dynamic `Default`/direct/configuration/CLI picker using existing popover/sheet language |
| `src/components/pariprashna/composer/Composer.tsx` | Modify | Replace static model state with server choice; preserve Depth/Length and composer geometry |
| `src/components/pariprashna/composer/model_options.ts` | Modify | Retire static shared-key rows when BYOK flag is on |
| `src/components/pariprashna/hooks/useAiChoices.ts` | Create | Load safe choices and persist per-conversation selection |
| `src/components/pariprashna/hooks/useLiveStream.ts` | Modify | Submit selection identity, never raw provider/model trust data |
| `src/components/pariprashna/PariprashnaApp.tsx` | Modify | Bind conversation selection lifecycle |
| `src/components/pariprashna/state/types.ts` | Modify | Replace `modelId` control with `aiSelection` |
| `src/lib/pariprashna/pipeline/stage_context.ts` | Modify | Carry resolved four-role execution plan and safe snapshot |
| `src/lib/pariprashna/pipeline/safety_gate.ts` | Modify | Resolve the authenticated user's selection before limits/first LLM call |
| `src/lib/pariprashna/pipeline/plan_stage.ts` | Modify | Invoke Planner/Deep Planner executors without model fallback |
| `src/lib/pariprashna/pipeline/synthesis_stage.ts` | Modify | Invoke Synthesizer executor and route summarization through Worker |
| `src/lib/pariprashna/pipeline/persistence_stage.ts` | Modify | Persist routing snapshot and route interpretation/title work through Worker |
| `src/lib/pipeline/pipeline_planner.ts` | Modify | Accept an injected role executor; preserve legacy overload while flag is off |
| `src/lib/pariprashna/interpretation/worker.ts` | Modify | Accept the turn's Worker executor |
| `src/lib/pariprashna/summaries/worker.ts` | Modify | Accept the turn's Worker executor |
| `src/lib/conversations/title.ts` | Modify | Accept the turn's Worker executor |
| `src/app/api/pariprashna/route.ts` | Modify | Resolve once per turn and pass roles/snapshot through all stages |
| `src/app/api/chat/consult/route.ts` | Modify | Use the central resolver for the legacy authenticated door while it exists |
| `src/app/api/mcp/prashna_ask/route.ts` | Modify | Resolve mapped-user default, use internal roles only, remove Madhav synthesis, return evidence envelope |
| `src/lib/pipeline/prashna_ask_synthesis.ts` | Retain | Keep for non-MCP legacy callers only; prove MCP no longer imports it |
| `src/lib/ai-console/observability.ts` | Create | Safe role/provider/model/configuration metadata projection |
| `src/lib/db/monitoring-types.ts` | Modify | Add safe AI routing metadata fields where schema supports them |
| `src/lib/db/monitoring-write.ts` | Modify | Persist safe routing metadata and `fallback_used=false` |

---

## Task 1: Freeze safe contracts and the cutover flag

**Files:**
- Create: `src/lib/ai-console/types.ts`
- Create: `src/lib/ai-console/errors.ts`
- Modify: `src/lib/config/feature_flags.ts`
- Test: `src/lib/ai-console/__tests__/types.test.ts`
- Test: `src/lib/ai-console/__tests__/errors.test.ts`

- [ ] **Step 1: Write failing contract tests**

Cover closed provider/CLI/role sets, discriminated choice variants, rejection of Inspector, safe serialization, and stable public error codes.

```typescript
export const AI_ROLES = ['synthesizer', 'planner', 'deep_planner', 'worker'] as const
export const PROVIDER_IDS = ['openai', 'anthropic', 'google', 'xai', 'deepseek', 'kimi', 'openrouter'] as const
export const CLI_IDS = ['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'] as const

export type AiChoiceRef =
  | { kind: 'provider_model'; connectionId: string; modelId: string }
  | { kind: 'custom_configuration'; configurationId: string }
  | { kind: 'local_cli'; cliId: CliId; modelId: string | null }

export type ConversationAiSelection =
  | { kind: 'default' }
  | { kind: 'explicit'; choice: AiChoiceRef }
```

- [ ] **Step 2: Run the red tests**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/types.test.ts src/lib/ai-console/__tests__/errors.test.ts
```

Expected: FAIL because the modules do not exist.

- [ ] **Step 3: Implement safe types, Zod schemas, and error normalization**

Add `AI_CONSOLE_BYOK` to `FeatureFlag` and `DEFAULT_FLAGS` with `false`. Define stable codes including `AI_DEFAULT_REQUIRED`, `AI_CHOICE_BROKEN`, `AI_CONNECTION_INVALID`, `AI_MODEL_UNAVAILABLE`, `AI_ROLE_INCOMPATIBLE`, `AI_CLI_NOT_GRANTED`, `AI_CLI_UNREACHABLE`, and `AI_PROVIDER_UNREACHABLE`. Normalize provider/CLI errors without copying full upstream bodies.

- [ ] **Step 4: Run tests and typecheck**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/types.test.ts src/lib/ai-console/__tests__/errors.test.ts
cd platform && npx tsc --noEmit
```

Expected: PASS; no Inspector member and no secret-bearing field in safe schemas.

- [ ] **Step 5: Commit**

```bash
git add platform/src/lib/ai-console platform/src/lib/config/feature_flags.ts
git commit -m "feat(ai-console): define routing contracts and cutover flag"
```

---

## Task 2: Add the governed persistence model

**Files:**
- Create: `migrations/1071_ai_console_byok_routing.sql` (or the free number reported at execution time)
- Test: `src/lib/ai-console/__tests__/migration_contract.test.ts`
- Test: `src/lib/ai-console/__tests__/migration_db.test.ts`

- [ ] **Step 1: Run the migration-number guard**

```bash
cd platform && npm run migration:next
```

Expected: `1071`. If not, stop, use the reported number, and update plan references before continuing.

- [ ] **Step 2: Use the `create-migration` skill and write a failing contract test**

The test must require these relations and constraints:

- `ai_provider_connections`
- `ai_connection_models`
- `ai_custom_configurations`
- `ai_custom_configuration_roles`
- `ai_user_defaults`
- `ai_cli_installations`
- `ai_cli_models`
- `ai_cli_grants`
- `ai_conversation_selections`
- `ai_turn_routing_snapshots`
- `ai_configuration_audit_log`

The migration must include:

- case-insensitive unique connection/configuration names per user;
- validation-state and provider/role/choice `CHECK` constraints;
- one row per user in `ai_user_defaults`;
- four unique role rows per configuration, enforced by the repository transaction plus a deferred constraint trigger that rejects commit unless all four roles exist;
- one conversation selection per conversation, with owner matching `conversations.user_id` through a deferred trigger;
- no plaintext credential column;
- dependency-preserving foreign keys (`RESTRICT` for referenced choices, `CASCADE` only for owned child catalogs/audits where approved);
- indexes for user lists, status refreshes, defaults, grants, conversation lookup, and turn correlation;
- RLS enabled with service-only access because Firebase authorization is enforced server-side;
- idempotent DDL inside `BEGIN`/`COMMIT`.

- [ ] **Step 3: Run the red contract test**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/migration_contract.test.ts
```

Expected: FAIL until the migration exists.

- [ ] **Step 4: Implement the migration and DB behavior test**

The DB test must prove duplicate names fail, a fifth/unknown role fails, incomplete configurations cannot commit, two defaults cannot exist for one user, and cross-user conversation selection ownership fails.

- [ ] **Step 5: Run migration checks**

```bash
cd platform && npm run guard:migration-numbers
cd platform && npx vitest run src/lib/ai-console/__tests__/migration_contract.test.ts
cd platform && RUN_DB_TESTS=1 npx vitest run src/lib/ai-console/__tests__/migration_db.test.ts
```

Expected: static contract PASS; DB test PASS when the local test database is available, otherwise honestly reported as unqualified.

- [ ] **Step 6: Dispatch the required `migration-guard` review and address findings**

Review for safe numbering, idempotency, lock duration, FK behavior, deferred constraints, indexes, and rollback impact.

- [ ] **Step 7: Commit**

```bash
git add platform/migrations platform/src/lib/ai-console/__tests__
git commit -m "feat(ai-console): add BYOK routing persistence"
```

---

## Task 3: Implement envelope encryption and secret hygiene

**Files:**
- Create: `src/lib/ai-console/crypto.ts`
- Test: `src/lib/ai-console/__tests__/crypto.test.ts`
- Test: `src/lib/ai-console/__tests__/redaction.test.ts`

- [ ] **Step 1: Write failing tests**

Test AES-256-GCM round trip, random per-record data keys/nonces, authentication failure on tamper, old key-version decrypt/new active-version write, keyed fingerprint stability, safe mask generation, and recursive redaction of common credential/error fields.

Required server-only API:

```typescript
export interface EncryptedCredential {
  ciphertext: Buffer
  wrappedDataKey: Buffer
  nonce: Buffer
  authTag: Buffer
  keyVersion: string
  mask: string
  fingerprint: string
}

export function encryptCredential(plaintext: string): EncryptedCredential
export function decryptCredential(record: EncryptedCredential): string
export function redactAiSecret(value: unknown): unknown
```

Use versioned `MARSYS_AI_KEK_<VERSION>` secrets plus `MARSYS_AI_ACTIVE_KEK_VERSION`; fail closed if configuration is absent or malformed.

- [ ] **Step 2: Run red tests**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/crypto.test.ts src/lib/ai-console/__tests__/redaction.test.ts
```

- [ ] **Step 3: Implement without logging plaintext or cryptographic material**

Use `randomBytes(32)`, AES-256-GCM for the credential, and AES-256-GCM for data-key wrapping. Use HMAC-SHA-256 with a separate fingerprint secret. Zero temporary buffers where practical.

- [ ] **Step 4: Verify secret scanning tests**

Expected: PASS; snapshots and thrown errors contain only masks/fingerprints and stable codes.

- [ ] **Step 5: Commit**

```bash
git add platform/src/lib/ai-console/crypto.ts platform/src/lib/ai-console/__tests__
git commit -m "feat(ai-console): encrypt and redact user credentials"
```

---

## Task 4: Build user-scoped repositories, transactions, and safe audit

**Files:**
- Create: `src/lib/ai-console/repository.ts`
- Create: `src/lib/ai-console/audit.ts`
- Modify: `src/lib/db/client.ts`
- Modify: `src/lib/admin/audit.ts`
- Test: `src/lib/ai-console/__tests__/repository.test.ts`
- Test: `src/lib/ai-console/__tests__/repository_isolation.db.test.ts`

- [ ] **Step 1: Add a transaction helper with rollback tests**

```typescript
export async function withTransaction<T>(fn: (client: PoolClient) => Promise<T>): Promise<T>
```

Ensure connection release in `finally` and rollback on all failures.

- [ ] **Step 2: Write failing repository/isolation tests**

Cover user-scoped CRUD, atomic default replacement, four-role save/version increment, dependency preview before delete, live catalog invalidation, conversation selection ownership, immutable snapshot insert, CLI grant revocation, and safe audits.

- [ ] **Step 3: Implement repository methods**

Required entry points include:

```typescript
listAiConsoleState(userId)
createConnection(userId, input, encrypted)
replaceConnectionCredential(userId, connectionId, encrypted)
storeConnectionValidation(userId, connectionId, result)
saveConfiguration(userId, input)
setUserDefault(userId, choice)
setConversationSelection(userId, conversationId, selection)
previewChoiceDependencies(userId, choice)
insertRoutingSnapshot(snapshot)
```

Every SQL statement that touches user-owned data must include `user_id`/ownership in the predicate. Super-admin APIs manage grants only; they do not call decrypt/invoke methods for another user.

- [ ] **Step 4: Add audit actions**

User audit events cover connection created/renamed/replaced/validated/deleted, configuration created/edited/duplicated/deleted, and default changed. `admin_audit_log` gains `ai_cli_grant` and `ai_cli_revoke` only. Store identifiers and safe metadata, never credential/probe/provider-body content.

- [ ] **Step 5: Run tests**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/repository.test.ts
cd platform && RUN_DB_TESTS=1 npx vitest run src/lib/ai-console/__tests__/repository_isolation.db.test.ts
```

- [ ] **Step 6: Commit**

```bash
git add platform/src/lib/db/client.ts platform/src/lib/ai-console platform/src/lib/admin/audit.ts
git commit -m "feat(ai-console): add isolated configuration repositories"
```

---

## Task 5: Implement seven provider discovery and validation adapters

**Files:**
- Create: `src/lib/ai-console/providers/types.ts`
- Create: `src/lib/ai-console/providers/catalog-policy.ts`
- Create: `src/lib/ai-console/providers/openai-compatible.ts`
- Create: `src/lib/ai-console/providers/anthropic.ts`
- Create: `src/lib/ai-console/providers/google.ts`
- Create: `src/lib/ai-console/providers/index.ts`
- Create: `src/lib/ai-console/validation.ts`
- Create: `src/lib/ai-console/revalidation.ts`
- Create: `src/app/api/admin/cron/revalidate-ai-connections/route.ts`
- Test: `src/lib/ai-console/providers/__tests__/*.test.ts`

- [ ] **Step 1: Verify current official provider contracts before coding**

Use official provider documentation only. Record authenticated model-list endpoint, auth header/query convention, generation endpoint, timeout behavior, and minimal output-limit field for OpenAI, Anthropic, Gemini, xAI, DeepSeek, Moonshot/Kimi, and OpenRouter. Do not copy credentials or response bodies into the plan/repo.

- [ ] **Step 2: Write the shared adapter contract and red tests**

```typescript
export interface ProviderValidationAdapter {
  readonly providerId: ProviderId
  discover(apiKey: string, signal: AbortSignal): Promise<DiscoveredModel[]>
  probe(apiKey: string, model: DiscoveredModel, signal: AbortSignal): Promise<ProbeUsage>
  createRuntimeBinding(apiKey: string, model: DiscoveredModel): RuntimeModelBinding
}
```

Every provider test must cover valid catalog/probe, invalid key, no compatible models, entitlement/billing failure, rate limit, removed model, timeout/network failure, and redacted normalized output.

- [ ] **Step 3: Implement compatibility policy**

Exclude embedding/image/audio-only, retired, and unsupported protocol models. Retain safe labels, model IDs, context/output limits when reported, and role/tool/structured-output compatibility. Do not hard-code a provider's catalog into `models/registry.ts`.

- [ ] **Step 4: Implement adapters**

Use one OpenAI-compatible transport factory with closed provider-specific base URLs; users cannot supply a URL. Keep Anthropic and Gemini provider-native. Probe with a fixed prompt and tightly capped output; discard probe text.

- [ ] **Step 5: Implement validation orchestration**

State flow: `untested -> validating -> validated | needs_attention | invalid | unreachable`. Only a successful authenticated discovery plus tiny generation probe produces `validated`. Preserve previously confirmed validity on transient unreachable checks while exposing the latest reachability state.

- [ ] **Step 6: Implement conservative revalidation**

Add an authenticated cron route using the repository's existing admin-cron guard pattern. Revalidate only stale connections, cap batch size/concurrency, and use cache timestamps to avoid provider churn. Runtime authentication, entitlement, or model-removal errors enqueue/mark the exact connection for revalidation; transient network errors mark reachability without rewriting a previously confirmed credential as permanently invalid.

- [ ] **Step 7: Run provider contract tests**

```bash
cd platform && npx vitest run src/lib/ai-console/providers/__tests__
```

Expected: PASS with mocked HTTP; this does not count as real provider qualification.

- [ ] **Step 8: Commit**

```bash
git add platform/src/lib/ai-console/providers platform/src/lib/ai-console/validation.ts platform/src/lib/ai-console/revalidation.ts platform/src/app/api/admin/cron/revalidate-ai-connections
git commit -m "feat(ai-console): validate seven user-owned AI providers"
```

---

## Task 6: Add safe AI Console APIs

**Files:**
- Create: `src/app/api/ai-console/route.ts`
- Create: `src/app/api/ai-console/connections/route.ts`
- Create: `src/app/api/ai-console/connections/[id]/route.ts`
- Create: `src/app/api/ai-console/connections/[id]/validate/route.ts`
- Create: `src/app/api/ai-console/configurations/route.ts`
- Create: `src/app/api/ai-console/configurations/[id]/route.ts`
- Create: `src/app/api/ai-console/default/route.ts`
- Test: `src/app/api/ai-console/__tests__/routes.test.ts`
- Test: `src/app/api/ai-console/__tests__/authz.test.ts`

- [ ] **Step 1: Read installed Next.js route-handler guidance**

Read the relevant Next 16 route-handler/request/caching documentation under `platform/node_modules/next/dist/docs/`. Mark all credential/configuration routes dynamic and non-cacheable.

- [ ] **Step 2: Write failing route/auth tests**

Prove active authentication, disabled-account rejection, strict body schemas/unknown-field rejection, ownership isolation, safe response shapes, masked credentials, dependency conflict responses, validation charge disclosure, and no credential echo in errors.

- [ ] **Step 3: Implement routes**

Use `getServerUserWithProfile()` and require `status='active'`. Return the standard disabled-feature response while `AI_CONSOLE_BYOK` is off. Credential create/replace accepts plaintext only in the request body, encrypts immediately, and never places it in a returned object. Delete first returns/uses a dependency preview and rejects while a default/configuration/conversation reference remains.

- [ ] **Step 4: Run tests**

```bash
cd platform && npx vitest run src/app/api/ai-console/__tests__
```

- [ ] **Step 5: Commit**

```bash
git add platform/src/app/api/ai-console
git commit -m "feat(ai-console): expose secure configuration APIs"
```

---

## Task 7: Build the central default and conversation routing resolver

**Files:**
- Create: `src/lib/ai-console/routing.ts`
- Create: `src/lib/ai-console/execution/types.ts`
- Test: `src/lib/ai-console/__tests__/routing.test.ts`
- Test: `src/lib/ai-console/__tests__/routing_no_fallback.test.ts`

- [ ] **Step 1: Write failing resolver tests**

Cover:

- direct provider model resolves the same exact connection/model for all four roles;
- direct CLI resolves the same CLI/model for all four roles;
- custom configuration resolves four independent current assignments;
- adding or validating a first option does not auto-select a default;
- `Default` follows a later global default change;
- explicit direct/CLI selection remains pinned;
- named configuration edits affect later turns but not earlier snapshots;
- missing/broken/invalid/revoked/unreachable choices stop with stable errors;
- no alternative connection/model/provider/CLI is queried after failure;
- disabled users and ownerless jobs fail closed.

- [ ] **Step 2: Implement the server-only resolver API**

```typescript
export async function resolveUserRouting(input: {
  userId: string
  source: 'pariprashna' | 'consult' | 'mcp' | 'backend'
  selection: ConversationAiSelection
  conversationId?: string
  turnId: string
}): Promise<ResolvedExecutionPlan>

export function toSafeRoutingSnapshot(plan: ResolvedExecutionPlan): SafeRoutingSnapshot
```

`ResolvedExecutionPlan` may contain decrypted credential-backed runtime bindings but must be `server-only`, non-enumerable where feasible, and impossible to pass through `Response.json`. `SafeRoutingSnapshot` contains only role, provider/CLI, connection/configuration IDs, model IDs, configuration version, selection mode, and resolution time.

- [ ] **Step 3: Persist snapshots only after final resolution and before first LLM call**

Use the same `turnId`/query correlation as Paripraśna/MCP. Snapshot insertion is append-only/idempotent by correlation ID.

- [ ] **Step 4: Run tests**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/routing.test.ts src/lib/ai-console/__tests__/routing_no_fallback.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add platform/src/lib/ai-console/routing.ts platform/src/lib/ai-console/execution/types.ts platform/src/lib/ai-console/__tests__
git commit -m "feat(ai-console): resolve defaults and conversation choices"
```

---

## Task 8: Add provider-backed role execution without environment-key fallback

**Files:**
- Create: `src/lib/ai-console/execution/provider-executor.ts`
- Create: `src/lib/ai-console/execution/index.ts`
- Modify: `src/lib/adapters/types.ts`
- Modify: `src/lib/adapters/raw.ts`
- Modify: `src/lib/adapters/dispatcher.ts`
- Modify: `src/lib/models/registry.ts`
- Test: `src/lib/ai-console/execution/__tests__/provider-executor.test.ts`
- Test: `src/lib/adapters/__tests__/runtime_binding.test.ts`

- [ ] **Step 1: Write red tests around injected runtime bindings**

Prove an injected provider model is used without reading `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, `DEEPSEEK_API_KEY`, or related environment variables. Prove xAI/Kimi/OpenRouter dispatch through the OpenAI-compatible adapter while retaining their own safe provider identity in observability.

- [ ] **Step 2: Extend the adapter request contract**

Add a server-only `runtimeBinding` carrying a provider-created `LanguageModel`, dynamic safe metadata, and connection identity. When present, `streamAdapterRaw` must not call `getModelMeta` or construct the global provider singleton. Preserve the existing path when the BYOK flag is off.

- [ ] **Step 3: Implement `RoleExecutor`**

It must support structured generation, streaming text, tool definitions/tool calls, usage, cancellation, and same-target transient retry. It must expose a safe descriptor separately from the runtime binding.

- [ ] **Step 4: Run focused adapter tests**

```bash
cd platform && npx vitest run src/lib/ai-console/execution/__tests__/provider-executor.test.ts src/lib/adapters/__tests__/runtime_binding.test.ts src/lib/adapters/__tests__/providers
```

- [ ] **Step 5: Commit**

```bash
git add platform/src/lib/ai-console/execution platform/src/lib/adapters platform/src/lib/models/registry.ts
git commit -m "feat(ai-console): execute roles with per-user provider bindings"
```

---

## Task 9: Detect, validate, grant, and execute local CLIs safely

**Files:**
- Create: `src/lib/ai-console/cli/types.ts`
- Create: `src/lib/ai-console/cli/registry.ts`
- Create: `src/lib/ai-console/cli/runner.ts`
- Create: `src/lib/ai-console/cli/validation.ts`
- Create: `src/lib/ai-console/execution/cli-executor.ts`
- Create: `src/app/api/ai-console/clis/route.ts`
- Create: `src/app/api/ai-console/clis/[cliId]/validate/route.ts`
- Create: `src/app/api/admin/users/[id]/ai-cli-grants/route.ts`
- Test: `src/lib/ai-console/cli/__tests__/*.test.ts`
- Test: `src/app/api/admin/users/[id]/ai-cli-grants/__tests__/route.test.ts`

- [ ] **Step 1: Inspect the installed CLIs without mutating auth/config**

For Codex, Claude Code, Gemini/Antigravity, and Kimi Code, record executable path, `--version`, `--help`, noninteractive prompt mode, machine-readable output mode, model selection/discovery behavior, and cancellation behavior. Do not log tokens or run login commands. If a CLI cannot meet the contract, mark it honestly unsupported instead of inventing flags.

- [ ] **Step 2: Write fake-executable red tests**

Cover installed, missing, unsupported version, unauthenticated, noninteractive failure, malformed output, timeout, cancellation, output overflow, model discovery, built-in default, argument injection, environment stripping, temp-dir cleanup, and concurrency caps.

- [ ] **Step 3: Implement the closed command registry and runner**

Each registry entry owns fixed arrays for version, discovery, probe, and execution. The runner accepts only a `CliId`, an approved model ID, stdin text, and an abort signal. Use `spawn(executable, args, { shell: false, cwd: tempDir, env: allowlistedEnv })`.

- [ ] **Step 4: Implement CLI role execution**

For tool-capable loops, use a bounded server-side loop: request machine-readable tool calls, validate names/arguments against the existing authorized tool set, execute internally, then resume the same CLI/model with tool results. If an adapter cannot demonstrate the contract for all four roles, it is not selectable as a direct/default CLI choice.

- [ ] **Step 5: Implement grants and user-safe routes**

Grants are denied by default, separately stored per user/CLI, and rechecked immediately before every invocation. Revocation blocks the next call. The admin may grant/revoke but may not reveal CLI auth state beyond safe validated/unreachable metadata and may not invoke as another user.

- [ ] **Step 6: Run tests**

```bash
cd platform && npx vitest run src/lib/ai-console/cli/__tests__ 'src/app/api/admin/users/[id]/ai-cli-grants/__tests__/route.test.ts'
```

- [ ] **Step 7: Commit**

```bash
git add platform/src/lib/ai-console/cli platform/src/lib/ai-console/execution/cli-executor.ts platform/src/app/api/ai-console/clis platform/src/app/api/admin/users
git commit -m "feat(ai-console): add governed local CLI execution"
```

---

## Task 10: Build the native-looking AI Console and navigation

**Files:**
- Create: `src/app/ai-console/layout.tsx`
- Create: `src/app/ai-console/page.tsx`
- Create: `src/components/ai-console/AIConsole.tsx`
- Create: `src/components/ai-console/ProviderConnectionsSection.tsx`
- Create: `src/components/ai-console/CustomConfigurationsSection.tsx`
- Create: `src/components/ai-console/LocalClisSection.tsx`
- Create: `src/components/ai-console/AiChoiceRadio.tsx`
- Create: `src/components/ai-console/ai-console.css`
- Modify: `src/components/shared/AppShellRail.tsx`
- Modify: `src/components/shared/MobileNavSheet.tsx`
- Modify: `src/components/nav/role-gates.ts`
- Test: `src/components/ai-console/__tests__/AIConsole.test.tsx`
- Test: `tests/e2e/portal/ai-console.spec.ts`

- [ ] **Step 1: Write component tests from the approved information architecture**

Assert exactly three section headings, no “Default AI” section, one exact-choice radio per usable row, no automatic default selection, masked credentials, charge disclosure, validation states with text/icons (not color alone), four role labels only, provider-first/model-second configuration selectors, a **Use this model for every role** convenience action, and disabled Save until all four roles are valid.

- [ ] **Step 2: Build the AppShell route**

Gate to authenticated active users and the local feature switch. Super-admin order is Cockpit → AI Console → AIOps/Observatory; guest order is Panchang → AI Console. Hide the destination while the flag is off. Use one shared nav descriptor so rail/mobile tests cannot drift.

- [ ] **Step 3: Build the three sections using Paripraśna language**

Wrap the page in `.pp-root`; reuse ink/panel/raised surfaces, gold hairlines, Cormorant display, system-sans controls, mono metadata, 6/12px radii, restrained 150ms motion, existing focus treatment, and mobile bottom-sheet conventions. Use the default radio inside the relevant model/configuration row.

- [ ] **Step 4: Implement responsive and accessibility states**

Add labelled controls, field errors associated with inputs, status live regions, keyboard-operable menus/radios, focus restoration after dialogs, 44px mobile targets, reduced motion, and empty/loading/error states consistent with Paripraśna.

- [ ] **Step 5: Run component and portal tests**

```bash
cd platform && npx vitest run src/components/ai-console/__tests__/AIConsole.test.tsx
cd platform && npx playwright test tests/e2e/portal/ai-console.spec.ts --project=chromium
```

- [ ] **Step 6: Capture desktop/mobile visual evidence**

Capture provider, custom configuration, CLI, invalid-key, and broken-default states. Compare against the live Paripraśna composer/sheets, not a generic settings page.

- [ ] **Step 7: Commit**

```bash
git add platform/src/app/ai-console platform/src/components/ai-console platform/src/components/shared platform/src/components/nav platform/tests/e2e/portal/ai-console.spec.ts
git commit -m "feat(ai-console): add Pariprashna-native configuration UI"
```

---

## Task 11: Add the Admin AI Access grant surface

**Files:**
- Create: `src/components/admin/AiAccessTab.tsx`
- Modify: `src/components/admin/AdminClient.tsx`
- Modify: `src/components/admin/types.ts`
- Test: `src/components/admin/AdminClient.test.tsx`
- Test: `src/components/admin/__tests__/AiAccessTab.test.tsx`

- [ ] **Step 1: Write failing tab/grant tests**

Assert an `AI Access` tab, four separate CLI grant toggles per user, default-denied state, confirmation on revoke, no provider-key visibility, and audit refetch after mutation.

- [ ] **Step 2: Implement with existing admin patterns**

Reuse current tab bar, tables, brand tokens, React Query, and confirmation dialog. Do not mix provider credentials into Admin; only the user who owns a key can manage it.

- [ ] **Step 3: Run tests and commit**

```bash
cd platform && npx vitest run src/components/admin/AdminClient.test.tsx src/components/admin/__tests__/AiAccessTab.test.tsx
git add platform/src/components/admin
git commit -m "feat(admin): govern per-user local CLI access"
```

---

## Task 12: Persist the Paripraśna picker per conversation

**Files:**
- Create: `src/app/api/conversations/[id]/ai-selection/route.ts`
- Create: `src/components/pariprashna/composer/AiChoicePicker.tsx`
- Create: `src/components/pariprashna/hooks/useAiChoices.ts`
- Modify: `src/components/pariprashna/composer/Composer.tsx`
- Modify: `src/components/pariprashna/composer/model_options.ts`
- Modify: `src/components/pariprashna/hooks/useLiveStream.ts`
- Modify: `src/components/pariprashna/PariprashnaApp.tsx`
- Modify: `src/components/pariprashna/state/types.ts`
- Test: `src/components/pariprashna/composer/__tests__/AiChoicePicker.test.tsx`
- Test: `src/app/api/conversations/[id]/ai-selection/__tests__/route.test.ts`
- Test: `tests/pariprashna/gates/g-ai-choice.spec.ts`

- [ ] **Step 1: Write failing selection tests**

Prove new conversations begin with symbolic `Default`, selection persists server-side across browser sessions, picker changes affect only subsequent questions, global default changes move `Default` but not explicit choices, broken selections remain visible with remediation, and submission blocks when no valid default exists.

- [ ] **Step 2: Implement the ownership-checked selection route**

`GET` returns safe current selection plus resolved label/status. `PUT` accepts only `ConversationAiSelection`; it revalidates ownership/availability and stores the reference, not a credential or client-trusted provider/model tuple.

- [ ] **Step 3: Replace the static model picker**

Preserve order `AI → Depth → Length`, the existing pill, desktop popover, mobile sheet, keyboard semantics, and compact composer geometry. Keep the textarea fixed at three rows with internal vertical scrolling; do not carry forward or reintroduce autogrow behavior while touching this component. Display `Default — <resolved choice>`. Group explicit options as Provider connections, Custom configurations, and Local CLIs.

- [ ] **Step 4: Change request controls**

Replace `modelId?: string` with a selection identity/reference. The server ignores any client label/provider claim and resolves from persistence. Keep `reading_depth` and `length_tier` unchanged.

- [ ] **Step 5: Run focused and visual gates**

```bash
cd platform && npx vitest run src/components/pariprashna/composer 'src/app/api/conversations/[id]/ai-selection/__tests__/route.test.ts'
cd platform && npx playwright test tests/pariprashna/gates/g-ai-choice.spec.ts --config=tests/pariprashna/playwright.config.ts
cd platform && npm run pariprashna:gates:mobile -- --grep "AI choice"
```

- [ ] **Step 6: Commit**

```bash
git add platform/src/app/api/conversations platform/src/components/pariprashna platform/tests/pariprashna/gates/g-ai-choice.spec.ts
git commit -m "feat(pariprashna): persist user AI choice per conversation"
```

---

## Task 13: Route all four native Paripraśna roles through the resolved plan

**Files:**
- Modify: `src/app/api/pariprashna/route.ts`
- Modify: `src/lib/pariprashna/pipeline/stage_context.ts`
- Modify: `src/lib/pariprashna/pipeline/safety_gate.ts`
- Modify: `src/lib/pariprashna/pipeline/plan_stage.ts`
- Modify: `src/lib/pariprashna/pipeline/synthesis_stage.ts`
- Modify: `src/lib/pariprashna/pipeline/persistence_stage.ts`
- Modify: `src/lib/pipeline/pipeline_planner.ts`
- Modify: `src/lib/pariprashna/interpretation/worker.ts`
- Modify: `src/lib/pariprashna/summaries/worker.ts`
- Modify: `src/lib/conversations/title.ts`
- Modify: `src/app/api/chat/consult/route.ts`
- Test: `src/app/api/pariprashna/__tests__/ai_routing.test.ts`
- Test: `src/lib/pariprashna/pipeline/__tests__/ai_role_routing.test.ts`
- Test: `src/app/api/chat/consult/__tests__/ai_routing.test.ts`

- [ ] **Step 1: Write red role-routing tests**

Use four distinguishable fake executors. Prove the normal planner uses Planner, depth escalation uses Deep Planner, interpretation/summary/title use Worker, and final native prose uses Synthesizer. Prove direct choice uses one target for all roles and custom configuration uses four targets.

- [ ] **Step 2: Resolve once before limits/first LLM call**

`bindTurnParams` must stop accepting a client model ID as authority when BYOK is on. Resolve authenticated user + conversation selection into one execution plan, emit the safe model label on `turn.open`, evaluate limits against the exact resolved role models, and insert the immutable snapshot before the first LLM call.

- [ ] **Step 3: Refactor planner dependency injection**

Add an options object to `callPipelinePlanner` with `plannerExecutor` and `deepPlannerExecutor`. Keep the legacy positional overload only for flag-off callers. Remove primary/fallback model switching from the BYOK branch; one same-target transient retry remains inside the executor.

- [ ] **Step 4: Thread Worker and Synthesizer explicitly**

Pass Worker into durable summary, interpretation sets, and title generation. Pass Synthesizer into the streaming synthesis stage. Do not use module-global defaults inside a BYOK-enabled turn.

- [ ] **Step 5: Update legacy authenticated consult door**

While `/api/chat/consult` remains reachable, it must resolve the logged-in user's default/selection through the same service. Do not leave an alternate shared-key user-facing door.

- [ ] **Step 6: Run tests**

```bash
cd platform && npx vitest run src/app/api/pariprashna/__tests__/ai_routing.test.ts src/lib/pariprashna/pipeline/__tests__/ai_role_routing.test.ts src/app/api/chat/consult/__tests__/ai_routing.test.ts
cd platform && npx vitest run src/app/api/pariprashna/__tests__/route.test.ts src/lib/pariprashna/interpretation/__tests__/worker.test.ts src/lib/pariprashna/summaries/__tests__
```

- [ ] **Step 7: Commit**

```bash
git add platform/src/app/api/pariprashna platform/src/app/api/chat/consult platform/src/lib/pariprashna platform/src/lib/pipeline/pipeline_planner.ts platform/src/lib/conversations/title.ts
git commit -m "feat(pariprashna): route four AI roles through user choices"
```

---

## Task 14: Make MCP use the mapped user's default and return evidence only

**Files:**
- Modify: `src/app/api/mcp/prashna_ask/route.ts`
- Modify: `src/app/api/mcp/prashna_ask/__tests__/route.test.ts`
- Create: `src/app/api/mcp/prashna_ask/__tests__/ai_routing.test.ts`
- Create: `src/app/api/mcp/prashna_ask/__tests__/no_synthesis_import.test.ts`
- Modify: `src/lib/__tests__/mcp/primitives.test.ts`

- [ ] **Step 1: Write red MCP contract tests**

Prove the authenticated `x-mcp-user` mapping resolves that user's current default, Planner/Deep Planner/Worker execute, Synthesizer does not execute, `synthesizeReading` is not imported/called, raw primitives stay byte-compatible, and missing/broken default returns a stable configuration error.

- [ ] **Step 2: Define the terminal evidence envelope**

```typescript
interface McpEvidenceEnvelopeV1 {
  schema_version: 'madhav.evidence.v1'
  synthesis: { mode: 'external'; performed_by_madhav: false }
  question: string
  plan: unknown
  results: unknown[]
  completeness: unknown
  judgment_flags: string[]
  response_accountability: unknown
  routing: SafeMcpRoutingSummary // planner/deep_planner/worker only
}
```

Keep the existing NDJSON progress framing; change only the terminal high-level payload. Evidence-budget calculations must use a dedicated configured envelope budget, never the internal synthesis model context window.

- [ ] **Step 3: Remove high-level MCP synthesis**

Delete `synthesizeReading` and synthesis model resolution from `prashna_ask`. Preserve safety/entitlement/completeness/accountability behavior as structured data. Mark Observatory metadata as external synthesis rather than fabricating an internal synthesis event.

- [ ] **Step 4: Run MCP tests**

```bash
cd platform && npx vitest run src/app/api/mcp/prashna_ask/__tests__ src/lib/__tests__/mcp/primitives.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add platform/src/app/api/mcp/prashna_ask platform/src/lib/__tests__/mcp/primitives.test.ts
git commit -m "feat(mcp): use user defaults and return evidence for host synthesis"
```

---

## Task 15: Record safe routing metadata in Observatory and audit

**Files:**
- Create: `src/lib/ai-console/observability.ts`
- Modify: `src/lib/db/monitoring-types.ts`
- Modify: `src/lib/db/monitoring-write.ts`
- Modify: `src/lib/pariprashna/observability/synthesis_observation.ts`
- Test: `src/lib/ai-console/__tests__/observability.test.ts`
- Test: `src/lib/llm/__tests__/observability_redaction.test.ts`

- [ ] **Step 1: Write red metadata/redaction tests**

Require accountable user, source, role, provider/CLI, model, connection/configuration/version IDs, Default-vs-explicit, status, latency, usage/cost, retry count, and safe error class. Reject credentials, ciphertext fields, prompt/probe text, full upstream errors, and CLI auth paths/tokens.

- [ ] **Step 2: Implement one safe projection**

All writers receive `SafeRoutingSnapshot` or a role projection from it. Set `fallback_used=false` for BYOK calls. MCP records planner/deep/worker calls and an `external_synthesis=true` terminal marker only.

- [ ] **Step 3: Run tests and commit**

```bash
cd platform && npx vitest run src/lib/ai-console/__tests__/observability.test.ts src/lib/llm/__tests__/observability_redaction.test.ts
git add platform/src/lib/ai-console/observability.ts platform/src/lib/db platform/src/lib/pariprashna/observability
git commit -m "feat(observatory): record safe user AI routing metadata"
```

---

## Task 16: Prove local cutover and retire shared-key user routing

**Files:**
- Create: `scripts/ai-console/local_acceptance.ts`
- Create: `scripts/ai-console/shared_key_route_audit.ts`
- Create: `docs/runbooks/ai-console-local-cutover.md`
- Modify: `package.json`
- Modify: `.env.example` (or the governed local env template actually used by the repo)
- Test: `tests/e2e/ai-console/byok-routing.spec.ts`
- Test: `src/lib/ai-console/__tests__/shared_key_audit.test.ts`

- [ ] **Step 1: Add acceptance/audit scripts**

Add scripts that:

- scan user-facing route dependency graphs for environment-key/global-model resolution;
- create two same-provider connections and distinguish their models;
- validate/set a direct default;
- create/edit/duplicate/delete a four-role configuration;
- test Default live movement and explicit pinning;
- test CLI grant, validation, invocation, and revocation;
- test another browser/session on the same conversation;
- test logged-in backend default resolution;
- test MCP evidence-only behavior;
- scan logs, API payloads, snapshots, Observatory, audit, fixtures, and screenshots for secret leakage.

- [ ] **Step 2: Document the local cutover sequence**

The owner manually adds credentials or validates CLIs, selects one exact default, enables both flags locally, runs acceptance, and only then removes shared environment-key resolution from user-facing runtime code. Rollback may turn the local flag off while preserving new data; it may not authorize silent shared-key fallback in public use.

- [ ] **Step 3: Run the focused and broad gates**

```bash
cd platform && npm run guard:migration-numbers
cd platform && npx tsc --noEmit
cd platform && npm run lint -- src/lib/ai-console src/app/api/ai-console src/components/ai-console src/components/pariprashna
cd platform && npx vitest run src/lib/ai-console src/app/api/ai-console src/app/api/pariprashna src/app/api/mcp/prashna_ask
cd platform && npm run pariprashna:gates
cd platform && npm run pariprashna:gates:mobile
cd platform && npx playwright test tests/e2e/ai-console/byok-routing.spec.ts --project=chromium
cd platform && npm run build
```

Expected: all available local gates PASS. Any unavailable DB, provider credential, CLI subscription, or Firebase/build prerequisite is reported as unqualified, not passed.

- [ ] **Step 4: Run real authorized smoke qualification**

With user-provided test credentials and installed subscriptions, qualify all seven providers and four CLIs individually. Record only provider/CLI, model, timestamp, result, latency/usage, and safe error code. Do not commit keys, auth files, raw prompts, raw completions, or provider bodies.

- [ ] **Step 5: Inspect the running UI**

Verify AI Console desktop/mobile states, exact default controls, Paripraśna picker continuity, fixed composer geometry, keyboard navigation, screen-reader labels, focus rings, reduced motion, and visual parity with Paripraśna. Use screenshots as local evidence, not as proof of backend routing.

- [ ] **Step 6: Run whole-branch reviews**

Request fresh security, code, and migration reviews. Require explicit findings on secret leakage, command injection, cross-user access, no-fallback behavior, MCP external synthesis, and design-system parity.

- [ ] **Step 7: Commit acceptance assets**

```bash
git add platform/scripts/ai-console platform/docs/runbooks/ai-console-local-cutover.md platform/package.json platform/tests/e2e/ai-console platform/src/lib/ai-console/__tests__/shared_key_audit.test.ts
git commit -m "test(ai-console): add local BYOK cutover evidence"
```

---

## Spec Coverage Matrix

| Spec area | Implemented by |
|---|---|
| Seven providers, multiple named keys, authenticated discovery/probe | Tasks 2–6 |
| Encryption, masks, fingerprints, isolation, no reveal | Tasks 3–6, 15–16 |
| Four roles only, named configurations, versioning | Tasks 1–2, 4, 7, 13 |
| Mandatory exact default and broken-default handling | Tasks 2, 4, 7, 10, 12 |
| Codex/Claude/Gemini-Antigravity/Kimi CLIs and per-user grants | Tasks 2, 9, 11 |
| Paripraśna persistent picker, live Default, pinned explicit choice | Tasks 7, 10, 12–13 |
| Backend-without-picker uses authenticated user's default | Tasks 7, 13, 16 |
| MCP mapped-user default and external synthesis | Task 14 |
| No silent fallback and immutable question snapshots | Tasks 7–8, 12–16 |
| Observatory and audit without secrets | Tasks 4, 15–16 |
| Local-first shared-key retirement | Task 16 |
| Madhav/Paripraśna visual system | Tasks 10–12, 16 |

## Final Completion Evidence

Implementation is not complete merely because code, tests, or screenshots exist. The final handoff must distinguish:

- code-complete;
- mocked-contract-tested;
- database-tested;
- locally UI-tested;
- real-provider-qualified per provider;
- real-CLI-qualified per CLI;
- shared-key user-route audit clean;
- public CLI terms gate still pending or approved;
- deployed/live accepted (out of scope for this local-first plan unless separately authorized).
