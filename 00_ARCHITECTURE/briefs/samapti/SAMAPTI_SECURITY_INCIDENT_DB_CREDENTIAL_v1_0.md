---
artifact: SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL
canonical_id: SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL
version: 1.2
status: CLOSED-BY-NATIVE-DISPOSITION — see §9-NATIVE-DISPOSITION
created: 2026-07-30
closed: 2026-07-31
lane: B-SECRET-ROTATE-PREP
governed_by: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md RULING 1, 18, 21, 22
related_lanes: B-SECRET-REDACT (RULING 2), B-SECRETSCAN-SCOPE (RULING 3)
---

# CLOSED (2026-07-31, native disposition) — see §9-NATIVE-DISPOSITION before reading further

> **NIḤŚEṢA closing note (2026-07-31):** the native has reviewed the credentials this document
> concerns and classified them **SECURE / accepted risk**. No rotation is to be performed, and this
> is not to be re-raised as a P0. This document's §0–§8 technical analysis (incident record,
> consumer inventory, compromise assessment, rotation runbook, recurrence guard) is retained
> in place, unedited, as the audit trail — per `ONGOING_HYGIENE_POLICIES_v1_0.md §A` archival
> discipline, history is not rewritten to match a later decision. The "Priority: P0" banner
> immediately below and the frontmatter's original `status: UNRESOLVED-PENDING-NATIVE-EXECUTION`
> reflect this lane's own assessment **at the time it was written (2026-07-30)** — read them as
> that, not as the document's current status. **§9-NATIVE-DISPOSITION (appended below §9) is the
> authoritative, current disposition.** PR #905 (plaintext-credential redaction in 27 files) merged
> separately as ordinary hygiene per the same native instruction.

# ⚠️ UNRESOLVED (as assessed 2026-07-30 — SUPERSEDED, see banner above) — PUBLIC EXPOSURE OF TWO LIVE EFFECTIVE-DATABASE-ADMINISTRATOR CREDENTIALS

> **THIS DOCUMENT IS PREPARATION ONLY. IT IS NOT A CLOSURE.**
>
> **The incident described below is UNRESOLVED.** Nothing has been rotated. No role has been
> created, altered, or disabled. No Secret Manager version has been written. No IAM binding has
> been changed. The SAMĀPTI swarm has no credential-administration authority (DVA RULING 1) and
> did not exercise any. Only read-only `gcloud` / `psql` / `git` / `gh` probes were run.
>
> **The incident becomes resolved only when the native — a human with credential-admin authority —
> executes §5 of this document and records the outcome in §9.**
>
> **Severity, in DVA RULING 18's corrected language:** the two live exposed credentials are not
> "high-privilege credentials on the app schema". Each is an **EFFECTIVE DATABASE ADMINISTRATOR
> credential capable of self-escalation and persistence**. Both `amjis_app` and `postgres` are
> members of `cloudsqlsuperuser` with `rolcreatedb = true` **and** `rolcreaterole = true`
> (independently re-derived from `pg_roles` — §8 probe D). On PostgreSQL 15, which this instance
> runs, `CREATEROLE` permits granting membership in **any non-superuser role**, `cloudsqlsuperuser`
> included, without `ADMIN OPTION`. A holder of either credential can therefore mint a new login
> role, elevate it, and **survive the rotation described in this document**. See §1.5 — and note
> the direct consequence: **rotation alone does not evict an attacker who has already established
> persistence.** §5 step 5.1 enumerates roles before anything else for exactly this reason.
>
> **Priority: P0.** Escalated twice from RULING 1's original assessment.

---

## §0 — What this lane found beyond RULING 1

DVA RULING 1 was issued on the A7-N8-AUDIT finding of **one** credential literal in 9 tracked files.
This lane independently re-derived that finding and, in the course of building the consumer
inventory, discovered **two further credential literals** on `origin/main` that the audit did not
surface.

| id | Role it authenticates as | Live today? | Tracked files on `origin/main` | First public commit | Days public (as of 2026-07-30) |
|---|---|---|---|---|---|
| **INC-1** | `amjis_app` | **NO — superseded** | 9 (19 occurrences) | `39b91dd0` · 2026-05-29 | 62 |
| **INC-2** | `amjis_app` — *effective DB administrator* | **YES — LIVE** | 16 (23 occurrences) | `0c2d4d98` · 2026-06-05 | 55 |
| **INC-3** | `postgres` — *effective DB administrator* | **YES — LIVE** | 2 (2 occurrences) | `599cfce1` · 2026-04-29 | **92** |

Three corrections to RULING 1's premises, all independently verified (§8):

1. **RULING 1's subject credential (INC-1) is already dead.** It was superseded on 2026-06-02 when
   `amjis-db-password` version 3 was created. A direct authentication probe returns
   `FATAL: password authentication failed for user "amjis_app"`. Its live-and-public window was
   ~2026-05-29 → 2026-06-02 (≈4 days), not 2 months. Its remaining value is as a recurrence signal,
   not as an active exposure.
2. **The credential that replaced it (INC-2) was itself committed in plaintext three days later**
   and is the credential `amjis-web` is serving with at this moment. The 2026-06-02 rotation
   therefore did not remediate the pattern — it reproduced it. Any rotation performed without §6's
   redaction/consumer discipline will reproduce it a third time.
3. **INC-3, the most severe of the three, was in no prior finding**: a live `postgres`
   effective-DB-administrator password, public for three months, held in **no Secret Manager
   secret at all** — it exists only in the repository and wherever the native keeps it.

Credentials are referenced throughout this document by id and by SHA-256 fingerprint only. **No
credential value appears anywhere in this document, in this lane's commits, or in its summary.**

| id | SHA-256 (first 16 hex) — for mechanical identification |
|---|---|
| INC-1 | `bd14b4e7cbc6c972` |
| INC-2 | `9916bb655a303c81` |
| INC-3 | `f0abfd07498574f6` |

Verify a candidate string against these with:
`printf '%s' "<candidate>" | shasum -a 256 | cut -c1-16`

**Changelog v1.0 → v1.1** (2026-07-30, same lane, reopened on DVA rulings 18/21/22): severity
language corrected throughout to *effective database administrator*, with the self-escalation and
persistence mechanism made explicit (§1.5); new §1.7 reachability-denominator finding; the two
production-proxying CI workflows promoted to **named consumers** with their authenticating roles
established, correcting a v1.0 error (§2.3); new §3 compromise assessment; runbook gained the
literal↔version confirmation step (5.2), an explicit non-reorderable create→bump→disable sequence
(5.7), the 13-pin `deploy.yml` audit (5.8), and pre/post persistence sweeps (5.1, 5.12).

---

## §1 — Incident record

### 1.1 — Repository exposure is public and confirmed

```
$ gh repo view amonty84/Madhav --json visibility,isPrivate,createdAt,forkCount,stargazerCount
{"createdAt":"2026-04-17T15:39:06Z","forkCount":0,"isPrivate":false,
 "stargazerCount":0,"visibility":"PUBLIC"}
```

The repository is **PUBLIC**. Fork count 0 and star count 0 bound the *observed* interest but do
**not** bound exposure: public GitHub content is continuously ingested by third-party crawlers,
code-search indices, and credential-harvesting bots, and GitHub's own event firehose has published
every push. **Absence of forks is not evidence of absence of compromise.**

Git history cannot be purged (DVA RULING 2 explicitly withholds history-rewrite authority, and a
rewrite would not recall bytes already replicated). **Rotation is the only remediation.** Redaction
(B-SECRET-REDACT) reduces recurrence, not exposure.

### 1.2 — INC-1 · `amjis_app`, superseded 2026-06-02

**Introduced:** commit `39b91dd0`, 2026-05-29, author Abhisek —
*"chore(conductor/build-orch): Phase A complete — 13 worktrees + 95-session queue + 11 scripts"*.
Native-authored, not another campaign's work (consistent with RULING 1).

**Locations on `origin/main`** — 9 files, 19 occurrences (never the value, only the coordinates):

| file | line(s) |
|---|---|
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/hard_gates_check.sh` | 46 |
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/preflight.sh` | 17 |
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/apply_migration.sh` | 7 |
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml` | 587, 605, 623, 641, 659, 677, 695, 713, 731, 1949, 2249 |
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/operator_runs/2026-05-30/.psql_url` | 1 |
| `platform/migrations/__tests__/test_mig_124.py` | 16 |
| `platform/migrations/__tests__/test_mig_125.py` | 15 |
| `platform/migrations/__tests__/test_mig_126.py` | 15 |
| `platform/migrations/__tests__/test_mig_127.py` | 16 |

**Secret Manager correspondence — CONFIRMED, not assumed** (DVA RULING 18(a) asked that this be
established rather than inferred from date proximity). Payloads were compared by shell equality
against the repository literal; no value was printed:

| secret | version | created | matches INC-1? | state today |
|---|---|---|---|---|
| `amjis-db-password` | **2** | 2026-05-28 | **YES** | **enabled** |
| `amjis-db-password` | 3 | 2026-06-02 | no (= INC-2) | enabled |
| `amjis-pipeline-db-url` | **2** | 2026-05-30 | **YES** (embedded in the DSN) | **enabled** |
| `amjis-pipeline-db-url` | 3 | 2026-06-06 | no (= INC-2) | enabled |

DVA's stated high-probability match — `amjis-db-password` version 2, created 2026-05-28, one day
before the 2026-05-29 commit — is **correct and now confirmed**. Both v2 versions remain `enabled`
even though the underlying database password no longer matches. That is dead weight and it is
misleading: a reader would reasonably assume an `enabled` version is valid. Disable them in
step 5.10.

**Current status:** DEAD against every role on the instance (`amjis_app`, `postgres`,
`retrieval_census_ro` all reject it — §8 probe B).

### 1.3 — INC-2 · `amjis_app` (effective DB administrator), LIVE

**Introduced:** commit `0c2d4d98`, 2026-06-05, author Abhisek —
*"feat(v13-prod): v13_production_gate.py — final cross-stream prod gate script"*.
Appears in **20 commits** across history.

**This is the credential production is using right now**: `amjis-web` binds
`DB_PASSWORD ← amjis-db-password:3`, and version 3's payload authenticates as `amjis_app`
(§8 probe A). `amjis-pipeline-db-url:3` embeds the **same** credential and is consumed by
`amjis-sidecar` and `brahma-build-pipeline-job`. It is **also** the credential the nightly
ṢAḌ-DARŚANA circularity-guard CI job authenticates production with (§2.3.1).

**Locations on `origin/main`** — 16 files, 23 occurrences:

| file | line(s) |
|---|---|
| `platform/python-sidecar/routers/sutravali.py` | 32 |
| `platform/python-sidecar/routers/permission_curve.py` | 69 |
| `platform/python-sidecar/brahmagyan/l0_embed_runner.py` | 23 |
| `platform/python-sidecar/build_ephemeris_1900_2150.py` | 28 |
| `platform/python-sidecar/run_bo_samskara_parallel.py` | 24 |
| `platform/python-sidecar/test_savepoint_failure_path.py` | 34 |
| `platform/python-sidecar/tests/test_gochara_intensity.py` | 37 |
| `platform/python-sidecar/tests/test_ka_gochara_sweep.py` | 815 |
| `platform/python-sidecar/tests/test_permission_curve_route.py` | 24 |
| `platform/python-sidecar/tests/test_cr131_gochara_db_reachability.py` | 53 |
| `platform/python-sidecar/tests/l2/test_b6_eval_harness.py` | 42 |
| `platform/python-sidecar/tests/l3/test_ka_dasha_kala.py` | 658 |
| **`platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py`** | **64** ← *executed nightly by CI — §2.3.1* |
| `platform/scripts/governance/v13_production_gate.py` | 13 |
| `docs/superpowers/plans/2026-06-17-ga-nakshatra-l1.md` | 157, 166, 1310, 1340, 1359, 1374, 1400, 1414 |
| `docs/superpowers/plans/2026-06-21-l2-bodha-writer-fixes-and-b6-hardening.md` | 447 |

**The shape that propagated it** — an env-override with a hard-coded production fallback:

```python
# platform/python-sidecar/routers/sutravali.py:30-33  (value redacted)
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://amjis_app:<REDACTED-LIVE-CREDENTIAL>@127.0.0.1:5433/amjis",
)
```

```python
# platform/scripts/governance/v13_production_gate.py:13  (value redacted)
PW = os.environ.get("DB_PASSWORD", "<REDACTED-LIVE-CREDENTIAL>")
```

`permission_curve.py:65-66` documents this as an intentional convention —
*"Same live DSN convention as routers/sutravali.py / routers/transit_search.py (env override,
hard-coded local-proxy fallback for dev)"*. **The convention itself is the defect.** A "local dev
fallback" holding a live effective-DB-administrator credential is a production credential, not a dev
default. Three files hold it with no env override at all (`l0_embed_runner.py:23`,
`tests/test_gochara_intensity.py:37`, `tests/l3/test_ka_jivana_parva_circularity_guard.py:64` —
bare literal assignment).

### 1.4 — INC-3 · `postgres` (effective DB administrator), LIVE, 92 days public

**Introduced:** commit `599cfce1`, 2026-04-29 —
*"Phase 14C Stream H: end-to-end verification + close report — Phase 14C COMPLETE"*.
Appears in **12 commits**.

**Locations on `origin/main`** — 2 files, 2 occurrences:

| file | line |
|---|---|
| `platform/src/lib/db/seed/observatory_pricing/run_seed.ts` | 74 |
| `00_ARCHITECTURE/MIGRATION_APPLY_INSTRUCTIONS_v1_0.md` | 71 |

**Why this is the worst of the three:**

1. It is written in a DSN of the form `postgresql://amjis_app:<literal>@127.0.0.1:5433/amjis` —
   **mislabelled as `amjis_app`** — but it does **not** authenticate as `amjis_app`. It
   authenticates as **`postgres`** (§8 probe C). Anyone reading the file sees an app credential;
   the credential is in fact an effective database administrator. This mislabelling is very likely
   why 92 days of audits, including A7-N8-AUDIT, walked past it.
