---
artifact: G1_E_DURABILITY_DR_RUNBOOK_v1_0
canonical_id: G1_E_DURABILITY_DR_RUNBOOK
version: 1.0
status: CURRENT — G1-E lane deliverable; PITR enablement and the restore
  drill this runbook specifies are UNEXECUTED, blocked on separate
  native authorization (see §5 and the companion
  G1_E_DURABILITY_STATUS_v1_0.md)
produced_during: Paripraśna P1 FOUNDATION, lane G1-E Durability
date: 2026-08-19
authoritative_side: claude
role: >
  Discharges the RPO/RTO + DR-runbook half of the G1-E roadmap line
  (PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md row "G1-E Durability" /
  PPR-33 / GAP-4). States exactly what "restore" means for this system,
  table set by table set, with the precise gcloud commands a person with
  restore authorization would run — so this document is immediately
  actionable the moment that authorization lands, without a second
  investigation pass. Does not itself enable PITR or execute a drill.
relates_to:
  - 00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md §4.9 (PPR-33 — the requirement this runbook satisfies the documentation half of)
  - 00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md (GAP-4 — PITR disabled, no restore drill)
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md (G1-E row)
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/G1_E_DURABILITY_STATUS_v1_0.md (companion status doc — what remains blocked and why)
  - platform/scripts/backup/irreplaceable_table_sets.sh (single source of truth for the table lists this doc cites)
  - platform/scripts/backup/export_irreplaceable_tables.sh / restore_irreplaceable_tables.sh (the independent logical-export mechanism, §6)
  - platform/supabase/migrations/575_pariprashna_chart_subject_consent.sql (G1-B — the consent/subject-rights tables in the ledger set)
  - platform/supabase/migrations/471_retire_mcp_predictions.sql (why mcp_predictions is explicitly excluded, §2.3)
changelog:
  - "1.0 (2026-08-19): initial runbook — table classification grounded in the real migrations (not assumed), RPO/RTO targets per PPR-33, concrete restore commands for both tiers, independent-export mechanism documented, PITR/drill execution explicitly deferred to separate authorization."
---

# G1-E — Durability: RPO/RTO + Disaster Recovery Runbook

## 0 — What this document is, and is not

This is the RPO/RTO statement and DR runbook PPR-33 requires. It specifies,
for every table this system's data lives in, how much data loss is
tolerable (RPO) and how long recovery may take (RTO), and gives the exact
commands to execute a restore.

**It is not a record that PITR is enabled or that a drill has run.** As of
this writing, per `PARIPRASHNA_ASBUILT_BASELINE_v1_0.md` GAP-4, Cloud SQL
PITR on the production instance is **disabled** and no restore drill has
ever been executed. Enabling PITR and running the drill are real
production-infrastructure actions with real cost/risk and are withheld from
this session pending a separate, explicit native go-ahead — see
`G1_E_DURABILITY_STATUS_v1_0.md` for the exact commands ready to run and why
they were not run here. This runbook is written so that when that
authorization lands, executing it is a matter of running the commands below
in order, not re-deriving them.

## 1 — The instance this runbook targets

Confirmed live (not assumed) via `gcloud sql instances list` — see
`00_ARCHITECTURE/CHAT_V2_STAGING_INVESTIGATION.md`:

| Field | Value |
|---|---|
| GCP project | `madhav-astrology` |
| Region | `asia-south1` |
| Cloud SQL instance | `amjis-postgres` |
| Database engine | PostgreSQL 15 |
| Database name | `amjis` |
| Instance connection name | `madhav-astrology:asia-south1:amjis-postgres` |

Exactly one Cloud SQL instance exists in the project — there is no separate
staging/DR instance today. A restore drill therefore targets a **clone**,
never the live instance in place, until a specific incident calls for an
in-place restore.

## 2 — Table classification (grounded in the real schema, not assumed)

The roadmap line groups tables into two RPO/RTO tiers: "ledger+conversations"
(≤1h / ≤4h) and "layer tables" (24h / 24h). The table lists below were built
by reading `platform/supabase/migrations/*.sql` and the legacy
`platform/migrations/*.sql` directly (`CREATE TABLE` / `DROP TABLE`
statements), then cross-checked against the actual live writer code (grep
for `INSERT INTO`) rather than assumed from naming convention — the same
"real detector, not a proxy" discipline CLAUDE.md §N.7/§N.8 requires of
every other status/grade signal in this codebase.

