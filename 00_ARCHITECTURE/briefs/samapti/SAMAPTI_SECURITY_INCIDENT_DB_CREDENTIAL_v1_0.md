---
artifact: SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL
canonical_id: SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL
version: 1.0
status: UNRESOLVED-PENDING-NATIVE-EXECUTION
created: 2026-07-30
lane: B-SECRET-ROTATE-PREP
governed_by: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md RULING 1
related_lanes: B-SECRET-REDACT (RULING 2), B-SECRETSCAN-SCOPE (RULING 3)
---

# ⚠️ UNRESOLVED — PRODUCTION DATABASE CREDENTIAL EXPOSURE

> **THIS DOCUMENT IS PREPARATION ONLY. IT IS NOT A CLOSURE.**
>
> **The incident described below is UNRESOLVED.** Nothing has been rotated. No role has been
> created, altered, or disabled. No Secret Manager version has been written. No IAM binding has
> been changed. The SAMĀPTI swarm has no credential-administration authority (DVA RULING 1) and
> did not exercise any.
>
> **The incident becomes resolved only when the native — a human with credential-admin authority —
> executes §4 of this document and records the outcome here.**
>
> **Two of the three exposed credentials are LIVE RIGHT NOW and one of them is a `cloudsqlsuperuser`
> member.** The scope is materially larger than DVA RULING 1 assessed. See §1 before doing anything
> else.
>
> **Priority: P0. Escalated from DVA RULING 1's assessment.**

---

## §0 — What this lane found that RULING 1 did not

DVA RULING 1 was issued on the A7-N8-AUDIT finding of **one** credential literal in 9 tracked files.
This lane independently re-derived that finding and, in the course of building the consumer
inventory, discovered **two further credential literals** on `origin/main` that the audit did not
surface.

| id | Role it authenticates as | Live today? | Tracked files on `origin/main` | First public commit | Days public (as of 2026-07-30) |
|---|---|---|---|---|---|
| **INC-1** | `amjis_app` | **NO — superseded** | 9 (19 occurrences) | `39b91dd0` · 2026-05-29 | 62 |
| **INC-2** | `amjis_app` | **YES — LIVE** | 16 (23 occurrences) | `0c2d4d98` · 2026-06-05 | 55 |
| **INC-3** | `postgres` (member of `cloudsqlsuperuser`) | **YES — LIVE** | 2 (2 occurrences) | `599cfce1` · 2026-04-29 | **92** |

Two corrections to RULING 1's premises, both independently verified (§7 evidence):

1. **RULING 1's subject credential (INC-1) is already dead.** It was superseded on 2026-06-02 when
   `amjis-db-password` version 3 was created. A direct authentication probe against the live
   instance returns `FATAL: password authentication failed for user "amjis_app"`. Its
   live-and-public window was ~2026-05-29 → 2026-06-02 (≈4 days), not 2 months. Its remaining
   value is as a recurrence signal, not as an active exposure.
2. **The credential that replaced it (INC-2) was itself committed in plaintext three days later**
   and is the credential `amjis-web` is serving with at this moment. The 2026-06-02 rotation
   therefore did not remediate the pattern — it reproduced it. Any rotation performed without §4's
   redaction/consumer discipline will reproduce it a third time.

**INC-3 is the most severe of the three** and was in no prior finding: a live `postgres`
superuser-tier password, public for three months, held in **no Secret Manager secret at all** —
it exists only in the repository and wherever the native keeps it.

Credentials are referenced throughout this document by id and by SHA-256 fingerprint only. **No
credential value appears anywhere in this document, in this lane's commits, or in its summary.**

| id | SHA-256 (first 16 hex) — for mechanical identification |
|---|---|
| INC-1 | `bd14b4e7cbc6c972` |
| INC-2 | `9916bb655a303c81` |
| INC-3 | `f0abfd07498574f6` |

Verify a candidate string against these with:
`printf '%s' "<candidate>" | shasum -a 256 | cut -c1-16`

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

**Secret Manager correspondence:** `amjis-db-password` **version 2** (created 2026-05-28, still
`enabled`) and `amjis-pipeline-db-url` **version 2** (created 2026-05-30, still `enabled`) both
carry INC-1. Both versions remain `enabled` in Secret Manager even though the underlying database
password no longer matches — dead weight that should be disabled during §4 (step 4.9).

**Current status:** DEAD against every role on the instance (`amjis_app`, `postgres`,
`retrieval_census_ro` all reject it — §7 probe B).

### 1.3 — INC-2 · `amjis_app`, LIVE

**Introduced:** commit `0c2d4d98`, 2026-06-05, author Abhisek —
*"feat(v13-prod): v13_production_gate.py — final cross-stream prod gate script"*.
Appears in **20 commits** across history.

**This is the credential production is using right now**: `amjis-web` binds
`DB_PASSWORD ← amjis-db-password:3`, and version 3's payload authenticates as `amjis_app`
(§7 probe A). `amjis-pipeline-db-url:3` embeds the **same** credential and is consumed by
`amjis-sidecar` and `brahma-build-pipeline-job`.

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
| `platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py` | 64 |
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
hard-coded local-proxy fallback for dev)"*. **The convention itself is the defect.** A "local
dev fallback" holding a live production credential is a production credential, not a dev default.
Two files hold it with no env override at all (`l0_embed_runner.py:23`,
`tests/test_gochara_intensity.py:37` — bare literal assignment).

