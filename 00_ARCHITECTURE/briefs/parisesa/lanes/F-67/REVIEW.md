---
lane: F-67
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, SPEC.md (R2 revised), DIAGNOSIS.md. No REVIEW_LEADS.md exists; prior REVIEW.md (pool-1, ratified INCOMPLETE-RETURN) read to understand prior deficiency.
Source verified at /Users/Dev/par-night/main-ro:
- platform/src/lib/retrieval/registry/tool_name_bridge.ts (grep for pratijna lines 203, 491, 592)
- platform-mcp/src/tools/register_p1_aliases.ts (imports at lines 22-28; dualOutput at 183; bodha_signals_get block at 530-602; resolveChartFactsAyanamsha usage at lines 377, 489, 567, 645, 697, 915, 965 et al.)
- platform-mcp/src/ exhaustive grep for server.tool registrations of bodha_pratijna_get / query_pratijna
- platform-mcp/src/generated/mcp_surface_profiles.generated.ts (pratijna descriptor at line 4688)
Exit test traced line-by-line against current source (no runtime needed — zero server.tool() hits confirmed by grep).

## Q1 — Mechanism vs. symptom

PASS. Spec correctly identifies root cause: `server.tool('bodha_pratijna_get', ...)` was never written despite capability being fully descriptor'd (mcp_surface_profiles.generated.ts:4688) and bridge-aliased (tool_name_bridge.ts:592). Fix adds the missing call — addresses the omission directly, not a symptom.

## Q2 — Sub-claim coverage

PASS. All DIAGNOSIS sub-claims map to spec elements:
- D.2 "descriptor + bridge alias confirmed": tool_name_bridge.ts:203 ✓, :491 ✓, :592 ✓; mcp_surface_profiles.generated.ts:4688 ✓ — all verified.
- D.3 "zero server.tool() registration": exhaustive grep of platform-mcp/src/ returns zero matches for either name — confirmed.
- D.1 "135 rows / 27 event classes": correctly deferred to Stage V; not in dispute for the registration fix.
- D.4 "assess_*/judgment_query non-consumption": correctly scoped out with stated reason (separate larger finding); spec §4/§7 documents this explicitly.

## Q3 — Exit test genuinely fails today

YES — confirmed by grep trace.
Grep of entire platform-mcp/src/ for `server\.tool.*bodha_pratijna_get` and `server\.tool.*query_pratijna` returns zero matches. Tool is not invokable today. Exit test `bodha_pratijna_get({chart_id:'482012f1-...'})` fails with "no such tool". Once registration block is added, call routes through tool_name_bridge.ts:592 to the already-wired query_pratijna capability URI, whose handler is present at the L2_bodha layer.

## Q4 — Sibling sites

PASS. Pure addition — net-new registration with no existing broken call sites. Broader audit of all ~180 bridge entries correctly flagged out-of-scope with a stated reason (DIAGNOSIS §4, SPEC §4). No sibling sites exist for this specific finding.

## Q5 — Recurrence guard

ACCEPTED. Spec recommends (does not build) a CI cross-check of bridge aliases against server.tool() registrations. Justification — pure-addition lane with no regression surface — is sound. The unbuilt guard is a quality risk (DIAGNOSIS §4 acknowledges more aliases may share the gap), but not a blocking deficiency for a lane whose entire fix is a new addition. Noted for S1 governance follow-up.

## Q7 — Citation accuracy / unverified assumptions

All primary spec citations verified against current source:
- `tool_name_bridge.ts:203` — confirmed: `query_pratijna: 'marsys://tool/L2/query_pratijna'` ✓
- `tool_name_bridge.ts:491` — confirmed: `'query_pratijna'` in allow-list array ✓
- `tool_name_bridge.ts:592` — confirmed: `bodha_pratijna_get: 'query_pratijna'` ✓ (R2 corrected from prior draft's 584)
- `mcp_surface_profiles.generated.ts:4688` — confirmed: descriptor description text matches spec verbatim ✓
- `register_p1_aliases.ts:25-28` import block — resolveChartFactsAyanamsha imported at line 26 within the block ✓
- `register_p1_aliases.ts:530-604` bodha_signals_get model block — confirmed: server.tool('bodha_signals_get',...) starts line 530, catch/errOut at 602 ✓
- `resolveChartFactsAyanamsha` usage lines (377, 489, 567, 645, 697, 915, 965) — all confirmed by grep ✓
- `dualOutput` function at `:188` (inline code comment) — actual definition is line 183; 5-line drift in a comment reference, not a normative spec claim; default `toolName = 'unknown_tool'` is at line 183. Non-blocking.

PRIMARY DEFICIENCY FROM PRIOR REVIEW (R1) CLOSED:
- R1 cited `na(ayanamsha_id as string | undefined)` undefined helper as compilation blocker. R2 SPEC.md uses `resolveChartFactsAyanamsha(ayanamsha_id as string | undefined)` throughout — confirmed correct and matching all 12 existing call sites in the same file. Deficiency closed.

No unverified assumptions remain in the normative spec.

## Verdict: COMPLETE
