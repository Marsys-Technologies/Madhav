---
artifact: G11_GRAZE_CONTACT_OPTIONS
version: "1.2"
status: "DRAFT for the owner — a plain-language options note; authorises NOTHING. The decision is the owner's (steward GRAZE-INTERIM, 2026-10-05; corrected by steward GRAZE-CORRECTION and Codex VERIFIER-CODEX-1)."
date: 2026-10-05
author: Stream B (Śāstra)
changelog:
  - "1.2 (2026-10-05, steward WRAP-TANGENCY / Codex on PR 3156): addendum — the exact-zero station TANGENCY is NOT this gap; separate pre-existing builder limit, never triggered on the real chart; counts and disposition added at the end."
  - "1.1 (2026-10-05): the worked example is from the TEST database's stub chart, not the native's chart (steward GRAZE-CORRECTION); the real-chart count is now given, computed read-only with the real natal longitudes and the pinned ephemeris (no build); the real cost of option A is stated (contact identities are numbered by the order of exact crossings, so adding grazes can renumber existing ones; Codex VERIFIER-CODEX-1)."
  - "1.0 (2026-10-05): first version (its example wrongly called the stub point the native's)."
---

# Near misses that never become exact (a "graze") — what to do with them

## What is the question?
When a planet moves past a sensitive point in the chart, the system counts it as a **contact** while the planet is within **one degree** of that point or of one of its aspect points. Normally the planet passes *through* the exact point, and the system stores the contact around that exact moment.

Sometimes a slow planet turns around (appears to move backwards, then forwards again) **before** reaching the exact point. It then spends days or weeks inside the one-degree zone, comes close, and never touches the exact point. That is a **graze**.

**An illustration (from the TEST database's stand-in chart, not the native's):** Jupiter, from 15 December 2003 to 23 January 2004 (39 days), stayed within one degree of an aspect point of the stand-in chart's Venus (at 265.39 degrees), came as close as **0.4 degrees** on about 4 January 2004, and never became exact. On the system's own strength scale (1 at exact, 0 at one degree away) that stretch peaks at **0.6**. This particular stretch says nothing about the real chart; it only shows the kind of event.

## How often does it happen on the REAL chart?
Computed **read-only, with no build**: the real natal longitudes (from the stored chart facts) and the pinned ephemeris, over 1998-01-01 to 2026-04-17, for every planet-to-point stretch the third and fourth paths (P3 and P4) would record (98 distinct planet / relation / point combinations across the 18 classes that have signature houses; the Moon is handled separately):

| What | Count | Meaning |
|---|---|---|
| Stretches inside the one-degree zone, in all | 1,945 | |
| **Plain** (the planet crosses the exact point, no turn-around inside) | 1,899 | stored and checked as designed |
| **Seam** (the planet turns around inside the zone *and* crosses the exact point on both sides) | **20** | stored as two touching contacts; the checker used to refuse these, fixed in PR 3143 |
| **Graze** (zone entered, exact point never reached) | **24** | **no contact is stored; the independent checker refuses the build** |
| Partial (a piece of a stretch with no crossing, but not a whole graze) | 0 | |
| Cut by the end date of the build (April 2026) | 2 | handled separately |

The 24 grazes: Mercury 10, Saturn 5, Jupiter 3, Mars 3, Venus 3; closest approaches from 0.14 to 0.99 degrees (strength on the 0-to-1 scale from about 0.01 to 0.86; median closest approach 0.6 degrees). Each of these distinct stretches can serve several classes. Full list: `/Users/Dev/pravaha/run/GRAZE_REAL_CHART_COUNT_20261005.txt`. In other words: **on the real chart this is not a rare corner case; a full build will meet it about 24 times.**

## Why it matters now
The two halves of the system disagree about grazes:
- The **builder** only stores a contact around an *exact* crossing, so it stores nothing for a graze.
- The **independent checker** re-reads the sky and expects *every* stretch inside the one-degree zone, so it expects the graze and refuses the build ("expected contact … is not in the ledger").

Nothing in the code or in any project document settles which is right. **A full build stops on the first graze** until this is decided.

## What the specification says
The design specification defines a contact as a conjunction or an aspect **within orb** (within the one-degree zone), and the strength is highest at exactness and falls to zero at one degree. On that reading **a graze is a contact**, with a lower peak. But the stored record of a contact is built around its exact moment, so the system as built has no place for a contact that never becomes exact.

