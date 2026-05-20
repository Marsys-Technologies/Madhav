---
canonical_id: R10_Y_S9
version: 1.0
status: CURRENT
session_id: Y-S9
title: Stream failure auto-retry on 5xx/timeout
depends_on: [Y-S5]
blocked_on: []
flag: MARSYS_FLAG_R10_AUTO_RETRY
flag_default: false
client_side: "no — server-side retry wrapper only"
authored: 2026-05-20
risk: HIGH — cost risk; default FALSE; opt-in only
---

# Y-S9 — Stream Failure Auto-Retry

## Context

When the synthesis pipeline encounters a 5xx error or timeout on an upstream call (LLM provider, tool execution), the current behavior is to surface the error to the user immediately. This session adds a single-retry wrapper: on a first 5xx or timeout, automatically route the retry to the next available stack in `STACK_ROUTING`, record the recovery in `query_trace_steps`, and only surface the error if the retry also fails.

**Risk classification:** HIGH — cost risk. A retry doubles the LLM cost for any failed request. Default FALSE. Must be explicitly opted in by operator.

**HARD CONSTRAINT — no retry-of-retry:** The retry wrapper MUST enforce that it fires at most once per query. If the retry request itself fails, surface the error immediately. Do NOT implement exponential backoff or multi-retry loops. One retry, max.

**Amendment 1:** Server-side flag only. `MARSYS_FLAG_R10_AUTO_RETRY` is read in the server-side retry wrapper. No `NEXT_PUBLIC_` prefix. No deploy.yml build-arg required.

**Amendment 3:** FLAGGED, default false — cost risk.

## Files in Scope

- `platform/src/lib/adapters/retry_wrapper.ts` (new) — wraps the streaming adapter call; on first 5xx/timeout, routes retry to next `STACK_ROUTING` stack; records `retry_recovery` in `query_trace_steps`; enforces single-retry-max via `is_retry: boolean` flag on the request context
- `platform/src/lib/feature_flags.ts` — add `MARSYS_FLAG_R10_AUTO_RETRY` (default `false`)
- Server-side route handler that invokes the streaming adapter — wire `retry_wrapper.ts` when flag enabled
- `platform/tests/` — unit tests

## Files Must NOT Touch

- Any `'use client'` components
- Phase 4C files
- `.github/workflows/deploy.yml` (server-side flag, no build-arg needed)
- `platform/src/lib/citations/preprocessCitations.ts`

## Acceptance Criteria

1. **Flag is server-side (Amendment 1 confirmation):** `MARSYS_FLAG_R10_AUTO_RETRY` does NOT appear with `NEXT_PUBLIC_` prefix. No deploy.yml entry required. Executor confirms: `grep -rn "NEXT_PUBLIC.*AUTO_RETRY" platform/src --include="*.ts*"` — zero results.
2. **Single-retry max (HARD CONSTRAINT):** The wrapper checks `request.is_retry === true` before attempting a retry. If already a retry, skip the wrapper and surface the error directly. The `is_retry` flag is set to `true` on the retry request context before dispatch. This is the primary safety gate against runaway retries — test it explicitly.
3. **Retry routing:** On first failure, retry is sent to the NEXT entry in `STACK_ROUTING` (not the same stack that failed). If only one stack is configured, no retry is possible — surface error immediately.
4. **`retry_recovery` trace step:** On successful retry, a `retry_recovery` entry is appended to `query_trace_steps` with fields: `original_stack`, `retry_stack`, `original_error_code`, `recovered_at` timestamp.
5. **Retry triggers:** The wrapper retries on: HTTP 5xx status codes, connection timeout (configurable `RETRY_TIMEOUT_MS = 30_000` constant), stream abort due to upstream error. It does NOT retry on: 4xx errors (client errors — no retry), successful streams that were stopped by the user.
6. **Error transparency:** When both the original request and the retry fail, the error surfaced to the user includes the fact that a retry was attempted (e.g., `"Query failed after retry"`).
7. **Flag guard:** When flag=false, no retry wrapper is applied. Errors surface immediately as before.
8. **Unit tests:** At least two tests: (a) `is_retry=false` + 5xx → retry fires, `retry_recovery` appended; (b) `is_retry=true` + 5xx → no retry, error surfaces immediately.

## Pre-commit Gates

```bash
# Verify flag is server-side only
grep -rn "NEXT_PUBLIC.*AUTO_RETRY\|NEXT_PUBLIC.*auto_retry" platform/src --include="*.ts*" && echo "FAIL: NEXT_PUBLIC found" || echo "PASS"

# Verify retry_wrapper exists
test -f platform/src/lib/adapters/retry_wrapper.ts && echo "PASS: retry_wrapper exists" || echo "FAIL"

# Verify single-retry guard
grep -n "is_retry" platform/src/lib/adapters/retry_wrapper.ts && echo "PASS: is_retry guard found" || echo "FAIL: HARD CONSTRAINT missing"

npx jest --testPathPattern="retry_wrapper|retryWrapper|auto.?retry" --passWithNoTests
```

## Commit Template

```
feat(streaming): single-retry on 5xx/timeout via retry_wrapper.ts [default false]

On first 5xx or timeout, retries to next STACK_ROUTING stack. Records
retry_recovery in query_trace_steps. Hard constraint: is_retry guard
prevents retry-of-retry. Guarded by MARSYS_FLAG_R10_AUTO_RETRY=false
(server-side; no NEXT_PUBLIC, no deploy.yml build-arg). Default false
— cost risk, opt-in only.
```

## Decision Log

*(Executor: document the operator flip command. Record any edge cases around STACK_ROUTING single-stack behavior.)*