2. `postgres` is a member of `cloudsqlsuperuser` with `CREATEDB` and `CREATEROLE` (§8 probe D) —
   the same effective-DB-administrator standing as `amjis_app`, with the same self-escalation and
   persistence properties described in §1.5. `cloudsqlsuperuser` owns both the `amjis` and
   `postgres` databases.
3. It is held in **no Secret Manager secret** — `gcloud secrets list` has no entry for it. It is
   unmanaged, unversioned, and unrotatable-by-config. Rotating it requires
   `gcloud sql users set-password postgres` and then hunting every consumer by hand.
4. 92 days of public exposure is the longest of the three, and it predates the entire
   build-orchestrator episode RULING 1 examined.
5. It is the role `fresh_chart_smoke.yml` declares its production connection as (§2.3.2).

### 1.5 — What "effective database administrator" means here, concretely (RULING 18)

DVA RULING 18 replaced this document's original characterisation. The corrected language is
load-bearing, so the mechanism is set out explicitly. All facts below are from `pg_roles` /
`pg_auth_members` / `pg_namespace` / `pg_tables`, independently re-derived (§8 probe D):

| property | `amjis_app` | `postgres` | consequence |
|---|---|---|---|
| member of `cloudsqlsuperuser` | yes | yes | `cloudsqlsuperuser` owns both databases (`amjis`, `postgres`); it is Cloud SQL's superuser-equivalent for a managed instance. |
| `rolcreatedb` | **true** | **true** | Can create new databases. |
| `rolcreaterole` | **true** | **true** | **The escalation and persistence primitive.** See below. |
| `rolcanlogin` | true | true | Directly usable as a login credential. |
| `rolconnlimit` | −1 (unlimited) | −1 | No throttle on concurrent misuse. |
| `rolvaliduntil` | null | null | **No expiry.** A leaked value stays valid until explicitly changed. |
| object ownership | schemas `public` + `auth`; **all 291 tables in `public`** | — | Full DDL and DML over the entire corpus. |

**Self-escalation.** The instance runs `POSTGRES_15` (`databaseInstalledVersion:
POSTGRES_15_17`). On PostgreSQL 15 and earlier, a role holding `CREATEROLE` may grant or revoke
membership in **any role that is not a superuser**, without needing `ADMIN OPTION` on it.
`cloudsqlsuperuser` has `rolsuper = false` (§8 probe D). A holder of INC-2 or INC-3 can therefore:

```sql
CREATE ROLE <attacker_role> WITH LOGIN PASSWORD '<theirs>';
GRANT cloudsqlsuperuser TO <attacker_role>;               -- permitted under PG15 CREATEROLE semantics
ALTER ROLE retrieval_census_ro WITH PASSWORD '<theirs>';  -- CREATEROLE can alter non-superuser roles
```

*(This lane did **not** test these statements — executing them would be a mutation, which the lane
is forbidden. The claim rests on the observed server version plus documented PostgreSQL 15
`CREATEROLE` semantics. PostgreSQL 16 narrowed this behaviour; this instance is not on 16. Treat it
as true unless disproved.)*

**Persistence.** The escalation above produces a role **independent of `amjis_app` and `postgres`**.
Rotating INC-2 and INC-3 — the entirety of §5 phases A–C — would **not** remove it.

**Two direct consequences, both folded into the runbook:**

- **§5 step 5.1 runs a role-enumeration sweep BEFORE any rotation step**, and step 5.12 repeats it
  after. Rotation may not be declared sufficient without both.
- **Rotation is necessary but not sufficient as a remediation.** If a persistence artefact were ever
  found, the remediation is no longer "rotate" but "rotate, revoke, and audit every object for
  tampering against a pre-exposure backup" — a materially larger operation, and one that R6 (no
  PITR, 7 daily backups) makes largely infeasible for INC-3's window. §3 exists to establish, as far
  as the evidence permits, whether that larger operation is required. Its present finding is that no
  such artefact is visible (§3.4) — stated with the limits §3.6 sets out, and never as "not
  compromised."

### 1.6 — Current risk posture (independently confirmed)

```
$ gcloud sql instances describe amjis-postgres \
    --format="json(state,settings.ipConfiguration,settings.tier,
                   settings.deletionProtectionEnabled,settings.connectorEnforcement)"
{
  "settings": {
    "connectorEnforcement": "NOT_REQUIRED",
    "deletionProtectionEnabled": false,
    "ipConfiguration": {
      "ipv4Enabled": true,
      "requireSsl": false,
      "serverCaMode": "GOOGLE_MANAGED_INTERNAL_CA",
      "sslMode": "ALLOW_UNENCRYPTED_AND_ENCRYPTED"
    },
    "tier": "db-g1-small"
  },
  "state": "RUNNABLE"
}
```

RULING 1's two findings are **CONFIRMED**, and five more are added:

| # | Finding | Confirmed value | Assessment |
|---|---|---|---|
| R1 | `authorizedNetworks` | **absent / null** | The control preventing *open-internet* exploitation of INC-2 and INC-3. Load-bearing — but see §1.7: it is not the only precondition, and the set of identities that bypass it is larger than one. |
| R2 | `requireSsl` | **false** (`sslMode: ALLOW_UNENCRYPTED_AND_ENCRYPTED`) | Public-IP instance accepting unencrypted connections. Defence-in-depth failure. |
| R3 | `ipv4Enabled` | **true**, PRIMARY `34.93.202.112` | Instance has a routable public address. Reachability from the open internet is gated only by R1. |
| R4 | `connectorEnforcement` | **NOT_REQUIRED** | Auth Proxy / connector use is conventional, not enforced. If R1 is ever relaxed, R1+R2+R4 compose into direct exploitability. |
| R5 | `deletionProtectionEnabled` | **false** | A holder of INC-2/INC-3 has DB-level destructive capability; instance-level deletion additionally needs GCP IAM, which the leak does not grant. |
| R6 | `pointInTimeRecoveryEnabled` | **false**; 7 retained backups, `transactionLogRetentionDays: 7` | Recovery granularity is 7 daily backups. **This is the binding constraint on the §1.5 "audit for tampering" path** — there is no pre-exposure restore point for INC-3, whose exposure began 2026-04-29. |
| R7 | `rolvaliduntil` | **null** on all three project roles | No credential on this instance expires. Every leak is permanent until manually rotated. |

**Net posture.** Not presently exploitable from the open internet — an attacker holding INC-2 or
INC-3 still needs either a GCP identity with Cloud SQL Client permission (to use the Auth Proxy) or
an entry in `authorizedNetworks` (there are none). RULING 1's "defence-in-depth failure, not a 2am
emergency" characterisation therefore **still holds for the network dimension**.

It does **not** hold for the *scope* or *privilege* dimensions. RULING 1 assessed a dead app
credential; the true state is two live effective-DB-administrator credentials, both public, one for
three months, both capable of minting persistence that outlives their own rotation.

### 1.7 — The reachability denominator (new finding; not in any prior ruling)

R1 is routinely described — including in this document's v1.0 — as *"the only thing standing between
this leak and direct exploitation."* That is true of the **open internet** and misleading about
everything else. The precondition an attacker must satisfy is not "compromise the GCP project
owner"; it is **"control any one of ~10 project identities."**

```
$ gcloud projects get-iam-policy madhav-astrology --flatten="bindings[].members" \
    --format="table(bindings.role,bindings.members)" | grep -E "cloudsql|editor"
roles/cloudsql.client   serviceAccount:938361928218-compute@developer.gserviceaccount.com
roles/cloudsql.client   serviceAccount:amjis-mcp-runtime@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.client   serviceAccount:amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.client   serviceAccount:amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.client   serviceAccount:brahma-conductor-bot@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.client   serviceAccount:brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.client   serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.client   serviceAccount:marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com
roles/cloudsql.editor   serviceAccount:brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com
roles/editor            serviceAccount:938361928218-compute@developer.gserviceaccount.com
roles/editor            serviceAccount:938361928218@cloudservices.gserviceaccount.com
roles/editor            serviceAccount:madhav-astrology@appspot.gserviceaccount.com
```

**8 service accounts hold `roles/cloudsql.client` explicitly. Three principals hold `roles/editor`,
which confers it implicitly** (one — `938361928218-compute` — holds both). All 15 service accounts
in the project are `disabled: False`.

**The composition that matters:** a leaked DB credential supplies *authorization*; any of these
identities supplies *reachability*. Neither alone is sufficient; together they are complete
compromise at effective-DB-administrator level. So the real question is not "is the DB on the
internet" (it is not) but "how many identities are one compromise away from turning a public
credential into a live session" — and the answer is about ten, three of which hold `roles/editor`
(broad project-wide power, the classic over-granted-default-SA shape) and two of which
(`938361928218-compute`, `marsys-pipeline-writer`) are **dormant** — no connection in 30 days
(§3.2) — yet still enabled and still granted.

