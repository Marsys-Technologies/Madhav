---
lane: F-44
stream: S2
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, SPEC.md, DIAGNOSIS.md (all in full). No REVIEW_LEADS.md found in lane directory.

Source verified against `/Users/Dev/par-night/main-ro`:
- `platform-mcp/src/lib/response_budget.ts` lines 36-42, 275-304, 340-416, 819-827 (Read tool, exact offsets)
- `platform-mcp/src/tools/kala_views/story.ts` lines 755-788 (Read tool)
- Grep for `DrillPointerLike`, `recover_via`, `instrument` type annotations

No code executed. All assertions are line-level traces against current `origin/main` source.

## Q1 — Mechanism vs. symptom

Both sub-defects addressed at the mechanism level.

**F-44b:** Fix targets the two literal-string sites (`response_budget.ts:292`, `:409`) inside the shared `finalizeMcpBudget`/`applyResponseBudget` utility. All 11 `finalizeMcpBudget` callers are fixed simultaneously because the defect lives in the shared utility. Mechanism, not symptom.

**F-44a:** Fix targets `story.ts:764` — where `chapter_count` is computed once from the pre-trim array before `finalizeMcpBudget` mutates `response.chapters` in-place at :781-785. Moving the count computation to post-trim reads the correct final length. Mechanism, not symptom.

## Q2 — Sub-claim → spec element mapping

SPEC.md §7 coverage table maps both sub-claims explicitly:

| Sub-claim | Spec element |
|---|---|
| F-44a: chapter_count/chapters desync | §2b |
| F-44b: non-actionable recover_via | §2a |

No unmapped sub-claims. DIAGNOSIS.md §2 identifies exactly two independent sub-claims; both are mapped.

## Q3 — Exit tests fail on today's code (code-traced)

**Test 1 (F-44b):** `expect(entry.recover_via.instrument).not.toBe('response_format:legacy')`

Traced: `response_budget.ts:409` hardcodes `recover_via: { instrument: 'response_format:legacy', ... }` — exact string confirmed in `main-ro`. The 2KB call hits this branch. **FAILS today.**

**Test 2a (F-44a, 2KB):** `expect(res2kb.content.chapter_count).toBe(res2kb.content.chapters.length)`

Traced: `story.ts:764` assigns `chapter_count: chapters.length` = 91 before trim. `finalizeMcpBudget` at :781-785 mutates `response.chapters` to `[]`. Nothing recomputes `chapter_count`. **FAILS today** (91 !== 0), consistent with DIAGNOSIS.md §1 live repro.

**Test 2b (F-44a, 8KB — regression guard):** `expect(res8kb.content.chapter_count).toBe(res8kb.content.chapters.length)`

The spec's comment "passes today by coincidence (1 kept, count still 91)" is incorrect — at 8KB `chapters` is trimmed to 1, so 91 !== 1 **also FAILS today**. This is a minor spec comment inaccuracy; the test assertion itself is correctly stated and both calls are good regression guards. Non-material to correctness.

## Q4 — Sibling sites

**F-44b:** Both emission sites confirmed (`response_budget.ts:292`, `:409`). DIAGNOSIS.md §4 grep against `platform-mcp/src` found exactly these two. Spec fixes both. No third site. Coverage complete.

**F-44a:** `kala_projections_get` (`projection_count`) and `kala_life_arc_get` (`parva_count`) excluded with stated reason: "plausible, not confirmed live." Exclusion is honest and correct — no defect asserted without live confirmation. Structural gap documented as follow-up census item.

## Q5 — Recurrence guard

**F-44b:** No lint guard; spec honestly states no mechanical lint is feasible for "don't invent a param name." Fix in shared utility closes all current callers simultaneously. A future third site needs code review. Honest and defensible.

**F-44a:** No guard built (single-tool fix). Excluded siblings flagged as natural follow-up via the `assembleSaraContent`/`companionCountField` precedent cross-reference. Honest.

## Q7 — Unverified assumptions / file:line citations

All citations verified against `main-ro`:

- `response_budget.ts:292` — CONFIRMED: exact `'response_format:legacy'` literal.
- `response_budget.ts:402-410` — CONFIRMED: collapsed-fallback branch; literal at line 409.
- `story.ts:764` — CONFIRMED: `chapter_count: chapters.length`.
- `story.ts:781-785` — CONFIRMED: `finalizeMcpBudget(response as unknown as Record<string, unknown>, {...})`.
- `TrimReportEntry.recover_via.instrument` (line 41) — CONFIRMED typed `string`, NOT `string | null`.
- `DrillPointerLike.instrument` (line 309) — CONFIRMED typed `string`, NOT `string | null`.

**Type widening confirmed required:** Spec says "if it's typed as `string`-only, widen it" — IT IS. Both `TrimReportEntry.recover_via` (line 41) and `DrillPointerLike` (line 309) must be widened to `string | null`. TypeScript will reject `instrument: null` without this. Spec correctly identifies the condition; builder finds both sites via compiler errors. Not a spec-level deficiency.

**Pseudocode variable name (non-material):** §2b shows `response['chapter_count'] = ...` after `finalizeMcpBudget`. Actual code assigns return to `const budgeted`. Since `finalizeMcpBudget` mutates input in-place and returns the same reference (confirmed: line 373 `const mutable = content as ...`, return `content` at line 371 early-exit), `response` and `budgeted` are the same object. Builder writes `budgeted.chapter_count = budgeted.chapters?.length ?? 0` — logically identical.

## Verdict: COMPLETE

Spec addresses both defects at the mechanism level. All file:line citations verified correct against current source. Exit tests confirmed-failing today by line-level code trace. Sibling coverage is honest and correctly scoped. Type-widening dependency correctly identified. Two minor inaccuracies (8KB comment, pseudocode variable) are non-material to correct implementation.
