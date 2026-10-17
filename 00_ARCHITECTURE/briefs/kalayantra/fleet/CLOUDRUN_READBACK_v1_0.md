---
artifact: CLOUDRUN_READBACK
version: "1.0"
status: REVIEW_CANDIDATE
produced_on: 2026-10-17
authority: J-2a run-1 dispatch V1 REJECTED (X-20261017T124945Z-review-j2a-13-dispatch-v1); pack MISSING M6/M7 ("no enabled fixed op reads Cloud Run job configuration/image/corpus or execution completion")
changelog:
  - "1.0: new read-only executor kind `cloudrun_job_readback` (fleet/cloudrun_readback.py, ky.cloudrun_readback/1)."
---

# `cloudrun_job_readback` — measured evidence about the deployed pipeline job

Closes pack M6/M7 for checklist rows 0.3 / 3.4 (SUBMIT §13). It **measures**; it does not judge. The signer compares the record to the reviewed main.

## The operation

| | |
|---|---|
| kind | `cloudrun_job_readback` (`executor_ops.json`; enabled_by J-2a) |
| class | read-only, `production:false`, no lease, no acceptance receipt, not fenced; runs in parallel with other reads |
| needs | capability `gcloud` (the executor's own gcloud identity; no credential reaches the request, the script or the output) |
| requesters | `adhikarin`, `v1`, `v2` |
| request args | none, or `{"execution": "brahma-build-pipeline-job-<suffix>"}` — nothing else (the executor refuses any other key; the script refuses any other flag and any other name shape, `smalltest_launch.EXECUTION`) |
| script | `fleet/cloudrun_readback.py`, extracted from origin/main and run by the executor; standard library only |
| calls | at most three fixed `gcloud` describes, all against project `madhav-astrology`, region `asia-south1`: the job `brahma-build-pipeline-job`; the registry digest of `…/amjis/brahma-pipeline:<commit>`; and, if asked, the one execution. No `execute`, `update`, `logging read`, `docker`, or image run. |
| output | one line: `ky.cloudrun_readback/1` JSON. Exit 0 = `status: MEASURED`; exit 1 = `status: REFUSED` with a `reason`; exit 2 = a disallowed argument |

Minimal request:

```json
{"operation_id": "OP-J2A-CR-1", "kind": "cloudrun_job_readback", "item_id": "J-2a", "idempotency_key": "OP-J2A-CR-1",
 "requested_by": "v1", "kyd": "<kyd>", "args": {"execution": "brahma-build-pipeline-job-abc12"}}
```

## What the record says (and the signer should compare)

* `job.image.reference` / `tag` / `digest` — what Cloud Run holds, and the registry digest that tag resolves to **at `measured_at`**.
* `provenance.image_commit` — the 40-hex commit in the tag. **How this ties the image to a commit:** `deploy.yml` job *Build & Deploy Pipeline Job Image* checks out `DEPLOY_SHA`, verifies `git rev-parse HEAD == DEPLOY_SHA`, builds `Dockerfile.pipeline`, pushes `brahma-pipeline:${DEPLOY_SHA}` (and `:latest`) and points the job at `…:${DEPLOY_SHA}`. So the tag is the commit **by CI convention**. The image itself carries no revision label (`provenance.image_attests_commit` is `false`), and a tag is mutable: an out-of-band push could move it. The digest pins what was measured; it does not prove who pushed it. A reference that is `:latest`, digest-only or another repository is **refused** (no commit can be tied to it).
* `provenance.job_label_commit_sha` — `null` today (the deploy step sets no job label; services have a `commit-sha` revision label). If it is ever set and disagrees with the tag, the record is refused.
* `job.service_account`, `timeout_seconds`, `max_retries`, `memory`, `cpu`, `labels`, `environment`. Compare to `deploy.yml` (`--service-account`, `--task-timeout=86400`, `--memory=16Gi`, `--cpu=4`, `--update-env-vars`, `--update-secrets`). Secrets show **name and version only**. Plain values show only for `GCP_PROJECT`, `PUBSUB_TOPIC`, `KA_KSHETRA_HASH_SPILL_DIR`, `SE_EPHE_PATH`, `SWE_EPHE_PATH`, `PYTHONPATH`; every other value is `value_withheld`. A new key needs a reviewed edit of the allowlist.
* `execution` (only when asked): `outcome` is `SUCCEEDED` only if the `Completed` condition is `True`, `completionTime` is present, `succeeded == taskCount`, and nothing failed, was cancelled or is running; `FAILED` on any failed/cancelled count or `Completed=False`; otherwise `RUNNING`. Also `start_time`, `completion_time`, the four counts, the image reference and args the execution carried (the `--run-id` it was launched with), `image_reference_equals_job`, and `log_uri` (the link only — **logs are not read**; a log read needs its own reviewed kind).
* `corpus.status: UNMEASURED_IN_DEPLOYED_IMAGE` — see below.

A required field that is missing or malformed refuses the **whole** record. A refused record is never evidence of anything but the refusal.

## Corpus evidence — precisely what exists

* **Exists:** `Dockerfile.pipeline` downloads the Swiss Ephemeris files and runs `sha256sum -c` on `sepl_18.se1`, `semo_18.se1`, `seas_18.se1`; a mismatch fails the build, so no image is pushed. `sefstars.txt` and `seleapsec.txt` are downloaded but **not** checksummed. Combined with the tag→commit tie above, the evidence is: *the Dockerfile at `provenance.image_commit` pins these digests, and CI built the tag from it.* The record names where to read this (`corpus.build_gate_read_at`); the signer runs `git show <image_commit>:platform/python-sidecar/Dockerfile.pipeline` and compares the three pinned digests with the local pinned corpus (`/Users/Dev/kalayantra/ephe`).
* **Does not exist:** any measurement of the corpus *inside the deployed image*. No image label, registry field or Cloud Run field records it, and reading it means running the image. The op therefore reports an honest null rather than a pass.
* **Smallest reviewed way to close it (proposal — not done here, because it changes a production image build and would move the digest mid-J-2a):** (1) in `deploy.yml`'s re-point step add `--update-labels=commit-sha=${DEPLOY_SHA}` (the services' scheme), which this op already reads and cross-checks; (2) in the same job, after the push, add a CI step that runs the pushed image once with `--entrypoint sha256sum` over `/app/ephe/*` and fails the deploy on a mismatch with the three pinned digests, and record the result as a job label (`ephe-ok=<first 12 hex of the digest list>`). With (1) the commit tie no longer rests on the tag alone; with (2) the corpus is measured in the deployed bytes at deploy time.

## Not proven by this op

The image digest at the moment an execution *started* (the execution record carries the reference as launched, not a resolved digest — `image_reference_equals_job` compares references only); who pushed the tag; the corpus in the running container; logs or the database effects of the run (use `readback_sql`).

## Shape caveat

(I) INTERPRETATION — no live gcloud response was captured for this build. The parser reads the Cloud Run v1 shapes the repo already reads (`spec.template.spec.template.spec.containers[0].image`, `deploy.yml`; `status.conditions` / `succeededCount` / `taskCount` for an execution, `gochara_seal_execution_check.py`; `image_summary.digest`, `gochara-verification-job-deploy.yml`). A different shape **refuses**, never guesses. Fixtures under `tests/fixtures/cloudrun_readback/` are shaped from those paths, not captured. If the first real run refuses on shape, the receipt's `reason` names the field; fix the parser, do not hand-edit the receipt.
