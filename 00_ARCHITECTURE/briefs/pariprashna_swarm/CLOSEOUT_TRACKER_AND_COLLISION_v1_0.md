---
artifact: CLOSEOUT_TRACKER_AND_COLLISION_v1_0
canonical_id: PARIPRASHNA_CLOSEOUT_TRACKER_AND_COLLISION
version: 1.1
status: CURRENT
authored_by: Claude Code sessions PARIPRASHNA-CLOSEOUT-2026-08-19,
  PARIPRASHNA-CLOSEOUT-FINAL-2026-08-20
date: 2026-08-19/20
purpose: >
  Close-out record for the Paripraśna Execution Observatory build + the cross-campaign
  collision cleanup it surfaced. §"Executive summary" is written for a reader with no
  memory of this work; the detailed-record sections below it are the session-by-session
  engineering log the summary is drawn from.
changelog:
  - "1.1 (2026-08-20, PARIPRASHNA-CLOSEOUT-FINAL, item 2): added the executive-summary
    section for a fresh reader; folded in round 3 (DD-12, the structural finding)."
  - "1.0 (2026-08-19/20, PARIPRASHNA-CLOSEOUT): initial close-out record for round 2
    (items 1-4: land #1355, wire tracker-health-check, reconcile lane count, preserve
    SAMPŪRTI's stranded main)."
---

# PARIPRAŚNA-CLOSEOUT — Tracker Land + Cross-Campaign Collision Cleanup

## Executive summary — the full arc, for a reader with no memory of this work

**What this is.** The Paripraśna implementation campaign (chat-engine build, phases
P0-P5) needed a live tracker: something that could tell, at a glance, whether the swarm's
30-odd (later 53) build lanes were actually progressing, without trusting any agent's own
narration of its progress. What follows is the story of building that tracker, the real
incident it uncovered in itself, and the collision cleanup that incident led to.

### The arc

1. **Naive spec → derived observatory.** The original tracker spec (superseded, see §7 of
   the amendments doc below) would have had agents write their own progress into a shared
   JSON file — a **narrated** tracker, trustworthy exactly as much as the busiest, most
   error-prone part of the system it was meant to watch. It was rebuilt instead as a
   **derived** observatory: `trackerd.py`, an out-of-process daemon that reads ground
   truth from git, `gh`, and the filesystem on its own schedule and computes lane state
   from that — an agent's own claim about its state is recorded too, but rendered
   separately and never counted, and a claim that contradicts derived evidence fires a
   real anomaly (CLAUDE.md §N.8 applied to the instrument itself, not just the product).
2. **Four hardening rounds, each landing a real bug found the hard way:**
   - **#1353 — frozen snapshot install.** The very first version ran the daemon straight
     out of a `/tmp` git worktree — mutable (a `git checkout` there would silently swap a
     running daemon's code) and reboot-fragile. Fixed to `install.sh --install-from-ref`,
     an immutable `git archive` snapshot at `~/.pariprashna-tracker-code/`, with the
     dashboard showing the running code's own provenance rather than assuming it's current.
   - **#1354 — private mirror + ref-freshness axis.** The collector's every `origin/*`
     read resolved against the *shared* checkout's remote-tracking refs, which only
     advance when some unrelated process happens to fetch there — silently-stale-looking-
     fresh, the exact failure class this tracker exists to catch. Fixed by giving the
     daemon its own private mirror clone, fetched on its own cadence, plus a new
     **ref freshness** axis on the dashboard (see below).
   - **#1355 — rate bucket, operational proof, T4, lock, remembered blindness.** Five
     independent fixes in one PR, the largest hardening round: the GitHub rate-limit cell
     read the wrong API bucket (always green, measuring nothing); the ref-freshness
     distinction got a real operational proof (a real push through a real mirror, not just
     a selftest with synthetic ages); a fourth, out-of-band recovery tier (T4, cron, not
     launchd) was built and *proven live* against production, not just asserted; a shared
     advisory lock closed a race between the four scripts capable of moving the daemon's
     launchd labels; and a "remembered blindness" banner was added so a restart can never
     silently launder an unexplained gap into green.
   - **#1359 — the DD-11 honesty amendment.** The most important round, and the one this
     whole arc is really about: a rule was written (DD-11 — the conductor must call
     `tracker-health-check` at every lane transition) and its own follow-up investigation
     found that *nothing calls it*, because no deterministic hook to call it *from* exists
     anywhere in the campaign. Rather than let the rule keep reading as satisfied, its
     status was corrected in place to **IN FORCE — NOT YET WIRED**. See "The structural
     finding" below for where this leads next (item 1 of *this* round, DD-12).

### The three freshness axes, and why none substitutes for another

The dashboard tracks three independently-computed kinds of "is this stale," because a
system can be green on any two and dead on the third:

- **Observer freshness** — is the tracker's own data current (client-side, computed from
  `TRACKER_DATA.generated_at` against the browser's clock, independent of whether the next
  fetch succeeds — a fully dead backend still produces a loud red banner).
- **Subject progress** — is the *swarm* moving (are lanes actually changing state), tracked
  separately from whether the tracker itself is alive. A green observer over a frozen
  subject is a **stall**, and renders differently from both healthy and genuinely dead.
- **Ref freshness** (added in #1354) — are the git refs the tracker reasons *from* actually
  current, independent of both of the above. The observatory can be alive, the swarm can be
  moving, and the refs it's deriving lane state from can still be stale — a green observer
  and a moving subject over stale refs is confidently wrong, not healthy.

A system can satisfy any two of these and fail the third silently if only two are checked
— which is exactly why all three are computed and displayed independently rather than
folded into one "everything's fine" signal.

### The measured 23m37s blind window

Mid-build, the tracker itself went dark for 23 minutes 37 seconds — first heartbeat gone at
`2026-08-19T20:35:52Z`, no recovery until `20:59:29Z`.

- **Cause:** three separate, bare `launchctl bootout` calls at `20:36:22Z` — no
  `bootstrap` alongside them, no intentional-stop marker, no record of why. This shape
  matches, exactly, `install.sh`'s own *documented* "Stop all three" one-liner from before
  this arc's hardening — not a stalled or colliding reinstall (which always pairs
  `bootout` with `bootstrap` per job and would show a different process shape).
- **Attribution was attempted and genuinely failed.** Every locally-recoverable forensic
  path was exhausted: the macOS unified log's per-process records (no parent-PID chain
  retained for `launchctl` invocations), shell history (no timestamps on this machine),
  `last` (one continuous console login spanning the whole day — uninformative on a
  single-user Mac), and every Claude Code session transcript active in the window — the
  long-running main session that covered the entire incident, all ~40 of its subagents,
  every other project directory, Codex session stores, Claude Desktop's session stores.
  None contain the literal command. *Who* ran it is not known and is not going to be
  recovered from what's available on this machine.
