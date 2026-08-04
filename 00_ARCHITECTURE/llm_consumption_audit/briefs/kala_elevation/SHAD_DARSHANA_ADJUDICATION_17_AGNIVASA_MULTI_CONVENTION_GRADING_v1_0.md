---
artifact: SHAD_DARSHANA_ADJUDICATION_17_AGNIVASA_MULTI_CONVENTION_GRADING
canonical_id: SHAD_DARSHANA_ADJUDICATION_17_AGNIVASA_MULTI_CONVENTION_GRADING
version: 1.0
status: RULED — ANTARYĀMIN (Conductor, foreground, SESSION-B-BUILD lane (d) part 1)
created: 2026-08-04
author: ANTARYĀMIN
governing: SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md ·
  SHAD_DARSHANA_ADJUDICATION_16_FOLLOWUP_MULTI_CONVENTION_GAP_v1_0.md (PR #1043) ·
  platform/supabase/migrations/533_kala_paddhati_profile.sql (ADJUDICATION-8)
---

# ADJUDICATION-17 — how Agnivāsa convention-B can flip live without silently overriding
# the native-confirmed convention

## The question (from PR #1043's followup)

ADJUDICATION-16 extracted a real, cited, computable arithmetic for convention-B
(`agnivasa_muhurta_chintamani_arithmetic`, MC 1.36: `(tithi_id + 1 + vara_id) mod 4`). Flipping
its `convention_status` to `computed` requires knowing how it interacts with convention-A
(`agnivasa_tithi_element_prithvi`, native-confirmed) in actual grading, since both would then be
`computed` + `constraint_role='hard'` in the same `factor_family='agnivasa'`.

## The evidence (traced directly, `platform-mcp/src/lib/kala_sky_pattern.ts`)

The `residence` branch of `compileConstraint` (`:1351-1403`) is the ONLY place `agnivasa`
actually enters grading:

```ts
const rows = rowsByFamily.get('agnivasa') ?? []          // bg_muhurta_lattice atoms
const usingProfile = b.per === 'paddhati_profile' && paddhati.available && paddhati.operative.length > 0
const favourableElements = ['prithvi']                    // HARDCODED
const matched = rows.filter((r) => {
  const el = String((r.detail as {element?:unknown}|null)?.element ?? '').toLowerCase()
  const isFav = favourableElements.includes(el)
  return wantFavourable ? isFav : !isFav
})
```

Two decisive findings:

1. **`usingProfile` is computed but never consulted for the actual match logic.** It only
   changes the disposition's `reason` STRING (`:1389-1396`) — whether to say "using the profile"
   or "using the corpus default." The `matched` filter always runs against the SAME hardcoded
   `favourableElements` and the SAME `bg_muhurta_lattice` rows regardless of what
   `paddhati.operative` actually contains. **`paddhati.operative`'s content cannot currently
   change grading outcomes for `agnivasa` at all** — a pre-existing gap this ruling does not
   need to fix, but must not be confused with the multi-convention question it's adjacent to.
2. **`bg_muhurta_lattice`'s atoms are baked from convention-A's arithmetic alone, at L0 build
   time** (confirmed independently by the PR #1043 builder's own investigation). Convention-B's
   classification is a DIFFERENT kind of value — `(tithi_id + 1 + vara_id) mod 4`, which depends
   on `vara_id` (weekday), which the lattice atoms' `detail.element` field was never built to
   carry. **There is no way to "blend" convention-B into the same `matched` filter — it isn't
   the same shape of computation, let alone the same data.**

## The ruling

**Convention-B does NOT enter the `residence` constraint's hard-gate matching path at all.**
Doing so would require either (a) rebuilding `bg_muhurta_lattice` to carry a second,
vara-dependent classification per atom — a real schema/writer change, out of this ruling's scope
and arguably its own separate proposal — or (b) computing convention-B live inline inside
`compileConstraint`, which would silently let an unconfirmed convention veto or dilute the
native-confirmed one exactly as ADJUDICATION-8 rail 2 forbids.

**Convention-B becomes a SECOND, SEPARATELY SERVED VOICE — concurrence/dissent, not a grading
input.** Same shape as W3K Lane 2's `kp_school_voice.ts` precedent (PR #1046, this same
session): compute convention-B's classification live for the SAME candidate date the residence
constraint already resolved for convention-A, and serve it alongside the muhūrta result as
"here is what a second, MC-cited convention would say about this same date" — informational,
never overriding, never entering `mode: 'require'`/`dropped_from_conjunction` gating.

**Consequence for `PaddhatiResolution.divergence` (Part 2 of this lane):** this gives the
`divergence` detector a REAL, comparable pair for the first time — convention-A's element
classification for a date (from the matched lattice atom) vs. convention-B's live mod-4 result
for the SAME date. `'agrees'`/`'diverges'` can now mean something concrete: do the two
conventions' favourability verdicts for this exact candidate date match or not. Before
convention-B had a computed arithmetic, there was structurally nothing to compare (correctly
`'none_computed'`); after, there is.

**Native-confirmed precedence:** convention-A stays the ONLY voice that can gate a candidate
(via the existing `residence` branch, unchanged). Convention-B's dissent is disclosed, never
determinative — this is the direct analogue of rail 3 (no builder may pin invented content and
label it "the native's lineage") applied to grading weight rather than content provenance.

## What this authorizes for implementation

1. `paddhati_v02` migration: convention-B row flips to `convention_status='computed'`,
   `native_confirmed` STAYS `FALSE` (unchanged — nothing here attests it as the native's
   practice). Purely additive, per ADJUDICATION-8's own designed reversibility.
2. A new served surface (new file or an addition alongside `kp_school_voice.ts`'s pattern) that,
   given a candidate date, computes convention-B's classification live from `tithi_id`/`vara_id`
   (already L1-canonical per ADJUDICATION-16) and reports it as a labeled second voice —
   analogous shape to how KP's dissent is served, not wired into `compileConstraint`.
3. The `divergence` field on `PaddhatiResolution`: a real detector comparing convention-A's
   resolved element for a date against convention-B's live mod-4 result for that SAME date,
   `'agrees'` | `'diverges'` | `'none_computed'` (the last only when convention-B genuinely isn't
   computed, no longer the permanent default).

## Reversibility

Total. New migration only (never edits 533/534); the new served voice is additive; no existing
grading path changes.

## Does this touch a FROZEN contract / rail?

No. No orchestrator/writer-contract change. Does not touch `compileConstraint`'s existing
`residence` branch logic (deliberately — see evidence above for why blending was rejected).
