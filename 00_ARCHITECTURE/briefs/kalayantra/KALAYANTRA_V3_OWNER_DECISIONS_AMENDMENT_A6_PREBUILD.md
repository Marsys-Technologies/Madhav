---
title: KĀLA-YANTRA v3 owner decisions — Amendment A6 (pre-build everything buildable; rehearse and pre-stage the chain)
version: 1.0
status: CURRENT
date: 2026-10-16
amends: surrogate ruling SR-A4-01 (pre-build), Amendment A4 (D-30 hand-offs), the Wave 4 phase procedure in the plan model (pre_acceptance steps)
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS. Amended files stay byte-identical, as A1–A5 did.
changelog:
  - 1.0 (2026-10-16): created on the owner direction of 2026-10-16 ~07:30Z: "get the other pieces ready too so we catch up fast when gates open; run at full capacity; expedite the chain."
---

# Amendment A6 — pre-build and rehearse

**Written for:** the cockpit session, the owner surrogate and every fleet job.

## §1 · Measured basis (tracker 2026-10-16 07:16Z)

| Measure | Value |
|---|---|
| Open items | 143 (131 waiting, 10 parked, 2 ready) |
| Already merged, waiting on a gate ("banked") | 49 |
| Open items that cannot be pre-built (operations, decisions, verdict reviews, close items) | 42 |
| Open items with code already in flight | 18 |
| **Open code/artifact items with no branch yet: pre-buildable now** | **83** (Wave 4: 59 · Wave 2: 24) |
| Tracker detectors starved by the 8 s tick budget | 100 items "unmeasured", 23 "detector timed out" |

## §2 · D-40 — pre-build everything buildable

Every open code or artifact item is built now under pre-build (SR-A4-01 generalised), in this order: chain items whose code gates the next Wave 4 phase; Wave 2 unlockers (K5-G1a/K5-G1b family, K5-2 family, retirement chain, K9-5/K9-6); the rest. Inherited-PR children are batched per phase into one packet each, as P02/P05/P08/P09 were. Concurrency runs as high as CPU idle ≥ 15% and free memory ≥ 20% allow. Each lands as "built, waiting on gate" and closes in the sweep when its gate opens.

## §3 · D-41 — rehearse every production operation before its real run

Each chain operation (small-test dispatch, teardown, measuring build, final build, protected window, qualification, flip, live readback) is first executed end to end on a throwaway target by its own agent job while the previous phase is still running, so the real run passes first time. The rehearsal receipt attaches to the phase's pre_acceptance step.

## §4 · D-42 — pre-stage the chain now, not phase by phase

Leases, backup-and-restore verification and tooling checks for J-2a are prepared before J-1a closes; the measuring build's dispatch, oracle and teardown are prepared before the small test ends; the protected-window mechanics are verified on the test cluster in advance; the century build's wall-clock is measured and it is scheduled to start the moment J-4a's readings exist; K5-G1a's steps are built in parallel with KA-3a against its interface.

## §5 · D-43 — the critical path today

Teardown fixtures (#3587) → main green → lift HOLD_SMALLTEST; J-1a steps (#3585, #3586) → J-1a done → J-2a dry run then run 1 → run 1 clean ⇒ run 2 not applicable (A4 D-30) → J-3c. In parallel: KA-3a → K5-G1a → K5-G1b → the sweep of 12 banked Wave 2 items. Each phase's wall-clock is reported as it completes.

## §6 · Infrastructure precondition

The tracker's non-blocking rebuild lands first: with the 8-second tick budget abandoning detector results, the tracker cannot see what is merged or ready, and neither launch-on-ready nor completion can work from a stale view.

## §7 · Success (72 hours)

| Measure | Target |
|---|---|
| Pre-buildable items with no branch | 0 |
| Chain phases whose real run failed after a passed rehearsal | 0 |
| Gap between a gate opening and the next phase's dispatch | under 15 minutes |
| Items "unmeasured" in the tracker | 0 |
