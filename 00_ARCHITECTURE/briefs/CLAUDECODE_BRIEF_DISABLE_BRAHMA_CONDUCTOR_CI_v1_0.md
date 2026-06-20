# Disable the obsolete Brahma Conductor scheduled CI (paste into Claude Code / Antigravity)

**Context:** `.github/workflows/brahma-conductor.yml` ("Brahma Conductor — Autonomous Build Driver") self-kicks
every 15 min via `schedule: cron '*/15 * * * *'` and FAILS on main every tick (~16s fast-fail; runs #136/#137/#138
red on the Actions tab). It drives the OBSOLETE brahma autonomous-build path (the same scaffolding behind the 10
worktree-bot/brahma PRs just closed as superseded by the L0/L1 closures). It is NOT a code gate — it doesn't
block merges or deploys (the Gaṇita Quality Gate + Deploy to Cloud Run are the real gates and are GREEN) — but
it paints main red on a schedule, eroding the CI signal (the persistent-red-noise problem). The autonomous
conductor is no longer the active build path; the orchestrator + manual closure passes superseded it.

**Goal:** stop the scheduled red without deleting history/auditability. Verify first, then make the minimal change.

---

## STEP 1 — Confirm it's genuinely obsolete (read-only, 2 min)

- Read `.github/workflows/brahma-conductor.yml` fully. Confirm: (a) the `schedule:` cron trigger, (b) it
  checks out main + auths to GCP via WIF + runs the brahma conductor driver, (c) `SMRITI_PATH:
  00_ARCHITECTURE/CONDUCTOR/brahma/smriti/build_state.yaml`.
- Open one failing run's log (Actions → "Brahma Conductor — Autonomous Build Driver" → run #138) and capture
  the actual failure step (likely the GCP WIF auth step or the driver finding retired state). Record it.
- Confirm nothing live depends on it: grep for `brahma-conductor-kick` (the repository_dispatch type) — if a
  Cloud Scheduler job still pings it, note that (it would also be failing and should be paused too).

## STEP 2 — Minimal change: remove the schedule (keep the workflow for manual use)

Preferred (reversible, preserves the workflow for `workflow_dispatch` manual runs):
- In `brahma-conductor.yml`, REMOVE the `schedule:` block (the `cron: '*/15 * * * *'`) and the
  `repository_dispatch` trigger if its Cloud Scheduler source is also retired. KEEP `workflow_dispatch` so it can
  still be run manually if ever needed.
- Add a top-of-file comment: `# Scheduled trigger disabled 2026-06-18 — brahma autonomous-build path superseded
  by the orchestrator + L0/L1 closure passes. Manual (workflow_dispatch) only. Re-enable schedule only if the
  autonomous conductor is reinstated.`

Alternative (if the whole workflow is dead): rename to `brahma-conductor.yml.disabled` OR delete it — but the
schedule-removal above is the safer default; do that unless you find a reason it must run.

## STEP 3 — Also pause the Cloud Scheduler backup trigger (if it exists)

The workflow has a `repository_dispatch: [brahma-conductor-kick]` "Cloud Scheduler Praharī backup trigger." If a
GCP Cloud Scheduler job still fires `brahma-conductor-kick`, it'll keep poking a workflow that no longer
schedules itself. Check `gcloud scheduler jobs list` (asia-south1 + any region) for a brahma-conductor kick job;
if present, PAUSE it (`gcloud scheduler jobs pause <name>`). Log if found/paused. (Operator action — note it if
you can't run gcloud.)

## STEP 4 — PR + verify

- Open a small PR (`chore/disable-brahma-conductor-schedule` → main) with the workflow change. Body: the failing
  run evidence (Step 1) + the rationale (obsolete autonomous-build path, superseded by L0/L1 closures, PRs
  #190/#194/#195/#196/#199 closed).
- After merge: confirm on the Actions tab that no NEW "Brahma Conductor" scheduled runs appear after the next
  15-min tick (the schedule is gone). The red runs in history stay (audit), but no new red.
- Confirm the real gates are unaffected: Gaṇita Quality Gate + Deploy to Cloud Run still run + green on the next
  push.

Report back: the failure cause you found, the workflow change made, whether a Cloud Scheduler kick job existed
(+ paused), and confirmation no new scheduled Brahma run fired post-merge.

**Net effect:** main's Actions tab stops showing scheduled red every 15 min; CI signal becomes trustworthy
(only real gates show), with the workflow preserved for manual re-use and full history intact.
