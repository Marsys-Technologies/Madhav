---
lane: F-134
stream: S3_SATYA (spec + build)
stage: S (SPEC)
author: SATYA-LEAD (sonnet)
tier: TIER4-POLISH
status: DRAFT — awaiting VERIFIER review
---

## Relationship to F-34 (CL-13 exemplar) — read this first

One of the five CL-13 siblings the plan (§2/§5) designates for exemplar-then-replicate: F-34
(`lanes/F-34/SPEC.md` §9) establishes the reviewed general shape — locate the surface's own
"actual extent served/valid" signal, compare it to what the response presents as current/upcoming,
expose the gap as a structured field rather than leaving it inferable only from raw dates. Here
the dimension is temporal validity (`peak_date` vs. `now_context_date`) rather than F-34's
horizon-coverage dimension, but the shape is the same three steps. Stage R should take "expose the
comparison structurally" as settled by F-34 and focus review on whether `is_past_peak`/the
`upcoming_window_count` treatment below is the correct instantiation for this surface.

# LEASE NOTE (read first)

`reading_checklist.ts` (the actual defect site) and its two call sites
(`register_d9_judgment.ts`, `register_d8_assess_domain.ts`) are **not** in any stream's
`OWNS` list in `PARISESA_EXECUTION_PLAN_v1_0.md §2`. Stage-D's own blast-radius section
flagged this and recommended posting `PAR-F-134-NEEDS-LEASE
platform/src/lib/retrieval/registry/layers/reading_checklist.ts` for conductor
resolution. Per this lane's build instructions, S3 is writing this SPEC as
**S3-builds-directly** (closest in spirit to S3's disclosure/truth-telling territory,
and the sibling CL-13 exemplar F-34 lives in S3's own lease), **pending final conductor
confirmation** of the lease grant. This spec does not depend on that confirmation to be
reviewable or buildable: every file/line named below is read fresh from the live tree,
the fix is self-contained to `reading_checklist.ts` + two call sites, and nothing here
assumes an S3-only fact. If the conductor routes the build to a different stream, this
document transfers unchanged — "specs travel; leases don't" (plan §2.1).

**Volatility note:** at Stage-D/S time this repo is under active concurrent build
traffic from other PARIŚEṢA lanes. Line numbers below were re-verified fresh via `grep
-n` immediately before writing this spec (confirmed twice, stable). BUILD must re-`grep`
for the anchors (`export async function fetchGocharaSweep`, `gochara_sweep: {`) rather
than trusting these line numbers blindly if the file has moved by build time.

# 1. Root-cause statement

`fetchGocharaSweep` (`platform/src/lib/retrieval/registry/layers/reading_checklist.ts:274`)
selects and ranks `kala_gochara_windows` rows with a pure **interval-overlap** predicate
(`window_end >= start AND window_start <= end`, `:326`) and ranks purely by
`ABS(signed_intensity)` (`:330`) — neither the selection nor the ranking nor the row
mapping (`:339-347`) ever compares a window's `peak_date` against the query's own `start`
(`as_of_date`, i.e. "now"), so a window whose peak already occurred is served identically
to a genuinely future one, with no field anywhere in `GocharaSweepResult` letting a
caller tell the two apart.

# 2. Files to change

## 2a. `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`

**What:** add a per-window `is_past_peak: boolean | null` field and an aggregate
`past_peak_window_count: number` field, computed by comparing each row's `peak_date`
against `start` (the call's own `as_of_date`) — no new query, reuses `start` which is
already in scope.

**Why:** this is the single shared function both call sites depend on (confirmed by
DIAGNOSIS §4: `fetchGocharaSweep` has exactly two importers, no third). Fixing it here
fixes both call sites' `top_windows` shape for free — the CL-13 "exemplar-then-replicate"
pattern (F-34) applied within one function instead of across siblings, because this
finding's siblings share one function rather than one predicate copied N times.

**Type changes** (`GocharaSweepWindow` interface, currently `:245-253`):
```ts
export interface GocharaSweepWindow {
  event_class: string
  temporal_shape: string | null
  window_start: string | null
  window_end: string | null
  peak_date: string | null
  valence: string | null
  is_adverse: boolean | null
  is_past_peak: boolean | null   // NEW — null when peak_date is null (honest "can't tell", §N.7 item 6)
}
```

**`GocharaSweepResult` interface** (currently `:255-263`) — add one new field, leave
`upcoming_window_count` untouched (see §7 for why it is not renamed or redefined):
```ts
export interface GocharaSweepResult {
  domain_covered: boolean
  upcoming_window_count: number
  past_peak_window_count: number   // NEW
  windows: GocharaSweepWindow[]
  valence_breakdown: Record<string, number>
  window_range: { start: string; end: string }
  note: string
  available: boolean
}
```

**Implementation** — inside `fetchGocharaSweep`, after the main window query (currently
`:316-333`) and its `out.upcoming_window_count = res.rows.length` line (`:334`), before
the `out.windows = res.rows.slice(0, 5).map(...)` line (`:339-347`):
```ts
    out.upcoming_window_count = res.rows.length
    const isPastPeak = (peakDate: string | null): boolean | null =>
      peakDate === null ? null : peakDate < start
    out.past_peak_window_count = res.rows.filter(r => isPastPeak(r.peak_date) === true).length
    for (const r of res.rows) {
      const v = r.valence ?? 'unknown'
      out.valence_breakdown[v] = (out.valence_breakdown[v] ?? 0) + 1
    }
    out.windows = res.rows.slice(0, 5).map(r => ({
      event_class: r.event_class,
      temporal_shape: r.temporal_shape,
      window_start: r.window_start,
      window_end: r.window_end,
      peak_date: r.peak_date,
      valence: r.valence,
      is_adverse: r.is_adverse,
      is_past_peak: isPastPeak(r.peak_date),
    }))
```
`start` is already the function's local binding for `as_of_date` (`:280`) — comparing two
`'YYYY-MM-DD'` strings lexically is a valid ordering test (same format the SQL layer
itself already uses for the `$3`/`$4` bind params), so no `Date` parsing is introduced.
`past_peak_window_count` is computed over the FULL `res.rows` set (all overlap-matched
rows, up to the `LIMIT 200`), matching how `upcoming_window_count` is already scoped —
not just the top-5 slice that becomes `windows` — so the count is honest even when a
past-peaked window doesn't make the top-5 cut.

Also update the docstring comment above the interfaces / function (currently describing
"top windows by |intensity| + a valence tally") to note the new past-peak disclosure, one
line, non-functional.

## 2b. `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`

**What:** (i) pass `past_peak_window_count` through into the served `gochara_sweep`
object; (ii) add one `judgment_flags` entry when the top-ranked served window has already
peaked.

**Why:** (i) is a direct passthrough of the new aggregate field into the response this
lane's own `reproduce_cmd` calls. (ii) closes the finding's most specific complaint — "its
**top-ranked** window ... is presented inside the 'upcoming' set" — at the layer callers
actually scan for salience in this tool (`judgment_flags`; this file already uses this
exact idiom for `gochara_domain_not_covered`, `sensitive_degree_firings_present`, etc. —
not a new mechanism, the established one).

**Current** (`gochara_sweep` object construction, `:1186-1194`):
```ts
            gochara_sweep: {
              domain: spec.signal_domain,
              domain_covered: gochara.domain_covered,
              upcoming_window_count: gochara.upcoming_window_count,
              valence_breakdown: gochara.valence_breakdown,
              window_range: gochara.window_range,
              top_windows: gochara.windows,
              note: gochara.note,
            },
```
**Fixed:**
```ts
            gochara_sweep: {
              domain: spec.signal_domain,
              domain_covered: gochara.domain_covered,
              upcoming_window_count: gochara.upcoming_window_count,
              past_peak_window_count: gochara.past_peak_window_count,
              valence_breakdown: gochara.valence_breakdown,
              window_range: gochara.window_range,
              top_windows: gochara.windows,
              note: gochara.note,
            },
```
`top_windows: gochara.windows` needs no edit — each element already carries the new
`is_past_peak` field once §2a lands (the array is passed through, not remapped).

**Flag addition** — near the existing gochara block (currently `:1109-1116`, right after
`const gochara = await fetchGocharaSweep(...)` and its existing
`gochara_domain_not_covered` flag), add a second conditional flag:
```ts
      const gochara = await fetchGocharaSweep(chart_id, spec.signal_domain, as_of_date)
      if (gochara.available && !gochara.domain_covered) {
        judgment_flags.push(judgmentFlag(
          'gochara_domain_not_covered',
          `the gochara sweep does not cover the '${spec.signal_domain}' domain ` +
          'for this chart — its silence here is NOT an all-clear (S4-05 discipline); drill kala_windows_get.',
        ))
      }
      if (gochara.windows[0]?.is_past_peak === true) {
        judgment_flags.push(judgmentFlag(
          'gochara_top_window_already_peaked',
          `the top-ranked (highest |intensity|) window in gochara_sweep.top_windows ` +
          `('${gochara.windows[0].event_class}', peak_date=${gochara.windows[0].peak_date}) ` +
          `already peaked before as_of_date=${as_of_date} — served for context (it is still ` +
          `inside the query's date-overlap horizon), but its intensity ranking should not be ` +
          `read as a forward-looking signal. See top_windows[].is_past_peak for the full set.`,
          'info',
        ))
      }
