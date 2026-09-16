# MADHAV Data Plane RI-02 Security Cutover v1.3

**Authority:** DP-SD-018 §§5–6 source design, amended by DP-SD-019 §§4 and 7 and DP-SD-020's human-reviewer-only supersession. This artifact does not itself prove live IAM, role, credential, database, deployment, or data mutation.

## DP-SD-019 bootstrap/routine delivery correction

**Reproduced failure.** At source base `d07ea4f3f3b6b0bcb5d66cbd7c1d5f67784d658f`,
`.github/workflows/deploy.yml` assigned `environment:
data-plane-production-cutover` to the always-run `migrate` job. GitHub evaluates
job environment protection before its steps, so a deployment against an already
`marked` database still requested the one-time independent bootstrap approval and
made protected DBA/migrator secrets part of the ordinary job's credential surface.
This blocked the routine no-new-migration path and every dependent web, MCP and
pipeline-image release; it did not add safety after semantic cutover acceptance.

**Smallest correction and finite source manifest.** This packet changes exactly:

- `.github/workflows/deploy.yml`;
- `platform/tests/unit/data_plane_security_contract.test.ts`;
- `platform/tests/unit/nirmana_evidence_ownership_deploy.test.ts`; and
- this cutover record.

No migration, role definition, lifecycle API, writer, orchestrator, producer
semantics, asset registry or pin is changed. The database principals remain exactly
the eight entries in **Principals and exact authority** below. The workflow has three
database jobs with a finite contract:

1. `migration-state` has no environment and receives only the ordinary
   `PROD_DATABASE_URL`. It reads the data-plane and Nirmana semantic status
   functions and emits only `marked` or `unmarked`; a missing secret, command
   failure or any other value fails the workflow.
2. `privileged-bootstrap` is the sole job bound to
   `data-plane-production-cutover`. It is created only when either inspected
   state is `unmarked`; it alone may receive the existing backup/isolated-restore
   receipt, cutover lease, DBA, data-plane migrator, Nirmana legacy-owner and
   Nirmana migrator secrets. Inside the cross-ref exclusive concurrency lock it
   re-reads both semantic states. A stale `unmarked -> marked` observation skips
   the already-completed operation; `marked -> unmarked`, unknown state, failed
   cutover or failed re-attestation fails closed. The existing exact-source GitHub
   deployment-review check, backup/restore binding, PostgreSQL advisory lease,
   quiescence locks, atomic migrations and rollback/canary controls are unchanged.
3. `migrate` has no environment and no bootstrap-only secret. It shares the exact
   `data-plane-production-cutover` concurrency group (without acquiring its
   environment) so routine migrations serialize across refs with bootstrap and
   with each other. It runs only after an intentional both-marked bootstrap skip
   or a successful required bootstrap, re-attests both states as `marked` using
   the ordinary credential, repeats IAM/runtime isolation attestation, and then
   invokes the general runner. Web, MCP and pipeline-image delivery retain
   `needs: [migrate]`; an unknown/partial/failed state cannot reach them.

The general runner remains unconditional and idempotent, so no-new-migration and
ordinary L3 code releases take the routine path without bootstrap approval. Its
existing protected-filename guard still rejects pending 1035/1036 application by
the ordinary credential. Workflow-level concurrency remains unchanged and the
shared job group closes the cross-ref concurrent-deployment race. Nirmana's
unrelated one-shot ownership transfer remains inside the privileged job rather
than being weakened into routine delivery.

**Affected frontier and exit condition.** This source correction unlocks only the
shared W1 release barrier and the first L3 frontier that depends on web/MCP/build
delivery (resonance, Yojaka, Avadhi, qualified overlays and applicable Kshetra
S0/S2/service proofs). It does not accept any asset, physical generation,
deployment or consumer value. Source exit requires parsed-workflow state-matrix
tests for marked, unmarked, unknown, pending, failed, stale and concurrent cases;
the existing security/Nirmana contract suites; YAML and `actionlint`; TypeScript;
and independent exact-tip review. Operational exit still requires the external
prerequisites below, a protected merge, authenticated bootstrap approval, accepted
isolated restore and cutover, marked-state routine deployment, governed canary and
independent physical W1 acceptance.

