---
artifact: G9_HORIZON_COVERAGE_OPTIONS
version: "1.1"
status: DRAFT for the owner — an options note; authorises NOTHING
date: 2026-10-04
author: Stream B (Śāstra) (steward GAPS-G8-G9)
scope: "One page, plain language: what the new Gochara engine ('5.0') will and will not answer, and three ways to deal with the dates it does not cover. Gap G9 of REBUILD_AND_UPSTREAM_SEQUENCING_v1_0 (v1.12)."
changelog:
  - "1.1 (2026-10-05, steward OWNER-RULING-5): the owner confirmed the product WILL move to Gochara 5.0 and leans to about 100 years from birth (1984 to 2084); option A is therefore effectively out; the note now says what an extension needs technically, with the one fact the lean raises: the sky data starts in 1998, not 1984."
  - "1.0 (2026-10-04): first version."
---

# G9 — what will "5.0" answer after 17 April 2026?

## The situation in plain words
The new engine is being built for **1 January 1998 to 17 April 2026** — the 28 years that the evaluation scores against your recorded life events (the scoring rules, EVALUATION_PROTOCOL_v2_3, end on 17 April 2026, the last day with recorded events). **Nothing in the new engine answers a date after 17 April 2026** — not the five and a half months since, and not any future date. The sky data underneath is already built to the year 2085, so the planetary geometry exists; what does not exist is the new engine's own windows and records beyond April 2026. A finished ("sealed") generation is never edited, so once the new engine is sealed over the scored period it cannot be stretched to cover more; a longer horizon means a new generation. Today the product answers every date from the older engine ("3.0", a century of ten-year slices from birth). Two further facts matter: the switch that makes the new engine the one people are served from does not exist yet (the database actually refuses it, on purpose), and the serving pointer holds **one** engine per person — so "new engine for the past, old engine for the future" is not something the product can do today without building it.

## Three options

**A. Keep the new engine as the scored past only; the old engine keeps serving the future.** *(Effectively out since the owner's decision of 4 October.)*
- Nothing more to build for the engine itself. 
- But the product's most useful questions are forward-looking, and they stay on the old engine; to serve the past from one engine and the future from another, a date-splitting layer must be designed and built. Without it the new engine is evidence only and is never switched on for readers. 
- Cost now: none. Cost later: a serving design that nobody has started.

**B. Build the full generation at a longer horizon from the start** (for example to 2085, the end of the sky data, or to a nearer date such as 2050).
- Work grows roughly in step with the number of days covered: **about 3.1 times** the work of the scored horizon for 1998–2085, about 1.8 times for 1998–2050 (an estimate from the day counts, not a measurement; the small test will give a real per-class figure at the scored horizon first).
- One build, one seal, one approval — but that one approval covers future windows that nobody can test against events, and the first full build has not been timed at all, so the biggest and riskiest build is also the first.
- The scoring rules need one added sentence: windows after 17 April 2026 are served but **not scored** (they have no outcomes yet). The scoring of the past is unchanged.

**C. Seal the new engine over the scored past first ('5.0'), then build a longer-horizon generation ('5.1') once '5.0' is sealed and timed.**
- '5.0' gives the evidence the campaign needs now (new engine against old on the recorded events); '5.1' adds the future with a real timing in hand, and replaces '5.0' as the one served (the old generation is kept whole).
- Cost: two full builds and two seals — roughly 1 + 3.1 times the scored-horizon work for a 2085 end date, against 3.1 for option B alone, i.e. about a third more total work in exchange for a smaller first step and a decision on the end date made with measured numbers.
- Same scoring sentence as B.

## Recommendation
**Option C** (unchanged by the owner's decision of 4 October: it was already the recommendation, and option A is now out), with the end date of '5.1' decided after the first full '5.0' build has been timed. It gets the scored evidence soonest, keeps the first big build the smaller one, and does not ask you to approve a future you cannot yet test. Option A is the right choice only if forward-looking answers are deliberately out of scope for this engine.

## What the owner's decision of 4 October changes (v1.1)
The owner has confirmed that the product **will** move to Gochara 5.0 (recorded in `NATIVE_DIRECT_RULINGS_20261004.md`; intent, not an instruction to switch now) and leans to **about 100 years from birth, 1984 to 2084**. A switch with coverage that ends on 17 April 2026 would leave every future date unanswered, so **option A is out**; the real choice is **B (one longer build) or C ('5.0' first, then '5.1')**. Still not ruled: the end date, and the start date.

**One fact the lean raises: the sky data starts on 1 January 1998, not in 1984.** The engine can be stretched to the end of the sky data (1 January 2085) with no new sky work; reaching back to 1984 means building the planetary geometry for 1984 to 1998 as a new, separate sky record set (a "backward partition is a new convention"), which is its own piece of work and changes the identity of everything built on it. The scoring only needs 1998 onward (the life-event log is scored from 1998), so the start can stay at 1998 for scoring; what is open is whether readers must also be answered for 1984 to 1998 (the legacy generation covers a century from birth, 1984 onward).

## What an extension needs technically
1. **One constant and its limits.** The build horizon is one constant in the writer (DEFAULT_HORIZON, now 1998-01-01 to 2026-04-17). The test-slice rules refuse any horizon outside it and require the one-class "full" run to equal it exactly, so changing the constant moves those limits with it. Changing it changes the implementation lock, the goldens and the writer digests (all regenerated), and the horizon of every candidate manifest.
2. **Sky data:** already built to 2085-01-01 (the substrate convention), so an end date up to 2084-12-31 needs nothing new; a start before 1998 needs the new sky record set above.
3. **Daśā rows:** the SETTLED-1 daśā rows (Vimśottarī, first three levels) run from 1950-01-01 to 2100-12-31, so they already cover 1984 to 2084 (read from the local capture of the re-pin; the rows are window-clipped at both ends by design).
4. **Scoring rules:** one added sentence in the evaluation protocol: windows after the observation mask (2026-04-17) are served but not scored. The scoring of the past is unchanged; the evaluation harness must clip at 2026-04-17 (to confirm in the harness code before the change).
5. **Cost:** work grows roughly with the number of days covered. 1998 to 2085 is 31,777 days against 10,334 today: **about 3.1 times**; 1984-02-05 to 2084-02-05 is 36,525 days: about 3.5 times, plus the new sky record set. Not measured: the only timing on record is 712 seconds for the whole 298-step plan on a test database with stand-in data at the current horizon, and the small test's second run will give the real per-class figure; verification and the seal brief grow too.
6. **Seal and approval:** the first approval would cover future windows nobody can test against events; that is acceptable only if the owner accepts "served, not scored" for the future, and it is the reason option C keeps the first seal smaller.

## The one thing I need from you
**Which future dates must the product answer, and how far ahead** (next 5 years, 25 years, the whole century)? That fixes the end date for B or C. This must be settled **before the flip decision (D-FLIP) and before the full build is sized.** It does not block the small test.

## What is known and not known
- Known: the horizon (EVALUATION_PROTOCOL_v2_3 section 1; the writer's DEFAULT_HORIZON); the sky data's 1998–2085 span; that the authority pointer holds one generation per person and refuses a '5.x' one today (migration 1236); the old generation's century-from-birth design (BASELINE_3_0).
- Not measured: the real cost multiple (the small test's second run gives the per-class cost at the scored horizon); how the old generation's windows end (I did not read production for this: the Gochara measurement hold on the canonical chart stands).
- No campaign document says how future dates are meant to be served: that is why this is an owner question.
