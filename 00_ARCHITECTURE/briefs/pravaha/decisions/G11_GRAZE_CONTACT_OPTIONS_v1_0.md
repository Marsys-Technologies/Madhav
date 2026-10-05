---
artifact: G11_GRAZE_CONTACT_OPTIONS
version: "1.0"
status: "DRAFT for the owner — a plain-language options note; authorises NOTHING. The decision is the owner's (steward GRAZE-INTERIM, 2026-10-05)."
date: 2026-10-05
author: Stream B (Śāstra)
---

# Near misses that never become exact (a "graze") — what to do with them

## What is the question?
When a planet moves past a sensitive point in the native's chart, the system counts it as a **contact** while the planet is within **one degree** of that point or of one of its aspect points. Normally the planet passes *through* the exact point on its way, and the system stores the contact around that exact moment.

Sometimes a slow planet turns around (appears to move backwards, then forwards again) **before** reaching the exact point. It then spends days or weeks inside the one-degree zone, comes close, and never touches the exact point. That is a **graze**.

**Real example, found on the native's chart.** Jupiter, from **15 December 2003 to 23 January 2004** (39 days): it sat within one degree of the point 120 degrees from the native's natal point at 265.39 degrees (the point at 145.39). Its closest approach was **0.4 degrees**, on about 4 January 2004. It never became exact. On the system's own strength scale (1 at exact, 0 at one degree away) that stretch peaks at **0.6**.

## Why it matters now
The two halves of the system disagree about grazes:
- The **builder** only stores a contact around an *exact* crossing, so it stores nothing for a graze.
- The **independent checker** looks at the sky again and expects *every* stretch inside the one-degree zone, so it expects the graze and refuses the build ("expected contact … is not in the ledger").

On this chart the marriage class alone hits this once in 28 years, and **a full build (and run 2 of the small test) stops on it**. The code does not decide the question; no document in the project decides it explicitly.

## What the specification says
The design specification defines a contact as a conjunction or an aspect **within orb** (within the one-degree zone), and the strength of a contact is highest at exactness and falls to zero at one degree. On that reading **a graze is a contact**, with a lower peak. But the stored record of a contact is built around its exact moment, so the system as built has no place for a contact that never becomes exact.

## The options
| | What it does | What it costs | What changes for readings |
|---|---|---|---|
| **A. Count grazes** (store them) | The builder records graze contacts, using the moment of closest approach in place of the exact moment, with a clear label. | A change to the database design (protected window), changes to the builder and the independent checker, new reviews, and the full build must be redone and re-timed. Largest. | Faithful to the specification. Jupiter in December 2003 to January 2004 would count, at about 0.6 strength. More contacts overall. |
| **B. Ignore grazes, say so** | The checker stops expecting stretches with no exact crossing; the system states plainly that near misses are not counted. | Small code change; no database change; a stated limit in every report. | The 2003-04 Jupiter stretch would **not** appear, although the specification would count it. Fewer contacts. Quietly changes which readings exist unless the limit is stated. |
| **C. Rule that a contact needs an exact crossing** | Same behaviour as B, but recorded as the rule (an amendment to how the specification is read), not as a limit. | Small code change plus a recorded ruling. | Same readings as B; the difference is that it becomes the intended meaning. |

## Where things stand
- To let the **small test** finish and **count** how many grazes exist, an interim is in the review PR (3143): on an unsealed, never-served test run only, grazes are **reported by name** (planet, point, dates, closest approach, strength) instead of stopping the run. A full build is unchanged and still stops.
- **Measured so far** (test database, real sky, whole 1998-2026 horizon): the marriage class has **exactly 1** graze (the one above). The other 25 classes are **not yet measured**; that is what the small test will show.

## Recommendation
Decide **after the small test reports how many grazes there are**, but lean to **A** as the end state, because it is what the specification says and it avoids silently dropping real near passes. Use the interim (report, do not stop) for the small test only. If the count is very small and time is short before the full build, B can serve as a stated, temporary limit, with the owner's approval; C should only be chosen if you want near misses *never* to count. Whichever is chosen must be written down before the full build results are read, because A, B and C change which readings the product has.
