---
artifact: KALA_BLUEPRINT_REVIEW
canonical_id: KALA_BLUEPRINT_REVIEW
version: "1.0"
status: CURRENT
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc), at the native's request"
reviews: "KALA_ELEVATION_BLUEPRINT_v1_0.md v4.0"
method: >
  Every gap below was verified against the repository, not inferred from the document. Where a
  claim rests on something this session could not check (both DB endpoints refusing), it says so.
  The review holds the blueprint to the standard the campaign itself produced: a claim with no
  code path that could make it false is null, and a document that only asserts will rot.
---

# Review of the Kāla elevation blueprint — what is missing, how to raise it, how to use it

## 1. Verdict

The blueprint is a good **map** and no longer a good **instrument**. Its body was written before
the campaign that tested it, and by v3.5 the truth had migrated into a 920-line diary of addenda
while the plan above it went stale on decisions, holds, portfolio rows and exit criteria. v4.0 fixes
that inversion. But the deeper problem is that the document cannot prove the thing it plans:
**the proof instrument it cites was never built**, the **contracts that make 22 assets a layer have
no owner**, and **no per-asset state exists** from which its own headline could be computed. The
campaign that used this blueprint did excellent tier-1 work — correctness, citations, conventions —
and the blueprint has no way to show that any of it made a reading *better*.

## 2. The stock-take: what changed between v3.5 and v4.0

| section | was | is |
|---|---|---|
| §9 decision queue | eight open decisions | D6/D7/D8 **ruled**; D1 open; D2/D3/D4/D5 **confirmed unruled**, with the receipts enum verified absent from code |
| §4 stream rows | "decide which member owns the served product"; "century on hold" | N-5/N-6a/N-10/N-14 ruled; Saṅgam and Kṣetra **closed**; stage-3 entry gate named |
| §6 W0 exit | cites `KALA_PHASE01_CLOSE_v1_0.md`; "harness carries `.se1` files" | that file **does not exist**; G4 **retracted** (files were present; the gap is the unowned backend) |
| §8 proof | "the frozen baseline `KALA_BASELINE_v1_0.md`" | **never created**; the W0 benchmark is a timing baseline with zero L3-Q references |
| §7 machinery | migrations at 1071+ | 1075+; 1070–1074 claimed by four unmerged branches |
| §4 denominator | "22" asserted | derived: 27 registered, 3 deleted, 1 tombstone, 1 unknown → **22 ± 1** |
| §11 | 28 addenda, 920 lines | moved to `KALA_ELEVATION_CHRONICLE_v1_0.md`; body rewritten from them |

Three artifacts the blueprint cited as if they existed do not: `KALA_BASELINE_v1_0.md`,
`KALA_PHASE2_DECISIONS_v1_0.md`, `KALA_PHASE01_CLOSE_v1_0.md`. That is the document's own §N.8
defect — pointers to detectors that were never built — and it is corrected in place.

## 3. What is missing — twelve gaps, each verified

**M1 — The proof instrument.** §8 says the layer is proven elevated by re-running a frozen baseline
of thirteen questions, three proving cases and one ordinary period after each wave, with ablation.
No such baseline exists. The only baseline artifact measures wall and CPU time. *Consequence:* every
wave that closes before this is built closes on *changed*, not *elevated*. *Falsifier:* a file that
freezes those thirteen questions and their current answers.

**M2 — Owners for the five synergy contracts.** §3.3 names the temporal contract, typed
qualification, co-reference, inherited independence and coverage-on-every-result as "layer-owned
packets, one owner each, W1." They appear in this blueprint, its review, one brief and one prompt,
and nowhere else. No packet. No owner. Contract 4's field (`independent_current_count`) is read by
**zero** `ka_*` consumers — its only reader is an L4 writer. *Consequence:* the campaign is elevating
22 assets, not a layer, and "synergistically" is a word in a document. *Falsifier:* a packet per
contract with a named lane.

