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

The GCP-native release path does not depend on GitHub. A named, approved GCP
release operator creates `monitor.tfplan` with Terraform and then applies that
exact saved plan from a trusted GCP environment. The wrapper accepts an apply
only when `IAC_APPLY_ENVIRONMENT=production` and `GCP_RELEASE_APPROVAL` contains
the recorded change/approval reference. Those values are traceability guards;
GCP IAM and Cloud Audit Logs are the actual authorization and evidence boundary.

Use short-lived [Application Default Credentials](https://docs.cloud.google.com/docs/terraform/authentication)
or service-account impersonation for the approved GCP release identity. The
wrapper refuses `GOOGLE_APPLICATION_CREDENTIALS`, so static service-account key
files cannot become an alternate release path. It also verifies that ADC is
available before Terraform initializes an apply. Do not put credentials, tokens,
or key material in the plan, repository, shell history, or release records.

The execution sequence is deliberately two-person and saved-plan based:

1. The approved GCP release operator creates a saved plan: `bash apply.sh plan monitor.tfplan`.
2. An independent reviewer records that the plan has exactly the approved
   resource changes and cites the approval reference.
3. The same approved GCP release identity applies that unchanged file with
   `IAC_APPLY_ENVIRONMENT=production` and the recorded `GCP_RELEASE_APPROVAL`.
4. Retain the Terraform output and corresponding Cloud Audit Logs entries as the
   release evidence. Do not use `-auto-approve`, ad-hoc console edits, or a new
   plan in place of the reviewed saved plan.

GitHub Actions has no monitor apply path; it is not a runtime or provisioning
dependency for this monitor.

Before the first GCP-native operation, retain state-handoff evidence from remote
plans: the old `infra/scheduler` root must show **zero** monitor destroys, and
this isolated root must show exactly the four intended creates, or the review
must contain explicit imports/state moves that reconcile a pre-existing monitor.
This is release evidence, not a documentation waiver. Do not apply until that
evidence, the saved-plan review, and the GCP release-identity approval are
recorded.

Before any apply, name the GCP operator group or dedicated release service
account in the approval record. Grant the first-apply permissions only to that
identity for the approved release window, and use service-account impersonation
when a human operator prepares or applies the plan. Do not grant those bootstrap
permissions to a broad developer, runtime, or scheduler identity.

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
