---
lane: F-34 (exemplar spec for CL-13 — also closes the undiagnosed sibling in
  `computeGocharaElectionAvoidance` at zero extra diagnosis cost, per DIAGNOSIS.md §4/§6)
stream: S3_SATYA (spec + build)
stage: S — SPEC
author: SATYA-LEAD (S3)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — gochara_forecast_get / gochara_election_avoidance_get: disclose partial-horizon truncation

## 0. Scope of this spec

Covers **F-34** (`gochara_forecast_get` → `computeGocharaForecast`) and its confirmed sibling
`gochara_election_avoidance_get` → `computeGocharaElectionAvoidance` — same file
(`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`), same defect shape, same fix.
`computeGocharaActivation` (`gochara_activation_get`) is excluded — see §4. This is the CL-13
exemplar (plan §2 S3 / §5): the general predicate this spec establishes is restated as a
reference pattern in §9 for F-31/F-33/F-35/F-78/F-134 to adapt to their own files.

## 1. Root-cause statement

Both `computeGocharaForecast` (`:1717`) and `computeGocharaElectionAvoidance` (`:2044`) set
`provenance_envelope.empty_reason` from a bare `rawRows.length === 0` predicate with no
comparison anywhere in either function between the requested `dateRange.end` and how far
`kala_gochara_windows` has actually been materialized for this chart — so a query whose front
edge overlaps swept data returns served windows with `empty_reason: null` even when the back
2/3 of the requested range (e.g. the F-34 repro's 2084-02-01..2085-06-01 tail of a
2083-06-01..2085-06-01 request) is structurally unswept, and nothing in the response says so.

## 2. Files to change

### 2a. `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` — extend
`GocharaCoverage`/`computeGocharaCoverage` with the chart's true materialization horizon
(one new field, one new query, zero new call sites)

**What:** Add `materialized_through: string | null` to the `sweep_completeness` object on the
`GocharaCoverage` interface (`:884-888`) and its return value (`:1070-1083`). Populate it from
one new scalar aggregate query added to `computeGocharaCoverage`'s existing `Promise.all`
(`:996-1016`, currently 3 parallel queries — becomes 4):

```ts
platformQuery(
  `SELECT MAX(window_end)::text AS materialized_through
     FROM kala_gochara_windows
    WHERE chart_id = $1` + AUTHORITATIVE_GENERATION_FILTER,
  [chartId],
  principal
).then((r) => ({ rows: r.rows, ok: true as const }))
 .catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
```
then `materialized_through: horizonResp.ok ? (horizonResp.rows[0]?.['materialized_through'] as string | null ?? null) : null`.

**Why here, not a fresh per-call query in each of the two consuming functions:** both
`computeGocharaForecast` and `computeGocharaElectionAvoidance` already call
`computeGocharaCoverage` once, unconditionally, at their own top (`:1615`, `:1863`), and that
call already batches 3 queries in one `Promise.all`. Folding the horizon query into that same
batch means the two consuming functions get the field for free — no new await, no added
wall-clock latency (still one parallel round-trip), one new query total instead of two.

**Why not literally "zero new query" (reconsideration of the pointer in DIAGNOSIS.md §5):**
DIAGNOSIS.md's blast-radius note suggested reusing `coverage.sweep_completeness` as-is or a
fresh `MAX(window_end)` query. Read directly, `sweep_completeness` as it exists today
(`:884-888`, `:1070-1083`) is `{substeps_committed, source, note}` — an execution-count, not a
date. It genuinely carries no horizon bound to reuse. `rawRows` (already fetched by each
consuming function) was also considered and rejected: both queries `ORDER BY` with the requested
range's start ascending and apply `LIMIT`, so when `LIMIT` binds, the returned rows are the
*earliest*-window_start rows in range, not necessarily the latest-window_end ones — using their
`MAX(window_end)` in that case would understate the true horizon and could false-positive
`partial_truncation` on a request that LIMIT paginated, not one the sweep never reached. A single
indexed `MAX(window_end)` scoped to `chart_id` (matching the existing
`AUTHORITATIVE_GENERATION_FILTER` for generation-consistency) is the only value in-scope that is
actually correct independent of the caller's `date_range`/`LIMIT`/filters, so it is added — but
folded into the one already-existing coverage fetch, keeping the *net* new round-trip count at
one, not two.

