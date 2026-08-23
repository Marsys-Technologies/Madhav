# F-121 SPEC (TIER3-EXPERIENCE) — kala_now_get dasha_sandhi silently caps at level 2, hiding a genuinely active level-4 (Sūkṣma) sandhi

Stream S4 VĀCA · Stage S SPEC · exemplar-class pairing with F-120 (independent mechanism —
see Exemplar Relationship below).

## Root-cause statement

`fetchVimshottariMdAdBoundaries` (`platform-mcp/src/tools/kala_views/now.ts:875-900`) hardcodes
`max_level: 2` on its `query_active_dashas` call — below that capability's own default of 3 and
max of 5 (`platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts:72,97`) — so
`buildBoundaryBand` (`now.ts:937-960`) structurally never receives a level-3 (Pratyantardaśā) or
level-4 (Sūkṣmadaśā) chain entry to band, and the served `dasha_sandhi.bands` array reports
`is_now_within_band: false` on all four MD/AD boundaries even when a real, `sandhi_flag: true`
Sūkṣma-level junction is active for the query date (live-verified: chart `482012f1-…`,
`as_of=2026-08-16`, `ganita_dasha_periods_get` row `level_n=4` shows `sandhi_flag: true` for
`2026-08-13..2026-08-25`, which contains that date).

## Files to change

**`platform-mcp/src/tools/kala_views/now.ts`** only. This file is in S4's own lease (S4 owns
`now.ts` / `explain.ts` / `ahead.ts` / `upaya.ts` per the stream's file scope; no `LEASES.json`
exists in this worktree to cross-check against, but `LEDGER_S4.md`'s F-121 row and DIAGNOSIS.md's
Blast Radius section both describe the fix as confined to this one file, and no other stream's
hold on `now.ts` is recorded anywhere in this lane's evidence). No change to
`query_active_dashas.ts` (the capability already supports what this fix needs — see below) and
no change to `dasha_sandhi.ts` / `kala_dasha_sandhi_get` (the separate all-level, item 1-full
surface — DIAGNOSIS.md confirms the two call paths stay independent; this is not a unification).

Two elements, both inside `now.ts`, no new capability or computation:

1. **`fetchVimshottariMdAdBoundaries` (`now.ts:882-885`):** raise the hardcoded `max_level: 2` to
   `max_level: 4`. `query_active_dashas` already supports up to 5 and defaults to 3 — this widens
   an existing, already-reachable query parameter; it fetches no new data source. This alone
   makes level-3/4 chain entries reach `buildBoundaryBand`, which needs no change itself (it is
   already generic over `entry.level_n`/`level_name` — see `now.ts:937-960`, nothing there is
   level-specific).
