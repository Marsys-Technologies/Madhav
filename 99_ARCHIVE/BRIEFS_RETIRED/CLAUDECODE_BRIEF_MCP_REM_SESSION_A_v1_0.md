---
canonical_id: CLAUDECODE_BRIEF_MCP_REM_SESSION_A
version: 1.0
status: READY
authored: 2026-05-26
session_id: MCP-REM-SESSION-A
parent_plan: MCP_TOOL_AUDIT_REM_V2_PLAN_v1_0.md
description: >
  Backward-compatible Zod schema aliases for 7 platform-mcp tools that
  regressed in Audit 3 due to API signature changes. Zero behavior changes;
  only input-validation layer extended with .transform() aliases.
  Target: 7 tools from 50%→90%+.
---

# MCP-REM Session A — Backward-Compat Schema Aliases

## §1 — Role and scope

You are executing a targeted remediation on the `platform-mcp` package only.
Seven MCP tools regressed from ~95% to ~50% in Audit 3 because their Zod
input schemas were changed without backward-compatible aliases. Callers
(including the MCP audit harness) using old parameter names get Zod validation
errors. This session adds backward-compat aliases to all 7 tools.

**No behavior changes.** No DB migrations. No new tools. Only input schemas.
All fixes follow the same `.transform()` pattern.

---

## §2 — Mandatory reads before any edits

1. `00_ARCHITECTURE/BRIEFS/MCP_TOOL_AUDIT_REM_v2_PLAN_v1_0.md §4 Session A` — exact transform specs for all 7 tools
2. `platform-mcp/src/tools/holistic_bundle_tool.ts`
3. `platform-mcp/src/tools/multi_school_bundle_tool.ts`
4. `platform-mcp/src/tools/cross_school_lookup.ts`
5. `platform-mcp/src/tools/query_ephemeris.ts`
6. `platform-mcp/src/tools/log_prediction.ts`
7. `platform-mcp/src/tools/vector_search.ts`
8. `platform-mcp/src/tools/read_asset.ts`

Read each file in full before touching it. Understand the current schema
and core logic so the transform wraps around it cleanly.

---

## §3 — Branch and worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add ../MadhavMCPSchemaA fix/mcp-schema-compat 2>/dev/null || \
  git worktree add ../MadhavMCPSchemaA -b fix/mcp-schema-compat
cd ../MadhavMCPSchemaA
```

All work in `/Users/Dev/Vibe-Coding/Apps/MadhavMCPSchemaA`.

---

## §4 — Exact changes (apply in order)

### A.1 — `platform-mcp/src/tools/read_asset.ts`

**Old schema used by callers:** `{ asset_key: string }`
**New schema:** `{ canonical_id: string }`
**Fix:** Accept both; normalize to `canonical_id`.

Find the Zod input schema definition (the `z.object({...})` for this tool's
input). Replace the `canonical_id: z.string()` line with:

```typescript
const inputSchema = z.object({
  canonical_id: z.string().optional(),
  asset_key: z.string().optional(),  // backward-compat alias
  section: z.string().optional(),
}).transform(i => ({
  canonical_id: (i.canonical_id ?? i.asset_key ?? '').toUpperCase(),
  section: i.section,
})).refine(i => i.canonical_id.length > 0, {
  message: 'canonical_id or asset_key is required',
});
```

If the existing schema has additional fields (e.g. `format`), preserve them
in the transform output. Do NOT change the tool's execution logic — only wrap
the input schema.

---

### A.2 — `platform-mcp/src/tools/vector_search.ts`

**Old param:** `query: string`
**New param:** `text: string`
**Fix:** Accept both; normalize to `text`.

In the input schema, change `text: z.string()` to:

```typescript
text: z.string().optional(),
query: z.string().optional(),  // backward-compat alias
```

Add at the end of the schema object (before closing `})`):

```typescript
// at the .transform() level:
}).transform(i => ({
  ...i,
  text: i.text ?? i.query ?? '',
})).refine(i => i.text.length > 0, { message: 'text or query is required' });
```

If the schema already has other required fields, keep them — only `text`
is being made backward-compat.

---

### A.3 — `platform-mcp/src/tools/cross_school_lookup.ts`

**Old param:** `topic: string`
**New param:** `claim: string`

Extend the schema:

```typescript
claim: z.string().optional(),
topic: z.string().optional(),  // backward-compat alias
```

In transform (or add one):

```typescript
}).transform(i => ({
  ...i,
  claim: i.claim ?? i.topic ?? '',
})).refine(i => i.claim.length > 0, { message: 'claim or topic is required' });
```

---

### A.4 — `platform-mcp/src/tools/multi_school_bundle_tool.ts`

**Old param:** `topic: string`
**New param:** `claim: string (min 10)`

```typescript
claim: z.string().optional(),
topic: z.string().optional(),  // backward-compat alias
```

Transform:

```typescript
}).transform(i => ({
  ...i,
  claim: i.claim ?? i.topic ?? '',
})).refine(i => i.claim.length >= 10, {
  message: 'claim (or topic) must be at least 10 characters',
});
```

---

### A.5 — `platform-mcp/src/tools/holistic_bundle_tool.ts`

**Old params:** `{ bundles: string[] }` (array of bundle names)
**New param:** `{ query_text: string (min 3) }`

```typescript
query_text: z.string().optional(),
bundles: z.array(z.string()).optional(),  // backward-compat alias
```

Transform:

```typescript
}).transform(i => ({
  ...i,
  query_text: i.query_text ?? (i.bundles && i.bundles.length > 0
    ? i.bundles.join(', ')
    : ''),
})).refine(i => i.query_text.length >= 3, {
  message: 'query_text (or non-empty bundles array) required, min 3 chars',
});
```

---

### A.6 — `platform-mcp/src/tools/query_ephemeris.ts`

**Old params (flat):** `{ date_from: string, date_to: string }`
**New param (nested):** `{ date_range: { from: string, to: string } }`

```typescript
date_range: z.object({ from: z.string(), to: z.string() }).optional(),
date_from: z.string().optional(),  // backward-compat flat params
date_to: z.string().optional(),
```

Transform:

```typescript
}).transform(i => ({
  ...i,
  date_range: i.date_range ?? (i.date_from && i.date_to
    ? { from: i.date_from, to: i.date_to }
    : undefined),
})).refine(i => i.date_range !== undefined, {
  message: 'date_range (or date_from + date_to) is required',
});
```

---

### A.7 — `platform-mcp/src/tools/log_prediction.ts`

**Old param:** `confidence: number` (float 0.0–1.0) with no `falsifier`
**New params:** `confidence: 'high'|'medium'|'low'`, `falsifier: string` (required)

For `confidence`:

```typescript
confidence: z.union([
  z.enum(['high', 'medium', 'low']),
  z.number().min(0).max(1),  // backward-compat float
]).transform(c =>
  typeof c === 'number'
    ? c > 0.75 ? 'high' : c >= 0.5 ? 'medium' : 'low'
    : c
),
```

For `falsifier` — make it optional with empty string default:

```typescript
falsifier: z.string().optional().default(''),
```

Do NOT change any other fields in this schema.

---

## §5 — Test requirements (write for each tool)

For each of the 7 tools, add or update the tool's test file in
`platform-mcp/src/tools/__tests__/` (or wherever tests live).

Each test file must include:

**Test A (old-signature backward-compat):**
```typescript
it('accepts old parameter name and returns valid result', async () => {
  // call with old signature
  // assert: no Zod validation error, result shape is correct
});
```

**Test B (new-signature still works):**
```typescript
it('accepts new parameter name and returns valid result', async () => {
  // call with new signature
  // assert: same result shape as old-signature call
});
```

Tests should mock the underlying DB/network calls so they run offline.
They are ONLY testing that input validation passes and the transform
produces the correct normalized shape — not end-to-end execution.

---

## §6 — Build verification

After all 7 edits are complete:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPSchemaA/platform-mcp
npm run build
```