**M3 — The determinism gate.** G11 says "wipe and rebuild" is unsafe until same-inputs→same-bytes is
checked in CI. The one CI hit for "determinism" is a Pariprashna reducer test. *Consequence:* the
native's rebuild stance is a preference, not a property. *Falsifier:* a build-twice-diff job that
fails.

**M4 — Per-asset state.** The blueprint cannot say where any of the 22 assets sits on either ladder
today. G16 named this as a tracker gap; the blueprint itself should be the tracker's specification.
*Consequence:* `Delivered N/22` and `Data-accepted N/22` are not computable from the document that
defines them. *Falsifier:* a table with 22 rows and two state columns.

**M5 — The receipts enum.** D2 has been "cheap and unblocking" for three versions. It is still
unruled and the enum member exists in no file. *Consequence:* the headline's first number is zero by
construction, forever.

**M6 — The serving contract.** G12 says serving is Pūrṇa's and L3 supplies "interface packets
only." The blueprint never states what L3 *guarantees* to any reader — field-level, per object.
*Consequence:* the last inch, which is the entire user value, is a pointer to another team.
*Falsifier:* an L3-owned interface spec with sentinel tests.

**M7 — The learning loop.** The product's own definition is calibrated, testable, correctable
prediction. The blueprint says L5 owns calibration and stops. It never says how a Kāla window becomes
an L5 prediction candidate, how an outcome flows back, or what changes in Kāla when it does.
Saṅgam's E6 gate now exists and the blueprint did not integrate it until v4.0. *Falsifier:* a
section that names the candidate path, the outcome path and the recalibration hook.

**M8 — UX acceptance.** §1 defines two experiences and each wave says "the person can now…". None
of those lines is checkable. *Consequence:* the user-experience goal the native named first has no
test. *Falsifier:* a scripted walkthrough per wave, run and recorded.

**M9 — Doctrine as machinery.** The campaign earned five disciplines (count(*) for absence; the
ruling set not a ruling; convergence is not verification; assert the post-condition; no signal
without a detector). All five live in prose. *Consequence:* the next campaign inherits them as
memory, which is how the four-name corpus list survived a day. *Falsifier:* at least one of them
as a CI guard.

**M10 — The value gap at the largest asset.** G8: `kala_field` (~8.6M rows, the layer's largest
product) has no retrieval capability. *Consequence:* the best-elevated asset in the layer would be
invisible to the person. Nothing else in the blueprint matters for that asset until this does.

**M11 — Restore drill.** G3: PITR disabled, no drill ever run on a `kala_*` table. *Consequence:* a
mutating campaign with no rehearsed way back, and every wave's "rollback" line is aspiration.

**M12 — Cost.** G5: the registry claims 24 min per chart; ≥7.5 h measured. The blueprint correctly
promises no schedule, but never says *when* cost becomes known. *Falsifier:* a measured per-asset
cost row after the first W1 build.

## 4. How to elevate the blueprint significantly — six moves, ranked by leverage

**E1 — Build the proof instrument first (M1).** Freeze `KALA_BASELINE_v1_0.md`: the thirteen
L3-Q questions, the three proving cases, one ordinary period, each run against *current* serving and
the answers recorded verbatim with their coverage and qualification. This is one session's work
and it is the only thing that converts every subsequent wave from "we changed it" to "we can show
the delta." Without it the blueprint is a plan for work that cannot be shown to have mattered.

**E2 — Make the blueprint a falsification surface.** Every claim in §1–§8 carries, inline, *what
would make it false and who checks*. That is §N.8 applied to the plan. The campaign's central lesson
was that documents asserting without detectors rot within a day; this should be the one document
that structurally cannot.

**E3 — Add the per-asset state table (M4) and make it the tracker's spec.** 22 rows, both ladders,
owner, wave, blocker, exact unblock condition. The scheduler in §7 reads it; the headline is
computed from it; G16 closes because the projection now has a source.

