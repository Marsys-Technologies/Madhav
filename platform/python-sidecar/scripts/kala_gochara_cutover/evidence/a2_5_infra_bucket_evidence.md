---
artifact: A2_5_INFRA_BUCKET_EVIDENCE
version: "1.0"
date: "2026-09-30"
actor: stream-A (Kimi Code)
authority: "Native authorisation relayed by steward M20260930T094824-db04 (2026-09-30T09:48:24Z)"
item: A2.5 (step infra_bucket)
---

# A2.5 — GCS bucket `gochara-century-stream` creation evidence

Authorisation (steward M20260930T094824-db04, native authority): create ONE GCS bucket
`gochara-century-stream` in the pipeline job's region (asia-south1), uniform bucket-level
access, public access prevention enforced, 30-day lifecycle delete; grant
`roles/storage.objectAdmin` ON THAT BUCKET ONLY to the `brahma-build-pipeline-job`'s
service account (read from the job spec; no project-level grant, no other principal).

## 1. Service account read from the live job spec

```
$ gcloud run jobs describe brahma-build-pipeline-job --region asia-south1
✔ Job brahma-build-pipeline-job in region asia-south1
Executed 548 times
Last executed 2026-09-19T22:48:39.083721Z with execution brahma-build-pipeline-job-j882q
Last updated on 2026-09-30T04:58:12.500508Z by github-actions@madhav-astrology.iam.gserviceaccount.com
Tasks: 1
Container None
  Image: asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:95e96d63cb8f5b58689d19f728266107f39df346
  Memory: 16Gi   CPU: 4
  Secrets: DATABASE_URL data-plane-builder-db-url:latest
Service account: data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com
SQL connections: madhav-astrology:asia-south1:amjis-postgres
```

Service account used for the grant: `data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com`
(matches the spec's `data-plane-builder-runtime@…`).

## 2. Bucket creation

```
$ gcloud storage buckets create gs://gochara-century-stream \
    --project=madhav-astrology --location=asia-south1 \
    --uniform-bucket-level-access --public-access-prevention
Creating gs://gochara-century-stream/...
```

## 3. 30-day lifecycle delete

Lifecycle file (`/tmp/gochara-century-stream-lifecycle.json`):

```json
{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 30}}]}
```

```
$ gcloud storage buckets update gs://gochara-century-stream \
    --lifecycle-file=/tmp/gochara-century-stream-lifecycle.json
Updating gs://gochara-century-stream/...
```

## 4. Bucket-scoped grant (no project-level grant, no other principal)

```
$ gcloud storage buckets add-iam-policy-binding gs://gochara-century-stream \
    --member="serviceAccount:data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
...
- members:
  - serviceAccount:data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com
  role: roles/storage.objectAdmin
etag: CAM=
resourceId: projects/_/buckets/gochara-century-stream
```

No `gcloud projects add-iam-policy-binding` was run. The only non-default binding is the
single service account above, on the bucket only. (The legacy projectEditor/projectOwner/
projectViewer entries are GCS default legacy bindings present on every new bucket.)

## 5. Post-creation verification

```
$ gcloud storage buckets describe gs://gochara-century-stream --format=json
location:               ASIA-SOUTH1
uniform_bucket_level_access: true
public_access_prevention:    enforced
lifecycle_config:
  rule:
  - action: {type: Delete}
    condition: {age: 30}
```

All four mandated properties verified live: region asia-south1, UBLA on, public access
prevention enforced, Delete at age 30 days. Grant verified in the bucket IAM policy (§4).
