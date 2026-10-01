# Observatory consumption ledger

Release candidate, updated 2026-10-01. Production operations require the active scoped coordination lease and the reviewed protected release path. Consumption figures are not customer billing.

## Review location

Worktree: `/Users/Dev/.codex/worktrees/observatory-metering/Madhav`.
Branch: `codex/observatory-metering`; rebased on current `main` for the release PR.

## Product surfaces

- `/usage`: an active user's own consumption. Ownership is enforced by the server, including exports and drill-down queries.
- `/observatory`: when enabled, administrators receive the new consumption dashboard.
- `/observatory/metering`: administrator ledger, pricing and recovery operations.
- `/api/usage`: owner-scoped summary, events, breakdown, trace and CSV.
- `/api/admin/observatory/metering`: the same analysis across accounts, gated by active super-admin status and Observatory enablement.
- `/api/admin/observatory/metering/manage`: rate evidence, bounded recovery, catalog refresh and tiny owned-connection tests. POST rejects cross-site origins and admits three operations per minute per administrator per process. It is not a distributed global rate limit.

API views use `view=summary|events|breakdown|trace|export`; `from` inclusive and `to` exclusive are ISO timestamps. Periods are bounded to 90 days. Optional filters: channel, purpose, provider, model, conversationId, turnId; administrators may also filter userId. Group dimensions: day (UTC), channel, purpose, provider, model, role, conversation, turn and administrator-only user. Trace requires a conversation or turn. Pages are at most 1,000 rows and use `nextCursor`; CSV returns the next cursor in `X-Next-Cursor`. Group output is capped at 200; narrow filters when needed. Pagination preserves PostgreSQL microseconds.

## Enablement prerequisites

1. Recheck reserved migration number 1202 against current `main` before merge. The additive `supabase/migrations/1202_ai_metering_ledger.sql` creates protected public-schema objects. After green exact-SHA CI, dispatch `deploy.yml` with `ai_metering_schema_migration=true`; its temporary grant, exact `--only` application, and unconditional revoke must all succeed before routine migration and service promotion. Verify the file's hash in `_migrations_applied` and that public-schema CREATE was revoked. The ordinary runner refuses this file before the protected window.
2. Configure `AI_METERING_RECOVERY_BUCKET` as a dedicated private GCS bucket using the existing runtime service identity. Limit object permissions to the accounting server/operators and verify write/list/read/delete permissions with synthetic data before enabling. Do not set an object-retention hold that would prevent deletion after successful replay. No prompt, response, credential or arbitrary provider body is stored. Local development may instead set `AI_METERING_RECOVERY_DIR`; filesystem recovery is prohibited in production.
3. After the migration and recovery bucket are verified, set `MARSYS_FLAG_AI_METERING_ENABLED=true` on the server and verify its serving revision. It defaults off. The server refuses a provider call if start persistence or recovery configuration fails. A charged call's terminal receipt must persist to the database or recovery buffer before semantic success is exposed. A hard process termination can still leave an incomplete start; it remains visibly pending and becomes stale after 15 minutes.
4. The production image bakes `NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED=true` at build time to reveal navigation. This is visibility only, never an authorization gate. Administrator APIs additionally require `MARSYS_FLAG_OBSERVATORY_ENABLED=true`.
5. Import verified rate cards or refresh the official OpenRouter catalog through the administrator operations screen. Do not mistake enabling the flag for live provider verification.

The metering flag is independent of AI Console's BYOK flag. Shared model routing keeps its existing auth, model selection and credential handling. Attribution scope is established after existing route admission using admitted account/turn values. Shared backend SDK calls without authenticated request attribution fail closed when enabled; tests must use the administrator gateway or a trusted internal metering scope.

## What is recorded

Each AI SDK V3 `doGenerate`/`doStream` invocation has a durable start and immutable receipt. SDK tool-loop steps and retries are individual attempts. Role-level compatibility totals do not add a second charge. Lineage contains account, conversation, original customer turn (including fallback), operation, snapshot/connection/test-run where known, channel, purpose, payer, role and actual bound model. An unavailable parent operation is null rather than a fabricated relationship.

Nested usage records input totals, uncached input, cache reads/writes, output totals, text and reasoning subsets, source and numeric allowlisted raw evidence. Unknown counts remain null. Inconsistent or incomplete input partitions cannot produce a complete price. Output already includes reasoning in SDK V3 totals; it is charged once unless an explicitly separate rate card applies. All monetary calculations use integer decimal units at 12 USD decimal places. Tiny provider-reported numeric charges are normalized to the same precision.

Success, error, deadline timeout, cancellation and missing-finish states are distinct. Counts unavailable after failure/cancellation are never represented as zero. Pending starts and recovery failures remain visible. Recovery replay is bounded and idempotent; it validates envelopes, owner/model/context identity conflicts and mathematical cost consistency. Evidence tables deny update, delete and truncate. Browser roles receive no direct access; trusted server roles use RLS policies, with Firebase ownership enforced in APIs.

CLI adapters report a single client-reported aggregate because their internal transport is outside this server's control. Subscription usage receives no invented per-token cash charge. External MCP client synthesis is outside Madhav's observed usage and must not be added to the server total.

## Coverage and historical evidence