### 1.4 — INC-3 · `postgres` (`cloudsqlsuperuser`), LIVE, 92 days public

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
   authenticates as **`postgres`** (§7 probe C). Anyone reading the file sees an app credential;
   the credential is in fact the instance's administrative account. This mislabelling is very
   likely why 92 days of audits, including A7-N8-AUDIT, walked past it.
2. `postgres` is a member of `cloudsqlsuperuser` with `CREATEDB` and `CREATEROLE`
   (§7 probe D). `cloudsqlsuperuser` owns both the `amjis` and `postgres` databases. This is
   full administrative control of the instance short of the managed-service boundary.
3. It is held in **no Secret Manager secret** — `gcloud secrets list` has no entry for it. It is
   unmanaged, unversioned, and unrotatable-by-config. Rotating it requires
   `gcloud sql users set-password postgres` and then hunting every consumer by hand.
4. 92 days of public exposure is the longest of the three, and it predates the entire
   build-orchestrator episode RULING 1 examined.

### 1.5 — Current risk posture (independently confirmed)

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

RULING 1's two findings are **CONFIRMED**, and three more are added:

| # | Finding | Confirmed value | Assessment |
|---|---|---|---|
| R1 | `authorizedNetworks` | **absent / empty** | The single control preventing direct internet exploitation of INC-2 and INC-3. It is load-bearing and it is the *only* thing that is. |
| R2 | `requireSsl` | **false** (`sslMode: ALLOW_UNENCRYPTED_AND_ENCRYPTED`) | Public-IP instance accepting unencrypted connections. Defence-in-depth failure. |
| R3 | `ipv4Enabled` | **true**, PRIMARY `34.93.202.112` | Instance has a routable public address. Reachability is gated only by R1. |
| R4 | `connectorEnforcement` | **NOT_REQUIRED** | Auth Proxy / connector use is conventional, not enforced. If R1 is ever relaxed, R1+R2+R4 compose into direct exploitability. |
| R5 | `deletionProtectionEnabled` | **false** | An actor with INC-3 (`postgres`) has DB-level destructive capability; instance-level deletion additionally needs GCP IAM, which the leak does not grant. |
| R6 | `pointInTimeRecoveryEnabled` | **false**; 7 retained backups, `transactionLogRetentionDays: 7` | Recovery granularity is 7 daily backups. Silent tampering older than 7 days would be unrecoverable and, absent PITR, hard to date. |

**Net posture.** Not presently internet-exploitable — an attacker holding INC-2 or INC-3 still needs
either a GCP identity with Cloud SQL Client permission (to use the Auth Proxy) or an entry in
`authorizedNetworks` (there are none). RULING 1's "defence-in-depth failure, not a 2am emergency"
characterisation therefore **still holds** for the *network* dimension.

It does **not** hold for the *scope* dimension. RULING 1 assessed a dead app credential; the true
state is a live app credential plus a live superuser credential, both public, the superuser one for
three months. **A single misconfiguration — one `authorizedNetworks` entry added for convenience,
one `--assign-ip` on a dev box, one service account over-granted — converts this from
defence-in-depth to direct compromise of the entire corpus with no further attacker effort.**

