---
artifact: ROLLOUT_DE_D2_HALT.md
version: "1.0"
status: HALT
stage: D.2
captured: 2026-05-23
trigger: Cache hit verification failed — both queries returned errors; new ERROR-level logs confirmed
---

# R11.D Rollout — D.2 HALT Record

## Halt trigger

Per brief halt rules: "Any flag flip that produces new ERROR-level logs in the 15-min watch → rollback that flag, HALT" and "Cache hit verification (D.2, D.3) failing on the 2nd-pass query → rollback, HALT."

Both conditions triggered simultaneously.

## Rollback executed

| Action | Revision | Status |
|---|---|---|
| MARSYS_FLAG_R11D_ANTHROPIC_CACHE=false | amjis-web-00344-8v9 | COMPLETE |

D.1 (MARSYS_FLAG_R11D_PROMPT_LAYOUT=true) remains active on rev 00344. See "Isolation status" below.

## Error log — 4 errors on rev amjis-web-00343-6lw (D.2 revision)

Both operator queries produced a two-error sequence each:

### Error type 1 — Vercel AI SDK pre-API validation (2 occurrences)
```
Error [AI_InvalidPromptError]: Invalid prompt: messages must not be empty
  cause: undefined,
  prompt: undefined
```
- 2026-05-22T19:39:26Z (query 1, first attempt)
- 2026-05-22T19:40:04Z (query 2, first attempt)

### Error type 2 — Anthropic API HTTP 400 (2 occurrences)
```
Error [AI_APICallError]: messages: text content blocks must be non-empty
  statusCode: 400
  url: https://api.anthropic.com/v1/messages
  model: claude-opus-4-7
  responseBody: {"type":"error","error":{"type":"invalid_request_error","message":"messages: text content blocks must be non-empty"}}
```
- 2026-05-22T19:40:42Z (query 1, retry — Anthropic request-id: req_011CbJB9NuZdz8m9oFD6X5BZ)
- 2026-05-22T19:42:57Z (query 2, retry — Anthropic request-id: req_011CbJBKGNwSoeBhdWEgH3Le)

## Pre-existing state check

- Rev `amjis-web-00341-667` (pre-flip): **0 occurrences** of `AI_InvalidPromptError` or `AI_APICallError` in logs.
- These errors are **new** and introduced by the D.1+D.2 revision combination.

## Root cause hypothesis

**Pattern:** Each query fails with `messages must not be empty` (prompt: undefined) first, then retries with partial messages that have an empty text content block (Anthropic HTTP 400).

**Likely source:** The `prompt_assembler.ts` D.1 reordering (tools → system → RAG → messages) is returning `undefined` or an empty array for the messages field in some code path, causing the Anthropic adapter's `chat()` to build a malformed messages array. On retry, the messages array has entries but at least one text content block is empty string.

**Isolation status:** D.1 (PROMPT_LAYOUT=true) was active on rev 00342 but was never query-tested (log-watch only). D.2 was added in rev 00343 when operator sent test queries. Therefore:
- Cannot isolate whether D.1, D.2, or their combination is the root cause.
- D.2 rolled back; D.1 remains active. Operator should decide whether to also roll back D.1 pending investigation.

## State at halt

| Flag | Current value | Revision |
|---|---|---|
| MARSYS_FLAG_R11V2_USE_ADAPTERS | true | 00344 (unchanged) |
| MARSYS_FLAG_R11D_PROMPT_LAYOUT | true | 00344 (D.1 still active) |
| MARSYS_FLAG_R11D_ANTHROPIC_CACHE | false | 00344 (rolled back) |
| MARSYS_FLAG_R11D_GEMINI_CACHE | false | not flipped |
| MARSYS_FLAG_R11E_*_LOOP | false | not flipped |

## Recommended investigation path

1. Check `platform/src/lib/providers/prompt_assembler.ts` (D.1 target) — does the reordering produce undefined or empty string for any message slot?
2. Check `platform/src/lib/providers/anthropic/adapter.ts` `chat()` method — how does it handle undefined `messages` or `system` in `AdapterChatRequest`?
3. Optional: Roll back D.1 (`MARSYS_FLAG_R11D_PROMPT_LAYOUT=false`) and retest a plain Anthropic query on the adapter path to isolate.

## Do not retry without fix

Per brief: "Do not auto-retry. Surface to operator." This halt doc is the artifact. Retry requires code fix → deploy → new flag flip sequence.

*ROLLOUT_DE_D2_HALT.md — captured 2026-05-23*