## The options
| | What it does | What it costs | What changes for readings |
|---|---|---|---|
| **A. Count grazes** (store them) | The builder records graze contacts, using the moment of closest approach in place of the exact moment, with a clear label. | **The real cost: contact identities are numbered by the order of the exact crossings of each planet-and-point pair (identity = the pair plus its crossing number). Putting grazes into that ordering can renumber the identities of existing contacts**, so every stored reference to them would have to be rebuilt; or grazes get a separate numbering, which is a design decision of its own. Also: a change to the database design (protected window), changes to the builder and the independent checker, new reviews, a full rebuild and re-timing. Largest. | Faithful to the specification. About 24 more stretches would count, at strengths from about 0.01 to 0.86. |
| **B. Ignore grazes, say so** | The checker stops expecting stretches with no exact crossing; every report states plainly that near misses are not counted. | Small code change; no database change; a stated limit in every report. | About 24 stretches that the specification would count are **not** counted. Fewer contacts. Quietly changes which readings exist unless the limit is stated. |
| **C. Rule that a contact needs an exact crossing** | Same behaviour as B, but recorded as the rule (an amendment to how the specification is read), not as a limit. | Small code change plus a recorded ruling. | Same readings as B; the difference is that it becomes the intended meaning. |

## Where things stand
- To let the **small test** finish and **count** grazes through the real pipeline, an interim is in the review PR (3143): on an unsealed, never-served test run only, grazes are **reported by name** (planet, point, dates, closest approach, strength) instead of stopping the run. A full build is unchanged and still stops.
- **Measured through the real runner on the test database** (stand-in chart): the marriage class, whole horizon, reports exactly 1 graze and completes. The real-chart count above is by arithmetic, not by a build.

## Recommendation
Decide **after the small test confirms the count through the pipeline**, but lean to **A** as the end state, because it is what the specification says and with 24 stretches on the real chart a silent drop is not small. Settle the numbering question (renumber versus separate numbering) before choosing A. B is acceptable only as a **stated, temporary limit** with the owner's approval; C only if you want near misses *never* to count. Whichever is chosen must be written down before the full build results are read, because A, B and C change which readings the product has.

## Addendum (v1.2): the station TANGENCY is a different defect, not a graze

Codex (on PR 3156) noted that when the body reaches the ray level EXACTLY at its station and turns back (a tangency with a root), `contacts.py` keeps only one of the two station-end candidates, so the support covers the approach and omits the return, and the independent certification rejects it (synthetic reproduction only).

**Disposition: a separate builder defect, not part of this gap.** A graze has NO exact crossing, so no contact is minted at all, and the decision (mint / ignore / require a crossing) is the owner's. A tangency HAS an exact root, so a contact is minted; what is wrong is which piece of it is kept. The mechanism is the seam de-duplication in `contacts.py` (about line 313): it exists for the 0/360 wrap, where two wrap-cut arcs report the same physical crossing, and it is gated on the ray level being EXACTLY 0 modulo 360 (`float(level) % 360.0 == 0.0`); with the body also exactly at a station there, the two station-end candidates look like that wrap twin and one is dropped. It does not need an owner decision: the right behaviour is simply to keep both (they are in different arcs on opposite sides of the station, so they are not the same crossing), as the seam rule already treats a station inside a band.

**Real chart (read-only arithmetic, 140 ray levels over the 98 point obligations):** the smallest distance of any ray level from exactly 0 or 360 is 0.8388 degrees (Saturn's aspect ray to natal Mercury); **0 ray levels are within 0.000001 degree of 0/360, so the gated path is never taken on this chart.** Independently, of the 112 stations inside an in-band stretch over 1998 to 2085, the closest approach to the ray level AT a station is 0.00170 degrees (Jupiter aspect to natal Venus, 2016-05-09) and 0.00179 (Mercury conjunction to natal Sun, 2047-02-26): **0 within one solver accuracy (0.00028 degree), 0 within 0.001, 2 within 0.01, 5 within 0.05.** The two closest are real transversal pairs of roots either side of the station and go through the ordinary two-contact path (the 2016 one is among the 20 seams of the scored horizon that all pass the strict junction test).

**What to do:** record it as a known limit (it can only appear for a point whose longitude is exactly a multiple of 30 degrees or a ray derived exactly to 0, e.g. a placeholder at a sign cusp, with the body at a station exactly there); fix it the next time `contacts.py` is touched, with a test that builds the exact tangency from a synthetic curve; it does not block the small test or the full build for the pinned chart. Stream A owns the fix (builder code).