### 2.1 — Ledger + conversations tier (RPO ≤ 1h, RTO ≤ 4h)

This tier is anything that records a real-world event, decision, or piece of
human-authored content — a chart rebuild can never regenerate a lost
conversation turn or a lost consent record, because nothing external to the
database describes what they contained.

**Conversations (the native's/cohort's actual dialogue):**
`conversations` · `conversation_messages` · `conversation_message_embeddings`
· `conversation_branches` · `conversation_folders` ·
`conversation_folder_members` · `conversation_shares` ·
`conversation_summaries` · `project_conversations`

**Ledger (consent, audit, prediction/outcome/calibration history):**
- Consent & subject-rights (G1-B, migration 575 — legal/consent state):
  `chart_subject_consent` · `chart_subject_consent_events` ·
  `chart_subject_exclusions` · `chart_subject_deletion_disputes` ·
  `chart_subject_deletion_tombstones`
- Prediction / outcome / calibration ledger (the substrate the L5 Mīmāṃsā
  calibration loop depends on — empirical, accrues from lived reality, never
  recomputable from ephemeris or classical texts):
  `brahma_prospective_ledger` (confirmed live writer:
  `platform/src/lib/lel/prospective_ledger.ts`) · `mimamsa_predictions` ·
  `mimamsa_calibration` · `mimamsa_calibration_snapshot` ·
  `mimamsa_intervention_ledger` · `mimamsa_adjudication_log` ·
  `mcp_prediction_outcomes`
- Audit trail: `audit_log` · `audit_events` · `admin_audit_log`

These 24 tables are the **two irreplaceable table sets** the independent
logical export (§6) covers — "two" meaning the conversations family and the
ledger family, matching this tier's own two-part name in the roadmap line.

### 2.2 — Layer tables tier (RPO/RTO 24h)

Every `chart_*` / `ganita_*` / `bodha_*` / `kala_*` / `phala_*` writer output
from the L1–L5 build (the `ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` orchestrator
asset outputs, per CLAUDE.md §N.1/§E): `chart_facts`, `chart_facts_history`,
`chart_facts_supersedence`, `chart_fact_identity`, `chart_dashas`,
`chart_divisionals`, `chart_panchanga_cache`, `ganita_dashas`,
`ganita_positions`, all `bodha_*` tables (Bodha/L2), all `kala_*` tables
(Kāla/L3), all `phala_*` tables (Phala/L4), and the deterministic L5
structural outputs (`mimamsa_multipliers`, `mimamsa_pool_contributions`,
`mimamsa_qa_eval`, `mimamsa_snapshot_cosign`, `mimamsa_export_log`).

The 24h target is generous **because this tier has a second, independent
recovery path that the ledger/conversations tier does not**: every one of
these tables is a deterministic function of `chart_facts` + birth parameters
+ classical computation rules (CLAUDE.md §N.4 "deterministic-first"). If a
layer table is lost or corrupted for a chart whose `chart_facts` and
`birth_params` survive, the FROZEN orchestrator ("click Build", §N.2) can
regenerate it from scratch — slower than a database restore, but a real,
already-built path that does not depend on Cloud SQL backups at all. A
Cloud SQL restore is still the first resort (it is faster and does not
consume ephemeris-service quota); the rebuild path is what justifies the
looser 24h number rather than matching the ledger tier's 1h/4h.

### 2.3 — Tables deliberately excluded from active DR scope, and why

- **`mcp_predictions`** — retired (migration `471_retire_mcp_predictions.sql`,
  2026-07-28). The table no longer exists in the live schema; only
  `mcp_predictions_retired_backup` remains, a dead historical snapshot of
  12 content-empty rows captured at retirement time. Not exported on a
  recurring basis — it cannot change, and restoring it recreates a table
  name (`mcp_predictions`) that migration 471 deliberately removed. If it is
  ever needed for audit, it is a single `pg_dump --table=mcp_predictions_retired_backup`
  away, run manually.
