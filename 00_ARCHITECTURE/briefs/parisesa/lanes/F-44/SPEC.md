---
lane: F-44
stream: S2 (MĀTRĀ), file owner of response_budget.ts + kala_views/story.ts (both S2's lease)
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — honest recover_via + resynced chapter_count for `kala_story_get`'s budget collapse path

Two independent sub-defects (DIAGNOSIS.md §3 confirmed these are separate functions, separate
fixes, tracked as one spec per that document's own recommendation, with two exit tests).

## 1. Root-cause statement

**F-44b:** `response_budget.ts`'s last-resort collapse fallbacks (`finalizeMcpBudget` :402-410,
`applyResponseBudget` :287-293) hardcode `recover_via.instrument: 'response_format:legacy'` — a
parameter that exists on no tool's schema anywhere in the codebase (confirmed by repo-wide grep,
DIAGNOSIS.md §4).
**F-44a:** `kala_story_get` (`kala_views/story.ts:764`) computes `chapter_count: chapters.length`
once, before the `chapters` array is later trimmed by `finalizeMcpBudget` (`:781-785`) — the two
values go out of sync at extreme budget pressure (91 vs 0 in the confirmed live repro).

## 2. Files to change

### 2a. `response_budget.ts:287-293` and `:402-410` (S2 HOT) — honest null over invented instrument

```ts
// BEFORE (both sites, byte-identical):
recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },

// AFTER:
recover_via: { instrument: null, hint: 'no smaller recovery instrument available at this budget — retry with a larger budget_kb if the calling tool accepts one, or omit budget_kb for the default ceiling' },
```
Per §N.7 item 6 ("an honest null beats an invented judgment") — this is the doctrinally correct
minimal fix. `instrument: null` requires confirming `DrillPointerLike`/`recover_via`'s type
permits a null instrument; if it's typed as `string`-only, widen it (small, low-risk type change,
this field is internal to the trim/recovery mechanism, not part of any external contract beyond
what's already inside `trim_report`).

### 2b. `kala_views/story.ts:764` (S2-owned) — resync after trim, not before

```ts
// BEFORE (:764, before finalizeMcpBudget runs):
chapter_count: chapters.length,
...
finalizeMcpBudget(response, { maxKb: input.budget_kb ?? 40, sections, ... })  // :781-785

// AFTER — move the count computation to read the post-trim array:
// (remove the early chapter_count assignment at :764)
...
finalizeMcpBudget(response, { maxKb: input.budget_kb ?? 40, sections, ... })
response['chapter_count'] = (response['chapters'] as unknown[])?.length ?? 0  // NEW, after trim
```
Mirrors the codebase's own established pattern for this exact defect class:
`assembleSaraContent`'s `CompositionReport.counts` field (`response_budget.ts:693-710` doc-comment:
"honest even when a layer is absent due to budget — closes the 'trim zeroes count but count field
still shows original' defect class, F-112") — same principle, applied to `kala_story_get`'s older,
non-Sāra-kernel code path.

## 3. Exit test

```ts
test('response_budget collapse fallback never names a fictional recovery instrument', async () => {
  const res = await callTool('kala_story_get', { chart_id: CANONICAL_CHART_ID, budget_kb: 2 })
  const entry = res.content.trim_report[0]
  expect(entry.recover_via.instrument).not.toBe('response_format:legacy')  // fails today
  expect(entry.recover_via.instrument).toBeNull()  // or a real, schema-valid instrument
})

test('kala_story_get chapter_count stays in sync with chapters after trim', async () => {
  const res2kb = await callTool('kala_story_get', { chart_id: CANONICAL_CHART_ID, budget_kb: 2 })
  expect(res2kb.content.chapter_count).toBe(res2kb.content.chapters.length)  // fails today: 91 !== 0

  const res8kb = await callTool('kala_story_get', { chart_id: CANONICAL_CHART_ID, budget_kb: 8 })
  expect(res8kb.content.chapter_count).toBe(res8kb.content.chapters.length)  // passes today by
    // coincidence (1 kept, count still 91) — must stay passing, not regress
})
```
First test fails today (verified live in DIAGNOSIS.md §1). Second test's first assertion fails
today (91 vs 0); its second call is a regression guard for the currently-accidentally-OK case.

## 4. Sibling sites covered

`response_format:legacy` (§2a): exactly 2 emission sites, both fixed (DIAGNOSIS.md §4 confirmed
no third site exists). `chapter_count` desync (§2b): specific to `kala_story_get`; DIAGNOSIS.md §4
flagged `kala_projections_get` (`projection_count`) and `kala_life_arc_get` (`parva_count`) as
"plausible, not confirmed live" siblings of the SAME general class (a `*_count` scalar beside a
budget-trimmable array with no resync) — **excluded from this spec's fix and exit test**, not
asserted as defects without live confirmation; recommended as a follow-up census once this
pattern is BUILD-verified on `kala_story_get`.

## 5. Recurrence guard

§2a: none of the two hardcoded-string sites remain — a future third site copying this pattern
would need to be caught by code review, not a lint (no generic way to lint for "don't invent a
param name" mechanically). §2b: none built (single-tool fix); the excluded siblings in §4 are the
natural follow-up if a generic guard is wanted later (e.g. extending §2b's `assembleSaraContent`
counts-precedent to the older `finalizeMcpBudget` path generally, mirroring F-45's own optional
`companionCountField` idea from that lane's SPEC.md §2b — cross-referenced, not duplicated here).

## 6. Dependencies and rollback

No DB migration. Both files are S2's own lease (`response_budget.ts` HOT, `kala_views/story.ts`
owned) — S2 builds this lane entirely, no cross-stream handoff. Sequencing note: `response_budget.ts`
is shared with F-13/F-56/F-111/F-112/F-122/F-46/F-14/F-15/F-124/F-125's own hot-file edits (S2's
"one builder, all day" discipline) — this spec's §2a hunk (lines 287-293, 402-410) is in a
DIFFERENT region of the file than F-14's grounding-assembly fix (~2925) or F-46's
`applyAutoBudgetToEnvelope` fix (~584-598), so no line-level collision expected, but the single
hot-file builder sequences commits regardless. Rollback: §2a and §2b are independent hunks in
independent files; either can be reverted without affecting the other.

## 7. Coverage table

| Sub-claim | Spec element |
|---|---|
| F-44a: chapter_count/chapters desync | §2b |
| F-44b: non-actionable recover_via | §2a |
