---
artifact: G1_E_DURABILITY_STATUS_v1_0
canonical_id: G1_E_DURABILITY_STATUS
version: 1.0
status: CURRENT — G1-E lane status; records what is BLOCKED and why,
  separately from the runbook so neither document can be misread as
  claiming more than it does
produced_during: Paripraśna P1 FOUNDATION, lane G1-E Durability
date: 2026-08-19
authoritative_side: claude
role: >
  States plainly, for anyone auditing G1-E later, exactly which parts of the
  roadmap line executed this session and which parts did not — and why the
  ones that didn't were deliberately withheld, not forgotten or failed.
  Written as its own document (not folded into the runbook) specifically so
  the runbook's existence — which is thorough, concrete, and immediately
  actionable — can never be mistaken for the drill having been run.
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/G1_E_DURABILITY_DR_RUNBOOK_v1_0.md (the runbook this status doc guards against being over-read)
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md (G1-E row)
  - 00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md (GAP-4)
changelog:
  - "1.0 (2026-08-19): initial status — PITR verify/enable and the restore drill BLOCKED pending separate authorization; export mechanism DONE and locally tested; provisioning against real infra NOT DONE."
---

# G1-E — Durability: session status

## Scope restriction this session operated under

This session's brief explicitly withheld authorization for enabling Cloud
SQL PITR, creating a scratch Cloud SQL instance, or executing a restore
drill — real production-infrastructure actions with real cost and risk,
reserved for a separate explicit go-ahead. No `gcloud sql` command was run
against the real `madhav-astrology` project at any point in this session.
No real GCP infrastructure was touched. Everything below that says "not
done" is not done *because of this restriction*, not because it was
attempted and failed.

## Done this session

| Item | Status | Evidence |
|---|---|---|
| RPO/RTO targets stated per tier | DONE | `G1_E_DURABILITY_DR_RUNBOOK_v1_0.md` §2 |
| Real table lists for both tiers, grounded in the actual schema (not assumed from naming) | DONE | Runbook §2; single source of truth at `platform/scripts/backup/irreplaceable_table_sets.sh` |
| Concrete, citable restore commands for both tiers | DONE | Runbook §3, §5 |
| Restore validation checklist | DONE | Runbook §4 |
| Independent logical-export script | DONE, implemented | `platform/scripts/backup/export_irreplaceable_tables.sh` |
| Restore/verify counterpart script | DONE, implemented | `platform/scripts/backup/restore_irreplaceable_tables.sh` |
| Export mechanism proven end-to-end against a real (throwaway, local) Postgres | DONE | Runbook §6.4 — export -> fresh restore target -> row-count + full-content match -> selectivity confirmed -> two real bugs found and fixed in the process |
| Cloud Scheduler + Cloud Run Job provisioning script for the real schedule | WRITTEN, not executed | `platform/scripts/backup/provision_logical_export_scheduler.sh` |

## Explicitly BLOCKED — not executed, pending separate authorization

**1. PITR verification against the real instance.** GAP-4's "disabled" finding
is dated 2026-07-19 and the baseline itself flags it "UNVERIFIED today,
presumed standing." This session did not re-run
`gcloud sql instances describe amjis-postgres --format=...backupConfiguration...`
against production to confirm the current state either way — that is a real
`gcloud sql` read against the real project, and even a read-only
`describe` call was treated as in-scope for the restriction rather than
carved out, since the brief's line is "do NOT run any `gcloud sql` command."
The exact command to run first, before anything else in this lane resumes,
is runbook §5 step 1.

**2. PITR enablement.** Runbook §5 steps 2–3 give the exact `gcloud sql
instances patch` command (`--enable-point-in-time-recovery
--transaction-log-retention-days=7`) and its verification. Not run.

**3. The restore drill.** PPR-33 requires "one restore drill executed at
G1... then quarterly." Runbook §3 gives the exact clone-and-extract commands
(`gcloud sql instances clone ... --point-in-time=...`) a drill would run,
against a scratch clone instance, never production in place. Not run — no
scratch Cloud SQL instance was created this session.

**4. Provisioning the logical export against real infrastructure.** The
script exists and works (proven locally, §6.4) but creating the actual GCS
bucket, service account, Cloud Run Job, and Cloud Scheduler trigger in
`madhav-astrology` was not attempted this session, consistent with "do not
touch any real GCP infrastructure." This is a lower-risk category than
PITR/the drill (no `gcloud sql` calls, no Cloud SQL instance mutation) but
was still left for an operator to run deliberately rather than executed
speculatively under a scope restriction whose spirit was clearly "nothing
touches real infra this session."

## What "ready to execute" means in practice

Everything in the runbook is written so that resuming this lane is: (a) get
the explicit authorization the brief withheld, (b) run runbook §5 to verify
then enable PITR, (c) run runbook §3's clone-and-extract sequence once as
the drill, recording the actual measured RTO against the checklist in §4,
(d) run `provision_logical_export_scheduler.sh` to wire the already-tested
export mechanism into real Cloud Scheduler. No further design or
table-classification work is needed first — that work is what this session
did.