- **The event is nonetheless adequately handled going forward**, on two independent
  legs: (1) the exact command that caused it — `install.sh`'s own printed "Stop all three"
  one-liner — no longer exists; `install.sh` prints `tracker-stop` instead, which cannot
  stop the jobs without first writing `STOPPED_INTENTIONALLY.json`; (2) even if a bare
  `launchctl bootout` is run some other way, entirely bypassing `tracker-stop`, the next
  daemon start compares against the last heartbeat, finds no marker, and writes
  `BLIND_WINDOW.json` — a sticky, restart-surviving record that only an explicit
  `tracker-ack-blind` retires. A recurrence is now **self-announcing**, which the original
  incident was not.

### The retracted overclaim

The first pass at root-causing this incident proposed a specific mechanism: an isolated-
`$HOME` test install of the tracker, unaware that `launchctl` labels are global to the
launchd domain regardless of `$HOME`, booting out the real production jobs via the shared
label. That hazard is **real** — independently verified by its own selftest, and closed by
`install.sh` refusing to run under a mismatched `$HOME` + the production label prefix. But
process-forensic follow-up (the exact `launchctl` call shape, three bare `bootout`s with no
`bootstrap`) does **not** match what that mechanism would produce, which is `bootout`+
`bootstrap` pairs. **The HOME/label hazard is real and guarded; it was not confirmed as
this specific incident's cause**, and the record was corrected to say so rather than let
the first plausible theory stand uncorrected.

