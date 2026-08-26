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
  job to the internal monitor route.

Terraform never stores the application secret. After a protected-main apply, an
approved secret-aware operator must configure the existing `MARSYS_CRON_SECRET`
as `X-Marsys-Cron-Secret` outside Terraform and state. Do not use `Authorization`:
Cloud Scheduler uses it for the OIDC token. The job ignores only its HTTP header
map so later plans preserve that externally managed header.

Use the approved secret-injection mechanism; never put the value in source,
Terraform input, or shell history:

```sh
gcloud scheduler jobs update http amjis-nirmana-elevation-monitor \
  --project=madhav-astrology \
  --location=asia-south1 \
  --update-headers='X-Marsys-Cron-Secret=<value injected only by the approved secret-aware operator>'
```

Verify the header exists without printing its value:

```sh
gcloud scheduler jobs describe amjis-nirmana-elevation-monitor \
  --project=madhav-astrology \
  --location=asia-south1 \
  --format=json | jq -e '.httpTarget.headers | has("X-Marsys-Cron-Secret")'
```

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
| Project and service account | `resourcemanager.projects.get`, `iam.serviceAccounts.create`, `iam.serviceAccounts.get`, `iam.serviceAccounts.getIamPolicy`, `iam.serviceAccounts.setIamPolicy` |
| `amjis-web` only | `run.services.get`, `run.services.getIamPolicy`, `run.services.setIamPolicy` |
| This monitor job only | `cloudscheduler.jobs.get`, `cloudscheduler.jobs.create`, `cloudscheduler.jobs.update` |
| `scheduler/nirmana-elevation-monitor` state objects | the existing Terraform-state read/write/lock object permissions (`get`, `list`, `create`, `update`, and lock release) |

No project-wide `roles/run.invoker`, broad token-creator grant, or permission to
read unrelated Scheduler jobs is required. No permission is granted by this
repository change.
