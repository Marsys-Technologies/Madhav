---
artifact: CLOSEOUT_TRACKER_AND_COLLISION_v1_0
canonical_id: PARIPRASHNA_CLOSEOUT_TRACKER_AND_COLLISION
version: 1.0
status: CURRENT
authored_by: Claude Code session PARIPRASHNA-CLOSEOUT-2026-08-19
date: 2026-08-19/20
purpose: >
  Close-out record for the four-item PARIPRASHNA-CLOSEOUT brief: land PR #1355 and
  make installed==merged (item 1), wire tracker-health-check into the conductor
  contract (item 2), reconcile the lane-count discrepancy (item 3), and preserve
  SAMPŪRTI's stranded local-main commits without re-landing them (item 4).
---

# PARIPRAŚNA-CLOSEOUT — Tracker Land + Cross-Campaign Collision Cleanup

## Item 1 — Land #1355, make installed == merged

**1a. Provenance pill split.** `code_provenance`'s binary `is_current` flag
conflated "unmerged, ahead of main" with "genuinely behind main" — both read
`is_current: false`, both rendered amber "STALE CODE". That amber is exactly
the state this observatory was deployed under for most of this session's work
(code running from an unmerged branch, live-verifying T4 before merge) —
training a reader to discount an amber that, when it means BEHIND or
DIVERGED, is real. `classify_code_provenance()` (`_common.py`, pure) now
returns one of four states from two booleans (`is_ancestor_of_main`,
`contains_latest_tracker_commit`):

| state | is_ancestor_of_main | contains_latest | amber? |
|---|---|---|---|
| CURRENT | true | true | no |
| AHEAD | false | true | no |
| BEHIND | true | false | yes (names commit count) |
| DIVERGED | false | false | yes |

Four selftests, one per state, each independently confirmed capable of
failing (neutered the classifier to always return `CURRENT`; 3 of 4 tests
correctly caught it — the CURRENT test trivially still passed, which is
expected and not a gap, since the other three prove the detector real).

**1b. Lease + merge.** Lease announced on `origin/campaign-coordination`
after confirming the conductor's P1 FOUNDATION merge (#1356, 4 real
migrations) was clear — checked its state before opening a window rather than
assuming, and it was still `OPEN`/in-queue at the time this session started
work, so items 1a/2a/2b/2c/3 were built and committed first (all disjoint
from `platform/**`) while waiting. #1356 merged at `2026-08-19T23:10:03Z`;
this session's branch was rebased onto the new `origin/main` tip
(`d653236c2`) before requesting its own window.

**CI caught a real governance-drift bug this session introduced**, and it was
fixed, not waived: editing `KICKOFF_PROMPT_SWARM_CONDUCTOR_v2_0.md`,
`PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md`, and
`PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` (items 2b/2c/3) without
rotating their declared fingerprint in `CAPABILITY_MANIFEST.json` failed
`drift_detector`'s CI gate (exit=2, 3 HIGH `fingerprint_mismatch` findings) —
correctly, per its own design. Fixed by rotating all three fingerprints to
their real sha256 (independently recomputed, matched the gate's own
"observed=" evidence) and adding `last_verified_session`/`last_verified_on`.
Re-ran locally: exit 2 → 3 (216 pre-existing MEDIUM/LOW findings remain,
unrelated to this branch, within CI's accepted range — the gate script
treats 0 and 3 as passing, 1/2 as failing).

*Self-correction recorded for completeness:* while cleaning up a local adhoc
drift-report scratch file with `rm -rf 00_ARCHITECTURE/drift_reports/`, this
command deleted the entire tracked historical directory (166 committed
files going back to April), not just the 2 new scratch files. Caught
immediately via `git status`, restored via `git checkout --
00_ARCHITECTURE/drift_reports/` before anything was committed or pushed —
verified restored (166 files back) and confirmed no tracked file was lost.
The two scratch files from a subsequent, final verification run were then
removed by exact filename, not a directory-wide `rm -rf`.