**Two grants are unnecessary on current evidence and should be removed independently of the
rotation:**

- **`amjis-mcp-runtime` holds `roles/cloudsql.client`** but `amjis-mcp` has no database credential
  of any kind (§2.1) and reaches data only through `amjis-web` / `amjis-sidecar`. A standing grant
  with no consumer.
- **`marsys-pipeline-writer`** last connected 2026-06-01 and corresponds to the retired
  build-orchestrator operator-run era. Retired tooling, live grant.

This does not make the incident internet-exploitable. It does mean R1 is a **narrower** control than
"the only thing standing between this leak and exploitation" implies, and it belongs in the severity
picture. Flagged to DVA as a scope question.

---

## §2 — Consumer inventory

Every system that authenticates to `amjis-postgres`. Each row was verified by direct read-only
inspection of the live resource or the file, not inferred from documentation.

### 2.1 — Production runtime (Cloud Run services)

| Consumer | Role | How it obtains the credential | Credential | Migration action |
|---|---|---|---|---|
| **`amjis-web`** (rev `amjis-web-01281-p25`) | `amjis_app` | `DB_PASSWORD` ← `secretKeyRef amjis-db-password` key **`3`** (version-pinned). `DB_USER=amjis_app`, `DB_NAME=amjis`, `INSTANCE_CONNECTION_NAME` as plain env. Consumed at `platform/src/lib/db/client.ts:63` (`password: process.env.DB_PASSWORD!`). | INC-2 | **Required.** Repoint to the new secret version. Version-pinned ⇒ will **not** pick up a new version automatically. |
| **`amjis-sidecar`** (rev `amjis-sidecar-00933-f9j`) | `amjis_app` | `DATABASE_URL` ← `secretKeyRef amjis-pipeline-db-url` key **`latest`**. Cloud SQL attached via `run.googleapis.com/cloudsql-instances` annotation (unix socket). | INC-2 (embedded in the DSN) | **Required.** Bound to `latest` ⇒ picks up a new version on next revision start, but **only** on restart — a new revision must be forced. |
| **`amjis-mcp`** (rev `amjis-mcp-00517-b5q`) | — | **No database credential of any kind.** Its full env is `MCP_INTERNAL_TOKEN`, `PYTHON_SIDECAR_API_KEY`, `MCP_CANARY_KEY`, `PLATFORM_URL`, `PYTHON_SIDECAR_URL`, `MCP_BASE_URL`. All data access is proxied through `amjis-web` / `amjis-sidecar`. Its runtime SA nevertheless holds `roles/cloudsql.client` — §1.7. | n/a | **None.** Verify health only (regression canary — it breaks if `amjis-web` breaks). |

> RULING 1's directive named `amjis-mcp` as a probable consumer. **It is not one.** Confirmed by
> full `gcloud run services describe` env dump (§8 probe E). The runtime migration surface is two
> services, not three.

### 2.2 — Production batch (Cloud Run jobs)

| Consumer | Role | How it obtains the credential | Credential | Migration action |
|---|---|---|---|---|
| **`brahma-build-pipeline-job`** | `amjis_app` | `DATABASE_URL` ← `secretKeyRef amjis-pipeline-db-url` key **`latest`**; Cloud SQL socket annotation; SA `amjis-web-runtime@`. The orchestrator job that runs chart builds. | INC-2 | **Required (passive).** Reads `latest` at each execution — no redeploy needed, but must not be mid-execution during the cutover. |
| **`brahma-foundation-bootstrap`** | — | No DB env (`BRAHMA_PLACEHOLDER=true`); no Cloud SQL annotation; SA `amjis-builder-runtime@`. | n/a | **None.** |

### 2.3 — CI / GitHub Actions — including the two production-proxying workflows (RULING 21)

DVA RULING 21 required that both workflows opening a Cloud SQL Auth Proxy to production be recorded
as **named consumers** with their authenticating role established, on the grounds that a rotation
that misses them turns green CI red at the worst possible moment. Both were investigated.

> **v1.0 CORRECTION.** v1.0 of this document recorded "no credential literal found" for
> `shad-darshana-circularity-guard.yml`. **That was wrong.** It grepped the workflow file only, not
> the test file the workflow executes. The test carries a live effective-DB-administrator credential.

#### 2.3.1 — `shad-darshana-circularity-guard.yml` — **authenticates as `amjis_app` using INC-2**