### 2b. Same file — `computeGocharaForecast` (`:1701-1726`): add `coverage_disclosure`

**What:** After `coverage` is destructured (`:1615`), compute once, unconditionally (covers both
the empty and non-empty `rawRows` cases with one code path):

```ts
const materializedThrough = coverage.sweep_completeness.materialized_through
const partialTruncation = materializedThrough !== null && materializedThrough < dateRange.end
```

Add to `provenance_envelope` (`:1707-1726`, alongside `empty_reason`):

```ts
coverage_disclosure: {
  requested_range: dateRange,
  materialized_through: materializedThrough,
  partial_truncation: partialTruncation,
  truncation_note: partialTruncation
    ? `Requested range extends to ${dateRange.end}; this chart's kala_gochara_windows ` +
      `materialization (all event classes, all generations) currently reaches only through ` +
      `${materializedThrough}. Windows beyond that date have not been swept -- this is a ` +
      `coverage gap, not a signal that nothing happens after ${materializedThrough}. See ` +
      `coverage.sweep_completeness / coverage.event_classes_targeted_not_swept for what has ` +
      `and has not been swept for this chart.`
    : null,
},
```

**Why unconditional (not gated behind `rawRows.length > 0`):** this is precisely the fix for the
asymmetry named in DIAGNOSIS.md §2 C2 — the totally-empty path already discloses via
`empty_reason`; folding `coverage_disclosure` into that same path too (rather than only the
non-empty path) means both paths now carry the same shape, and the empty-path's own
`empty_reason` text (which already says "see coverage.sweep_completeness") gets a concrete date
to point at instead of a bare pointer.

**Scope boundary — the `not_covered` early return (`:1632-1646`) is NOT touched:** that branch is
a *domain*-coverage refusal (the requested `domain` isn't in this chart's event-class universe at
all — a different, already-fully-disclosed condition via `not_covered.cross_pointer`), orthogonal
to the *date-horizon* truncation this spec addresses. Adding `coverage_disclosure` there would
not close any part of C1/C2 and is excluded to keep this spec's diff mechanical and reviewable.

### 2c. Same file — `computeGocharaElectionAvoidance` (`:2031-2052`): identical shape

**What:** Same two-line derivation and same `coverage_disclosure` object, added to its
`provenance_envelope` (`:2036-2052`) immediately alongside its own `empty_reason` (`:2044-2050`).
Byte-identical logic to §2b — this function's `coverage` comes from the same
`computeGocharaCoverage` call (`:1863`), so §2a's one new field is already available here with no
further query changes.

**Deliberate non-inclusion of `is_adverse` in the horizon query:** the materialization horizon
(§2a) is intentionally computed over ALL rows for the chart, not `is_adverse = true` rows only.
`is_adverse` is a scored property of each materialized window, not a sweep-scope boundary — an
adverse-only `MAX(window_end)` could sit earlier than the true sweep horizon purely because no
window scored adverse near the tail (a genuinely clean result, correctly covered by this
function's own `empty_reason` text at `:2046-2048`, "an honestly clean window, not a fabricated
all-clear"). Scoping the horizon check to `is_adverse=true` would conflate that honest-clean case
with genuine under-sweep and false-positive `partial_truncation` on a fully-swept, genuinely
adverse-free tail. Using the same chart-wide horizon as §2b keeps the two disclosures answering
the same question ("how far did the sweep get") rather than two different ones.

## 3. Exit test

New file: `platform-mcp/src/tools/retrieval/register_gochara_windows_cl13.test.ts`

```ts
import { describe, it, expect, vi, afterEach } from 'vitest'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function mockFetch(opts: { maxWindowEnd: string; rowWindowEnd: string }) {
  vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
    const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
    if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
    if (sql.includes('MAX(window_end)')) {
      return Promise.resolve(fakeJsonResponse([{ materialized_through: opts.maxWindowEnd }]))
    }
    if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) {
      return Promise.resolve(fakeJsonResponse([]))
    }
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([]))
    if (sql.includes('build_substep_progress')) {
      return Promise.resolve(fakeJsonResponse([{ substeps_committed: 9, swept_event_classes: ['career'] }]))
    }
    // main overlap query — every returned row's window_end sits at the swept horizon
    return Promise.resolve(fakeJsonResponse([{
      id: 1, chart_id: CHART_ID, event_class: 'career', temporal_shape: 'point',
      window_start: '2083-06-01', window_end: opts.rowWindowEnd, peak_date: '2083-06-01',
      milestone_id: null, is_irreversibility_milestone: false, signed_intensity: 0.2,
      raw_intensity: 0.2, valence: 'benefic', calibration_state: 'structural_prior',
      suppression_state: null, contributing_systems: [], active_sentences: [],
      peak_basis: null, generation: 'v1', era_slice_key: null, term_breakdown: null,
      resolution: null, parent_window_id: null,
    }]))
  })
}

