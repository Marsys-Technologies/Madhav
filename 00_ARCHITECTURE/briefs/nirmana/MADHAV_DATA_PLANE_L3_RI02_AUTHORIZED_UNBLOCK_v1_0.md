---
artifact: MADHAV_DATA_PLANE_L3_RI02_AUTHORIZED_UNBLOCK
version: "1.0"
status: ACTIVE_SOURCE_DESIGN
strategy_decision: DP-SD-018
parent_decision: DP-SD-017
campaign_id: madhav-data-plane-l3-kala
packet_id: L3-RI-02-AUTHORIZED-UNBLOCK
opened_on: 2026-09-15
owner_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
integration_branch: codex/madhav-data-plane-execution
integration_checkpoint: 5142109f7f219ea860f859e322646f79d875bee8
coordination_lease: MADHAV-DATA-PLANE-L3-RI02-20260915
coordination_pin: 7eec8577e40778c72c8fdc17c5792646eee791c4
delivery_claim: NONE
---

# L3-RI-02 authorized unblock

## 1. Immutable authority and continuing goal

This packet consumes the immutable DP-SD-018 amendment at content commit
`6b6ce9c06ce54fb7c474d97c70257a505bf2ed84` and approval commit
`7f21f27b14a7909424591a530096dc2f5d6e2b13`, alongside the unchanged DP-SD-017
parent content `793972c754b106688097dbc54536c1a9c270a793` and approval
`04a9ab33effa23e5e9b4e89772330ae264498a9b`.

The existing full L3 goal remains the objective. Its product control plane still
reports `blocked`; this owner-authorized resumption is treated as a fresh blocker
audit and does not convert the goal to complete or replace it with a producer-only
goal. Source acceptance, protected integration, deployed state, physical data,
consumer value and empirical evidence remain distinct.

The 22 active L3 identities and protected retired `ka_gochara_sweep` denominator
are unchanged. L4/L5 elevation and empirical predictive-performance work remain
outside scope.

## 2. Resumption reconciliation

| Surface | Fresh observation | Disposition |
|---|---|---|
| Execution worktree | Clean at `5142109f7f219ea860f859e322646f79d875bee8` on `codex/madhav-data-plane-execution` | Preserved; no reset, move or recreation. |
| Protected main | `origin/main@731e311f0b8f5f84db2f152b93951e1d3d50d89a` after fetch | Candidate remains unreleased. |
| Execution PR | No open PR for the execution branch | No PR/deploy inference. |
| Existing heartbeat | `l3-k-la-execution-recovery`, ACTIVE, 15-minute task heartbeat | Updated in place for DP-SD-018/RI-02; no duplicate. |
| Pūrṇa recovery | `MADHAV-PURNA-ANVESANA-W7-20260915` ACTIVE through 23:30 IST; source-local ceiling; explicitly excludes migrations 1035/1036 | Preserved as a foreign active owner. |
| Prior Data Plane leases | W0 expired after accepted source work; RI-01 expired at 11:30 IST | Closed/superseded on the live coordination branch. |
| Current RI-02 lease | `MADHAV-DATA-PLANE-L3-RI02-20260915`, remote pin `7eec8577e40778c72c8fdc17c5792646eee791c4`, through 18:00 IST | Source/local/disposable work only; not a production lock. |
| Session handshake | `verification_artifacts/madhav_data_plane_l3_ri02_session_open.yaml` | Validator: 0 violations. |
| Local DB credentials | `DATABASE_URL` and `DBURL` absent | No local live-DB claim. |
| Cloud target | Project `madhav-astrology`; Cloud SQL `amjis-postgres`; region `asia-south1`; PostgreSQL 15; RUNNABLE | Matches DP-SD-018 target, but no write was made. |
| Current database users | `amjis_app`, existing Nirmāṇa control/evidence/migrator principals, `postgres`, `retrieval_census_ro` | No dedicated Data Plane owner/migrator/builder principal yet observed. |
| GitHub secret names | Existing general and Nirmāṇa URL secrets only; no dedicated Data Plane secret observed | Values not read or exposed. |
| Serving web | `amjis-web-02258-jj2`, 100%, image commit `731e311f0b8f5f84db2f152b93951e1d3d50d89a` | Current protected main is served; L3 source is not deployed. |
| Build job | `brahma-build-pipeline-job` runs as `amjis-web-runtime@...` with `amjis-pipeline-db-url`; image commit `c558e60d3267ded79d65fd25f50ee926ce27b75a` | Existing builder credential/identity is not the required Data Plane non-owner proof. |
| Migration namespace | Protected main ends at 1032; Pūrṇa owns 1033/1034 in stacked source branches; Data Plane owns 1035/1036 candidates | Recheck live application and open-PR identities before any release. |

