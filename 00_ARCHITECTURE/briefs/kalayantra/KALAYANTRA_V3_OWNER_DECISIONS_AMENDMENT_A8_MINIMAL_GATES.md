---
title: KĀLA-YANTRA v3 owner decisions — Amendment A8 (the minimal gate model; everything else is retired)
version: 1.0
status: CURRENT
date: 2026-10-17
amends: KALAYANTRA_RELAUNCH_PLAN_v2_7.md (§3–§10, §14–§17 gating, loops, qualification, receipts, pins), KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md (bundle verification, "Never" list), KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md (§3–§11 where they state gates), the fleet cards and COVERAGE matrices, the J-2a pack SUBMIT/FILL rules, executor_ops.json production flags, the tracker completion rules, Amendments A1–A7 where they are superseded below
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS. It is the operative gate list. A rule not listed in §3 is NOT binding on any job, lane or session, whatever document still states it, until it is recorded under A3 D-26 with its cost.
changelog:
  - 1.0 (2026-10-17): created on the owner direction of 2026-10-17 ~18:00Z: "This problem has been plaguing us despite my several requests. Thoroughly analyse the entire execution and the plan. Implementation velocity is the highest priority; governance and security reviews only the essential; testing only the essential. Fix it everywhere so this doesn't keep repeating." Based on four parallel audits (governing documents; fleet, tracker and executor code; fast-lane scripts and templates; 72 hours of job data).
---

# Amendment A8 — the minimal gate model

**Written for:** the cockpit session, the owner surrogate, every fleet job and lane, the executor's signer, and whoever next audits the campaign. §3 is the whole rulebook for gating. §4 lists what is retired, by name, so nobody re-derives it from an older text. §5–§6 are the concrete edits. §7 is how we know it worked.

## §1 · Why this keeps repeating

Seven amendments in three days each cut a visible symptom, and the ceremony grew back. The audits found the cause: the campaign runs under a **nine-document precedence stack** (plan v2.7, cockpit prompt, charter, velocity amendment, owner decisions, A1–A7, cards, packs) whose base documents were never edited because packets pin their hashes. Every job and every cockpit cycle re-reads the whole stack and resolves its contradictions by adding another check. The plan's retired machinery (bootstrap receipts, dispatcher loops, veto windows, claims and heartbeats, verifier boundary, qualification receipts, coverage matrices) is still marked authoritative, so agents keep rebuilding pieces of it under "(I) INTERPRETATION".

| Measured, 72 hours to 2026-10-17 23:40Z | Value |
|---|---|
| Agent jobs finished / agent-hours | 730 / 248 |
| Share of agent-hours that was ceremony (merge churn, pack re-identification, multi-lane acceptance, step receipts, re-rounds, premature pre-builds) | about 50% (58% in the last 24 h) |
| Gate conditions one code item passes from build to DONE today | 26 (27 with a migration) |
| Gate conditions the minimal safe model needs | 8 |
| Separate reviewer signatures one production write operation collects today | 3–4 (pre-acceptance, post-receipt verdict, step verdict, quiescence) |
| Hand-written agent briefs | 479 of 786 (61%); about 40–50 cockpit hours |
| Jobs for one valid scoped backup (five attempts across re-identification) | 20 pre-acceptance + 5 post + 2 quiescence |
| Pack versions of the J-2a request pack in 36 hours | 7 (v3.2 → v3.7.2); 98 identities re-minted in 24 h |
| Tracker `done` movement in the last 24 h, against 47 PRs merged | 80 → 83 |

## §2 · What is NOT touched

Root `CLAUDE.md` §I and §N. The owner's kept rules (A1): never read, print or copy a credential; never `rm -rf` a working copy; never fabricate a review record, receipt or verdict; the global HOLD; no L0–L2 asset in any Kāla run; a FROZEN-contract change is a STOP for the native. The native's personal data: profiles are never exported; chart rows live only in the governed export folder or an isolated throwaway database, never in git, PRs, logs or reports.

## §3 · The gate list (the whole rulebook)

**Per code change**
1. One branch, one PR. The launcher commits, pushes, opens the PR, merges `main` in once, runs the local pre-flight, and arms auto-merge when the review is ACCEPTED and CI is green (A3 D-24, A7 D-48). Agents never run git writes or `gh`.
2. **One independent review**, reviewer ≠ author, one round, under the owner's testing standard (D-OWNER-TESTS-20261016): the reviewer enumerates the distinct claims, each has one source-cited oracle, each oracle is shown to fail on one planted reversion. A second round only for a BLOCKING finding. Non-blocking findings are posted on the PR; they never create a child item or a second job.
3. **The verdict binds to the diff**, not the head commit: `git patch-id --stable` of `base..head`. A merge from `main` that leaves the patch-id unchanged and merges cleanly inherits the verdict automatically. A rebase with the same patch-id inherits too.
4. **Required CI green** at the PR head: the 16 required checks including Kāla DB Tests and the Earned-Signal Gate (A3 D-22). Markdown and plan-model PRs merge on CI alone (A3 D-25.1). Generated outputs are produced only by CI from `main` (A5 D-33).
5. **DONE = merged + accepted + contained in a successful deploy of `main`** (A7 D-46). Dependencies on other code items close when those are merged and deployed; chain activation is `activation_pending: <gate>`, shown beside DONE, never a step receipt. Operation items are done by their executor receipt.
6. Six jobs per item; the seventh parks the item with a one-line note (A2 D-17.5, without the ruling ceremony).