```
(Signature/third-arg convention — `'info'`/`'warning'` severity string — matches the
existing `bearing_yogas_no_domain_match` etc. call shape in the sibling
`register_d8_assess_domain.ts` and the two-arg calls already in this file; BUILD confirms
`judgmentFlag`'s actual signature at the anchor before writing this call, since the two
call sites in this file use both 2-arg and 3-arg forms today.)

## 2c. `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`

**What:** pass `past_peak_window_count` through into the served `gochara_sweep` object
(same passthrough as 2b-i). No flag addition here (see §4 for why).

**Current** (`gochara_sweep` object construction, `:1148-1156`):
```ts
        gochara_sweep: {
          domain: t5SignalDomain,
          domain_covered: t5Gochara.domain_covered,
          upcoming_window_count: t5Gochara.upcoming_window_count,
          valence_breakdown: t5Gochara.valence_breakdown,
          window_range: t5Gochara.window_range,
          top_windows: t5Gochara.windows,
          note: t5Gochara.note,
        },
```
**Fixed:**
```ts
        gochara_sweep: {
          domain: t5SignalDomain,
          domain_covered: t5Gochara.domain_covered,
          upcoming_window_count: t5Gochara.upcoming_window_count,
          past_peak_window_count: t5Gochara.past_peak_window_count,
          valence_breakdown: t5Gochara.valence_breakdown,
          window_range: t5Gochara.window_range,
          top_windows: t5Gochara.windows,
          note: t5Gochara.note,
        },
