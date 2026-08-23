---
finding: F-11
stream: S1 DVARA
class: CL-01 reachability
spec_status: COMPLETE
rs_class: RS-A
writer_asset: null
data_delta: narrow
---

# F-11 SPEC — `query_kala_paddhati_profile` absent from MCP surgical whitelist

## 1. Root cause

`query_kala_paddhati_profile` is absent from `SURGICAL_TOOLS`, `TOOL_NAME_TO_URI`, and `MCP_TO_RETRIEVAL_TOOL` in `tool_name_bridge.ts`, so `isAllowedSurgicalTool()` returns `false` and `/api/mcp/primitives/[tool]` returns HTTP 400 instead of routing to the already-registered L3 capability.

## 2. Files to change

### `platform/src/lib/retrieval/registry/tool_name_bridge.ts` — three additions, one file

**a. `SURGICAL_TOOLS` array (~line 503, before `] as const`):**
Append `'query_kala_paddhati_profile'`. This is the `SurgicalToolName` type-level entry; without it `MCP_TO_RETRIEVAL_TOOL`'s value type is invalid and `isAllowedSurgicalTool` rejects the MCP key at step 2 of the whitelist invariant.

```ts
  // F-11: ṢAḌ-DARŚANA W3 item 37 — paddhati convention profile (L3 Kāla, per-chart)
  'query_kala_paddhati_profile',
] as const
```

**b. `TOOL_NAME_TO_URI` map (L3 Kāla block, after ~line 136):**
Add the direct URI mapping. Required by `whitelist_resolution_invariant.test.ts` line 78, which checks `TOOL_NAME_TO_URI` membership directly (not via `resolveToolUri`'s generated-projection fallback), so the fallback is insufficient here.

```ts
  // F-11: ṢAḌ-DARŚANA W3 item 37 — paddhati convention profile (per-chart config, migrations 533/534/537)
  query_kala_paddhati_profile: 'marsys://tool/L3/query_kala_paddhati_profile',
```

**c. `MCP_TO_RETRIEVAL_TOOL` map (after the ṢAḌ-DARŚANA W3 muhūrta block, ~line 602):**
Add the MCP-name-to-retrieval-name entry. This makes `isAllowedSurgicalTool('query_kala_paddhati_profile')` return `true` and wires the MCP call to the registered L3 handler.

```ts
  // F-11: ṢAḌ-DARŚANA W3 item 37 — paddhati profile (kala_sky_pattern.ts fetchPaddhatiProfile)
  query_kala_paddhati_profile: 'query_kala_paddhati_profile',
```

**Why only this file:** The capability handler (`query_kala_paddhati_profile.ts`), its URI (`marsys://tool/L3/query_kala_paddhati_profile`), and its `registerCapability` call in `L3_kala/index.ts` are already correct and present. The DB table `kala_paddhati_profile` is seeded by migrations 533/534/537. Nothing else needs to change.

## 3. Exit test

**File:** `platform/src/lib/retrieval/registry/whitelist_resolution_invariant.test.ts`

**Command:**
```bash
pnpm --filter platform test whitelist_resolution_invariant
```

**FAILS on today's code** when `query_kala_paddhati_profile` is added only to `MCP_TO_RETRIEVAL_TOOL` without the matching `SURGICAL_TOOLS` and `TOOL_NAME_TO_URI` entries: the `it.each(entries)` loop runs for the new pair and fails at step 2 (SURGICAL_TOOLS membership) and step 3 (`TOOL_NAME_TO_URI` missing). The aggregate test at line 69 also fails. This partially-applied state is the canonical proof that the guard is live.

**PASSES after full fix** (all three additions): the loop runs a case for `'query_kala_paddhati_profile' → 'query_kala_paddhati_profile'` and verifies all 5 invariant steps: `isAllowedSurgicalTool` true, `SURGICAL_TOOLS` contains the retrieval name, `resolveToolUri` defined, `getCapability` registered, `getToolByName` defined (not undefined → no 500).

Note: `ritual_mode2_gate.test.ts` mocks `callPlatformPrimitive` and is already green on unmodified code — not a valid fail/pass exit test for this fix.

## 4. Sibling census

Live callers of `callPlatformPrimitive('query_kala_paddhati_profile', ...)`:
- **`platform-mcp/src/lib/kala_sky_pattern.ts`** (`fetchPaddhatiProfile`) — sole caller, confirmed by exhaustive grep across `main-ro`.

No aliases needed; no other MCP-facing entry points reach this capability. The honest-degrade path that fires when the 400 is returned (confirmed in DIAGNOSIS §2) is correct behavior from the caller's perspective and requires no fix — only the routing gap does.

Sibling census is exhaustive: one site, no exclusions.

## 5. Recurrence guard

`platform/src/lib/retrieval/registry/whitelist_resolution_invariant.test.ts` — the WP-1.7 durable guard (already in CI) — enforces that every `MCP_TO_RETRIEVAL_TOOL` value is in `SURGICAL_TOOLS`, resolves via `TOOL_NAME_TO_URI`, maps to a registered capability, and returns a live tool from `getToolByName`. Any future name added to `MCP_TO_RETRIEVAL_TOOL` without all three entries causes CI to fail closed. No new guard required.

## 6. Dependencies and rollback

- **Other lanes:** none. The L3 capability and its registration pre-exist this fix.
- **Rebuild:** none. This is a routing/whitelist code fix. No writer, no asset, no data change.
- **Rollback:** revert the three lines in `tool_name_bridge.ts`; the MCP route returns 400 again and the honest-degrade path re-engages.

## 7. Coverage table

| Diagnosis sub-claim | Spec coverage |
|---|---|
| `query_kala_paddhati_profile` absent from `MCP_TO_RETRIEVAL_TOOL` (400 on every Mode-2 call) | §2c: adds `query_kala_paddhati_profile: 'query_kala_paddhati_profile'` to map |
| Mechanism: `isAllowedSurgicalTool()` returns false → 400 | §1 root cause; §3 exit test step 1 verifies `isAllowedSurgicalTool` |
| SURGICAL_TOOLS type integrity required (implied by `SurgicalToolName` type) | §2a: adds `'query_kala_paddhati_profile'` to array |
| TOOL_NAME_TO_URI entry required by whitelist invariant test (line 78) | §2b: adds URI mapping `marsys://tool/L3/query_kala_paddhati_profile` |
| Capability already registered in L3_kala/index.ts — no handler fix needed | §2 WHY: confirmed, no change to capability or registration |
| Surface degrades HONESTLY — not a correctness defect | §4: documented; excluded from fix scope |
| Sibling census not performed in diagnosis | §4: performed here; one site, no exclusions |
| Fix mirrors F-02 pattern (missing MCP whitelist entry for an existing capability) | §2: same file, same three-point invariant contract |
