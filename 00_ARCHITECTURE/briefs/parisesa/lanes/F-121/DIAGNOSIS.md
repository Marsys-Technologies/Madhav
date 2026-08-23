# F-121 DIAGNOSIS — kala_now_get dasha_sandhi reports "no junction" while a Sūkṣma-level sandhi is active

stream: S4 VĀCA · tier: TIER3-EXPERIENCE · exemplar candidate (paired with F-120)

## Live Reproduction

Both calls made live against canonical chart `482012f1-710e-4a25-994a-93821f5871aa`.

**`kala_now_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa)`** (as_of resolved to `2026-08-16`):

```json
"dasha_sandhi": {
  "as_of_date": "2026-08-16",
  "band_convention": "LITE convention (item 1-lite, wave W1): each daśā-period boundary (its own start date AND its own end date) carries a band of ± round(3% × that period's own span in days), per KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2 (\"configurable orb, last/first ~3% of period span\"). Simplification: uses the SAME period's span on both sides of each boundary rather than the full classical asymmetric last-outgoing/first-incoming convention (which needs the adjacent period too) — that full two-period, all-level, both-direction calendar is item 1-full (W3).",
  "bands": [
    {"level_n":1,"level_name":"Mahadasha","lord_graha":"Mercury","boundary_kind":"period_start","boundary_date":"2010-08-18","is_now_within_band":false},
    {"level_n":1,"level_name":"Mahadasha","lord_graha":"Mercury","boundary_kind":"period_end","boundary_date":"2027-08-18","is_now_within_band":false},
    {"level_n":2,"level_name":"Antardasha","lord_graha":"Saturn","boundary_kind":"period_start","boundary_date":"2024-12-08","is_now_within_band":false},
    {"level_n":2,"level_name":"Antardasha","lord_graha":"Saturn","boundary_kind":"period_end","boundary_date":"2027-08-18","is_now_within_band":false}
  ]
}
```

`coverage` array entry: `{"concept":"dasha_sandhi","state":"computed"}` — flat, no scope qualifier, no
sibling "levels 3-4: not_computed" entry.

**`ganita_dasha_periods_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, ayanamsha_id='lahiri_chitrapaksha', as_of_date='2026-08-15', all_levels=true)`**:

`rows[3]` (level_n=4, Sūkṣma):
```json
{
  "level_n": 4, "lord_graha": "Mercury", "lord_sign": "Capricorn",
  "start_date": "2026-08-13", "end_date": "2026-08-25",
  "sandhi_flag": true, ...
}
```

Confirmed: `as_of_date=2026-08-15` falls inside `2026-08-13..2026-08-25`, and this L1-authoritative row
already carries `sandhi_flag: true` for that exact window. Re-run against `as_of=2026-08-16` (the date
`kala_now_get` actually resolved "now" to) — the Sūkṣma period `2026-08-13..2026-08-25` still contains
that date, so the same `sandhi_flag=true` row is active at the moment `kala_now_get` was queried.

**Reproduces live.** All four served bands are `is_now_within_band=false`; the genuinely active
level-4 sandhi is invisible to the response.

## Claim Decomposition

| # | Claim | Verified |
|---|---|---|
| a | `dasha_sandhi` block computes only 4 bands over levels 1-2 | TRUE — `bands` contains exactly 2 boundaries × 2 levels (Mahā start/end, Antar start/end); no level 3 (Pratyantar) or level 4 (Sūkṣma) bands ever appear |
| b | All 4 report `is_now_within_band=false` | TRUE — verified in live response above |
| c | A genuinely-active level-4 sandhi exists per `ganita_dasha_periods_get` | TRUE — `sandhi_flag=true` on the Sūkṣma row spanning 2026-08-13..2026-08-25, containing both the query's `as_of_date` and the date `kala_now_get` resolved "now" to |
| d | `coverage` array marks `dasha_sandhi` as flatly "computed" | TRUE — `{"concept":"dasha_sandhi","state":"computed"}`, no companion entry for levels 3-4 |
| e | `band_convention` prose discloses the 2-vs-1-period simplification but not the level restriction | TRUE — see full string in Mechanism section; it names the "SAME period's span on both sides" simplification and points to "item 1-full (W3)" for the full **two-period, both-direction** calendar, but never states that Pratyantardaśā/Sūkṣmadaśā (levels 3-4) are not examined at all in the lite pass |

## Mechanism (file:line, quoted code)

**Where `dasha_sandhi.bands` is constructed** —
`platform-mcp/src/tools/kala_views/now.ts:962-989` (`computeDashaSandhi`), fed by
`platform-mcp/src/tools/kala_views/now.ts:875-900` (`fetchVimshottariMdAdBoundaries`).

The level cap is set here, `now.ts:882-885`:

```ts
async function fetchVimshottariMdAdBoundaries(...) {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_active_dashas',
    { chart_id: chartId, date: dateISO, ayanamsha_id: ayanamshaId, systems: 'vimshottari', max_level: 2 },
    principal,
  )
```

