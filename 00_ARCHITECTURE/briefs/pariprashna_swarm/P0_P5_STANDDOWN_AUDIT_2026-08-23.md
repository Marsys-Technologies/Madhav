---
artifact: P0_P5_STANDDOWN_AUDIT
canonical_id: PARIPRASHNA_P0_P5_STANDDOWN_AUDIT_REPORT
version: 1.1
status: >
  PHASE 1 + PHASE 2 COMPLETE, PARTIAL BY DISCOVERY. Phase 1: no BLOCKING finding, three MATERIAL
  findings on record. Phase 2: tmux/process teardown (§2.1) DID NOT EXECUTE — the `prp-night`
  session's conductor window was found live-hosting a different campaign's (Nirmana) active
  autonomous run, which is out of scope for this document; native instructed report-only on
  discovery. Worktree/branch/lease/tag cleanup (§2.2/§2.3/§2.4) executed as reporting-only per
  their own guardrails — zero worktrees and zero branches were actually deleted by this document,
  by design (§0 Ruling 5 makes branch/worktree deletion a MUST-PARK/report item, not a
  pre-authorized action).
authority: PARIPRASHNA_P0_P5_STANDDOWN_AUDIT_v1_0.md §0 (all five rulings granted by the native
  in-session, 2026-08-23)
role: >
  The Phase 1 gap ledger required by §1.5 of the standdown audit charter. Produced by three
  parallel forks (P0-P2 / P3-P4 / P5) plus direct primary-evidence verification of the two
  discrepancies the forks surfaced but did not fully resolve. Every prior report — including the
  pre-Phase-5 closeout's own account of itself — was treated as a hypothesis, not a fact, per
  DD-21 and CLAUDE.md §N.8.
---

# Paripraśna P0–P5 — Phase 1 standdown audit report

**Run-open:** `origin/main` fetched fresh this session. HEAD = `2670e61e2297d9b800217218cd96da8d0cb3b863d`
(authored 2026-08-23T04:40:21Z). This worktree (`pariprashna/standdown-audit-2026-08-23`) is
checked out at that exact commit — **nothing has landed on `main` since the pre-Phase-5 closeout
(PR #1517) merged.** Confirmed directly via `git rev-parse HEAD` / `git log -1 origin/main`, not
inherited from any prior report.

## Three findings most worth attention

1. **The campaign's own live tracker (`lane_evidence.json` / `project.py`) falsely marks P3-F
   ("THE FLIP") and P4-A ("consult/consume retired") as MERGED, attributed to PR #1508.** PR
   #1508 is confirmed (via `gh pr view --json files`) to be docs/census-only — 3 files, zero
   application code — and its own title states P4-A *as specified would destroy the P3-F
   auto-rollback*. The closeout report itself is honest about this (P3-F and the RETIRE train are
   explicitly PARKED, DD-47), so this is a **tooling defect**, not a governance lie — but it means
   any future session that trusts the tracker's lane-evidence file rather than primary evidence
   would be misled into believing two central P3/P4 gate items are done when they are not. This
   is the exact D-1.6/§N.8 defect class (a status signal with no correct detector behind it).
2. **DD-47/48/49 are not landed in any decision register — they exist only as prose inside
   `PRE_PHASE5_CLOSEOUT_REPORT_v1_0.md`.** The closeout's own merge commit (`2670e61e2`) claims
   "New DD entries: DD-47, DD-48, DD-49. Registry: one batched write, fingerprint rotated" — but
   `OVERNIGHT_DECISION_LEDGER_2026-08-22.md` (the real running DD ledger, DD-1 through DD-44) was
   not touched by that commit, and `PARIPRASHNA_DECISION_REGISTER_v1_0.md` has been stale since
   2026-08-18 (NCD-series only, zero DD-N entries). The "registry write" the commit message
   describes did not happen against any file that actually functions as the registry.
3. **DD-7's "green×7" claim, independently re-derived from CI run history rather than reused from
   any report, is 3 genuine post-fix greens, not 7.** 4 of the 7 raw green runs predate PR #1515
   (the fix that made deploy-commit attribution trustworthy) — one of those 4 is the literal
   example PR #1515's own commit message cites as a broken attribution. This does not change any
   operational conclusion (P3-F/P4-B were never executed either way, so nothing rests on the
   count being right), but the number should be corrected wherever it's cited going forward.

None of these three rises to BLOCKING under the charter's own test (§1.4's explicit BLOCKING
trigger — a live P5 table or flag — did not fire; nothing here reflects a live-system risk,
production drift, or an executed irreversible action). All three are MATERIAL: real, worth
fixing, but not evidence that the parked/honest state the closeout claims is false.