afterEach(() => vi.restoreAllMocks())

describe('CL-13 — partial-horizon truncation disclosure', () => {
  it('gochara_forecast_get: FAILS today — flags partial_truncation when the swept horizon ' +
     'falls short of a partially-overlapping requested range', async () => {
    mockFetch({ maxWindowEnd: '2084-01-31', rowWindowEnd: '2084-01-31' })
    const { computeGocharaForecast } = await import('./register_gochara_windows.js')
    const result = await computeGocharaForecast(
      CHART_ID, { start: '2083-06-01', end: '2085-06-01' },
      undefined, undefined, 50, { userId: 'test' } as never
    )
    const envelope = result['provenance_envelope'] as Record<string, unknown>
    expect(envelope['empty_reason']).toBeNull() // rows overlap the front — C2's existing correct case
    const disclosure = envelope['coverage_disclosure'] as Record<string, unknown>
    expect(disclosure).toBeDefined()
    expect(disclosure['materialized_through']).toBe('2084-01-31')
    expect(disclosure['partial_truncation']).toBe(true)
    expect(disclosure['truncation_note']).toMatch(/2084-01-31/)
  })

  it('gochara_election_avoidance_get: same shape, same sibling fix', async () => {
    mockFetch({ maxWindowEnd: '2084-01-31', rowWindowEnd: '2084-01-31' })
    const { computeGocharaElectionAvoidance } = await import('./register_gochara_windows.js')
    const result = await computeGocharaElectionAvoidance(
      CHART_ID, { start: '2083-06-01', end: '2085-06-01' },
      undefined, 50, { userId: 'test' } as never
    )
    const envelope = result['provenance_envelope'] as Record<string, unknown>
    const disclosure = envelope['coverage_disclosure'] as Record<string, unknown>
    expect(disclosure['partial_truncation']).toBe(true)
  })

  it('negative control: partial_truncation is false when the horizon covers the full request', async () => {
    mockFetch({ maxWindowEnd: '2085-06-01', rowWindowEnd: '2085-06-01' })
    const { computeGocharaForecast } = await import('./register_gochara_windows.js')
    const result = await computeGocharaForecast(
      CHART_ID, { start: '2083-06-01', end: '2085-06-01' },
      undefined, undefined, 50, { userId: 'test' } as never
    )
    const disclosure = (result['provenance_envelope'] as Record<string, unknown>)['coverage_disclosure'] as Record<string, unknown>
    expect(disclosure['partial_truncation']).toBe(false)
    expect(disclosure['truncation_note']).toBeNull()
  })
})