### T4, proven live

The fourth recovery tier (cron, not launchd — a launchd-domain bootout, the incident's own
mechanism, cannot touch a crontab entry) was not just built and unit-tested; it was proven
against the real production system. The actual incident was reproduced (raw bootout ×3, no
marker) against a live deployment, and T4's cron tick caught and recovered it: **measured
3 minutes 51 seconds from bootout to full health**, with the incident event and the
resulting `BLIND_WINDOW.json` record both captured as real evidence, then acknowledged and
cleaned up afterward since it was a deliberate test.

### The collision cleanup

While working, five commits were found stranded on a local, never-pushed `main` —
`origin/main..main` five commits deep, from the SAMPŪRTI campaign, not this one. They were
**preserved, not re-landed**: branched onto `sampurti/stranded-main-2026-08-15` and pushed
to `origin`, with all five commits independently reverified reachable from `origin`'s copy
(not just a successful push) *before* local `main` was force-updated to match `origin/main`.
Content re-verification refined the original claim of "three commits carry unique content"
— `993522c00` (a test file) is a confirmed byte-identical duplicate of an already-merged
commit (`1d6f3ad5a`, PR #1286); but `2139b3015` (a 2-line marker) is *not* a clean duplicate
the same way — its exact bytes are not verbatim anywhere on `origin`, even though its
*substance* was already superseded by a later, corrected post on `campaign-coordination`.
Net: four of five commits carry bytes not verbatim on `origin/main`, not three, though one
of those four is substantively redundant. **Re-landing is owed to SAMPŪRTI, not done here**,
and carries two preconditions the re-landing session will need to satisfy: renumber the
`CURRENT_STATE` version bump (the stranded commit's `v6.59→v6.60` is now stale — `origin/main`
has moved since), and relocate `SAMPURTI_SESSION_LOG.md` per `ROOT_FILE_POLICY §2` (a
root-level file, not on that policy's exhaustive allow-list).

### The rm -rf near-miss

During CI cleanup in round 2, `rm -rf 00_ARCHITECTURE/drift_reports/` — intended to remove
two local scratch files — deleted the entire tracked directory instead: 166 committed
historical files going back to April. Caught via `git status` before anything was
committed, restored with `git checkout --`, verified restored, and the actual two scratch
files removed afterward by exact filename. No harm done, but recorded here (and in the
tracker's own README, under "Operational hazards") specifically so a future session doesn't
spend the same cycle rediscovering it: **delete by exact filename, never `rm -rf` a
directory that also holds tracked files.**

### The structural finding — what is NOT covered

DD-11 (the conductor calls `tracker-health-check` at every lane transition) is **written**
but **not mechanically enforced**, and the follow-up investigation into why found something
larger than a missing single call: **lane transitions in this campaign are prose-only.**
There is no deterministic per-lane hook anywhere — not for tracker event emission, not for
`tracker-health-check`, not for `may_touch` lease enforcement, not for budget accounting
against the DD-5 ceilings. All of it depends on an agent remembering to do it, at exactly
the kind of boundary where the 23-minute blind window happened. This is now its own entry,
**DD-12**, in `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` §2 (this round's item 1;
full text there, not duplicated here) — a proposed `lane(...)` wrapper that would make the
per-lane discipline structural rather than remembered, with a single P2-close decision
point: either the wrapper gets built and DD-11 moves to WIRED, or DD-11 is explicitly
downgraded to ADVISORY. **This session did not build that wrapper** — P2 is mid-flight, and
inserting a new mandatory hook into a running phase is exactly the disruption DD-11 itself
was written to avoid. Whether it gets built is P2 close's decision, not this session's.

Also not covered by any of this work: the conductor's own adoption of DD-11 in practice
(one manual, read-only `tracker-health-check` invocation is recorded on
`campaign-coordination` from the P2 presentation-truth-wave entry, plus a commitment to
keep invoking it by hand for the rest of P2 — real signal, still agent-remembered, not
proof of mechanical enforcement); and anything outside the `pariprashna_swarm/` tree this
work never touched.

---

## Detailed record — round 2 (PARIPRASHNA-CLOSEOUT, 2026-08-19/20, items 1-4)

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

## Detailed record — round 3 (PARIPRASHNA-CLOSEOUT-FINAL, 2026-08-20, items 1-3)

### Item 1 — DD-12, the structural finding

Full text lives in `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` §2, immediately
after DD-11 (not duplicated here). Summary: the DD-11 investigation's root cause — no
deterministic per-lane hook exists anywhere in this campaign, for tracker emission,
health-checking, `may_touch` enforcement, or budget accounting alike — is now its own
register entry, DD-12, with the proposed fix (a `lane(...)` wrapper making per-lane
discipline a side effect of being called rather than a remembered step) and a single
P2-close decision point that now governs both DD-11 and DD-12: either the wrapper is
built and DD-11 moves to WIRED, or DD-11 is explicitly downgraded to ADVISORY. DD-11's
own deadline clause was removed in favor of this one, per the brief's instruction — one
decision point, not two. No code was written this session; P2 is mid-flight and the
whole point of DD-11's own effective-date note was not to reach into a running phase.

### Item 3 — Final integrity sweep

Every dated or conditional obligation found live across the Paripraśna document set —
`PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` (DD-1..DD-12, RF-1..RF-12),
`CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md` (X-1..X-7), the SAMPŪRTI
re-landing debt (this arc's own item 4), and anything else surfaced along the way.
Owner/deadline/detector columns below reflect what's actually verifiable from the
documents and `campaign-coordination`, not an exhaustive re-audit of every phase's own
internal residual list — where that scope limit applies, it's noted per-row.

| ID | Obligation | Owner | Deadline | Detector behind "satisfied"? |
|---|---|---|---|---|
| DD-1 | AC-15/W-4 week-of-use verdict | native (async signal) | none — by design, async; explicitly never records a PASS | Real: automated feel-proxy metric battery at stated targets. Self-guarding text ("swarm never records an AC-15 PASS") not independently re-verified this sweep. |
| DD-2 | ANTHROPIC_API_KEY delist | P0-F lane | P0 close | **Discharged** — confirmed via `campaign-coordination`'s P0-close entry ("P0-F DD-2 anthropic delist"). |
| DD-3 | Infra operator packet (PITR/scratch/rotation) | native (explicit go-ahead required) | **NONE — open-ended HOLD** | N/A, not started; correctly not claimed as done. **Flag: no deadline set for when this HOLD itself gets revisited.** |
| DD-4 | Retirement commit + flag deletion (P4) | conductor | P4 | Contingent on real, named checks (verifier line-by-line diff, 7 green smokes, rollback pin) — not yet due. |
| DD-5 | Build-run spend ceilings | conductor/agents | per-phase, ongoing | **No** — the tracker's own README states budget tracking is "CLAIMED-only... necessarily self-reported," not derived. DD-5's own text ("ceiling hit = clean halt") reads as an enforced mechanism; there is no derived one. **This is a live, confirmed instance of the exact DD-12 finding** (DD-12 already names "budget accounting against the DD-5 ceilings" as one of the disciplines with no deterministic hook) — not a new gap, but worth naming concretely rather than leaving DD-12's claim abstract. |
| DD-6 | Taste calls | judge panel | ongoing, no fixed date | Process-based (panel majority), not a single detector claim. |
| DD-7 | Seven-smoke hold (P3) | conductor (autonomous wait) | P3 | Real: CI history, `green×7` count — not yet due. |
| DD-8 | Q-2 reading grading + docs seal (P4) | gate-runner | P4 | Real, explicitly labeled MACHINE-GRADED — not yet due. |
| DD-9 | G0 PR merge | kickoff step 0 | G0 | **Discharged** — PR #1346, per `campaign-coordination`'s own Step-0-complete entry. |
| DD-10 | CAMPAIGN_COORDINATION dirty-file conflict | every session | perpetual | Procedural discipline, continuously exercised (including by every worktree/lease action across this whole arc). |
| DD-11 | tracker-health-check halt rule | conductor | superseded — see DD-12 | **Already corrected this arc**: honestly marked `IN FORCE — NOT YET WIRED` rather than reading as enforced. The one entry in this table that used to be the exact defect class and now explicitly is not. |
| DD-12 | Structural finding / `lane` wrapper | this arc / whoever closes P2 | P2 close | New this session. Binary outcome required at the deadline — the one item in this whole table designed so it *cannot* silently read as satisfied without a real choice being made. |
| RF-1..RF-12 | Design findings from the original swarm-plan review | — | mostly discharged at the phase their FIX named (RF-1's ports refactor at P0, confirmed via `campaign-coordination`) | These are closed findings folded into standing process (train protocol, migration allocator, ownership rules, etc.), not per-instance dated obligations — correctly out of scope for this table's "owner + deadline" framing, noted here so their absence from the rows above isn't mistaken for an oversight. |
| X-1..X-7 | Isolation rules (lease-before-merge, governance-batching, no root-brief-write, worktree-only, no stash, deploy/DB leasing, fetch-before-cut) | every session, perpetual | none — standing, always-on | Procedural, exercised continuously through this whole arc's own worktree/lease/coordination discipline — not a one-time detector to check off. |
| SAMPŪRTI re-landing (this arc's item 4) | Re-land `47e3a6a54`/`c64eee28c`/`2e56ba9d1` from `sampurti/stranded-main-2026-08-15`, with CURRENT_STATE renumbering + `SAMPURTI_SESSION_LOG.md` relocation as preconditions | SAMPŪRTI, explicitly (not this campaign) | **NONE STATED** | N/A — preservation is done and verified; re-landing itself hasn't started. **Flag: no deadline exists for when SAMPŪRTI's debt should be discharged**, same shape as DD-3's open-ended hold. |
| G1-A flag-enablement residuals (HS-4 false-positive; `/api/chat/consult` partial safety wiring) | Must resolve before `PARIPRASHNA_SAFETY_GATE_ENABLED` ever flips `true` | whichever session flips that flag (not named) | **NONE STATED** — gated on a future event, not a phase boundary | Not independently re-verified this sweep whether a real detector backs "resolved" for either residual — flagged for scope, not confirmed broken. |
| P2-D outbox migration | Deferred; a schema-train lease will be opened separately before the migration is written | P2-D lane | **NONE STATED**, open-ended "separately, before..." | N/A — correctly *not* claiming the migration exists; flag default `false`, graceful degrade documented. No false-satisfied risk here; included for completeness of the sweep, not as a problem. |

**Summary of what this sweep found:** three obligations carry an owner but no deadline
(DD-3's infra hold, the SAMPŪRTI re-landing debt, the G1-A flag-enablement residuals) —
open-ended by original design in DD-3's case, not obviously by design in the other two.
One obligation (DD-5) is a live, confirmed instance of exactly the defect class this
whole arc was about: text that reads as an enforced ceiling with no derived mechanism
behind it, already covered by DD-12's blanket finding but worth naming directly. DD-11
is the one row in the table that used to be this defect class and now explicitly says
so instead of hiding it. No entry was found reading as fully SATISFIED while silently
lacking a detector — the closest candidates (DD-5, the G1-A residuals) are already
either named (DD-5, via DD-12) or explicitly flagged above as unverified, not silently
passed over.