Injected execution policy at resumption is `danger-full-access` with approval
policy `never`; this is runtime capability, not evidence that repository, cloud or
database gates have passed.

## 3. Frozen packet manifest and ownership

| Lane | Writer ownership | Allowed outputs | Explicit exclusions | Terminal source/design gate |
|---|---|---|---|---|
| P — provenance | `/root/ri02_provenance`; branch `codex/data-plane-ri02-provenance`; worktree `/tmp/madhav-ri02-provenance.HlOca6` | Generated writer/layer pins; versioned successor receipt generator/runtime representation and exact tests; Lane-P evidence | No writer behavior, migrations, deploy workflow, runtime bindings, L4 behavior, L5, retired sweep, Pūrṇa, execution ledger | Exact delta classification, historical reconstruction, rejection tests, unaffected-layer identity and independent exact-tip review. |
| S — security/DBA/release design | `/root/ri02_security`; branch `codex/data-plane-ri02-security`; worktree `/tmp/madhav-ri02-security.Ho9lQ5` | Exact 1035/1036 or forward candidates as application state requires; protected-owner lifecycle APIs; role-realistic disposable tests; scoped deploy/preflight/attestation and cutover evidence; bounded individual L1/L2 writer call-site adaptation required to use those lifecycle APIs | No provenance generated files, `WriterBase`, broader producer semantics, live role/secret/IAM/DB/deploy mutation, L4/L5, retired sweep, Pūrṇa, execution ledger | Disposable restricted-login positive/negative proof, exact role/object/cutover matrix and independent security/migration review. |
| Root — conductor/integrator | Existing execution task/worktree only | Coordination row, session handshake, this packet, execution ledger, serialized later integration | No self-certification; no foreign worktree/branch; no production action under RI-02 source-design lease | Both lane tips independently accepted; exact reviewed release candidate frozen. |

No worker may certify its own terminal claim. Generated files and shared release
paths have one serialized integrator. A later protected release/cutover receives
its own fresh exclusive lease and live collision check.

## 4. Immediate executable actions

1. Lane P recomputes and adjudicates L0/L1/L2 and metadata-only L4 provenance,
   preserving old bytes and original-tree reconstruction.
2. Lane S proves migration application state, maps exact objects/principals and
   implements the protected lifecycle boundary plus role-realistic disposable
   tests and release adapters.
3. Root reconciles each clean committed tip, dispatches independent reviewers,
   applies bounded corrections, and freezes one exact release candidate.
4. Only after both design exits pass may the conductor claim a separate exclusive
   cutover lease, push/open a focused protected PR and advance through normal
   checks, merge, deployment, attested SQL/role/secret cutover and independent
   production verification.
5. Physical W1 and L3 W2-W8 remain automatically sequenced after genuine RI-02
   release/cutover acceptance; no upstream row or source pass is grandfathered as
   current physical evidence.

## 5. Current non-claims

This packet has not created database roles, credentials, secret versions or IAM
bindings; has not applied a migration, opened a PR, deployed, built/rebuilt chart
data, selected a generation, integrated a consumer, evaluated value or accepted
the layer. The exact next gate is the independently accepted P + S source/design
candidate.

## 6. Bounded technical rulings

### RI02-R-001 — admit the derived `ka_sangam` provenance successor

- **Question:** truthful regeneration at checkpoint `5142109f7` reports a stale
  checked-in `ka_sangam` digest because an already accepted W2 shared import
  changed its import closure. Excluding that shared source would conflict with
  the accepted W2 packet; retaining the stale generated value would make the
  inventory checker dishonest.
