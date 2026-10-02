---
artifact: ROLES_AND_SEAL_PROVISIONING_RUNBOOK
version: "1.0"
status: "WRITTEN, NOT AUTHORISED TO RUN. No act in this runbook is performed by anyone until the steward says so. Authority: decisions/NATIVE_RESPONSES_BY_DELEGATE_v1_0.md §2 (NRS-CREDENTIAL-ACTS-20261002, acts 1–8), §3 (NRS-SEAL-APPROVER-20261002), reading RUL §3.6. Act 9 (the window dispatch) and every seal approval are the owner's, in person."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 (steward M20261002T122622-b1af)
how_to_use: "Execute as WRITTEN. Any deviation, surprise or failed check = STOP, report, do not fix forward. After each act: send the report of §3 before the next act begins. A 'stop' from the owner halts at the next act boundary."
proved_on_the_disposable_mirror: "PostgreSQL 15.17 with scram-sha-256 and a real pg_hba: `CREATE ROLE … LOGIN NOINHERIT … PASSWORD NULL` is accepted; the role has rolcanlogin = true and rolpassword IS NULL; a login attempt with ANY password is refused ('password authentication failed'); `ALTER ROLE … PASSWORD '<x>'` later makes it log in; `ALTER ROLE … PASSWORD NULL` makes it refuse again; `pg_has_role(<new role>, 'cloudsqlsuperuser', 'MEMBER')` = false for a role made by SQL CREATE ROLE (2026-10-02, §6)."
---

# Roles and seal provisioning — the runbook

## 0. What this is, in plain words
Option A needs two new database logins (a **verifier** and a **sealer**), a place for each password, a machine identity for the verification job, and an approval gate that only the owner can open. This runbook is the exact, checkable sequence the steward follows — **once, in one sitting, immediately before the protected-window dispatch** — so that migration 1240's role-guarded grants fire on their own. Nothing here is run until the steward says so. Nobody sees a password.

