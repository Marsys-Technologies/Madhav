# MADHAV Data Plane RI-02 Security Cutover v1.1

**Authority:** DP-SD-018 §§5–6 source design. This artifact does not authorize live IAM, role, credential, database, deployment, or data mutation.

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

## Mandatory IAM transition before first cutover

1. Inventory the exact secrets on the current revisions/jobs. Observed inventory:
   - web: `DEEPSEEK_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, `NVIDIA_NIM_API_KEY`, `PYTHON_SIDECAR_API_KEY`, `SUPER_ADMIN_EMAIL`, `amjis-db-password`, `firebase-admin-credentials`, `mcp-canary-key`, `mcp-internal-token`, `mcpt-scheduler-secret`, `nirmana-campaign-control-db-password`, `nirmana-evidence-ingress-db-password`, `openai-api-key`;
   - MCP: `PYTHON_SIDECAR_API_KEY`, `mcp-canary-key`, `mcp-internal-token`;
   - sidecar: `GOOGLE_GENERATIVE_AI_API_KEY`, `PYTHON_SIDECAR_API_KEY`, `amjis-pipeline-db-url`;
   - current build job: `amjis-pipeline-db-url`.
2. Grant each runtime service account `roles/secretmanager.secretAccessor` on only its exact current secret resources. Do not create a data-plane secret yet.
3. Deploy/canary the unchanged revisions and one non-mutating job probe; retain the previous revision and policies as rollback material.
4. Remove every project-level `roles/secretmanager.secretAccessor` binding. Re-run canaries and prove unrelated identities cannot access each sampled secret.
5. Create dedicated `data-plane-builder-runtime@...` with only `roles/cloudsql.client` at project scope and `roles/pubsub.publisher` on `cockpit-events`. Grant it accessor only on new `data-plane-builder-db-url`; grant no Run Admin, Artifact Registry writer, token-creator, owner/editor, or project-wide secret role.
6. Provision `data_plane_builder`, `data_plane_verifier`, and `data_plane_migrator` database logins through the approved secret channel. Store builder URL only in the exact Secret Manager secret. Store DBA and migrator URLs only as protected GitHub deployment secrets; never argv, image, log, artifact, service, job, web, build-image step, or MCP configuration.
7. The workflow IAM preflight must pass before the DBA URL or migrator URL is read. It aggregates conditional bindings, queries effective IAM through Cloud Asset Inventory, rejects ancestor/project aggregate secret access, checks the builder SA impersonation policy, inventories every Cloud Run revision and job, permits the builder secret only on `brahma-build-pipeline-job`, and forbids DBA/migrator material everywhere.

## Database cutover and attestation

1. Take a Cloud SQL backup, successfully restore-test that exact backup, and record the immutable `backup-id:restore-operation-id` receipt, protected object owners/ACLs, active build count, and migration-ledger digests. Pause build dispatch; serving reads continue. The `data-plane-production-cutover` GitHub environment must require an independent reviewer, issue a unique UUID cutover lease, and hold the one-shot DBA/migrator/backup evidence secrets. The deploying actor and recorded approver must differ.
2. Run `data-plane-protected-cutover.ts` once. It holds the exclusive PostgreSQL advisory transaction lease while proving build-run quiescence, running `data-plane-ownership-preflight.ts` as direct `postgres`, running `data-plane-migration-attestation.ts` as direct `data_plane_migrator`, and earning semantic `marked` status before releasing the lease. The ownership preflight checks normalized pre-created logins and `pgcrypto`, creates the three NOLOGIN owners, performs the exact `bo_samvada` legacy-owner row transition, transfers schema/tables/sequences, closes default PUBLIC execution/type grants, and installs explicit ACLs atomically.
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
- Rotate the pre-existing shared `amjis_app` credential and replace MCP argv URL transport in a separate governed change.
- Verify GitHub environment protection restricts the one-shot DBA and migrator secrets, then remove the DBA secret after durable marked status.

## Bounded writer compatibility authority delta

The independent security rejection authorized only individual L1/L2 mutation call sites needed for scoped lifecycle compatibility and expressly prohibited `WriterBase` changes. Inventory covered `ga_writers/_idempotency.py`, `bodha_writers/_idempotency.py`, the direct L1 delete writers (`ga_dashas`, `ga_prashna`, `ga_medical`, `ga_yoga`, `ga_vastu`, `ga_transit_anchors`, `ga_vargas`, `ga_vichara`, `ga_condition`, heavy-writer wrapper and dispatcher), and direct L2 delete writers (`bo_chart_gestalt`, `bo_sangati`, `bo_cdlm_summary`, `bo_upaya`, `bo_pratijna`, `bo_cgm_motifs`, `bo_drishti`, `bo_yantra_mechanism`, `bo_cgm_paths`, `bo_anveshana`). Only the shared-table L1 call sites (`ga_writers/_idempotency.py`, `ga_dashas_writer.py`, `ga_condition_writer.py`, `pipeline/dispatcher.py`) required an explicit scope-receipt call; all one-asset-per-table predicates are already safely constrained by the row-level guard. The MSR helpers retain their existing lifecycle assertion, upgraded to an exact owner-held signal receipt.