- **`chart_grants`** — access-control state (roles/RLS), a G1-C concern, not
  scoped to this lane.
- Any table not listed in §2.1 or §2.2 above and not covered by this section
  should be treated as **unclassified** — flag it to native rather than
  assuming it silently belongs to whichever tier seems safer. This runbook
  is a snapshot of the schema as read on 2026-08-19; a new table added later
  needs a deliberate classification, not a default.

## 3 — What "restore" means, concretely, tier by tier

Cloud SQL exposes exactly two DB-level restore primitives once PITR is
enabled: a full-instance point-in-time clone, and a restore from a discrete
automated/on-demand backup. Neither operates on a subset of tables — Cloud
SQL restores the whole instance (or a whole clone of it) to a point in time.
**Table-level granularity comes from the independent logical export (§6),
not from Cloud SQL PITR.** This is precisely why the roadmap line asks for
both: PITR is the fast, low-RPO, whole-instance safety net; the logical
export is the granular, Cloud-SQL-independent second line of defense.

### 3.1 — Ledger + conversations: RPO ≤ 1h, RTO ≤ 4h

**Primary mechanism — PITR clone-and-extract** (does not disrupt the live
instance; the clone is a separate instance, queried and then torn down):

```bash
# 1. Clone the production instance to the desired point in time (ISO-8601,
#    UTC). This creates a NEW, separate Cloud SQL instance — production is
#    never touched by this step.
gcloud sql instances clone amjis-postgres \
  amjis-postgres-restore-$(date -u +%Y%m%dT%H%M%SZ) \
  --project=madhav-astrology \
  --point-in-time="2026-08-19T12:00:00Z"

# 2. Once RUNNABLE, connect to the clone (Cloud SQL Auth Proxy or an
#    authorized network) and extract only the affected rows/tables — do NOT
#    swap the clone in for production wholesale for a partial-corruption
#    incident; pg_dump/pg_restore the specific ledger/conversations tables
#    (§2.1) from the clone into production, scoped to the actual blast
#    radius (e.g. by chart_id or by a known corruption time window).
cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres-restore-<ts> --port=5434 &
pg_dump "postgresql://<user>@127.0.0.1:5434/amjis" \
  -Fc --table=conversations --table=conversation_messages \
  -f /tmp/pitr_extract.dump
# ... pg_restore the extracted tables/rows into production, or hand the
# extracted dump to the incident owner for row-level reconciliation.

# 3. Tear down the clone once the extract is verified — it is billed as a
#    full second instance while it exists.
gcloud sql instances delete amjis-postgres-restore-<ts> --project=madhav-astrology
```

**Catastrophic fallback — full in-place restore** (production is
unavailable for the duration; use only if the primary instance itself is
lost, not for a data-content incident):

```bash
gcloud sql backups list --instance=amjis-postgres --project=madhav-astrology
gcloud sql backups restore <BACKUP_ID> \
  --restore-instance=amjis-postgres \
  --backup-instance=amjis-postgres \
  --project=madhav-astrology
```

**Independent fallback — logical export** (used when PITR itself is the
thing that failed, was misconfigured, or its retention window has already
rolled past the needed point in time — the exact GAP-4 failure mode this
lane exists to hedge against): restore the most recent `ledger_*.dump` /
`conversations_*.dump` produced by §6's export into a scratch database via
`restore_irreplaceable_tables.sh`, then reconcile forward. RPO on this path
is bounded by the export cadence (hourly, §6.3), which is why it is
provisioned on the same cadence as the ledger/conversations RPO target
rather than a looser one.

### 3.2 — Layer tables: RPO/RTO 24h

```bash
# Same PITR clone mechanism as §3.1, coarser point-in-time granularity
# (daily automated backup timestamp is sufficient — no need to target an
# arbitrary minute for tables with a deterministic-rebuild fallback).
gcloud sql instances clone amjis-postgres \
  amjis-postgres-restore-$(date -u +%Y%m%dT%H%M%SZ) \
  --project=madhav-astrology \
  --point-in-time="<yesterday's backup timestamp>"
# Extract the affected chart_*/bodha_*/kala_*/phala_*/mimamsa_* tables the
# same way as §3.1 step 2, or —
```

