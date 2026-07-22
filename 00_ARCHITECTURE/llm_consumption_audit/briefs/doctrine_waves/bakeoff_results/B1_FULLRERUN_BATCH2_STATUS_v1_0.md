---
artifact: B1_FULLRERUN_BATCH2_STATUS
type: BATCH STATUS / BLOCKER REPORT (not a scoring result)
version: 1.0
status: BLOCKED — DR-19 pre-check failed; dispatch premise (a committed BATCH-1 run manifest)
  does not exist on this branch, on origin, or anywhere in repo history. No contender scored, no
  CRPS/hit-rate/DR-17 grade computed, no LEL event read, no negative controls drawn.
authored_by: Claude Code (Sonnet 5), D-4b B-1 chunked re-run dispatch, BATCH 2/3, 2026-07-22
branch: wave/D-4b/B1-full-rerun (worktree .claude/worktrees/wave-D-4b-B1-full-rerun)
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
---

# B-1 full re-run — BATCH 2/3 dispatch — status report

**This is not a scoring report.** Per the dispatch's own non-negotiable ground rules (CLAUDE.md
B.10, DR-16, DR-19) — "never fabricate a numerical chart value, score, count, or DB row" and "if
blocked, say so plainly; never claim unverified success" — this session performed the required
DR-19 pre-check before any scoring work and found the dispatch's premise does not hold. No
contenders were scored. No file matching the expected batch-artifact naming was written.

## 1. DR-19 check (performed first, per instruction)

- `git fetch origin main` run; branch confirmed as `wave/D-4b/B1-full-rerun` (not the initial
  environment banner's `impl/wave-5` — matches the precedent B-1 dispatch's own noted banner/live
  mismatch, resolved the same way: trust live `git`, not the banner).
- `git pull origin wave/D-4b/B1-full-rerun` → **`fatal: couldn't find remote ref
  wave/D-4b/B1-full-rerun`**. This branch has never been pushed to `origin`.
- Local branch HEAD (`5d8d16ba`) is byte-identical to `origin/main` HEAD — `git log
  main..HEAD` returns zero commits. The branch carries no unique history whatsoever.
- `CLAUDECODE_BRIEF.md` (root): `status: ACTIVE` — governs, points to `CONDUCTOR_PROTOCOL.md` +
  current wave brief.
- `BRIEF_D4B.md`: `status: OPENED` — campaign is live and this branch's wave (D-4b) is the
  active one. **No branch/campaign mismatch on that axis.**
