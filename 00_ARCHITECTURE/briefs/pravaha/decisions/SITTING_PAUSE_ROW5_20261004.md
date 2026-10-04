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
  - "1.1b (2026-10-04, steward SIT-PAUSE-NOTE-FIX M20261004T003626-2454): the password-reset recommendation REMOVED (rotation ruled out); option A is now a REFRESH from Secret Manager with the exact URL form and percent-encoding rules; the statement that the steward did not touch the credential overnight added."
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
- There is no written re-arm procedure for this particular login, and none is needed: a valid credential for the same login already exists in the governed place (see the update below). **Resetting or rotating the `postgres` password is ruled OUT** (steward and Suvarṇa): it would break Suvarṇa's own executors hours before their window.

## Update (steward, 00:45Z 2026-10-04): the real position is better than the diagnosis above
Suvarṇa probed and their administrator login WORKS as `postgres` from the governed Google Secret Manager secret `cloudsql-postgres-admin-password` (project `madhav-astrology`, latest version — names only; no value was read for this note). So a valid credential exists and the database is fine. Only OUR copy — the GitHub environment secret `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL` (environment `data-plane-production-cutover`), last changed 2026-09-24 — is stale. The remedy is to REFRESH that secret from the governed source. **No rotation.**

**The steward did not touch the credential overnight, on purpose:** moving or changing a credential is the owner's act, and the update train runs after Suvarṇa's window settles anyway, so nothing was lost by waiting.

## Ways forward (what each needs from you)
- **A (recommended) — refresh the GitHub environment secret from the Secret Manager secret; nothing is rotated.** Either you do it yourself in your morning, or you say "steward, do it" and the steward pipes the value across in ONE pipeline with nothing printed, nothing in a command line and no file (stdin only). Then the steward re-grants the temporary permission (act 11) with a NEW 2-hour expiry and re-runs the same reviewed create-roles job.
  - **The exact form the one-shot script expects** (it parses the secret once into the standard database connection settings; it refuses anything else): `postgresql://postgres:<PASSWORD, percent-encoded>@127.0.0.1:5432/amjis` — scheme `postgres://` or `postgresql://`; user `postgres`; host exactly `127.0.0.1` (or `localhost` / `[::1]`) because the workflow's Cloud SQL proxy listens on 127.0.0.1:5432; database `amjis`; a single host (no commas); NO `host=`, `hostaddr=` or `service=` option (refused); `?sslmode=…` is allowed but not needed.
  - **Percent-encoding:** the password must be encoded for URL use. The script takes the text after the LAST `@` as the host part and decodes the password with a standard URL decoder, so a raw `@`, `:`, `/`, `?`, `#`, `%`, space, `[` or `]` in the password would break the parse — encode EVERY character that is not a letter or digit as `%XX` (the one-liner below does this). A trailing newline from Secret Manager must be stripped.
  - **For the steward (owner's say-so only; not run by me):** `gcloud secrets versions access latest --secret=cloudsql-postgres-admin-password --project=madhav-astrology | python3 -c 'import sys,urllib.parse as u; pw=sys.stdin.read().rstrip("\n"); sys.stdout.write("postgresql://postgres:%s@127.0.0.1:5432/amjis" % u.quote(pw, safe=""))' | gh secret set DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL --env data-plane-production-cutover --repo Marsys-Technologies/Madhav` — the value travels only through the pipe (stdin of `gh secret set`, which reads it when no value is given); nothing is echoed. Check afterwards with `gh secret list --env data-plane-production-cutover` (the "updated" time changes; the value is never shown). The re-run of create-roles is the real proof; if the login is still rejected the run stops before any statement, exactly as before.
- **B — the runbook's option B from this machine under your identity**, using the same governed Secret Manager secret in-process. Nothing enters GitHub; the audit log shows only your identity.
- **C — a dedicated temporary administrator login** (the Pūrṇa pattern). Slowest: new reviewed code. Not recommended.
Either way the credential stays out of every log and every message. After row 5 the stored GitHub copy can be removed again if you want that route closed.

## Timing (Suvarṇa's schedule)
- Suvarṇa's S-L1 window OPENS 07:30Z today (about 3–5 hours to "SETTLED-1" or an abort). From 06:30Z our side stops: no merge to main, no work on the main chart, nothing under the Kāla paths, until "SETTLED-1 received AND the dasha re-pin is merged".
- Rows 5–6 (create the two logins, the approval environment and the proof workflow) can run before 06:30Z, or after SETTLED-1.
- The update train (#2867 → #2919 → #2999, heads 448ca5328 / fb3f5b1a9 / e44f9fe2d, untouched meanwhile) and the protected window run AFTER SETTLED-1 and the re-pin.
- On restart the earlier read-only checks (rows 2–3) are taken again, because main will have moved.

## What I need from you
One decision: option A (refresh, either by you or on your word by the steward) or B, and, separately, whether to keep or revoke the Firebase-agent exception.