Must exit 0. Zero TypeScript errors.

```bash
npm test
```

Must pass all tests including the 14 new backward-compat tests (2 per tool).

---

## §7 — Acceptance criteria (all must pass before commit)

- [ ] AC-A.1: `npm run build` exits 0 in `platform-mcp/`
- [ ] AC-A.2: `npm test` passes all tests in `platform-mcp/`
- [ ] AC-A.3: For each of 7 tools: old-signature test passes (no Zod error)
- [ ] AC-A.4: For each of 7 tools: new-signature test passes (same result shape)
- [ ] AC-A.5: Zero changes outside `platform-mcp/src/tools/` (confirm with `git diff --name-only`)
- [ ] AC-A.6: No changes to any tool's execution logic (only input schema wrappers)
- [ ] AC-A.7: Each edited file has the backward-compat section clearly commented
  `// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---`

---

## §8 — Commit

```bash
git add platform-mcp/src/tools/
git commit -m "fix(mcp-schema-compat): backward-compat Zod aliases for 7 regressed tools

Session A of MCP Tool Audit Remediation v2.
Adds .transform() input aliases for old caller signatures:
  - read_asset: asset_key → canonical_id
  - vector_search: query → text
  - cross_school_lookup: topic → claim
  - multi_school_bundle: topic → claim
  - holistic_bundle: bundles[] → query_text
  - query_ephemeris: date_from+date_to → date_range{from,to}
  - log_prediction: confidence float → enum; falsifier optional

No behavior changes. No DB migrations. Input validation layer only.
MCP-REM-V2 §4 Session A AC all pass."
```

Push:
```bash
git push origin fix/mcp-schema-compat
```

---

## §9 — Session close signal

Paste back to Cowork chat:

```
SESSION-A COMPLETE
Branch: fix/mcp-schema-compat
Commit: <SHA>
Build: PASS
Tests: PASS (N total, 14 new backward-compat)
All 7 AC-A.* checks: PASS
Tools patched: read_asset, vector_search, cross_school_lookup,
               multi_school_bundle, holistic_bundle, query_ephemeris,
               log_prediction
```

---

## §10 — Must NOT touch

- `platform/` (any file)
- Any tool file NOT listed in §4
- `platform-mcp/src/server.ts`
- `platform-mcp/Dockerfile`
- Any migration file
- `CLAUDE.md`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`

Violating must_not_touch is a session discipline failure.

---

*End of CLAUDECODE_BRIEF_MCP_REM_SESSION_A_v1_0.md*
