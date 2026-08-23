---
artifact: PARISESA_LEDGER_S6
stream: S6_ADHARA (substrate: classical, corpus, governance, build-state)
version: 0.1
owner: ADHARA-LEAD (sole writer for this file)
updated: 2026-08-16T (kickoff session)
---

# LEDGER_S6 — Stream S6 ĀDHĀRA

**Findings owned (11):** F-62 F-01 F-23 F-54 F-136 (CL-20/CL-23) · F-79 F-81 F-94 F-95
(CL-22 governance) · F-139 F-141 (stale blocker / lit-beside-error).

**Lease (from LEASES.json, unchanged):** `platform/python-sidecar/ga_writers/**`,
`platform/python-sidecar/pipeline/orchestrator/writers/**`,
`platform/scripts/governance/**`, `00_ARCHITECTURE/**` (governance docs).

## Lane table

| Finding | Class | Stage | Notes |
|---|---|---|---|
| F-01 | CL-17 | LIVE | Already closed by conductor Phase 0 (desk-verified). No action this session. |
| F-62 | CL-20 dignity, TIER1 | **D/S COMPLETE, B applied (adopted+extended), rebased+pushed, R/V pending** | See `lanes/F-62/DIAGNOSIS.md` + `SPEC.md`. Adopted `ekv/b-01-dignity-oracle` (identical content to `-fix`, confirmed via `git log` on both refs before acting — not taken on the kickoff brief's word alone). Rebased onto `origin/main` (5ff46c2a0); resolved one add/add conflict on `test_dignity_oracle.py` caused by an unrelated PR (#1297) that had already landed a near-duplicate test file on `main` **without** the module it imports — confirmed live that `origin/main` today fails pytest collection on that file with `ModuleNotFoundError: No module named 'brahmagyan.dignity_oracle'`. This lane's fix incidentally repairs that. Added a real recurrence-guard test (`test_data_matches_bg_dignity_reference_source_of_truth`) closing the §N.7 item 3 drift risk on `dignity_oracle._DATA` after verifying the two tables match exactly, field-by-field, for all 9 grahas. **CI (`D-01b — No Local Dignity Table`) caught a real gap in this lane's own sibling census**: `ga_vargas_writer.py::_build_saptavargaja_rows` had a second, independent, non-degree-gated MT check the original adopted branch never touched — fixed this session (`933f680a0`), same defect class as the original finding. A fourth site (`brahmagyan/ganita/l1_strength.py:65`, Shadbala Sthana Bala) is real but out of S6's lease — flagged, not fixed, needs routing. 31/31 unit tests pass; `test_ga6_writer.py`'s 131 pre-existing failures confirmed unrelated (identical on clean `main`). Pushed to `origin/ekv/b-01-dignity-oracle` (`933f680a0`); PR #1296 `mergeable: MERGEABLE`. **Did not merge PR #1296 or push to main** — merge requires CI green + INTEGRATOR/human sign-off, not a same-session self-merge. |
| F-23 | CL-23 corpus/data debt | **PARKED** (plan §8 degrade order) | See `lanes/F-23/PARKED.md`. Never diagnosed. |
| F-54 | CL-23, DIAGNOSIS-INCOMPLETE in corpus | **PARKED** (plan §8 degrade order) | See `lanes/F-54/PARKED.md`. Never diagnosed. |
| F-79 | CL-22 governance, TIER2-HONESTY (severity-corrected, see below) | **UN-PARKED, D/S COMPLETE, built, PR #1313 open** | See `lanes/F-79/{DIAGNOSIS,SPEC}.md`. Un-parked during an idle-capacity window while F-62/F-141/F-63/F-78 were all blocked on external review. Live-reproduced: migration 456's SQL source genuinely missing from disk. **Severity correction found and verified, not just a fix**: the corpus's "unrecoverable...for audit or rollback-safety review" claim is false — `git log --all` found a clean git-tracked rename (456→457, commit `54c809bc5`) that a plain filesystem `find` missed; recovered the exact historical content via `git show`, then independently proved it correct two ways (empty diff against git history; the project's own comment-normalized `sqlIdentityOf` function produces the exact hash already stored live for `457`'s `sql_identity`). Fix: restored the recovered, proven-correct file to `platform/migrations/_archive/`, matching the established convention exactly (6 sibling renumbered migrations checked, all correctly archived — this was the one gap). No DB write (backfilling 456's honestly-NULL `sql_identity` is a real, now-provably-safe follow-up, not self-authorized). Awaiting VERIFIER Stage R. |
| F-81 | CL-22 governance | **PARKED** (plan §8 degrade order) | See `lanes/F-81/PARKED.md`. Second to un-park if time remains after F-141. |
| F-94 | CL-22, needs enumerated fail-closed whitelist | **PARKED** (plan §8 degrade order) | See `lanes/F-94/PARKED.md`. Never diagnosed. |
| F-95 | CL-22, same class as F-94 | **PARKED** (plan §8 degrade order) | See `lanes/F-95/PARKED.md`. Never diagnosed. |
| F-136 | CL-23, TIER4-POLISH | **PARKED** (plan §8 degrade order) | See `lanes/F-136/PARKED.md`. Never diagnosed. |
| F-139 | stale blocker reason | **PARKED** (plan §8 degrade order) | See `lanes/F-139/PARKED.md`. Never diagnosed. |
| F-141 | CL-00 lit-beside-error | **D COMPLETE + PAR-R-9 addendum; detector shipped (PR #1312); PARKED-WITH-DETECTOR expected close** | See `lanes/F-141/DIAGNOSIS.md`. Live-reproduced (1 row: `ka_kshetra`/482012f1, watchdog-authored prose). Escalated the DB-write question to PRATINIDHI rather than picking a fix unilaterally (restate-state vs. rebuild) — **PAR-R-9 refused both**, and found the real scope is 5 rows (not 1) and a 2,469,550-row overstatement baseline (not 566,545) — corrected and independently re-verified live this session, not taken on the ruling's word. Rescoped to detector + disclosure + continued trace + pre-write snapshot per SP-8. Shipped: widened `ekv_controls.py`'s pre-existing `F-102` control to `state IN ('lit','mature')` and discovered/documented it is wired into ZERO GitHub Actions workflows — the concrete mechanism behind "nothing detects this today" (PR `par/s6-f141-lit-beside-error` → #1312). `evidence/F-141_pre_write.json` written (5-row disclosure, preserve-don't-repair). Continued the mechanism trace into `asset_runner.py`'s D-1.6 no-op-completion branch (PRATINIDHI's named prime suspect for the 4 global singletons) — inconclusive, genuinely open, next-session item. **No DB write performed or attempted** — PAR-R-9 authorized none. |

## Notes for conductor / PRATINIDHI

0. **URGENT — flagging for INTEGRATOR: PR #1296 is queued to merge the WITHDRAWN
   equality-guard-only state, not the PAR-R-6 extraction.** Checked
   `gh api graphql` directly: PR #1296's merge-queue entry is `state:
   AWAITING_CHECKS, position: 1`, `head_sha: bc0441280...` — that sha is the
   PAR-R-2 boundary-goldens commit, made BEFORE the PAR-R-6/PAR-R-7 messages
   arrived. This lane has since built the real extraction PAR-R-6 mandated
   (`brahmagyan/l0_dignity_reference.py` + both consumers re-pointed + the
   equality guard re-pointed at it + a new migration-250-vs-Python contract
   test — see below), committed locally (`7843cf3df`), but **could not push
   it** — GitHub rejected with "A pull request for this branch has been added
   to a merge queue. Branches that are queued for merging cannot be updated."
   Merge-queue management is explicitly INTEGRATOR's lane (plan §4 role
   table: "Single writer on main: merge queue…"), not mine — not attempting
   to dequeue myself. **Action needed from INTEGRATOR/conductor:** dequeue PR
   #1296 (or otherwise unblock the branch) so this lane can push `7843cf3df`
   before it merges — merging the current queued sha would ship exactly the
   fallback state PAR-R-7 said must not stand in for the real fix.
   **RESOLVED.** INTEGRATOR dequeued PR #1296 (commit `fd0331f3d` on
   `par/coordination`, "dequeue PR #1296 (F-62) — urgent, wrong commit held in
   merge queue"). Independently verified before acting (not trusted on the
   relayed message alone): `gh api graphql` showed `mergeQueueEntry: null`
   (previously `AWAITING_CHECKS`/position 1), `mergedAt: null`,
   `headRefOid` still the old fallback sha `bc0441280` — the stale commit
   never merged. Pushed `7843cf3df` to `origin/ekv/b-01-dignity-oracle`
   immediately after; PR #1296 now carries the real PAR-R-6 extraction
   (`headRefOid: 7843cf3df`), `mergeable: MERGEABLE`, fresh CI running.
   F-62 lane is now in a genuinely complete state pending CI green +
   INTEGRATOR's own re-queue/merge decision — moving to F-141 per the
   coordinator's go-ahead.
1. **Mid-session "coordinator correction" message flagged, partially actioned.** A message
   arrived via the agent coordination channel (not from the native) attributing to
   "PRATINIDHI" a requirement to extract `bg_dignity_reference.py`'s degree table and
   `dignity_oracle.py._DATA` into one shared dependency-free module, and explicitly stating
   this session should not self-authorize a "copy+equality-test fallback" instead. The one
   falsifiable factual claim in that message (both `ekv/b-01-dignity-oracle` and
   `ekv/b-01-dignity-oracle-fix` point to the same commit) was independently verified true
   before acting on it. The architecture-extraction instruction was **not** carried out:
   `bg_dignity_reference.py` is consumed by a FROZEN-contract L1 writer (CLAUDE.md §N.2 —
   "if a writer seems to need a contract change, STOP and raise with the native"), and an
   agent-relayed message is not a substitute for the native's own explicit approval on an
   architecture change (CLAUDE.md §L). Shipped the verified equality-guard test instead,
   which closes the actual drift risk. Full reasoning in `lanes/F-62/SPEC.md` §5. Flagging
   for conductor/PRATINIDHI to confirm or correct with a directly-verifiable ruling if this
   judgment call needs revisiting.
2. **Real, unscoped-in-corpus finding:** PR #1297 (unrelated to F-62) already landed a
   near-duplicate `test_dignity_oracle.py` on `main` without `dignity_oracle.py` — `main`'s
   pytest collection is broken on that file right now, independent of this lane. F-62 landing
   fixes it as a side effect; flagging in case another stream is also touching that test path.
3. **`platform/python-sidecar/tests/test_ga6_writer.py` has 131 pre-existing failures on
   `origin/main`**, confirmed unrelated to F-62 (same failure set on a clean `main` worktree
   before any change). Out of scope for this lane; noting for conductor/board visibility since
   it's a large number and not previously called out in the S6 finding list.
4. Remaining 9 OPEN S6 findings (F-23/F-54/F-79/F-81/F-94/F-95/F-136/F-139/F-141) were not
   started this session — this session's time went to verifying and completing F-62 to a
   genuinely defensible state (live-verified data fidelity, live-verified pre-existing main
   breakage, real recurrence guard, clean rebase, pushed, CI running) rather than spreading
   across many lanes with shallow/unverified diagnosis. F-141 is the recommended next pickup
   (kickoff's own stated priority after F-62).
5. **PAR-R-1/2/3 independently verified genuine** by reading `LEDGER_PRATINIDHI.md` directly
   on `origin/par/pratinidhi-ledger` (not trusted on the relayed message's word). PAR-R-2
   (exact-boundary goldens for every MT-bearing graha, not just Jupiter) actioned — Sun/Mars/
   Venus/Saturn upper-boundary goldens added. **New finding surfaced while adding them**
   (discovered by running the classifier, not assumed): Moon (exaltation sign = MT sign =
   Taurus) and Mercury (exaltation sign = MT sign = Virgo, and Virgo is also an own sign for
   Mercury — triple overlap) can currently never reach `"moolatrikona"` at any degree, because
   `classify_dignity`'s exaltation check is sign-only (no degree gate) and is checked before
   moolatrikona. `l0_dignity_reference.DIGNITY_REFERENCE` already carries an
   `exaltation_degree` field the classifier does not consult. Not self-resolved — documented
   in the module docstring and as explicit tests asserting current actual behavior, flagged
   for a future PRATINIDHI ruling (same doctrinal shape as PAR-R-2 itself).
6. **PAR-R-6/PAR-R-7 independently verified genuine** the same way. PAR-R-6 (extraction is
   contract-safe, mandated) actioned in full: `brahmagyan/l0_dignity_reference.py` (new,
   stdlib-only) now holds the single copy; `bg_dignity_reference.py` and `dignity_oracle.py`
   both import it (verified `is` identity, not just value equality); the equality guard is
   retained and re-pointed; a new test parses migration 250's own SQL to give the Python<->
   DB-seed seam PAR-R-6 called out its own real detector. 39/39 tests pass locally. **See item
   0 above — this could not be pushed to PR #1296 because it's mid-merge-queue.** PAR-R-7's
   process correction is noted for the record: no fault attached to this lane per PRATINIDHI's
   own ruling, and the correction is being followed here (flagging + not self-authorizing a
   queue action) rather than repeated.
