# F-44 — DIAGNOSIS

Stream: S2 MĀTRĀ · Class: CL-11/05 · File: `platform-mcp/src/lib/response_budget.ts` (S2 HOT)
Stage: D (DIAGNOSE) · Chart: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, canonical)

## 1. Live reproduction — REPRODUCES (both sub-claims confirmed)

Three calls to `kala_story_get`, varying only `budget_kb`, against the canonical chart.

### `budget_kb: 2` (collapsed-fallback path fires)
```json
{
  "chapters": [],
  "chapter_count": 91,
  "dedup_report": {"source_row_count": 91, "deduped_row_count": 91, "collapses": []},
  "budget_kb_applied": 2,
  "budget_kb_requested": 2,
  "trim_report": [
    {
      "path": "(trim_report)",
      "original_count": 3,
      "kept_count": 1,
      "reason": "full trim_report omitted to fit budget",
      "recover_via": {"instrument": "response_format:legacy", "hint": "full untrimmed response"}
    }
  ],
  "drill_pointers": [],
  "judgment_flags": [{"code": "budget_exceeded_after_trim", "detail": "2kb budget still exceeded after full trim."}]
}
```
`chapters` is `[]` (0 of 91 kept) while `chapter_count` still reads `91` — the count and the
array it purports to describe have gone out of sync. The single surviving `trim_report` entry
is the generic collapsed-summary marker, not a per-section entry naming `chapters`, and its
`recover_via.instrument` is `"response_format:legacy"`.

