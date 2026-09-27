---
title: "KIMI_REVIEW_PACKET_SANGAM_SUMMARY_v1_0"
version: "1.0"
status: COMPLETED
role: review_request
owner: "L3 Saṅgam design session (madhav-d9)"
layer: L3
asset: ka_sangam
description: "Author-written packet sending the layman ruling summary to Kimi K3 (max effort) for review."
frontmatter_added: "2026-09-23 — prepended for governance-gate parity (madhav-fc G18 finding: briefs tree is outside the frontmatter gate); body byte-identical to the prior commit"
---

# Review request — the layman summary of the seven Saṅgam rulings

You are Kimi K3, acting as an independent reviewer. Earlier you produced recommendations on these
seven decisions (KIMI_K3_RECOMMENDATIONS_SANGAM_DECISIONS_v1_0.md). Since then the author verified
your citations, adopted most of your recommendations, overrode one, and the ruling sheet
(SANGAM_RULING_SHEET_v1_0.md) accumulated a day of cross-session corrections. The author then wrote
the **layman summary below** for the native (Abhisek Mohanty, the chart owner) to rule from.

**Your job: break the summary before the native reads it.** Do NOT write any file. Print your review.

## Read (working directory is the repo)
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_RULING_SHEET_v1_0.md` — the reference the summary must be faithful to
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KIMI_K3_RECOMMENDATIONS_SANGAM_DECISIONS_v1_0.md` — your own prior advice
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4.md` §8 — the decisions as framed
- Optional depth: `SANGAM_ELEVATION_FINAL_v1_0.md`; `EVENTS.jsonl` (last ~15 lines) for today's corrections

## What to check, in this order
A. **Fidelity.** For each of the seven items: does the summary say what the sheet says? Flag any
   claim that is stronger, weaker, or different from the sheet — especially numbers, pāda
   assignments, and what is "measured" vs "cited" vs "computed".
B. **What the layman framing loses.** For each item: is anything material to the *ruling* omitted
   that a plain-language reader needs (a cost, a precondition, a dependency, a caveat)? Be specific
   — quote the missing point from the sheet.
C. **Where the author overrode you.** M-1 cusp frame: you recommended Śrīpati; the author
   recommends Placidus-as-stored because L1 already computes Placidus cusps (ga_positions_writer,
   ga_kp_significators) and B.10 forbids values with no L1 fact behind them. Do you concede, hold,
   or amend — and why, classically and structurally? Also M-1d: the author's mean-node
   recommendation now rests on L1 serving ONLY `RAH_MEAN` (no `RAH_TRUE` subject) — does that
   change your reasoning?
D. **Recommendation quality.** For each of the seven: is the author's one-line recommendation the
   right call, and is its stated reason the *real* reason? Where you disagree, give the alternative.
E. **Priority order.** The author says: M-3 first (blocking, needs an owner), then M-1's node
   sub-decision (changes a natal pāda), then M-2's BAV=4; the rest can be "agree". Is that the right
   order for the native's attention? What would you move?
F. **Missing.** Anything the native should be told before ruling that is in neither the summary nor
   the sheet.

## Standards
Acharya-grade. Tag every claim [D] doctrine (name the text) / [P] practice / [J] judgment / [U]
unverified. Never present a number as fact. Say UNVERIFIABLE rather than guess. Close with:
**Verdict** — `SEND_AS_IS` / `SEND_WITH_EDITS` (list them, verbatim replacement text) / `REWRITE`.

---

## THE SUMMARY UNDER REVIEW (verbatim, as written for the native)

Here are the seven, in plain terms, with my recommendation on each.

**1. M-1 — How should Saṅgam decide a planet is "touching" a point in your chart?**
Today it uses Western-style angles (60°, 90°, 120°) that Vedic texts don't use, and it searches on the wrong side for Mars and Saturn's special aspects. Proposal: four proper contracts — Parāśari planet-specific aspects (the main one), Moon-based gochara with vedha, Jaimini sign-aspects (only on a Jaimini route), Tājika (only for annual questions). Two sub-decisions ride along: **node convention** — your natal facts use *mean* Rāhu, the transit scanner uses *true*, and the L0 store is true under a contract that says mean; and **house cusps** — Kimi suggested Śrīpati, but L1 already stores Placidus.
*Recommendation:* adopt the four contracts; **mean node**, because that's what L1 already serves and names; **Placidus-as-stored** for cusps, not a third house system. Note: ruling mean isn't free — you must also pick how to handle the true-node L0 store (I'd keep it and derive mean at read, with the ~1° disagreement declared on every row).

**2. M-2 — Aṣṭakavarga: is 4 bindus "good enough"?**
Modern practice says ≥4 supports. Phaladīpikā's own list says 3 = fear, **4 = fear**, 5 = accomplishment. The current code doesn't use this at all — the check has been dead.
*Recommendation:* three states — **≥5 support, 4 indeterminate, ≤3 obstruct** — evaluated for the transiting planet's *own* bindus, not just the sign total. Record which edition's vocabulary we use (Santhanam's "bindu" means the *bad* mark).

**3. M-3 — Your June ruling has two halves that now contradict each other. Which governs?** *(Blocking.)*
§4.5 said "no sky-scanning inside Saṅgam — consume pre-computed transit events, slow planets only." §4.6 said "pick a planet per signature and scan, with a confidence gate." The code did §4.6. Two elevations (E1, E3) can't start until you say which stands.
*Recommendation:* **re-affirm §4.5 as the mechanism** (Saṅgam consumes events, doesn't scan), keep §4.6's planet-attribution as a refinement, and grant a *bounded* fast tier (Moon/Sun contacts only inside an already-qualified window). The catch: someone upstream must then *produce* those events — either the Gochara stream amends the shared scanner, or its proposed new kernel is approved. **Only you can name that owner.**

**4. M-7 — Should a planet's weakness silence a window, or colour it?**
Today, if the lord is debilitated the score is exactly 0 — the window vanishes. But a weak lord classically produces *trouble*, not nothing; erasing it hides the adverse events you'd most want to see.
*Recommendation:* **yes, separate them** — intensity and valence as distinct fields; dignity moves from "gate" to "sign." The strongest-supported item on the sheet, three independent texts.

**5. M-4 — Which divisional chart judges which domain, and can any condition veto?**
Marriage → D9, career → D10, and so on; BPHS gives the full list (wealth D2, parents D12, learning D24, evil D30…).
*Recommendation:* adopt the full table; **no condition ever vetoes**, all are signed conditions; the "relevant lords" per domain get ratified line by line, not automated.

**6. M-5 — When Saturn crosses a point three times (direct-retro-direct), is that one event or three?**
Today: three rows, counted as three witnesses.
*Recommendation:* **one episode with three child passes**, no default "peak" pass, and the monthly-wave consumer counts occupied days, not rows.

**7. M-6 — When may the learning layer (L5) start scoring Saṅgam's windows against your real life?**
*Recommendation:* **open consumption once identity is stable**, but keep "empirically evaluated" closed until five conditions hold — predeclared protocol, held-out chronology, a minimum count *you* set, censoring rules, base-rate discipline. The machinery must be willing to say "no demonstrated skill."

**Where to spend your attention:** #3 first (it blocks two elevations and needs an owner named), then #1's node sub-decision (it changes a natal pāda in your own chart — true Rāhu is Rohiṇī pāda 4, mean is pāda 3), then #2's BAV=4. The other four can be "agree" if the reasoning holds for you.