```bash
# ALTERNATIVE, equally valid for this tier only: rebuild via the FROZEN
# orchestrator instead of touching Cloud SQL at all. Requires chart_facts +
# birth_params to be intact (i.e. this table itself, or an upstream backup
# of it, survived). This is a product action ("click Build" for the
# affected chart), not a gcloud command — see
# ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 for the WriterBase contract this
# invokes.
```

## 4 — Restore validation checklist (any tier)

A restore is not "done" when `pg_restore`/the clone reaches RUNNABLE — it is
done when this checklist passes:

1. **Row counts match expectation.** Compare `SELECT count(*)` per restored
   table against the last known-good count (from monitoring, or from the
   pre-incident export's own TOC — see §6.2's fail-loud table-presence
   check, which doubles as a row-count witness).
2. **Spot-check content, not just counts.** A restore that matches row
   counts but has silently substituted rows (e.g. an ordering bug) is worse
   than an obvious failure. Pull 3–5 known rows by primary key and diff
   field-by-field against a pre-incident reference if one exists.
3. **FK/constraint integrity holds.** Run `\d+` / a constraint-validation
   pass on the restored tables; a partial restore (some but not all tables
   in a dependency chain) can leave orphaned foreign keys.
4. **The consuming code path actually reads correctly**, not just that the
   table looks populated — e.g. for `chart_subject_consent`, exercise
   `resolveSubjectConsent` (the live consumer, `safety_gate.ts`) against a
   restored chart, not just a raw SELECT.
5. **Record the drill/incident** in this document's own changelog (or the
   relevant incident log) with: what was restored, from what point in time,
   how long it took (the actual RTO measurement, feeding PPR-33's two-week
   baseline), and this checklist's pass/fail per item.

## 5 — PITR: verification and enablement commands (NOT YET RUN)

**Status:** disabled, per GAP-4 (last verified 2026-07-19, presumed standing
— see §1 of the companion status doc for the honest "unverified today"
caveat). Enabling it is withheld from this session; see
`G1_E_DURABILITY_STATUS_v1_0.md` for why. The commands below are exactly
what an operator with go-ahead runs, in order:

```bash
# 1. Verify current state first — do not assume GAP-4's 2026-07-19 finding
#    is still accurate; it may have drifted either direction since.
gcloud sql instances describe amjis-postgres \
  --project=madhav-astrology \
  --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled,settings.backupConfiguration.transactionLogRetentionDays,settings.backupConfiguration.enabled,settings.backupConfiguration.startTime)"

# 2. If disabled, enable automated backups (a PITR prerequisite) + PITR
#    itself + a transaction-log retention window that comfortably covers the
#    tightest RPO target in this runbook (1h) with margin for detection lag
#    — 7 days is Cloud SQL's practical default ceiling for cost-sensible
#    retention and is what this runbook recommends.
gcloud sql instances patch amjis-postgres \
  --project=madhav-astrology \
  --backup-start-time=02:00 \
  --enable-point-in-time-recovery \
  --transaction-log-retention-days=7

# 3. Confirm it actually took effect — do not trust the patch command's own
#    exit code as the detector (§N.8: a status claim needs a real check
#    behind it). Re-run the describe command from step 1 and confirm
#    pointInTimeRecoveryEnabled now reads True.
gcloud sql instances describe amjis-postgres \
  --project=madhav-astrology \
  --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled)"
```

## 6 — Independent logical export mechanism

Implemented and locally tested (§6.4) as of this lane. Not yet provisioned
against real Cloud SQL/Cloud Scheduler infrastructure — see the companion
status doc.

### 6.1 — Why a second, independent mechanism at all

PITR is a single subsystem inside Cloud SQL. GAP-4 exists precisely because
that subsystem was silently off with nobody noticing for an unknown period.
A backup mechanism that depends entirely on Cloud SQL's own backup
configuration being correct has exactly one point of failure. The logical
export in `platform/scripts/backup/export_irreplaceable_tables.sh` is a
plain `pg_dump` against the running database — it does not read or depend on
any Cloud SQL backup/PITR setting, so a Cloud-SQL-level misconfiguration
(the GAP-4 failure mode) cannot silently take this mechanism down with it.

### 6.2 — What it does, and the defect it was built to survive

