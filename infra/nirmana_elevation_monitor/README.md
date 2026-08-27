# Nirmana elevation monitor Terraform root

This root owns only the Nirmana monitor and uses the dedicated GCS state prefix
`scheduler/nirmana-elevation-monitor`. It is intentionally separate from
`infra/scheduler`, whose remote state owns unrelated Scheduler jobs. State
ownership is an operational release gate: do not infer it from this repository
layout or from an earlier claim that the monitor was never applied.

## Resources

- `google_service_account.nirmana_elevation_monitor` — the dedicated
  `amjis-nirmana-monitor` OIDC identity.
- `google_cloud_run_v2_service_iam_member.nirmana_elevation_monitor_invokes_web`
  — `roles/run.invoker` on only `amjis-web`.
- `google_service_account_iam_member.cloud_scheduler_mints_nirmana_monitor_oidc`
  — `roles/iam.serviceAccountOpenIdTokenCreator` for Cloud Scheduler's service
  agent on only that dedicated service account.
- `google_cloud_scheduler_job.nirmana_elevation_monitor` — the five-minute POST
  job `amjis-nirmana-elevation-monitor` to the internal monitor route, with the
  Cloud Scheduler OIDC token.

The route authenticates only the Cloud Scheduler OIDC bearer token. It verifies
the fixed Cloud Run audience
`https://amjis-web-938361928218.asia-south1.run.app` and the dedicated service
account `amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com` before
any observation work. Terraform fixes the same audience in `main.tf` and rejects
project or region overrides that would mint a non-matching principal. There is no
custom header, shared secret, or alternate application authentication value in
Terraform state.

## Apply discipline and bootstrap permissions

Review-ref plans may run through the dispatch-only IaC workflow with
`module: nirmana_elevation_monitor`; they save `monitor.tfplan` as a short-lived
artifact. Apply is permitted only on protected `main`, in the named `production`
GitHub environment, and only by downloading and applying that exact saved plan.
The wrapper rejects local/worktree applies, an unsaved plan, another ref, and an
unnamed environment. Do not apply from a worktree.

Before the first protected-main operation, retain state-handoff evidence from
remote plans: the old `infra/scheduler` root must show **zero** monitor destroys,
and this isolated root must show exactly the four intended creates, or the review
must contain explicit imports/state moves that reconcile a pre-existing monitor.
This is release evidence, not a documentation waiver. Do not dispatch an apply
until that evidence, plan review, protected CI, and production-environment
reviewer configuration are recorded.

The plan job authenticates as the established
`github-actions@madhav-astrology.iam.gserviceaccount.com`. The gated apply job
uses the separate
`github-actions-nirmana-apply@madhav-astrology.iam.gserviceaccount.com` identity.
Before any apply, its WIF trust must require the GitHub `production`
environment, and any first-apply permission must be granted only to that
identity for the approved release window. Do not add the temporary
monitor-bootstrap permissions to the plan identity: plan runs before the GitHub
environment approval.

Before the first apply, confirm the Cloud Scheduler API's Google-managed service
agent exists. The Terraform executor needs only the following first-apply
permission families, scoped to this project, `amjis-web`, the dedicated service
account, and this state prefix where the platform permits it:

| Scope                                               | Required permissions                                                                                                                                                                         |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Project and dedicated service account               | `resourcemanager.projects.get`, `iam.serviceAccounts.create`, `iam.serviceAccounts.get`, `iam.serviceAccounts.getIamPolicy`, `iam.serviceAccounts.setIamPolicy`, `iam.serviceAccounts.actAs` |
| `amjis-web` only                                    | `run.services.get`, `run.services.getIamPolicy`, `run.services.setIamPolicy`                                                                                                                 |
| This monitor job only                               | `cloudscheduler.jobs.get`, `cloudscheduler.jobs.create`, `cloudscheduler.jobs.enable`                                                                                                        |
| `scheduler/nirmana-elevation-monitor` state objects | the existing Terraform-state read/write/lock object permissions (`get`, `list`, `create`, `update`, and lock release)                                                                        |

No project-wide `roles/run.invoker`, broad token-creator grant, or permission to
read unrelated Scheduler jobs is required. No permission is granted by this
repository change.

The provider resumes a newly created Scheduler job, so
`cloudscheduler.jobs.enable` is required; `cloudscheduler.jobs.update` is not
required for this reviewed add-only plan. Platform IAM cannot name-constrain
every first-create permission, so the temporary release binding must be
independently reviewed, time-bounded, and removed immediately after a verified
apply; never convert it into a standing broad executor role.
