# Nirmana elevation monitor Terraform root

This root owns only the Nirmana monitor and uses the dedicated GCS state prefix
`scheduler/nirmana-elevation-monitor`. It is intentionally separate from
`infra/scheduler`, whose remote state owns unrelated Scheduler jobs. The monitor
has never been applied, so this separation requires no state move and must not
delete or recreate any existing Scheduler resource.

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
any observation work. Terraform therefore has no externally managed HTTP headers
or application-authentication value in its state.

## Apply discipline and bootstrap permissions

Run only through the protected manual IaC workflow
(`module: nirmana_elevation_monitor`) or an approved protected-main operator. Do
not apply from a worktree.

Before the first apply, confirm the Cloud Scheduler API's Google-managed service
agent exists. The Terraform executor needs only the following first-apply
permission families, scoped to this project, `amjis-web`, the dedicated service
account, and this state prefix where the platform permits it:

| Scope | Required permissions |
| --- | --- |
| Project and dedicated service account | `resourcemanager.projects.get`, `iam.serviceAccounts.create`, `iam.serviceAccounts.get`, `iam.serviceAccounts.getIamPolicy`, `iam.serviceAccounts.setIamPolicy`, `iam.serviceAccounts.actAs` |
| `amjis-web` only | `run.services.get`, `run.services.getIamPolicy`, `run.services.setIamPolicy` |
| This monitor job only | `cloudscheduler.jobs.get`, `cloudscheduler.jobs.create`, `cloudscheduler.jobs.update` |
| `scheduler/nirmana-elevation-monitor` state objects | the existing Terraform-state read/write/lock object permissions (`get`, `list`, `create`, `update`, and lock release) |

No project-wide `roles/run.invoker`, broad token-creator grant, or permission to
read unrelated Scheduler jobs is required. No permission is granted by this
repository change.