```
Again `top_windows: t5Gochara.windows` needs no edit — `is_past_peak` flows through
automatically per-window once §2a lands, for all four `assess_*` tools (`assess_wealth`,
`assess_career`, `assess_marriage`, `assess_health`) that share this one call site.

# 3. Design choice: flag in place, not exclude — justification

The finding's own `mechanism` field (manifest, verbatim): *"no `is_past_peak` /
`already_occurred` flag distinguishes it from a genuinely upcoming peak"* — the corpus
names the fix as a **missing flag**, not a missing filter. The `claim` field complains the
window is "presented... alongside... future... windows with no flag distinguishing" —
again, a disclosure gap, not an inclusion gap. Excluding past-peaked windows from
`top_windows`/the count would:
- violate B.10/§N.6 (never silently drop data the caller didn't ask to have dropped) —
  an already-peaked `major_gain` window is still classically meaningful context (e.g. "the
  biggest hit of this yoga already landed"), and dropping it converts an honest disclosure
  gap into a new, different silent omission;
- break the CL-13 doctrine explicitly named in this lane's build brief: "disclose the
  degradation structurally, don't just describe it in prose (or, here, don't just delete
  it)" — the F-34 exemplar's fix pattern is a structured field, not a narrower filter;
- risk shrinking `top_windows` below a caller-visible count in cases where most
  intensity-ranked matches happen to be past-peaked, silently thinning an already-compact
  top-5 slice for no stated reason.

Flagging in place (per-window `is_past_peak` + aggregate `past_peak_window_count` + a
`judgment_query`-level salience flag) preserves every existing byte of served data,
adds the exact structural distinction the finding says is missing, and lets a caller
choose to filter client-side if it wants a peak-only forward view — which the flag itself
now makes possible for the first time.

# 4. Exit test

New test file:
`platform/src/lib/retrieval/registry/layers/__tests__/reading_checklist.fetch_gochara_sweep_past_peak.test.ts`

Follows the existing sibling test's mock convention exactly
(`reading_checklist.fetch_gochara_sweep.test.ts`, mocks `@/lib/db/client`, no live DB):

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { fetchGocharaSweep } from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('fetchGocharaSweep — F-134 past-peak disclosure', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('flags an already-peaked window with is_past_peak=true and counts it, ' +
     'while a genuinely future window gets is_past_peak=false', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '3' }] }) // coverage probe
      .mockResolvedValueOnce({
        rows: [
          { // reproduces F-134's live top_windows[0]: peaked over a year before as_of_date
            event_class: 'major_gain', temporal_shape: 'interval',
            window_start: '2024-02-05', window_end: '2034-01-30',
            peak_date: '2025-04-27', valence: 'gain', is_adverse: false,
          },
          { // genuinely future peak — must NOT be flagged
            event_class: 'major_loss', temporal_shape: 'interval',
            window_start: '2024-02-05', window_end: '2034-01-30',
            peak_date: '2030-08-14', valence: 'loss', is_adverse: true,
          },
          { // null peak_date — must be null (honest "can't tell"), not true/false
            event_class: 'financial_deception', temporal_shape: 'interval',
            window_start: '2024-02-05', window_end: '2034-01-30',
            peak_date: null, valence: 'loss', is_adverse: true,
          },
        ],
      })

    const result = await fetchGocharaSweep(CHART_ID, 'wealth', '2026-08-16', 3)

    expect(result.windows[0].is_past_peak).toBe(true)
    expect(result.windows[1].is_past_peak).toBe(false)
    expect(result.windows[2].is_past_peak).toBeNull()
    expect(result.past_peak_window_count).toBe(1)
    // upcoming_window_count is unchanged in meaning — still the raw overlap-matched count
    expect(result.upcoming_window_count).toBe(3)
  })
})
```