function fakeJsonResponse(rows: Record<string, unknown>[]) {
  return new Response(JSON.stringify({ rows }), { status: 200 })
}
```

**Fails today:** `provenance_envelope.coverage_disclosure` does not exist on today's code (the
key is never assigned in either function) — `envelope['coverage_disclosure']` is `undefined`,
so `expect(disclosure).toBeDefined()` and every property access on it fail immediately. This is
a genuine red, not a soft assertion: reproduces DIAGNOSIS.md's live finding (`empty_reason: null`
with 16 of 24 requested months unswept and nothing disclosing it) in a deterministic, mocked,
CI-runnable form. **Passes after §2a-2c land** for all three tests, using the mocking convention
already established in `register_gochara_windows_mr01.test.ts` (mock `globalThis.fetch`, branch
on SQL substring — no live DB required, consistent with the file's existing unit-test style).

## 4. Sibling sites covered / excluded

| Function | Tool | Covered? |
|---|---|---|
| `computeGocharaForecast` (`:1605`) | `gochara_forecast_get` | **YES — §2b** (this is F-34 itself) |
| `computeGocharaElectionAvoidance` (`:1854`) | `gochara_election_avoidance_get` | **YES — §2c.** Confirmed genuine sibling in DIAGNOSIS.md §4 (byte-identical `rawRows.length === 0` gate at `:2044`, no horizon check); not yet filed as its own numbered finding — closed here as a zero-extra-diagnosis-cost bonus per DIAGNOSIS.md §6. |
| `computeGocharaActivation` (`:1334`) | `gochara_activation_get` | **Excluded — different shape, see below.** |

**`computeGocharaActivation` exclusion reasoning:** it takes a single `asOfDate` point, not a
`dateRange` (`:1336`, `WHERE ... window_start <= $2 AND window_end >= $2`) — there is no "front
of the range overlaps swept data, back does not" case to disclose; the query is binary
(swept-for-that-date or not) and its `empty_reason` at `:1429-1432` is a correct, unqualified
zero-rows check for that shape. **Coverage-honesty caveat worth flagging, not fixing here** (per
DIAGNOSIS.md §4's own note): if `asOfDate` itself lands beyond the chart's materialization
horizon, `computeGocharaActivation` will also report `empty_reason: 'an honest zero-activation
result'` when the true state is "this date has never been swept," which is the same underlying
asymmetry one level down — but fixing it would require a *different* predicate shape (a single-date
horizon check, not a range-truncation one) and is not part of C1/C2 as filed. Recommend a
follow-up note for whoever specs a possible eighth CL-13-adjacent finding, not built here.

**No other CL-13 lane's file** (`assess_health`, `ganita_dasha_periods_get`,
`mimamsa_insight_get`, `kala_field_snapshots`, `judgment_query`) is touched by this spec — those
are F-31/F-33/F-35/F-78/F-134, each its own file, each needing its own Stage-D mechanism trace
against the reference pattern in §9.

**Cross-stream flag (not resolved here):** S2's `lanes/F-14/SPEC.md` §0 claims F-31
(`assess_health` missing disclosure) is closed by the *same* fix as its own F-14/F-15/F-124
(missing `attachDomainCompleteness`/`attachDomainReading` call-sites in `registry_bridge.ts`) —
a different root-cause class than CL-13's "disclosure gated on total emptiness" pattern this spec
addresses. Whoever specs F-31 for CL-13 should read S2's F-14 spec first: F-31 may need either
S2's fix, this spec's pattern, both, or a reconciliation between the two specs — not re-diagnosed
from zero. Flagging only; out of scope to resolve in this document.

## 5. Recurrence guard

The exit test's negative-control case (§3, third test) asserts `partial_truncation: false` when
the horizon covers the full requested range — this is what prevents a future edit from making the
predicate over-fire (false positives are as much a defect as the original silence: they would
train callers to distrust a disclosure field that cries wolf). No existing lint enforces the
"date-range query needs a horizon-aware empty/partial disclosure" shape across the codebase yet;
recommend (out of this spec's build scope, flagged for the conductor) a follow-up static check —
"every exported `compute*` function in `retrieval/**` whose signature takes a `dateRange` param
must set both `empty_reason` and `coverage_disclosure` on its `provenance_envelope`" — modeled on
the existing `fact-category-pin-lint` CI guard pattern (`check_fact_category_pinning.py`), as the
CL-13 class's own recurrence guard once all six lanes are built. This spec's own two call sites
are covered by the exit test in the meantime.

## 6. Dependencies and rollback

**No DB migration.** `kala_gochara_windows.window_end` already exists and is indexed via the
table's existing chart_id/window_start/window_end access pattern (both consuming functions
already filter on it). No new table, no new column. Purely additive: one new field on
`GocharaCoverage.sweep_completeness`, one new field (`coverage_disclosure`) on two functions'
`provenance_envelope`. No existing field is removed, renamed, or changed in meaning — safe for
any consumer that doesn't yet know the new keys exist. **No other lane must land first.**
`register_gochara_windows.ts` was unowned in the plan §2 OWNS map at the time this spec was
originally drafted — that framing was wrong (VERIFIER wave-1 caught it: "inside S3's exclusive
lease" asserted a pre-existing lease that did not exist). The conductor has since granted this
file to S3 formally (`LEASES.json`, in recognition of S3 being the working owner and F-34 being
the CL-13 exemplar the other four findings depend on) — the lease is now real, but as of a
conductor grant, not as an inherited pre-existing claim. **Rollback:** revert the single commit;
no schema or contract change to unwind.

**One build-time verification item, not a dependency:** `finalizeMcpBudget` (`response_budget.ts`)
measures the *whole* content object (windows + coverage + provenance_envelope) as one unit per
the W3 fix documented at this file's own top-of-file comment (`:96-103`) — Build should confirm
in the exit test's live-shape assertion that `coverage_disclosure` (a handful of short strings and
one boolean) survives budget trimming intact; it is negligible relative to the `windows` array,
the section the trimmer actually targets (`windowsSection(...)`), so no `hardFloor` declaration is
expected to be needed, but Build should not assume this without checking the trimmed output.