**E4 — Name the five contracts as the first W1 packets (M2), using the same reframe as L0.** They
are not a role; they are five jobs. Contract 1 is a fix in one file ten writers import. Contract 4
is a field Saṅgam already emits plus readers nobody wrote. State each as a bounded packet with a
lane, and the word "synergistically" starts meaning something.

**E5 — Add three sections the blueprint lacks:** the serving contract L3 guarantees (M6), the
learning loop from window to outcome to recalibration (M7), and per-wave UX walkthroughs (M8).
Each is short. Each is currently a pointer to somewhere else.

**E6 — Turn the five disciplines into guards (M9).** Concretely: a corpus-absence lint — any
`not_in_corpus` in code must cite a `count(*)` receipt; the governance frontmatter gate extended to
the briefs tree with parse failure as a violation (G18); the build-twice-diff (G11). Three guards,
each with a code path that fails.

## 5. How to use the blueprint to take Kāla to the next level

The blueprint's highest use is not as a schedule. It is as **the layer's contract with the person
who reads it** — and "next level" has a precise meaning in the product's own terms.

**The campaign so far has been almost entirely F24 tier 1: computational correctness.** Node
conventions, citations, epoch declarations, a blind anchor replaced, a corpus error unwound. All of
it necessary. None of it is what a person experiences. **Tier 2 — explanatory value, a *better
reading* — is what "next level" means for the person, and nothing in the layer measures it. Tier
3 — empirical performance — only acquired a gate last night.** The blueprint's job is to carry the
layer across that line, and here is how each part of it does that:

1. **§3.3 is the elevation.** The person the native described wants readings that differ honestly,
   each carrying its confidence and salience, so the reconciling LLM can weigh them without
   force-fitting. That is *exactly* what the five contracts supply: co-reference so readings line
   up; typed qualification so each says how much it knows; coverage so an absent window is not a
   universal denial; inherited independence so three restatements of one source do not count as
   three. **Owning those five contracts is the difference between a correct pile of assets and a
   layer an LLM can reason over.** Do E4 before any further per-asset work.

2. **§8 is how elevation becomes visible.** Once E1 exists, every wave answers the same thirteen
   questions and the delta is the elevation — with the ablation showing which asset earned it and
   the added-error count showing what it cost. That is tier 2 measured. Today it is unmeasurable.

3. **The E6 gate is the door to tier 3.** Kāla windows become L5 prediction candidates under a gate
   that can only see large effects and says so. That is the product's promise — calibrated,
   testable, correctable — beginning to be true for this layer. Use the blueprint's learning-loop
   section (E5) to make the path from window to outcome to recalibration explicit, so the loop
   runs by design rather than by someone remembering.

4. **Fix the last inch first (M10, M6).** The layer's largest asset is unreadable by the product.
   An elevation that the person cannot reach is not an elevation. The interface contract and the
   `kala_field` read path are worth more to the person than any three frontier assets.

5. **Use the disciplines as inheritance, not memory.** The campaign proved that four careful
   sessions checking each other can hold one false premise for a day, and that one query breaks
   it. The next campaign should not have to relearn that. Guards (E6) make the lesson a property
   of the repository.

6. **Keep the chronicle separate and keep it honest.** The value of last night was not the
   findings; it was that every one of them was verified or retracted in place, with the retraction
   recorded as loudly as the claim. The blueprint stays current; the chronicle stays true. Neither
   should be edited to make the other look better.

## 6. What I would do first, in order

1. **E1** — freeze the baseline. One session. Everything after it becomes measurable.
2. **E4** — five contract packets with lanes. This is the layer-level elevation.
3. **D2** — the receipts enum. One member, no migration, three versions overdue.
4. **M10** — the `kala_field` read path and the L3 interface spec. The last inch.
5. **E6** — the three guards, starting with the corpus-absence lint.
6. **E3** — the per-asset state table, once the L0 repair and the three streams' stage-3 work
   give it something true to show.

The L0 repair runs in parallel and blocks none of these.