`max_level: 2` is hardcoded — it never requests level 3 (Pratyantardaśā) or level 4 (Sūkṣmadaśā) rows
from `query_active_dashas` at all. This is confirmed at the capability itself,
`platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts:72` (parameter doc:
"Deepest level to report (1=Mahā, 2=Antar, 3=Pratyantar). Default 3") and `:97`
(`Math.min(Math.max(Number(args['max_level'] ?? MAX_LEVEL_DEFAULT), 1), 5)`) — the capability itself
defaults to level 3 and supports up to level 5; `now.ts` explicitly requests LESS than the
capability's own default.

**Where `is_now_within_band` is computed per band** — `now.ts:937-960` (`buildBoundaryBand`):

```ts
function buildBoundaryBand(
  entry: ActiveDashaBoundaryEntry,
  boundaryKind: 'period_start' | 'period_end',
  asOfDate: string,
): DashaSandhiBand | null {
  if (!entry.start_date || !entry.end_date) return null
  const spanDays = daysBetween(entry.start_date, entry.end_date)
  if (spanDays <= 0) return null
  const bandWidthDays = Math.max(1, Math.round(spanDays * SANDHI_BAND_FRACTION))
  const boundaryDate = boundaryKind === 'period_start' ? entry.start_date : entry.end_date
  const bandStart = addDays(boundaryDate, -bandWidthDays)
  const bandEnd = addDays(boundaryDate, bandWidthDays)
  return {
    level_n: entry.level_n,
    ...
    is_now_within_band: isDateWithinInclusive(asOfDate, bandStart, bandEnd),
  }
}
```

This runs once per boundary of each entry returned by `fetchVimshottariMdAdBoundaries` — since that
fetch is capped at `max_level: 2`, `buildBoundaryBand` structurally never sees a level 3/4 entry, so
it can never emit a band for the Sūkṣma junction that is actually active. The four `false` values are
not wrong computations — they are the honest answer to a narrower question ("is now near a level-1/2
boundary") being served in the same field/grammar as the broader question a caller asks
("am I in a sandhi right now").

**Where the coverage array entry is set to "computed"** — `now.ts:1796-1803`:

```ts
dashaSandhi.result
  ? computedCoverage('dasha_sandhi')
  : honestEmptyCoverage(
      'dasha_sandhi',
      !dashaSandhi.chainReachable
        ? 'L3 active-dasha registry (query_active_dashas) unreachable this call.'
        : 'No active Vimśottarī MD/AD chain resolved for this chart/date — honest empty, not fabricated. Full daśā-sandhi calendar (all levels, both directions) is item 1-full (wave W3).',
    ),
```

`dashaSandhi.result` is non-null whenever `computeDashaSandhi` produced ANY bands (`now.ts:983`:
`if (bands.length === 0) return { result: null, ... }`) — i.e. whenever levels 1-2 resolved at all,
regardless of whether levels 3-4 were ever examined. The `honest_empty` branch only fires when NO
MD/AD chain resolves (registry unreachable, or chart genuinely has no active chain) — it is not
reachable by the "levels 1-2 resolved but 3-4 were never asked for" case, which is the normal case on
every call. The coverage vocabulary itself (`platform-mcp/src/lib/kala_envelope.ts:316`
`export type CoverageState = 'computed' | 'honest_empty' | 'not_in_corpus'`) has no state that can
express "computed, but only over a documented sub-scope" — there is no way, given the current
`KalaCoverageEntry` contract, to emit `dasha_sandhi_levels_3_4: not_computed` as a sibling entry
alongside `dasha_sandhi: computed`. This is a real gap in the vocabulary, not just a call-site
omission: even a corrected call site would need a second coverage concept name to state the
level restriction machine-readably, which the corpus's own mechanism note anticipates
("The honest form would be a coverage entry ... alongside the bands").

## Sibling Census

Searched `now.ts`, `ahead.ts`, `explain.ts`, `upaya.ts`, `story.ts`, `priority.ts`, `ritual.ts`,
`elect.ts` for the same shape: a `max_level`-capped `query_active_dashas` (or equivalent) call feeding
a per-item **boolean absence claim**, reported under a flat `computedCoverage(...)` with no
scope-qualified coverage entry.

Two other `max_level: 2` call sites exist, but neither reproduces the specific hazard (a boolean
"not in X" grammar standing in for a scope limit):

- `now.ts:721` (`fetchActiveVimshottariChain`, feeding `dasha_lord_current_transit_condition`, item
  28) — caps at level 2, but "dasha lord" is defined AS the MD/AD lord by the concept itself; it does
  not assert an absence claim about deeper levels, so a caller cannot misread it as "no deeper-level
  condition exists."
- `ahead.ts:411` (`fetchActiveVimshottariChain`, forward-horizon counterpart of the above) — same
  shape/same non-hazard for the same reason.
- `ahead.ts:638` (`system: 'mudda', max_level: 2`) — a different dasha system (Mudda), same
  non-hazard reasoning: it reports the active Mudda lord chain, not an absence claim about a deeper
  Mudda level.

One near-positive counterexample, worth noting as the pattern this finding's fix should follow:
`sukshma_boundary_uncertainty` (`now.ts:807-832`) DOES read level-4 data specifically and its served
`convention` string explicitly discloses that level 5 (Prāṇa-daśā) is "NEVER computed for any chart by
design" — i.e. this sibling field in the SAME file already does the disclosure `dasha_sandhi` is
missing, for a different level boundary. This is direct in-file precedent that the fix (disclosing the
level restriction in-band) is both expected practice and already implemented once in this exact file.

No second boolean-per-item "all-clear-shaped" defect of this class was found in the searched files.
**Not found in the searched files does not mean absent everywhere** — `explain.ts`/`upaya.ts` were
grepped for `computedCoverage(` call sites (listed) but not individually audited line-by-line for this
same boolean-grammar hazard; that would need its own pass if the exemplar unification with F-120 wants
a project-wide census rather than a same-file / cited-files census.

## Blast Radius

The fix is narrow and does NOT require a new capability or new computation:

- `query_active_dashas` (the capability `now.ts` already calls) supports `max_level` up to 5 and
  defaults to 3 — `now.ts` is requesting LESS than the capability's own default. Raising
  `max_level: 2` to `max_level: 4` in `fetchVimshottariMdAdBoundaries` (`now.ts:882-885`) is sufficient
  to make levels 3-4 data reach `buildBoundaryBand` — the data is not "unreachable," it is simply not
  being asked for.
- This does NOT unify the two call paths into one builder (see Exemplar Note below) — it only widens
  the existing lite-path query's level parameter. `computeDashaSandhi` (`now.ts`) and
  `computeDashaSandhiCalendar` (`dasha_sandhi.ts`) remain two independently-maintained
  implementations reading the same L1 table through two different registry capabilities
  (`query_active_dashas` vs `marsys://tool/L1/get_dashas`).
- A second, independent fix is needed regardless of the `max_level` change: the coverage vocabulary
  itself has no way to express "computed over a documented sub-scope" — `honest_empty` doesn't fit
  (levels 1-2 DID compute successfully) and `not_in_corpus` doesn't fit (the data exists, it's just
  not requested). Either a new `CoverageState` value, or a documented convention of emitting a second
  named coverage concept (e.g. `dasha_sandhi_levels_3_4`) alongside `dasha_sandhi`, is required to
  close this honestly per the corpus's own suggested fix.