## 7. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Spec element |
|---|---|
| C1 — the tool silently truncates at the swept horizon when a query partially overlaps it | §2a (new `materialized_through` field, chart-wide horizon) + §2b/§2c (`coverage_disclosure`/`partial_truncation` predicate added to both `computeGocharaForecast` and `computeGocharaElectionAvoidance`) |
| C2 — the same tool discloses correctly for the *total*-emptiness case but not the partial one (asymmetric honesty) | §2b/§2c's unconditional (not `rawRows.length`-gated) placement of `coverage_disclosure` closes the asymmetry: both the empty and non-empty paths now carry the same field, and `empty_reason`'s existing pointer to `coverage.sweep_completeness` (`:1721`, `:2047`) now resolves to a concrete date via §2a instead of a bare directive to "go check" |
| Sibling — `computeGocharaElectionAvoidance` has the identical gate, unfiled as its own finding | §2c (byte-identical fix, zero extra diagnosis cost) |
| Exclusion — `computeGocharaActivation` is a different (point-query) shape | §4 (excluded, reasoned; caveat flagged, not built) |

## 8. Exemplar status

Recommend: this spec proceeds to Stage R first (it is the CL-13 pathfinder per plan §5); once
COMPLETE, §9 below is the pattern the other five CL-13 lanes cite rather than re-derive.

## 9. Reference pattern for CL-13 siblings

**The general predicate (lift this shape, not this code):** every CL-13 finding is a surface that
answers a request scoped by some dimension — a date range, a depth tier, a requested set of
fields/systems, a requested window — and that surface's honesty mechanism (an `empty_reason`,
`not_covered`, or similar flag) only fires on *total* non-service, leaving a *partial* shortfall
(served less of the dimension than was asked for) silently indistinguishable from full service.
The fix is always the same three-part shape, adapted to the surface's own data: (1) compute — or,
preferably, locate an *already-computed* value already resident in the same request's pipeline
representing — the actual extent of what could be/was served on the requested dimension (here:
`materialized_through`, the true swept-date ceiling; for a depth-tiered surface it might be
"deepest tier actually populated"; for a multi-system surface, "systems actually queried vs.
requested"); (2) compare the requested extent to the actual extent with an explicit predicate
(here: `dateRange.end` vs. `materialized_through`) and expose both the comparison inputs and the
boolean result structurally, never only in prose; (3) place the result unconditionally alongside
the existing empty/not-covered disclosure, not gated behind it, so the two mechanisms jointly
cover the full space (total-absence + partial-shortfall) instead of the second silently
inheriting the first's blind spot. Before adding a query to compute (1), check whether the
request's own pipeline already computes something adjacent (as this spec initially assumed of
`coverage.sweep_completeness` and, on reading the code, found it did *not* actually carry a date —
extend the adjacent structure to genuinely carry the bound, as §2a does, rather than trust an
assumption that it already does or bolt on an unrelated new field). F-31/F-33/F-35/F-78/F-134 each
find their own version of "the actual extent" in their own file (`assess_health`'s domain/reading
completeness, `ganita_dasha_periods_get`'s dasha-depth coverage, `mimamsa_insight_get`'s
calibration-population extent, `kala_field_snapshots`'s snapshot horizon, `judgment_query`'s
grounding-layer completeness) — none of them can reuse this file's code, but every one of them
should be able to point at this section and say "same three-part shape, different dimension."