2. **`SANDHI_BAND_CONVENTION` (`now.ts:855-862`):** extend the string to state the level scope
   explicitly, mirroring the in-file precedent at `sukshma_boundary_uncertainty`
   (`now.ts:807-832`, whose served `convention` text already discloses "level 5 [Prāṇa-daśā] is
   NEVER computed for any chart by design"). Add a sentence naming which levels this field now
   bands (1 through 4 — Mahā/Antar/Pratyantar/Sūkṣma) and stating that level 5 (Prāṇa-daśā) is
   never computed for any chart, same wording convention as the sibling field. This is a prose
   addition to an existing served string, not a schema change.

**Not in scope for this lane (considered and declined — see Reserved-Question Determination
below):** no change to `CoverageState` (`platform-mcp/src/lib/kala_envelope.ts:316`) and no new
sibling coverage-concept entry for `dasha_sandhi`.

## Reserved-Question Determination (PAR-R-7)

DIAGNOSIS.md's Blast Radius section floats two shapes for closing the coverage-vocabulary gap it
identifies ("computed over a documented sub-scope" has no expressible state): (a) add a new
`CoverageState` enum value, or (b) emit a second named coverage concept
(e.g. `dasha_sandhi_levels_3_4`) alongside the existing entry. Read narrowly, this pair of options
looks like a genuinely reserved design choice — but it is not, for a reason specific to element 1
above: **once `max_level` is raised to 4, `dasha_sandhi`'s `computed` coverage state becomes
literally true again.** The gap DIAGNOSIS names ("levels 1-2 resolved but 3-4 never asked for,
reported as flat `computed`") is a description of the *current, broken* behavior — after this fix,
the field genuinely does examine every classically-computed level (1-4; level 5 is never computed
for any chart, by design, system-wide — not a `dasha_sandhi`-specific restriction). There is no
longer a sub-scope silently excluded from a `computed` claim, so there is nothing left for a new
`CoverageState` value or a second coverage entry to disclose that the widened `band_convention`
string (element 2) does not already state in-band. `CoverageState` is a shared type consumed
across every concept in this file's `coverage` array (`kala_envelope.ts:316`, documented as a
deliberate 3-state design in its own header comment) — extending it would be a cross-cutting
schema change with a blast radius far beyond this one TIER3 finding, and DIAGNOSIS.md gives no
evidence that a scope narrower than "extend the shared enum" was ever actually required; it
surfaces the option because it was reasoning about the *unfixed* state, not the *fixed* one. The
in-file precedent (`sukshma_boundary_uncertainty`) itself resolves this the same way: it discloses
its level-5 restriction purely via its served `convention` prose string, never via a bespoke
coverage state. Following that precedent is not picking the "smaller/safer" of two live options —
it is the same shape DIAGNOSIS's own Exemplar Note points to as "the pattern this finding's fix
should follow," applied to a scope that the fix itself closes. **No ESCALATE-TO-PRATINIDHI
required.**

## Exit test

**Extend the existing test file** `platform-mcp/src/__tests__/kala_now_get_sandhi_w1_joins.test.ts`
(does not need to be created — it already covers `dasha_sandhi` item 1-lite end-to-end, including
mocking `marsys://tool/L3/query_active_dashas`). Command: `cd platform-mcp && npx vitest run
src/__tests__/kala_now_get_sandhi_w1_joins.test.ts`.

Add:

1. **A new mock chain fixture with level 3 and level 4 entries** (the existing `ACTIVE_CHAIN`
   const only has level 1/2 — add a sibling fixture, e.g. `ACTIVE_CHAIN_WITH_SUKSHMA`, with a
   level_n=4 entry whose `start_date`/`end_date` span brackets the test's `as_of` date closely
   enough that its `is_now_within_band` band computation is exercised non-trivially — e.g.
   `start_date: '2026-08-13', end_date: '2026-08-25'` against `as_of: '2026-08-16'`, mirroring
   the live-reproduction numbers in DIAGNOSIS.md so the fixture is grounded in a real observed
   case, not an arbitrary one).
2. **Assert the request now asks for `max_level: 4`, not `2`.** The mock's request-body capture
   (`JSON.parse(String(init?.body ?? '{}'))`) already exposes `args`; assert
   `body.args?.max_level === 4` (or equivalent field path) on the captured
   `query_active_dashas` call. This is the guard against a regression back to `2` — see Recurrence
   guard below.
3. **Assert a level-4 band is present and correctly reports `is_now_within_band: true`** for the
   `as_of` date that DIAGNOSIS.md found genuinely falls inside the active Sūkṣma period — this is
   the test that would have caught F-121 before it shipped: pre-fix, this band would never exist
   in `result.dasha_sandhi?.bands` at all (level 4 never fetched); post-fix, it must exist with
   `boundary_kind` bracketing the date and `is_now_within_band === true`.
4. **Assert `band_convention` names the level scope.** Extend the existing "serves an explicit,
   documented band_convention string" test (`now.ts` line ~119 in the current test file) with
   `expect(result.dasha_sandhi?.band_convention).toEqual(expect.stringContaining('Sūkṣma'))` (or
   the ASCII-safe equivalent already used elsewhere in this codebase for the same word) and an
   assertion that it names level 5 / Prāṇa as never computed, matching the wording pattern
   already tested for `sukshma_boundary_uncertainty` elsewhere in this file.
5. Existing tests (`bands.length).toBe(4)` at line 78, band-width-days assertions, the two
   `honest_empty` tests) are unaffected — the pre-existing mock `ACTIVE_CHAIN` fixture has only
   2 levels regardless of the `max_level` requested, so `bands.length` stays 4 for those specific
   tests; the new level-3/4 fixture is additive, not a rewrite of the existing cases.

## Sibling sites covered

From DIAGNOSIS.md's Sibling Census (searched `now.ts`, `ahead.ts`, `explain.ts`, `upaya.ts`,
`story.ts`, `priority.ts`, `ritual.ts`, `elect.ts` for the same shape — a `max_level`-capped
`query_active_dashas`-equivalent call feeding a per-item boolean absence claim under a flat
`computedCoverage(...)`):

