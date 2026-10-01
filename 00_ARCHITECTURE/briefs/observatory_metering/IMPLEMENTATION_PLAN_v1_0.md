---
artifact: OBSERVATORY_METERING_PLAN
version: 1.0
status: IMPLEMENTED_LOCAL_REVIEW
created: 2026-09-29
changelog: ["v1.0: native-authorized implementation plan"]
---
# Observatory Metering Implementation Plan

> For agentic workers: execute inline using executing-plans; independent whole-change review follows implementation.

Goal: evidence-backed granular AI consumption and scoped user/admin analysis.
Architecture: SDK transport wrapper, immutable attempt/receipt ledger, versioned rates, durable recovery, shared read APIs and UI.
Tech stack: TypeScript, Next.js, PostgreSQL, AI SDK V3, Vitest, existing GCS storage.
Spec: DESIGN_v1_0.md in this directory.

## Global constraints
- Dedicated worktree, local uncommitted review state under GIP P.4.
- No real provider calls, production operations or applied-migration edits.
- Default-off flag, server-side active-user and super-admin checks.
- Null remains unknown; aggregate leaf attempts only; exact decimal USD.
- No conversation content, credentials or arbitrary provider/error bodies in telemetry.

## Review focus
- Cancellation/failure after billed output, missing finish, durable recovery.
- Missing/inconsistent cache and reasoning subcategories.
- SDK steps/retries and duplicate deliveries.
- Effective dates, partial prices, stale rates and unsupported fee units.
- Cross-user reads/exports, pagination, spreadsheet formulas and charged admin tests.

### Task 1: normalization and pricing
Files: platform/src/lib/metering/{types,usage,pricing}.ts and __tests__.
Interfaces: normalizeSdkUsage(), priceUsage(); disjoint quantities, exact USD strings, completeness.
- [x] Write and observe failing tests for nested usage, unknown/zero and subset semantics.
- [x] Implement normalization and snapshot costing; run focused tests.

### Task 2: ledger and recovery
Files: additive migration; metering/{repository,recovery,service}.ts.
Interfaces: startAttempt(), finishAttempt(), recoverReceipts(), importRateCard().
- [x] Test start-before-call, deduplication, missing prices and DB outage recovery.
- [x] Implement immutable records, safe metadata and recovery storage.
- [x] Apply only to disposable local PostgreSQL; verify constraints and real queries.

### Task 3: execution instrumentation
Files: metering/model.ts, AI Console execution, legacy observation and validation paths.
Interfaces: meterModel() and request context; one receipt per transport invocation.
- [x] Test transport success/error/cancel/retry/tool-loop behavior.
- [x] Instrument model methods and CLI aggregates; retain auth/redaction/routing guarantees.
- [x] Run existing execution and observation tests.

### Task 4: scoped analysis APIs
Files: metering query/parser modules; /api/usage and /api/admin/observatory/metering.
Interfaces: summary, breakdown, trace, pagination, CSV, recovery, pricing and admin test routes.
- [x] Test authorization, bounded filters, unknown totals and CSV safety.
- [x] Implement scoped SQL and guarded administrative operations.
- [x] Exercise real disposable database fixtures.

### Task 5: user/admin views
Files: shared usage dashboard, user/admin pages and navigation.
Interfaces: responsive accessible consumption/trace views with completeness.
- [x] Test loading/error/empty/partial states and drill-down.
- [x] Implement using existing brand tokens and Next.js conventions.
- [x] Run component/type checks.

### Task 6: verification and handoff
Files: runbook and evidence/progress artifacts.
- [x] Full lint, TypeScript and test gates.
- [x] Independent migration, security and code review; fix material findings.
- [x] Record migration status, local evidence and runtime limits.
- [x] Release implementation lease; retain worktree for review.
