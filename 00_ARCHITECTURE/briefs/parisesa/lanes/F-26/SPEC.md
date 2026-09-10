---
artifact: SPEC_F-26
lane: F-26
stage: S
rs_class: RS-A
writer_asset: null
data_delta: narrow
---

# F-26 SPEC — `kala_life_arc_get` `include_lel_events` honest-disclosure fix

## 1. Root-cause statement

`kala_life_arc_get` in `register_p1_synthesis.ts` advertises an `include_lel_events` Zod parameter and forwards it to `query_life_arc` capability (`include_lel_events !== false`), but the capability handler never reads that parameter, its SQL never joins any LEL table, and its own descriptor declares `lel_capable: false`—so every `include_lel_events: true` call silently returns zero LEL data while the MCP tool description falsely promises "cross-links to LEL events that fell within that Parva."

## 2. Files to change

### `platform-mcp/src/tools/register_p1_synthesis.ts`

**Changes (lines 670–700):**

1. **Remove `include_lel_events` from the Zod schema** (currently lines 678–679): delete the `include_lel_events: z.boolean().optional().describe(…)` entry entirely.
2. **Remove forwarding arg** (currently line 692): remove `include_lel_events: include_lel_events !== false,` from the object passed to `callRegistryCapability`; remove `include_lel_events` from the destructured call args (line 683).
3. **Rewrite the tool description** (currently lines 670–675): remove the sentence "cross-links to LEL events that fell within that Parva"; replace with a disclosure such as: "Note: LEL-event join is not yet implemented for this tool (lel_capable: false at the capability layer)."

**Why:** This is the sole user-visible path where `include_lel_events` is ever forwarded with its true value (both `ahead.ts:826` and `story.ts:700` have already defensively hardcoded `false`). Removing the param and correcting the description makes `kala_life_arc_get` honest without touching any file outside S5's OWNS scope.

### `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts`

**Changes: NONE.**

The capability already correctly self-declares `lel_capable: false` (line 39) and its `input_schema` already omits `include_lel_events`. File is internally honest. Root-cause SQL fix (adding the actual LEL join) requires `PAR-F-26-NEEDS-LEASE` over L3_kala and is deferred to a future lane. Touching this file now is out of scope.

## 3. Exit test

**File:** `platform-mcp/src/__tests__/register_p1_synthesis_life_arc_lel_noop.test.ts`

**Command:** `npx vitest run platform-mcp/src/__tests__/register_p1_synthesis_life_arc_lel_noop.test.ts`

**FAILS on current code because:**
- The source of `register_p1_synthesis.ts` contains the string `include_lel_events` inside the `kala_life_arc_get` tool block.
- The source contains the string `cross-links to LEL events`.

**PASSES after fix because:**
- The string `include_lel_events` no longer appears in the `kala_life_arc_get` block.
- The string `cross-links to LEL events` no longer appears in the file.

**Test strategy:** Source-text assertion—read `register_p1_synthesis.ts` as a string, slice the `kala_life_arc_get` tool block (from `'kala_life_arc_get'` to the next `server.tool(` call), and assert absence of both strings. No live server or DB required.

```ts
// register_p1_synthesis_life_arc_lel_noop.test.ts
import { readFileSync } from 'fs'
import { join } from 'path'
import { describe, it, expect } from 'vitest'

const SRC = readFileSync(
  join(__dirname, '../tools/register_p1_synthesis.ts'),
  'utf-8'
)

// Isolate just the kala_life_arc_get tool block
const blockStart = SRC.indexOf("'kala_life_arc_get'")
const blockEnd   = SRC.indexOf('server.tool(', blockStart + 1)
const block      = SRC.slice(blockStart, blockEnd === -1 ? undefined : blockEnd)

describe('F-26: kala_life_arc_get must not advertise include_lel_events (no-op)', () => {
  it('include_lel_events is absent from the tool block', () => {
    expect(block).not.toContain('include_lel_events')
  })

  it('description does not falsely claim LEL cross-links', () => {
    expect(SRC).not.toContain('cross-links to LEL events')
  })
})
```

## 4. Sibling sites covered

Diagnosis §4 census — all 4 `include_lel_events` sites in the repo:

| Site | Status | Action |
|---|---|---|
| `platform-mcp/src/tools/register_p1_synthesis.ts:678,692` | **DEFECT — user-visible** | Fixed by this lane (§2 above) |
| `platform-mcp/src/tools/kala_views/ahead.ts:826` | **EXCLUDED** — already hardcodes `false`; no LEL claim in description | No change needed |
| `platform-mcp/src/tools/kala_views/story.ts:700` | **EXCLUDED** — already hardcodes `false`; file-header comment (lines 59–61) independently documents the defect | No change needed |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts` (handler + descriptor) | **EXCLUDED per PAR-F-26-NEEDS-LEASE** — descriptor correctly states `lel_capable: false`; handler correctly ignores the (now-removed) upstream param | No change needed this lane |

No other capability in the repo exhibits the "advertised LEL param forwarded to an lel_capable:false handler" pattern (DIAGNOSIS §4 confirms singleton).

## 5. Recurrence guard

The same exit-test file (`register_p1_synthesis_life_arc_lel_noop.test.ts`) serves as the recurrence guard: it asserts that `include_lel_events` is absent from the `kala_life_arc_get` block and that `cross-links to LEL events` is absent from the file. CI will fail closed if either string is re-introduced. For broader protection, add a comment at the top of the deleted block noting: `// include_lel_events intentionally absent — capability lel_capable:false (F-26); re-adding requires actual LEL join in query_life_arc.ts`.

## 6. Dependencies and rollback

- **Other lanes:** None. `query_life_arc.ts` is not touched; no L3_kala rebuild triggered.
- **Lease:** `PAR-F-26-NEEDS-LEASE` applies only to `query_life_arc.ts` which this spec does not touch. The one changed file (`register_p1_synthesis.ts`) is S5-owned and unblocked.
- **DB / migration:** None. This is a pure MCP schema + description-text change. No writer assets touched.
- **Rebuild policy:** `writer_asset: null`, `data_delta: narrow` — no rebuild required, no shadow run required (no writer layer).
- **Rollback:** Revert one commit on `register_p1_synthesis.ts`. No migration to undo, no data state to restore.

## 7. Coverage table

| Diagnosis sub-claim | SPEC coverage |
|---|---|
| (a) `include_lel_events` param declared in tool schema (register_p1_synthesis.ts:678–679) | §2: param removed from Zod schema; exit test asserts absence |
| (b) Param never read in capability handler (query_life_arc.ts:99–105) | §2: forwarding arg also removed from call site (line 692); handler untouched (already correctly ignoring it; now not called with it) |
| (c) SQL never joins LEL (query_life_arc.ts:147–177) | §2/§6: Out of scope — needs L3_kala lease + LEL schema implementation; disclosed in updated tool description; flagged via PAR-F-26-NEEDS-LEASE for future lane |
| (d) `lel_capable: false` self-declaration correct (query_life_arc.ts:39) | §2: confirmed correct, file not touched |
| Tool description false claim: "cross-links to LEL events" (register_p1_synthesis.ts:674) | §2: description rewritten; exit test asserts string absent |
| ahead.ts:826 defensive false (corroborating sibling) | §4: site verified, correct state, excluded |
| story.ts:700 defensive false + self-documenting header (corroborating sibling) | §4: site verified, correct state, excluded |