- `now.ts:721` (`fetchActiveVimshottariChain`, feeds `dasha_lord_current_transit_condition`,
  item 28) — also caps at `max_level: 2`, but NOT a sibling defect: "dasha lord" is defined AS the
  MD/AD lord by the concept itself, so it makes no absence claim about deeper levels a caller could
  misread. **Not touched by this lane** — different concept, different (correct) semantics.
- `ahead.ts:411` (`fetchActiveVimshottariChain`, forward-horizon counterpart) — same non-hazard
  reasoning, same non-sibling disposition. **Not touched.**
- `ahead.ts:638` (`system: 'mudda', max_level: 2`) — different daśā system (Mudda), reports the
  active Mudda-lord chain, not an absence claim about a deeper Mudda level. **Not touched.**
- `sukshma_boundary_uncertainty` (`now.ts:807-832`) — not a sibling defect, a **positive
  precedent**: already does the disclosure this fix adds to `dasha_sandhi`, for the level-5
  boundary. Element 2 of this spec follows its wording pattern; the field itself is unchanged.

DIAGNOSIS.md notes explicitly that `explain.ts`/`upaya.ts` were grepped for `computedCoverage(`
call sites but not individually line-audited for this same boolean-grammar hazard — a
project-wide census beyond the searched files was out of scope for the D-stage pass and remains
out of scope for this Stage-S spec (single-file fix, per Files to change above).

## Exemplar Relationship to F-120

