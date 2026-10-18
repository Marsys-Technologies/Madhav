---
title: KĀLA-YANTRA v3 owner decisions — Amendment A7 (essential governance only; implemented is the headline)
version: 1.0
status: CURRENT
date: 2026-10-17
amends: Amendment A1 (D-13 production-operation form), Amendment A2 (D-21 reporting), Amendment A4 (D-38 cadence), Amendment A6 (D-40 pre-build scope, D-41 rehearsals), surrogate rulings SR-A4-01 (strict ordered completion) and SR-J2A-LEASE/SUBMIT rules (acceptance validity), the executor V1–V4 pre-acceptance procedure, the tracker's completion definition for code items
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS. Amended files stay byte-identical, as A1–A6 did.
changelog:
  - 1.0 (2026-10-17): created on the owner direction of 2026-10-17 ~17:30Z: "Are we overkilling ourselves with additional governance, testing, verification and security? Only essential governance, testing and security. Cut out the extraneous ones. Drive implementation velocity towards closure."
---

# Amendment A7 — essential only

**Written for:** the cockpit session, the owner surrogate, the executor's verifier lanes and every fleet job.

## §1 · What the last 24 hours measured (16 Oct 17:30Z → 17 Oct 17:30Z)

| Where agent time went | Jobs | Hours | Share |
|---|---|---|---|
| Merge, CI and pack repair (re-merges, re-pins, relabels) | 29 | 9 | 30% |
| Production-operation reviews (V1–V4, post-acceptance, quiescence) for ~15 small-test requests | 95 | 9 | 28% |
| PR reviews, step receipts, oracle hardening | 44 | 5 | 16% |
| Builds | 23 | 4 | 13% |
| Small-test chain work itself | 17 | 4 | 12% |
| Rehearsals | 2 | 0 | 1% |

47 PRs merged; tracker `done` moved 80 → 83; `built_waiting_on_gate` 35; total 264. Fifty-eight percent of agent time went to ceremony around merges and around one small production test. The ceremony did catch real defects (BG-01, 1394, #3688, the restore base, 1235) and those classes of check stay. The multiplicity around them does not.

## §2 · D-44 — one signer for production operations; none for reads

1. **Read-only readbacks** (`readback_sql`, `migration_readback`, `cloudrun_job_readback`, census and absence reads) need **no reviewer**. The executor's read-only enforcement is the control. They are accepted mechanically on completion.
2. **Writing operations** (backup, restore proof, teardown, dispatch, protected windows) need **one** independent signer (V1) working a fixed checklist, not four reviewers. V2–V4 are retired.
3. **Post-acceptance and quiescence** are executor-written mechanical checks (row counts, session list, fence state), not review jobs.
4. Checklist rows that cannot be measured are stated as gaps, as before; a gap that touches data safety blocks, anything else is recorded.

## §3 · D-45 — acceptances persist

Phase A readbacks, dry-run acceptances, pack identities and signer acceptances stay valid across lease renewals and across `main` commits that do not change the operation's script, SQL or arguments. Only the changed request is re-run. A pack is re-pinned only when one of its own scripts changed. The "lease change voids Phase A" rule is withdrawn.

## §4 · D-46 — implemented is the headline; activated is tracked beside it

1. A code or artifact item is **DONE (implemented)** when its code is merged, accepted under criterion v2, and contained in a successful deployment of `main`. Its code-verifiable steps are covered by that acceptance; **separate step-receipt agent jobs for code items are abolished.** Operation items keep their receipts: the receipt is the operation.
2. **Strict ordered completion (SR-A4-01) is retired for code items.** An item whose only open dependency is another item or a chain gate is DONE and carries `activation_pending: <gate>`; the tracker shows **implemented / total** as the headline and **activated / total** beside it. The campaign closes when both are complete.
3. Decision items (D-*) and verdict items (V-*) are unchanged.

## §5 · D-47 — build and rehearse two phases ahead, not twelve

Pre-builds (A6 D-40) and rehearsals (A6 D-41) run only for the next two chain phases and for open Wave 2 items. Phases further out are built when they come within two phases. Already-merged pre-builds stay.

## §6 · D-48 — one merge-up per held change

A held PR is merged with `main` once, when it enters the live set, through the preflight; children ride their parents. Repeated re-merge, re-pin and relabel cycles stop. Target: merge/CI repair under 10% of agent time.

## §7 · D-49 — the small test closes with one clean run

Run 2 (one clean run after the fixed verifier), its teardown and absence readback, and the J-2d-a55i receipt complete the small test. Then J-3c. No further small-test ceremony.

## §8 · D-50 — reporting

Three reports a day to the owner's analysis session (06:00Z, 12:00Z, 18:00Z) plus incidents; one a day to the owner. The tracker logs closures continuously.

## §9 · What stays, because it caught real defects

Criterion v2 reviews, one round; the required checks on `main` including the Earned-Signal Gate; honest nulls (N.7.6); the executor's read-only path for production data; one lease per production window; a scoped, proven backup before any data-changing operation; the owner's kept rules (credentials, no `rm -rf`, no fabricated records, the global HOLD, no L0–L2 asset in a Kāla run).
