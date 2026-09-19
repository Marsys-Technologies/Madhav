---
artifact: MADHAV_DATA_PLANE_L3_UNBLOCK_AND_RESUME_AMENDMENT
version: "1.0"
status: APPROVED_FOR_EXECUTION
approved_on: 2026-09-15
strategy_decision: DP-SD-018
native_authority: >
  Make an autonomously executable plan to unblock the current block and give
  all authorizations for this to complete autonomously as it was being executed
  to the full completion. Send this instruction to the Execution - Data Plane
  so it can resume the work.
parent_decision: DP-SD-017
parent_content_commit: 793972c754b106688097dbc54536c1a9c270a793
parent_approval_commit: 04a9ab33effa23e5e9b4e89772330ae264498a9b
parent_brief: MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md
parent_strategy: MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md
strategic_task: "Strategy — Data Plane / 01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
execution_branch: codex/madhav-data-plane-execution
execution_worktree: /Users/Dev/.codex/worktrees/c9bd/Madhav
execution_checkpoint_observed: 5142109f7f219ea860f859e322646f79d875bee8
reviewed_w2_source: 47131772b355ae2c67b1f6fb2b90e9fa007e2202
reviewed_ri01_source: 6a7ecc17117163debcc4b742aa183f17588ef621
protected_main_observed: 731e311f0b8f5f84db2f152b93951e1d3d50d89a
observed_on: 2026-09-15
goal_policy: "Continue the existing full L3 goal; this is an authority and prerequisite amendment, not a replacement producer-only goal. No token budget."
delivery_target: "LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED"
next_stage_hold: "L4/L5 elevation and empirical predictive-performance work remain outside scope."
changelog:
  - "1.0: Native-authorized two-blocker remediation, narrow provenance and DBA/deployment authority, non-circular protected delivery, and automatic continuation to the full DP-SD-017 L3 outcome."
---

# L3 unblock and autonomous resumption — DP-SD-018

## 1. Decision and precedence

The native authorizes execution, not another proposal-only audit. The existing
Execution — Data Plane conductor is delegated the acting provenance-adjudication,
DBA, release and technical-surrogate duties described below, using independently
owned implementation and verification roles. It must resolve the two current
blockers and continue the remaining approved L3 campaign without another routine
human approval at each packet, role provision, PR, deployment or DAG wave.

This is a narrow, explicit exception to DP-SD-017's prohibition on credential,
identity/IAM/infrastructure operations and its reservation of non-L3 provenance
approval, and to the matching credential prohibition in autonomy CHARTER v2.0.
It applies only to the described data-plane cutover in the existing authorized
Madhav environment. It does not amend those documents globally. Keep the original
approved brief and historical receipts immutable; consume this amendment alongside
their exact content/approval pins. Contrary older RI-01 authority wording is
superseded only to the extent expressly stated here.

Authorization is permission to perform and prove the repair, not a declaration
that either blocker is closed. Actual external privileges, authenticated access,
independent acceptance, protected checks and recoverability are still required.
No prompt grants an unavailable provider entitlement or bypasses an approval
enforced outside this task.

The product definition, DP-SD-009 meaning/epistemic contracts, DP-SD-017 full L3
scope and 22 active identities plus protected retired sweep remain unchanged.
W0 and W2 source acceptance are retained at their exact revisions and scopes;
they are not promoted to deployment, physical-data or consumer-value acceptance.

## 2. Verified starting point and first action

At inspection the execution worktree was clean at the header checkpoint. W0
was independently accepted; W2's first-frontier source packet covered eight
writers and four service/pure identities. RI-01's code-owned admission defects
were independently closed, while production owner isolation and protected
L0/L1/L2/L4 provenance remained held. Protected main was the header revision,
and no execution-branch PR existed. These are observations to refresh, not
immutable claims about the environment at resumption.

Open packet L3-RI-02-AUTHORIZED-UNBLOCK. Its first bounded action is to consume
the immutable DP-SD-018 pin, call get_goal, reconcile current worktree/PR/main,
execution state, automation, live coordination, migration application and actual
administrative capabilities, and record the scoped owners plus next executable
actions. Reuse the existing task and permanent branch; do not reset, recreate,
rename or move them. Preserve all intervening changes.

Use isolated codex/ packet worktrees on a verified current protected base, with
only the required reviewed predecessor changes brought forward. The permanent
branch retains campaign continuity; reconcile accepted packets into it without
blindly merging unrelated strategy/planner branches or force-rewriting history.
Do not redo accepted research unless changed operands invalidate it.

