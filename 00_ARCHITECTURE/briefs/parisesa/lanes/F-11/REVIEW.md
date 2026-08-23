---
lane: F-11
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read PROTOCOL.md, SPEC.md, DIAGNOSIS.md (no REVIEW_LEADS.md present). Verified all file:line citations against `/Users/Dev/par-night/main-ro`. Specifically:
- Grepped `tool_name_bridge.ts` for `query_kala_paddhati_profile` (no hits — confirmed absent from all three structures)
- Read `SURGICAL_TOOLS` array (lines 437–504), `MCP_TO_RETRIEVAL_TOOL` map (lines 512–603), `TOOL_NAME_TO_URI` (lines 77–209) to confirm absence and understand insertion points
- Verified `query_kala_paddhati_profile.ts` capability handler exists at `platform/src/lib/retrieval/registry/layers/L3_kala/query_kala_paddhati_profile.ts`
- Verified `registerCapability(queryKalaPaddhatiProfileCapability)` at `L3_kala/index.ts:70`
- Verified sole caller at `platform-mcp/src/lib/kala_sky_pattern.ts:691` (`callPlatformPrimitive('query_kala_paddhati_profile', ...)`)
- Read `whitelist_resolution_invariant.test.ts` fully to understand 5-step invariant and `it.each(entries)` iteration
- Confirmed migrations 533, 534, 537 all exist and reference `kala_paddhati_profile`
- Grepped all of `platform-mcp/src/` for `query_kala_paddhati_profile` — only test mocks and `kala_sky_pattern.ts` found

## Q1 — Mechanism vs symptom

COMPLETE. The spec correctly identifies the mechanism: `isAllowedSurgicalTool()` reads `Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)` (tool_name_bridge.ts:613), and since `query_kala_paddhati_profile` is absent from that map, the check returns `false` → the `/api/mcp/primitives/[tool]` route returns HTTP 400 before ever reaching the capability. The spec traces this to the three-point invariant (SURGICAL_TOOLS membership, TOOL_NAME_TO_URI resolution, registered capability), all of which are violated. Not symptom-only.

## Q2 — Diagnosis sub-claims vs spec coverage

DIAGNOSIS has two explicit claims:
1. "query_kala_paddhati_profile unreachable from Mode-2 sky_pattern_spec path" → covered §1 root cause + §2c MCP_TO_RETRIEVAL_TOOL addition. ✅
2. "surface degrades HONESTLY" → documented and explicitly excluded from fix scope in §4. ✅

DIAGNOSIS §3 cites `tool_name_bridge.ts:508+` — verified: line 508 is the JSDoc for `MCP_TO_RETRIEVAL_TOOL`; `+` correctly points into the map. Close enough. ✅

DIAGNOSIS §4 explicitly says sibling census was not performed. Spec §4 supplies it. ✅

No unmapped diagnosis sub-claims.

## Q3 — Exit test genuinely red on today's code?

NUANCED — no pre-fix red state, but test is still a valid builder guard.

`whitelist_resolution_invariant.test.ts` iterates `Object.entries(MCP_TO_RETRIEVAL_TOOL)`. Since `query_kala_paddhati_profile` is absent from that map on today's unmodified code, it does NOT appear in the `it.each` loop — the test passes today without detecting the defect. The spec's claim "FAILS on today's code" refers specifically to the partially-applied state (tool added to MCP_TO_RETRIEVAL_TOOL only), NOT to unmodified source. The spec acknowledges this implicitly: "The partially-applied state is the canonical proof that the guard is live."

This is inherent to the "absent whitelist entry" defect class — there is no possible pre-fix red assertion short of an exhaustive registry coverage test (which doesn't exist). The exit test correctly detects a builder error (partial application) and confirms the complete fix is consistent. This limitation does not warrant INCOMPLETE-RETURN; the spec is honest about the partial-apply proof.

Trace for unmodified code: `entries = Object.entries(MCP_TO_RETRIEVAL_TOOL)` → `query_kala_paddhati_profile` not present → `it.each` never runs a case for it → test passes. ✅ (test passes today, would fail on partial apply, passes on complete fix — builder guide is sound)

## Q4 — Sibling sites

COMPLETE. Spec §4 claims sole caller is `platform-mcp/src/lib/kala_sky_pattern.ts` (`fetchPaddhatiProfile`). Independent grep of all `platform-mcp/src/` confirms:
- `kala_sky_pattern.ts:691` — actual `callPlatformPrimitive('query_kala_paddhati_profile', ...)` call ✅
- `ritual_mode2_gate.test.ts:181` — mock switch-case, not a live caller ✅
- `kala_sky_pattern.test.ts:193` — test assertion string, not a live caller ✅

Census is exhaustive. Spec §4's exclusion of the honest-degrade path from fix scope is correctly stated.

## Q5 — Recurrence guard

ADEQUATE for defect class. `whitelist_resolution_invariant.test.ts` (WP-1.7) enforces all 5 invariant steps for every MCP_TO_RETRIEVAL_TOOL entry. Any future addition to MCP_TO_RETRIEVAL_TOOL without matching SURGICAL_TOOLS + TOOL_NAME_TO_URI entries causes CI to fail closed. The guard does not detect the "absent entry" variant (a tool intentionally omitted from the map), but that requires a different coverage approach and is out of scope for this CL-01 lane. Guard is correctly characterized. ✅

## Q7 — Unverified assumptions / file:line accuracy

All checked:
- `platform/src/lib/retrieval/registry/tool_name_bridge.ts` — exists ✅
- `query_kala_paddhati_profile` absent from SURGICAL_TOOLS, TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL — confirmed by grep (zero hits) ✅
- `SURGICAL_TOOLS` array ends before `] as const` at line 504 — confirmed ✅
- `MCP_TO_RETRIEVAL_TOOL` starts at line 512, ends at line 603 — confirmed; spec's "~line 602" is accurate ✅
- `TOOL_NAME_TO_URI` L3 Kāla block at lines 134–136 — confirmed; additional L3 entries at 195–199; insertion point is valid ✅
- URI pattern `marsys://tool/L3/query_kala_paddhati_profile` consistent with `query_dasha_dossier`, `query_temporal_view`, etc. ✅
- Capability handler file `query_kala_paddhati_profile.ts` — exists ✅
- `registerCapability(queryKalaPaddhatiProfileCapability)` at `L3_kala/index.ts:70` — confirmed ✅
- Migrations 533, 534, 537 — all exist referencing `kala_paddhati_profile` ✅
- `whitelist_resolution_invariant.test.ts:78` checks `TOOL_NAME_TO_URI` membership directly — confirmed at line 78 ✅
- `ritual_mode2_gate.test.ts` mocks `callPlatformPrimitive` — confirmed; spec correctly notes it's already green ✅

**writer_asset/data_delta/RS-A accuracy:** `writer_asset: null` correct (no writer, no data generation). `data_delta: narrow` correct (routing code only). `rs_class: RS-A` correct (serving-layer change, no DB writes). No rebuild required. ✅

## Verdict: COMPLETE

All seven rubric items pass. The spec correctly identifies the three-point whitelist invariant as the mechanism, maps every diagnosis sub-claim to a spec element, supplies the sibling census the diagnosis skipped, and provides a valid recurrence guard. All file:line citations verified against main-ro. The exit test's inability to red on unmodified code is inherent to the defect class (absent entry) and correctly characterized in the spec — not a deficiency warranting return.