- However, the dispatch's specific premise — "Read the committed run manifest
  (`bakeoff_results/B1_RUN_MANIFEST_v1_0.json`) and its hash... consume it exactly as committed"
  and "this is BATCH 2/3" (implying BATCH 1 already ran and committed a manifest + partial
  results) — is **not supported by any live evidence**:
  - `find . -iname "*B1_RUN_MANIFEST*"` across the whole worktree: zero hits.
  - `git log --all --diff-filter=A -- "**/B1_RUN_MANIFEST*"`: zero hits, across every branch in
    the repository, not just this one.
  - `bakeoff_results/` on this branch contains exactly the files that predate this dispatch:
    `B1_BAKEOFF_STATUS_v1_0.md`, `B1_NARROWED_STATUS_v1_0.md`,
    `B1_NARROWED_TRAIN_EVENTSET_v1_0.json` (31 TRAIN events, not the full 56), `B1_NARROWED_TRAIN_PER_EVENT_v1_0.json`,
    `B1_NARROWED_TRAIN_SUMMARY_v1_0.json`, `B1_NARROWED_TRAIN_RUNLOG_v1_0.txt`, and
    `b1_driver_v1_0.ts`. None of these is a run manifest for a chunked full-56-event re-run, and
    `b1_driver_v1_0.ts`'s own header explicitly self-describes as "Ad-hoc driver script for this
    dispatch — NOT a committed harness artifact" (from the prior, superseded NARROWED run) — not
    the "batch-runner harness from step 1" the dispatch refers to.
  - The authoritative live campaign ledger, `STATE_D4B.md` (most recent version,
    `updated_at: 2026-07-22T13:23:00Z`, on `main`), states for this exact lane in its own words:
    > `{lane: "B-1 full re-run", branch: wave/D-4b/B1-full-rerun, status: not_started_no_pr,
    > result: "NO PR EXISTS ... Local worktree carries only UNCOMMITTED WIP: a new
    > dr17_grading.ts implementation + test file... No scoring run, no results artifact, no
    > preregistration-packet bump. THIS IS THE WAVE'S EXACT BLOCKER THIS PASS."}`
  - The one piece of real WIP that *was* salvaged from a prior crashed attempt on this branch —
    `dr17_grading.ts` (23/23 tests, `tsc --noEmit` clean) — landed on `main` via PR #704
    (`0c17e927`), and that commit's own message says explicitly: "Not yet wired into
    `b1_driver_v1_0.ts` or exercised end-to-end against real chart data — that happens in the
    next B-1 re-run attempt." Confirmed still true: `grep -n "dr17_grading"
    b1_driver_v1_0.ts` returns zero matches — the module is not imported anywhere yet.

**Conclusion: there is no BATCH 1. No batch-runner harness capable of consuming a manifest and
scoring a chunk of the 56-event set has been built or committed. No run manifest, hash, or prior
batch commit exists to pull, read, or consume.** Proceeding to "score PERMISSION systems
naisargika/mudda/kalachakra/narayana/sade_sati against the manifest's full 56-event set... N=1000
mirrored shuffled-birth controls per the manifest" would require either (a) inventing a manifest
that was never ratified/committed, or (b) inventing scores/CRPS/control results with no real
harness run behind them. Both are direct B.10 violations of exactly the kind the precedent B-1
dispatch (`B1_BAKEOFF_STATUS_v1_0.md`) already identified and refused once on this same lane.

## 2. What this session did NOT do (explicit, per "never claim unverified success")

- Did not read, hash, or consume any `B1_RUN_MANIFEST_v1_0.json` — it does not exist.
- Did not invoke any batch-runner harness — none exists; only the superseded ad-hoc
  `b1_driver_v1_0.ts` (NARROWED, 14-contender, 31 TRAIN-event, pre-F1/F2, already-superseded)
  is present.
- Did not import or exercise `dr17_grading.ts` against real data — confirmed unwired.
- Did not score `naisargika`, `mudda`, `kalachakra`, `narayana`, or `sade_sati` against any event
  set, full or partial.
- Did not draw N=1000 (or any N) mirrored shuffled-birth controls.
- Did not compute any CRPS value, positive or negative — so the required F-2 zero-negative-CRPS
  verification could not be performed this batch (there is no output to check). This is reported
  honestly as "not run," not conflated with "F-2 verified clean."
- Did not write any `*_batch2_*` or contender-scored intermediate artifact — writing one would
  have no real computation behind it.

## 3. What IS confirmed true and reusable for whoever runs BATCH 1 first

- F-1 (PR #699) and F-2 (PR #697) are merged on `main` — independently re-confirmed present in
  this branch's `git log` (both commits are ancestors of `5d8d16ba`).
- `dr17_grading.ts` (PR #704, `0c17e927`) is merged on `main` and present on this branch at
  `platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/dr17_grading.ts` — real, tested
  (23/23 per its own commit message), but **not yet wired into any driver script**.
- The 56-event full corpus is a real, committed spec:
  `D4B_PREREGISTRATION_PACKET_v1_0.md` v1.2 (FROZEN, committed 2026-07-21), §0 corrects the
  event count to 56 against the live LEL corpus (`total_events_logged: 57`, one non-dated event
  excluded from the scored set).
- The five PERMISSION contenders named in this dispatch (naisargika, mudda, kalachakra,
  narayana, sade_sati) are plausible members of the existing 12-PERMISSION-system roster
  referenced by the prior NARROWED run and the `wave/D-4b/permission-bridge` lane (PR #693) —
  not independently re-verified against `roster.ts` this session, since no scoring call was
  reached.

## 4. Recommended next step (not performed here — outside this batch's authority)

Per `STATE_D4B.md`'s own framing, what's actually missing before any chunked batch dispatch can
run is: (1) a real batch-runner harness that can accept a chunk assignment and a manifest hash and
score against it idempotently, (2) `dr17_grading.ts` wired into that harness, and (3) a
`B1_RUN_MANIFEST_v1_0.json` actually authored, hash-committed, and pushed to
`wave/D-4b/B1-full-rerun` as the BATCH 1 step. None of that is BATCH 2/3 scope, and this session
did not attempt it — inventing a manifest to unblock itself would be exactly the fabrication this
dispatch's own ground rules forbid.

**This batch's status: BLOCKED, reported honestly, nothing fabricated, no commit of fabricated
scores. Stopping here per instruction.**