## Exemplar Note

The generalizable defect class here (candidate for unification with F-120, contents unknown to this
lane): **a per-item boolean computed over a narrower scope than its field name/grammar implies, served
under a flat "computed" coverage marker whose vocabulary has no slot for declaring the narrower
scope.** The absence-of-coverage (level 3-4 never asked for) is rendered in the identical grammar as
absence-of-condition (level 3-4 genuinely checked and found clear) — the caller cannot distinguish "I
checked and it's false" from "I never checked." The in-file precedent at
`sukshma_boundary_uncertainty` (which DOES disclose its own level-5 restriction in its served
`convention` string) shows the codebase already has the pattern for the fix; `dasha_sandhi`'s
`band_convention` string simply omits the analogous disclosure for levels 3-4. Whether F-120 shares
this exact shape (boolean-grammar-outruns-scope) or a different coverage-vocabulary gap is for the
stream lead to confirm once both lanes report.

## Verdict

**REPRODUCES LIVE — TIER3-EXPERIENCE confirmed, EXEMPLAR-CANDIDATE for a shared defect class with
F-120.**

- Mechanism pinned: `platform-mcp/src/tools/kala_views/now.ts:882-885` (hardcoded `max_level: 2`,
  below the underlying capability's own default of 3 and max of 5) feeding
  `now.ts:937-960` (`buildBoundaryBand`, produces `is_now_within_band=false` for all served bands
  because no level-3/4 entry is ever fetched) and `now.ts:1796-1803` (coverage entry collapses to flat
  `computed` the instant ANY level-1/2 band resolves, with no vocabulary slot to disclose the
  level-3/4 gap).
- No ESCALATE-TO-PRATINIDHI needed — this is not a reserved/ambiguous determination; live
  reproduction, mechanism, and fix shape are all concrete and unambiguous.
- Recommended fix (for the implementing lane, not applied by this diagnosis pass): (1) raise
  `max_level` in `fetchVimshottariMdAdBoundaries` to at least 4 so `buildBoundaryBand` can see and
  band Pratyantardaśā/Sūkṣmadaśā boundaries; (2) either add a `CoverageState` capable of expressing
  partial/sub-scope computation, or emit a second named coverage concept disclosing whichever levels
  remain out of scope, following the `sukshma_boundary_uncertainty` in-file precedent for disclosure
  wording.
