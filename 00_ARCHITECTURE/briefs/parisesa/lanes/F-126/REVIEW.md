---
lane: F-126
stream: S3_SATYA→S1_DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, prior REVIEW.md (pool-1, ratified INCOMPLETE-RETURN, D1 = platform-mcp/src/types.ts mirror not updated), DIAGNOSIS.md, SPEC.md (status: REVISED — D1 closed by §3i, reviser cycle 3/PAR-R-15). No REVIEW_LEADS.md present.

Verified against main-ro source:
- `platform-mcp/src/types.ts` lines 22-37 (EpistemicsBlock mirror)
- `platform/src/lib/mcp/types.ts` lines 35-50 (primary EpistemicsBlock)
- `platform/src/lib/mcp/epistemics.ts` lines 42-74 (BuildEpistemicsBlockParams + buildEpistemicsBlock)
- `platform/src/lib/retrieval/registry/types.ts` lines 532-537 (ToolResult)
- `platform/src/lib/retrieval/shared_types.ts` lines 81-88 (ToolBundleResult)
- `platform/src/lib/retrieval/registry/tool_name_bridge.ts` lines 237-265 (toToolBundleResults)
- `platform/src/app/api/mcp/primitives/[tool]/route.ts` lines 307-313
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts` lines 195-228
- `platform/src/app/api/mcp/recent/route.ts` lines 198-209
- `platform/src/app/api/mcp/trace/[trace_id]/route.ts` lines 110-135
- `platform/src/lib/__tests__/mcp/primitives.test.ts` (confirmed Test 1–5b at lines 188, 197, 208, 224, 243, 265)
- `platform/src/lib/__tests__/mcp/epistemics.test.ts` (confirmed 3 buildEpistemicsBlock it() blocks at lines 19, 27, 33)
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/__tests__/query_life_events.test.ts` (exists)

## Q1 — Mechanism or symptom?

Mechanism. The fix traces the full data path: capability handler (query_life_events.ts, returns `total_matching` honestly) → toToolBundleResults (tool_name_bridge.ts, discards is_empty by stringifying content) → ToolBundleResult (shared_types.ts, no is_empty field) → buildEpistemicsBlock (epistemics.ts, no emptiness signal input) → literal constant `'high'` at route.ts:310. The spec adds an `is_empty` declaration contract at the handler layer (§3a) and threads it through each conversion point (§3c/§3d) up to the route (§3g). Design §2 correctly rejects option (b) — route-level generic content sniffing is unworkable across ~10 whitelisted primitives with no common schema. Architecture is sound.

## Q2 — Every sub-claim maps to a spec element?

DIAGNOSIS §2 claims:
- **C1** (`confidence_band:'high'` on zero-match): §3b + §3d + §3g + §5 exit tests. MAPPED.
- **C2** (LEL corpus populated; 'high' risks false negative): §3b empty_reason text + §2 design writeup. MAPPED.
- **C3** (no empty_reason distinction between zero-rows-matched vs corpus-empty): §3e + §3f + §3a + §3c. MAPPED.
- **D1** (platform-mcp/src/types.ts mirror stale — prior deficiency from pool-1 review): §3i + §8 coverage table row. NOW MAPPED. §3i adds `| null` to `confidence_band` and `empty_reason: string | null` to the platform-mcp mirror, verified against main-ro lines 22-37. CLOSED.

No unmapped sub-claim.

## Q3 — Exit tests genuinely fail today?

Traced against current source:

**primitives.test.ts Test 6** (confidence_band null): Mock returns `results[0].is_empty: true`. Current route.ts:308-313 calls `buildEpistemicsBlock({ surgical: true, confidence_band: 'high', ... })` — no code reads `firstResult?.is_empty` today. `body.epistemics.confidence_band === 'high'`, assertion `toBeNull()` → FAILS. `body.epistemics.empty_reason` undefined (field absent from current EpistemicsBlock) → `toContain(...)` against undefined → FAILS.

