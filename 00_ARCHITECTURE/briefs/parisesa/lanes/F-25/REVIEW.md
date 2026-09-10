---
lane: F-25
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-25/SPEC.md, F-25/DIAGNOSIS.md. No REVIEW_LEADS.md present. Inspected source at `/Users/Dev/par-night/main-ro` (origin/main, pre-fix):
- `platform-mcp/src/tools/kala_views/register_all.ts` (full, 65 lines)
- `platform-mcp/src/tools/kala_views/dasha_sandhi.ts` (full, 384 lines)

No runtime execution; line-by-line trace against current source confirmed defect and validated all spec claims.

## Q1 — Mechanism vs. symptom

COMPLETE. The spec addresses the mechanism: `registerDashaSandhiCalendar(server)` at `register_all.ts:64` omits `principal`, so `dasha_sandhi.ts`'s handler constructs a hardcoded placeholder identity instead of receiving the real caller's principal. The spec names the exact parameter-threading gap and the resulting auth failure path — not merely "tool returns empty." Mechanism-level. ✓

## Q2 — Diagnosis sub-claim mapping

COMPLETE. DIAGNOSIS §2 has one compound claim; SPEC §7 maps it explicitly:
- "dropped Principal at tool registration → every dispatch fails authorization" → SPEC §2: `register_all.ts` updated to pass real `principal`.
- "failure swallowed into honest-empty, masking auth bug as data gap" → SPEC §2: removing the placeholder removes the cause, not a new honesty layer.

No unmapped sub-claim. ✓

## Q3 — Exit test genuinely fails on today's code

CONFIRMED by source inspection. In `main-ro`:
- `register_all.ts:64`: `registerDashaSandhiCalendar(server)` — no `principal` argument.
- `dasha_sandhi.ts:331`: `export function registerDashaSandhiCalendar(server: McpServer): void` — signature takes only `server`.
- `dasha_sandhi.ts:361`: handler constructs `const principal: Principal = { user_uid: 'system', key_id: 'system', role: 'super_admin' }` — hardcoded placeholder.
- `callRegistry` at `dasha_sandhi.ts:74–88` uses `principal.user_uid`/`principal.key_id` in headers to POST `/api/retrieval/capability`; `system`/`system` fails the entitlement gate for real callers, triggering the `!reachable` branch at `dasha_sandhi.ts:277–291` → `honestEmptyCoverage(…'could not be dispatched this call.')` → `boundaries:[]`.

Exit test `kala_dasha_sandhi_get({chart_id:'482012f1-…'})` would return `boundaries:[]` on main-ro exactly as the spec and live-session evidence state. ✓

Minor observation: `computeDashaSandhiCalendar` at line 267 uses the parameter name `_principal` (underscore prefix conventionally signals "unused") but actually passes it to `fetchDashaRows` at line 275. This is a pre-existing naming inconsistency in the unchanged code, not introduced by the fix and not affecting correctness.

## Q4 — Sibling sites

COMPLETE. `register_all.ts` lines 56–63 confirmed: all 8 sibling `registerKala*Tool(server, principal)` calls pass `principal`. Line 64 is the sole outlier. The spec's exclusion of out-of-`kala_views/*` sites is stated with a rationale (CL-01 scope). ✓

## Q5 — Recurrence guard

NONE PRESENT — honestly disclosed. SPEC §5 states "None added on the branch" and recommends a lint/contract test asserting every `register*Tool(server, …)` call inside `registerAllKalaViews` passes `principal` as its second argument. This is the correct defect class (parameter-threading omission at registration). The spec correctly defers the guard requirement to VERIFIER's judgment given the TIER-1/adopted-branch nature. Flagged, not blocking: the gap is transparent and the defect pattern is highly visible from the diff; a new register function would require a deliberate decision to omit `principal` against the established pattern of 8 correct sibling calls.

## Q7 — Spec citations vs. current source

- `register_all.ts:64` → VERIFIED: `registerDashaSandhiCalendar(server)` is exactly line 64. ✓
- `dasha_sandhi.ts:358-362` → VERIFIED: line 358 opens the async handler, line 361 is the hardcoded placeholder construction. ✓
- `register_all.ts:64` (DIAGNOSIS §3) → same, verified. ✓
- writer_asset / data_delta / RS-A: this lane is CL-01 reachability (a serving-layer parameter-threading fix); it writes no new data assets, has no `data_delta` field, and does not reference RS-A. The rebuild policy is not triggered. No shadow run required (no writer layer touched). ✓

## Named deficiencies

Neither is INCOMPLETE-RETURN-blocking given the adopted-branch/TIER-1 context and honest disclosure, but noted for VERIFIER:
1. No recurrence guard — `platform-mcp/src/tools/kala_views/register_all.ts` (no lint/contract test for `principal` threading). Disclosure in SPEC §5 is adequate.
2. No automated test on branch — exit test is a live MCP call, not a committed unit test. SPEC §3 discloses this explicitly and proposes VERIFIER decide. Adequate.

## Verdict: COMPLETE

The spec correctly identifies the mechanism, maps all diagnosis sub-claims, cites accurate file:line locations (verified against main-ro source), covers sibling sites with a stated exclusion rationale, and honestly discloses both the missing recurrence guard and the missing unit test. The exit test demonstrably fails on today's code (traced line-by-line). Both disclosed gaps are appropriate deferrals to VERIFIER for a TIER-1 adopted-branch lane. No hidden assumptions found. No unmapped claims. COMPLETE.