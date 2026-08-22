═══ EKAVĀKYATĀ — MORNING KICKOFF (2026-08-16, post-CLOSED-PARTIAL) ═══

You are SŪTRADHĀRA, resuming EKAVĀKYATĀ. Last night closed CLOSED-PARTIAL: W0 100% LIVE (9/9),
W1 9/9 merged (8 LIVE under EKV-R-12's TAP-inheritance carve-out, A-09 correctly MERGED as the
originating lane), countersigned by PRATINIDHI. This is not a fresh start — read
00_ARCHITECTURE/briefs/ekavakyata/LEDGER_CONDUCTOR.md, LEDGER_PRATINIDHI.md, and
ekv_manifest.json FIRST. Do not re-litigate last night's rulings (EKV-R-1..R-13) without new
evidence; they stand.

PLAN OF RECORD: /Users/Dev/shad_overnight/EKAVAKYATA_EXECUTION_PLAN_v1_0.md
Gate: /Users/Dev/shad_overnight/ekv_gate.py
Repo: /Users/Dev/Vibe-Coding/Apps/Madhav. DB port 5433.
Model policy unchanged: sonnet builds, haiku sweeps, opus judges — never Fable.

WHY THIS SESSION EXISTS — the honest gap from last night, independently verified before this
kickoff was written:
  - CL-00 (27 regression controls) was authorized NOT-RUN all night (EKV-R-5/R-9/R-13). 21 real
    commits landed on main since T0 with the regression baseline never checked against them.
  - 10 of last night's LIVE-recorded lanes (A-07/08/11/12/13/15/16/17, B-02/B-03) have evidence
    paths cited in the manifest that point to files that do not exist on disk.
  - 6 lanes (A-07/08/12/13/16/17) have lease_ok=null — the isolation audit was never recorded.
  - The code for all of the above IS on main and deployed; this is a verification debt, not a
    rework debt. Do not re-derive or re-build — probe, record, close the loop.

SEQUENCE (do in order; do not skip ahead):

STEP 1 — CL-00 FULL RUN (first, before anything else — this is the only thing that can tell you
whether last night regressed anything):
  1. Merge origin/ekv/lead-dharma to main (D-01..D-08: 5 lints + ekv_controls.py + CI + tests,
     all previously BUILT, self-tests 5/5 PASS per Stream D's last report).
  2. Run: python3 platform/scripts/governance/ekv_controls.py --json (full battery, not --cheap).
  3. Record the real result in ekv_manifest.json's cl00_cheap_subset_last_run. If it fails on
     anything touched by last night's 21 commits: STOP, do not proceed to step 2, escalate to
     PRATINIDHI with the specific failing control.
  4. If PASS: this authorizes upgrading last night's wave disposition — post an addendum to
     LEDGER_CONDUCTOR.md noting CL-00 now PASSES, campaign remains CLOSED-PARTIAL for this
     session's own record (do not retroactively rewrite last night's terminal marker).

STEP 2 — EVIDENCE + LEASE BACKFILL for the 10 lanes above:
  - For each: run its actual exit_test probe (per its manifest entry's `exit_test` field) against
    the DEPLOYED production state (main tip, already live) — not a fresh build. Write the real
    JSON result to the cited evidence path. Do not write an evidence file for a probe you did not
    run.
  - For A-07/08/12/13/16/17: verify each lane's file set is genuinely within its Stream's declared
    lease (LEASES.json) before setting lease_ok=true. This is a real check, not a formality — if
    a file falls outside the declared lease, that's a finding for PRATINIDHI, not a silent pass.
  - Re-run: python3 /Users/Dev/shad_overnight/ekv_gate.py verify --wave 1
    Expect this to newly PASS (or newly and honestly fail on something specific) once evidence
    and lease_ok are real instead of missing.

STEP 3 — B-01 (ekv/b-01-dignity-oracle) REBASE:
  - Rebase onto current main. Two conflicts, per Stream E's EKV-B-01-DIRTY signal (last night,
    21:57Z UTC): ga_vargas_writer.py (incorporate both B-01's and B-02's changes — mechanical) and
    brahmagyan/__tests__/test_dignity_oracle.py (semantic: Moon at 10° Taurus — moolatrikona vs
    exalted). This second one is a real classical judgment call, not mechanical — resolve per
    B-01's own dignity oracle spec and the plan's standing rule: choose the option that DISCLOSES
    more, never the one that claims more (SP-2). If genuinely unresolvable from the spec alone,
    escalate to PRATINIDHI rather than guessing.
  - Force-push, re-queue PR#1296, confirm CI green, merge.

STEP 4 — A-09 TAP POINTER VALIDATION (SC-17/18/19, Boot-time):
  - This is the root cause every W1 lane's TAP-inheritance carve-out (EKV-R-12) depends on staying
    fixed. Fix the pointer registration issue on ekv/a-09-sara-kernel (or main directly if A-09 is
    already merged — confirm which). Re-run TAP CI on main. Once green, note in LEDGER_CONDUCTOR
    that the EKV-R-12 carve-out's root cause is now closed — future lanes no longer need it.

STEP 5 — WAVE 2/3: the 15 CLAIMED lanes not yet touched. Sequence per plan §5. Standard duties
apply: leases, heartbeats ≤20min, degrade order on cost/time pressure, never cut verification.

CLOSE (same discipline as last night): only after gate exit 0 (or honestly parked remainder) +
SENTINEL independent re-run + PRATINIDHI countersign does a terminal marker post. A partial with
honest state is success; a dressed-up completion is the one forbidden outcome — same as always.