The active Purna recovery Wave 7 owns a separate source-local campaign. Recheck
its live lease and migration reservations before choosing IDs or editing shared
interfaces. Coordinate exact non-overlapping scopes; do not edit its worktree,
goal, queue, ledger or unpublished migration contents. Source-only planning leases
are not production locks; a real overlapping live owner remains authoritative.
Replace/close only this execution campaign's stale leases through the governed
protocol, then acquire a fresh operation-specific fence before shared mutation.

## 3. Explicit delegated authority

| Domain | Newly authorized action | Boundaries and evidence |
|---|---|---|
| L0/L1/L2 provenance | Appoint acting per-layer adjudicators; inspect changed writer/import closures, accept already authorized compatible changes or exclude unapproved changes from the owned release candidate; issue versioned superseding source/analysis receipts, update generated pins and the narrow generator/validator/tests needed to represent them. | Independent exact-source review; preserve historical receipts and their reconstruction. No invented doctrine, wholesale layer redesign or inherited deployment/freeze claim. |
| L4 provenance only | Reconcile inherited L4 source against existing approved/protected evidence; correct derived metadata or issue an evidenced provenance-only successor. | No L4 writer behavior change, rebuild, freeze, claim issuance or elevation. Exclude unapproved L4 deltas from the owned candidate when not needed. Never alter another owner's checkout. |
| Database security | Acting DBA may use legitimately available administrative access to create scoped protected NOLOGIN owners, a deployment-only migrator and a non-owner builder; grant/revoke exact memberships/ACLs, transfer named object ownership and implement narrowly audited lifecycle APIs. | Existing authorized database/project only; exact object/principal matrix before writes; no database-wide REASSIGN OWNED, broad grants, superuser/BYPASSRLS builder or self-certification. |
| Credentials and bindings | Provision dedicated data-plane credentials, store them directly through approved GitHub/Secret Manager mechanisms, create required secret versions, and change exact affected CI/service/job secret bindings and resource-level access grants. | New or specifically mapped data-plane credentials only. No copying secrets into chat, logs, source, argv or unencrypted artifacts; no bulk secret inventory, unrelated credential rotation, project-wide IAM elevation, new cloud project or unrelated service infrastructure. |
| SQL/deployment adapters | Modify the exact unapplied 1035/1036 candidates or append new migrations if already applied; implement protected-owner function execution, attested migration routing, startup/preflight and runtime connection selection required for this cutover. | Current application tracker plus semantic effects must prove application state. Never edit an applied migration; legacy migration behavior outside the mapped objects remains protected. |
| Delivery and data | Commit, push, open/update focused PRs, use the normal protected merge/queue and deployment path, run reviewed bootstrap/cutover, backup/restore rehearsal, canary, rollback and the already authorized L0-L2 precursor materialization and L3 builds. | Exact reviewed tree and operation gates; exclusive shared-write leases; canonical chart/shared substrate only. No direct-main writes, force push, protection bypass or fabricated receipt. |
| Technical decisions | Surrogate may decide bounded implementation details, packet scopes within this amendment, repair iterations, workflow order and whether a technical hold's existing measurable exit conditions are earned. | Written evidence-based ruling; implementers cannot approve their own work. Policy, source rights, new doctrine/purpose and later-layer elevation are not delegated. |

This authority expires at genuine L3 campaign closure. Before any production
change, record the exact existing project/instance/database, affected deployment
jobs/services, secret resource IDs and principal identities from live discovery.
The previously observed project/instance was madhav-astrology /
asia-south1:amjis-postgres; a mismatch is a scope check, not permission to use
another target. Do not generate or expose credentials in this Strategy task.

## 4. Lane P — provenance reconciliation and truthful supersession

Owner: acting provenance adjudicators for the four affected layers, with one
serialized generated-file integrator and an independent verifier. This lane can
run alongside Lane S's isolated design and tests.

1. Recompute exact per-asset writer/import-closure and aggregate hashes from
   the selected immutable candidate, existing pins and original receipts. Trace
   each difference to its owning source change and accepted requirement. RI-01's
   written full frozen L0 hash differs from the actual generator/pin/test value;
   do not copy a narrative hash into new evidence. At the observed checkpoint,
   the source-held L0 digest is
   5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178.
2. Classify each delta as approved intentional change, derived/import change,
   generator defect, stale receipt, or unapproved/foreign source. Preserve the
   accepted L3 packet; keep unchanged L5/other asset evidence unchanged. Select
   the smallest compatible release set; do not roll back valid accepted L0-L2
   changes merely to reproduce an obsolete hash.