**1c. Reinstall + verify.** PR #1355 merged as `a73b6af9f` (squash, per the
merge queue's own strategy) at `2026-08-19T23:34:43Z`. Reinstalled production
via `install.sh --install-from-ref origin/main`. Verified, each item its own
independent check (not inferred from the install command's exit code):

- **Jobs loaded:** `launchctl list | grep pariprashna` — all three present,
  fresh PIDs (trackerd 17220, serve 17227).
- **Heartbeat fresh:** waited specifically for a heartbeat whose `pid` field
  matched the newly-bootstrapped trackerd (17220), not just any heartbeat
  under the age threshold — the first read after reinstall was stale
  carryover from the pre-reinstall process (pid 23035) and would have been a
  false pass if taken at face value. Genuine fresh heartbeat: `cycle: 1`,
  age 8.4s.
- **Selftests:** ran `trackerd.py --selftest` directly against the deployed
  snapshot at `~/.pariprashna-tracker-code/` (not this session's worktree) —
  20/20 pass.
- **LAN:** `curl` against the token-gated local URL — HTTP 200.
- **Mirror fetch:** `ref_freshness.last_fetch_ok: true`,
  `consecutive_failures: 0`, fetched at `23:36:37Z`.
- **Cron (T4) present:** `crontab -l` shows the `*/5 * * * *` entry pointing
  at the new snapshot's `tracker-cron-watchdog`.
- **Provenance pill:** `code_state: "CURRENT"`, `code_stale: false`,
  `code_sha: a73b6af9f70d8cb987b73ee516c4b614abe9f225` —
  **exactly `origin/main`'s tip**, confirmed by direct string comparison, not
  inference.

## Item 2 — Wire tracker-health-check into the conductor contract

**2a.** `tracker-health-check` previously checked heartbeat age only. Now
checks all five conditions the dashboard's own trustworthiness depends on:
jobs loaded (`launchctl list`, no lock acquired — this script never sources
`_tracker_lock.sh`, since a conductor calling it at every lane transition
must never wait behind `install.sh`/`tracker-stop`/`tracker-start`), heartbeat
fresh (<180s), selftest passing (as of its last run), refs fresh (mirror
fetched within 180s), no unacknowledged blind window. Exit 0 only if all five
hold; exit 1 with a one-line diagnosis naming which failed. Measured 0.6s
against real production (well under the "under a second" requirement).
Selftested: all five failure conditions triggered independently plus the
all-healthy case, asserting the lock directory is never created and total
runtime stays under 1s; observed failing first by disabling the
jobs-unloaded check specifically and confirming that scenario silently
reported healthy.

**2b.** DD-11 added to `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` §2's
existing Delegated Decision register (not a new register, per the brief):
the conductor calls `tracker-health-check` at every lane transition; a
non-zero exit is a HALT condition, same shape as every other DD-5-style halt
in that same register (halt at the next lane boundary, pin rollback, write
resume state, restore the observatory, report).

**2c.** Explicit note added immediately after the DD-11 row: the rule takes
effect at the next phase boundary (P1 close), not mid-phase. The P1 conductor
was mid-phase as this was written (confirmed live — PR #1356, P1 FOUNDATION,
was in its own merge window at the same time this session opened); inserting
a new mandatory per-lane-transition call into a running phase would risk
exactly the kind of unplanned interruption DD-11 exists to prevent. P1
finishes under the rules it started under; P2 opens under DD-11.

**Observation, not acted on:** `KICKOFF_PROMPT_SWARM_CONDUCTOR_v2_0.md`
already said "DD-1..DD-11" (twice) *before* this session added the actual
DD-11 row — i.e. it already anticipated an eleventh decision existing. The
content added here (the tracker-health-check halt rule) is exactly what item
2b specified, and the number lines up. Flagging the pre-existing reference
for the record rather than treating the alignment as either a problem to fix
or a coincidence to silently absorb.

## Item 3 — Reconcile the lane count

Renumbered nothing, per the brief. Added a note to
`PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md` (right after its "Sizing
convention" paragraph) and a one-line pointer to
`KICKOFF_PROMPT_SWARM_CONDUCTOR_v2_0.md` (next to its existing citation of
the roadmap): lane decomposition expanded to 53 during P0, tracked live in
`tracker/PLAN.yaml` (`PLAN.yaml`'s own `note_on_lane_count` field already
recorded this fact — this item makes it discoverable from the two documents
a reader actually reaches for). Division of authority: `PLAN.yaml` is
normative for lane count, identity, and dependency edges; the roadmap is
normative for intent and PPR mapping.

## Item 4 — Stranded local main (preserved, not re-landed)

Full account posted to `origin/campaign-coordination` (§6 LOG,
`~23:10Z` entry, commit `dd313b622`) — not duplicated verbatim here; summary:

- **4a.** Confirmed via `git worktree list` (257 worktrees checked) that no
  worktree had `main` checked out, before touching anything.
- **4b.** Confirmed the five-commit divergence (`origin/main..main`) and
  re-verified per-commit content via diffstat + targeted diffs, rather than
  trusting the brief's numbers as given. **Refined the brief's "three commits
  carry unique content" claim**: `993522c00` (a test file) is confirmed
  byte-identical to an already-merged commit on `origin/main` (`1d6f3ad5a`,
  PR #1286) — a genuine duplicate, matching the brief. But `2139b3015` (a
  2-line FIELD-INTEGRATED marker) is **not** a clean duplicate the way
  `993522c00` is — its exact bytes are not verbatim anywhere on
  `origin/main` or `origin/campaign-coordination` — even though this same
  coordination file's own log (line 2273 at the time of reading) documents
  that its *substance* was already superseded by a corrected re-post
  ("prior commit 2139b3015 went to local main only, never pushed"). Net: 4 of
  5 commits carry bytes not verbatim on `origin/main`, not 3 — but one of
  those four is already substantively redundant. This did not change the
  preservation mechanism (branching captures all five bytes-identical
  regardless of this classification), so item 4 proceeded rather than
  halting on the discrepancy — reported prominently instead, both here and
  in the coordination-branch entry itself.
- **4c.** `sampurti/stranded-main-2026-08-15` branched from local `main` at
  `2e56ba9d1`, pushed to `origin`, and — the actual gate — all five commits
  independently reverified reachable from `origin`'s copy via
  `git merge-base --is-ancestor` (not just a successful `git push` exit
  code) before local `main` was touched.
- **4d.** Local `main` force-updated to `origin/main` (`9b4f63669` at the
  time) — a pure ref update, safe per 4a's confirmation.
- **4e.** Row appended to `origin/campaign-coordination` §6 (commit
  `dd313b622`) recording all of the above, plus what re-landing this content
  will owe SAMPŪRTI: a re-numbered `CURRENT_STATE` version bump (the
  original `v6.59→v6.60` is now stale — `origin/main` has moved since), and
  relocating `SAMPURTI_SESSION_LOG.md` per `ROOT_FILE_POLICY §2` (verified
  directly against that file's exhaustive root-file list — it is not on it).
  This session did not attempt either re-landing step.

## What contradicted this brief

1. **Item 4b's "three unique commits" claim** — refined to four-of-five
   carry non-duplicate bytes, with the nuance on `2139b3015` explained above.
   Did not change the preservation mechanism or its outcome.
2. **Item 1's implicit assumption that a merge-window request could be
   opened immediately** — the conductor's own P1 FOUNDATION merge (#1356,
   with 4 real production migrations) was actively in its own merge-queue
   window when this session opened `origin/campaign-coordination` for the
   first read. Not a contradiction of anything stated, but worth recording
   as the reason items 1a/2a/2b/2c/3 were built and committed *before* item
   1b's lease/merge, not after — the brief's own item ordering ("do the four
   items in this order") is about items 1-4 relative to each other, and was
   followed; the *internal* sequencing within item 1 (build first, merge
   once clear) was this session's own judgment call given the live
   collision risk.
3. **The self-inflicted `rm -rf` near-miss** on `00_ARCHITECTURE/drift_reports/`
   during item 1's CI-fix cleanup, recorded above under item 1c — caught and
   reverted before anything was committed, but recorded here because the
   brief's own §N.8 discipline is "report evidence, not intentions," and a
   mistake caught and fixed is still worth surfacing plainly rather than
   quietly omitting.