**Per migration**
7. Additive; number from the allocator; applied in the job's guarded local fixture; protected-class files go through the automated window after merge (A4 D-31) with the GitHub environment approval recorded via API under the surrogate's decision id (A1 D-10); applied-ness is proven by the `verify-migrations-deployed` CI check plus a mechanical `migration_readback`. No post-deploy reviewer job.

**Per production data operation (the executor is the only credential holder)**
8. Read-only kinds need no reviewer and no fence; they are accepted mechanically on COMPLETED (A7 D-44.1). `*_dryrun` kinds are read-only with a credential: rollback proof in the receipt, no acceptance, no fence.
9. Writing kinds (backup, restore proof, teardown, dispatch, protected windows): **one** independent signer (V1) on a fixed checklist, bound to `{operation_id, kind, item_id, args, reviewed_commit, chart_id}` and nothing else, valid until the request bytes it binds change (A7 D-44.2, D-45). No post-receipt verdict, no step verdict, no quiescence review; post-acceptance and quiescence are executor-written mechanical checks.
10. A scoped backup with restore proof before the first data-changing operation of a window, valid until a scope table's content hash changes (measured at dispatch), not on a clock.
11. One coordination lease per production window, taken for the whole window, auto-renewed, checked at execute. The fence is set only for remote-asynchronous kinds (dispatch, century, verification job) and released by the executor's own completion read (`cloudrun_job_readback` SUCCEEDED/FAILED). Synchronous kinds release on receipt.
12. Identities are minted per attempt automatically; a FAILED attempt never needs a preparation job; a lapsed label never needs a new pack version.
13. D-13 order and stop-at-first-failure; D-14 automatic stops (red `main` → HOLD_MERGES; a production failure → HOLD). The small test closes with one clean run (A7 D-49).

**Decisions and records**
14. The surrogate decides everything except the four hard stops, as conditional approvals (A4 D-29); one `ky decide … --delegated --detail` line is the record; the owner may veto after the fact. A new restriction is a recorded decision with its cost or it is not binding (A3 D-26).
15. One owner report a day plus incidents (A5 D-38). One SESSION_OPEN/CLOSE pair with SESSION_LOG and CURRENT_STATE at campaign open and close (`CLAUDE.md` §G/§H). One red-team at macro-phase close.

That is the whole list. Everything below is retired.

## §4 · Retired, by name

Retired means: not binding, not to be rebuilt, not to be cited as authority. Code that enforces an item here is changed under §5.

- **Plan v2.7 bundle verification and activation records** (PLAN §1, COCK:21–58): byte-identical bundle checks, successor chains, `entrypoints` maps. The plan lives on `main` and is edited in place.
- **Hash pins of documents in packets and packs** (PLAN:511–529; `kypacket.py` working-tree sha checks, size cap, excerpt and KU checks; pack `rebind_pins.py`): pin by path, section and commit only; REPIN jobs are abolished.
- **Multi-lane acceptance** (V2–V4 pre-acceptance; per-receipt post-acceptance by a lane; quiescence review jobs; fence release by a lane): replaced by §3.8–§3.11.
- **Short expiry clocks** (3-hour acceptance age cap, 4-hour backup clock, `expires_at` inside the request digest, "lease change voids Phase A", fill/queue minimum margins): replaced by §3.9–§3.12.
- **Phase A re-runs and the eleven 14-* reads with acceptances**: one pre-dispatch read and one post-teardown absence read, mechanically accepted.
- **Signer attestation of deployed image/config/corpus and the M12 reviewer gate**: `cloudrun_job_readback` and the dispatch script compare and refuse; no reviewer rows.
- **J-1a lane qualification ritual** (six lane receipts bound to J-1a): the kinds' CI suites and the first production dry run suffice.
- **Step receipts, step-review jobs and strict ordered completion for code items** (176 plan-model step detectors on code items; `ky step` for code; `deps_open_strict` as a completion gate): A7 D-46.
- **Exact-head verdicts, the descent-based inheritance predicate and verifier-boundary triple checks** (`not_descendant`, snapshot hash, tracked-hash set, `kyboundary.sh`): §3.3 and a clean `git status`.
- **Packet-exit "Astra" reviews with NEW-ITEM fan-out** for every K family: only the publication gate (K9-4a) and the flip review (V-J6) remain, by the normal reviewer.
- **The post-deploy reviewer verdict for data-writing items**: §3.7.
- **Retired fleet machinery still marked authoritative**: dispatcher lane and `kygate.sh` per-tick gates, launch qualification receipts, claims/renewals/heartbeats, veto window and PENDING_VETO, action records for model jobs, controller-owned verdict publication, enforced verifier boundary, bootstrap/final manifests and receipts, B-3/B-4/B-5 rehearsal/coverage/backfill gates, COVERAGE matrices, cards restating `CLAUDE.md`, circuit breakers, measurement baselines beyond A2 D-21.
- **Triple decision ledgers and notification proofs**: one record.
- **The cockpit "Never" list** (COCK:131–149) where it contradicts A1 D-10 and A3 D-24.3: the cockpit merges, launches and records; agents never run git or `gh`.
- **Separate rehearsal jobs that duplicate an executor dry-run kind**, and pre-builds or rehearsals more than two phases ahead (A7 D-47).
- **Child-item fan-out of non-blocking findings, "confirm" jobs after fixes, and re-review of a pure main merge**.
- **Hourly reports** and the `HOURLY REPORT DUE` watch hook.