3. For each affected layer, record old and new assets/digests, exact source,
   review, reasons and scope of successor authority. Changed assets earn new
   relevant source/analysis acceptance; unchanged identities retain their own
   valid evidence. Aggregate equality is not per-asset production acceptance.
4. The existing generator forbids L0 regeneration and embeds frozen constants.
   A reviewed, versioned successor-admission mechanism is explicitly authorized
   in that generator and its receipt implementation/tests. Retain the immutable
   original receipt and a way to reconstruct/validate it against its original
   tree; append a superseding binding instead of relabeling old evidence. No
   arbitrary CLI force option, disabled mismatch check or constant-green test.
5. Review an immutable implementation predecessor, generate its inventory, then
   commit the adjudicated receipt referencing that predecessor. Independently
   check final candidate content equivalence and later protected merge bindings.
   Never require a commit to contain its own future SHA. A source successor is
   not a deployed/frozen receipt; operational acceptance is earned separately.
6. Prove authorized successor acceptance; rejection of unreviewed writer/import,
   wrong layer/source/hash/definition and stale-generation claims; immutable
   historical reconstruction; unaffected-layer identity preservation; exact
   generated drift checks and all formerly failing frozen-L0 receipt tests.

Exit P: all selected release-layer provenance is independently accepted at its
declared source scope and mandatory pin/receipt checks genuinely pass. Runtime
generation/freeze statuses remain unreached until later witnessed operations.

## 5. Lane S — protected owner, lifecycle API and credential design

Owner: one security/DBA implementation owner, one deployment integrator for
shared workflow paths, and a separate security/migration verifier. Select exact
role names after collision checks; the following are logical responsibilities.

| Actor | Required ability | Must not possess |
|---|---|---|
| Protected L1/L2 owner | Own explicitly mapped protected history/head/intent/receipt objects and narrowly scoped lifecycle functions; NOLOGIN. | Runtime/login use or broad ownership of unrelated schemas. |
| Deployment-only migrator/bootstrap | Assume only mapped owners for reviewed DDL/ownership; perform authentic migration attestation. | Mounting in application/build runtime or generic access granted by name alone. |
| Non-owner builder | Execute admitted lifecycle operations and required current writer DML through the frozen writer/transaction contract. | Protected-table direct mutation, owner membership, role administration, trigger disabling, protected schema/function replacement or terminal acceptance writes. |
| Web/serving application | Existing needed serving access through independently tested compatible interfaces. | Data-plane build or protected lifecycle writes merely because it formerly owned objects. |
| Independent verifier/acceptance actor | Catalog/data read proof and existing authenticated terminal-evidence interfaces according to its separate role. | Builder credentials or generic unrestricted terminal-event writes. |

The current SQL is invoker-default with SELECT/EXECUTE grants; a non-owner login
alone breaks legitimate generation writes. Explicitly design and implement the
protected-owner lifecycle boundary, using narrowly audited SECURITY DEFINER
functions or an equivalently constrained mechanism. Pin safe search_path,
schema-qualify references, restrict EXECUTE, validate caller/subject/context and
generation state, and defend against temporary-object substitution, dynamic-SQL,
RLS/trigger, transitive membership and function-replacement bypasses.

Map tables, sequences, functions, triggers, policies, schemas, views, default
privileges and ownership dependencies by exact identity. Include the active
producer objects whose owner rights could defeat history/receipt protection,
capture-trigger execution, legacy writer DML and legitimate temporary-input
binding. Do not use blanket grants or transfer unrelated ownership.

Prove the complete role matrix on disposable PostgreSQL using actual restricted
connections, not administrator sessions pretending to be the builder. Positive
tests cover open/bind/populate/capture/complete/exact replay/select and authorized
rollback; negative tests cover forged completion, undeclared/excess partitions,
completed-history mutation, wrong chart/context, owner escalation, TRUNCATE,
trigger disablement, schema/function replacement and direct head/receipt edits.
Verify statement/transaction failure leaves existing history and selected heads
unchanged. Ensure honest unavailable states do not masquerade as accepted data.

Prepare a reviewed exact bootstrap and deployment plan. Reuse the existing
status → one-shot preflight → deployment-only attestation pattern where suitable;
do not assume the existing NIRMANA_MIGRATOR_DATABASE_URL is authorized for these
objects. The general PROD_DATABASE_URL migration runner must neither recreate
protected objects as amjis_app nor skip unapplied work based on an invented
marker. Bind attestation to exact application/SQL identity and verify effects.

