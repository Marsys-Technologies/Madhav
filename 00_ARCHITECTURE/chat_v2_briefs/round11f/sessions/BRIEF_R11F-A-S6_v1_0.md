---
artifact: BRIEF_R11F-A-S6_v1_0.md
session_id: R11F-A-S6
version: 1.0
phase: A
parallel_safety: false
depends_on: [R11F-A-S2]
estimated_loc_delta: +60 (normalizer + tests)
---

# R11F-A-S6 — Tool inputSchema Normalization (AI SDK v6 CoreTool fix)

## Background

A-S5 smoke produced a second halt: Anthropic API HTTP 400 with
`tools.0.custom.input_schema.type: Field required`.

**Root cause:** The Vercel AI SDK upgraded from v5 → v6 between R11.A implementation
and this arc. In v6, `CoreTool` uses `inputSchema` (not `parameters`) as the field the
SDK pipeline reads. `prepareToolsAndToolChoice()` in `ai/dist/index.js` accesses
`tool2.inputSchema` — if that field is absent (because we set `parameters` instead),
`asSchema(undefined)` returns `{ properties: {}, additionalProperties: false }` with no
`type` field. Anthropic's API strictly requires `input_schema.type: "object"` on every
custom tool.

The adapter bug is compounded by lack of defensive schema normalization at the catalogue
boundary. This session fixes both.

## Scope

Two discrete fixes in two files:

### Fix 1 — `platform/src/lib/retrieve/tool_catalogue.ts`

Export `normalizeInputSchema(raw)` — the defensive boundary function. It:
- Always sets `type: 'object'`
- Preserves `properties` if it is a plain object; defaults to `{}`
- Preserves `required[]` if present; omits if absent
- Handles null/undefined/malformed input without throwing

Apply `normalizeInputSchema({})` in `convertRetrievalToolToChatTool` (replaces the
inline literal). This is the single normalization boundary for all catalogue tools.

### Fix 2 — `platform/src/lib/providers/anthropic/adapter.ts`

In the `chat()` method, change the CoreTool construction from:

```ts
parameters: jsonSchema(tool.inputSchema ?? { type: 'object', properties: {} }),
```

to:

```ts
inputSchema: jsonSchema(normalizeInputSchema(tool.inputSchema as any) as any),
```

`inputSchema` is the AI SDK v6 field. This is a one-field rename plus normalization
call. All other adapter code is unchanged.

## Tests

### New file: `platform/tests/synthesis/tool_catalogue_schema_normalization.test.ts`

Tests for `normalizeInputSchema`:
- Empty schema `{}` → `{ type: 'object', properties: {} }`
- Properties-only schema → `{ type: 'object', properties: {...} }`
- Required array preserved when present
- No required field injected when absent
- Malformed properties (non-object) → `{ type: 'object', properties: {} }` without throw
- Fully valid schema passes through unchanged
- null input handled gracefully

Tests for `buildChatToolsFromNames` schema invariant:
- All emitted ChatTools have `inputSchema.type === 'object'`
- Mixed known/unknown names: known tools still emit normalized schemas

### Augmented: `platform/tests/providers/anthropic/e2e-loop-roundtrip.test.ts`

In the happy-path test: assert that every tool passed to `streamText` has an `inputSchema`
field (not `parameters`) containing a schema with `type: 'object'`.

New test case: request with `inputSchema: {}` and `inputSchema: { properties: {...} }` (no
root type) — both must arrive at streamText with `type: 'object'` after normalization.

## Acceptance Criteria

```bash
# AC.a — new normalization tests pass
npx vitest run platform/tests/synthesis/tool_catalogue_schema_normalization.test.ts --no-coverage

# AC.b — A-S4 tightened fixture passes
npx vitest run platform/tests/providers/anthropic/e2e-loop-roundtrip.test.ts --no-coverage

# AC.c — full Anthropic test suite passes (A-S1 + A-S4 + tool events)
npx vitest run platform/tests/providers/anthropic/ platform/tests/retrieval/tool_catalogue.test.ts --no-coverage

# AC.d — TypeScript clean (no new errors in touched files)
npx tsc --noEmit 2>&1 | grep -E "adapter\.ts|tool_catalogue\.ts"
# expected: (empty — no errors)
```

## Commit sequence (this session)

1. `fix(r11f): normalize tool inputSchema at catalogue boundary; guarantee root type:object for all providers`
2. `test(r11f): tool catalogue schema normalization regression; tighten A-S1 and A-S4 fixtures`
3. `chore(r11f): insert A-S6 in queue; A-S5 blocked_by A-S6; clear A-S5 halt`

## What this session does NOT change

- No other provider adapters (Google, OpenAI, DeepSeek, NVIDIA) — Phase B sessions apply
  the same `inputSchema` pattern when implementing those adapters.
- No route.ts changes.
- No planner changes.
- No test fixture schemas change except the explicit tightening in A-S4.

## After this session

A-S5 (Anthropic visual smoke) re-runs. Phase B may proceed only after A-S5 PASS.