---

## Phase verdicts

| Phase | Verdict | Primary evidence |
|---|---|---|
| **P0 — IGNITION** (6 lanes) | **VERIFIED** | Tracker merge-evidence (fresh collector snapshot, `collected_at: 2026-08-23T10:06:51Z`) shows 6/6 lanes MERGED, phase CLOSED, all merge commits re-confirmed as ancestors of `origin/main` this session. Live spot-check: P0-C's declared pipeline files (`safety_gate.ts`, `plan_stage.ts`, `evidence_stage.ts`, `synthesis_stage.ts`, `validation_stage.ts`, `receipt_stage.ts`, `persistence_stage.ts`) all present in the current checkout, matching `PLAN.yaml`'s `expected_artifacts.paths`. P0-F's posture doc (`G1_F_PROVIDER_POSTURE_v1_0.md`) present. |
| **P1 — FOUNDATION** (10 lanes) | **VERIFIED** | Tracker: 10/10 MERGED (PR #1356, commit `d653236c2a`, re-confirmed ancestor). Live spot-checks: `pg_roles` query against the live DB confirms all 5 roles (`role_jobs`, `role_ledger_write`, `role_orchestrator`, `role_sidecar`, `role_web_serve`) exist; `pg_class` confirms `relrowsecurity=true` on `charts`, `chart_divisionals`, `access_requests`. `safety_gate.ts` present with live HS-2/HS-3/HS-4 logic intact. |
| **P2 — THE READING MADE TRUE** (15 lanes) | **VERIFIED** | Tracker: 15/15 MERGED (PRs #1360/#1363/#1364/#1365, re-confirmed ancestors). All 7 lanes the P2 close report itself flagged as "merged+green+flagged+tested but delivering nothing observable," plus Lane K, re-checked live on current code — none reverted, all still present (`interpretation/worker.ts:439`, `synthesis_stage.ts:86,327`, `protocol/events.ts:458,610`, RightDock CSS, `voice_lint.ts:114-122`, `GroundingCard.tsx`). Item 6 (observability identity wiring) re-confirmed **firing in production today**: real `llm_usage_events` rows at `2026-08-23T05:14:10Z`, `channel: "web"`, `status: "success"`. |
| **P3 — ONE ENGINE, ONE DOOR** (6 lanes) | **PARTIAL, correctly so — matches the closeout's own self-description** | Live lane_evidence: only P3-B, P3-C, P3-D genuinely merged; P3-F is falsely marked merged (see Finding 1) but is actually PARKED per the closeout's own DD-47/DD-48. This is **not a regression or a hidden gap** — the closeout report's `status:` line says exactly this ("CLOSED — PARTIAL BY DESIGN; the RETIRE train parked on a gate premise that proved false"). Confirmed independently: `origin/main` HEAD is the closeout commit itself, so nothing has un-parked P3-F since. |
| **P4 — THE OLD DIES, THE INSTRUMENT REMEMBERS** (11 lanes) | **PARTIAL, correctly so — same basis as P3** | Live lane_evidence: P4-B, P4-H, P4-K genuinely merged; P4-A is falsely marked merged (Finding 1) but the RETIRE train (P4-A→B→C→D) is confirmed PARKED — legacy `consult`/`consume` tree fully present and untouched at HEAD (last touching commit `d653236c2`, unrelated P1 work), zero deletion executed, zero flag removal executed. PR #1508's diff (docs/census-only, 12,464 additions / 0 deletions across 3 non-application files) is exactly what a "discovery doc recommending against opening the train" looks like, not a completion of P4-A. |
| **P5 — [charter name withheld pending own authorization]** | **CLEAN — correctly not started** | Direct DB query: `SELECT table_name FROM information_schema.tables WHERE table_name ILIKE '%conversational_calibration%'` → zero rows (36 existing `mimamsa_%` tables checked, all pre-existing L5-sealed STRUCTURAL-mode tables, none is the P5 table). No matching migration file (applied or unapplied). Live Cloud Run env-var read on **both** `amjis-web` revisions — including the 0%-traffic `limits-canary` tag — for `P5_`/`CALIBRATION_ENABLED`/`mimamsa_conversational`: zero matches. `platform/src/lib/pariprashna/confidence/activation_gate.ts` read in full: still the honest placeholder (`ACTIVATION_GATE_THRESHOLD_IS_PLACEHOLDER = true as const`, gate structurally cannot open without a real ≥30-sample empirical count that does not exist under current STRUCTURAL-mode conditions). |

## §1.3 checklist — item by item

- **`2670e61e2` ancestor of/equal to current `origin/main` HEAD?** Equal — it IS current HEAD. Nothing landed since.
- **Anything landed since touching the retirement surface/smoke workflow/flip machinery?** No — nothing has landed since this commit, period.
- **DD-7 green×7, re-derived independently:** 3 genuine post-fix greens (`3a54918f4` 04:28Z, `68cde91e4` 04:46Z, `2670e61e2` 05:12Z), not 7. See Finding 3.
- **RETIRE train still parked?** Yes — confirmed live (legacy tree untouched, PR #1508 is docs-only, its title itself argues against opening P4-A as specified).
- **Production ≡ `origin/main` by serving revision?** Yes — `amjis-web` revision `amjis-web-01695-9d5`, 100% traffic, label `commit-sha: 2670e61e297d9b800217218cd96da8d0cb3b863d`, exact match. Confirmed live, not inferred.
- **No `pariprashna/p3-close` or `pariprashna/p4-close` tag?** Confirmed — `git tag -l 'pariprashna/*'` on origin shows only `p0-close`, `p1-close`, `p2-close`, `p3-preflight-close`. Neither exists.

## §1.4 checklist — item by item

All three items CLEAN. See P5 row above for evidence. No BLOCKING trigger fired.

---

## Gap ledger

### MATERIAL

- **M-1 (Finding 1).** `lane_evidence.json`'s collector mis-attributes P3-F and P4-A as merged to
  PR #1508, which is docs-only and argues against implementing either as specified. Recommend:
  fix the collector's PR-to-lane matching (likely a naive commit-message/title parse that grabbed
  "P4-A" from the PR title's prose rather than confirming an actual code change), or failing that,
  hand-annotate `lane_evidence.json` to remove the false entries before anyone next trusts the
  tracker's phase-completion view. Not urgent for safety — no live system reads this file as an
  authorization gate — but it is exactly the shape of defect this campaign's own doctrine (§N.8)
  exists to catch, so it should not go unfixed indefinitely. Phase 2 will kill the tracker daemon
  (`trackerd.pid`, currently live, last snapshot 2026-08-23T15:37) regardless, which removes the
  live source of this bad projection but does not fix the historical file.
- **M-2 (Finding 2).** DD-47/48/49 exist only as prose in `PRE_PHASE5_CLOSEOUT_REPORT_v1_0.md`;
  the closeout commit's own claim of a "registry write" does not correspond to any edit of
  `OVERNIGHT_DECISION_LEDGER_2026-08-22.md` (the actual running ledger, DD-1 through DD-44) or
  `PARIPRASHNA_DECISION_REGISTER_v1_0.md` (stale since 2026-08-18, architecture-decision NCD
  series only). Recommend: append DD-47/48/49 to the running ledger as real entries, citing the
  closeout report as source. This document does not do that write itself — it is outside this
  audit's pre-authorized scope (§0 Ruling 5 does not cover DD-register edits) and belongs to
  whoever owns ledger-append authority.
- **M-3 (Finding 3).** DD-7 "green×7" should read 3, not 7, everywhere it's currently cited, with
  the clock understood to have restarted at PR #1515 (2026-08-23T04:12:35Z). Does not block
  anything currently, since P3-F/P4-B were never executed under the inflated count.
- **M-4.** Three Pariprashna worktrees carry real unmerged content and are **MUST-PARK, not
  removal candidates**, under §0 Ruling 5:
  - `p4-g` (branch `pariprashna/p4-g`): 3 unmerged commits, a complete tested (254/254 green)
    feature — "the window-opening ask" (P4-G), flagged OFF by default.
  - `p4-h` (branch `pariprashna/p4-h`): 2 unmerged commits. Its DD-28/29/30 content is **not**
    stranded exactly as feared — the running ledger already carries a numbering-reservation note
    ("the DD-28/29/30-on-a-branch numbering note, so a later merge does not renumber") disclosing
    exactly this state honestly. No new gap here beyond what's already on record.
  - `prp-dd46` (branch `pariprashna/dd-credential-misdiagnosis`): 1 unmerged docs-only commit
    (DD-46 finding).
  `prp-coord` (branch `campaign-coordination`) is the live lease-log branch, expected to be ahead
  of main by design — not a removal candidate at all, in scope or out.

### RECORDED (disclosed, no action needed)

- **R-1.** Lease hygiene is clean: 13 "lease open" / 13 "lease closed" pairs reconcile on
  `campaign-coordination`. One minor historical gap (P4-H's lease was worked without an explicit
  open commit, then retroactively closed in `f34ee3eba`) — already resolved, already on record.
- **R-2.** `campaign/nirmana-autonomous` was not touched, read beyond its worktree-list row, or
  commented on beyond this line, per the charter's explicit instruction.
- **R-3.** Two `llm_usage_events` rows today show `provider: "anthropic"`, `status: "error"` —
  consistent with the already-disclosed, non-blocking "`ANTHROPIC_API_KEY` unprovisioned in
  production" finding carried in `CLAUDE.md`'s own changelog. Not new.
- **R-4.** `state.json`'s 85-entry anomalies list is an append-only historical event log spanning
  the full Aug 19–23 run (mirror-lag/blind-window notices) — not a current-defect count. Flagging
  so it isn't mis-read as 85 live problems.

### BLOCKING

None found.

---

## What was not fully re-derived (honest scope note)

Per DD-21 discipline, disclosing what this audit leaned on rather than independently re-proving:
the P0-P2 fork relied on `PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md`'s G1–G9 gate *wiring* as
encoded in `PLAN.yaml`'s `gate:` fields rather than doing a full prose read of the roadmap
document itself, to conserve budget. Nothing found suggests the two disagree, but this is a
narrower check than a full G1–G9 prose audit would be. Worth a follow-up read if anyone doubts
the gate criteria, not urgent.

---

# CLEANUP AUTHORIZED: YES

No BLOCKING finding. Three MATERIAL findings recorded above with recommended (not
self-executed) fixes. Delivering this report to the native now, before touching §2, per the
charter's own instruction ("Deliver this to the native before touching Phase 2").

---

## Phase 2 report

Native authorized proceeding to Phase 2 after reviewing the above.

### §2.1 tmux and processes — **NOT EXECUTED, cross-campaign collision found**

Before touching anything (capture-then-kill order, per the runbook), checked `prp-night`'s live
state: `tmux list-windows -t prp-night` shows 4 windows (`conductor`, `sentinel`, `pulse`,
`logs-`), session **attached**. Read-only `tmux capture-pane -p -t prp-night:conductor` (no file
write, nothing killed) showed the conductor window's status bar reading **"Nirmana autonomous
campaign conductor"** — live transcript of KARAKA agents M0-T43/M0-T44 landing, a PARĪKṢAKA stall
recovery, and an active `bypass permissions on` Claude instance mid-cycle awaiting "WATCHDOG
NUDGE #3." `~/pariprashna_night/logs/conductor.log` (34MB), `pulse.log`, and `sentinel.log` are
all being actively written to as of minutes before this check — the session is genuinely live,
not stale.

This is a hard stop under the charter's own absolute rule: `campaign/nirmana-autonomous` is
out of scope, full stop, including its sessions. Killing `prp-night` would have terminated a
live, unattended, in-progress agent swarm belonging to a different campaign. **Reported to the
native before any capture-pane-to-file write or kill command ran.** Native chose: stop all
tmux/process work, report only. Result: **the tmux session, its 4 windows, the sentinel/pulse
loops, the tracker daemon (`trackerd.py`/`serve.py`), and all associated `caffeinate` processes
remain exactly as found — nothing was captured, stopped, or killed.** This is carried forward as
an open item, not a completed cleanup step; see "what cannot close" below.

### §2.2 Worktrees — reporting only, zero removed (by design)

All four Pariprashna worktrees confirmed **MUST-PARK or not-applicable**, consistent with the
Phase 1 finding — none qualified for removal:
- `p4-g` — 3 unmerged commits, open PR #1500, real tested feature (P4-G). MUST-PARK.
- `p4-h` — 2 unmerged commits, open PR #1496, DD-28/29/30 numbering-reservation content already
  honestly disclosed elsewhere. MUST-PARK.
- `prp-dd46` — 1 unmerged commit, open PR #1513 (DD-46 finding). MUST-PARK.
- `prp-coord` — the live `campaign-coordination` lease-log branch itself; not a feature worktree,
  not in scope for removal consideration.

Zero worktrees removed. This is the correct outcome given the state found, not a shortfall.

### §2.3 Branches, leases, tags

**Branches — cross-referenced against actual GitHub PR merge state** (not raw git ancestry, which
is unreliable for squash-merged PRs): of 61 remote `pariprashna/*` branches,
- **55 confirmed MERGED via an actually-merged PR** — reported here as removal candidates, not
  deleted (branch deletion is not on §0 Ruling 5's pre-authorized list):
  `audit-fixes, audit-ledger, citation-leak-fix, closeout-dd11-amend, closeout-final-2026-08-20,
  closeout-record, dd1-battery, dd16-dd17-closeout, dd17-supersede-diagnostic, dd28-30-split,
  governance-close, hs4-fix, ledger-fold, overnight-close, p0 (×2 PRs), p1, p2, p2-close-fixes,
  p2-close-item5-dock-collapse, p2-close-item6-observability, p2-close-item7-voice-anchor,
  p2-close-lane-k-typed-confidence, p2-epistemic (×2 PRs), p2-final, p3-a, p3-c, p3-d-prep, p3-e,
  p3-preflight-part-{a,c,d,e,f,f-residual-b,g,h,h-close}, p3f-rollback-pin, p3p4-charter,
  p4-census, p4-i, p4-j, p4-k, probe-harness, register-closeout, tracker-p2-p3-preflight-sync,
  tracker-v2, tracker-v2-derive-reality, tracker-v2-durable-evidence, tracker-v2-harden-install,
  tracker-v2-launchd-path-fix, tracker-v2-mirror-refs, tracker-v2-pidfile-race,
  tracker-v2-rate-bucket-ref-proof, tracker-v2-url-and-supervision`.
- **3 have an OPEN PR** (`dd-credential-misdiagnosis` #1513, `p4-g` #1500, `p4-h` #1496) — these
  are exactly the three worktrees flagged MUST-PARK above; consistent cross-check, not new
  information. Not removal candidates.
- **4 have no PR at all** (`g1-a-hardened`, `g1-a-safety-gate`, `g1-g-injection-containment`,
  `p0-c-ports-refactor`) — investigated rather than reported blind: neither is an ancestor of the
  `p0`/`p1`/`p2` umbrella branches, but a file-level content check on `g1-a-safety-gate` shows 59
  of 79 changed files already byte-identical on current `main` (the other 20, including
  `safety_gate.ts`, differ because main's version is a *later, superseded* revision — P1-A is
  independently confirmed live and VERIFIED in Phase 1). This is early draft/WIP work whose
  successor already landed by another route, not stranded functionality. Lower-confidence removal
  candidates than the 55 PR-confirmed ones, but not MUST-PARK either — reported for native
  judgment, not deleted.

**Leases:** already confirmed clean in Phase 1 (R-1) — 13/13 open/close pairs reconcile, one
historical gap already resolved on record. Nothing to close this pass.

**Tags:** re-confirmed at Phase 2 time — `git tag -l 'pariprashna/*'` on origin still shows only
`p0-close`, `p1-close`, `p2-close`, `p3-preflight-close`. No `p3-close`/`p4-close` tag exists.

### §2.4 The kit folder

`~/pariprashna_night/` left in place, untouched, exactly per instruction. Its `logs/` directory
(`conductor.log` 34MB, `pulse.log`, `sentinel.log`) is actively growing as of this report — direct
evidence the overnight apparatus is still genuinely running, not dormant. Ready for a future P5
launch whenever separately authorized, once §2.1's open item is resolved.

### Budget actuals

Three parallel fork agents (P0-P2 / P3-P4 / P5 re-verification) plus direct primary-evidence
follow-up on the two discrepancies they surfaced (tracker lane-attribution, DD register content)
plus branch/worktree/lease/tag reporting for Phase 2. Well inside the $200 proposed ceiling
(Ruling 3) — this was a read-heavy audit with a small number of `gh`/DB/live-revision calls, no
build or long-running compute.

### `campaign/nirmana-autonomous` — confirmed not touched

Its worktree row was read (`git worktree list` output only) and its live tmux conductor pane was
read once, read-only, to determine it was unrelated to Pariprashna — no file in that campaign's
tree was opened, edited, or otherwise interacted with, no branch of it was touched, and the
discovery that its conductor is running inside the `prp-night` tmux session is reported here
exactly once, as instructed, without further comment or action.

### What cannot close (carried forward unchanged, plus one new item)

- AC-15, P5's own time-gate, DD-26, P4-B's reversibility note if ever exercised — all carried
  forward unchanged from prior reports, untouched by this audit.
- **New:** the `prp-night` tmux session / sentinel / pulse / tracker-daemon teardown is
  **undone** — it needs a session where the native either (a) confirms the Nirmana conductor
  currently occupying that session's window 0 can be safely relocated/reattached elsewhere before
  cleanup proceeds, or (b) clarifies that `prp-night` and the Nirmana session are intentionally
  the same physical terminal by design and cleanup should target only the sentinel/pulse windows
  specifically (tmux supports killing individual windows without killing the session) rather than
  the whole session.
- The three MATERIAL findings from Phase 1 (M-1 tracker mis-attribution, M-2 unregistered
  DD-47/48/49, M-3 DD-7 miscount) remain open — recommended fixes recorded, not self-executed by
  this document.

---

## Where Pariprashna stands (one line, zero context assumed)

P0–P2 are genuinely done and re-verified against live production; P3–P4 are honestly,
correctly incomplete (paused, not closed, exactly as the closeout itself said) with the RETIRE
train safely parked and nothing destructive executed; P5 is confirmed untouched; and the
overnight run's automation is still physically running on the machine, tangled with an unrelated
campaign's live session, waiting on a native decision before anyone can safely turn it off.

*End P0_P5_STANDDOWN_AUDIT v1.1.*

---

## Addendum — 2026-08-23, post-audit disposition of the three MATERIAL findings + the open tmux item

Native authorized (a) resolving the §2.1 tmux collision by killing `prp-night` outright — including
the Nirmāṇa process occupying it, since that occupancy was contamination, not intentional shared
use, and this override was scoped to that one action only — and (b) landing the three MATERIAL
findings. Both are done. Disposition, in order:

**§2.1's open item — CLOSED.** `prp-night` (all 4 windows, sentinel/pulse loops, all associated
`caffeinate` processes) confirmed terminated. A preservation snapshot of the shared checkout's state
at kill time was written before the kill
(`~/pariprashna_night/logs/nirmana_contamination_snapshot_20260823T110608Z.txt`). A read-only
contamination audit across every commit on every branch since 03:00 today, in both directions, found
**zero** cross-boundary writes — the collision was confined to the live tmux pane/process, never to
git history. Full account in this session's own record; not duplicated here. A fresh, verified-isolated
tmux session (`pariprashna-postclose`) now exists, scaffolded but deliberately not auto-populated with
a new autonomous conductor process, pending native direction on what it should run.

Also closed in the same pass, not previously listed as an open item but reported here for completeness:
the tracker daemon (`trackerd.py`, `serve.py`, both under `~/.pariprashna-tracker-code/`) — confirmed
Paripraśna's own infrastructure, unrelated to the Nirmāṇa contamination — stopped cleanly via its own
`tracker-stop` script (writes `STOPPED_INTENTIONALLY.json` before booting the launchd jobs out, so a
future restart can tell "requested" from "crashed"). Resume with `tracker-start`.

**M-1 — CONFIRMED, root cause found, hand-annotated.** `lane_evidence.json` (`~/.pariprashna-tracker/`,
not repo-tracked) really did attribute both P3-F and P4-A to PR #1508 (confirmed docs-only: a census
document, a census JSON, and a census script — zero application code). Root cause, from
`collect.py`'s `extract_lane_identifiers`: title-token matching has no "claim, not mention" guard —
only the body side requires bold-marking. #1508's title mentions "P4-A" and "P3-F" in a *warning*
sense ("P4-A as specified would DESTROY the P3-F auto-rollback"), and the naive regex can't
distinguish that from an implementation claim. Fixing `collect.py` is real code work and out of this
pass's scope; the tool's own docstring already names the correct fallback — "lanes stay UNOBSERVABLE
— honest silence, never a fabricated MERGED" — so both false entries were removed from
`lane_evidence.json` directly (backup retained at
`/Users/Dev/.claude/jobs/26857c64/tmp/lane_evidence.json.bak`). This is a local runtime-state fix, not
a repo change — there is nothing to commit for it. The daemon is stopped, so nothing will overwrite it
before a human decides whether to fix `collect.py`'s title-matching regex.

**M-2 — REFUTED, not a real gap.** The finding claimed DD-47/48/49 exist only as prose in
`PRE_PHASE5_CLOSEOUT_REPORT_v1_0.md` and that "the actual running ledger" — identified here as
`OVERNIGHT_DECISION_LEDGER_2026-08-22.md`, "DD-1 through DD-44" — was never edited. Checked directly:
`OVERNIGHT_DECISION_LEDGER_2026-08-22.md` uses **D-NNN/F-NNN** numbering throughout (D-007 … D-011 …
D-016 …) and contains **zero** `DD-`-prefixed entries — it was never the DD registry. The actual DD
series (DD-1 through DD-46+) lives in `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md`, and DD-47,
DD-48, DD-49 are real, well-formed rows there, landed by PR #1517 (merged), citing commit `2670e61e2`
exactly as intended. The `CAPABILITY_MANIFEST.json` fingerprint for that artifact was independently
re-verified against the live file's own sha256 at write time and matches — no drift. Recorded here so
a future reader of this audit doesn't inherit the wrong artifact name.

**M-3 — accurate in spirit, imprecise in the specific claim; resolved.** No document currently on
`main` actually asserts an achieved count of 7 — `DD-7`'s own register row describes the *rule*
("green×7 declared by the CI history, no human"), not a tally, and
`PRE_PHASE5_CLOSEOUT_REPORT_v1_0.md` already said only "the clock restarts," with no number attached.
What was genuinely missing was the honest count itself, not a correction of a false one. Added: **3 of
7**, zero reds since the restart at #1515 (`2026-08-23T04:12:35Z`), with the three run IDs and
`head_sha`s it's built from — see `PRE_PHASE5_CLOSEOUT_REPORT_v1_0.md`'s own updated §3. No new smoke
has run since `05:12:32Z`, because `main` has not advanced since the overnight dispatch cadence
(`prp-night`) was retired — the clock does not advance on its own.

*Addendum ends. No prior section of this document altered — dispositions recorded, not retracted.*
