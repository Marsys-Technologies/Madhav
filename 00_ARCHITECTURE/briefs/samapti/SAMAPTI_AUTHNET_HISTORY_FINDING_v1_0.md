---
artifact: SAMAPTI_AUTHNET_HISTORY_FINDING
canonical_id: SAMAPTI_AUTHNET_HISTORY_FINDING
version: 1.0
status: PERFORMED — QUESTION ANSWERED
created: 2026-07-30
lane: B-AUTHNET-HISTORY
governed_by: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md RULING 38
addresses: SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL_v1_0 §3.6 item 4 · RES-8
related_rulings: 1, 18, 22, 36, 38
instance: madhav-astrology:asia-south1:amjis-postgres
mode: READ-ONLY — no GCP resource, IAM binding, secret, or database state was modified
---

# `authorizedNetworks` change history — `amjis-postgres`

## §0 — The answer, stated first

> **`authorizedNetworks` on `amjis-postgres` has NEVER held any value — broad or narrow — at any
> point between instance creation (2026-04-25T11:59:51Z) and now (2026-07-30).**
>
> The field was never set at creation and was never touched by any of the seven subsequent
> configuration changes. There was **no window** during which a leaked database password was
> directly exploitable from the open internet by network reachability alone.

**Consequence for the incident's risk assessment: the network dimension is UNCHANGED — it does
NOT escalate.** RULING 36 identified this as the one finding that could overturn the compromise
conclusion. It does not overturn it. The `SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL_v1_0` §1.6
characterisation — *"not presently exploitable from the open internet"* — is now established as
true **for the entire exposure window**, not merely for the moment it was probed.

**This is a narrowing of the risk, not a discharge of it.** Everything else in the incident stands
untouched: two live effective-database-administrator credentials are public; the §1.7 reachability
denominator (~10 project identities that convert a leaked credential into a live session) is
undiminished by this finding; §3.6 items 1, 2, 3 and 5 remain open exactly as written. **RES-8 is
closed. Rotation is not.**

---

## §1 — Technique: what was ruled, what was used, and why they differ

RULING 38 ruled the instrument: **Cloud Asset Inventory** (`gcloud asset get-history`), with
**windowed Admin Activity queries** as the sanctioned fallback, and explicitly forbade repeating the
unbounded log sweep that timed out at 9 minutes.

### 1.1 — Why the PRIMARY technique was not available (and would not have sufficed)

Cloud Asset Inventory was attempted first, per the ruling. It failed for a reason that is itself a
finding:

```
$ gcloud asset search-all-resources --scope=projects/madhav-astrology \
    --asset-types="sqladmin.googleapis.com/Instance" --format=json
API [cloudasset.googleapis.com] not enabled on project [madhav-astrology].
ERROR: (gcloud.asset.search-all-resources) ... Cloud Asset API has not been used in project
madhav-astrology before or it is disabled.  ... reason: SERVICE_DISABLED
```

Confirmed independently against the enabled-service list (`gcloud services list --enabled` — 60
services; `cloudasset.googleapis.com` absent).

**Two independent reasons this path was closed, and the second matters more than the first:**

