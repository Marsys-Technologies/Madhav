# Cloud Tasks — `amjis-build-queue`

Provisions the Cloud Tasks queue that backs `/api/build/start`. Unit
`4.build_trigger` of the Platform Modernization program.

## Architecture

```
[/clients/[id]/build  Build button]
        │ POST /api/build/start { chart_id, ayanamsha_role }
        ▼
[amjis-web  src/app/api/build/start]   ─── authorizeChartAccess gate (owner/super_admin)
        │
        │ google-cloud-tasks createTask → OIDC token (audience = web URL)
        ▼
[Cloud Tasks queue: amjis-build-queue]
        │
        │ POST {audience}/api/build/task  (OIDC-bearer)
        ▼
[amjis-web  src/app/api/build/task]   ─── verify OIDC, invoke Job
        │
        │ run_v2.JobsClient.RunJob → marsys-build-pipeline-job
        ▼
[Cloud Run Job: marsys-build-pipeline-job]   (chart_id, ayanamsha_role)
        │
        │ writes build_events rows  (asset, stage, status, % complete)
        ▼
[Postgres: build_events]
        │
        │ /api/build/events/[buildId] SSE
        ▼
[Cockpit /clients/[id]/build progress UX]
```

## Apply (operator-side, NOT from this worktree)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/infra/cloud_tasks
./apply.sh plan       # diff
./apply.sh apply      # creates queue + invoker SA + IAM bindings
```

The output names land in `.github/workflows/deploy.yml` env_vars as:

- `BUILD_TASK_QUEUE`            (e.g. `amjis-build-queue`)
- `BUILD_TASK_QUEUE_LOCATION`   (`asia-south1`)
- `BUILD_TASK_INVOKER_SA`       (`amjis-build-invoker@madhav-astrology.iam.gserviceaccount.com`)
- `BUILD_TASK_AUDIENCE`         (the prod `amjis-web` URL)

After apply, redeploy `amjis-web` so the new env_vars land in the container.

## Feature flag

`MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true` — defaults **false** until the
operator-side smoke passes end-to-end (Cloud Task enqueue → Job execute →
build_events rows → cockpit SSE).