**Fails today:** `is_past_peak` and `past_peak_window_count` do not exist anywhere in
`GocharaSweepWindow`/`GocharaSweepResult` or the `fetchGocharaSweep` implementation — the
first two `expect`s fail with `undefined !== true` / `undefined !== false`
(TypeScript itself would also reject `result.windows[0].is_past_peak` as a property that
doesn't exist on the type, so this test does not currently compile against the live
interfaces — a stronger red than a runtime assertion failure). **Passes after:** all four
assertions hold given §2a's implementation.

A second, small assertion can be added to `register_d9_judgment.ts`'s existing
integration test (`__tests__/register_d9_judgment.integration.test.ts`) or a new focused
test, confirming the `gochara_top_window_already_peaked` flag fires on a fixture shaped
like the live repro — left to BUILD to wire into whichever of the two existing
`register_d9_judgment` test files fits the established fixture-construction pattern there,
since the reading_checklist-level test above is what makes the exit test's own red→green
claim unambiguous and file-size-bounded; VERIFIER may request the second assertion be
added before Stage-R sign-off if it judges the flag itself needs direct coverage.

# 5. Sibling sites covered

Both of `fetchGocharaSweep`'s two importers (DIAGNOSIS §4's exhaustive grep — confirmed no
third exists):
- `register_d9_judgment.ts` (`judgment_query`'s `gochara_sweep`) — §2b, this finding's own
  `reproduce_cmd`.
- `register_d8_assess_domain.ts` (`assess_wealth`/`assess_career`/`assess_marriage`/
  `assess_health` via the shared domain dispatcher) — §2c, the genuine sibling DIAGNOSIS
  flagged as "not yet re-reproduced live but byte-identical code path." Both are covered
  by the same §2a type/field change; §2c's `top_windows` gets `is_past_peak` for free
  without any local code change beyond the `past_peak_window_count` passthrough line.

No third call site is excluded because none exists (grep-confirmed both at Stage-D and
re-confirmed fresh for this spec).

# 6. Recurrence guard

The exit test (§4) type-checks against `GocharaSweepWindow`/`GocharaSweepResult` directly
— any future refactor that drops `is_past_peak` or `past_peak_window_count` from the
interfaces, or stops populating them, fails this test at both the TypeScript-compile layer
(missing property) and the runtime-assertion layer. Because `fetchGocharaSweep` is the
single shared implementation (not copied per-caller), there is no per-site recurrence risk
the way CL-11's ~22-site helper defaulting had — a third future caller of
`fetchGocharaSweep` inherits the fix automatically, by construction, the same way the two
existing callers do. No additional lint is proposed; the type signature itself is the
guard.

# 7. Dependencies and rollback

No DB migration, no schema change — `peak_date` is an existing column already selected by
the query; the fix is pure application-layer disclosure. No other lane's build must land
first. `upcoming_window_count` is deliberately left with its current field name and
current semantics (raw overlap-matched row count) rather than renamed or redefined to mean
"genuinely-still-ahead count" — renaming would be a breaking change to the existing
passing test `reading_checklist.fetch_gochara_sweep.test.ts:79`
(`expect(result.upcoming_window_count).toBe(1)`) and to both call sites' already-live
`reading_checklist_units[].count` fields, for a rename that isn't what the finding asked
for (see §3). Rollback: revert the single commit spanning the three files in §2; all three
changes are additive (new interface fields, new object-literal keys, one new conditional
flag block) — nothing removed, nothing renamed, so a revert is a clean no-op regression to
today's (defective) behavior with zero migration or state cleanup.

# 8. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Spec element | How it's closed |
|---|---|---|
| C1: reports `upcoming_window_count=3` with `window_range` starting "now" | §2a (field left as-is, documented) + §7 (explicit rationale for not redefining it) | The count's existing meaning (raw overlap-match) is now legible in context because `past_peak_window_count` sits next to it — a caller can now see 1 of the 3 is past-peak instead of inferring nothing. |
| C2: top-ranked window's `peak_date` is >1 year in the past despite being served inside "upcoming" | §2a (`is_past_peak` per window) + §2b flag (`gochara_top_window_already_peaked`, specifically keys off `windows[0]`) | Directly targeted — this is the exact case the new top-window flag detects. |
| C3: already-peaked window sits alongside genuinely future windows with no structural distinction | §2a (`is_past_peak: true/false` on every window in the array, not just the top one) | Every element of `top_windows` now carries the distinguishing field; §3 explains why elements are kept, not removed. |
| C4: no flag (`is_past_peak`/`already_occurred` or equivalent) exists anywhere in the response | §2a (`is_past_peak` field name — literally the name the finding's own `mechanism` field proposes) + §2b/§2c passthrough of `past_peak_window_count` into both served responses | The exact named gap is filled with the exact named field, in both callers. |