**Workflow rollback.** Before cutover, revert this four-file packet to restore the
prior single-job topology; no database rollback is involved. After cutover, do
not restore the approval-on-every-deploy topology as a substitute for data-plane
rollback. Keep the database marked and restricted, pause dependent delivery, use
the migrator-only generation rollback and prior serving/job revisions described
below, and repair the routine gate through a new protected change.

## Observed live state (read-only, 2026-09-15)

- Cloud SQL `madhav-astrology:asia-south1:amjis-postgres` is PostgreSQL 15 and RUNNABLE. Direct application login is `amjis_app`; database owner is `cloudsqlsuperuser`; `amjis_app` owns `public` and the current producer objects.
- `_migrations_applied` has no row for 1035 or 1036, and neither history root exists. The exact candidates are unapplied; no forward migration number is required.
- No `data_plane_*` role or GitHub data-plane secret exists. Required role names have no collision.
- `amjis-web` and `brahma-build-pipeline-job` both currently execute as `amjis-web-runtime@...`; the job reads `amjis-pipeline-db-url`.
- Project IAM grants `roles/secretmanager.secretAccessor` broadly to web, MCP, sidecar, default-compute, conductor, and swarm identities. Therefore a new project secret is exposed to serving identities even if it also has a narrow resource policy. This is a blocking cutover precondition.
- `amjis-builder-runtime@...` is rejected for this boundary: its project-level `roles/run.admin`, Artifact Registry writer power, existing bootstrap-job attachment, and separate WIF trust make it an administrative/deployment identity, not an untrusted producer.
- Existing local MCP PostgreSQL launch processes expose the shared `amjis_app` URL in argv. The value was not inspected or reproduced. This is pre-existing, outside the new data-plane credential scope; rotate the shared credential and remove argv transport in a separate packet.

## Principals and exact authority

| Principal | Login | Membership | Authority |
|---|---:|---|---|
| `data_plane_schema_owner` | no | migrator only | owns `public`; no database `CREATE`; grants schema `CREATE` only to protected layer owners |
| `data_plane_l1_owner` | no | migrator only | owns L1 active tables, owned sequences, 1035 history/views/functions/triggers |
| `data_plane_l2_owner` | no | migrator only | owns L2 active tables, owned sequences, 1036 history/views/functions/triggers; read/row-lock on L1 head for exact input pinning |
| `data_plane_migrator` | yes, NOINHERIT | three protected owners | deployment-only; ledger insert/select and lifecycle rollback; never Cloud Run-mounted |
| `data_plane_builder` | yes, NOINHERIT | none | exact producer DML; lifecycle open/bind/capture/complete/select; no schema create, owner membership, TRUNCATE, TRIGGER, REFERENCES, history mutation, or rollback |
| `data_plane_verifier` | yes, NOINHERIT | none | SELECT and generation-selection functions only |
| `amjis_app` | yes | no protected owner | serving SELECT only on protected producer/history surfaces; no protected writes or schema create |
| `role_orchestrator` | no | no protected owner | no protected table/function privilege |

Every login is required to be non-superuser, non-CREATEROLE, non-CREATEDB, non-replication, and non-BYPASSRLS. The owner roles are additionally NOLOGIN. The preflight temporarily grants only the memberships and database `CREATE` needed for the legacy-owner transfer inside one transaction, then revokes them before commit.

## Protected object map

L1 active tables: `chart_facts`, `chart_dashas`, `chart_divisionals`, `ga_condition_composite`, `ga_yoga_firings`, `chart_vichara`, `ga_transit_anchors`, `l1_tajik_varsha_year_lords`, `ga_medical`, `ga_vastu_planet_direction_map`, `ga_prashna_lagna`, `ga_prashna_judgment`.

L2 active tables: `bodha_msr_signals`, `bodha_cgm_nodes`, `bodha_cgm_edges`, `bodha_contradictions`, `bodha_cgm_paths`, `bodha_cgm_motifs`, `bodha_cgm_sub_graphs`, `bodha_cgm_chart_topology_summary`, `bodha_mechanisms`, `bodha_cdlm_cells`, `bodha_convergence`, `bodha_triangulation`, `bodha_cdlm_chart_summary`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_pattern_clusters`, `bodha_pratijna`, `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_chart_summary`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies`, `bodha_signal_embeddings`, `bodha_discoveries`, `bodha_anomalies`, `bodha_question_lenses`, `bodha_chart_gestalt`, `synthesis_quality_scorecard`, `bodha_grounding_matches`.

