---
artifact: PRE_PHASE5_CLOSEOUT_REPORT
canonical_id: PARIPRASHNA_PRE_PHASE5_CLOSEOUT_REPORT
version: 1.0
status: CLOSED — PARTIAL BY DESIGN; the RETIRE train parked on a gate premise that proved false
authority: PARIPRASHNA_PRE_PHASE5_CLOSEOUT_PROMPT_v1_0 (native-authored, 2026-08-23)
executes: PARIPRASHNA_P3_P4_COMPLETENESS_AUDIT_AND_CLOSE_v1_0 + PARIPRASHNA_P3_P4_FINAL_CLOSURE_v1_0
---

# Paripraśna — pre-Phase-5 closeout report

*P3 and P4 are complete to the limit of what is verifiable; here is exactly what remains open, and
why each cannot close yet.*

## The three things most worth your attention

**1. The charter's own hard gate named a fix that does not exist.** §0 blocked the entire RETIRE
train — and therefore the irreversible deletion — on *"#1508's redirect-loop fix … merged, deployed,
and its redirect assertions observed green."* **#1508 contains no fix.** Its complete diff is a
468-line census document, an 11,438-line census JSON, and a 558-line census script: zero application
code. No redirect-loop fix exists anywhere on `main`.

This matters more than a citation error, because **the gate was satisfiable by observation**. Anyone
checking *is #1508 merged? deployed?* would have answered yes to both, opened P4-A, and lit the path
to an irreversible deletion having verified the gate exactly as written. Filed as **DD-47**.

*Mitigating, and verified:* `/consult` carries no redirect today, so the loop is **prospective, not
live**. Production is not in the hazard. The RETIRE train parks — which is what §0's own fallback
prescribes, and is a correct outcome, not a failure.

**2. The blocker everyone was waiting on was never the blocker.** The campaign had recorded the
smoke's permanent red as a stale `FIREBASE_ADMIN_CREDENTIALS` secret requiring a native credential
operation. The actual defect was in the probe: `tagConversationAsHarness` is documented *"Best-effort
— never fails the turn,"* and its `try/catch` honoured that for connection errors — but the
credential resolution sat **outside** the guard, and `envOrSecret` shells out to `gcloud`, which
throws on any runner without gcloud auth. **The one line that could kill the turn was the one line
the guard did not cover.** Fixed in **#1514**; the smoke has been green since (`32615067230`,
11/11). No credential was moved into CI, and none needed to be.

**3. The green×7 counter was reading the wrong artifact, and its clock restarts now.** A
`workflow_run` job checks out the default-branch tip, not the deployed commit. Smoke `32615193678`
labelled itself `0253f5e8e` at 03:22:42Z while production served `97d2b7312` — and `0253f5e8e`'s own
deploy did not begin until **03:30:21Z, eight minutes later**. Four runs showed 7–9 minute skew. The
counter that gates THE FLIP *and* the irreversible deletion was reading that. Fixed in **#1515**
(**DD-48**). Every green banked before that fix is of uncertain attribution, so **the honest green×7
clock starts from #1515, not before.**

**The current honest tally, re-derived from CI history directly (not carried forward from memory):
3 of 7, zero reds since the restart.**

| smoke run | `head_sha` | conclusion |
|---|---|---|
| `32617962733` @ 2026-08-23T04:28:33Z | `3a54918f4` | success |
| `32618696909` @ 2026-08-23T04:46:40Z | `68cde91e4` | success |
| `32619782448` @ 2026-08-23T05:12:32Z | `2670e61e2` | success |

No smoke has run since 05:12:32Z — `main` has not advanced (no new `Deploy to Cloud Run` to trigger
one) since the overnight tmux infrastructure (`prp-night`) was retired. **The flip clock has not
completed and does not advance on its own; it needs four more genuine deploy-triggered greens.**

## Disposition of the audit's gap ledger

| gap | state at closeout | how |
|---|---|---|
| BLOCKING-1 — un-PR'd census carrying the rollback-destroying finding | **CLOSED** | #1508 merged |
| BLOCKING-2 — smoke attributes results to an undeployed commit | **CLOSED** | #1515, with a can-fail detector |
| MATERIAL-1 — failure annotation cannot execute | **CLOSED** | #1511 |
| MATERIAL-2 — P3-C's only DB detector has never run | **CLOSED** | #1511 |
| MATERIAL-3 — smoke permanently red and unenforced | **DISSOLVED** | #1514; green since 03:19Z |
| MATERIAL-4 — DD-28/29/30 live only on a branch that must not merge | **CLOSED** | #1512 |
| MATERIAL-5 — stale precondition claim in the rollback pin | **CLOSED** | #1511 |
| MATERIAL-6 — DD-1's proof has no in-repo evidence | **CLOSED, with a correction** | #1516 |

**MATERIAL-6's correction is worth reading.** The circulating claim was *"13/13 can-fail proven."*
Running the battery's offline proof mode banks **7**, each with both halves recorded (`red_fired`
*and* `green_clean`). The other six are browser-lane and need a live surface this run did not drive.
The receipt now lives at a tracked path; `platform/.gitignore:21` is deliberately unchanged, because
routine run artifacts *should* be untracked — what was missing was a curated committed copy.

## Parked, with the reason each cannot close

**RETIRE train (P4-A → P4-B deletion → P4-C → P4-D) — PARKED.** Its gate's premise is false
(DD-47). The closeout deliberately did **not** write the redirect fix itself: that is
safety-critical auto-rollback-path code whose only purpose is unblocking an irreversible deletion,
and it is a native call. **No deletion occurred. Nothing in the legacy tree was touched.**

