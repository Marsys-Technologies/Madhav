---
title: V3-E-016 — real-chart context leak: root cause, fix, and live proof
canonical_id: V3_E_016_ROOT_CAUSE_AND_FIX
version: 1.0
status: CURRENT
authored: 2026-08-29
campaign: Pariprashna Experience Assurance v3 — overnight closeout
lane: B1 (Security Engineer)
finding: V3-E-016 (stream S3, CRITICAL, TRIAGED → root-caused and fixed)
disposition: RESERVED TO THE SURROGATE — this document does not rule
---

# V3-E-016 — the native's private chart corpus was injected into every chart's synthesis prompt

## 0. One-paragraph summary

V3-E-016 was **still fully reproducible on current production after PR #1646**.
It is not model memorization and not a chart-id mix-up in request tracking. It
is a real, mechanical data-flow leak: `platform/src/lib/bundle/bundle_hydrator.ts`
read the native's own chart corpus off disk and joined it verbatim into the
synthesis system prompt **without ever consulting which chart the turn was
about** — and it force-injected the largest of those documents, `CGM_v9_0.md`
(~79 KB of Abhisek Mohanty's Chart Gestalt Map), as an unconditional *floor*
asset on **every turn for every chart in the system**. When the web door's
retrieval floor came back mostly empty (the known MCP↔web namespace gap: 5
served / 9 empty of 14), the model answered the synthetic chart's factual
question out of the only chart data actually in its context — the native's.
The fix is an additive authorization gate: a manifest asset that declares a
`native_id` may only enter a synthesis prompt for the chart that native's
corpus actually describes. Proven RED→GREEN end-to-end through the real route.

## 1. Re-reproduction on CURRENT production (post-#1646) — RED

Per the lane's safety rails, the **only** input sent was the synthetic
operator-E2E chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a`. The native's chart
`482012f1-…` was never used as a query input; it appears here only as data that
came *out*.

| | |
|---|---|
| Door | `POST https://amjis-web-qm256lasva-el.a.run.app/api/pariprashna` |
| Harness | `platform/scripts/probe/ask.ts` (existing, unmodified) |
| Query | "What nakshatra is the Moon placed in for this chart, and which sign is the Lagna?" |
| `chart_id` in POST body **and** in the turn's own `turn.open` SSE event | `1c826d5a-41cb-4450-b4dc-59d440e5f75a` |
| `chart_id_explicit` | `false` (correctly defaulted to the synthetic chart) |
| Model | `gemini-3.1-pro-preview` |
| turn_id | `8f8f91b7-470b-4260-87ae-10d4b2da6eb5` |
| Terminal status | `ok`, 37 events, not partial |

**Served prose, verbatim:**

> "In this chart, the Moon is placed in the nakshatra of Purva Bhadrapada
> (pada 3), located within the sign of Aquarius [1]. The Lagna (Ascendant) is
> in the sign of Aries [2]."

Chart `1c826d5a`'s actual Moon is **Ardra / Gemini** (ground-truthed in the
original S3 filing via `ganita_positions_get`). "Purva Bhadrapada" and "Aries
Lagna" are two of the native's seven FORENSIC birth anchors (CLAUDE.md §B).

The turn's own receipt detected the problem and shipped anyway:

```
evidence_grades: { primary: 0, supporting: 0, contextual: 0,
                   unverified: 2, prior_reading: 0, hallucination_count: 2 }
citation_gate  : PASS — "informational query (factual); citations not required"
coverage       : served 5 / empty 9 / dark 0 / floor_item_total 14
channel_note   : "9 of 14 floor items have NO web-executable retrieval tool
                  (MCP↔web namespace gap)"
```

**Conclusion: PR #1646 did NOT close V3-E-016.** #1646 widened
`citation_resolver.ts`'s id-recognition scope, which is why the two citations
now render as `[unverified citation 1]` / `[unverified citation 2]` in the
`citation.define` events rather than as resolved-looking labels. That is a real
improvement to citation *honesty* and it is orthogonal: the leaked content still
reached the reader, and the reader-facing prose still carried plain, unflagged
`[1]` / `[2]` markers.

## 2. Root cause

### 2.1 The mechanism

1. `CAPABILITY_MANIFEST.json` marks six assets with `native_id: "abhisek"` —
   `CGM`, `MSR`, `CDLM`, `RM`, `UCN`, `LEL`. These are not reference corpus.
   They are **one specific living person's chart**, in prose and structured
   YAML. `CGM` additionally carries `always_required: true`.
2. `bundle_hydrator.ts` declared `FLOOR_ASSET_IDS = ['CGM']` and prepended CGM
   to the asset list on **every** call, regardless of the plan.
3. For each asset it called `storage.readFile(entry.path)` and pushed the file's
   full text into `HydratedBundle.assets[].content`.
4. `synthesis_stage.ts:assembleSynthesisContext` joins exactly that:

   ```ts
   const rawBundleSystemContent = (bundle.assets as Array<{ content: string }>)
     .map((a) => a.content).filter(Boolean).join('\n\n')
   ```

   …and passes it to `buildConsultSystemContent({ bundleSystemContent, … })` —
   i.e. straight into the model's system prompt.