Current conversation doors covered: Pariprashna, Consult, Consult continuation, Build, and MCP prashna_ask. BYOK roles (planner/deep planner/worker/synthesizer) are tracked by the authenticated executor. Shared OpenAI, Anthropic, Google, DeepSeek and NIM adapter models plus direct continuation/Build and capability SDK models use the same transport seam. Owned connection validation probes are recorded as `validation`; administrator generation tests are `backend/admin_test` with server-generated test-run IDs and explicit charge acknowledgement.

Historical `llm_usage_events` stay visible as `legacy_aggregate`, with historical estimated cost separated from calculated ledger cost. Exact invocation references and marked compatibility observations avoid duplication. Old provider-native observation shims have no active production call sites in this base; their existing rows remain historical aggregates, not asserted transport receipts. Arbitrary scripts that bypass Madhav and call provider APIs directly cannot be observed by the server. They must be migrated to the authenticated administrator test gateway or a trusted internal metered execution before claiming full organizational coverage.

## Rates and honest cost interpretation

Immutable rate cards carry provider/model, effective and observation timestamps, official source URL, token class prices, and applicability. A receipt freezes the selected card and charge lines at call time. New rate versions never rewrite old receipts. Import accepts only supported official HTTPS sources and bounded decimal values; context-tier/finite interval cards require a dedicated adapter and are rejected. Older `llm_pricing_versions` are compatibility evidence, not automatically fresh prices.

OpenRouter catalog refresh converts documented per-token prices to per-million decimal rates. Unknown positive fees, tier modifiers and dynamic routers are marked inapplicable; an inapplicable observed version supersedes the previous token tariff, avoiding a fabricated complete price. Other providers require reviewed source-attributed imports at this version. No credential or provider generation is used to refresh the public catalog. Refresh is an explicit action; no scheduler or universal automatic pricing scraper was deployed.

Provider-reported cost and calculated cost are separate fields. Catalog rates can differ from an actual routed endpoint or invoice. These figures are consumption transparency and internal accounting evidence, not customer invoices, credits or paid balances. Provider invoice reconciliation, retrospective adjustment events, automatic cross-provider rate refresh, paid tool/modality fee calculators, external-client receipts and empirical answer-quality scoring are subsequent scope. The existing budget/reconciliation/quality instruments still read their legacy datasets; the new consumption dashboard is the source for transport-level completeness.

Official references consulted: https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties and https://openrouter.ai/docs/cookbook/administration/usage-accounting .

## Local verification

For a repeatable, token-free local gate from the repository root, run
`python3 platform/scripts/observatory/local_metering_acceptance.py`. It passes
only allowlisted test variables to its child processes, uses a synthetic
Firebase browser configuration, and invokes no provider or CLI generation
command. It runs the metering and affected-route tests with the metering flag
enabled, disposable PostgreSQL integration, the full existing suite with the
flag at its default-off setting, lint, TypeScript, a production build, and
anonymous HTTP gate checks. Logs and `results.json` are saved under
`00_ARCHITECTURE/briefs/observatory_metering/verification/<date in IST>/`.

Do not use `MARSYS_FLAG_AI_METERING_ENABLED=true npm test` as a whole-suite
acceptance signal. Older direct-adapter unit tests invoke models without an
authenticated request context, and their owned-connection validation fixture
does not implement the new ledger tables. The global flag intentionally makes
those fixtures fail closed. The enabled-mode gate exercises admitted request
routes, the physical model wrapper, connection probes and the real disposable
ledger separately; it does not turn off attribution to make those tests pass.

`python3 platform/scripts/observatory/local_metering_db_test.py` starts a fresh loopback-only PostgreSQL cluster in a temporary directory, runs the integration tests, stops only its own server and removes only that temporary cluster. It never reads production connection configuration. `AI_METERING_PG_BIN` may select a local PostgreSQL binary directory. Tests apply the migration twice and exercise immutable/RLS/tenant/cost/recovery/cursor behavior.

Focused: from platform, `npx vitest run src/lib/metering src/components/metering src/lib/ai-console/execution/__tests__`.
Full gates: `npm test`, `npm run lint`, `npx tsc --noEmit`.

Independent migration and whole-change reviews have been completed; four accounting/pagination/lineage/status findings were fixed with regression coverage. No live provider, CLI subscription, hosted browser session, production database, deployment or invoice reconciliation was exercised. Those remain rollout/acceptance prerequisites, not local test claims.

CLI adapter availability has an additional version gate. The registered binary
must match the pinned version in `src/lib/ai-console/cli/registry.ts`; a local
binary's `--version` and `--help` are insufficient to approve a new version.
Validate identity, auth, machine output format and cancellation with a tiny
owned test before changing a pin. A direct terminal prompt bypasses Madhav's
ledger and is not metering acceptance evidence. The 2026-09-30 local version
inventory and the static AI Console route-audit baseline comparison are in the
verification report; neither is a hosted readiness claim.

## Rollback and recovery

Disable the server metering flag to restore the prior routing and observation behavior. Keep the immutable evidence and recovery bucket for audit; do not drop, truncate or delete the ledger as an ordinary rollback. Re-enable only after the migration, rates, attribution and recovery permissions are verified. Use the administrator recovery action to drain buffered receipts; it reports recovered and failed counts and preserves failed files for inspection. Missing terminal starts require provider-request/invoice evidence when available; never manufacture tokens or zero-dollar completion to close them.
