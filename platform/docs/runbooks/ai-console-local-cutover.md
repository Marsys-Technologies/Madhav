# AI Console local cutover

This runbook is the owner-operated boundary between an additive local build and retirement of the shared-key user route. Code, mocked contracts, a successful build, or a skipped browser test are not cutover acceptance.

## Safety boundary

- Use only a disposable local database whose name starts with `ai_console_test_` on `localhost`, `127.0.0.1`, or `::1`.
- Use a disposable authenticated Madhav test user. Do not use a production account, shared database, Cloud SQL proxy, or production credential.
- Never pass credentials on a command line, commit them, paste them into a report, or enable Playwright screenshot, trace, or video capture while a credential is entered.
- Provider probes may incur a small charge. Set the provider smoke authorization only after the owner has approved those calls.
- CLI qualification may consume subscription allowance. It is local-only and separately requires provider-terms/account authorization before any public multi-user use.
- Do not run login commands or change CLI configuration from this procedure.

## 1. Prepare local encryption and flags

Create two distinct random 32-byte values and encode each once as canonical base64. Store them only in the local secret environment:

- `MARSYS_AI_ACTIVE_KEK_VERSION=V1`
- `MARSYS_AI_KEK_V1=<canonical base64 of exactly 32 random bytes>`
- `MARSYS_AI_FINGERPRINT_SECRET=<different canonical base64 of exactly 32 random bytes>`

Keep both feature flags false while preparing the database:

- `MARSYS_FLAG_AI_CONSOLE_BYOK=false`
- `NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK=false`

Apply migration `1120_ai_console_byok_routing.sql` only to the approved disposable database, then run:

```text
RUN_DB_TESTS=1 DATABASE_URL=postgresql://...@127.0.0.1:5432/ai_console_test_<name> npm run test -- src/lib/ai-console/__tests__/migration_db.test.ts src/lib/ai-console/__tests__/repository_isolation.db.test.ts
```

The database lane is `UNQUALIFIED` unless both the local host and `ai_console_test_` database-name boundary are satisfied.

## 2. Prepare the private browser fixture

Create an absolute-path JSON file outside the repository, readable only by the owner. It supplies the disposable user ID, an existing disposable conversation, the Paripraśna URL for that conversation, owner-supplied provider credentials, two credentials for the same provider, a minimal valid Consult request, and—only when separately available—authenticated MCP bridge details. Never put this file in the repository or a test artifact directory. Use this shape; replace every placeholder locally and omit any provider or MCP entry that is not authorized:

```json
{
  "userId": "<disposable-user-id>",
  "conversationId": "<disposable-conversation-uuid>",
  "pariprashnaPath": "/clients/<client-id>/pariprashna?conversation=<conversation-uuid>",
  "providers": {
    "openai": { "apiKey": "<private>", "preferredModel": "<optional-model-id>" },
    "anthropic": { "apiKey": "<private>" },
    "google": { "apiKey": "<private>" },
    "xai": { "apiKey": "<private>" },
    "deepseek": { "apiKey": "<private>" },
    "kimi": { "apiKey": "<private>" },
    "openrouter": { "apiKey": "<private>" }
  },
  "sameProvider": {
    "providerId": "openai",
    "first": { "apiKey": "<private-first-credential>" },
    "second": { "apiKey": "<private-second-credential>" }
  },
  "consultRequest": { "<required-consult-field>": "<disposable-value>" },
  "mcp": {
    "url": "<local-authenticated-mcp-route>",
    "headers": { "<required-header>": "<private>" },
    "request": { "<required-request-field>": "<disposable-value>" }
  },
  "inspectionUrls": ["<optional-safe-observatory-or-audit-projection-url>"]
}
```

Set these local environment entries without printing their values:

- `SMOKE_SESSION_COOKIE`
- `AI_CONSOLE_E2E_OWNER_CONFIG_PATH` (absolute path to the private JSON file)
- `AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED=true` only when real provider probes are approved
- `AI_CONSOLE_CLI_SMOKE_AUTHORIZED=true` only when real subscription calls and the applicable terms are approved

Leave either authorization unset to produce an honest `UNQUALIFIED` row for that lane.

## 3. Owner onboarding

Start the local server with both feature flags set to true. Sign in as the disposable test user, open **AI Console**, and confirm it has exactly:

1. Provider connections
2. Custom configurations
3. Local CLIs

Manually add or validate the intended provider connections. Confirm authenticated discovery and the small generation probe complete, then explicitly choose one exact model or complete custom configuration as the default. No option is selected automatically.

For a local CLI, a super-admin must grant the exact `(user, CLI)` pair before the user validates it. A detected executable alone is not subscription qualification.

## 4. Run the evidence gates

From `platform/`, run the static and focused checks:

```text
npm run guard:migration-numbers
npx tsc --noEmit
npm run lint -- scripts/ai-console src/lib/ai-console src/app/api/ai-console src/components/ai-console src/components/pariprashna tests/e2e/ai-console
npx vitest run src/lib/ai-console src/app/api/ai-console src/app/api/pariprashna src/app/api/chat/consult src/app/api/mcp/prashna_ask
npm run pariprashna:gates
npm run pariprashna:gates:mobile
npm run ai-console:e2e
npm run build
npm run ai-console:audit-shared-keys
npm run ai-console:acceptance
```

The acceptance runner uses three states only:

- `PASS`: the behavior ran and its assertions passed.
- `FAIL`: the behavior ran and failed.
- `UNQUALIFIED`: a prerequisite was absent or no qualifying test executed.

Its exit code is `0` only when every row is `PASS`, `1` when any row is `FAIL`, and `2` when no row failed but at least one remains `UNQUALIFIED`. To write the safe machine-readable matrix under the already ignored `platform/verification/ai-console/` directory, set `AI_CONSOLE_ACCEPTANCE_JSON=true`. The report contains no command output, identities, secrets, prompts, completions, provider bodies, database rows, or cookies.

## 5. Inspect the real local behavior

With the disposable user, verify desktop and 390×844 mobile behavior without credential-entry capture:

- two same-provider connections remain distinguishable by connection name and exact model;
- direct default selection and all four custom roles work;
- configuration create, edit, duplicate, and delete work;
- a conversation on `Default` follows a changed global default on its next question;
- an explicit direct selection remains pinned;
- a picker change affects subsequent turns and is visible from another browser context;
- logged-in backend work resolves the user's default;
- MCP returns `madhav.evidence.v1` with external synthesis and no Madhav reading;
- each granted CLI validates, executes a permitted request, and stops after revocation;
- application projections, logs, Observatory/audit views, and generated artifacts contain no secret material.

## 6. Retirement decision

Do not retire the shared-key path unless every acceptance row is `PASS`, including all seven provider rows, all four CLI rows, the disposable database, authenticated browser flows, leakage inspection, build, and `route_graph_clean`.

The import-graph audit intentionally follows both flag branches. While legacy/shared-key imports remain reachable from a user-facing route, it exits non-zero and cutover is blocked. Do not add an allowlist for those paths. Retirement is a later reviewed change that deletes the user-facing legacy authority and then reruns this entire sequence.

## Rollback

Before genuine retirement, a local rollback may set both AI Console flags back to false. Preserve all AI Console data and do not rewrite defaults or conversations. After public cutover, rollback must fail closed; it may not silently restore shared-key user routing. Credential deletion, key rotation, deployment, and production database changes are separate owner-authorized operations and are not part of this runbook.
