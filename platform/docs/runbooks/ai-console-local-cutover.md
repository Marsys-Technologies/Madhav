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

Apply migrations `1124_ai_console_byok_routing.sql` and
`1125_ai_snapshot_shape_operator_precedence.sql`, in that order, only to the
approved disposable database, then run:

```text
RUN_DB_TESTS=1 AI_CONSOLE_TEST_DATABASE_URL=postgresql://...@127.0.0.1:5432/ai_console_test_<name> npm run test -- src/lib/ai-console/__tests__/migration_db.test.ts src/lib/ai-console/__tests__/repository_isolation.db.test.ts
```

The database lane is `UNQUALIFIED` unless the effective parsed PostgreSQL
target is an unambiguous loopback host and an `ai_console_test_*` database.
Do not add URI query parameters or libpq `host`, `hostaddr`, `service`, socket,
or equivalent overrides; the shared guard used by the runner and both database
test suites rejects those forms before a client can connect.

## 2. Prepare the private browser fixture

Create a regular, non-symlink JSON file outside both the repository and every
artifact directory. Its containing directories must be owner-only and the file
must have mode `0600`. The runner resolves its real path, verifies ownership and
permissions, and validates the complete schema before starting a browser; a
missing or malformed fixture is `UNQUALIFIED`. All HTTP targets, including the
base URL and optional MCP bridge, must parse as loopback-only HTTP(S) URLs.
Secret-bearing requests reject redirects instead of forwarding credentials to a
different origin.

The application currently has no public HTTP read route for immutable routing
snapshots, invocation receipts, or configuration audit rows. Therefore the
owner must expose a narrow, read-only, loopback local inspection helper over the
disposable database. It must return only the safe schema described below, scoped
to the exact disposable user and turn correlation. Do not expose prompts,
outputs, credentials, encryption material, arbitrary metadata, or raw errors.
The browser lane is `UNQUALIFIED` when these inspection URLs are absent.

Use this shape; replace every placeholder locally and omit only the optional MCP
entry when it is unavailable:

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
  "pariprashnaRequest": {
    "chartId": "<owned-disposable-chart-uuid>",
    "messages": [{ "id": "owner-test-question", "role": "user", "parts": [{ "type": "text", "text": "<approved-small-question>" }] }]
  },
  "consultRequest": { "<required-consult-field>": "<disposable-value>" },
  "inspection": {
    "identityUrl": "http://127.0.0.1:<port>/local-ai-acceptance/identity",
    "routingEvidenceUrlTemplate": "http://127.0.0.1:<port>/local-ai-acceptance/turn/{turnId}",
    "latestEvidenceUrl": "http://127.0.0.1:<port>/local-ai-acceptance/latest"
  },
  "leakage": {
    "serverLogPath": "/private/owner-only/server.log",
    "routingSnapshotPath": "/private/owner-only/routing-snapshots.json",
    "observatoryPath": "/private/owner-only/observatory.json",
    "auditPath": "/private/owner-only/audit.json",
    "artifactDirectory": "/private/owner-only/artifacts",
    "urls": ["http://127.0.0.1:<port>/api/ai-console", "http://127.0.0.1:<port>/api/admin/audit-log"]
  },
  "mcp": {
    "url": "http://127.0.0.1:<port>/<local-authenticated-mcp-route>",
    "headers": { "<required-header>": "<private>" },
    "request": { "<required-request-field>": "<disposable-value>" }
  }
}
```

For every exact turn, the routing inspection response must be a strict safe
object with `userId`, `correlationId`, persisted `selection`, exact
`resolvedChoice`, all four resolved `roles`, succeeded terminal invocation
receipts for the roles actually called, and exactly one matching Observatory
row for every such role, including Worker or Deep Planner when invoked, with
`fallbackUsed:false`. Extra or mismatched identities fail acceptance. The latest endpoint
accepts `conversationId` and `after` query parameters for Consult/CLI evidence.
The identity endpoint returns only `{ "userId": "<exact-disposable-user>" }`.
The four leakage files and artifact directory must already exist outside the
repository with owner-only permissions; every leakage input is mandatory.
The runner snapshots each file's inode, size, modification time, and byte
offset before the run. Every one must then contain a non-empty current-run
record or timestamp/correlation; an unchanged or stale `{}` is not evidence.

Set these local environment entries without printing their values:

- `SMOKE_SESSION_COOKIE`
- `AI_CONSOLE_E2E_OWNER_CONFIG_PATH` (absolute path to the private JSON file)
- `AI_CONSOLE_E2E_BASE_URL=http://127.0.0.1:<local-port>` (origin only)
- `AI_CONSOLE_E2E_EXTERNAL_SERVER=true` (the runner never starts a server or forwards the application database/Firebase environment)
- `AI_CONSOLE_E2E_ARTIFACT_DIR=/private/owner-only/artifacts` (must exactly match the fixture; the acceptance runner derives it after successful preflight)
- `AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED=true` only when real provider probes are approved
- `AI_CONSOLE_CLI_SMOKE_AUTHORIZED=true` only when real subscription calls and the applicable terms are approved

