---
artifact: BRIEF_R11F-A-S2_v1_0.md
session_id: R11F-A-S2
version: 1.0
phase: A
parallel_safety: false
depends_on: [R11F-A-S1]
estimated_loc_delta: +90
---

# R11F-A-S2 — Route.ts: Tool Catalogue Population (Fix Break B1)

## Scope

Fix Break B1: `route.ts:946` passes `tools: []` to `adapter.tools(...)`, so even after
A-S1 patches the adapter, the request carries an empty tool list. This session:

1. Writes a `convertRetrievalToolToChatTool(name: string) → ChatTool` helper that reads
   name, description, and inputSchema from the MARSYS retrieval registry.
2. Replaces the `tools: []` stub with a call to this helper for each planner-authorised
   tool name.
3. Covers the helper with a unit test.

## Files May Touch

```
platform/src/app/api/chat/consume/route.ts
platform/src/lib/retrieval/tool_catalogue.ts   (new file — create if not exists)
platform/tests/retrieval/tool_catalogue.test.ts (new file)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/**   (covered in A-S1 and Phase B)
CLAUDE.md
deploy.yml
```

## Preconditions

1. A-S1 committed and on branch `chat-v2/r11f-agentic-loop`.
2. `cd platform && npx vitest run --no-coverage 2>&1 | tail -5` — 0 failures.

## Implementation

### Step 1 — Locate the retrieval registry

Read `platform/src/lib/retrieval/index.ts` (or equivalent entry point). Identify how
tools are registered — look for the registry object that maps tool names to
`{ name, description, execute, inputSchema }` shapes. The planner uses this to select tools.

### Step 2 — Author `convertRetrievalToolToChatTool`

Create `platform/src/lib/retrieval/tool_catalogue.ts`:

```typescript
import type { ChatTool } from '@/lib/providers/types'
import { retrievalRegistry } from './index'  // adjust import per actual export

/**
 * Converts a retrieval registry entry into a ChatTool suitable for adapter.tools().
 * Returns null if the tool name is not found in the registry.
 */
export function convertRetrievalToolToChatTool(name: string): ChatTool | null {
  const entry = retrievalRegistry[name]
  if (!entry) return null
  return {
    name: entry.name,
    description: entry.description,
    inputSchema: entry.inputSchema ?? { type: 'object', properties: {} },
  }
}

/**
 * Converts an array of planner-authorised tool names into ChatTools.
 * Silently skips names not found in the registry (logs a warning).
 */
export function buildChatToolsFromNames(names: string[]): ChatTool[] {
  const result: ChatTool[] = []
  for (const name of names) {
    const tool = convertRetrievalToolToChatTool(name)
    if (tool) {
      result.push(tool)
    } else {
      console.warn(`[tool_catalogue] tool '${name}' not found in retrieval registry; skipping`)
    }
  }
  return result
}
```

Adjust imports to match the actual registry export. If `inputSchema` does not exist on
registry entries, derive it from the tool's Zod schema using `zodToJsonSchema` (check if
that dependency exists; if not, use a manual shape).

### Step 3 — Patch route.ts

Locate the stub at route.ts:~946:
```typescript
tools: [],  // Stub: full MCP tool dispatch wired in follow-up arc
```

Replace with:
```typescript
tools: buildChatToolsFromNames(
  plannerResult.authorisedTools ?? []  // adjust field name per actual planner output
),
```

Import `buildChatToolsFromNames` at the top of route.ts:
```typescript
import { buildChatToolsFromNames } from '@/lib/retrieval/tool_catalogue'
```

**Critical**: look at how the planner's authorised tool list is surfaced in the existing
dispatch block. It may be on `plannerResult.tools`, `plannerResult.tool_names`, or similar.
Read the surrounding context at lines 920–960 carefully before patching.

### Step 4 — Unit test

Create `platform/tests/retrieval/tool_catalogue.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { buildChatToolsFromNames } from '@/lib/retrieval/tool_catalogue'

describe('buildChatToolsFromNames', () => {
  it('returns ChatTool array for known tools', () => {
    const tools = buildChatToolsFromNames(['query_ephemeris', 'query_panchanga'])
    expect(tools).toHaveLength(2)
    expect(tools[0].name).toBe('query_ephemeris')
    expect(tools[0].inputSchema).toBeDefined()
  })

  it('skips unknown tools with warning', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const tools = buildChatToolsFromNames(['nonexistent_tool'])
    expect(tools).toHaveLength(0)
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('nonexistent_tool'))
    warn.mockRestore()
  })

  it('returns empty array for empty input', () => {
    expect(buildChatToolsFromNames([])).toEqual([])
  })
})
```

## Acceptance Tests

```bash
# AC.a: stub removed from route.ts
grep -c "tools: \[\].*Stub" platform/src/app/api/chat/consume/route.ts
# expected: 0

# AC.b: helper imported
grep -c "buildChatToolsFromNames" platform/src/app/api/chat/consume/route.ts
# expected: >= 1

# AC.c: unit tests pass
cd platform && npx vitest run tests/retrieval/tool_catalogue.test.ts --no-coverage 2>&1 | tail -5
# expected: no failures

# AC.d: full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- `platform/src/lib/retrieval/tool_catalogue.ts` (new)
- `platform/tests/retrieval/tool_catalogue.test.ts` (new)
- Patched `platform/src/app/api/chat/consume/route.ts` (stub replaced)
- Commit message: `fix(r11f-a-s2): route.ts replaces tools:[] stub with retrieval registry catalogue`

## Rollback Steps

```bash
git revert HEAD  # removes tool_catalogue.ts, test, and route.ts patch
```