| property | finding |
|---|---|
| Triggers | `workflow_dispatch`, nightly `cron: '17 20 * * *'`, and `push` to `main` touching `ka_*` writer paths |
| Proxy | `./cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres` (L66-68); WIF identity `github-actions@madhav-astrology.iam.gserviceaccount.com` |
| What it runs | `pytest platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py -m integration` |
| **Authenticating role** | **`amjis_app` — an effective database administrator (§1.5)** |
| **Credential source** | **A hard-coded literal.** `test_ka_jivana_parva_circularity_guard.py:64` — `LIVE_DSN = "postgresql://amjis_app:<INC-2>@127.0.0.1:5433/amjis"`. No env override; bare module-level assignment. |
| Runs to date | **Zero.** `gh run list --workflow=shad-darshana-circularity-guard.yml` returns no runs — the workflow is new (landed with ṢAḌ-DARŚANA PR #897). **It will begin firing nightly.** |
| Writes? | The workflow header states the test "reads/writes-then-rolls-back real rows for the canonical chart (482012f1)", opening one transaction and rolling back in a `finally`. |

**This is CI running against production as an effective database administrator, nightly, on a
credential that is public on GitHub.** It is also why INC-2's redaction cannot be treated as
cosmetic: redacting `test_ka_jivana_parva_circularity_guard.py:64` without supplying the credential
by another route **breaks a ṢAḌ-DARŚANA gate that campaign describes as "untouchable."**

**Ownership caveat (conductor manual §7):** the workflow and the test are ṢAḌ-DARŚANA surface. This
lane **read and reported only** — nothing was modified. Sequencing against B-SECRET-REDACT is a DVA
question.

**Migration action:** required, and the most delicate one. The correct end state is env indirection
(`os.environ["DATABASE_URL"]`) with the workflow supplying `DATABASE_URL` from Secret Manager — not
a replacement literal. Because the job only reads and rolls back, `retrieval_census_ro` is very
likely sufficient and would remove an effective-DB-administrator credential from CI entirely; that
call belongs to ṢAḌ-DARŚANA.

#### 2.3.2 — `fresh_chart_smoke.yml` — **declares role `postgres`; has never reached the DB**

| property | finding |
|---|---|
| Exists on `origin/main`? | **Yes** — confirmed by direct read from the `origin/main` worktree. (DVA noted its own earlier read was branch-lagged; the file is present and was investigated for real.) |
| Triggers | schedule + `workflow_dispatch`; explicitly *not* wired to push/PR (its header explains the job takes many hours) |
| Proxy | `./cloud-sql-proxy --address 127.0.0.1 --port 5433 …` (L99-101), WIF identity `github-actions@`, **no `--auto-iam-authn` flag** |
| **Declared role** | **`postgres` — the other effective database administrator (§1.5)**, at L147: `PROD_DATABASE_URL: postgresql://postgres@127.0.0.1:5433/amjis` |
| **Credential source** | **None in the file.** The DSN is passwordless; there is no `PGPASSWORD` for the production connection anywhere in the workflow. **Confirmed: this workflow carries no literal credential.** (The `PGPASSWORD: postgres` at L183 and `postgres:postgres` DSN at L184 belong to the *ephemeral local service container*, not production.) |
| Does it work? | **Unproven, and almost certainly not.** `postgres` is a `BUILT_IN` Cloud SQL user, not an IAM user, so `--auto-iam-authn` could not help even if it were set — and it is not. A passwordless libpq connection to Cloud SQL should fail with `fe_sendauth: no password supplied`. |
| Empirical evidence | Exactly **one** run in its history — `id=30425772357`, 2026-07-29, **conclusion: failure** — and it failed at *"Authenticate to Google Cloud"*. Every subsequent step, including *"Start Cloud SQL Auth Proxy"* and *"Snapshot production schema…"*, is recorded as **`skipped`**. **The DB step has never executed.** |

**What this means for the rotation.** Not a *live* consumer today, but a **declared** one: it states
an intent to read production as `postgres`. If the WIF failure is fixed without also fixing the
role, the first successful run becomes an INC-3-class consumer — CI reading the whole production
corpus as an effective database administrator. The workflow's own header anticipates this, calling
it a *"follow-up hygiene item: provision a dedicated read-only DB role for this job."*

**Migration action:** required, and it should be resolved *before* the WIF failure is fixed, not
after. The job only ever `pg_dump`s and `SELECT`s (its header is explicit). `retrieval_census_ro`
already exists, is read-only, has its own managed secret, and is not exposed. Point the job at that
role — do **not** give it the rotated `postgres` password.

#### 2.3.3 — The rest of CI

| Workflow | How it obtains the credential | Status | Migration action |
|---|---|---|---|
| `deploy.yml` | **(a)** Migrations step (L203): `DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}` against a proxy on `127.0.0.1:5432`. Hard-fails if unset. **(b)** Deploy step (L304): `secrets:` declares `DB_PASSWORD=amjis-db-password:3` — **the version pin lives in the workflow file.** | GH secret `PROD_DATABASE_URL` exists, updated 2026-06-22. Its role/credential is **not readable** (GH secrets are write-only). | **Required, two edits** — step 5.7, the highest-risk step in the runbook. Step 5.8 audits the other 12 pins for the same trap. |
| `samiksha-daily.yml` | `DATABASE_URL: ${{ secrets.DATABASE_URL }}` (L63); step no-ops with exit 0 when unset (L67-69). | GH secret `DATABASE_URL` is **not configured** (§8 probe F). The daily sweep is a no-op today. | **None now.** If ever wired, it must use the new role. |
| `tap-ci.yml` | `DATABASE_URL: ${{ secrets.TAP_DATABASE_URL }}` (L106/112/118); passes when unset by design. | GH secret `TAP_DATABASE_URL` is **not configured**. | **None now.** Same rider. |

### 2.4 — Local developer / operator surface

| Consumer | How it obtains the credential | Credential | Migration action |
|---|---|---|---|
| `/Users/Dev/.claude.json` → `mcpServers.postgres.args[2]` | Plaintext DSN `postgresql://amjis_app:<literal>@127.0.0.1:5433/amjis` in the developer's Claude config (outside the repo). | **INC-2** | **Required.** Update after rotation or the local Postgres MCP breaks. Not a repo file — will be missed by any repo-scoped scanner, including the fixed one. |
| `build_orchestrator/scripts/{hard_gates_check,preflight,apply_migration}.sh` | Hard-coded literal (§1.2). Retired scaffold; assume unused. | INC-1 (dead) | Redaction only — B-SECRET-REDACT. Already non-functional. |
| `build_orchestrator/operator_runs/2026-05-30/.psql_url` | Hard-coded DSN, one line. | INC-1 (dead) | Redaction only. |
| `platform/migrations/__tests__/test_mig_12{4,5,6,7}.py` | Hard-coded literal in test setup. | INC-1 (dead) | Redaction only. These tests cannot currently connect. |
| `platform/python-sidecar/**` (13 files, §1.3) | `os.environ.get(..., "<live literal>")` fallback, or bare literal. **One is executed by nightly CI — §2.3.1.** | **INC-2** | **Required.** Env indirection per RULING 2 **and** the literal must not be replaced with the *new* credential — replace with a fail-fast env read. |
| `platform/scripts/governance/v13_production_gate.py:13` | `os.environ.get("DB_PASSWORD", "<live literal>")`. | **INC-2** | **Required.** Same treatment. |
| `platform/src/lib/db/seed/observatory_pricing/run_seed.ts:74` | Hard-coded DSN. | **INC-3** (`postgres`) | **Required.** A seed script should never run as an effective DB administrator. |
| `00_ARCHITECTURE/MIGRATION_APPLY_INSTRUCTIONS_v1_0.md:71` | Documented copy-paste DSN. | **INC-3** | **Required.** This is the copy-paste seed that propagated the pattern. |
| `docs/superpowers/plans/2026-06-1{7,21}-*.md` | Transcribed command output inside plan documents (9 occurrences). | **INC-2** | **Required.** Historical plan docs — redact in place; they are not executable. |

### 2.5 — Roles present on the instance

| Role | Attributes | Objects | Credential status |
|---|---|---|---|
| `amjis_app` | `LOGIN`, `CREATEDB`, `CREATEROLE`, member of `cloudsqlsuperuser`, no conn limit, **no expiry** | Owns schemas `public` and `auth`; **owns all 291 tables in `public`** | **INC-2 — LIVE, public. Effective DB administrator.** |
| `postgres` | `LOGIN`, `CREATEDB`, `CREATEROLE`, member of `cloudsqlsuperuser`, **no expiry** | — | **INC-3 — LIVE, public. Effective DB administrator.** |
| `retrieval_census_ro` | `LOGIN`, conn limit **5**, no CREATE rights; `USAGE` on `public`; default ACL grants `SELECT` on future `amjis_app` tables | none | Secret `retrieval-census-ro-db-password` v1 (2026-07-19). **Not exposed** — verified absent from the working tree and from git history. Untouched by this runbook, and the natural target for both §2.3 CI jobs. |

**The ownership fact that shapes the runbook:** `amjis_app` owns every object. Dropping it, or
reassigning ownership, would be a large and risky operation. `ALTER ROLE ... NOLOGIN` disables
authentication while leaving ownership and group semantics intact — which is why §5 disables rather
than deletes, and why the new role is granted **membership in** `amjis_app` rather than a
reconstructed grant set.

---

## §3 — Compromise assessment (RULING 22) — best-effort, read-only

> **HARD FRAMING, per DVA RULING 22.** Everything below establishes, at most, **"no evidence of
> misuse in the window we can see."** That is the only conclusion the evidence supports and it is
> the only phrasing used. **Nothing in this section may be read, cited, or paraphrased as "not
> compromised."** §3.6 states the limits precisely.

### 3.1 — The instrument, and why it is stronger here than expected

Cloud SQL does not log database-level authentication by default (pgAudit is not enabled), so *which
DB role* a given session used is not recoverable. However:

- `authorizedNetworks` is empty (R1), so the Cloud SQL Auth Proxy / connector is the **only** path
  to the instance;
- every connector handshake emits a `cloudsql.instances.connect` **Admin Activity** audit entry
  carrying the **GCP principal** that obtained it.

The set of GCP identities that have reached the instance is therefore fully enumerable, even though
the DB role they used is not. Because a leaked DB credential is useless without one of those
identities (§1.7), the principal list is a genuine — if indirect — misuse detector.

**Retention is far better than assumed.** DVA's ruling anticipated *"roughly 30 days against a much
longer exposure window."* That is the Data Access default; Admin Activity logs sit in the
`_Required` bucket with a 400-day retention that cannot be shortened. Probed directly:

```
$ gcloud logging read '…resource.type="cloudsql_database" AND timestamp<"2026-04-26T00:00:00Z"' \
    --limit=5 --freshness=400d
2026-04-25T23:26:57Z  cloudsql.instances.connect  mail.abhisek.mohanty@gmail.com
2026-04-25T23:06:54Z  cloudsql.instances.connect  938361928218-compute@developer.gserviceaccount.com
2026-04-25T23:03:47Z  cloudsql.instances.connect  938361928218-compute@developer.gserviceaccount.com
```

The instance was created 2026-04-25T11:59:51Z. **Connect-event coverage begins the same day and is
continuous to the present** — it covers **100% of the exposure window of all three credentials**
(INC-3 from 2026-04-29, INC-1 from 2026-05-29, INC-2 from 2026-06-05). This is a materially better
epistemic position than RULING 22 assumed, and is reported as such. It does **not** repair the
limits in §3.6.

### 3.2 — Every principal that has ever connected

Enumerated by two complementary methods: a positive aggregation, and negative queries that exclude
each identified principal and ask whether anything remains.

| principal | kind | connects (30d) | first seen | last seen | attributable to |
|---|---|---|---|---|---|
| `amjis-web-runtime@…` | Cloud Run SA | 1,796 | ongoing | ongoing | `amjis-web` (§2.1) |
| `mail.abhisek.mohanty@gmail.com` | the native | 712 | 2026-04-25 | ongoing | operator sessions — **includes this lane's own read-only probes** |
| `github-actions@…` | WIF CI SA | 528 | ongoing | ongoing | `deploy.yml` migrations + the §2.3 workflows |
| `amjis-sidecar-runtime@…` | Cloud Run SA | 89 | ongoing | ongoing | `amjis-sidecar` (§2.1) |
| `marsys-pipeline-writer@…` | project SA | **0** | 2026-05-30 | **2026-06-01** | retired build-orchestrator operator-run era (`operator_runs/2026-05-30/`); source IPs Google-owned `2600:1900::/…` |
| `938361928218-compute@developer…` | default compute SA | **0** | **2026-04-25** | **2026-05-28** | early bootstrap / Cloud Build path; source IP `34.96.40.27` (Google-owned) |

**Exhaustiveness test.** Excluding all six principals over the retained window returned **zero rows**
(§8 probe CA-16b, window 2026-04-25 → 2026-07-01; and probe CA-10, last 30 days excluding only the
four current ones, also zero). **No seventh identity has ever connected to this instance.**

**Disposition of the two extra principals.** Both are internal to the native's own GCP project
(`@madhav-astrology.iam.gserviceaccount.com` / `@developer.gserviceaccount.com`), both connected
from Google-owned address space, and both correspond to identifiable historical project activity.
**Neither is external and neither is anomalous on its face.** Both are nonetheless **dormant with
live grants** — zero connections in 30 days, still enabled, still holding `roles/cloudsql.client`
(§1.7). They are standing risk, not evidence of misuse.

### 3.3 — Administrative-plane history

`gcloud sql operations list` returns the instance's complete operation history — **123 operations
back to creation on 2026-04-25**, i.e. the full exposure window. Stripping routine daily backups
leaves 17 events:

```
2026-04-25T11:59:57Z  CREATE           mail.abhisek.mohanty@gmail.com
2026-04-25T12:04:01Z  CREATE_DATABASE  mail.abhisek.mohanty@gmail.com
2026-04-25T12:04:04Z  CREATE_USER      mail.abhisek.mohanty@gmail.com
2026-04-25T12:04:26Z  UPDATE_USER      mail.abhisek.mohanty@gmail.com
2026-05-28T12:33:54Z  UPDATE_USER      mail.abhisek.mohanty@gmail.com   ← = amjis-db-password v2 (INC-1)
2026-05-28T12:48:48Z  UPDATE           mail.abhisek.mohanty@gmail.com
2026-05-28T12:58:16Z  UPDATE           mail.abhisek.mohanty@gmail.com
2026-05-28T13:04:24Z  UPDATE           mail.abhisek.mohanty@gmail.com
2026-05-28T18:16:57Z  FAILOVER         mail.abhisek.mohanty@gmail.com
2026-05-28T18:30:45Z  UPDATE           mail.abhisek.mohanty@gmail.com
2026-05-28T18:35:46Z  UPDATE           mail.abhisek.mohanty@gmail.com
2026-06-02T16:23:52Z  EXPORT           mail.abhisek.mohanty@gmail.com
2026-06-02T17:16:22Z  DELETE_BACKUP    mail.abhisek.mohanty@gmail.com
2026-06-02T17:43:41Z  UPDATE_USER      mail.abhisek.mohanty@gmail.com   ← = amjis-db-password v3 (INC-2)
2026-06-02T17:54:38Z  UPDATE           mail.abhisek.mohanty@gmail.com
2026-06-07T00:51:37Z  MAINTENANCE      (Google)
2026-07-16T16:07:40Z  UPDATE           mail.abhisek.mohanty@gmail.com
```

Findings:

- **Every non-automated operation across the instance's entire life is attributed to
  `mail.abhisek.mohanty@gmail.com`.** No third-party principal appears anywhere on the admin plane.
  The corresponding audit-log view (non-connect methods) agrees and adds the 2026-05-28
  clone/failover/delete sequence — also all the native.
- **Exactly one `CREATE_USER`**, at instance bootstrap. No user created through the Admin API since.
- **Exactly three `UPDATE_USER` events**, correlating 1:1 with the three `amjis-db-password`
  versions (2026-04-25 → v1, 2026-05-28 → v2/INC-1, 2026-06-02 → v3/INC-2). This independently
  corroborates §1.2's Secret-Manager-to-database timeline and confirms all three password changes
  were made by the native's own account.
- **Seven `cloudsql.instances.update` config changes.** Whether any transiently added an
  `authorizedNetworks` entry is **not established** — §3.6 item 4, RES-8.

### 3.4 — Persistence sweep (the §1.5 escalation vector)

The highest-signal indicator for a `CREATEROLE` compromise is an unexpected role. Full enumeration:

```sql
SELECT rolname, rolcanlogin, rolcreaterole, rolcreatedb, rolsuper, rolreplication
FROM pg_roles ORDER BY rolname;    -- 30 rows
```

- **30 roles total: 27 are PostgreSQL / Cloud SQL built-ins** (`pg_*`, `cloudsql*`) **and 3 are
  project roles** — `amjis_app`, `postgres`, `retrieval_census_ro`. **No unexpected role exists.**
- The full `pg_auth_members` grant graph (13 edges) contains no anomalous grant: the only
  non-built-in memberships are `amjis_app → cloudsqlsuperuser` and `postgres → cloudsqlsuperuser`,
  both `admin_option = f`, both expected.
- No role carries `rolreplication` other than the Cloud SQL built-ins.

**This is the cleanest signal available and it is clean.** It is also the signal that matters most —
because, per the next paragraph, it is the *only* place in-database persistence would show.

**A caveat that cuts both ways, and it is important.** `retrieval_census_ro` was created around
2026-07-19 (its secret's creation timestamp), yet **no `CREATE_USER` admin operation exists for it**
(§3.3 shows only one, at bootstrap). It was therefore created with in-SQL `CREATE ROLE`, not through
the Admin API. **This proves, from this instance's own history, that in-SQL role creation is
invisible to the administrative audit trail** — exactly the mechanism §1.5 identifies as the
persistence vector. The admin-plane cleanliness in §3.3 therefore does **not** cover in-DB
persistence at all. The role enumeration above is the only instrument that does, and its clean
result is a point-in-time observation, not a historical one: a role created and later dropped would
leave no trace either way.

### 3.5 — Live connection state

`pg_stat_activity` at the time of probing showed only this lane's own two `psql` sessions plus
`cloudsqladmin`/`cloudsqlagent` internals. **This is a weak instrument and is reported as such:** a
single point sample that did not even capture the production services' pooled connections, and says
nothing about any earlier period. Recorded for completeness, not as evidence.

### 3.6 — Epistemic limits — read this before citing anything above

**The honest conclusion is: no evidence of misuse in the window we can see.** Specifically:

1. **"No evidence of misuse" is not "not compromised."** The queries above can show only that no
   *unexpected GCP identity* reached the instance and that no *currently-existing* role is
   unexpected. They cannot show that a legitimate identity was not itself compromised and used to
   carry a leaked DB credential — which is precisely the attack the §1.7 denominator describes, and
   it would appear in these logs as ordinary traffic from `amjis-web-runtime` or `github-actions`.
2. **Database-level authentication is not logged.** pgAudit is not enabled. There is no record
   anywhere of *which DB role* any session authenticated as, or of failed authentication attempts.
   A successful use of INC-2 or INC-3 by a compromised project identity would leave **no
   distinguishing trace whatsoever**.
3. **In-database persistence is invisible to the audit trail** — demonstrated by this instance's own
   `retrieval_census_ro` (§3.4). A role created and dropped inside the exposure window is
   unrecoverable.
4. **`authorizedNetworks` change history is not established.** `gcloud sql operations describe` does
   not return request bodies, and this lane did not retrieve the per-update request payloads from
   the audit log. Seven `cloudsql.instances.update` operations occurred (§3.3); the **current**
   value is null, but whether a CIDR was transiently present is **unknown**. This is the single most
   consequential gap, because such an entry is exactly the event that would have converted this leak
   into a directly usable one. It is answerable — RES-8 gives the query — and this lane did not
   answer it.
5. **Data-plane forensics are foreclosed.** PITR is off and only 7 daily backups are retained (R6).
   There is **no pre-exposure restore point for INC-3**, whose exposure began 2026-04-29. Tampering
   older than 7 days could be neither detected by diff nor undone.
6. **This project has no queryable long-horizon event history** of its own. Everything above rests
   on Google-side retention — a rolling 400-day window that will begin dropping the earliest
   exposure days from 2027-05-30 onward. **If the RES-8 question is to be answered at all, it should
   be answered soon.**

**No result in §3 discharges the rotation.** Rotation is required regardless of what the logs show,
because the credentials are public and permanent (§1.1).

---

## §4 — Pre-execution checklist (native)

- [ ] **4.1** Confirm no build is in flight: no `brahma-build-pipeline-job` execution running, and
      SAMĀPTI's BUILD-LOCK is free. A mid-rebuild cutover risks a half-written asset.
- [ ] **4.2** Confirm no deploy is in flight and no PR is auto-merging. A `deploy.yml` run landing
      between steps 5.6 and 5.7 will re-pin `amjis-web` to the old secret version.
- [ ] **4.3** Confirm the nightly `shad-darshana-circularity-guard.yml` (20:17 UTC) is not about to
      fire, or disable it for the maintenance window. It authenticates as `amjis_app` from a
      hard-coded literal (§2.3.1) and **will fail the moment `amjis_app` is set `NOLOGIN`**.
- [ ] **4.4** Take a fresh on-demand backup: `gcloud sql backups create --instance=amjis-postgres`.
      PITR is off (R6); this is the only rollback floor.
- [ ] **4.5** Record the current serving revisions so a rollback target exists:
      `gcloud run services describe amjis-web --region=asia-south1 --format='value(status.traffic)'`
      (and the same for `amjis-sidecar`).
- [ ] **4.6** Decide the new role name. This document uses **`amjis_app_v2`**. Choose once.
- [ ] **4.7** Generate the new password with a CSPRNG, never by hand, never in shell history:
      `python3 -c "import secrets;print(secrets.token_urlsafe(32))"` — and pipe it straight to
      `gcloud secrets versions add` (step 5.4). **Never paste it into a file.**

---

## §5 — Zero-downtime rotation runbook

> **NOT EXECUTED. This is a written procedure for the native.** Every command below that mutates
> state was deliberately **not run** by this lane. Only the read-only probes in §8 were run.
>
> Design principle: **additive first, subtractive last.** At no point between 5.2 and 5.9 is any
> working credential invalidated, so every step before 5.10 is abandonable by stopping.

### Phase 0 — Establish the facts the rotation depends on

**5.1 — Persistence sweep BEFORE touching anything (RULING 18 / §1.5).**

Because both leaked credentials hold `CREATEROLE` and can mint a role that survives their own
rotation, the rotation is only meaningful if no such role already exists. Capture the baseline:

```bash
cloud-sql-proxy --address 127.0.0.1 --port 5433 \
  madhav-astrology:asia-south1:amjis-postgres &
psql -h 127.0.0.1 -p 5433 -U postgres -d amjis
```

```sql
SELECT rolname, rolcanlogin, rolcreaterole, rolcreatedb, rolsuper, rolreplication, rolvaliduntil
FROM pg_roles ORDER BY rolname;                                    -- expect exactly 30 rows
SELECT r.rolname AS member, g.rolname AS granted, m.admin_option
FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
                       JOIN pg_roles g ON g.oid=m.roleid ORDER BY 1,2;  -- expect exactly 13 rows
```

**Save this output.** Step 5.12 diffs against it. Expected: the 3 project roles plus 27 built-ins,
and the 13 grant edges in §8 probe D. **Any additional login role, or any additional grant of
`cloudsqlsuperuser`, is a persistence artefact — STOP the rotation and escalate**, because at that
point rotation is not the remediation (§1.5).

**5.2 — Confirm, do not assume, which enabled Secret Manager version carries the leaked literal
(RULING 18(a)).**

This lane already performed this confirmation (§1.2): `amjis-db-password` **v2** and
`amjis-pipeline-db-url` **v2** carry INC-1, **v3** of both carries INC-2, and all four are
`enabled`. Re-confirm at execution time, because a version may have been added since. Compare by
hash; never print a payload:

```bash
for s in amjis-db-password amjis-pipeline-db-url; do
  for v in $(gcloud secrets versions list "$s" --filter="state=ENABLED" --format="value(name)"); do
    printf '%s v%s -> %s\n' "$s" "$v" \
      "$(gcloud secrets versions access "$v" --secret="$s" | shasum -a 256 | cut -c1-16)"
  done
done
```

Match the fingerprints against the §0 table (`bd14b4e7cbc6c972` = INC-1, `9916bb655a303c81` =
INC-2). **Record which versions matched. Step 5.10 disables exactly those and nothing else** —
disabling a version you have not fingerprinted is how a working consumer gets broken by accident.

### Phase A — Create the replacement role (additive; zero risk to running services)

**5.3 — Create the new Postgres role.**

`amjis_app` owns all 291 tables and both schemas. Do **not** reconstruct its grant set
table-by-table — grant membership in it instead, which is exact by construction and cannot drift.

```sql
-- new login role; password supplied interactively, never in shell history
CREATE ROLE amjis_app_v2 WITH LOGIN PASSWORD '<NEW-PASSWORD-FROM-4.7>';

-- exact privilege equivalence, by membership rather than reconstruction
GRANT amjis_app TO amjis_app_v2;
GRANT cloudsqlsuperuser TO amjis_app_v2;

-- match the attributes read in §8 probe D
ALTER ROLE amjis_app_v2 CREATEDB CREATEROLE;

-- CRITICAL: make objects created by v2 (i.e. migrations) owned by amjis_app,
-- not by amjis_app_v2. Without this, ownership fragments across two roles and
-- the next rotation becomes far harder than this one.
ALTER ROLE amjis_app_v2 IN DATABASE amjis SET role TO amjis_app;
```

> **Consider narrowing while you are here.** `CREATEDB`/`CREATEROLE` are what make this an
> effective-DB-administrator credential (§1.5). Nothing in the consumer inventory needs them —
> `amjis-web`, `amjis-sidecar`, and the build job read and write rows; `deploy.yml` runs DDL
> migrations, which membership in the owning role already covers. Omitting `CREATEDB CREATEROLE`
> would make the *next* leak far less severe. This is a deliberate deviation from strict
> equivalence — called out, not silently applied, because it changes behaviour and §5's contract is
> "equivalent grants." **Recommended; native's call.** RES-9.

> **Alternative (simpler, if the native prefers no second role):** skip Phase A and just
> `gcloud sql users set-password amjis_app --instance=amjis-postgres --prompt-for-password`, then
> update every secret. **This is not zero-downtime** — every consumer breaks the instant the
> password changes and stays broken until each is repointed. RULING 1 asked for the two-role path
> precisely to avoid that window. Use the two-role path.

**5.4 — Verify the new role, then add new Secret Manager versions (additive).**

```sql
SELECT rolname, rolcanlogin, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname='amjis_app_v2';
SELECT g.rolname FROM pg_auth_members m
  JOIN pg_roles r ON r.oid=m.member JOIN pg_roles g ON g.oid=m.roleid
  WHERE r.rolname='amjis_app_v2';   -- expect: amjis_app, cloudsqlsuperuser
```

Prove it works, from a separate shell:

```bash
PGPASSWORD='<NEW>' psql -h 127.0.0.1 -p 5433 -U amjis_app_v2 -d amjis \
  -tAc "SELECT current_user, count(*) FROM chart_facts;"
# expect: amjis_app_v2|27554   (the L1_GANITA_CLOSURE canonical count)
```

A wrong or zero count means the grant is wrong. **Stop and fix before Phase B.** Then:

```bash
# app password — piped, never written to a file, never echoed
printf '%s' '<NEW-PASSWORD>' | gcloud secrets versions add amjis-db-password --data-file=-

# pipeline DSN — same credential, socket form, matching the shape of v3
printf '%s' 'postgresql://amjis_app_v2:<NEW-PASSWORD>@/amjis?host=/cloudsql/madhav-astrology:asia-south1:amjis-postgres' \
  | gcloud secrets versions add amjis-pipeline-db-url --data-file=-
```

Record the version numbers returned (they will be **4** for both if no one else has added versions).
Verify without printing payloads:

```bash
gcloud secrets versions list amjis-db-password    --format="table(name,state,createTime)"
gcloud secrets versions list amjis-pipeline-db-url --format="table(name,state,createTime)"
```

> **Note:** `amjis-db-password` holds a bare password (consumed as `DB_PASSWORD` alongside
> `DB_USER=amjis_app`), while `amjis-pipeline-db-url` holds a full DSN that embeds the **username**.
> Because the username changes to `amjis_app_v2`, `amjis-web` **also** needs its `DB_USER` env var
> changed — see 5.6. Missing this is the most likely cause of a failed cutover.

### Phase B — Migrate consumers one at a time, verifying after each

**5.5 — `amjis-sidecar` (first — lowest blast radius, `latest`-bound).**

```bash
gcloud run services update amjis-sidecar --region=asia-south1 \
  --update-secrets=DATABASE_URL=amjis-pipeline-db-url:latest \
  --update-env-vars=ROTATION_STAMP=$(date +%s)
```

`ROTATION_STAMP` forces a new revision so the `latest` binding is actually re-read (the established
convention already present on both `amjis-web` and `amjis-sidecar`).

**Verify before proceeding:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://amjis-sidecar-qm256lasva-el.a.run.app/health   # 200
gcloud run services describe amjis-sidecar --region=asia-south1 \
  --format="value(status.latestReadyRevisionName,status.conditions[0].status)"
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-sidecar"
   AND (textPayload:"password authentication failed" OR textPayload:"does not exist")' \
  --limit=20 --freshness=10m
```

Expect the log query to return **nothing**. If it returns rows, roll back with
`gcloud run services update-traffic amjis-sidecar --region=asia-south1 --to-revisions=amjis-sidecar-00933-f9j=100`
and stop.

**5.6 — `amjis-web` (second — the user-facing service).**

Two changes in one revision — the secret version **and** `DB_USER`:

```bash
gcloud run services update amjis-web --region=asia-south1 \
  --update-secrets=DB_PASSWORD=amjis-db-password:4 \
  --update-env-vars=DB_USER=amjis_app_v2,ROTATION_STAMP=$(date +%s)
```

**Verify:**

```bash
curl -s https://amjis-web-qm256lasva-el.a.run.app/api/health        # expect {"status":"ok"}
# a DB-backed read, not just the liveness probe — health can be green with a dead pool
curl -s -o /dev/null -w "%{http_code}\n" https://amjis-web-qm256lasva-el.a.run.app/api/charts
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-web"
   AND severity>=ERROR' --limit=30 --freshness=10m
```

Roll back to `amjis-web-01281-p25` on any failure.

**5.7 — `deploy.yml` and the GitHub Actions secrets — THE ORDERING IS NOT OPTIONAL (RULING 18(b)).**

`deploy.yml:304` hard-codes `DB_PASSWORD=amjis-db-password:3`. The two failure modes are symmetric
and both are real:

| mistake | consequence |
|---|---|
| **Disable v3 without bumping the pin** | The next `deploy.yml` run resolves `amjis-db-password:3`, gets a disabled version, and the deploy fails — or deploys a revision that cannot reach the database. **Production breaks at the next unrelated merge**, and the outage is attributed to that PR rather than to the rotation. |
| **Bump the pin without disabling v3** | The rotation is cosmetic. The leaked credential remains valid and the incident is not remediated. |

**The required sequence is strictly: create v4 (5.4) → bump the pin to `:4` and prove it by
deploying (5.7) → only then disable v2 and v3 (5.10).** Do not reorder. Do not compress. Do not
disable anything until a deploy has landed green on `:4`.

1. Determine what `PROD_DATABASE_URL` currently holds. It is not readable via the API; check the
   native's own record. If unknown, **replace it regardless** — an unknown-provenance production
   DSN is itself a finding.
2. Rewrite it to the new role:
   ```bash
   printf '%s' 'postgresql://amjis_app_v2:<NEW-PASSWORD>@127.0.0.1:5432/amjis' | gh secret set PROD_DATABASE_URL
   ```
   (Port 5432 — that is the port `deploy.yml:189` starts the proxy on. The §2.3 workflows use 5433.
   Do not conflate them.)
3. Edit `deploy.yml:277` `DB_USER=amjis_app` → `DB_USER=amjis_app_v2` and `deploy.yml:304`
   `DB_PASSWORD=amjis-db-password:3` → `:4`. Land as a normal PR.
4. **Verify by running a deploy** and re-checking that `amjis-web`'s serving revision carries
   `amjis-db-password:4` and `DB_USER=amjis_app_v2`. A rotation that survives one deploy cycle is
   rotated; one that has not been deploy-tested is not.

**5.8 — Audit ALL 13 version-pinned secrets in `deploy.yml`, not just line 304 (RULING 18(c)).**

Line 304 is one instance of a general trap: **any numerically-pinned secret is a silent revert
waiting for its own rotation.** The complete set on `origin/main` today — note the actual line
numbers; RULING 18 cited 458-459 for what is in fact 468-469:

| # | line | binding | secret : pin |
|---|---|---|---|
| 1 | 303 | `FIREBASE_ADMIN_CREDENTIALS` | `firebase-admin-credentials:1` |
| 2 | **304** | **`DB_PASSWORD`** | **`amjis-db-password:3`** ← this rotation |
| 3 | 305 | `OPENAI_API_KEY` | `openai-api-key:2` |
| 4 | 306 | `GOOGLE_GENERATIVE_AI_API_KEY` | `GOOGLE_GENERATIVE_AI_API_KEY:1` |
| 5 | 307 | `DEEPSEEK_API_KEY` | `DEEPSEEK_API_KEY:1` |
| 6 | 308 | `NVIDIA_NIM_API_KEY` | `NVIDIA_NIM_API_KEY:1` |
| 7 | 309 | `PYTHON_SIDECAR_API_KEY` | `PYTHON_SIDECAR_API_KEY:1` |
| 8 | 310 | `SUPER_ADMIN_EMAIL` | `SUPER_ADMIN_EMAIL:1` |
| 9 | 312 | `MCP_INTERNAL_TOKEN` | `mcp-internal-token:1` |
| 10 | 390 | `PYTHON_SIDECAR_API_KEY` (sidecar) | `PYTHON_SIDECAR_API_KEY:1` |
| 11 | 391 | `GOOGLE_GENERATIVE_AI_API_KEY` (sidecar) | `GOOGLE_GENERATIVE_AI_API_KEY:1` |
| 12 | 468 | `MCP_INTERNAL_TOKEN` (mcp) | `mcp-internal-token:1` |
| 13 | 469 | `PYTHON_SIDECAR_API_KEY` (mcp) | `PYTHON_SIDECAR_API_KEY:1` |

*(Lines 311, 313, 470 use `:latest` and are not subject to the trap:
`mcpt-scheduler-secret:latest`, `mcp-canary-key:latest`, `mcp-canary-key:latest`.)*

Regenerate rather than trusting the table:

```bash
grep -nE "^[[:space:]]+[A-Z_]+=[a-zA-Z0-9_-]+:[0-9]+[[:space:]]*$" .github/workflows/deploy.yml
```

For each, confirm the pinned version is still `enabled`:

```bash
for s in firebase-admin-credentials amjis-db-password openai-api-key \
         GOOGLE_GENERATIVE_AI_API_KEY DEEPSEEK_API_KEY NVIDIA_NIM_API_KEY \
         PYTHON_SIDECAR_API_KEY SUPER_ADMIN_EMAIL mcp-internal-token; do
  echo "== $s"; gcloud secrets versions list "$s" --format="table(name,state,createTime)"
done
```

**Recommendation, not part of the rotation:** the pins prevent surprise credential changes, but they
convert every future rotation into a two-place edit whose second place is easy to forget. Either
move to `:latest` with an explicit revision bump in the deploy step, or add a CI check that fails
when a workflow pins a version that is not the highest enabled one. RES-11.

**5.9 — The remaining consumers.**

- **`brahma-build-pipeline-job`** — bound to `amjis-pipeline-db-url:latest`; picks up the new
  version at its next execution, no config change. Prove it rather than assuming:
  `gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 --wait`.
- **`shad-darshana-circularity-guard.yml`** (§2.3.1) — **will break at step 5.11.** It reads INC-2
  from `test_ka_jivana_parva_circularity_guard.py:64`. Coordinate with B-SECRET-REDACT and
  ṢAḌ-DARŚANA: the test must take its DSN from `os.environ["DATABASE_URL"]` and the workflow must
  supply it. Strongly prefer `retrieval_census_ro` — it only reads and rolls back.
- **`fresh_chart_smoke.yml`** (§2.3.2) — declares `postgres`. Repoint to `retrieval_census_ro`
  **before** its WIF failure is repaired, so its first successful run is not an
  effective-DB-administrator session.
- **Local dev** — update `/Users/Dev/.claude.json` → `mcpServers.postgres.args[2]`, preferably to an
  env-var reference so it never holds a literal again. Confirm no other machine or shell profile
  holds the old password.

### Phase C — Disable the leaked roles, then prove nothing depended on them

**5.10 — Disable the fingerprinted Secret Manager versions.**

Only now, and only the versions fingerprinted in 5.2:

```bash
gcloud secrets versions disable 2 --secret=amjis-db-password      # INC-1
gcloud secrets versions disable 3 --secret=amjis-db-password      # INC-2
gcloud secrets versions disable 2 --secret=amjis-pipeline-db-url  # INC-1
gcloud secrets versions disable 3 --secret=amjis-pipeline-db-url  # INC-2
```

Disable, do not destroy — a disabled version can be re-enabled if a forgotten consumer surfaces; a
destroyed one cannot. Revisit after a full week of clean operation and destroy then.

**5.11 — Confirm zero remaining use of the old roles, then disable them.**

First, positive evidence that no session is authenticating as `amjis_app`:

```sql
SELECT usename, application_name, client_addr, count(*), max(backend_start)
FROM pg_stat_activity GROUP BY 1,2,3 ORDER BY 1;
```

`amjis_app` must not appear. Because that is a point sample, also check a window:

```bash
gcloud logging read \
  'resource.type="cloudsql_database" AND resource.labels.database_id="madhav-astrology:amjis-postgres"
   AND textPayload:"connection authorized: user=amjis_app "' \
  --limit=50 --freshness=2h
```

(The trailing space matters — it excludes `amjis_app_v2`.) When both are clean:

```sql
-- DISABLE, do not DROP. amjis_app owns all 291 tables and both schemas; NOLOGIN
-- removes authentication while preserving ownership and the group membership
-- amjis_app_v2 inherits from.
ALTER ROLE amjis_app NOLOGIN;
```

Then rotate INC-3 — the live effective-DB-administrator credential public for 92 days. Not optional:

```bash
gcloud sql users set-password postgres --instance=amjis-postgres --prompt-for-password
# then store it, so it stops being unmanaged:
printf '%s' '<NEW-POSTGRES-PASSWORD>' | gcloud secrets create amjis-postgres-superuser-password --data-file=-
```

Resolve `fresh_chart_smoke.yml` (5.9) before this, or accept that the next repair of that workflow
will need the new value.

**5.12 — Prove it, including the persistence re-check.**

The rotation is only demonstrated if the old credentials are shown to be *dead*, not merely
*unused* — and only complete if no persistence artefact appeared during the window:

```bash
# expect: FATAL: role "amjis_app" is not permitted to log in
PGPASSWORD='<OLD-INC-2>' psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -w -tAc "SELECT 1;"

# expect: FATAL: password authentication failed for user "postgres"
PGPASSWORD='<OLD-INC-3>' psql -h 127.0.0.1 -p 5433 -U postgres -d amjis -w -tAc "SELECT 1;"

# services healthy 30+ minutes after the disable
curl -s https://amjis-web-qm256lasva-el.a.run.app/api/health
curl -s https://amjis-mcp-qm256lasva-el.a.run.app/health
curl -s -o /dev/null -w "%{http_code}\n" https://amjis-sidecar-qm256lasva-el.a.run.app/health
```

Then re-run **step 5.1's two queries** and diff against the saved baseline. Expected delta: exactly
one new role (`amjis_app_v2`) and exactly two new grant edges (`amjis_app_v2 → amjis_app`,
`amjis_app_v2 → cloudsqlsuperuser`). **Anything else is a persistence artefact and the incident
escalates beyond rotation** (§1.5).

**5.13 — Watch for stragglers for 72 hours.**

```bash
gcloud logging read \
  'resource.type="cloudsql_database"
   AND (textPayload:"password authentication failed" OR textPayload:"is not permitted to log in")' \
  --limit=100 --freshness=72h
```

Any hit names a consumer this inventory missed. Add it here before closing the incident. Expect at
minimum a hit from `shad-darshana-circularity-guard.yml` if 5.9 was not completed.

### Phase D — Close the incident

**5.14 —** Append an EXECUTION RECORD to §9: date, who executed, new role name, new secret version
numbers, revision ids before/after, the 5.12 output including the role diff, and the 5.13 result.
Change this document's frontmatter `status` to `RESOLVED` and bump the version. **Until that record
exists, the incident is open.**

### Rollback

| Step reached | How to undo |
|---|---|
| 5.1–5.4 | Nothing to undo; the additions are inert. Optionally `DROP ROLE amjis_app_v2;` and disable the new secret versions. |
| 5.5–5.9 | `gcloud run services update-traffic <svc> --region=asia-south1 --to-revisions=<pre-rotation-revision>=100`. Revert the `deploy.yml` PR. Old credentials are still valid at this point. |
| 5.10 | `gcloud secrets versions enable <n> --secret=<name>`. |
| 5.11 (`NOLOGIN`) | `ALTER ROLE amjis_app LOGIN;` — instantly restores the old path. |
| 5.11 (`postgres` rotation) | Not reversible to the old value; recover by setting a further new password. Keep the new one in Secret Manager. |

---

## §6 — Recurrence guard

Rotation without these is a countdown to the fourth incident. The 2026-06-02 rotation is the proof:
it fixed INC-1 and produced INC-2 three days later.

**6.1 — `B-SECRETSCAN-SCOPE` (sibling lane, DVA RULING 3) — the detector gap.**
`platform/scripts/governance/secret_scan.sh` is allowlist-scoped to 8 `SCAN_TARGETS` while its
docstring claims *"Scan the repository tree, suppress known-noise paths"*. Confirmed empirically:

```
$ bash platform/scripts/governance/secret_scan.sh
secret_scan: gitleaks not found — using bash regex set
secret_scan: PASS (no literal credentials in scanned paths)
EXIT=0
```

**The scanner returns PASS while two live effective-DB-administrator credentials sit on
`origin/main` in eighteen files.** This is §N.8's canonical failure: green because it stopped
looking.

Four gaps, not one:

- **(a) Scope.** 14 of the 16 INC-2 files and 1 of the 2 INC-3 files are outside all 8 targets
  (`platform/python-sidecar/`, `platform/src/`, `docs/`, `00_ARCHITECTURE/`). RULING 3 covers this.
- **(b) Pattern shape — not in RULING 3, surfaced here.** Even *inside* a scanned target the scanner
  misses the dominant leak shape. `platform/scripts/` **is** a `SCAN_TARGET`, yet
  `platform/scripts/governance/v13_production_gate.py:13` was not caught, because the pattern set
  requires `(PGPASSWORD|DB_PASSWORD|DATABASE_PASSWORD)=<value>` and the code reads
  `os.environ.get("DB_PASSWORD", "<literal>")` — no `=`. **Widening scope alone would still miss
  it.** Add a pattern for the env-default idiom in both languages:
  `os.environ.get\(\s*["'][A-Z_]*(PASSWORD|SECRET|TOKEN|KEY|URL)["']\s*,\s*["'][^"']{8,}` and the
  JS/TS equivalents `process.env.X ?? "…"` / `process.env.X || "…"`.
- **(c) Fixtures.** RULING 3 mandates `fail/` fixtures reproducing the leaked shape. Include
  **both**: the bare DSN literal *and* the `env.get(name, default)` idiom.
- **(d) Test files must not be exempt.** The single most operationally dangerous instance —
  `test_ka_jivana_parva_circularity_guard.py:64` — is a test file executed nightly against
  production (§2.3.1). Any suppression rule excluding `tests/` would have missed it.

**6.2 — `B-SECRET-REDACT` (sibling lane, DVA RULING 2) — the copy-paste seed.**
RULING 2 scoped it to the 9 INC-1 files. On this lane's evidence it must also cover the 16 INC-2
files and the 2 INC-3 files — **27 files total, 44 occurrences**. The INC-1 files are inert (dead
credential); the other 18 hold live effective-DB-administrator credentials and are the urgent half.

Redaction of the INC-2/INC-3 files must **fail fast, not fall back**:

```python
# correct — no default; missing env is a loud error
DB_URL = os.environ["DATABASE_URL"]
```

The `os.environ.get(NAME, "<literal>")` idiom must not be preserved with a *new* literal. That is
exactly how INC-2 was born.

**One file needs coordination, not just redaction:**
`platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py:64` is ṢAḌ-DARŚANA
surface and is executed by a nightly CI gate the campaign calls "untouchable" (§2.3.1). Redacting it
without supplying `DATABASE_URL` from the workflow breaks that gate.

**Git history cannot be purged** (RULING 2 withholds history-rewrite authority; a rewrite would not
recall replicated bytes). INC-1 appears from `39b91dd0` onward, INC-2 in 20 commits, INC-3 in 12.
**They are public permanently. Rotation is the whole remediation; redaction is the recurrence
control.**

**6.3 — Structural controls (neither sibling lane covers these).**

| Control | Rationale |
|---|---|
| Make `secret_scan.sh` a **blocking** CI gate on `main` (RULING 3 names this). | Today nothing stops the next literal from landing. |
| Enable GitHub **push protection / secret scanning** on `amonty84/Madhav`. | Free for public repos; catches at push time, before the bytes are public. Defence that does not depend on this repo's own tooling. |
| Ban the `env.get(NAME, "<literal>")` idiom in a lint rule, not just a scanner. | The scanner catches secrets; the lint catches the *shape* that produces them. |
| **Right-size the application role** — no `CREATEDB`/`CREATEROLE` (§5.3 note). | This is what turns a leaked app password into an effective-DB-administrator credential with a persistence primitive (§1.5). The single highest-leverage severity reduction available. |
| **Prune the reachability denominator** (§1.7): drop `roles/cloudsql.client` from `amjis-mcp-runtime` and `marsys-pipeline-writer`; review `roles/editor` on the three default SAs. | Shrinks the set of identities that can turn a leaked credential into a live session. |
| Set `requireSsl=true` (R2) and consider `connectorEnforcement=REQUIRED` (R4). | Turns `authorizedNetworks` from a single control into one of three. |
| Set `deletionProtectionEnabled=true` (R5) and enable PITR (R6). | Recovery floor is 7 daily backups with no point-in-time granularity — and PITR is what would make a future tampering question answerable (§3.6 item 5). |
| Put the `postgres` password in Secret Manager (step 5.11). | Unmanaged today — no version history, no rotation path, no audit. |
| Set `rolvaliduntil` on login roles, or adopt a dated rotation cadence recorded in `CURRENT_STATE`. | No credential on this instance expires (R7); both prior rotations were incident-driven. |
| Enable **pgAudit** or Cloud SQL `log_connections`. | §3.6 item 2: there is currently no record of which DB role any session used. This is the gap that made the compromise assessment indirect. |

---

## §7 — Residuals

| # | Residual | Owner |
|---|---|---|
| RES-1 | **INC-2 and INC-3 exist at all**, and both are effective-DB-administrator credentials. RULING 1's scope was materially incomplete; RULING 18 corrected the severity. | DVA (addressed) |
| RES-2 | **B-SECRET-REDACT's scope (9 files) is too narrow**: should be 27 files / 44 occurrences. The 9 it covers hold the DEAD credential; the 18 it does not hold the LIVE ones. | DVA → B-SECRET-REDACT |
| RES-3 | **B-SECRETSCAN-SCOPE's scope is too narrow**: the pattern-shape gap (§6.1b) survives fixing scope, and any `tests/` exemption would miss the worst instance (§6.1d). | DVA → B-SECRETSCAN-SCOPE |
| RES-4 | `fresh_chart_smoke.yml` declares production access as `postgres` (§2.3.2). It has never reached the DB — its only run failed at WIF auth. **Must be repointed to `retrieval_census_ro` before the WIF failure is repaired.** | B-lane / native |
| RES-5 | `shad-darshana-circularity-guard.yml` runs nightly as `amjis_app` from a hard-coded live literal (§2.3.1). **ṢAḌ-DARŚANA-owned** — reported, not touched. Breaks at step 5.11 unless coordinated. | Report to ṢAḌ-DARŚANA |
| RES-6 | GH Actions secret `PROD_DATABASE_URL` (updated 2026-06-22) has unknown contents and unknown role. Unknowable read-only. | Native (step 5.7) |
| RES-7 | `amjis-db-password` v2 and `amjis-pipeline-db-url` v2 remain `enabled` while carrying a dead credential — misleading; an enabled version reads as valid. | Step 5.10 |
| RES-8 | **`authorizedNetworks` change history is not established** (§3.6 item 4) — the single most consequential gap in the compromise assessment, and the one with a deadline (§3.6 item 6). Answerable with: `gcloud logging read 'logName:"cloudaudit.googleapis.com%2Factivity" AND protoPayload.methodName="cloudsql.instances.update"' --freshness=400d --format="json(timestamp,protoPayload.request)"`, inspecting each of the seven request bodies for `ipConfiguration.authorizedNetworks`. **This lane did not run it.** | Native / follow-on lane |
| RES-9 | `amjis_app` holds `CREATEDB`/`CREATEROLE`/`cloudsqlsuperuser` — the properties that make this an effective-DB-administrator incident. §5.3 offers the narrowing but does not apply it, to avoid coupling two risks. | Follow-on |
| RES-10 | `WATCHDOG_SECRET` is a plaintext env var on `amjis-web` despite a `watchdog-secret` Secret Manager entry existing. Not repo-exposed (verified) — same class of defect. | Follow-on |
| RES-11 | 13 numerically-pinned secrets in `deploy.yml` (§5.8) each carry the same silent-revert trap. No CI check detects a pin that is not the highest enabled version. | Follow-on |
| RES-12 | **~10 identities can reach the instance** (§1.7), two of them dormant with live grants. Not exploitable alone, but it is the denominator that makes the leaked credentials usable. | Follow-on |
| RES-13 | No DB-level authentication logging (pgAudit / `log_connections`). §3's assessment had to proceed indirectly through GCP principals because of this. | Follow-on |

---

## §8 — Evidence appendix (read-only commands actually run)

Every command below was executed by this lane. **No mutating command was run.** Credential values
were compared by shell equality and by SHA-256 and were never printed into any artifact.

**Probe A — is `amjis-db-password:3` the live `amjis_app` password?**
```
$ cloud-sql-proxy --address 127.0.0.1 --port 5434 madhav-astrology:asia-south1:amjis-postgres &
  [madhav-astrology:asia-south1:amjis-postgres] Listening on 127.0.0.1:5434
$ PGPASSWORD=$(gcloud secrets versions access 3 --secret=amjis-db-password) \
    psql -h 127.0.0.1 -p 5434 -U amjis_app -d amjis -w \
    -tAc "select 'AUTH_OK as '||current_user||' @ '||current_database();"
AUTH_OK as amjis_app @ amjis
```

**Probe B — is INC-1 still live?** (value read from `hard_gates_check.sh:46` into a shell var, never echoed)
```
amjis_app           : rejected — FATAL: password authentication failed for user "amjis_app"
postgres            : rejected
retrieval_census_ro : rejected
```

**Probe C — what does INC-3 authenticate as?**
```
amjis_app           : rejected
postgres            : *** AUTHENTICATES — LIVE ***
retrieval_census_ro : rejected
```

**Probe D — role attributes, memberships, ownership (RULING 18 severity basis).**
```
       rolname       | rolsuper | rolcreatedb | rolcreaterole | rolcanlogin | rolconnlimit | rolvaliduntil
---------------------+----------+-------------+---------------+-------------+--------------+---------------
 postgres            | f        | t           | t             | t           |           -1 | (null)
 amjis_app           | f        | t           | t             | t           |           -1 | (null)
 retrieval_census_ro | f        | f           | f             | t           |            5 | (null)

  member   |   granted_role
-----------+-------------------
 amjis_app | cloudsqlsuperuser
 postgres  | cloudsqlsuperuser
   (full graph: 13 edges, all others between Cloud SQL / pg_* built-ins; all admin_option = f)

 nspname |   owner   |  nspacl
---------+-----------+---------------------------------------------------------
 auth    | amjis_app |
 public  | amjis_app | {amjis_app=UC/amjis_app,postgres=UC/amjis_app,
                       retrieval_census_ro=U/amjis_app}

owned_by_amjis_app | total_public_tables
              291  |                 291

databaseInstalledVersion: POSTGRES_15_17     (PG15 CREATEROLE semantics — §1.5)
```

**Probe E — Cloud Run credential bindings.**
```
amjis-web     : DB_PASSWORD ← secretKeyRef{name: amjis-db-password, key: '3'}
                DB_USER=amjis_app  DB_NAME=amjis
                INSTANCE_CONNECTION_NAME=madhav-astrology:asia-south1:amjis-postgres
amjis-sidecar : DATABASE_URL ← secretKeyRef{name: amjis-pipeline-db-url, key: latest}
                annotation run.googleapis.com/cloudsql-instances=…:amjis-postgres
amjis-mcp     : (no DB credential of any kind)
jobs          : brahma-build-pipeline-job → DATABASE_URL ← amjis-pipeline-db-url:latest
                brahma-foundation-bootstrap → no DB env
```

**Probe F — GitHub Actions secrets (names only; values are write-only).**
```
$ gh secret list
FIREBASE_ADMIN_CREDENTIALS  NEXT_PUBLIC_FIREBASE_* (6)  NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
PROD_DATABASE_URL (2026-06-22)  SMOKE_CHART_ID  SMOKE_SESSION_COOKIE
```
`DATABASE_URL` and `TAP_DATABASE_URL` are **absent** ⇒ `samiksha-daily.yml` and `tap-ci.yml` are
no-ops today.

**Probe G — Secret Manager version fingerprints (payloads compared by equality, never printed).**
```
amjis-db-password       v1 disabled 2026-04-25 | v2 enabled 2026-05-28 [= INC-1] | v3 enabled 2026-06-02 [= INC-2]
amjis-pipeline-db-url   v1 enabled  2026-04-28 | v2 enabled 2026-05-30 [= INC-1] | v3 enabled 2026-06-06 [= INC-2]
retrieval-census-ro-db-password  v1 enabled 2026-07-19  [not exposed]
amjis-pipeline-db-url v3 embeds the SAME credential as amjis-db-password v3.
```

**Probe H — live service health at the time of writing (rotation baseline).**
```
amjis-web     /api/health  → 200 {"status":"ok"}
amjis-mcp     /health      → 200 {"status":"ok","service":"marsys-mcp","tools":88}
amjis-sidecar /health      → 200
revisions     amjis-web-01281-p25 · amjis-mcp-00517-b5q · amjis-sidecar-00933-f9j
```

**Probe I — exposure counts on `origin/main`** (`git grep -l --fixed-strings "$VAL" origin/main | wc -l`).
```
INC-1 :  9 files · 19 occurrences · 1st commit 39b91dd0 (2026-05-29)
INC-2 : 16 files · 23 occurrences · 1st commit 0c2d4d98 (2026-06-05) · 20 commits in history
INC-3 :  2 files ·  2 occurrences · 1st commit 599cfce1 (2026-04-29) · 12 commits in history
```

**Probe J — the current scanner's verdict** (§6.1).
```
$ bash platform/scripts/governance/secret_scan.sh
secret_scan: PASS (no literal credentials in scanned paths)   EXIT=0
```

**Probe K — the two production-proxying workflows (RULING 21).**
```
$ grep -n "LIVE_DSN" platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py
64:LIVE_DSN = "postgresql://amjis_app:<INC-2 REDACTED>@127.0.0.1:5433/amjis"
$ gh run list --workflow=shad-darshana-circularity-guard.yml --limit=8
  (no runs)
$ grep -n "PROD_DATABASE_URL" .github/workflows/fresh_chart_smoke.yml
147:          PROD_DATABASE_URL: postgresql://postgres@127.0.0.1:5433/amjis
$ gh run list --workflow=fresh_chart_smoke.yml --limit=8
2026-07-29T05:40:36Z  completed/failure  id=30425772357
$ gh run view 30425772357 --json jobs
  "Authenticate to Google Cloud"                → failure
  "Start Cloud SQL Auth Proxy …"                → skipped
  "Snapshot production schema + reference data" → skipped
```

**Probe L — `deploy.yml` version pins (RULING 18(c)).**
```
$ grep -cE "^[[:space:]]+[A-Z_]+=[a-zA-Z0-9_-]+:[0-9]+[[:space:]]*$" .github/workflows/deploy.yml
13
$ grep -cE "^[[:space:]]+[A-Z_]+=[a-zA-Z0-9_-]+:latest[[:space:]]*$" .github/workflows/deploy.yml
3
  (13 numeric pins at lines 303-310, 312, 390, 391, 468, 469 — §5.8 table)
```

**Probe CA-1 — full role enumeration (persistence sweep).** 30 rows: 27 built-ins + `amjis_app`,
`postgres`, `retrieval_census_ro`. No unexpected role. Grant graph: 13 edges, no anomaly.

**Probe CA-5 — connecting principals, positive aggregation.**
```
$ gcloud logging read '…methodName="cloudsql.instances.connect"' --freshness=30d \
    --format="value(protoPayload.authenticationInfo.principalEmail)" | sort | uniq -c
1796 amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com
 712 mail.abhisek.mohanty@gmail.com
 528 github-actions@madhav-astrology.iam.gserviceaccount.com
  89 amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com
```

**Probes CA-10 / CA-11 / CA-16b — negative (exhaustiveness) queries.**
```
CA-10  exclude the 4 current principals, freshness=30d   → ZERO rows
CA-11  exclude the 4 current principals, freshness=400d  → surfaces exactly two more:
         marsys-pipeline-writer@…        2026-05-30 → 2026-06-01  (Google IPv6 2600:1900::/…)
         938361928218-compute@developer… 2026-04-25 → 2026-05-28  (34.96.40.27)
CA-16b exclude ALL SIX, window 2026-04-25 → 2026-07-01   → ZERO rows
       ⇒ no seventh identity has ever connected to this instance
```

**Probes CA-13/CA-14 — audit retention floor.**
```
$ gcloud logging read '…resource.type="cloudsql_database" AND timestamp<"2026-04-26T00:00:00Z"' \
    --limit=5 --freshness=400d
2026-04-25T23:26:57Z  cloudsql.instances.connect  mail.abhisek.mohanty@gmail.com
2026-04-25T23:06:54Z  cloudsql.instances.connect  938361928218-compute@developer.gserviceaccount.com
2026-04-25T23:03:47Z  cloudsql.instances.connect  938361928218-compute@developer.gserviceaccount.com
  ⇒ coverage begins on the instance's creation day (2026-04-25T11:59:51Z),
    i.e. 100% of the exposure window of all three credentials.
```

**Probes CA-3/CA-9 — administrative plane.** `gcloud sql operations list --limit=400` returns 123
operations back to 2026-04-25; the 17 non-backup events are listed in §3.3. The corresponding
non-connect audit-log view agrees and adds the 2026-05-28 clone/failover/delete sequence. **Every
non-automated operation is attributed to `mail.abhisek.mohanty@gmail.com`. No third-party principal
appears on the admin plane at any point in the instance's life.**

**Probe CA-18 — reachability denominator (§1.7).** 8 service accounts hold `roles/cloudsql.client`;
3 principals hold `roles/editor`; all 15 project service accounts are `disabled: False`.

**Cleanup.** The local Cloud SQL Auth Proxy started for the probes was stopped
(`pkill -f "cloud-sql-proxy --address 127.0.0.1 --port 5434"` → `proxy stopped`). A local process
only; no infrastructure was modified.

---

## §9 — EXECUTION RECORD

*(empty — the runbook has not been executed)*

| field | value |
|---|---|
| Executed on | — |
| Executed by | — |
| §5.1 pre-rotation role baseline (30 roles / 13 grants?) | — |
| New role name | — |
| New `amjis-db-password` version | — |
| New `amjis-pipeline-db-url` version | — |
| `amjis-web` revision before → after | — |
| `amjis-sidecar` revision before → after | — |
| `deploy.yml` pin bumped + deploy proven green | — |
| §5.8 13-pin audit result | — |
| `shad-darshana-circularity-guard.yml` migrated | — |
| `fresh_chart_smoke.yml` repointed to `retrieval_census_ro` | — |
| §5.12 can-fail proof output | — |
| §5.12 post-rotation role diff (expect +1 role, +2 grants) | — |
| §5.13 72h straggler check | — |
| `postgres` (INC-3) rotated + stored in Secret Manager | — |
| RES-8 `authorizedNetworks` history question answered | — |
| Incident status | **UNRESOLVED** (as of the runbook's own writing — see §9-NATIVE-DISPOSITION below) |

---

## §9-NATIVE-DISPOSITION — the actual, authoritative outcome (2026-07-31, NIḤŚEṢA campaign)

The native reviewed the credentials INC-1/INC-2/INC-3 catalogued above and made the following
disposition, relayed as an explicit, binding instruction to the NIḤŚEṢA campaign:

- **Classification: SECURE / accepted risk.** No rotation is to be performed.
- **Priority: not P0.** Not to be re-raised as a P0 in any future session.
- **§5 (the zero-downtime rotation runbook) is NOT to be executed.** It remains in this document
  as a prepared, reviewed procedure available if the native's risk assessment changes in the
  future — not as an outstanding action item.
- **Separately, PR #905** (redaction of plaintext DB credentials from 27 tracked files — the
  B-SECRET-REDACT lane referenced in this document's frontmatter) **was merged** during NIḤŚEṢA,
  as ordinary hygiene. That is independent of, and does not imply anything about, the rotation
  question above: redacting a plaintext literal from tracked files is good hygiene regardless of
  whether the credential itself is rotated.
- **This document's technical content (§0–§8) is not disputed** — the consumer inventory, the
  `cloudsqlsuperuser`/`rolcreaterole` self-escalation analysis, and the compromise assessment are
  retained as accurate, useful audit-trail material. Only the *priority/action* conclusion is
  superseded, by the native's explicit accepted-risk classification.

No `gcloud`/`psql`/IAM/Secret Manager mutation was performed by this disposition — it is a
documentation-only closure, consistent with the SAMĀPTI swarm never having held
credential-administration authority (DVA Ruling 1).

| field | value |
|---|---|
| Disposition date | 2026-07-31 |
| Disposed by | Native (relayed via NIḤŚEṢA campaign brief) |
| Rotation executed | **No — explicitly declined, not required** |
| Incident status | **CLOSED — SECURE / accepted risk** |

---

*End of SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL v1.1 — B-SECRET-ROTATE-PREP, 2026-07-30.
Preparation only. Not a closure. No credential was rotated, created, disabled, or written by this
lane; no IAM, Secret Manager, Cloud SQL, or Cloud Run resource was modified. The compromise
assessment in §3 establishes, at most, no evidence of misuse in the window we can see — never that
the credentials were not misused.*