1. **Enabling the API is a mutation.** This lane's hard constraint is read-only. `gcloud services
   enable` changes project state, and doing it unsupervised to satisfy a read-only investigation is
   precisely the class of action Rulings 1/18/21/28/31/40 reserve to the native. Not done.
2. **Even if enabled, it would have answered nothing.** Cloud Asset Inventory retains asset
   metadata history for **35 days**. The question spans **96 days** (2026-04-25 → 2026-07-30), and
   the highest-risk sub-window — INC-3's exposure opening 2026-04-29, and the entire 2026-05-28
   configuration-change cluster — sits **outside** that retention entirely. Enabling the API today
   also does not retroactively populate history for a period during which it was disabled. **The
   ruled primary instrument was structurally incapable of answering this question.** Recording this
   so no follow-on lane spends time re-attempting it.

### 1.2 — What was actually used: two independent instruments, cross-checked

Rather than day-slicing 96 days blindly, this lane used a **control-plane instrument to enumerate
the operations first**, then opened a **~2-minute log window per operation**. That converts a
96-day scan into 8 targeted lookups. Every query returned in seconds; nothing approached the prior
9-minute timeout.

**Instrument A — Cloud SQL control plane (not a log scan).** `gcloud sql operations list` is the
Cloud SQL service's own authoritative record of every mutation applied to the instance. It is not
subject to logging retention and it reaches back to instance creation (the `CREATE` operation is
present in its output, which bounds completeness from below).

**Instrument B — Admin Activity audit log, windowed.** Admin Activity logs live in the `_Required`
bucket with **400-day retention that cannot be shortened**, so the full 96-day window is in scope.
Used in two modes: (i) a ~2-minute window per known operation id to retrieve request bodies;
(ii) a 7-slice sweep (≈15 days each) filtered to `instances.create|update|patch` to detect any
operation that Instrument A might have missed.

**Freshness note (pre-empting a reviewer's objection):** `gcloud logging read` defaults to
`--freshness=1d`, which would silently truncate results. It is suppressed when the filter contains
an explicit `timestamp` restriction — every query below carries one, and this is **empirically
proven** by the queries returning entries from 2026-04-25, 96 days old.

---

## §2 — Complete operation inventory (Instrument A)

```
$ gcloud sql operations list --instance=amjis-postgres --project=madhav-astrology \
    --filter="operationType!=BACKUP_VOLUME" --limit=500 \
    --format="table(name,operationType,status,insertTime,startTime,endTime,user)"
```

All 17 non-backup operations in the instance's entire life. Every one is attributed to
`mail.abhisek.mohanty@gmail.com` (the native) except the Google-initiated `MAINTENANCE`:

| # | Operation id | Type | Time (UTC) | Actor |
|---|---|---|---|---|
| 1 | `bc28d074…481f` | **CREATE** | 2026-04-25T11:59:57 | native |
| 2 | `121ab94a…d99b` | CREATE_DATABASE | 2026-04-25T12:04:01 | native |
| 3 | `9a4e9125…de93` | CREATE_USER | 2026-04-25T12:04:04 | native |
| 4 | `86caabf1…5bef` | UPDATE_USER | 2026-04-25T12:04:26 | native |
| 5 | `af1f0958…e27c` | UPDATE_USER | 2026-05-28T12:33:54 | native |
| 6 | `3e5466da…ab0f` | **UPDATE** | 2026-05-28T12:48:48 | native |
| 7 | `1250cd0c…afd1` | **UPDATE** | 2026-05-28T12:58:17 | native |
| 8 | `3aa5c1d2…a38a` | **UPDATE** | 2026-05-28T13:04:24 | native |
| 9 | `d595538b…d04d` | FAILOVER | 2026-05-28T18:16:57 | native |
| 10 | `145da02a…98f6` | **UPDATE** | 2026-05-28T18:30:45 | native |
| 11 | `978150d8…718f` | **UPDATE** | 2026-05-28T18:35:46 | native |
| 12 | `6b2fc662…5b08` | EXPORT | 2026-06-02T16:23:52 | native |
| 13 | `a6910f99…0f35` | DELETE_BACKUP | 2026-06-02T17:16:22 | native |
| 14 | `6fd0d7c6…0fdd` | UPDATE_USER | 2026-06-02T17:43:41 | native |
| 15 | `5b47bb99…fae5` | **UPDATE** | 2026-06-02T17:54:38 | native |
| 16 | `6f731db4…7427` | MAINTENANCE | 2026-06-07T00:51:38 | *(Google)* |
| 17 | `34ffd686…8ced` | **UPDATE** | 2026-07-16T16:07:40 | native |

**Seven `UPDATE` operations** — exactly matching the count in the incident document §3.3, which
independently corroborates that neither record is missing operations. Plus the `CREATE`, these are
the **eight operations capable of setting `authorizedNetworks`**. The three `UPDATE_USER` events
correlate 1:1 with the three password versions (already established in the incident doc §3.3);
`CREATE_USER`/`CREATE_DATABASE`/`EXPORT`/`DELETE_BACKUP`/`FAILOVER`/`MAINTENANCE` cannot alter
instance IP configuration.

---

## §3 — Per-operation request bodies (Instrument B)

Each query used a ~2-minute window pinned to the operation id, e.g.:

```
$ gcloud logging read 'logName="projects/madhav-astrology/logs/cloudaudit.googleapis.com%2Factivity"
    AND resource.type="cloudsql_database"
    AND operation.id="3e5466da-9077-4111-ac9f-ab0f0000002f"
    AND timestamp>="2026-05-28T12:48:00Z" AND timestamp<="2026-05-28T12:50:00Z"' \
  --project=madhav-astrology --limit=10 \
  --format="json(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail,
                 protoPayload.requestMetadata.callerIp,protoPayload.request.body,protoPayload.status)"