### `budget_kb: 8` (ordinary per-section trim — for contrast)
`chapters` kept 1 of 91 (`"life-arc chapters: floored to 1 (hard-cap)"`), `chapter_count: 91`
(still correct here because 1 ≠ 0 didn't trigger the "is this field even meaningful anymore"
question the way 2KB's full-zero does, but the field is never resynced in either case —
8KB just didn't drop it all the way to empty). Real per-section `trim_report` entries,
`recover_via.instrument: "kala_story_get"` (a real, actionable instrument).

### `budget_kb` omitted (default 40KB — no trim)
`chapters` full 91-entry array, `chapter_count: 91` (consistent because nothing was trimmed),
no `trim_report`, no `budget_kb_applied`.

Raw JSON for all three calls is reproduced verbatim above (full payloads captured in this
session's tool-call log; the 2KB and 8KB responses are large — the 2KB response is quoted in
full above since it's small; the 8KB/default responses ran ~15-20KB of chapter detail each and
are elided here to keep this document reasonable — every field named in this diagnosis was
read directly off the live response, not inferred).

**Second reproduce check — is `"response_format:legacy"` a real parameter?** No.
`KalaStoryInputShape` (`platform-mcp/src/tools/kala_views/story.ts:198-211`) declares exactly:
`chart_id`, `top_k`, `question_frame`, `budget_kb`. There is no `response_format` parameter on
this tool's schema — a caller acting on the `recover_via` hint would pass an argument the tool
rejects.

## 2. Claim decomposition

The finding bundles two genuinely distinct sub-claims:

- **F-44a (chapter_count/chapters desync):** at extreme budget pressure, `chapters` drops to
  an empty array while `chapter_count` (a sibling scalar computed from the same pre-trim data)
  keeps reporting the original count — the response asserts "91 chapters" and serves 0, with
  no field disclosing that the count is now stale relative to the array.
- **F-44b (non-actionable recover_via):** the honesty mechanism's own last-resort fallback
  points callers at an instrument (`response_format:legacy`) that does not exist on the calling
  tool's schema — the "how to get the rest" pointer is itself broken.

These are independently true and independently fixable — a fix that resyncs `chapter_count`
without fixing `recover_via` (or vice versa) closes only one sub-claim.

## 3. Mechanism → file:line (confirmed against current file; line numbers below are exact
against `platform-mcp/src/lib/response_budget.ts` as read in this session — 830 lines total,
not ~655; the corpus's "~655 lines per wc -l" note has drifted, flagging for the corpus owner)

### F-44b — the collapsed-fallback recover_via, TWO instances, byte-identical string

**Instance 1 — `finalizeMcpBudget`'s 1-entry-still-too-big fallback**, `response_budget.ts:402-410`:
```ts
    if (estimateBytes(content) > maxBytes) {
      // Even a 1-entry trim_report doesn't fit — collapse to a minimal summary.
      mutable['trim_report'] = [{
        path: '(trim_report)',
        original_count: result.trim_report?.length ?? 0,
        kept_count: 1,
        reason: 'full trim_report omitted to fit budget',
        recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },
      }]
    }
```
This is the exact code path `kala_story_get`'s `budget_kb: 2` call hit — `finalizeMcpBudget` is
called from `story.ts:781-785`. `finalizeMcpBudget` degrades the trim_report itself (biggest
entry first, then to this 1-entry summary, then — see below — abandons the merged
drill_pointers) once the base content + attached trim_report/drill_pointers still exceed the
byte ceiling. The literal string `'response_format:legacy'` is hardcoded here with no reference
to the calling tool's actual schema — `finalizeMcpBudget` has no way to know what recovery
parameter (if any) the caller's tool actually exposes, so it emits a generic placeholder that
happens to describe NO real tool in this codebase (`response_format` is not a parameter on
`kala_story_get`, and a repo-wide grep — see §4 — finds it is not a parameter on any tool that
reaches this code path).

**Instance 2 — `applyResponseBudget`'s own `'(whole response)'` branch**, `response_budget.ts:287-293`:
```ts
    trimReportByPath.set('(whole response)', {
      path: '(whole response)',
      original_count: before,
      kept_count: afterSections,
      reason: `still ${afterSections}B after flooring every section to 0 (ceiling ${maxBytes}B) — base content exceeds budget`,
      recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },
    })
```
Same literal string, same defect, a layer lower — this fires inside `applyResponseBudget` itself
(called by `finalizeMcpBudget` at line 370) when every declared section has been floored to 0 and
the content is *still* over budget before trim_report/drill_pointers attachment is even
considered. Any caller of bare `applyResponseBudget` (not wrapped in `finalizeMcpBudget`) would
surface this literal directly.

Both sites are honest about the mechanism itself (§N.8 is satisfied for "there is a real budget
check here, it isn't fabricated") but not honest about *actionability* — the string names an
instrument no schema exposes; §N.7 item 6 ("an honest null beats an invented judgment") is the
closer doctrinal match: the correct move when there is no real recovery instrument to name is an
honest `null`/generic hint text, not a plausible-sounding but nonexistent parameter name.

### F-44a — the `chapter_count`/`chapters` desync

`kala_story_get`'s handler, `platform-mcp/src/tools/kala_views/story.ts`:
- Line 764: `chapter_count: chapters.length` — computed ONCE, before any budget trimming, from
  the full 91-entry deduped array.
- Lines 769-779: `chapters` is declared as a `TrimmableSection` (`path: 'chapters'`, `minKeep: 5`,
  `getArray`/`setArray` closing over `response.chapters`) — this is the ONLY section declared for
  this tool besides the shared `kalaEvidenceTrimmableSection`.
- Lines 781-785: `finalizeMcpBudget(response, { maxKb: input.budget_kb ?? 40, sections, … })` —
  mutates `response.chapters` in place via the section's `setArray`. Nothing in
  `finalizeMcpBudget`/`applyResponseBudget` (nor in `story.ts`) re-derives or re-writes
  `response.chapter_count` after the array is cut.

`chapter_count` is not a scalar the budget mechanism was ever told about — it has no
`TrimmableSection` entry and is not in `IMMUNE_HONESTY_FIELDS`
(`response_budget.ts:56-101`, which lists `judgment_flags`, `empty_reason`,
`catalog_only_rows_in_page`, `receipt_state`, `budget_kb_applied`, `budget_kb_requested`,
`trim_report`, `completeness`, `epistemic`, `coverage`, `reading_contract`, `reading`,
`domain_completeness`, `completeness_directive`, `coverage_map`, `verdict` — `chapter_count` is
in none of these categories, and correctly so: it isn't a honesty-field, it's a plain derived
count that the array-trim invalidates). The mechanism is generic-by-design (§N.6/§N.7 doctrine:
one shared trimmer, not per-tool bespoke logic) and has no concept of "this scalar field is
derived from that array section and must move with it" — this is a caller-side omission, not a
`response_budget.ts` defect. `story.ts` is the file that needs to either (a) recompute
`chapter_count` from the post-trim `response.chapters.length` after `finalizeMcpBudget` returns,
or (b) declare `chapter_count` honestly as "pre-trim total" via a differently-named field and
leave a `served_count`/similar alongside it, or (c) route `chapter_count` through the same
mechanism the corpus already established elsewhere for this exact problem — see F-112's
"trim zeroes count but count field still shows original" defect class, explicitly named in this
same file's own doc-comment (`response_budget.ts:701-703`, the `CompositionReport.counts` field
docstring: *"honest even when a layer is absent due to budget (closes the 'trim zeroes count but
count field still shows original' defect class, F-112)"*). **F-44a is the same defect class as
F-112, on a different tool, via the OLDER subtraction-based mechanism** — F-112 was fixed for the
newer `SaraKernel`/`assembleSaraContent` composition path (assess_* tools only); `kala_story_get`
still uses the older `finalizeMcpBudget` path and was never given the equivalent fix.

## 4. Sibling census

### F-44b's defect class — `recover_via: { instrument: 'response_format:legacy', ... }`

Repo-wide grep for the literal string `response_format:legacy` and for `response_format'` as a
declared Zod parameter, scoped to `platform-mcp/src` (the read-only main-tip checkout,
`.claude/worktrees/par-s2-main-ro`):

```
platform-mcp/src/lib/response_budget.ts:292:      recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },
platform-mcp/src/lib/response_budget.ts:409:        recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },
```

Exactly 2 emission sites — both inside `response_budget.ts` itself (§3 above). Neither
`finalizeMcpBudget` caller (11 files: `registry_bridge.ts`, `register_p1_aliases.ts`,
`phala_outlook.ts`, `phala_event_anchors.ts`, `kala_views/elect.ts`, `kala_views/shared.ts`,
`kala_views/ahead.ts`, `kala_views/now.ts`, `kala_views/story.ts`,
`retrieval/holistic_bundle.ts`, `retrieval/register_gochara_windows.ts`) declares a
`response_format` parameter on ANY of its tools — grep for `response_format` across
`platform-mcp/src/tools/**` as a Zod shape key returns zero matches. **Every tool that reaches
either fallback site is equally affected** — this is not `kala_story_get`-specific; it is a
property of the shared mechanism, so the sibling count is "every caller of `finalizeMcpBudget`
or bare `applyResponseBudget` that can be driven hard enough over budget to hit PASS 2 exhaustion"
— i.e. all 11 files above, times however many tools each registers through it. No tool-specific
carve-out exists that would make one caller's `response_format:legacy` real while another's
isn't — it's uniformly fictional.

### F-44a's defect class — a scalar `*_count` field never resynced after its sibling array is trimmed

Grepped `platform-mcp/src/tools/kala_views/*.ts` and `platform-mcp/src/tools/register_p1_*.ts`
for `_count:` assignments that are computed from a `.length` BEFORE a `TrimmableSection`
covering the same array is declared, cross-referenced against each file's own trim wiring:

- `kala_views/story.ts:764` (`chapter_count: chapters.length`) vs. `chapters` TrimmableSection
  at `:772-778` — **confirmed defect** (this finding).
- `retrieval/kala_temporal.ts` (kala_bundle_get, uses `budgetMcpContent` per
  `response_budget.ts:634`) — grep for `_count:` in this file returns no top-level
  `*_count` scalar sibling to a trimmed array in the same shape (checked; not a sibling of this
  specific defect, though it shares the general "budget trim, honesty fields" family).
- `register_p1_ganita.ts` / `register_p1_synthesis.ts` (F-46's own weak path,
  `applyAutoBudgetToEnvelope`) — `autoDetectTrimmableSections` auto-declares array sections by
  key name but has no concept of a sibling `*_count` scalar either; any tool in these two files
  that ships a hand-written `*_count` alongside an auto-detected trimmable array (e.g.
  `projection_count` in `kala_projections_get`'s `register_p1_aliases.ts` response, or
  `parva_count`/`filters` in `kala_life_arc_get`'s content) is a **candidate sibling** for the
  same desync — not confirmed live in this session (would need a payload large enough to trigger
  a full-zero floor on the specific array those counts describe), but the mechanism is identical:
  no code path anywhere in `response_budget.ts` ever touches a `*_count` field, by construction
  (`autoDetectTrimmableSections` only ever discovers/declares literal arrays, never scans for a
  paired scalar). **This is a structural gap in the shared mechanism, not just `kala_story_get`'s
  bug** — every `*_count`/`*_total` scalar anywhere in this codebase that sits beside a
  budget-trimmable array is a latent instance, confirmed for `kala_story_get`, plausible for
  `kala_projections_get` (`projection_count`) and `kala_life_arc_get` (`parva_count`) pending a
  live trigger test with a small enough `budget_kb`.

## 5. Blast radius

- **§N.6/§N.7/§N.8 controls touched:** §N.6 (Serving Density) — a count field that lies about
  what's served is the density-honesty violation this principle exists to prevent. §N.7 item 6
  (honest null over invented judgment) — directly on point for F-44b's fictional
  `response_format:legacy`. §N.8 (Earned-Signal) — `chapter_count` claiming "91" with 0 actually
  served is exactly "a signal without a detector behind the specific claim it asserts."
- **CL-00 controls:** none of the 27 CL-00 controls are believed to directly assert on
  `kala_story_get`'s `chapter_count`/`chapters` parity or on `recover_via.instrument` validity —
  this is new ground, not a regression risk against an existing CL-00 assertion (unconfirmed
  without reading the CL-00 control list itself, which was out of scope for this diagnosis pass;
  SPEC stage should verify against `parisesa_gate.py`'s CL-00 cheap subset before build).
- **Other lanes sharing these files:** `response_budget.ts` is S2's own HOT file (exclusive
  lease per §2) — F-46 (this campaign, same stream) is the other finding in this same file; F-13,
  F-28, F-56, F-111, F-112, F-122 (CL-05), F-12/F-36/F-37/F-45 (CL-06), F-14/F-15/F-124/F-125
  (CL-14) are all S2 findings that may touch the same file — SEQUENCE, don't parallelize, edits
  to `response_budget.ts` within S2. `kala_views/story.ts` is explicitly S2-owned per §2.1's
  lease-conflict table (S2 owns `elect.ts`, `story.ts`, `ritual.ts`, `priority.ts`, `shared.ts`;
  S4 owns `now.ts`/`explain.ts`/`ahead.ts`/`upaya.ts` — `story.ts` is clean for S2, no
  cross-stream conflict for the F-44a half of this fix).
- **F-112 precedent:** the `CompositionReport.counts` mechanism already built for
  `assembleSaraContent` (assess_* tools, `response_budget.ts:693-710`) is the codebase's OWN
  prior fix for this exact defect class on the newer composition path — a SPEC for F-44a should
  look at replicating that "counts computed at assembly, honest even when a layer is omitted"
  pattern for `kala_story_get` rather than inventing a new resync mechanism.
- **A-09 sāra-kernel cross-reference (EKAVĀKYATĀ, `ekv/a-09-sara-kernel`):** confirmed via direct
  diff that `response_budget.ts` on this branch is **byte-identical** to the file on
  `origin/main` (`par-s2-main-ro`) — the A-09 `SaraKernel`/`assembleSaraContent` code
  (lines 641-830) is ALREADY merged/present on main; A-09 is not a pending merge risk for this
  file. `assembleSaraContent` is a wholly separate, non-subtractive composition path (used only
  by `assess_*` tools via `register_d8_assess_domain.ts` / `buildAssessResponse`) — it does not
  call `applyResponseBudget` or `finalizeMcpBudget` at all, so a fix to F-44's two subtractive
  fallback sites (lines 292, 402-410) cannot regress `assess_*`'s composition path. A SPEC/BUILD
  for F-44 should stay out of the `SaraKernel`/`assembleSaraContent` region
  (`response_budget.ts:641-830`) entirely — no reason to touch it, and touching it would be
  scope creep into a different, already-closed mechanism.
- **S6's F-141 note (per task brief):** F-141 (`ka_kshetra` state='lit' beside a denying
  `last_error`) is a §N.8 no-op-completion defect in the ORCHESTRATOR's build-state promotion
  predicate (`platform/python-sidecar/pipeline/orchestrator/**`), not in
  `response_budget.ts` or anywhere in the MCP serving layer. It shares this campaign's §N.8
  "signal without a real detector" doctrine with F-44a but touches no common file — no direct
  blast-radius interaction, only a shared doctrinal lineage.
- **Lease risk not enumerated in §2.1:** F-44's fix is entirely inside `response_budget.ts`
  (S2 HOT) and `kala_views/story.ts` (S2-owned per §2.1) — **no cross-stream lease conflict**
  for F-44, unlike F-46 (see F-46's own DIAGNOSIS.md §5).

## Evidence

Live JSON captured in this session's tool-call transcript for:
`kala_story_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, budget_kb=2)`,
`kala_story_get(..., budget_kb=8)`, `kala_story_get(..., budget_kb=<omitted>)`.
The `budget_kb=2` response is reproduced verbatim in §1 above (small enough to inline in full).
