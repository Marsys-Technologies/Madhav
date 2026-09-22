---
artifact: KALA_KICKOFF_REDIRECT_001
version: "1.0"
status: CURRENT
date: 2026-09-22
addressed_to: the Phase 0/1 setup session (worktree /Users/Dev/madhav-l3/setup, branch l3/kala-setup-phase01)
from: the strategic session that wrote KICKOFF_PHASE_0_1.md
effect: amends three items of the kickoff; cancels nothing; adds no scope
---

# Redirect 001 — three corrections to your kickoff, none of which stop you

Your kickoff was written before its author had read the W0 tier beneath the Strategy. Read these
five documents now, in this order, and then apply the three corrections below:

1. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md` (ACCEPTED)
2. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` — §3, §4.1, §4.4, §7
3. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` — reading rules + census
4. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_EXECUTION_FOCUS_AMENDMENT_v1_0.md` — §5, §6
5. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md` — §6 rows dated 2026-09-15/16 for L3

## Correction 1 — item 0.2: your P0 work is right; your close-out framing must change

The kickoff said "no receipt shows the required tests ran." **Receipts exist** —
FOUNDATION_SAFETY §4.1 (Kshetra `3f109869d`, 27 focused / 133 expanded, independent ACCEPT) and
§4.2 (Bhavishya `a3e518864`, 25 passed + disposable lock proof, independent ACCEPT); ledger rows
2026-09-15 04:04 / 04:47 / 05:01. Those proofs ran against a strict fake. What FOUNDATION_SAFETY
itself lists as not run is the **populated real-database rehearsal** (§4.1 "No production
rehearsal is inferred", §4.2 "remains not run"). Your `_p0_harness.py`,
`test_ka_kshetra_p0_planning_readonly.py` and `test_bhavishya_p0_empty_generation_db.py` are
exactly that — **additive, keep them.** In `KALA_PHASE01_CLOSE_v1_0.md`, cite §4.1/§4.2 and the
ledger rows as the accepted prior and describe your work as "real-DB rehearsal added to accepted
fake-based proof." Never write that P0 was unproven before you.

## Correction 2 — decision D1: the design is frozen; ask the native to release a hold, not to re-decide

Your D1 recommends Option A (adopt the 1035/1036 pattern) from a source read. The recommendation
is correct — and it was **already frozen and independently accepted at W0**: FOUNDATION_SAFETY §6
(eight design points) and CURRENT_STATE §4.4 ("reviewed design, not physical infrastructure").
What is open is **physical implementation**, held on `L3-W1-UPSTREAM-GENERATIONS-01`
(FOUNDATION_SAFETY §8 item 2), which waits on the RI-01 precursor release. Reframe D1 in
`KALA_PHASE2_DECISIONS_v1_0.md` to: *"Authorize physical L3 generation infrastructure now, per the
frozen W0 design (cite §6), and state what releases the W1 hold."* Keep your Option A analysis as
the independent confirmation that the frozen design is the right one. Do not present the design as
undecided.

## Correction 3 — item 0.4: overlay, do not rebuild

CURRENT_STATE §4.1 already holds the source-derived DAG (81 declared entries, 32 active-L3 edges,
one producer/use row per identity with W0 disposition), and the FIELD_CONTRACT_REGISTER holds 699
fields across 39 partitions with receiver and falsifying test per row. DP-SD-019 §6 forbids
"another tracker, scheduler or blanket per-field paperwork system." `KALA_IO_USE_MATRIX_v1_0.md`
therefore = the **F12 operator-role overlay on the existing §4.1 edges** (which edge is
`computation` / `applicability` / `counterevidence` / `uncertainty` / `interpretation` / `exclusion`
/ `relevance_navigation` / `evaluation`), citing register rows for fields. If you have already
started a from-scratch matrix, fold it into the overlay and cite the existing map as the base.

## Unchanged

0.1 (baseline on L3-Q01–Q13 — yours is correctly scoped), 0.3 (five cost profiles — the W0
benchmark baseline explicitly defers these to "future packet measurements"; keep), 0.5, and all of
Phase 1. Stop condition unchanged: `WAITING_FOR_STRATEGIC_BRIEF`.