5. **Nothing anywhere in that path took `chart_id` as an input.** `hydrateBundle`
   did not even accept one.

So the native's ~79 KB Chart Gestalt Map — containing, at `CGM_v9_0.md` lines
135–136, `sign: Aquarius` / `degree: "27°02′48″"`, and at line 714
`node_label: Purva Bhadrapada` — sat in the system prompt of every turn about
every chart. The degree string in the original S3 capture ("27°02′48″") is a
byte-for-byte match with line 136 of that file. That is the smoking gun: it was
never memorization, it was in the prompt.

### 2.2 Why the leak surfaced on *this* query in particular

The web door has no retrieval tool for `positions_snapshot`,
`chart_digest_read`, `dignity_scan`, etc. (`web_namespace_gap` — 9 of 14 floor
items). So for a positional-fact question the model had **no** grounded data for
the requested chart, and exactly one chart's positional data in context: the
native's. The receipt honestly reported the gap; the synthesis layer filled it.
The namespace gap is the *trigger*; the unscoped corpus injection is the *cause*.

### 2.3 Blast radius (measured, not estimated)

Production `public.charts` holds six rows. Every one of them was receiving the
native's corpus:

| chart | subject | role |
|---|---|---|
| `482012f1-…` | Abhisek Mohanty (the native — legitimate) | native |
| `1c826d5a-…` | Abhinandan Mohanty (synthetic operator-E2E) | native |
| `42a4bbdf-…` | a third party | native |
| `9da866fb-…` | a third party | native |
| `178ab5ef-…` | a public figure | native |
| `1b30aebc-…` | a public figure | native |

Five of six charts, four of them other real people, were served turns whose
system prompt contained the native's private birth data.

### 2.4 The trap that made the DB column unusable as the fix

`public.charts.native_id` looks like the natural authorization key. It is not:
migration 008 declares it `VARCHAR(64) NOT NULL DEFAULT 'abhisek'`, and **all
six production rows carry the default** — including the synthetic chart and the
four third-party charts (verified by direct query). Keying the gate off that
column would have admitted the native's corpus for every chart in existence,
i.e. it would have encoded the bug as the fix while looking like a repair. This
is the §N.8 defect class exactly: a signal whose detector measures a proxy
rather than the claim.

### 2.5 Relationship to E-018 (the panchang leak, closed in #1635)

Confirmed distinct, as the EDIR entry already argued, and the root cause now
proves it: E-018 was a missing per-chart authorization check on a caller-supplied
`chart_id` at `/api/panchang`. V3-E-016 never asks the authorization layer for
the wrong chart at all — the wrong chart's *documents* were unconditionally
loaded into the prompt by a code path that had no concept of charts. The EDIR's
open question ("is there a shared upstream cause?") is answered: **no shared
cause, but the same doctrinal gap** — a data path that reached a chart-scoped
asset without a chart-scoped check.

## 3. The fix

Additive scoping only. No existing check is loosened anywhere.

**New — `platform/src/lib/bundle/native_corpus_scope.ts`**
An explicit, auditable binding from `native_id` → the one `chart_id` whose
subject that corpus describes, plus `decideAssetScope(entry, chartId)`:

- asset with no `native_id` → chart-agnostic, admissible everywhere (unchanged);
- `native_id` bound to **this** chart → admissible (unchanged — the native's own
  reading is not narrowed by one byte);
- `native_id` bound to a **different** chart → `native_binding_mismatch`, withheld;
- `native_id` with **no binding at all** → `native_binding_unknown`, withheld.
  Fail-closed: adding a new native's corpus to the manifest without binding it
  here withholds it rather than broadcasting it.

**Changed — `platform/src/lib/bundle/bundle_hydrator.ts`**

- `hydrateBundle(plan, manifest, { chartId })` — `chartId` is **required**.
  There is deliberately no unscoped or defaulted path, because the default is
  what leaked. Both production callers already had the chart id in hand.
- The scope decision runs **before** the storage read, so a withheld document is
  never even loaded into process memory for the wrong turn.
- A withheld asset is recorded on the returned bundle as
  `excluded_native_scoped: [{ asset_id, reason, was_floor }]` — an inspectable
  record, not a silent drop.
- **Floor interaction, stated plainly:** a floor asset that is inadmissible for
  this chart is *withheld*, not fatal. The pre-existing floor `throw`s are
  untouched and still fire for what they were always about — a floor asset that
  is missing from the manifest, path-less, or unreadable, i.e. a broken
  deployment. "Correctly refused for this chart" is a different condition from
  "broken," and hard-failing every non-native chart's turn would be a worse
  outcome than the honest, recorded absence.
- `floor_enforced` now reports `true` only when a floor asset was *actually*
  injected — a prepended-then-withheld asset must not leave a green signal with
  no injection behind it (§N.8).

**Changed — call sites (both, exhaustively):**
`platform/src/lib/pariprashna/pipeline/evidence_stage.ts` and
`platform/src/app/api/chat/consult/route.ts` now pass `{ chartId }`.

## 4. Proof — demonstrated-can-fail, RED before and GREEN after