```

### 3.1 — Instance creation · 2026-04-25T11:59:51Z · `cloudsql.instances.create`

Request body, verbatim and complete:

```json
{ "databaseVersion": "POSTGRES_15", "name": "amjis-postgres", "project": "madhav-astrology",
  "region": "asia-south1",
  "settings": { "availabilityType": "ZONAL",
    "backupConfiguration": { "enabled": true, "startTime": "02:00" },
    "dataDiskSizeGb": "10", "dataDiskType": "PD_SSD", "pricingPlan": "PER_USE",
    "replicationType": "SYNCHRONOUS", "storageAutoResize": true, "tier": "db-g1-small" } }
```

**No `ipConfiguration` key at all.** The instance was created with the Cloud SQL defaults:
`ipv4Enabled` true (public IP allocated) and `authorizedNetworks` **empty**. No CIDR was ever
seeded at birth. Caller IP `103.167.97.126`, principal `mail.abhisek.mohanty@gmail.com`.

### 3.2 — The seven `UPDATE` operations

Every one is a **`SqlInstancesPatchRequest`** — verified explicitly (see §3.3). Full body of each:

| # | Time (UTC) | Settings field(s) in request body | Touches `ipConfiguration`? |
|---|---|---|---|
| 1 | 2026-05-28T12:48:48 | `tier: db-custom-2-4096` | **NO** |
| 2 | 2026-05-28T12:58:17 | `availabilityType: REGIONAL` | **NO** |
| 3 | 2026-05-28T13:04:24 | `backupConfiguration` (PITR **on**, 7 retained, 02:00) | **NO** |
| 4 | 2026-05-28T18:30:45 | `availabilityType: ZONAL` (reverts #2) | **NO** |
| 5 | 2026-05-28T18:35:46 | `tier: db-custom-1-3840` | **NO** |
| 6 | 2026-06-02T17:54:38 | `tier: db-g1-small` (reverts #1/#5) | **NO** |
| 7 | 2026-07-16T16:07:40 | `backupConfiguration` (PITR **off**, `transactionalLogStorageState: CLOUD_STORAGE`) | **NO** |

The whole seven-operation history is a coherent, benign story: a 2026-05-28 scale-up/HA experiment
(tier up, regional, PITR on) that was walked back the same evening and completed on 2026-06-02
(zonal, original tier), plus a 2026-07-16 backup-configuration adjustment. **Not one request body
contains an `ipConfiguration` key, and therefore not one contains `authorizedNetworks`.**

All seven were issued by `mail.abhisek.mohanty@gmail.com` from residential-looking Indian IPv6
addresses in three `2409:40e2:…` / `2405:201:…` prefixes; all returned `status.message: OK`. **No
third-party principal appears on the configuration plane at any point.**

### 3.3 — Why "absent from the request body" means "never set" here

This distinction is load-bearing and is the difference between a sound conclusion and a guess.

A Cloud SQL `UPDATE` (HTTP PUT, `SqlInstancesUpdateRequest`) **replaces** the settings object —
absence of a field there means *cleared*, which would leave the intermediate state ambiguous. A
**PATCH** (`SqlInstancesPatchRequest`) merges only the fields present — absence means *not touched*.

Verified for all eight operations:

```
$ ... --format="value(protoPayload.request[\"@type\"])"
CREATE   bc28d074…  google.cloud.sql.v1beta4.SqlInstancesInsertRequest
UPDATE   3e5466da…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
UPDATE   1250cd0c…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
UPDATE   3aa5c1d2…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
UPDATE   145da02a…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
UPDATE   978150d8…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
UPDATE   5b47bb99…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
UPDATE   34ffd686…  google.cloud.sql.v1beta4.SqlInstancesPatchRequest
```

**All seven are PATCH.** (Note the audit-log `methodName` is `cloudsql.instances.update` even for
PATCH requests — a filter on `methodName` therefore correctly catches both, which is why the §4
sweep is complete.)

So the chain is closed end to end: created with the field **absent** (§3.1) → seven **merge**
operations, none of which mentions it (§3.2) → **absent today** (§5). There is no operation left in
which a value could have been introduced, and none in which one could have been silently dropped.

---

## §4 — Completeness sweep: did Instrument A miss an operation?

To rule out a configuration change that produced an audit entry but no listed operation (e.g. a
failed or rejected update), the full window was swept in **seven ≈15-day slices** — never
unbounded — filtered to the three instance-mutating methods:

```
$ gcloud logging read 'logName="projects/madhav-astrology/logs/cloudaudit.googleapis.com%2Factivity"
    AND resource.labels.database_id="madhav-astrology:amjis-postgres"
    AND (protoPayload.methodName="cloudsql.instances.update"
      OR protoPayload.methodName="cloudsql.instances.patch"
      OR protoPayload.methodName="cloudsql.instances.create")
    AND timestamp>="<slice-start>" AND timestamp<"<slice-end>"' \
  --project=madhav-astrology --limit=50 \
  --format="value(timestamp,protoPayload.methodName,operation.id,protoPayload.status.message)"
