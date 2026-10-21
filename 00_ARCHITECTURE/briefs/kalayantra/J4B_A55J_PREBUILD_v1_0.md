---
artifact: J4B_A55J_PREBUILD
version: "1.0"
status: BUILT_WAITING_ON_GATE — source preparation only; operational acceptance not earned
date: 2026-10-20
authority: "A6 D-40 / SR-A4-01; SR-GRANTS-MINIMAL; SR-A55J-A55M-RESCOPE (DECISIONS_SURROGATE.jsonl line 289)"
changelog:
  - "1.0: the post-window provisioning of the full build, prepared inside the existing one-shot workflow and the existing Cloud Run readback. No migration, no new executor kind, nothing dispatched."
---

# J-4b-a55j preparation: post-window provisioning

Item J-4b-a55j (inherited Pravāha A5.5j) needs four things true in production after the protected window: the 1378 v7 grants (the title's "1241 v7, PR 2949" is the same migration before its renumbering to 1378; it has landed and is unchanged), the L1 read ACLs, the sealer's password, and the verification job configured but disabled. This branch prepares the source for each. It provisions nothing, dispatches nothing and enables nothing.

## What was built, and where

| Need | Built | Oracle |
|---|---|---|
| L1 read ACLs (`chart_facts`, `chart_dashas`; 1378 header lines 53–57 leave them to the data-plane ACL owner) | stage `grant-l1-reads` of `platform/scripts/gochara-provision-roles.sh`: SELECT on those two tables for `gochara_verifier` and `gochara_sealer`, nothing else, closure-checked (SELECT only, no write privilege, no grant option) in the SAME transaction; refuses if a role or table is absent | `platform/python-sidecar/tests/test_gochara_provision_roles_script.py` against a real throwaway PostgreSQL 15 |
| Sealer password (replaces person-run act 2b staging) | stage `sealer-credential`: password generated in the run, full DSN written to Secret Manager (`gochara-sealer-db-url`) BEFORE the role is touched, role activated in one transaction with its postconditions, observed by an authentication, then listed. Failure compensates (password back to NULL, verified) and destroys this run's secret version. Never printed, never read back | same file |
| Dispatch | `fleet/role_provisioning_dispatch.py` serves the three stages; `grant-l1-reads` takes no `dsn_tail`; `sealer-credential` accepts only the sealer's loopback tail `@127.0.0.1:5432/<db>` (runbook line 62: the two roles' tails differ). Still lease-gated, still refuses `sealer-password` | `fleet/tests/test_executor_role_provisioning_dispatch.py` |
| Workflow | `.github/workflows/gochara-role-provisioning-oneshot.yml` offers the two new stages (workflow_dispatch only, unchanged environment gate) | `platform/tests/unit/gochara_role_provisioning_workflow_static.test.ts` |
| Verification job configured | `cloudrun_job_readback --job gochara-verification-job` (SR-A55J-A55M-RESCOPE: no new executor kind): one describe call, ten named checks (image by digest, verifier identity, entry point, exact environment, runner digest and commit, one task, Cloud SQL, retries, resources). See `fleet/CLOUDRUN_READBACK_v1_0.md` v1.4 | `fleet/tests/test_cloudrun_readback_verification_job.py` |
| Verification job disabled | the executor table entry `verification_job` keeps `enabled: false`; asserted by the same test | same |
| Independent readback of grants and principals | already built by J-4b: `platform/scripts/readbacks/gochara_provisioning_readback.sql` (principals, the full 1378 set, the two L1 reads, grant options, memberships). Unchanged here | its existing suite |
| Builder cannot write verification rows | the same SQL, kinds `builder-write` and `builder-column-write`: every write privilege of `data_plane_builder` on `ka_gochara_search_inventory_verification` and `ka_gochara_eval_window_verification` must read false from the catalog (read from privileges, never attempted) | its existing suite |

## Production steps that are prepared but NOT executed (for the sitting, after A5.5e / J-4a)

Each is a person-gated or controller-gated act; this branch does none of them.

1. After the window and the routine 1378 deploy, and after `create-roles` has run: a reviewed `gochara_role_provisioning_dispatch` request, stage `grant-l1-reads`, `confirm PROVISION-GOCHARA-ROLES`, `window_lease_id` = the request's own lease. Then stage the audit SQL under `run/ops/sql/` and request `readback_sql`; every row must read `ok = true`.
2. Create the empty Secret Manager container `gochara-sealer-db-url` and bind `secretVersionManager` TEMPORARILY to the workflow's principal (as act 11 did for the verifier secret); remove the binding after step 3. Not done here: these are production IAM acts.
3. After the live-gate proof, stage `sealer-credential` with the sealer's loopback tail. Evidence: the run's printed non-secret facts (attributes, `secret_version:` lines). The password is never printed.
4. Deploy the verification job definition from `main` through the existing `gochara-verification-job-deploy.yml`, then request `cloudrun_job_readback` with `job = gochara-verification-job`. `all_checks_ok` must be true; a null `max_retries_is_zero` is settled by the workflow's v2 REST read, not assumed true.
5. The controller writes the operation receipt at `/Users/Dev/kalayantra/run/ops/receipts/J-4b-a55j.json` (the item's detector path) binding the request, operation and evidence digests, and the independent reviewer writes the step receipt `principals_grants_disabled_config`. Neither exists yet; no builder writes them.

## What this does NOT prove

That any principal exists, any grant is held, the sealer has a password, or the job is deployed: all of that is production state, measured only by the steps above. A green source test is not an operation receipt.

## Interpretations

* **(I)** The title's "1241 v7 (PR 2949)" is migration 1378 as landed (renumbered). Alternative: a separate 1241 migration; none exists on main (`platform/migrations/` has 1240, 1242).
* **(I)** The L1 grants and the sealer credential are two new stages of the existing one-shot rather than a migration or a new executor kind (SR-GRANTS-MINIMAL, SR-A55J-A55M-RESCOPE). Alternative: a small additive migration for the L1 grants; rejected because 1378 says the data-plane ACL owner manages those ACLs.
* **(I)** "Disabled" means the executor table admission state, as in `J4B_PREBUILD_v1_0.md`. A Cloud Run job has no native switch; stopping every other principal from running it would need a separately specified IAM or scheduler policy.
* **(I)** The `--job` shape is taken from the deploy workflow's flags, not a captured live response; the first real run proves it and a different shape refuses.
* **(I)** The provisioning tests need PostgreSQL 15 binaries (`GOCHARA_PROVISION_TEST_PGBIN`) and a valid `LC_ALL`; under PostgreSQL 17 the role creator becomes an automatic member of each role it creates, which the 15-shaped membership assertion rejects. Cloud SQL is the 15 shape.