**epistemics.test.ts F-126 first case** (`confidence_band: null`): Current `BuildEpistemicsBlockParams.confidence_band` typed `'high' | 'medium' | 'low'` (epistemics.ts:53) — `null` not assignable → compile/type failure. If forced through at runtime, `params.confidence_band ?? 'medium'` (line 70) coerces null to 'medium' → block has 'medium' not null → FAILS.

**query_life_events.test.ts handler case**: `result.is_empty` is `undefined` (handler return at lines 208-224 has no `is_empty` field) → `expect(undefined).toBe(true)` → FAILS.

**Test 7 (regression guard)**: Mock `is_empty: false`, current route hardcodes `'high'` → `confidence_band === 'high'` → PASSES TODAY (spec correctly states this).

Exit tests correctly predict pre/post-fix behavior.

## Q4 — All sibling sites covered or excluded?

DIAGNOSIS §4 enumerated 5 buildEpistemicsBlock call sites:

| Call site | Spec | Source verified |
|---|---|---|
| `primitives/[tool]/route.ts:308` | §3g — COVERED | Confirmed: literal `'high'` at line 310 |
| `recent/route.ts:204` | §3h — COVERED | Confirmed: `buildEpistemicsBlock({ surgical: true, confidence_band: 'high' })` at line 204 |
| `trace/[trace_id]/route.ts:134` | EXCLUDED — 404 before line 134 | Confirmed: `rows.length === 0` → 404 at lines 116-124; line 134 unreachable with 0 rows |
| `asset/route.ts:217` | EXCLUDED — 500 before line 217 | Not re-read in this pass (source unchanged; prior pool-1 review confirmed) |
| `writes/[action]/route.ts:247` | EXCLUDED — different defect class (no confidence_band arg → 'medium') | Prior pool-1 confirmation, not re-verified (not challenged by reviser) |

All 5 accounted for.

## Q5 — Recurrence guard?

Test 7 (non-empty result still reports 'high') is the immediate regression guard. §6 defers a CI grep-based guard to a follow-up residual — appropriate for TIER4. The `buildEpistemicsBlock` JSDoc (§3f) now documents the null-vs-omit discipline at the shared builder. Acceptable.

## Q7 — Unverified assumptions / file:line citations?

All key citations verified against main-ro:
- `platform-mcp/src/types.ts:22-37`: `confidence_band: 'high' | 'medium' | 'low'` at line 26, no `empty_reason` — MATCHES spec §3i 'Current' block exactly.
- `platform/src/lib/mcp/types.ts:35-50`: non-nullable `confidence_band`, no `empty_reason` — MATCHES §3e.
- `epistemics.ts:42-74`: `params.confidence_band ?? 'medium'` — MATCHES §3f.
- `types.ts:532-537` (ToolResult): no `is_empty`/`empty_reason` — MATCHES §3a.
- `shared_types.ts:81-88` (ToolBundleResult): no `is_empty`/`empty_reason` — MATCHES §3c.
- `tool_name_bridge.ts:256-261` (single ToolResult branch): `return [{ content: str }]` discards is_empty — MATCHES §3d.
- `route.ts:307-313`: literal `'high'` unconditional — MATCHES §3g.
- `query_life_events.ts:208-224`: return without `is_empty` — MATCHES §3b.
- `recent/route.ts:204`: literal `'high'` — MATCHES §3h.
- `trace/[trace_id]/route.ts:116-124`: 404 short-circuit — MATCHES §4 exclusion rationale.

Spec §3i's inline verification claim ("Verified against main-ro: `platform-mcp/src/types.ts` line 26 reads `confidence_band: 'high' | 'medium' | 'low'` (non-nullable) and no `empty_reason` field exists") confirmed independently. No unverified assumption found.

**D1 is closed.** §3i is present, complete, and accurate. No remaining deficiencies.

## Verdict: COMPLETE