Leave either authorization unset to produce an honest `UNQUALIFIED` row for that lane. The acceptance runner passes subprocesses a minimal environment: only the database lane receives `AI_CONSOLE_TEST_DATABASE_URL`, and only browser lanes receive the session/fixture/authorization entries. Every command has a deadline; timeout terminates its detached process group with a bounded TERM/KILL sequence and records `FAIL`.
Real validation requests are globally throttled per user. The browser harness
sequences them and honors bounded `Retry-After` responses; a throttle generated
by the harness itself must not be mistaken for an invalid credential.

## 3. Owner onboarding

Start the local server with both feature flags set to true. Sign in as the disposable test user, open **AI Console**, and confirm it has exactly:

1. Provider connections
2. Custom configurations
3. Local CLIs

Manually add or validate the intended provider connections. Confirm authenticated discovery and the small generation probe complete, then explicitly choose one exact model or complete custom configuration as the default. No option is selected automatically. The disposable user must already have a restorable default because the current API has no clear-default operation; otherwise mutation lanes are `UNQUALIFIED`.

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
- direct, custom-configuration, moved-Default, and explicit-pinned selections each execute a real native turn through ordered `turn.open`, content, successful `turn.commit`, durable `turn.persisted`, and final `turn.close{status:"ok"}` with no error event;
- the exact immutable selection and all four resolved roles match the safe routing evidence; every actual invocation/Observatory row matches the expected provider/model or CLI and records `fallbackUsed:false`;
- configuration create, edit, duplicate, and delete work;
- a conversation on `Default` follows a changed global default on its next question;
- an explicit direct selection remains pinned;
- a picker change affects subsequent turns and is visible from another browser context;
- logged-in backend and CLI work consume a final semantic `finish{finishReason:"stop"}` with no error event and exact safe routing evidence; generic HTTP 2xx is insufficient;
- MCP returns `madhav.evidence.v1` with external synthesis and no Madhav reading;
- each granted CLI validates, executes a permitted request, and stops after revocation;
- application projections, current-run server-log deltas, routing snapshots/receipts, Observatory, audit outputs, safe URLs, and artifact directories contain no credential values, secret-bearing fields, broad credential formats, or credential-bearing screenshot/trace/video/HAR artifact;
- the authenticated UID equals the configured disposable user, the reserved test namespace begins clean, previous default/conversation/grants are restored, cleanup errors fail the test, and every test-created connection/configuration is verified deleted.

## 6. Retirement decision

Do not retire the shared-key path unless every acceptance row is `PASS`, including all seven provider rows, all four CLI rows, the disposable database, authenticated browser flows, leakage inspection, build, and `route_graph_clean`.

The import-graph audit intentionally follows both flag branches. While legacy/shared-key imports remain reachable from a user-facing route, it exits non-zero and cutover is blocked. Do not add an allowlist for those paths. Retirement is a later reviewed change that deletes the user-facing legacy authority and then reruns this entire sequence.

## Rollback

Before genuine retirement, a local rollback may set both AI Console flags back to false. Preserve all AI Console data and do not rewrite defaults or conversations. After public cutover, rollback must fail closed; it may not silently restore shared-key user routing. Credential deletion, key rotation, deployment, and production database changes are separate owner-authorized operations and are not part of this runbook.