Use existing authenticated administrative channels. Provision dedicated random
credentials through secret-safe tooling and managed stores, never request that
the user paste them. Resource-level grants may allow the mapped existing CI or
runtime identities to access only their required secrets. Prefer no new cloud
service account; broader project IAM or unrelated infrastructure remains out of
scope. Prove fresh connections, pool refresh, exact runtime identities and that
the deployment-only credential cannot be reached from web/build/MCP runtime.
Retire only superseded data-plane bindings after compatibility/rollback proof;
do not rotate or invalidate unrelated shared credentials.

Exit S-design: independent security/migration review accepts exact source,
disposable role-realistic positive/negative evidence and recoverable cutover.
This is permission to progress to protected delivery, not a live isolation claim.

## 6. Non-circular release, cutover and W1 sequence

The older RI-01 condition requiring completed production cutover before its PR
is explicitly replaced by this staged order. Do not require a deployed repair
as the precondition for proposing the code that performs that repair.

1. P and S-design complete; freeze a focused exact release candidate and obtain
   independent code/provenance/migration/security review plus mandatory checks.
   Open/update its PR without waiting for completed production role cutover.
2. Reconcile fresh main, migration reservations/applied identities and the live
   planner campaign. Integrate through the protected path in small compatible
   packets. Repair narrowly scoped mandatory release-gate defects autonomously
   with independent review; no repository-wide hygiene campaign or weakened CI.
3. Under a fresh exclusive cutover lease, verify bounded snapshot/restore and
   compatibility evidence, quiesce only the exact affected build writer if
   needed, run the reviewed administrator bootstrap, apply the protected schema
   through its dedicated migrator, attest actual effects, then switch exact
   runtime/job secret bindings and drain only mapped old pools/sessions. Do not
   kill foreign workloads or rely on an expired W0/RI01 lease.
4. Independently verify protected merged/served tree, applied SQL identities,
   owners/transitive memberships/ACLs/function context/default privileges,
   authentic restricted-login behavior and secret non-reachability. Check
   ordinary serving and legitimate writer workflows still function. Reconcile
   the real tracker/evidence mechanism; manual status promotion is forbidden.
5. If cutover fails, pause builds, roll back compatible application/configuration
   or selected heads under the reviewed plan, preserve immutable history and
   owner isolation, then repair/retry within bounds. Returning to owner-powered
   builds or weakening protections is not an acceptable functional rollback.
6. Only after RI-01 release/cutover acceptance, open physical W1 under its own
   renewed lease: verify F0/current-operation prerequisites, backup/restore and
   canary; materialize/select compatible L0 → L1 → L2 generations in the actual
   DAG, validating contributing partitions, rich fields and transitive content.
   Reuse independently accepted matching physical generations when permitted;
   do not rebuild all upstream data unnecessarily. Never translate source
   acceptance or historical rows into current witnessed freeze evidence.
7. Continue automatically into remaining W2 → W8 work under DP-SD-017, retaining
   accepted source work and starting actual downstream data only from accepted
   upstream vectors. Include the measured performance programme, full asset/data
   contracts, history-safe publication, serving and consumer-value proof.

All gates are operation-specific: pre-entry authority/review/restore precedes
mutation; deployment/data/consumer acceptance is proved after the corresponding
operation. A pending CI/deploy/build is monitored, not an automatic campaign stop.

## 7. Exact scope admission and protected exclusions

The first implementation manifest must enumerate exact files/objects/services
before mutation. This amendment admits only the following additional surfaces:

- platform/scripts/generate/nirmana_analysis_layer_pins.py; the actual writer
  inventory generator; platform/src/generated/nirmana-analysis-layer-pins.json,
  nirmana-writer-digests.json, nirmana-analysis-receipts.ts and exact associated
  receipt tests/fixtures, with versioned source-adjudication evidence.
- The already accepted L0/L1/L2 source/import closure and exact compatibility
  corrections necessary to preserve those accepted contracts. No blanket edit
  authority over all earlier-layer writers; the reviewed manifest names each.
- platform/supabase/migrations/1035_data_plane_l1_producer_history.sql and
  1036_data_plane_l2_producer_generations.sql only while proven unapplied, or
  newly reserved follow-up migrations; exact affected lifecycle adapters/tests.
- .github/workflows/deploy.yml, platform/scripts/migrate.ts, narrowly named
  data-plane ownership/preflight/attestation scripts and exact runtime/job
  connection configuration required by the security matrix.
- Corresponding existing cloud database, secret resources, scoped resource-level
  IAM and affected CI/service/job bindings identified in the reviewed manifest.