**P3-F (THE FLIP) — PARKED, time-gated.** Six preconditions, verified at flip time. Two cannot be
met today: green×7 needs seven greens on real cadence and its clock restarts at #1515; and the
ceiling reject demonstration has never been performed.

**Ceiling reject demonstration — PARKED, with a runbook.** `CEILING_REJECT_DEMONSTRATION_RUNBOOK_v1_0.md`
is ready to run in a supervised session. What *is* now proven: the refusal path works and its
detectors are real — neutralising `if (!spend.allowed)` turned exactly three tests red (flag-flip,
per-turn breach, daily breach) while the other seven stayed green; reverted clean. That upgrades the
audit's *"the refusal path is unexercised."* It **is** exercised; what is missing is a live
observation.

Why not executed autonomously: the drill needs `MARSYS_SPEND_CEILING_PER_TURN_USD` on a revision,
and `gcloud run deploy` mutates the service template even with `--no-traffic`. Earlier the same
night that exact mechanism disabled Paripraśna in production for ~80 minutes. A template carrying a
near-zero ceiling would refuse **every** production turn. It blocks nothing — the flip is time-gated
regardless. *The runbook records the one fact that makes this cheap: the ceiling check is a
**pre-dispatch projection**, so the refusal costs no LLM spend at all.*

**#1496 (P4-H) and #1500 (P4-G) — RE-PARKED on evidence.** D-011's own falsifier was tested against
`main@0253f5e8e` and **both limbs still fail**: `metadata_json` has 19 consumer files (not one), and
no client can transmit a dispute `comment`. Both writers named in the ruling still replace the column
wholesale — `conversation_writer.ts:74` and `pariprashna/store/writer.ts:77`. P4-G re-parks
consequentially: it reaches no reader, and its dispute answer depends on P4-H's intact root cause.
Re-park records are posted to both PRs.

*A method note, recorded because it nearly produced a false all-clear:* a first grep for
`metadata_json = EXCLUDED.metadata_json` matched only **one** writer and would have suggested the
second had been fixed. It had not — `store/writer.ts` aligns its assignment with extra whitespace.
The narrow pattern had changed, not the code.

## Verifications performed

- **Production ≡ main — TRUE, verified directly.** The serving image is tagged with the full git
  sha: `amjis-web:0253f5e8e128bfbabc90baedc2d9ec2880edd699`, 100% traffic to `amjis-web-01692-bt9`,
  identical to `origin/main`. This is a *direct* check, not the inference the overnight run's
  disputed claim rested on. It is a point-in-time fact and does not retroactively settle §5.1.
- **Worktree hygiene — 13 stale worktrees removed** after per-path verification. One,
  `prp-close`, held **staged** content that was **behind** `main`: its index would have reverted the
  decision ledger by 1,442 lines, the run report from `v1.0 FINAL` to `v0.1 IN PROGRESS`, and the
  rollback pin from `v1.2` to `v1.1`. Nothing in it was unlanded. **The danger is precisely that it
  looks like work.** This is DD-44 recurring by a second mechanism — not a killed agent, but lanes
  that merged normally — and is filed as **DD-49** with the argument for automating DD-44's check.
- **Lease hygiene — clean.** All Paripraśna leases closed. This run declared one scope and releases
  it at close.
- **Report/repo divergence — the standing-RED coordination notice was stale and actively
  dangerous.** It told other campaigns a red on the smoke was "not a regression in your work." That
  is now false, and believing it would let a genuine red be waved through. Retracted at the same
  visibility it was posted, with the attribution-skew warning attached.

## What this run must NOT be read as closing

Stated plainly, per the charter's §2, not as a footnote. **None of these gate anything above, none
were forced, none were silently dropped.**

- **AC-15** — the native's own week of daily use. Never closes by agent work. The DD-1 battery
  substitutes as P4's gate **only**; a later NO still spawns its own remediation wave.
- **P4-D grading** is machine-graded (DD-8) — never the native's judgment, and never to be reported
  as such.
- **P4-B reversibility asymmetry** — moot: no deletion occurred. Had it landed, an AC-15 NO
  afterward would be revert-recoverable, **not costless**.
- **DD-26** — tiered Gemini pricing; inputs >200K stay under-priced. Known, disclosed, open.
- **Any newly minted Firebase key** — out of scope; old keys want a deliberate review this run did
  not perform.
- **P5 itself** — gated by time, not work. **Nothing here starts its clock early, and finishing this
  list is not a reason to read "P5 can start now" backwards into it.**
- **#1513/DD-46 and the Nirmāṇa Build Tracker campaign** — explicitly out of scope; untouched.

## Ledger

**Merged this run:** #1514 (probe contract), #1515 (BLOCKING-2 / DD-48), #1516 (MATERIAL-6).
**Re-parked:** #1496, #1500. **Untouched by scope:** #1513.
**New DD entries:** DD-47, DD-48, DD-49. **Registry:** one batched write, fingerprint rotated
`55a7beb4…` → `4c547c7b…`; `drift_detector` re-run at **79 findings, exit 3** — the baseline held,
and **`DRIFT_BASELINE_MAX` was not raised.**

**No gate or lint was disabled to make anything pass. No credential was rotated or moved into CI.
No schema migration was executed. No native ruling was reversed. The native's real chart
(`482012f1-…`) was never touched.**