## §5 · Edits applied or ordered

**Code (PRs, one review each):**
- `executor.py`: decouple refresh refusal from admission (a merged executor change plus a queued request must not stop all admissions); `request_digest` excludes `acceptance_receipt` and `expires_at`; drop the 3-hour `APPROVAL_MAX_AGE_S`; drop `required_rows` and `restore_verified` as preconditions except `backup_taken` for `*_teardown`; `*_dryrun` kinds lose `production: true` while keeping the rollback-proof receipt check; fence set only for remote-asynchronous kinds and auto-released on COMPLETED for synchronous kinds; drop the `lane_receipts` qualification. (The conductor's `a7-mech-accept` adds the executor-written post-acceptance and quiescence.)
- `kyverdicts.py`: inheritance by `git patch-id --stable` equality plus a clean `merge-tree`; `not_descendant` removed; publish checks reduce to result-valid, head == reviewed head, author ≠ reviewer, `git status --porcelain` empty.
- `kypacket.py`: pin by revision blob only; no working-tree hash; no size cap; no excerpt or KU checks; `packet_sha256` dropped.
- Tracker (`completion.py`, `state.py`, `cli.py`): A7 D-46 `activation_pending`; `deps_open_strict` not a completion gate for code items; no `ky step` for code items; verify-on-busy waits instead of refusing; the post_deploy verdict rule replaced by a mechanical `migration_readback` detector. (The conductor's `a7-completion` carries this.)
- Plan model: the 176 code-item `step_evidence` entries removed; operation steps keep theirs, fed from executor receipts by script.
- Plan and prompt: `KALAYANTRA_RELAUNCH_PLAN_v3_0.md` folds A1–A8 into one operative text, marks retired sections HISTORICAL, and carries §3 above as its gate chapter; `KALAYANTRA_V3_COCKPIT_PROMPT_v3_0.md` is the owner's kept rules plus §3; `D-OWNER-ENGINE-20261017` is recorded in the decisions file.

**Fast lane (cockpit-owned scripts; ordered to the cockpit with the audit's edit list):** `mk_task.py` for the six recurring brief families; one landing path (`cx_post.sh` → `mergeup.sh` → preflight → arm; `landfix.sh`, `after_merge.sh`, `lift_freeze.sh`, `prep_postfreeze.sh`, `requeue_dropped.sh`, `jump_queue.sh` deleted); `mergeup.sh` with prefix normalisation, auto-launched conflict job, per-PR counter; 3-way resolver for `plan_model.json`; `review_wave.sh` without checks (3) and (5) and without child fan-out; no step reviews for code items; `prebuild_items.sh` two-phase limit; pack: one signer request, read-only ops mechanically accepted, `MAIN` from `SOURCE_PINS.json` at runtime, per-attempt identities, `--backup-label auto`, `expires_at` out of the digest, R1 deleted, one `window.sh`, `lease_row.py take` for the whole window with auto-renew, `PACK/env.sh` written by the pack; `watch.sh` without the hourly and steps hooks; `autolaunch.sh` logging state changes only.

**Header:** `COMMON_HEADER.md` names this amendment and the kept rules as the authority order; the testing standard appears once; Codex branches removed.

## §6 · How a job reads the rules from now on

Authority order, in full: root `CLAUDE.md` §I/§N → the owner's kept rules (§2) → this amendment §3 → the packet's own contract and tests. Nothing else is consulted for gating. Where an older text says more, it is HISTORICAL.

## §7 · Success (72 hours from merge)

| Measure | Target |
|---|---|
| Ceremony share of agent-hours (merge churn, re-identification, multi-lane acceptance, step receipts, re-rounds) | under 15% (from ~50%) |
| Reviewer signatures per production write operation | 1 |
| Reviewer jobs per read-only production operation | 0 |
| Pack versions per production window | 1 |
| Gate conditions from build to DONE for a code item | 8 |
| Hand-written briefs | under 20% of jobs |
| Items DONE (implemented) | reflects merged + accepted + deployed within one deploy cycle |
| Repeat of any §4 item in a job brief, template or script | 0 (a repeat is a D-26 breach) |