- **Decision:** Lane P may add an L3 metadata-only, versioned successor binding
  for exactly `ka_sangam` alongside the affected L0/L1/L2/L4 provenance set.
  This is a derived/import-closure consequence of accepted L3 source, not new
  writer behavior or a reopening of W2.
- **Evidence required:** preserve the original L3 receipt/pin bytes and W2
  acceptance, name the exact old/new digest and accepted source closure, reject
  any other unapproved L3 identity/source delta, and prove historical
  reconstruction plus current generated consistency.
- **Reversibility and non-claims:** removing the new successor restores the old
  metadata view without changing source behavior or history. It grants no
  physical-data, deployment, freeze, consumer-value or empirical status.

### RI02-R-002 — fail closed on inherited secret reachability

- **Question:** the current build job runs as the web runtime identity, and live
  project IAM grants broad Secret Manager access to serving/runtime identities.
  A new Data Plane secret in the same project would therefore be reachable even
  without an explicit resource grant.
- **Decision:** Lane S must treat this topology as a failed cutover precondition.
  The design must first preserve each runtime's existing secret dependencies by
  exact resource grants, verify a canary and rollback, then remove inherited
  project-wide secret access from every runtime that must not reach Data Plane
  credentials. The deployment-only migrator remains CI-only and is never mounted
  in Cloud Run. The builder uses an independently isolated runtime identity;
  reuse an existing identity only if its effective privileges satisfy the exact
  matrix, otherwise specify the smallest dedicated identity.
- **Evidence required:** effective-access negatives for web, MCP, sidecar and all
  unrelated runtimes; positive access only for the mapped job/secret pair; exact
  old/new IAM and secret-binding snapshots; ordinary-serving canary; reversible
  rollback. Removing broad access is not proof until fresh credentials and live
  bindings are independently tested.
- **Scope:** source/design/disposable proof now; no IAM, secret, role, deployment
  or database mutation under the current RI-02 source-design fence.

### RI02-R-003 — require lifecycle enforcement at every protected mutation

- **Question:** independent security review of Lane-S candidate `70417f577` used
  restricted PostgreSQL logins to bypass the proposed lifecycle boundary through
  direct active-table DML. Existing individual writers issue direct deletion or
  replacement statements, so revoking those grants without adapting call sites
  would either retain the bypass or break the producer path.
- **Decision:** Lane S may adapt only the individual L1/L2 writer SQL call sites
  required to invoke scoped lifecycle mutation/deletion APIs. `WriterBase` and
  producer semantics remain outside the expansion. Every protected table and
  mutation event must be inventoried and exercised under restricted logins.
- **Evidence required:** direct builder DML is denied outside admitted context;
  captured rows determine published counts; exact-input binding is mandatory;
  complete ACL, recursive membership, function/trigger definition, IAM,
  deployment-order and migration-identity checks fail closed; the original
  writer outcomes remain covered by focused compatibility tests.
- **Non-claims:** this is a source compatibility correction, not live role,
  credential, IAM, migration, build or deployment authority.

## 7. Source/design gate status

Lane P is independently accepted at exact branch tip
`8ebb3737cedfd4fde802f30845d94f8e8a641c33` and integrated serially as
`1b429bd18`, `350582ca6`, `540ad88d4` and `7b1576d59`. Its 12 Python tests,
13 receipt tests, generator drift check and provenance inventory check pass in
the integration worktree. The accepted proof binds real commits, exact
content-addressed decisions, the complete active/non-writer/retired identity
sets and a recursively validated linear successor history.

Lane S candidate `70417f577bc3d6a02cfc3fb8c6381a9f8fcbcaf9` is rejected by
independent adversarial review. Restricted-login PostgreSQL probes reproduced
direct-DML lifecycle bypass, fabricated/empty generation publication and
semantic-status false-green paths. Source review also found fail-open secret
isolation, unsafe deployment ordering and incomplete migration identity
attestation. Correction under RI02-R-003 is active. Therefore both-lane source
acceptance, release-candidate freeze and production cutover remain ineligible.