**Not established by this lane** (stated as unperformed, per §8's discipline — never as passed):

- Whether INC-2 or INC-3 has ever been used by an unauthorised party. Determining this requires
  Cloud SQL auth-log review over the full exposure window (2026-04-29 → present), which exceeds
  this lane's scope. **Recommended as a follow-on for the native**; commands in §6.
- Whether GitHub Actions secret `PROD_DATABASE_URL` (last updated 2026-06-22) carries INC-2, INC-3,
  or a fourth credential. GitHub Actions secrets are write-only via the API; this is unknowable
  read-only and must be checked by the native (§4, step 4.6).

---

## §2 — Consumer inventory

Every system that authenticates to `amjis-postgres`. Each row was verified by direct read-only
inspection of the live resource or the file, not inferred from documentation.

### 2.1 — Production runtime (Cloud Run services)

| Consumer | Role | How it obtains the credential | Credential | Migration action |
|---|---|---|---|---|
| **`amjis-web`** (rev `amjis-web-01281-p25`) | `amjis_app` | `DB_PASSWORD` ← `secretKeyRef amjis-db-password` key **`3`** (version-pinned). `DB_USER=amjis_app`, `DB_NAME=amjis`, `INSTANCE_CONNECTION_NAME` as plain env. Consumed at `platform/src/lib/db/client.ts:63` (`password: process.env.DB_PASSWORD!`). | INC-2 | **Required.** Repoint to the new secret version. Version-pinned ⇒ will **not** pick up a new version automatically. |
| **`amjis-sidecar`** (rev `amjis-sidecar-00933-f9j`) | `amjis_app` | `DATABASE_URL` ← `secretKeyRef amjis-pipeline-db-url` key **`latest`**. Cloud SQL attached via `run.googleapis.com/cloudsql-instances` annotation (unix socket). | INC-2 (embedded in the DSN) | **Required.** Bound to `latest` ⇒ picks up a new version on next revision start, but **only** on restart — a new revision must be forced. |
| **`amjis-mcp`** (rev `amjis-mcp-00517-b5q`) | — | **No database credential of any kind.** Its full env is `MCP_INTERNAL_TOKEN`, `PYTHON_SIDECAR_API_KEY`, `MCP_CANARY_KEY`, `PLATFORM_URL`, `PYTHON_SIDECAR_URL`, `MCP_BASE_URL`. All data access is proxied through `amjis-web` / `amjis-sidecar`. | n/a | **None.** Verify health only (regression canary — it will break if `amjis-web` breaks). |

> RULING 1's directive named `amjis-mcp` as a probable consumer. **It is not one.** Confirmed by
> full `gcloud run services describe` env dump (§7 probe E). This is good news for the runbook:
> the migration surface is two services, not three.

### 2.2 — Production batch (Cloud Run jobs)

| Consumer | Role | How it obtains the credential | Credential | Migration action |
|---|---|---|---|---|
| **`brahma-build-pipeline-job`** | `amjis_app` | `DATABASE_URL` ← `secretKeyRef amjis-pipeline-db-url` key **`latest`**; Cloud SQL socket annotation; SA `amjis-web-runtime@`. This is the orchestrator job that runs chart builds. | INC-2 | **Required (passive).** Reads `latest` at each execution — no redeploy needed, but must not be mid-execution during the cutover. |
| **`brahma-foundation-bootstrap`** | — | No DB env (`BRAHMA_PLACEHOLDER=true`); no Cloud SQL annotation; SA `amjis-builder-runtime@`. | n/a | **None.** |

### 2.3 — CI / GitHub Actions

| Workflow | How it obtains the credential | Status | Migration action |
|---|---|---|---|
| `.github/workflows/deploy.yml` | **(a)** Migrations step (L203): `DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}` against a Cloud SQL Auth Proxy on `127.0.0.1:5432`. Hard-fails if unset. **(b)** Deploy step (L304): `secrets:` block declares `DB_PASSWORD=amjis-db-password:3` — **the version pin lives in the workflow file**. | GH secret `PROD_DATABASE_URL` exists, updated 2026-06-22. Its role/credential is **not readable** (GH secrets are write-only). | **Required, two edits.** (a) Rewrite the GH secret. (b) Bump `amjis-db-password:3` → the new version in `deploy.yml`, else the next deploy silently reverts `amjis-web` to the old credential. **This is the single highest-risk step in the runbook.** |
| `.github/workflows/samiksha-daily.yml` | `DATABASE_URL: ${{ secrets.DATABASE_URL }}` (L63); the step no-ops with exit 0 when unset (L67-69). | GH secret `DATABASE_URL` is **not configured** (`gh secret list` — §7 probe F). The daily sweep is a no-op today. | **None now.** Record that if it is ever wired, it must use the new role. |
| `.github/workflows/tap-ci.yml` | `DATABASE_URL: ${{ secrets.TAP_DATABASE_URL }}` (L106/112/118); passes when unset by design. | GH secret `TAP_DATABASE_URL` is **not configured**. | **None now.** Same rider. |
| `.github/workflows/fresh_chart_smoke.yml` | Starts a proxy on `127.0.0.1:5433`; uses `PROD_DATABASE_URL: postgresql://postgres@127.0.0.1:5433/amjis` (L147) — **role `postgres`, no password in the URL**; ephemeral local PG uses `postgres:postgres` (L183-184, harmless). | Reads production via the **`postgres`** role. Passwordless in the URL — either relies on an environment `PGPASSWORD`, or this step is currently failing/skipped. **Not established by this lane.** | **Investigate then act.** If it authenticates as `postgres`, it is an INC-3 consumer and must move to a read-only role, not to `postgres`. |
| `.github/workflows/shad-darshana-circularity-guard.yml` | Starts a proxy on `127.0.0.1:5433` (L66-68). No credential literal or DB secret reference found. | Not established. | **Investigate.** Owned by ṢAḌ-DARŚANA (§7 not-owned) — report, do not modify. |

### 2.4 — Local developer / operator surface

| Consumer | How it obtains the credential | Credential | Migration action |
|---|---|---|---|
| `/Users/Dev/.claude.json` → `mcpServers.postgres.args[2]` | Plaintext DSN `postgresql://amjis_app:<literal>@127.0.0.1:5433/amjis` in the developer's Claude config (outside the repo). | **INC-2** | **Required.** Update after rotation or the local Postgres MCP breaks. Not a repo file — will be missed by any repo-scoped scanner, including the fixed one. |
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/{hard_gates_check,preflight,apply_migration}.sh` | Hard-coded literal (§1.2). Retired scaffold; assume unused. | INC-1 (dead) | Redaction only — B-SECRET-REDACT (RULING 2). Already non-functional. |
| `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/operator_runs/2026-05-30/.psql_url` | Hard-coded DSN, one line. | INC-1 (dead) | Redaction only — B-SECRET-REDACT. |
| `platform/migrations/__tests__/test_mig_12{4,5,6,7}.py` | Hard-coded literal in test setup. | INC-1 (dead) | Redaction only. These tests cannot currently connect. |
| `platform/python-sidecar/**` (13 files, §1.3) | `os.environ.get(..., "<live literal>")` fallback, or bare literal. | **INC-2** | **Required.** Env indirection per RULING 2 **and** the literal must not be replaced with the *new* credential — replace with a fail-fast env read. |
| `platform/scripts/governance/v13_production_gate.py:13` | `os.environ.get("DB_PASSWORD", "<live literal>")`. | **INC-2** | **Required.** Same treatment. |
| `platform/src/lib/db/seed/observatory_pricing/run_seed.ts:74` | Hard-coded DSN. | **INC-3** (`postgres`) | **Required.** A seed script should never run as `postgres`. |
| `00_ARCHITECTURE/MIGRATION_APPLY_INSTRUCTIONS_v1_0.md:71` | Documented copy-paste DSN. | **INC-3** | **Required.** This is the copy-paste seed that propagated the pattern. |
| `docs/superpowers/plans/2026-06-1{7,21}-*.md` | Transcribed command output inside plan documents (9 occurrences). | **INC-2** | **Required.** Historical plan docs — redact in place; they are not executable. |

### 2.5 — Roles present on the instance

| Role | Attributes | Objects | Credential status |
|---|---|---|---|
| `amjis_app` | `LOGIN`, `CREATEDB`, `CREATEROLE`, member of `cloudsqlsuperuser`, no conn limit, no expiry | Owns schemas `public` and `auth`; **owns all 291 tables in `public`** | **INC-2 — LIVE, public** |
| `postgres` | `LOGIN`, `CREATEDB`, `CREATEROLE`, member of `cloudsqlsuperuser` | — | **INC-3 — LIVE, public** |
| `retrieval_census_ro` | `LOGIN`, conn limit **5**, no CREATE rights; `USAGE` on `public`; default ACL grants `SELECT` on future `amjis_app` tables | none | Secret `retrieval-census-ro-db-password` v1 (2026-07-19). **Not exposed** — verified absent from the working tree. Untouched by this runbook. |

**The ownership fact that shapes the runbook:** `amjis_app` owns every object. Dropping it, or
reassigning ownership, would be a large and risky operation. `ALTER ROLE ... NOLOGIN` disables
authentication while leaving ownership and group semantics intact — which is why §4 disables rather
than deletes, and why the new role is granted **membership in** `amjis_app` rather than a
reconstructed grant set.

---

## §3 — Pre-execution checklist (native)

Do these before step 4.1. Each is cheap and each prevents a specific failure seen in §2.

- [ ] **3.1** Confirm no build is in flight: no `brahma-build-pipeline-job` execution running, and
      SAMĀPTI's BUILD-LOCK is free. A mid-rebuild cutover risks a half-written asset.
- [ ] **3.2** Confirm no deploy is in flight and no PR is auto-merging. A `deploy.yml` run landing
      between steps 4.5 and 4.6 will re-pin `amjis-web` to the old secret version.
- [ ] **3.3** Take a fresh on-demand backup: `gcloud sql backups create --instance=amjis-postgres`.
      PITR is off (R6); this is the only rollback floor.
- [ ] **3.4** Record the current serving revisions so a rollback target exists:
      `gcloud run services describe amjis-web --region=asia-south1 --format='value(status.traffic)'`
      (and the same for `amjis-sidecar`).
- [ ] **3.5** Decide the new role name. This document uses **`amjis_app_v2`**. Choose once; it
      appears in every subsequent step.
- [ ] **3.6** Generate the new password with a CSPRNG, never by hand, never in shell history:
      `python3 -c "import secrets;print(secrets.token_urlsafe(32))"` — and pipe it straight to
      `gcloud secrets versions add` (step 4.3). **Never paste it into a file.**

---

## §4 — Zero-downtime rotation runbook

> **NOT EXECUTED. This is a written procedure for the native.** Every command below that mutates
> state was deliberately **not run** by this lane. Only the read-only probes in §7 were run.
>
> Design principle: **additive first, subtractive last.** At no point between 4.1 and 4.8 is any
> working credential invalidated, so every step before 4.9 is trivially abandonable by simply
> stopping.

### Phase A — Create the replacement role (additive; zero risk to running services)

**4.1 — Create the new Postgres role.**

`amjis_app` owns all 291 tables and both schemas. Do **not** attempt to reconstruct its grant set
table-by-table — grant membership in it instead, which is exact by construction and cannot drift.

Connect through the Auth Proxy as `postgres`:

```bash
cloud-sql-proxy --address 127.0.0.1 --port 5433 \
  madhav-astrology:asia-south1:amjis-postgres &
# password for `postgres` = INC-3 today; this is the last legitimate use of it
psql -h 127.0.0.1 -p 5433 -U postgres -d amjis
```

```sql
-- new login role; password supplied interactively, never in history
CREATE ROLE amjis_app_v2 WITH LOGIN PASSWORD '<NEW-PASSWORD-FROM-3.6>';

-- exact privilege equivalence, by membership rather than reconstruction
GRANT amjis_app TO amjis_app_v2;
GRANT cloudsqlsuperuser TO amjis_app_v2;

-- match the attributes read in §7 probe D
ALTER ROLE amjis_app_v2 CREATEDB CREATEROLE;

-- CRITICAL: make objects created by v2 (i.e. migrations) owned by amjis_app,
-- not by amjis_app_v2. Without this, ownership fragments across two roles and
-- the next rotation becomes far harder than this one.
ALTER ROLE amjis_app_v2 IN DATABASE amjis SET role TO amjis_app;
```

> **Alternative (simpler, if the native prefers no second role):** skip Phase A entirely and just
> `gcloud sql users set-password amjis_app --instance=amjis-postgres --prompt-for-password`, then
> update every secret. **This is not zero-downtime** — every consumer breaks the instant the
> password changes and stays broken until each is repointed. RULING 1 asked for the two-role path
> precisely to avoid that window. Use the two-role path.

**4.2 — Verify the new role, read-only.**

```sql
SELECT rolname, rolcanlogin, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname='amjis_app_v2';
SELECT g.rolname FROM pg_auth_members m
  JOIN pg_roles r ON r.oid=m.member JOIN pg_roles g ON g.oid=m.roleid
  WHERE r.rolname='amjis_app_v2';   -- expect: amjis_app, cloudsqlsuperuser
```

Then prove it can actually work, from a separate shell:

```bash
PGPASSWORD='<NEW>' psql -h 127.0.0.1 -p 5433 -U amjis_app_v2 -d amjis \
  -tAc "SELECT current_user, count(*) FROM chart_facts;"
# expect: amjis_app_v2|27554   (the L1_GANITA_CLOSURE canonical count)
```

A wrong or zero count here means the grant is wrong. **Stop and fix before Phase B.**

**4.3 — Add new Secret Manager versions (additive — existing versions untouched).**

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
> changed — see 4.5. Missing this is the most likely cause of a failed cutover.

### Phase B — Migrate consumers one at a time, verifying after each

Order is chosen so the least-critical consumer proves the credential first.

**4.4 — `amjis-sidecar` (first — lowest blast radius, `latest`-bound).**

```bash
gcloud run services update amjis-sidecar --region=asia-south1 \
  --update-secrets=DATABASE_URL=amjis-pipeline-db-url:latest \
  --update-env-vars=ROTATION_STAMP=$(date +%s)
```

`ROTATION_STAMP` forces a new revision so the `latest` binding is actually re-read (this is the
established convention in the service's existing env — see the `ROTATION_STAMP` values already
present on both `amjis-web` and `amjis-sidecar`).

**Verify before proceeding:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://amjis-sidecar-qm256lasva-el.a.run.app/health   # expect 200
gcloud run services describe amjis-sidecar --region=asia-south1 \
  --format="value(status.latestReadyRevisionName,status.conditions[0].status)"
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-sidecar"
   AND (textPayload:"password authentication failed" OR textPayload:"role \"amjis_app_v2\" does not exist")' \
  --limit=20 --freshness=10m
```

Expect the log query to return **nothing**. If it returns rows, roll back with
`gcloud run services update-traffic amjis-sidecar --region=asia-south1 --to-revisions=amjis-sidecar-00933-f9j=100`
and stop.

**4.5 — `amjis-web` (second — the user-facing service).**

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

**4.6 — `deploy.yml` and the GitHub Actions secrets (third — the silent-revert trap).**

**This step is mandatory and is the one most likely to be forgotten.** `deploy.yml:304` hard-codes
`DB_PASSWORD=amjis-db-password:3`. If it is not updated, the **next merge to `main` will silently
revert `amjis-web` to the old credential** — and after step 4.9 that credential will be disabled,
so the revert will take production down at deploy time rather than at rotation time. That is the
worst possible failure shape: a delayed outage attributed to an unrelated PR.

1. Determine what `PROD_DATABASE_URL` currently holds. It is not readable via the API; check the
   native's own record. If unknown, **replace it regardless** — an unknown-provenance production
   DSN is itself a finding.
2. Rewrite it to the new role:
   ```bash
   printf '%s' 'postgresql://amjis_app_v2:<NEW-PASSWORD>@127.0.0.1:5432/amjis' | gh secret set PROD_DATABASE_URL
   ```
   (Port 5432 — that is the port `deploy.yml:189` starts the proxy on. `fresh_chart_smoke.yml` and
   `shad-darshana-circularity-guard.yml` use 5433. Do not conflate them.)
3. Edit `deploy.yml:277` `DB_USER=amjis_app` → `DB_USER=amjis_app_v2` and `deploy.yml:304`
   `DB_PASSWORD=amjis-db-password:3` → `:4`. Land as a normal PR.
4. **Verify by running a deploy** and re-checking that `amjis-web`'s serving revision still carries
   `amjis-db-password:4` and `DB_USER=amjis_app_v2`. A rotation that survives one deploy cycle is
   rotated; one that has not been deploy-tested is not.

**4.7 — `brahma-build-pipeline-job` (fourth — passive).**

Bound to `amjis-pipeline-db-url:latest`; it picks up the new version at its next execution. No
config change needed. Prove it:

```bash
gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 --wait
gcloud run jobs executions list --job=brahma-build-pipeline-job --region=asia-south1 --limit=1
```

Do not leave this untested — a batch job that fails to authenticate fails silently until the next
scheduled build.

**4.8 — Local developer surface (fifth).**

- Update `/Users/Dev/.claude.json` → `mcpServers.postgres.args[2]` to the `amjis_app_v2` DSN
  (or, better, to an env-var reference so it never holds a literal again).
- Confirm no other machine or shell profile holds `amjis_app`'s old password.

### Phase C — Disable the leaked roles, then prove nothing depended on them

**4.9 — Confirm zero remaining use of the old role, then disable it.**

First, positive evidence that no session is authenticating as `amjis_app`:

```sql
SELECT usename, application_name, client_addr, count(*), max(backend_start)
FROM pg_stat_activity GROUP BY 1,2,3 ORDER BY 1;
```

`amjis_app` must not appear. Because `pg_stat_activity` is a point sample, also check a window:

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

Then rotate INC-3 as well — this is not optional, it is the live superuser credential:

```bash
gcloud sql users set-password postgres --instance=amjis-postgres --prompt-for-password
# then store it, so it stops being unmanaged:
printf '%s' '<NEW-POSTGRES-PASSWORD>' | gcloud secrets create amjis-postgres-superuser-password --data-file=-
```

Before rotating `postgres`, resolve `fresh_chart_smoke.yml`'s use of it (§2.3) — that workflow reads
production as `postgres` and will break. It should be moved to `retrieval_census_ro` (read-only,
already provisioned) rather than given the new superuser password.

**4.10 — Disable the superseded Secret Manager versions.**

```bash
gcloud secrets versions disable 2 --secret=amjis-db-password      # INC-1
gcloud secrets versions disable 3 --secret=amjis-db-password      # INC-2
gcloud secrets versions disable 2 --secret=amjis-pipeline-db-url  # INC-1
gcloud secrets versions disable 3 --secret=amjis-pipeline-db-url  # INC-2
```

Disable, do not destroy — a disabled version can be re-enabled if a forgotten consumer surfaces;
a destroyed one cannot. Revisit after a full week of clean operation and destroy then.

**4.11 — Prove the disablement (the can-fail step).**

The rotation is only demonstrated if the old credential is shown to be *dead*, not merely *unused*:

```bash
# expect: FATAL: role "amjis_app" is not permitted to log in
PGPASSWORD='<OLD-INC-2>' psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -w -tAc "SELECT 1;"

# expect: FATAL: password authentication failed for user "postgres"
PGPASSWORD='<OLD-INC-3>' psql -h 127.0.0.1 -p 5433 -U postgres -d amjis -w -tAc "SELECT 1;"

# and the services still healthy, 30+ minutes after the disable
curl -s https://amjis-web-qm256lasva-el.a.run.app/api/health
curl -s https://amjis-mcp-qm256lasva-el.a.run.app/health
curl -s -o /dev/null -w "%{http_code}\n" https://amjis-sidecar-qm256lasva-el.a.run.app/health
```

**4.12 — Watch for stragglers for 72 hours.**

```bash
gcloud logging read \
  'resource.type="cloudsql_database"
   AND (textPayload:"password authentication failed" OR textPayload:"is not permitted to log in")' \
  --limit=100 --freshness=72h
```

Any hit names a consumer this inventory missed. Add it here before closing the incident.

### Phase D — Close the incident

**4.13 —** Append an EXECUTION RECORD to §8 of this document: date, who executed, new role name,
new secret version numbers, revision ids before/after, the §4.11 output, and the §4.12 result.
Change this document's frontmatter `status` from `UNRESOLVED-PENDING-NATIVE-EXECUTION` to
`RESOLVED` and bump to v1.1. **Until that record exists, the incident is open.**

### Rollback

| Step reached | How to undo |
|---|---|
| 4.1–4.3 | Nothing to undo; the additions are inert. Optionally `DROP ROLE amjis_app_v2;` and disable the new secret versions. |
| 4.4–4.8 | `gcloud run services update-traffic <svc> --region=asia-south1 --to-revisions=<pre-rotation-revision>=100`. Revert the `deploy.yml` PR. Old credentials are still valid at this point. |
| 4.9 | `ALTER ROLE amjis_app LOGIN;` — instantly restores the old path. |
| 4.10 | `gcloud secrets versions enable <n> --secret=<name>`. |
| after `postgres` rotation | Not reversible to the old value; recover by setting a further new password. Keep the new one in Secret Manager. |

---

## §5 — Recurrence guard

Rotation without these three is a countdown to the fourth incident. The 2026-06-02 rotation is the
proof: it fixed INC-1 and produced INC-2 three days later.

**5.1 — `B-SECRETSCAN-SCOPE` (sibling lane, DVA RULING 3) — the detector gap.**
`platform/scripts/governance/secret_scan.sh` is allowlist-scoped to 8 `SCAN_TARGETS` while its
docstring claims *"Scan the repository tree, suppress known-noise paths"*. This lane confirms the
gap empirically:

```
$ bash platform/scripts/governance/secret_scan.sh
secret_scan: gitleaks not found — using bash regex set
secret_scan: PASS (no literal credentials in scanned paths)
EXIT=0
```

**The scanner returns PASS while a live production superuser credential sits on `origin/main` in
two files and a live app credential sits in sixteen.** This is §N.8's canonical failure: green
because it stopped looking.

Two gaps, not one — B-SECRETSCAN-SCOPE should fix both:

- **(a) Scope.** 14 of the 16 INC-2 files and 1 of the 2 INC-3 files are outside all 8 targets
  (`platform/python-sidecar/`, `platform/src/`, `docs/`, `00_ARCHITECTURE/`). RULING 3 covers this.
- **(b) Pattern shape — not in RULING 3, surfaced here.** Even *inside* a scanned target the
  scanner misses the dominant leak shape. `platform/scripts/` **is** a `SCAN_TARGET`, yet
  `platform/scripts/governance/v13_production_gate.py:13` was not caught, because the pattern set
  requires `(PGPASSWORD|DB_PASSWORD|DATABASE_PASSWORD)=<value>` and the code reads
  `os.environ.get("DB_PASSWORD", "<literal>")` — no `=`. Widening scope alone would still miss it.
  **Add a pattern for the env-default idiom** in both languages:
  `os.environ.get\(\s*["'][A-Z_]*(PASSWORD|SECRET|TOKEN|KEY|URL)["']\s*,\s*["'][^"']{8,}` and the
  JS/TS equivalent `process.env.X ?? "…"` / `process.env.X || "…"`.
- **(c) Fixture.** RULING 3 mandates `fail/` fixtures reproducing the exact leaked shape. Include
  **both** shapes: the bare DSN literal *and* the `env.get(name, default)` idiom.

**5.2 — `B-SECRET-REDACT` (sibling lane, DVA RULING 2) — the copy-paste seed.**
Removes the plaintext from current file contents via env-var indirection. **Its scope must be
widened.** RULING 2 scoped it to the 9 INC-1 files. On this lane's evidence it must also cover the
16 INC-2 files and the 2 INC-3 files — **27 files total, 44 occurrences**. The INC-1 files are
inert (dead credential); the other 18 hold live secrets and are the urgent half.

Redaction of the INC-2/INC-3 files must **fail fast, not fall back**:

```python
# correct — no default; missing env is a loud error
DB_URL = os.environ["DATABASE_URL"]
# or, with a message
DB_URL = os.environ.get("DATABASE_URL") or sys.exit("DATABASE_URL is required")
```

The `os.environ.get(NAME, "<literal>")` idiom must not be preserved with a *new* literal. That is
exactly how INC-2 was born.

**Git history cannot be purged** (RULING 2 withholds history-rewrite authority; a rewrite would not
recall replicated bytes). INC-1 appears in commits from `39b91dd0` onward, INC-2 in 20 commits,
INC-3 in 12. **They are public permanently. Rotation is the whole remediation; redaction is the
recurrence control.**

**5.3 — Structural controls (neither sibling lane covers these).**

| Control | Rationale |
|---|---|
| Make `secret_scan.sh` a **blocking** CI gate on `main` (RULING 3 names this). | Today nothing stops the next literal from landing. |
| Enable GitHub **push protection / secret scanning** on `amonty84/Madhav`. | Free for public repos; catches at push time, before the bytes are public. Defence that does not depend on this repo's own tooling. |
| Ban the `env.get(NAME, "<literal>")` idiom in a lint rule, not just a scanner. | The scanner catches secrets; the lint catches the *shape* that produces them. |
| Set `requireSsl=true` (R2) and consider `connectorEnforcement=REQUIRED` (R4). | Turns `authorizedNetworks` from the only control into one of three. |
| Set `deletionProtectionEnabled=true` (R5) and enable PITR (R6). | Recovery floor is currently 7 daily backups with no point-in-time granularity. |
| Put the `postgres` superuser password in Secret Manager (step 4.9). | It is unmanaged today — no version history, no rotation path, no audit. |
| Adopt a rotation cadence with a dated review, recorded in `CURRENT_STATE`. | Both prior rotations were incident-driven. |

---

## §6 — Residuals and open questions

**Residuals — discovered by this lane, not fixed (never silently dropped):**

| # | Residual | Owner |
|---|---|---|
| RES-1 | **INC-2 and INC-3 exist at all.** RULING 1 was scoped to INC-1. The swarm's understanding of this incident was materially incomplete until this lane. DVA should consider whether RULING 1 needs amending. | DVA |
| RES-2 | **B-SECRET-REDACT's scope (9 files) is too narrow** — should be 27 files / 44 occurrences (§5.2). The 9 it currently covers are the *dead* credential; the 18 it does not are the live ones. | DVA → B-SECRET-REDACT |
| RES-3 | **B-SECRETSCAN-SCOPE's scope is too narrow** — the pattern-shape gap (§5.1b) is independent of the scope gap and survives fixing it. | DVA → B-SECRETSCAN-SCOPE |
| RES-4 | `fresh_chart_smoke.yml:147` reads **production** as role `postgres` via a passwordless DSN. Either it is failing silently, or it has an out-of-band `PGPASSWORD`. Unresolved. It is an INC-3 consumer either way. | B-lane / native |
| RES-5 | `shad-darshana-circularity-guard.yml:66-68` starts a proxy against production with no visible credential source. **Owned by ṢAḌ-DARŚANA (§7 not-owned)** — reported, not touched. | Report to ṢAḌ-DARŚANA |
| RES-6 | GH Actions secret `PROD_DATABASE_URL` (updated 2026-06-22) has unknown contents and unknown role. Unknowable read-only. | Native (step 4.6) |
| RES-7 | `amjis-db-password` v2 and `amjis-pipeline-db-url` v2 remain `enabled` in Secret Manager while carrying a dead credential. Harmless but misleading; a reader would reasonably assume an enabled version is valid. | Step 4.10 |
| RES-8 | **No compromise assessment has been performed.** Whether INC-2 or INC-3 was ever used by an unauthorised party is unknown. Query: `gcloud logging read 'resource.type="cloudsql_database" AND resource.labels.database_id="madhav-astrology:amjis-postgres" AND textPayload:"connection authorized"' --freshness=30d` — note Cloud Logging's default retention will not reach back to 2026-04-29, so the early window may be unrecoverable. | Native |
| RES-9 | `amjis_app` holds `CREATEDB`, `CREATEROLE`, and `cloudsqlsuperuser` — far beyond what an application role needs. The rotation is a natural moment to right-size it, but doing so inside the rotation would couple two risks. Deliberately excluded from §4. | Follow-on |
| RES-10 | `WATCHDOG_SECRET` is set as a **plaintext env var** on `amjis-web` rather than a `secretKeyRef`, even though a `watchdog-secret` Secret Manager entry exists (created 2026-06-06). Not exposed in the repo (verified), so not part of this incident, but the same class of defect. | Follow-on |

**Questions for DVA:** see the lane's FINAL_SUMMARY.

---

## §7 — Evidence appendix (read-only commands actually run)

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

**Probe D — role attributes and memberships.**
```
       rolname       | rolsuper | rolcreatedb | rolcreaterole | rolcanlogin | rolconnlimit
---------------------+----------+-------------+---------------+-------------+--------------
 postgres            | f        | t           | t             | t           |           -1
 amjis_app           | f        | t           | t             | t           |           -1
 retrieval_census_ro | f        | f           | f             | t           |            5

  member   |   granted_role
-----------+-------------------
 amjis_app | cloudsqlsuperuser
 postgres  | cloudsqlsuperuser

 nspname |   owner   |                          nspacl
---------+-----------+-----------------------------------------------------------
 auth    | amjis_app |
 public  | amjis_app | {amjis_app=UC/amjis_app,postgres=UC/amjis_app,
                       retrieval_census_ro=U/amjis_app}

owned_by_amjis_app | total_public_tables
              291  |                 291
```

**Probe E — Cloud Run credential bindings** (`gcloud run services describe … --format="yaml(spec.template.spec.containers[].env, …)"`).
```
amjis-web     : DB_PASSWORD ← secretKeyRef{name: amjis-db-password, key: '3'}
                DB_USER=amjis_app  DB_NAME=amjis
                INSTANCE_CONNECTION_NAME=madhav-astrology:asia-south1:amjis-postgres
                SA: amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com
amjis-sidecar : DATABASE_URL ← secretKeyRef{name: amjis-pipeline-db-url, key: latest}
                annotation run.googleapis.com/cloudsql-instances=…:amjis-postgres
                SA: amjis-sidecar-runtime@…
amjis-mcp     : (no DB credential of any kind — full env is MCP_INTERNAL_TOKEN,
                 PYTHON_SIDECAR_API_KEY, MCP_CANARY_KEY, PLATFORM_URL,
                 PYTHON_SIDECAR_URL, MCP_BASE_URL)
                SA: amjis-mcp-runtime@…
```

**Probe F — GitHub Actions secrets (names only; values are write-only).**
```
$ gh secret list
FIREBASE_ADMIN_CREDENTIALS   2026-05-18   NEXT_PUBLIC_FIREBASE_*  (6)   2026-04-30
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY 2026-05-31   PROD_DATABASE_URL     2026-06-22
SMOKE_CHART_ID               2026-05-29   SMOKE_SESSION_COOKIE     2026-05-29
```
`DATABASE_URL` and `TAP_DATABASE_URL` are **absent** ⇒ `samiksha-daily.yml` and `tap-ci.yml` are
no-ops today.

**Probe G — Secret Manager version metadata (payloads compared by equality, never printed).**
```
amjis-db-password       v1 disabled 2026-04-25   v2 enabled 2026-05-28 [= INC-1]   v3 enabled 2026-06-02 [= INC-2]
amjis-pipeline-db-url   v1 enabled  2026-04-28   v2 enabled 2026-05-30 [= INC-1]   v3 enabled 2026-06-06 [= INC-2]
retrieval-census-ro-db-password  v1 enabled 2026-07-19  [not exposed]
```

**Probe H — live service health at the time of writing (rotation baseline).**
```
amjis-web     https://amjis-web-qm256lasva-el.a.run.app/api/health  → 200 {"status":"ok"}
amjis-mcp     https://amjis-mcp-qm256lasva-el.a.run.app/health      → 200 {"status":"ok",
              "service":"marsys-mcp","version":"1.0.0","tools":88}
amjis-sidecar https://amjis-sidecar-qm256lasva-el.a.run.app/health  → 200
revisions     amjis-web-01281-p25 · amjis-mcp-00517-b5q · amjis-sidecar-00933-f9j
```

**Probe I — exposure counts on `origin/main`** (`git grep -l --fixed-strings "$VAL" origin/main | wc -l`).
```
INC-1 :  9 files · 19 occurrences · 1st commit 39b91dd0 (2026-05-29)
INC-2 : 16 files · 23 occurrences · 1st commit 0c2d4d98 (2026-06-05) · 20 commits in history
INC-3 :  2 files ·  2 occurrences · 1st commit 599cfce1 (2026-04-29) · 12 commits in history
```

**Probe J — the current scanner's verdict** (§5.1).
```
$ bash platform/scripts/governance/secret_scan.sh
secret_scan: PASS (no literal credentials in scanned paths)   EXIT=0
```

**Cleanup.** The local Cloud SQL Auth Proxy started for probes A–D was stopped
(`pkill -f "cloud-sql-proxy --address 127.0.0.1 --port 5434"` → `proxy stopped`). It was a local
process only; no infrastructure was modified.

---

## §8 — EXECUTION RECORD

*(empty — the runbook has not been executed)*

| field | value |
|---|---|
| Executed on | — |
| Executed by | — |
| New role name | — |
| New `amjis-db-password` version | — |
| New `amjis-pipeline-db-url` version | — |
| `amjis-web` revision before → after | — |
| `amjis-sidecar` revision before → after | — |
| `deploy.yml` updated (PR) | — |
| §4.11 can-fail proof output | — |
| §4.12 72h straggler check | — |
| `postgres` (INC-3) rotated | — |
| Incident status | **UNRESOLVED** |

---

*End of SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL v1.0 — B-SECRET-ROTATE-PREP, 2026-07-30.
Preparation only. Not a closure. No credential was rotated, created, disabled, or written by this
lane; no IAM, Secret Manager, Cloud SQL, or Cloud Run resource was modified.*