Owned sequences are discovered only through PostgreSQL `OWNED BY` dependencies of those exact relations and follow the table owner. Existing active-table RLS policies are captured exactly (name, command, permissiveness, role OIDs and normalized USING/WITH CHECK expressions) under the protected owner; any addition, removal or drift is deployment-blocking. The `l1_data_plane_capture` and `l2_data_plane_capture` triggers remain enabled and their functions, immutable-history triggers, history tables, heads, current views, selection functions, and rollback functions are created under their layer owner.

Lifecycle entry points are `SECURITY DEFINER`, schema-qualified, and pin `search_path = pg_catalog, public, pg_temp`. A BEFORE INSERT/UPDATE/DELETE guard is installed on every listed active table and requires direct `session_user = data_plane_builder`, matching transaction-local chart/asset/generation/partition/contract/build context, an active `build_runs`/`build_run_assets` tuple, and an exact table-to-asset mapping. Capture has no legacy fall-through and records both inserts and updates. Shared `chart_facts` deletion requires `authorize_l1_chart_facts_delete`, whose protected-owner temporary receipt contains the exact fact IDs selected by chart/category/ayanamsha scope. MSR parent and child deletion similarly requires a protected-owner temporary receipt containing the exact locked signal IDs returned by `assert_l2_msr_delete_safe`. Other one-asset-per-table delete predicates retain their existing SQL but every affected row is checked against the admitted chart and asset. No `WriterBase` or producer semantics were changed.

L2 binding locks every selected upstream head, builds an empty-or-populated temporary relation for every protected manifest table, and writes a temporary receipt owned by `data_plane_l2_owner`. Open rejects an absent, caller-owned, stale or vector-mismatched receipt and atomically persists the receipt with the run intent. Completion compares caller counts with distinct captured protected rows, rejects discrepancies, and permits zero only when the registry explicitly declares `target_floor = 0`; a digest cannot manufacture an empty head. Rollback requires direct `data_plane_migrator`. Callers cannot write heads, generations, snapshots, bind receipts or terminal state directly.

The semantic status gate is bound to the exact migration filename, SHA-256 and normalized `sql_identity`, rejecting null, missing, duplicate or mismatched rows. It recursively traverses role membership, compares exact schema/table/sequence/function EXECUTE allowlists, verifies function signatures through protected definition digests, checks trigger function OIDs/event/timing bits, rejects policies and unknown grantees, and attests views and default privileges.

## External GitHub environment prerequisite — DP-SD-020 replacement

DP-SD-020 supersedes only the former human/separate-reviewer dependency. Before
a cutover run is dispatched, repository administrators must provision the
`data-plane-production-cutover` environment with no `required_reviewers` rule
and a deployment branch policy of
`protected_branches=true, custom_branch_policies=false`. The workflow token must
retain `actions:read` so the job can authenticate both
`GET /repos/{owner}/{repo}/environments/data-plane-production-cutover` and
`GET /repos/{owner}/{repo}/actions/runs/{run_id}`. An environment name alone is
not protection evidence: absent/unreadable policy, a human-review dependency,
an unprotected branch policy, or a mismatch to the exact run/repository/SHA all
fail closed.

The backup receipt is prepared for the queued run and records the exact
`repository`, `workflowRunId`, `environment`,
`authorityDecision="DP-SD-020"`, and
`executionMode="native_authorized_automated_cutover"`. At execution, the source
authenticates the GitHub environment and workflow run and binds those values to
the immutable deploy SHA and cutover lease. Neither a free-form approver nor a
human approval-history surrogate is accepted. All other security, isolation,
backup, restore, lease, quiescence, rollback and postflight controls remain
unchanged.

## Mandatory IAM transition before first cutover