`export_irreplaceable_tables.sh --set {conversations|ledger|both}` produces
one `pg_dump -Fc` (custom format, compressed) file per set plus a `.sha256`
sidecar, in `$OUT` (or uploaded to `$GCS_BUCKET` if set). The table lists
live in one place, `irreplaceable_table_sets.sh`, so this script and the DR
runbook's §2.1 table lists cannot drift apart silently.

**A real defect was found and fixed while building this**, worth recording
here because it is exactly the class of bug CLAUDE.md §N.8 exists to name:
`pg_dump` given multiple `--table` flags does **not** error when some (not
all) of the requested table patterns match zero relations — it silently
dumps whatever it did find and exits 0. Verified directly (pg_dump 15.17): a
request for 9 conversations-set tables against a database containing only 1
of them produced a "successful," non-empty `.dump` file with no error, no
warning, no non-zero exit — an export that looked completely fine while
silently missing 8 of 9 tables. The fix: after every dump, the script reads
the archive's own table of contents back via `pg_restore --list` and
confirms every requested table actually landed in it, failing loudly and
naming the missing tables if not. A size-only sanity check (dump file isn't
suspiciously small) would **not** have caught this — 1-of-9 tables is not an
empty file, it is silently wrong content.

### 6.3 — Scheduling

Not yet provisioned (§ status doc). `provision_logical_export_scheduler.sh`
(untested against real infra, written and ready) sets up: a dedicated
least-privilege service account (Cloud SQL Client + object-admin on one GCS
bucket only — no Cloud SQL admin/edit role, no project-wide storage access),
a Cloud Run Job running the export in a minimal container
(`platform/scripts/backup/Dockerfile`), and an hourly Cloud Scheduler
trigger — hourly to match the tightest RPO tier this export covers (§2.1),
with objects lifecycle-deleted from GCS after 30 days (a safety-net
retention window, not a permanent archive).

### 6.4 — Local test performed (proves the mechanism, not production access)

Executed this session against a throwaway Docker `postgres:15` container
(`g1e-scratch-pg`, removed after the test — no state left behind):

1. Built a fixture database with all 24 tables from `irreplaceable_table_sets.sh`
   (representative sample data in `conversations`, `conversation_messages`,
   `chart_subject_consent`, `mimamsa_predictions`, `audit_log`; minimal stub
   rows elsewhere) plus one table (`chart_facts`) deliberately **not** in
   either export set, to prove selectivity.
2. Ran `export_irreplaceable_tables.sh --set both` — produced
   `conversations_*.dump` (9 tables, 10,974 bytes) and `ledger_*.dump`
   (15 tables, 16,526 bytes), each with a verified `.sha256`.
3. Created a second, completely fresh scratch database and ran
   `restore_irreplaceable_tables.sh --dump <file> --target-db <fresh-db>`
   for both dumps.
4. **Verified actual restorability, not just a clean exit code:** row counts
   for `conversations` (2), `conversation_messages` (3),
   `chart_subject_consent` (1), `mimamsa_predictions` (2), and `audit_log`
   (2) matched source exactly; full-row content diff on `mimamsa_predictions`
   showed byte-identical `id` (UUID primary keys, not regenerated),
   `chart_id`, `prediction_text`, and `confidence` values between source and
   restored target. `chart_facts` — the deliberately excluded table —
   correctly did **not** exist in the restored target.
5. Verified the fail-loud behavior from §6.2 directly: exported against a
   database missing 8 of 9 conversations-set tables and confirmed the script
   now exits 1 and names the 8 missing tables, where the pre-fix version
   exited 0 with a silently partial dump.
6. Verified the restore script's checksum gate: a corrupted copy of a valid
   `.dump` file (one appended garbage byte) was correctly rejected before
   any `pg_restore` ran against the target database.
7. Fixed one portability bug found in the same pass: `restore_irreplaceable_tables.sh`'s
   optional `--clean` flag used an empty-bash-array expansion that fails
   under `set -u` on bash 3.2 (macOS's default `/bin/bash`, still common on
   developer machines and minimal containers) — switched to the
   `"${arr[@]+"${arr[@]}"}"` portable idiom.

No production database or real Cloud SQL instance was touched by this test.
