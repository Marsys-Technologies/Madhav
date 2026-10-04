---
artifact: SITTING_PAUSE_ROW5_20261004
version: "1.1"
status: RECORD — for the owner's morning
date: 2026-10-04
paused_at: "2026-10-04T00:32Z"
written_by: "Stream B (madhav-8b) at the steward's request (SIT-PAUSED-ROW5)"
audience: "the owner, reading in the morning"
evidence: "/Users/Dev/pravaha/run/sitting-20261003/manual/{row5-create-roles.txt, act11-removal-and-inventory.txt, act3.txt, act4.txt, act10.txt, act7-live-proof.txt, act3-declared-exception.txt}"
changelog:
  - "1.0 (2026-10-04): recorded."
  - "1.1 (2026-10-04, steward ST-SCHEDULE-SL1 M20261004T003602-7503): Suvarṇa's S-L1 schedule folded in; the stale-secret finding (their administrator login works from Secret Manager; only our GitHub environment secret is stale) replaces the password-reset ways forward with the owner's two options A/B."
---

# The protected-window sitting is paused at row 5 — nothing is broken, one decision is needed

## Bottom line
The first half of the sitting is done and checked. At the first step that needs the database administrator's login (row 5, creating the two new database logins), that login was rejected. Nothing was created, the temporary permission given for that step was removed again, and the system is exactly as safe as before. The sitting waits for one decision from you about how to refresh our copy of the administrator login.

## What is done (rows 1–4 and the set-up acts)
- Rows 1–3 checked and agreed: every pre-window check passed (the runner's all-pass evidence, the two second-pair-of-eyes reviews).
- The 1219 change from Suvarṇa and my revoke change (1302) are in production. `role_orchestrator` can no longer write to the Gochara windows table.
- A test-only fix (#3115) went in to stop an over-strict safety test from rejecting every pull request that adds a database change; without it the window's update train could not merge.
- Acts 3, 10 and 4 done and read back clean: the verification service account (no keys), its single permission, its one secret container.
- One security exception was declared and recorded (decisions/DECLARED_CONTROL_PLANE_EXCEPTION_20261003.md) for a Google-managed Firebase agent whose standing permission tripped the isolation check. A normal deploy afterwards ran green with the check passing. **Your morning decision: confirm it, or revoke it (one command) — see that note.**
- The three pull requests of the update train (#2867, #2919, #2999) are rebuilt on the current main and all six required checks are green. They are deliberately NOT merged yet: they must wait until the two new logins exist (a rule on the page).
- Row 4's merges are on main and recorded.

## What failed (row 5)
The one-shot "create roles" job connects to the database as the administrator account `postgres`, using a password stored as a GitHub secret. The database answered "password authentication failed". The job stopped before running anything.

## The exact state right now
- Database: no `gochara_verifier` and no `gochara_sealer` login exists. Nothing half-made.
- Secret Manager: no password version was written. The temporary permission (act 11) was removed and verified; only the verification account keeps its one permission.
- The update train is not merged. The sitting checklist is unchanged apart from a pause note at the top (page v1.19).

## Why it failed (what I can tell, without touching any password)
- It is NOT the Pūrṇa "disabled bootstrap" the deploy file talks about; that is a different login and a different secret.
- The `postgres` login exists and is allowed to log in. The stored GitHub secret was last changed on 2026-09-24 — the same day the database password was rotated and the secret refreshed. So the stored password no longer matches the database's real password (rotated later, or never proven to work). I cannot tell which without using the password, which I did not.
- There is no written re-arm procedure for this particular login. The only precedent is the 24 September fix: reset the `postgres` password with Cloud SQL admin rights and update the secret.

## Update (steward, 00:45Z 2026-10-04): the real position is better than the diagnosis above
Suvarṇa's own administrator login works, from the governed Secret Manager value. So the database is fine and no password needs resetting. Only OUR copy — the GitHub environment secret `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL`, last changed 2026-09-24 — is stale. Nobody reads or moves that credential in the meantime.

## Ways forward (what each needs from you) — the owner's two options
- **Option A — you refresh the GitHub environment secret yourself** from the governed Secret Manager value, in your morning. Nobody else touches it. After that the steward re-grants the temporary permission (new 2-hour expiry) and re-runs the same reviewed job.
- **Option B — you authorise the steward to move the value across without ever printing it** (Secret Manager → the GitHub environment secret, piped, never shown, never stored in a file). Same re-run afterwards.
- (Not recommended: a dedicated temporary administrator login on the Pūrṇa pattern — new reviewed code.)
Either way the credential stays out of every log and every message. After row 5 the stored copy can be removed again if you want the route closed.

## Timing (Suvarṇa's schedule)
- Suvarṇa's S-L1 window OPENS 07:30Z today (about 3–5 hours to "SETTLED-1" or an abort). From 06:30Z our side stops: no merge to main, no work on the main chart, nothing under the Kāla paths, until "SETTLED-1 received AND the dasha re-pin is merged".
- Rows 5–6 (create the two logins, the approval environment and the proof workflow) can run before 06:30Z, or after SETTLED-1.
- The update train (#2867 → #2919 → #2999, heads 448ca5328 / fb3f5b1a9 / e44f9fe2d, untouched meanwhile) and the protected window run AFTER SETTLED-1 and the re-pin.
- On restart the earlier read-only checks (rows 2–3) are taken again, because main will have moved.

## What I need from you
One decision: option A or B for refreshing our GitHub secret, and, separately, whether to keep or revoke the Firebase-agent exception.
