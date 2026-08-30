---
canonical_id: PARIPRASHNA_ASSURANCE_CONTROL_ARCHIVE_PROVENANCE
version: 1.0
status: ARCHIVED
date: 2026-08-30
---

# Provenance — Paripraśna Experience Assurance control-plane archive

This directory holds the durably-archived system of record for the Paripraśna Experience
Assurance Programme v3.0 campaign, taken at final closeout after the campaign was sealed.

## What this is

- `control-plane.sqlite3` — a live `.backup` (sqlite's own backup API, not a raw file copy) of
  `~/.pariprashna-assurance-control/control-plane.sqlite3`, taken 2026-08-30 while the control
  plane's launchd service was still running and healthy. **734 events**, matching the count the
  live tracker reported at seal. Confirmed via `SELECT COUNT(*) FROM events` against the copy.
- `PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN_v2_0.md`, `CLOSEOUT_KICKOFF_PROMPT_v2.txt` — the
  operational plan and kickoff prompt used to drive the closeout session that ultimately sealed
  the campaign.

## What was deliberately excluded

- `local-credentials.json`, `p1-credentials.json`, `p2-credentials.json` — the actor bearer
  tokens. Never committed, regardless of the native's secret-scan deferral ruling (see
  `NATIVE_DECISION_SECRET_SCAN_DEFERRAL_v1_0.md`) — that ruling deferred remediation *effort* on
  already-flagged pre-existing findings; it did not authorize introducing new raw credential
  material into the repository, and this archive doesn't need to.
- Release-manifest and recovery-snapshot directories under `~/.pariprashna-assurance-control-*` —
  operational backups, not the system of record itself; left on disk, not archived to the repo.

## Credential-safety check on what WAS archived

`control-plane.sqlite3`'s `actors` table stores only `token_hash` (a one-way hash of each
actor's bearer token, per the schema — `CREATE TABLE actors (... token_hash TEXT NOT NULL
UNIQUE)`), never the raw token. Confirmed by direct query before archiving. No other table in
this database stores credential material. `bash platform/scripts/governance/secret_scan.sh` was
run against this archive as part of the same PR that adds it.

## Sealed state at archive time

Gates CG-0…CG-7 all CLOSED. Campaign completion 100.0%. Tracker replay integrity `ok: true`
(`65a4a88e1675e4aebc2658dd…`). Full account:
`00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_V3_FINAL_CLOSE_REPORT_v1_0.md`.

## Service disposition

The six launchd services that served this control plane
(`com.marsys.pariprashna-assurance-control`, `-trackerd`, `-serve`, `-watchdog`,
`-assurance.shadow.sync`, `-assurance.shadow.dashboard`) were stopped after this archive was
taken, once this PR was pushed. Their plists were moved (not deleted) to
`~/Library/LaunchAgents/_archived-pariprashna-20260830/` on the local machine — that move is a
local filesystem operation, not a repo change, and is not represented in this commit.