## 1. Facts and standing rules this runbook rests on
1. **Order (NRS-CREDENTIAL-ACTS §2.5):** **7** (now, code only) → *[window preconditions hold; dispatch scheduled]* → **3 → 4 → 1 → 5 → 2a** → *[live-gate proof, after 5 and before 2b]* → **9** (owner dispatches the window) → **8** (1241 by the ordinary deploy, then verify) → *[L1 read ACLs by the data-plane owner]* → *[Codex ACCEPT of the verification job]* → **2b → 6** → first operator-dispatched verification → first seal (owner approves).
2. **Identity.** Both CLIs on the steward's machine run as the owner's accounts (verified read-only: `gh api user` → `amonty84`; `gcloud auth list` → `mail.abhisek.mohanty@gmail.com`, project `madhav-astrology`). Every act therefore appears in the audit logs under the owner's identity. **This is exactly why the seal approver must be an identity no agent session can use (§5.3).** Every report states the identity used.
3. **Roles are created by SQL `CREATE ROLE` over the ownership-admin path ONLY.** **Never** `gcloud sql users create` and never the console: both make the new user a member of `cloudsqlsuperuser`. Every role act ends with `SELECT pg_has_role('<role>','cloudsqlsuperuser','MEMBER')` = **false**.
4. **Passwords are never seen by anyone** (§2). Generated at execution, written once into the SQL statement and once into the secret store by `stdin` pipes, never echoed, never in argv, never in a file, never in a message.
5. **No grants are made in any act.** Grant sources for the two roles are 1240 (role-guarded, fires because the roles exist when it runs) and 1241 (belt-and-braces backfill carrying 1240's set too). A role created here holds **nothing** and belongs to **no** role.
6. **Pre-existence is a stop condition** for every resource named below.
7. **No production query beyond the read-only checks named here; none touches chart data.**
8. **No act is performed by analogy.** If a step is not written here, it is not authorised.

## 2. Handling secrets (applies to every act that sets a password)
```
# run inside ONE subshell; PW exists only there; xtrace OFF; nothing is echoed
( set +x; umask 077
  PW="$(openssl rand -hex 48)"                                  # 384 bits, URL-safe (hex), generated at execution
  printf "ALTER ROLE %s PASSWORD '%s';\n" "$ROLE" "$PW" | psql "$ADMIN_CONN" -v ON_ERROR_STOP=1 -X -q      # statement goes over stdin, not argv
  printf '%s' "postgresql://${ROLE}:${PW}@${DSN_HOST_PATH_AND_PARAMS}" | <secret-store write from stdin>    # same variable, second pipe
  unset PW )
```
- `printf` is a shell builtin: the password is in no process's argument list. `psql -c "…PASSWORD '…'"` and `--set=pw=…` are **forbidden** (argv is visible in `ps`).
- `DSN_HOST_PATH_AND_PARAMS` (host or `/cloudsql/<instance>` socket, port, database, `sslmode`) is copied from the **shape** of the builder's DSN with user and password blanked — obtained with a redacting transform (`sed -E 's#//[^@]*@#//USER:PASS@#'`), recorded in the act's report, never the builder's secret value.
- **The report carries only:** the secret's resource name and version id, the role name, and the read-only verification output.

## 3. Report template (sent after EACH act, before the next begins)
Act number and name · identity used (login) · UTC timestamp · resource names created · the read-only verification output (no secrets) · the rollback command · the audit-log reference · "NEXT ACT WAITS FOR YOUR 'continue' / 'stop'".

## 4. Preconditions common to acts 3–2a (read-only checks, all must be TRUE; a FALSE = STOP)
| # | check | how (read-only) |
|---|---|---|
| P1 | The owner has fixed the dispatch time and the sitting is open | the steward's note; the owner's message |
| P2 | Act 7 (secret-isolation preflight extension) is merged and its CI green | `gh pr view <n> --json state,mergeCommit` |
| P3 | The window preconditions of NRS-CREDENTIAL-ACTS §2.6 hold: Codex R10-1, R10-2, R10-3, R10-4, R10-7 closed at source; **1240 and 1241 ACCEPT on their FINAL bytes**; the composed rehearsal re-run on those bytes; 1206 **still unapplied** (re-confirmed read-only immediately before — `SELECT count(*) FROM _migrations_applied WHERE filename LIKE '1206%'` = 0 and `to_regclass('public.ka_gochara_search_inventory_verification') IS NULL`); routine 1230/1234/1236 applied by the ordinary deploy | the review verdict; the ledger query; `gh pr view` |
| P4 | Nothing of these names exists yet: SA `gochara-verifier-runtime@…`, secret `gochara-verifier-db-url`, roles `gochara_verifier` / `gochara_sealer`, environment `gochara-seal` | `gcloud iam service-accounts list --filter=email:gochara-verifier-runtime*`; `gcloud secrets list --filter=name:gochara-verifier-db-url`; `SELECT rolname FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')` (0 rows); `gh api repos/Marsys-Technologies/Madhav/environments/gochara-seal` (404) |
| P5 | **The SQL admin route is settled** (OPEN ITEM — see §7.1): which session holds `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL` for acts 1 and 2a | the steward states the route before the sitting |

## 5. The acts

### Act 7 — extend the secret-isolation preflight (code only; NOW)
- **Executor:** Stream B authors; the steward reviews and queues. **Not yet authored** (see §7.3).
- **Spec of the gate:** `platform/scripts/data-plane-secret-isolation-preflight.ts` must know the pair `gochara-verifier-runtime@<project>.iam.gserviceaccount.com` / `gochara-verifier-db-url` and assert: the builder SA binds only the builder secret; the verifier SA binds only the verifier secret; neither can read the other's; **unknown pairs still fail**; the builder pair (`BUILDER_SERVICE_ACCOUNT`, `BUILDER_SECRET`) is unchanged. The sealer has no GCP identity at all (its credential lives only in the `gochara-seal` environment secret).
- **Verification:** CI green plus the gate's own tests, including a negative test per assertion. **Rollback:** revert the PR. **Report:** PR number, merge commit, CI run id.

### Act 3 — create the verifier's service account
- **Preconditions:** P1–P5.
- **Command:** `gcloud iam service-accounts create gochara-verifier-runtime --project madhav-astrology --display-name "Gochara verification job runtime (no keys)"`
- **Least privilege:** project roles = **the minimum the builder SA holds for Cloud SQL connectivity and logging** (mirror them: list the builder SA's roles read-only first and report the list); **no project-level Secret Manager role; no key file is ever created.**
- **Verification (read-only):** `gcloud iam service-accounts describe gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com`; `gcloud projects get-iam-policy madhav-astrology --flatten=bindings[].members --filter="bindings.members:serviceAccount:gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com" --format="value(bindings.role)"` (roles listed in the report); `gcloud iam service-accounts keys list --iam-account=…` shows **no user-managed key**.
- **Rollback:** `gcloud iam service-accounts delete gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com`. **Report:** SA email, roles held, audit-log reference.

### Act 4 — the verifier's secret container and its single binding
- **Preconditions:** act 3 done and verified; the secret does not exist.
- **Commands:** `gcloud secrets create gochara-verifier-db-url --replication-policy=automatic` (container only — **no version yet**); `gcloud secrets add-iam-policy-binding gochara-verifier-db-url --member=serviceAccount:gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com --role=roles/secretmanager.secretAccessor`.
- **Verification:** `gcloud secrets get-iam-policy gochara-verifier-db-url` shows **exactly one** accessor binding (the verifier SA) and no other principal with `secretmanager.versions.access`; the same command on `data-plane-builder-db-url` shows the verifier SA **absent**; the builder SA absent from the verifier secret; **act 7's gate passes**.
- **Rollback:** destroy any versions; `gcloud secrets delete gochara-verifier-db-url`. **Report:** secret resource name; the policy output.

### Act 1 — `CREATE ROLE gochara_verifier` (SQL, ownership-admin path)
- **Preconditions:** acts 3–4 done and verified; `pg_roles` shows the role **absent**; still inside the sitting.
- **Statement (exactly this; no PASSWORD clause here — the password is set in the same act by §2, never in the CREATE):**
  `CREATE ROLE gochara_verifier LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS CONNECTION LIMIT <n> PASSWORD NULL;` — `<n>` is the job's concurrency (recorded here by the steward from the job design; default `4`).
  Then the password pipeline of §2 with `ROLE=gochara_verifier` and the secret store write `gcloud secrets versions add gochara-verifier-db-url --data-file=-`.
- **Never** `gcloud sql users create`, never the console. **No GRANT, no membership edge.**
- **Verification (read-only; all five are reported verbatim):**
  1. `SELECT rolname, rolcanlogin, rolinherit, rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls, rolconnlimit FROM pg_roles WHERE rolname = 'gochara_verifier';` → `t / f / f / f / f / f / f / <n>`.
  2. `SELECT pg_has_role('gochara_verifier','cloudsqlsuperuser','MEMBER');` → **false** (any other value = STOP).
  3. `SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname='gochara_verifier') OR roleid = (SELECT oid FROM pg_roles WHERE rolname='gochara_verifier');` → **0**.
  4. `SELECT count(*) FROM information_schema.role_table_grants WHERE grantee = 'gochara_verifier';` → **0**.
  5. `data-plane-ownership-status.ts` still green (the name is outside `data_plane_`, so the name gate and DP-SD-018 are untouched).
  And: `gcloud secrets versions list gochara-verifier-db-url` shows version 1 **enabled**.
- **Rollback:** `DROP OWNED BY gochara_verifier; DROP ROLE gochara_verifier;` and destroy the secret version. **Report:** the five outputs; secret version id; audit-log reference.

### Act 5 — the approval-gated environment `gochara-seal`
- **Preconditions:** act 1 done; **the approver identity of §5.3 exists and satisfies its condition** (the owner's act); the environment does not exist.
- **Command (ONE API call, all four settings together):**
  `gh api -X PUT repos/Marsys-Technologies/Madhav/environments/gochara-seal --input -` with the JSON body
  `{"wait_timer":0,"prevent_self_review":true,"can_admins_bypass":false,"reviewers":[{"type":"User","id":<APPROVER_USER_ID>}],"deployment_branch_policy":{"protected_branches":true,"custom_branch_policies":false}}`
  where `<APPROVER_USER_ID>` = `gh api users/<approver login> --jq .id`.
- **Not the pattern to copy:** the existing `data-plane-production-cutover` environment has **no required reviewers and `can_admins_bypass: true`** (read-only API, this session). `gochara-seal` must be stricter in every one of the four settings.
- **Hold:** the sealer's secret is **not** created until the reviewer rule is confirmed present (a secret behind an environment with no human gate is a seal path with no gate).
- **Verification:** `gh api repos/Marsys-Technologies/Madhav/environments/gochara-seal` shows `required reviewers` = exactly **one** = the §5.3 login; `prevent_self_review: true`; `can_admins_bypass: false`; `deployment_branch_policy.protected_branches: true`; `gh secret list --env gochara-seal` is **empty**.
- **Rollback:** `gh api -X DELETE repos/Marsys-Technologies/Madhav/environments/gochara-seal`. **Report:** the environment JSON (no secrets); reviewer login.

### Act 2a — `CREATE ROLE gochara_sealer` with NO password
- **Preconditions:** act 1 done; the role absent; still inside the sitting.
- **Statement:** `CREATE ROLE gochara_sealer LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD NULL;` — the role **exists** (so 1240's role-guarded sealer grants fire) but **cannot authenticate by password at all** until act 2b. *Proved on the disposable mirror (see frontmatter).*
- **If the server rejects `PASSWORD NULL`** (not expected: it is core PostgreSQL syntax and was accepted on the PG15 mirror): fall back to **`CREATE ROLE gochara_sealer NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;`** — the role still exists for 1240's guard — and act 2b becomes `ALTER ROLE gochara_sealer LOGIN PASSWORD …`. Record which form was used in the report. **Do not** substitute a placeholder password.
- **Verification:** the same five outputs as act 1 for `gochara_sealer`, plus either `SELECT rolpassword IS NULL FROM pg_authid WHERE rolname='gochara_sealer'` (if the admin path may read `pg_authid`) = **true**, or the report records that the `CREATE ROLE` carried no password clause.
- **Rollback:** `DROP ROLE gochara_sealer;`. **Report:** the outputs; audit-log reference.

### Live-gate proof (after act 5, before act 2b; one time)
A no-op workflow (`gochara-seal-gate-proof.yml`, `workflow_dispatch`, one job `environment: gochara-seal`, one step that prints a line) is dispatched. It must: (1) **wait** for approval; (2) the **steward's machine token attempts to act on the pending deployment and is REFUSED**; (3) the owner approves from his own device; (4) the job runs. The report carries the run id, the refused attempt's output and the approval record (login, timestamp). Only then is the environment live and only then is a credential placed behind it (act 2b).
- **Deliberate adjustment to the response's literal text (flagged for the steward):** NRS-SEAL-APPROVER §3.3 says *no agent ever calls any deployment-approval API for `gochara-seal`*, while §3.4 has the steward attempt an approval under the machine token. To keep §3.3 absolute, step (2) uses `state=rejected` — `gh api -X POST repos/Marsys-Technologies/Madhav/actions/runs/<run_id>/pending_deployments --input -` with `{"environment_ids":[<id>],"state":"rejected","comment":"machine-identity probe"}` — which is refused for a non-reviewer exactly as an approval would be, and if it unexpectedly **succeeds** it merely rejects a no-op run. **If the attempt succeeds, STOP: the machine identity can act as the reviewer (the §5.3 condition failed) — nothing further runs until the owner fixes the identity.**

### Act 9 — dispatch of the protected migration window (the owner, in person)
Routine 1234/1236 first (ordinary deploy), then 1204 → 1206 (with PC-4) → 1232 → 1233 → 1240, then routine 1241. **Precondition: acts 3, 4, 1, 5, 2a done and reported** — both roles exist when 1240 runs, so its role-guarded grants fire. No rollback (protected migrations refuse re-application; forward-fix only). The runbook adds no step to this act.

### Act 8 — apply 1241, then verify it granted to both principals
- **Executor:** the ordinary deploy; the steward verifies. **Precondition:** the window completed; 1241's final bytes carry Codex ACCEPT.
- **Verification (all must hold):**
  (i) 1241's post-check line `migration 1241 principals found: gochara_verifier=t, gochara_sealer=t, data_plane_builder=t` — **a line naming zero or one principal = STOP** (never edit 1241 after it is applied; the follow-up is a new migration carrying the same spec);
  (ii) 1241 raised no `post-apply ACL closure failed` (it closes the entire required **and prohibited** ACL for both principals over every `ka_gochara_*`/`kala_gochara_*` relation — table- and column-level — and every `ka_gochara_*` function);
  (iii) the verifier holds INSERT (+ pre-seal DELETE on its own window-verification table) on exactly the two verification tables and nothing on any builder-written table; the sealer holds only the seal set (INSERT on the seal table, a **column-level** UPDATE of the four publication columns, a column-level SELECT of `(chart_id, generation)` on `kala_gochara_windows`, the read set and the seal-side functions); the builder holds **nothing** on either verification table (PC-4); 1240's own role-guarded grants are present.
- **Rollback:** a new REVOKE migration (never an edit). **Report:** the post-check line verbatim; the ACL query outputs.

### Not one of the nine — L1 read ACLs (the data-plane ACL owner)
SELECT on `chart_facts` and `chart_dashas` for **both** principals through the ownership preflight's allowlist — **before the first verification run.** RLS is **off** on both tables (and on `bg_transit_rules`) in production, so a table-level SELECT suffices; neither principal reads `charts`. Verification: `has_table_privilege` for both roles on both tables = true.

### Act 2b — set the sealer's password behind the gate
- **Preconditions:** act 5 verified **with its reviewer rule present**; the live-gate proof passed.
- **Pipeline (§2):** `ALTER ROLE gochara_sealer PASSWORD …` (or `LOGIN PASSWORD …` for the NOLOGIN fallback) over the admin path **and**, in the same pipeline, `gh secret set gochara-sealer-db-url --env gochara-seal --body-file -`. The DSN lives **only** in the environment secret — no copy in Secret Manager or anywhere else; only jobs declaring `environment: gochara-seal` can read it (GitHub's enforcement).
- **Verification:** `gh secret list --env gochara-seal` shows the one secret; `gh api …/environments/gochara-seal` still shows the four protection settings unchanged.
- **Rollback:** `ALTER ROLE gochara_sealer PASSWORD NULL;` and delete the environment secret. **Report:** secret name; confirmation the four settings are unchanged.

### Act 6 — deploy the verification job (after Codex ACCEPT of the job's code)
Defined in `deploy.yml` by Stream A with the steward: same image, the verifier entry point (`pipeline/orchestrator/verification_job.py`), runtime SA = act 3's, the one secret of act 4 as `GOCHARA_VERIFIER_DB_URL`. **Preconditions:** Codex ACCEPT at source of the job (R10-1 complete expected-record derivation, R10-3 lock before read, R10-4 mandatory identity derivation + real runner identity recorded + combined gate, R10-5 identity check covers column grants and login/session separation, R10-6 one boundary contract) and the composed rehearsal re-run on the final bytes; acts 1, 3, 4, 7, 8 and the L1 ACLs done. **The job is dispatched by an operator only** (never by the orchestrator, never on build completion); it refuses by name and writes nothing on any identity or precondition failure. **Verification:** `gcloud run jobs describe gochara-verification-job` shows the SA and the one secret; act 7's gate passes in the deploy; a first run against the held candidate ends in rows **or** a named refusal, never a silent exit. **Rollback:** revert the PR; `gcloud run jobs delete`.

## 5.3 The seal approver identity (the owner's act, in person)
**Condition:** the required reviewer of `gochara-seal` is a GitHub identity **for which no credential exists on any machine or in any session an agent can use.** The owner chooses: **(i)** a dedicated approval account used only from his phone or browser and never authenticated in any CLI, added with the least role that can be a reviewer; or **(ii)** keep `amonty84` as reviewer and remove its token from every agent-accessible machine, re-authenticating the steward's `gh` as a different account (or a fine-grained token) that cannot approve deployments. **Checkable:** `gh api user` on the steward's machine returns a login **different** from the reviewer login; the live-gate proof shows the machine probe **refused**. **Policy, regardless of mechanism:** no agent ever approves any deployment to `gochara-seal`, with any token, for any reason. The owner is the **sole** required reviewer; no second reviewer is added while the chart being sealed is his own. If he is unavailable, the seal waits.

## 6. The seal brief the sealing workflow must show before the gate
A job that runs **before** the environment-gated job, needs **no sealer credential**, and prints to the run summary, every line computed from the database by the same functions the seal uses (never from orchestrator build state): **(1)** chart id, generation, the candidate manifest id and status `candidate`; **(2)** `ka_gochara_candidate_gate_violations(chart, generation)` — the **combined** gate — **= 0** (list shown if not); **(3)** `m of m` (class, path) grains `VERIFIED`, the verifier policy version, the verification job run id, **the runner's recorded code identity** (commit/digest) and timestamps; **(4)** the result policy in force (first candidate: all numeric result fields NULL; serves nothing); **(5)** migration ledger: 1240 and 1241 applied (filenames, `applied_at`); **(6)** the disclosures that attach to the sealed generation; **(7)** one sentence: **a seal is not a flip** — nothing is served until D-FLIP, a separate decision of the owner; **(8)** the exact `DEPLOY_SHA` of the sealing code and a link to the review verdict that accepted it. Inside the gated job the sealing step **re-checks the gate** (the 1206/1240 seal triggers refuse unless every required verification row exists, is `VERIFIED` and still matches the stored data), so what he was shown is what is sealed, or the seal is refused. The seal row records the approver login and the run id. He approves only if the brief reads as he expects; anything unexpected → **Reject**, and the steward investigates.

## 7. Open items to settle BEFORE the sitting (stated, not assumed)
1. **The SQL admin route (P5).** `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL` is a GitHub secret consumed by the protected-cutover jobs (`deploy.yml:903`, `data-plane-protected-cutover.ts:51`). The steward cannot read a GitHub secret, so acts 1 and 2a/2b need either (a) a Cloud SQL admin connection under the owner's gcloud identity that can `CREATE ROLE`, or (b) a **one-shot, reviewed `workflow_dispatch` workflow** that runs exactly the statements above in an environment holding the admin URL. Which one is available is a fact to be established first; if (b), the workflow is itself reviewed code (never a generic "run SQL" job).
2. **The seal-brief database credential.** The brief job reads the database but must hold no sealer credential. Candidate: a third, read-only, grant-minimal login for that one purpose (a further credential act, **not authorised** by the responses file) — or the combined-gate function exposed through an existing read-only path. Decide before act 2b.
3. **Act 7 is not yet authored.** The responses file lists it as "Stream B authors; merge now (reviewed)". The code change to `data-plane-secret-isolation-preflight.ts` (with its negative tests) is Stream B's next deliverable after this runbook.
4. **A tension flagged above** (live-gate proof uses `state=rejected` to keep the no-agent-approval rule absolute).

5. **Open formality, due BEFORE D-FLIP (blocks nothing in this runbook, no seal, no window):** the BPHS graduated-aspect passage is re-read by a human against the served corpus. The BPHS chapter 26 passage is cited by **chunk id**, with the note "re-point when the L0 corpus fix lands", because two corpus-tool defects are open with the L0 owner: `find_verses_about` with a `text_ids` filter returns 0 results, and `read_chapter(bphs, 26)` returns chapter 1 chunks. Nothing in this runbook depends on either.

## 8. What is reported back to the owner, in plain words, after each act
"Act N is done: <what now exists>, created by <identity> at <time>; I checked <the five read-only things> and they read <results>; nothing was granted to it; to undo it I would <rollback>; the next act is <N+1> and waits for your 'continue'." — no password, no secret value, no command output beyond the verification lines.
