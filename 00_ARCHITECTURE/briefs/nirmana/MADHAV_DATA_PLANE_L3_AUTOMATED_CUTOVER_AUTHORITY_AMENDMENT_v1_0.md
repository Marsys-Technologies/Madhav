---
artifact: MADHAV_DATA_PLANE_L3_AUTOMATED_CUTOVER_AUTHORITY_AMENDMENT
version: "1.0"
status: NATIVE_AUTHORIZED_SOURCE_AMENDMENT
recorded_at: 2026-09-16T10:56:52Z
strategy_decision: DP-SD-020
parent_decisions:
  - DP-SD-017
  - DP-SD-018
  - DP-SD-019
source_base: 113ccc37eb93f02416907fee75b52958792eae7a
coordination_lease_commit: 85b25bac593dc932415dc38207db94720031e033
destination_task: 01a0998a-8240-7631-97ce-36c6d4734fde
---

# L3 automated cutover authority amendment — DP-SD-020

## 1. Native authority and narrow supersession

The Native explicitly authorized proceeding without a separate person reviewing
the cutover and instructed the existing automated plan to continue beyond that
point when complete. This decision removes only the human/separate-reviewer
dependency introduced for the GitHub production-cutover environment. It does
not waive source review, CI, security verification, branch protection, evidence
binding, rollback readiness, or any database and production safety control.

DP-SD-020 therefore supersedes only these prior requirements:

- a GitHub `required_reviewers` rule for `data-plane-production-cutover`;
- `prevent_self_review=true` as a cutover prerequisite;
- a human deployment approval event and `/approvals` history for the exact run;
- an `approvedBy` field in the backup/restore receipt.

All other provisions of DP-SD-017, DP-SD-018 and DP-SD-019 remain binding.

## 2. Replacement automated environment contract

The cutover job must still use the named
`data-plane-production-cutover` GitHub environment. The authenticated
environment response must show no `required_reviewers` rule and the deployment
branch policy must be exactly `protected_branches=true` and
`custom_branch_policies=false`. The workflow token retains `actions:read` and
must authenticate the exact repository, workflow-run ID and immutable deploy
SHA. Failure to read or match any of those values fails closed.

The exact JSON backup/restore receipt replaces `approvedBy` with:

- `authorityDecision: "DP-SD-020"`;
- `executionMode: "native_authorized_automated_cutover"`.

Those fields are immutable run bindings, not free-form inputs. A human reviewer
rule is treated as a stale dependency and blocks the automated cutover until the
environment matches this decision.

## 3. Controls preserved without reduction

The following gates remain mandatory and fail closed:

1. exact protected source, repository and workflow-run binding;
2. accepted source checks and independent technical/security verification;
3. dedicated builder service account, builder-only secret and least-privilege
   runtime IAM, with no broad or inherited runtime Secret Manager accessor;
4. fresh production backup, restore of that exact backup only to a distinct
   isolated validation instance, PostgreSQL/schema/state attestation, and an
   expiring exact receipt;
5. a unique cutover lease, serialized workflow concurrency, refreshed semantic
   state and build-run quiescence under the database lock;
6. protected NOLOGIN ownership, restricted login topology, exact migration
   identities, transactional cutover and post-cutover semantic attestation;
7. rollback material, canaries, service health, routine-delivery barrier and
   complete postflight evidence before any delivery or acceptance claim.

No broad IAM grant, credential disclosure, protection bypass, arbitrary-branch
deployment, destructive production restore, L0 restart, L4/L5 work, or empirical
success claim is authorized.

### Control-plane administrator clarification

Live preflight established that the project's sole human `roles/owner` is also
reported by Google as having `secretmanager.versions.access` and service-account
token permissions. Removing that sole Owner would create an administrative
lockout risk and is not a runtime-isolation control. The preflight must therefore
distinguish control-plane administration from workload authority without
creating a general exception.

Exactly one repository-declared `user:` principal may be accepted only as an
unconditional `roles/owner` binding on `projects/madhav-astrology`. The same
principal is rejected at any folder or organization ancestor. Every additional
user, service account, group, domain, conditional grant, role, or inherited
secret/impersonation grant remains blocking. The builder secret's own policy
still contains exactly one accessor: the dedicated builder runtime. This
clarification adds no principal or permission; it makes the gate model the one
pre-existing Native administrative principal separately from runtime access.

The same rule applies to Google-managed control-plane service agents: only an
exact built-in service-agent role paired with its canonical principal derived
from the authenticated project number may remain on this exact project. This
allowlist covers only the enabled Vertex AI, App Engine, Cloud Build, Scheduler,
Tasks, Compute, GKE, Pub/Sub and Cloud Run service agents. A wrong role/member,
condition, project number, ordinary service account, folder or organization
binding remains blocking. These provider agents are not accepted as builder
runtime principals; the builder service account's resource policy remains the
single GitHub Actions allowlist.

## 4. Current observation and non-claim

At 2026-09-16T10:56:52Z, pull request `#2615` was source-clean at
`113ccc37eb93f02416907fee75b52958792eae7a`, but the named GitHub environment,
dedicated builder service account and builder secret were still absent. The
exclusive coordination lease is durably recorded at
`85b25bac593dc932415dc38207db94720031e033`.

This artifact authorizes the bounded source and live remediation described
above. It does not claim that the amendment has merged, the environment or IAM
resources exist, a backup was restored, a migration ran, production data was
built, a consumer used L3, or L3 reached acceptance.