### 4.1 End-to-end through the real route (the load-bearing proof)

Both runs used the **same** unmodified harness (`scripts/probe/ask.ts`), the
**same** query, the **same** synthetic chart, the **same** local server against
the **real** production database and the **real** corpus files. The only
variable between them was whether the fix was in the working tree.

**RED — pre-fix code (`git stash`ed fix, server restarted), turn `c221ab09-…`:**

> "In this chart, the Lagna (Ascendant) is in the sign of Aries. The Moon is
> placed in the nakshatra of Purva Bhadrapada (specifically in Pada 3).
> Additionally, the current Vimshottari dasha period is Saturn Mahadasha and
> Rahu Antardasha."

**GREEN — post-fix code, turn `40a01c94-…`:**

> "The Lagna sign and the exact Moon nakshatra with pada are not currently
> available in the provided chart details (known gap). If you can provide the
> birth date, time, and location, I can determine these specific placements for
> you. For context on the chart's current timeline, as of today, August 28,
> 2026, the active Vimshottari dasha period is Saturn Mahadasha and Rahu
> Antardasha."

Marker scan on the GREEN prose: `Purva Bhadrapada` **absent**, `Aquarius`
**absent**, `27°02` **absent**, `Aries` **absent**, `Bhubaneswar` **absent**,
`1984` **absent**. The leak is gone and — a genuine bonus, not the thing being
claimed — the model produced the honest-absence answer the receipt's
`honest_gaps` machinery was always structurally built to carry.

### 4.2 At the leak carrier, unmocked, now permanent in CI

`platform/src/__tests__/lib/bundle/native_corpus_scope.real_manifest.test.ts`
runs against the **real** `CAPABILITY_MANIFEST.json` and the **real** corpus
files via the **real** storage client — nothing mocked. It asserts:

- no native-private marker (`Purva Bhadrapada`, `27°02′48″`, `Bhubaneswar`,
  `1984-02-05`) reaches the synthetic chart's bundle, on the floor-injection
  path **and** when the planner names `CGM/MSR/CDLM/LEL/RM/UCN` outright;
- the canonical chart still receives its own corpus (so the two negative
  assertions above cannot pass vacuously);
- the real manifest still marks `CGM` as `native_id: abhisek` (guards the
  premise the whole fix rests on).

Pre-fix, this file's negative assertions fail — the synthetic chart's bundle
contained all four markers across 79,040 bytes of injected CGM.

### 4.3 Mutation proof (§N.8 — does the detector actually detect?)

Deleting the mismatch branch from `decideAssetScope` (making it admit
everything) turns **5 tests RED** across the two bundle test files; restoring it
returns **13/13 GREEN**. The guard is not decorative.

## 5. What this fix does NOT claim

Stated plainly rather than left for a reader to discover:

1. **It closes the leak, not the hallucination.** The synthesis layer still has
   no gate on `evidence_grades.hallucination_count` — `validation_stage.ts`
   contains zero references to it, as the original EDIR entry found. After this
   fix the model can no longer answer out of the *native's* chart, but nothing
   here stops it from inventing a different plausible answer. That is
   V3-E-032's territory (`citation_resolver.ts` / the validation gate), a
   separate open finding. The GREEN run happened to produce an honest gap; it is
   not *guaranteed* to by this change.
2. **The MCP↔web namespace gap is untouched.** 9 of 14 floor items still have no
   web-executable retrieval tool. Non-canonical charts now get *less* context
   than before, honestly labelled — which is correct, and which makes closing
   the namespace gap more urgent, not less.
3. **Post-fix proof is local, not deployed.** The GREEN run above is the real
   route, real DB, real files, real model — but on `localhost:3111`, because
   deploying is outside this lane's remit. A post-merge live re-proof against
   the deployed revision is the remaining verification step.
4. **The receipt does not yet disclose the withholding to the reader.**
   `excluded_native_scoped` is returned by the hydrator and logged; wiring it
   into the turn receipt's `honest_gaps` block is an obvious and small follow-on
   that this PR deliberately did not take on.

## 6. Disposition

**Not ruled here.** This lane's recommendation is
**fixed-and-verified-live-ready**. The disposition of V3-E-016 on the tracker is
reserved to the Surrogate.

## 7. Evidence index

| Artifact | Where |
|---|---|
| Production RED capture (post-#1646) | turn `8f8f91b7-470b-4260-87ae-10d4b2da6eb5`, probe out `89bb5b05-…` (gitignored per convention — cite by turn_id) |
| Local RED control (pre-fix code) | turn `c221ab09-aec0-4034-a0cd-703db82a78bd` |
| Local GREEN (post-fix code) | turn `40a01c94-9a7d-43b1-a3d4-93ff329b417c` |
| Leaked bytes, exact source | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` lines 135–136 (`Aquarius` / `27°02′48″`), line 714 (`Purva Bhadrapada`) |
| CI detector | `platform/src/__tests__/lib/bundle/native_corpus_scope.real_manifest.test.ts` |
| Unit detector | `platform/src/__tests__/lib/bundle/bundle_hydrator.test.ts` (`native-corpus chart scoping` block) |