1. Inventory the exact secrets on the current revisions/jobs. Observed inventory:
   - web: `DEEPSEEK_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, `NVIDIA_NIM_API_KEY`, `PYTHON_SIDECAR_API_KEY`, `SUPER_ADMIN_EMAIL`, `amjis-db-password`, `firebase-admin-credentials`, `mcp-canary-key`, `mcp-internal-token`, `mcpt-scheduler-secret`, `nirmana-campaign-control-db-password`, `nirmana-evidence-ingress-db-password`, `openai-api-key`;
   - MCP: `PYTHON_SIDECAR_API_KEY`, `mcp-canary-key`, `mcp-internal-token`;
   - sidecar: `GOOGLE_GENERATIVE_AI_API_KEY`, `PYTHON_SIDECAR_API_KEY`, `amjis-pipeline-db-url`;
   - current build job: `amjis-pipeline-db-url`.
2. Grant each current runtime identity resource-level accessor on only the exact inventory above, then canary the unchanged web/MCP/sidecar revisions and one non-mutating build-job probe. Retain the previous policies and revisions as rollback material.
3. During the exclusive maintenance window, remove these exact six project-wide grants, in this order, and verify after each removal:
   1. `serviceAccount:938361928218-compute@developer.gserviceaccount.com`
   2. `serviceAccount:amjis-mcp-runtime@madhav-astrology.iam.gserviceaccount.com`
   3. `serviceAccount:amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com`
   4. `serviceAccount:amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com`
   5. `serviceAccount:brahma-conductor-bot@madhav-astrology.iam.gserviceaccount.com`
   6. `serviceAccount:brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com`

   Each operation is `gcloud projects remove-iam-policy-binding madhav-astrology --role=roles/secretmanager.secretAccessor --member=<exact-member>`. Re-read the policy and halt unless the project-level accessor member set is empty. Also halt on any folder/organization accessor grant; do not compensate with a condition.
4. Only after step 3 is proven, create `data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com` and the `data-plane-builder-db-url` secret. The builder receives exactly `roles/cloudsql.client` on project `madhav-astrology`, `roles/pubsub.publisher` on topic `cockpit-events`, and no other project/topic role. Set the builder service-account IAM policy to exactly one unconditional `roles/iam.serviceAccountUser` member: `serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com`.
5. Provision `data_plane_builder`, `data_plane_verifier`, and `data_plane_migrator` database logins through the approved secret channel. Add the builder URL as a new secret version through stdin; never place it in argv or a file retained after the window. Set the `data-plane-builder-db-url` resource IAM policy—not an additive project grant—to exactly one unconditional binding: `roles/secretmanager.secretAccessor` for `serviceAccount:data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com`. Re-read the complete policy and require byte-for-byte principal/role/condition equality.
6. Store DBA and migrator URLs only as protected GitHub environment secrets; never argv, image, log, artifact, service, job, web, build-image step, or MCP configuration. Prepare the isolated restore and exact cutover receipt before approving the queued environment deployment.
7. Rebind only `brahma-build-pipeline-job` in `asia-south1` using `--service-account=data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com --set-secrets=DATABASE_URL=data-plane-builder-db-url:latest`. Read every service, revision and job in every region and require exactly one conforming named job, with no other builder identity/secret reference or literal credential scalar.
8. Run the fail-closed IAM preflight before the DBA URL or migrator URL is used. It aggregates conditional bindings across project/folder/organization, resolves predefined/basic/custom permissions with their exact parent, checks builder impersonation, and verifies the full Cloud Run inventory. Then execute one governed canary covering open, bind, populate, capture, complete, replay, select and rollback; independently verify negatives before dispatch resumes.

These are future operator actions. This source lane performed only the read-only
inventory needed to name the six existing grants and did not mutate IAM, secrets,
Cloud Run, or a live database.

## Database cutover and attestation

1. Take a fresh Cloud SQL backup and restore that exact backup only to a distinct isolated validation instance—never over production. Read-attest PostgreSQL 15, the expected schema identity, and unmarked pre-cutover state on that instance. Record one exact JSON receipt containing `authorityDecision`, `backupId`, `environment`, `executionMode`, `expiresAt`, `leaseId`, `repository`, `restoreOperationId`, `sourceCommit`, `validationInstance`, and `workflowRunId`; it expires within 48 hours and is accepted only for the matching immutable deploy commit, unique lease, exact DP-SD-020 automated-authority binding, authenticated GitHub environment/workflow run, and validation instance. Start the authenticated Cloud SQL Auth Proxy for the API-verified `project:region:validationInstance` connection name on the dedicated loopback validation port. The validation database URL must address that loopback port exactly; a separately supplied URL/instance string is rejected. Pause build dispatch; serving reads continue.
2. Run `data-plane-protected-cutover.ts` once. It holds the exclusive PostgreSQL advisory transaction lease plus `SHARE ROW EXCLUSIVE` locks on `build_runs` and `build_run_assets` while proving build-run quiescence, running `data-plane-ownership-preflight.ts` as direct `postgres`, running `data-plane-migration-attestation.ts` as direct `data_plane_migrator`, and earning semantic `marked` status before releasing the lease. The table locks prevent a new build from entering after the zero-active-build observation. The ownership preflight checks normalized pre-created logins and `pgcrypto`, creates the three NOLOGIN owners, performs the exact `bo_samvada` legacy-owner row transition, transfers schema/tables/sequences, closes default PUBLIC execution/type grants, and installs explicit ACLs atomically.
3. The migration attestation applies stripped 1035 and 1036 bodies under `SET LOCAL ROLE` to their exact owners and inserts both ledger rows in the same transaction. Either both migrations and both markers commit or none do.
4. Run semantic status attestation before any general migration or deploy dependency can complete. A ledger row alone is insufficient: exact identities, recursive memberships, owners, ACLs, definition digests, triggers, views, policies, sequences, schemas, defaults and negative privileges must converge.
5. Run the general migration runner. It may verify already-recorded 1035/1036 hashes but throws if either protected file is pending, preventing `PROD_DATABASE_URL`/`amjis_app` creation.
6. Update `brahma-build-pipeline-job` to the dedicated SA and exact builder secret. Execute one governed canary covering open, bind, populate, capture, complete, replay, select and rollback; independently verify negative operations and failure atomicity before resuming dispatch.

## Rollback

- Before database mutation: restore the saved per-secret policies and previous service/job revisions if a canary fails. Do not create or bind the data-plane secret while project-wide accessor exists.
- After owner transfer but before migration commit: the preflight/attestation transactions roll back automatically. Re-run only after semantic inspection; never hand-edit the marker.
- After successful migration: do not return protected ownership or the builder credential to `amjis_app`. Pause dispatch, revert the build job to its prior image while keeping the dedicated restricted SA/credential, and use the migrator-only generation rollback functions to select a prior complete generation. Restore the database backup only for unrecoverable structural failure under separate destructive authorization.
- IAM rollback may restore the recorded resource-level policies. It must not restore project-wide Secret Manager access. If current-runtime secret grants were missed, add the exact missing resource grant and canary again.

## Residual release gates

- Live IAM transition, secret/role provisioning, backup, maintenance window, and canary execution remain operator actions; none were performed by this source-design lane.
- Verify that the existing `PROD_DATABASE_URL` Actions secret is available to
  non-environment jobs before integration. The state and routine jobs fail closed
  when it is absent; this packet does not copy or widen any secret.
- Rotate the pre-existing shared `amjis_app` credential and replace MCP argv URL transport in a separate governed change.
- Provision and API-verify the GitHub environment protection described above; the current source cannot be released while that external prerequisite is absent. Remove the DBA secret after durable marked status.

## Bounded writer compatibility authority delta

The independent security rejection authorized only individual L1/L2 mutation call sites needed for scoped lifecycle compatibility and expressly prohibited `WriterBase` changes. Inventory covered `ga_writers/_idempotency.py`, `bodha_writers/_idempotency.py`, the direct L1 delete writers (`ga_dashas`, `ga_prashna`, `ga_medical`, `ga_yoga`, `ga_vastu`, `ga_transit_anchors`, `ga_vargas`, `ga_vichara`, `ga_condition`, heavy-writer wrapper and dispatcher), and direct L2 delete writers (`bo_chart_gestalt`, `bo_sangati`, `bo_cdlm_summary`, `bo_upaya`, `bo_pratijna`, `bo_cgm_motifs`, `bo_drishti`, `bo_yantra_mechanism`, `bo_cgm_paths`, `bo_anveshana`). Only the shared-table L1 call sites (`ga_writers/_idempotency.py`, `ga_dashas_writer.py`, `ga_condition_writer.py`, `pipeline/dispatcher.py`) required an explicit scope-receipt call; all one-asset-per-table predicates are already safely constrained by the row-level guard. The MSR helpers retain their existing lifecycle assertion, upgraded to an exact owner-held signal receipt.