**Independent mechanisms, same defect class, not a shared builder — per DIAGNOSIS.md for both
lanes.** F-120's mechanism lives in `platform/src/lib/retrieval/registry/layers/L1_ganita/
get_dashas.ts` (L1 registry layer: a hardcoded `lvl > 3` filter building a `byLevel` map that
narration reads, plus an unconditional "current" string label and a `sandhi_flag` check pinned
only to the level-1 row). F-121's mechanism is in `platform-mcp/src/tools/kala_views/now.ts` (L3
serving facade: a fresh `query_active_dashas` call capped at `max_level: 2`, feeding a
band/boolean structure, not a narration sentence). Different file, different layer, different
function, different cap value (3 vs. 2), different served shape (narration string vs.
band array + coverage entry). F-120's own diagnosis explicitly concludes "TWO fixes, one shared
defect class... no shared helper to fix once." This spec fixes F-121's file only; F-120's fix is
a separate lane's SPEC.md, not covered here.

**The shared defect class** (for the exemplar write-up, not itself a code change): a
narrative/summary-producing code path hardcodes a fixed, low dasha-level ceiling and asserts a
"current state" / "no junction" claim in a grammar indistinguishable from "I checked the deeper
level and it's clear," when in fact the deeper level was never examined. Both F-120 and F-121 fix
this the same conceptual way — widen the level ceiling to the depth the underlying data already
supports, and make the served claim's scope legible — but via two independent code changes in two
independent files, because the two surfaces (L1 narration string vs. L3 band/coverage structure)
share no helper function.

## Recurrence guard

Two guards, one per element of the fix, both asserting the actual computed content rather than a
type/shape check (§N.7 item 4 / §N.8: a signal needs a real detector behind it, not a presence
check that a hardcoded value would also satisfy):

1. **The `max_level: 4` regression guard is the exit test's assertion on the outbound request
   body** (exit-test item 2 above) — it inspects what `now.ts` actually *asked* the registry for,
   not just what came back. A silent revert of `max_level` back to `2` (or any value < 4) fails
   this assertion immediately, independent of whatever the mock happens to return, because the
   assertion targets the call-site argument, not the response shape.
2. **The level-4 band presence + correctness guard is the exit test's fixture-grounded assertion**
   (exit-test item 3) using the DIAGNOSIS.md live-observed dates (`2026-08-13..2026-08-25`
   bracketing `2026-08-16`) rather than synthetic round numbers — this is deliberately the same
   discipline F-135's spec used (substring/value assertions tied to real computed numbers, not a
   hardcoded-string-shaped placeholder that a lazy `null`-always or always-`false` implementation
   could satisfy). A regression that re-introduces the `max_level: 2` cap, OR one that fetches
   level 3-4 data but fails to plumb it into `buildBoundaryBand`, OR one that bands it but computes
   `is_now_within_band` incorrectly, all fail this single assertion — it is a true end-to-end
   check of the exact claim F-121 diagnosed as false.

No CI lint beyond these two test assertions is proposed — the defect is call-site-specific
(one hardcoded literal, one string), not a class of call sites needing a project-wide static
check (contrast F-135, where the recurrence risk was a whole field's compute-vs-hardcode
distinction).

## Dependencies and rollback

- **No cross-lane dependency.** `now.ts` is in S4's own lease; no other stream is recorded as
  holding it (`LEDGER_S4.md`'s F-121 row shows no lease-hold flag, unlike F-130 which was told to
  flag a possible cross-stream overlap and did). Stage B may proceed once this spec clears Stage R
  without waiting on any other lane's release.
- **Rollback:** two independent, additive-in-effect changes to one file — (1) a one-token literal
  change (`max_level: 2` → `4`) and (2) a string-literal extension (no field added/removed, no
  type change, no consumer of `SANDHI_BAND_CONVENTION` needs updating since it is served as an
  opaque string). A `git revert` of the one commit fully restores prior behavior. No data
  migration, no schema change, no new capability call, no change to `dasha_sandhi.ts`'s
  independent all-level surface.

## Sub-claim coverage table (from DIAGNOSIS.md's Claim Decomposition)

| DIAGNOSIS.md claim | Verified | Spec element that closes it |
|---|---|---|
| (a) `dasha_sandhi` computes only 4 bands over levels 1-2 | TRUE | Element 1 (`max_level: 2 → 4`) — post-fix, bands are computed over levels 1-4 whenever the chain resolves that deep |
| (b) All 4 served bands report `is_now_within_band=false` | TRUE (for the reproduced case) | Element 1 — once level-4 entries reach `buildBoundaryBand`, a genuinely active Sūkṣma junction now produces a band with `is_now_within_band=true`; exit-test item 3 asserts this directly |
| (c) A genuinely-active level-4 sandhi exists per `ganita_dasha_periods_get` (`sandhi_flag=true`, `2026-08-13..2026-08-25`) | TRUE | Element 1 + exit-test item 1/3, which reuses these exact live-observed dates as the fixture |
| (d) `coverage` array marks `dasha_sandhi` flatly "computed," no level-3/4 qualifier | TRUE (pre-fix) | Resolved by the Reserved-Question Determination: post-fix, `computed` is literally accurate (all classically-computed levels examined), so no coverage-entry change is needed — closed by Element 1, not a new coverage concept |
| (e) `band_convention` discloses the 2-vs-1-period simplification but not the level restriction | TRUE | Element 2 (`SANDHI_BAND_CONVENTION` extended to name levels 1-4 and the never-computed level 5, mirroring the `sukshma_boundary_uncertainty` precedent) |

## Verdict

Stage S complete. No ESCALATE-TO-PRATINIDHI required (see Reserved-Question Determination). No
cross-lane dependency recorded. Ready for Stage R independent review.