```

| Slice | Entries | Operation ids seen |
|---|---|---|
| 04-25 → 05-10 | 1 | `bc28d074…` (create) |
| 05-10 → 05-25 | 0 | — |
| 05-25 → 06-09 | 12 | `3e5466da`, `1250cd0c`, `3aa5c1d2`, `145da02a`, `978150d8`, `5b47bb99` (×2 each: `first`+`last`) |
| 06-09 → 06-24 | 0 | — |
| 06-24 → 07-09 | 0 | — |
| 07-09 → 07-24 | 2 | `34ffd686…` (×2) |
| 07-24 → 07-31 | 0 | — |

**Result: exactly 1 create + 7 updates, every `status.message: OK`, operation ids matching
Instrument A one-for-one with zero extras and zero omissions.** Two independent instruments — the
Cloud SQL control plane and the Admin Activity audit log — agree completely on the operation set.

**Adjacent check — no clone could have carried the data onto an open network:**

```
$ gcloud sql instances list --project=madhav-astrology
NAME            DATABASE_VERSION  REGION      AUTHORIZED_NETWORKS  IPV4_ENABLED  CREATE_TIME               STATUS
amjis-postgres  POSTGRES_15       asia-south1                      True          2026-04-25T11:59:51.223Z  RUNNABLE
```

`amjis-postgres` is the **only** Cloud SQL instance in the project, and no `CLONE` operation appears
in §2. There is no sibling instance that could have held the same data behind a permissive
`authorizedNetworks`.

---

## §5 — Current state (the terminal point of the timeline)

```
$ gcloud sql instances describe amjis-postgres --project=madhav-astrology --format=json
```

```json
"ipConfiguration": {
  "ipv4Enabled": true,
  "requireSsl": false,
  "serverCaMode": "GOOGLE_MANAGED_INTERNAL_CA",
  "sslMode": "ALLOW_UNENCRYPTED_AND_ENCRYPTED",
  "message": "Configuring authorized network or using CloudSQL auth proxy or language connectors
              is a prerequisite for connecting to Public IP. ..."
}
```

`authorizedNetworks` **absent**; `createTime` 2026-04-25T11:59:51.223Z; `settingsVersion` 155;
public PRIMARY IP `34.93.202.112`. This reconfirms incident findings R1/R2/R3/R4 unchanged.

---

## §6 — Timeline of every `authorizedNetworks` value observed

| From | To | Value | Set by | Evidence |
|---|---|---|---|---|
| 2026-04-25T11:59:51Z (creation) | 2026-07-30 (now) | **∅ — never set, empty throughout** | *(never set by anyone)* | §3.1 create body · §3.2 all seven PATCH bodies · §4 completeness sweep · §5 current state |

**The timeline has exactly one row. There is no second value to report.**

- **Was `authorizedNetworks` ever broader than its current (empty) state?** **No.**
- **When / for how long / what CIDR?** **Not applicable — no such window exists.**
- `0.0.0.0/0` — or any other CIDR, broad or narrow — **never appears** in the instance's
  configuration history.

---

## §7 — Honest limits — what this finding does NOT establish

Per RULING 38 and the incident document's §3.6 discipline, the boundary of the claim is stated
explicitly. This check is **PERFORMED**, not partial — but it is performed against a specific
question, and these are its edges:

1. **This covers the network-reachability precondition only.** It does **not** speak to the §1.7
   reachability denominator, which is the live risk: ~10 GCP identities hold `roles/cloudsql.client`
   (8 explicitly, 3 via `roles/editor`), any one of which converts a leaked credential into a live
   session **without** needing `authorizedNetworks` at all. **An empty `authorizedNetworks` for the
   whole window narrows the attack surface to that denominator; it does not eliminate it.**
2. **Absence of an admin-plane record is not proof against non-API paths.** The precedent is in this
   instance's own history: `retrieval_census_ro` was created via in-SQL `CREATE ROLE` and is
   **invisible** to the administrative audit trail (incident §3.4). That mechanism does not apply to
   `authorizedNetworks` — instance IP configuration has no in-SQL equivalent and can only be changed
   through the Admin API, which always emits both an operation record and an audit entry — but the
   general caution is recorded rather than waved away.
3. **The `MAINTENANCE` operation (2026-06-07) was not opened.** It is Google-initiated and carries
   no user-supplied settings body. Google's maintenance does not alter customer IP configuration,
   and the current state (§5) is consistent with the pre-maintenance state, so this is not treated
   as a gap — but it is the one operation in §2 whose request body was not inspected, and it is
   named here rather than passed over silently.
4. **`settingsVersion` is 155 against only 7 user updates.** This is expected — the counter
   increments on Google-side internal events (backups, maintenance, certificate handling), not only
   on user config changes — and it is **not** evidence of unlogged updates, since §4's independent
   audit sweep found no operations beyond the seven. Recorded because the number invites the
   opposite inference at a glance.
5. **This finding does not reduce the severity of the credential exposure by one step.** Both live
   effective-DB-administrator credentials remain public, and the CREATEROLE self-escalation and
   persistence analysis (incident §1.5) is entirely untouched by anything here. **Rotation remains
   P0 and is not discharged.**

**Retention deadline — now moot for this question.** RULING 38's urgency rested on evidence
expiring: Admin Activity's rolling 400-day window would have begun dropping the earliest exposure
days from **2027-05-30**. The question is answered ahead of that deadline and the underlying
evidence is transcribed into §2–§4 of this document, so the finding survives the retention window
regardless of what Google drops later.

---

## §8 — Disposition

| Item | Before | After |
|---|---|---|
| Incident §3.6 item 4 | "**not established** … the single most consequential gap" | **ESTABLISHED — negative.** Never set. |
| **RES-8** | Open · owner *Native / follow-on lane* | **CLOSED** by this document |
| RULING 38 | Open, time-critical | **DISCHARGED — PERFORMED** (not UNPERFORMED; no gap to declare) |
| RULING 36's overturn risk | Open — could overturn the compromise conclusion | **DID NOT OVERTURN.** Conclusion holds and is now stronger. |
| E1-SAMGATI binding (Ruling 38) | Close report may not state a final compromise conclusion | **UNBLOCKED** — the check succeeded; the close report may state its conclusion, in §3.6's "no evidence of misuse in the window we can see" language, which this finding supports for the network dimension across the *entire* window |

**Net effect on the incident.** The one open question that could have escalated this to a live
open-internet exposure is answered in the negative, with the full 96-day window covered by two
agreeing instruments. The incident's severity is now driven **entirely** by credential privilege and
the reachability denominator — which is exactly where RULING 39 (privilege narrowing) and RULING 40
(IAM pruning) already direct the remediation. **This finding confirms the remediation priorities are
aimed at the right target; it removes no item from the runbook.**

---

## §9 — Read-only attestation

Every command run in this lane was `describe` / `list` / `read`. No `gcloud services enable`, no
`gcloud sql instances patch`, no IAM change, no Secret Manager access, no database connection, no
mutation of any kind. The Cloud Asset API was deliberately **left disabled** rather than enabled to
satisfy this investigation (§1.1). No credential value is reproduced anywhere in this document.