- Owned execution evidence, per-layer successor-provenance records, coordination
  rows and existing authenticated acceptance/registry interfaces. Pinned native
  strategy/brief/approval and historical receipt bytes remain immutable.

Everything else inherits DP-SD-017. Preserve frozen WriterBase and caller-owned
transactions/build state, complete Swiss serialization, protected retired
ka_gochara_sweep, private-event/purpose/source controls, and original issued
claims/observations. No L4/L5 elevation, empirical outcomes, doctrine changes,
unapproved source/method adoption or narrowed denominator to manufacture closure.

The surrogate may resolve a named L3 technical/operational hold by proving its
existing release conditions and recording the ruling via authorized interfaces.
This is not blanket lifting of century/source/method/history/NIRMANA_HOLD gates.
A required held capability remains incomplete until legitimately resolved.

## 8. Goal, autonomy and recovery

The persistent goal remains the full goal_objective in the pinned DP-SD-017
brief; record DP-SD-018 as its newly approved prerequisite/authority delta. If
the goal is active, continue it. If the product has resumed a blocked goal, use
this new user authority for a fresh blocker audit. If no goal exists, create
the original full L3 objective with this amendment referenced and no budget.
Never mark an unfinished goal complete merely to replace it or to report that
the unblocking packet passed. Do not downgrade the endpoint to source-only.

Reuse the existing thread heartbeat l3-k-la-execution-recovery. Update its prompt
through the product automation tool to consume DP-SD-017 plus DP-SD-018, check
real external operands and ownership, advance eligible work, and stay quiet on
unchanged state. Do not add a second heartbeat/conductor or a standalone cron.
Actual scheduled wakes have been observed; the old state file still says first
wake proof is pending. Reconcile that evidence and prove one durable-state
continuation into eligible work before claiming unattended recovery success.

There is one conductor and three original L3 workstreams. P and S are bounded
unblocking lanes, not new permanent tasks. They may run in parallel where file,
schema and security boundaries are independent; reserve verifier/integrator
capacity. Serialize generated files, migration IDs, integration and shared
production writes. Builders/operators never certify their own evidence.

Do not ask the user again for the permissions expressly granted here. Route
routine technical choices to the surrogate, record the ruling and execute. Use
at most two identical transient retries; repeated deterministic failure gets one
bounded root-cause packet and a revised plan. Continue every genuinely eligible
independent packet; do not generate busywork while real gates are unchanged.

If necessary administrative access is genuinely unavailable, inspect approved
access paths and complete independent local/review preparation. Record the exact
denied operation, target/required privilege, affected dependency and smallest
external action without exposing secrets. Authorization does not justify
privilege escalation through an unauthorized path. Ask only for a truly external
capability or materially new excluded scope; keep the heartbeat and resumable
evidence. Apply the product's genuine-blocker threshold, not a false completion.

## 9. Completion and handback

Unblocking closes only when P, S and RI-01's live release/cutover gates pass.
That is an intermediate event; immediately continue W1 and all remaining approved
L3 work. Full campaign completion still requires every required active asset's
type-appropriate terminal disposition, accepted physical code-and-data DAG,
compatible layer publication/history/rollback, protected source/deployment and
migration proof, actual scoped consumer integration and value comparison, and
truthful independent tracker/evidence reconciliation.

Retired/probe assets receive applicable evidence, never fabricated row builds.
Tests, PRs, heartbeat wakes and elapsed time are not accepted-asset counts.
Report source, physical data, deployment, consumer use and value separately.

At genuine full L3 completion, close its goal, pause its heartbeat, release only
owned leases, preserve immutable evidence and clean only proven-safe temporary
worktrees. Return a concise closure packet here and keep L4/L5 waiting for their
own strategy. Until then, retain the precise next eligible action or true external
blocker. No further routine human approval is required by this amendment.

## 10. Independent handoff review

Independent reviewer l3_data_dag_astra returned scoped approval on 2026-09-15
with no blocking wording changes for the complete 354-line draft, SHA-256
4c2588a725c09349cef8cc3a1dd15909d552a7f006faa5c8454b9bf0cd4d2db5.
The reviewer independently inspected the exact implementation checkpoint and
confirmed the provenance supersession, reviewed-predecessor/final-candidate
bindings, protected actor matrix, non-circular release sequence, available-access
honesty, L4 metadata-only boundary and autonomous full-goal continuation.
Only approval status and this review record were added after that review.

This is bounded handoff approval, not source-provenance acceptance, live role
isolation, deployment, physical data or consumer-value acceptance. Immutable
content/approval pins and actual dispatch are recorded in the strategic ledger.
