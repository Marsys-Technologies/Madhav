---
artifact: SITTING_PAUSE_ROW5_20261004
version: "1.0"
status: RECORD — for the owner's morning
date: 2026-10-04
paused_at: "2026-10-04T00:32Z"
written_by: "Stream B (madhav-8b) at the steward's request (SIT-PAUSED-ROW5)"
audience: "the owner, reading in the morning"
evidence: "/Users/Dev/pravaha/run/sitting-20261003/manual/{row5-create-roles.txt, act11-removal-and-inventory.txt, act3.txt, act4.txt, act10.txt, act7-live-proof.txt, act3-declared-exception.txt}"
changelog:
  - "1.0 (2026-10-04): recorded."
---

# The protected-window sitting is paused at row 5 — nothing is broken, one decision is needed

## Bottom line
The first half of the sitting is done and checked. At the first step that needs the database administrator's login (row 5, creating the two new database logins), that login was rejected. Nothing was created, the temporary permission given for that step was removed again, and the system is exactly as safe as before. The sitting waits for one decision from you about how to get a working administrator login.

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

## Ways forward (what each needs from you)
1. **Reset the `postgres` password, update the secret, re-run (recommended; smallest change).** You (or the steward under your account) reset the password in Google Cloud SQL, store the new password in the GitHub secret `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL`, then the steward re-grants the temporary permission with a fresh 2-hour expiry and re-runs the same reviewed job. Afterwards: set the password again to a throw-away random value (or delete the secret) so the administrator route is closed again.
2. **Same reset, but run from your own machine instead of GitHub.** Same password reset; the steward connects under your Google identity, runs the same reviewed statements, closes the connection. The password never enters GitHub, but the audit log then shows only your identity.
3. **A dedicated temporary administrator login** (the pattern used for Pūrṇa). Safest in principle, slowest: new code that needs a review round. Not recommended tonight.

Whichever you choose, it is a password/infrastructure action that only you, or the steward on your explicit say-so, should perform.

## Timing
Rows 5–9 (create the logins, merge the train, run the protected update, verify) must finish before Suvarṇa's next upstream window (W1) begins, or else start after their window is settled; the two must not overlap. The steward lifted Suvarṇa's freeze at 00:32Z, so a restart is possible as soon as there is a working login. On restart the earlier read-only checks (rows 2–3) are taken again, because main has moved since.

## What I need from you
One decision: option 1, 2 or 3 (I recommend 1), and, separately, whether to keep or revoke the Firebase-agent exception.
