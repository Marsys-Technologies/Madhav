---
artifact: CLOUDRUN_READBACK
version: "1.3"
status: REVIEW_CANDIDATE
produced_on: 2026-10-17
authority: J-2a run-1 dispatch V1 REJECTED (X-20261017T124945Z-review-j2a-13-dispatch-v1); pack MISSING M6/M7 ("no enabled fixed op reads Cloud Run job configuration/image/corpus or execution completion")
changelog:
  - "1.3: optional `metrics` argument (SR-BOLD-09, BOLD-09-METRICS): two more fixed read-only `gcloud monitoring time-series list` calls (Cloud Run job container CPU and memory utilisation) for ONE execution, summarised as mean / p95 / highest-bucket bound, with the CPU read against the allocated vCPUs as a `shape` (SINGLE_THREAD_BOUND when p95 sits at ~1 vCPU of several). Additive: the `metrics` key exists only when asked, so a run without it prints exactly what 1.2 printed. NOT yet in the executor table's `allowed_args` (see Metrics, below)."
  - "1.2: `logs` reads EVERY entry of the execution (J3C-v2 blocking M-J3-6/7: a 26-class build overflowed the single newest-1000 page, so STRETCH_SINK counts read null). Same fixed filter, paged newest-first by an added `timestamp<=` cursor; hard caps (60 pages, 420 s); `page_full` is replaced by `truncated` + `truncation_reason` + `pages_read` + `max_pages`. Still additive to ky.cloudrun_readback/1 (key removed from the `logs` object: nothing in the repo read `page_full`)."
  - "1.1: optional `logs` argument (SR-J3-READ-KINDS): one fixed `gcloud logging read` of the execution's job log, parsed for STRETCH_SINK/1 lines and asset.substep progress. Additive; the schema stays ky.cloudrun_readback/1 (the new `logs` key is null unless asked)."
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
| request args | none, or `{"execution": "brahma-build-pipeline-job-<suffix>"}`, or `{"execution": "…", "logs": "true"}` — nothing else (the executor refuses any other key; the script refuses any other flag and any other name shape, `smalltest_launch.EXECUTION`) |
| script | `fleet/cloudrun_readback.py`, extracted from origin/main and run by the executor; standard library only |
| calls | at most three fixed `gcloud` describes, all against project `madhav-astrology`, region `asia-south1`: the job `brahma-build-pipeline-job`; the registry digest of `…/amjis/brahma-pipeline:<commit>`; and, if asked, the one execution. With `logs`, further calls of the one fixed `gcloud logging read`, one per page of up to 1000 entries (see "Logs" below). No `execute`, `update`, `docker`, or image run. |
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
* `execution` (only when asked): `outcome` is `SUCCEEDED` only if the `Completed` condition is `True`, `completionTime` is present, `succeeded == taskCount`, and nothing failed, was cancelled or is running; `FAILED` on any failed/cancelled count or `Completed=False`; otherwise `RUNNING`. Also `start_time`, `completion_time`, the four counts, the image reference and args the execution carried (the `--run-id` it was launched with), `image_reference_equals_job`, and `log_uri` (the link only; the log itself is read only with `logs`, below).
* `corpus.status: UNMEASURED_IN_DEPLOYED_IMAGE` — see below.

A required field that is missing or malformed refuses the **whole** record. A refused record is never evidence of anything but the refusal.

## Logs (`logs: "true"`, only with `execution`)

`--logs` without `--execution`, or with a malformed name, is refused before any cloud call. The one `gcloud logging read` uses a filter built only from constants and the regex-validated execution name: `resource.type="cloud_run_job"`, `resource.labels.job_name="brahma-build-pipeline-job"`, `resource.labels.location="asia-south1"`, `labels."run.googleapis.com/execution_name"="<execution>"`, narrowed to lines containing `STRETCH_SINK` or `asset.substep`. It is read **page by page**, newest first (`--order=desc`, `--limit=1000`): each following call adds exactly one clause, `AND timestamp<="<oldest entry time of the previous page>"` (inclusive, so a tie at the seam is not lost; entries are de-duplicated by `insertId`). The cursor time is only ever taken from gcloud's output after it matches a strict `YYYY-MM-DDThh:mm:ss[.n{1,9}]Z` shape. A page shorter than 1000 proves the oldest entry was reached. Bounds: `LOG_MAX_PAGES` = 60 calls (60,000 entries) and `LOG_BUDGET_S` = 420 s in total. The record's `logs` object (null when not asked):

* `pages_read`, `max_pages`, `entries_returned` (distinct entries over all pages), `truncated` (older entries exist that were not read) with `truncation_reason` (`page_cap` · `time_budget` · `stuck_cursor` = a full page of one instant, no progress · `unpageable_time` = a full page whose oldest time is not strict UTC), `unreadable_lines`.
* `sink` — `STRETCH_SINK/1` records (`stretch_sink.log_line`) counted as `counts_by_kind_reason` (`kind/reason`) and `records_by_event_class`, de-duplicated by `(event_class, record_id)` (`duplicate_record_lines`; the `record_id` carries no event class, so classes legitimately share ids — SR-STRETCH-SINK-COUNTS) and also given per class as `counts_by_kind_reason_by_event_class`; each `STRETCH_SINK_SUMMARY/1` line with `read_counts_by_kind_reason` (what was read for that class), `records_match_summary`, `counts_by_kind_match_summary` and `digest_matches_records` (MEASURING_BUILD_CONTRACT v1.0 MB-2.4: sha256 of the sorted record_ids joined by `\n`).
* `substeps` — per asset: sub-steps seen, `total`, `last_index`, `first_at`/`last_at`, `elapsed_seconds`, and per sub-step `seconds_since_previous` (differences of **log-entry times**; the `asset.substep` event itself carries no duration); plus `last_substep` (asset, key, index, total, time) for the newest.

**Honest nulls (N.8).** A line that cannot be read as what it claims (truncated, cut in its prefix, wrong schema, missing or mistyped field) adds to `unreadable_lines`, and then `record_count`, `counts_by_kind_reason` and `records_by_event_class` are **null** (never zero, never the readable part standing in for the whole); the readable part is still given as `record_count_lower_bound` / `counts_by_kind_reason_lower_bound`. The same applies to a `truncated` read and to an empty read (an empty read may be retention or ingestion lag, not a measured zero). A later page that fails refuses the whole record (never page 1 alone). The two reconciliation flags are null unless the count is exact. A summary whose JSON parses but whose `records` is not a count keeps its other fields and reads `records` null. A sub-step time that cannot be read makes the seconds that depend on it null, and `last_substep` null. Output order is total (entries sorted by time, then `insertId`), so equal log content gives an equal record whatever order gcloud returned time ties in. Reading is newest-first, so `last_substep` stays the true newest even when `truncated`; per-asset `substeps_seen` / `first_at` / `elapsed_seconds` are then lower bounds.

(I) INTERPRETATION: `asset.substep` events reach the job log as `[event] <json>` only when the job runs without `PUBSUB_TOPIC` (events.emit_event); with it set they go to Pub/Sub and `substeps` is empty — reported as empty, not as "no sub-steps ran". The log shapes were read from the repo's emitters, not from a live log; the first real run is the proof. Schema kept at `/1` because the change is additive (a new key, null by default).

## Metrics (`--metrics true`, only with `execution`; SR-BOLD-09)

`--metrics` without `--execution` is refused before any cloud call. Two further fixed calls, `gcloud monitoring time-series list` on the same gcloud identity (no new credential), one per metric type, each filtered to `resource.type="cloud_run_job"`, the job and the region, over the execution's own window: its `startTime` to its `completionTime` (to now while it still runs; `window.end_is_now`). Metric types recorded in the record: `run.googleapis.com/container/cpu/utilizations` and `run.googleapis.com/container/memory/utilizations` (distributions of the fraction of the container's limit). The execution is identified by that window, not by a metric label (a concurrent execution of the job would be pooled in; `scoping` says so).

Per metric: `status` (`OK` · `ABSENT` = nothing sampled in the window · `UNREADABLE` = a point that is not a well-formed distribution · `QUERY_FAILED` = gcloud's exit status only, never its stderr · `NOT_QUERIED` = no readable start time), `series`, `points`, `samples`, `mean` (sample-weighted), `p95` (pooled bucket counts, linearly interpolated inside its bucket; null when the points use different bucket layouts or it falls in an open end bucket) and `max_upper_bound` (the upper edge of the highest non-empty bucket — a bound on the peak, not a sample maximum; null when that bucket is open). Everything that cannot be read is **null, never zero**. CPU adds `allocated_vcpus` (the job's `cpu`), `mean_vcpus`, `p95_vcpus` and `shape`: `SINGLE_THREAD_BOUND` (p95 within 0.8–1.25 vCPU and mean ≥ 0.5 vCPU, with more allocated), `BURSTY_AT_ONE_VCPU` (same p95, mean below 0.5), `SATURATES_ALL_VCPUS` / `SATURATES_ALLOCATION_ONE_VCPU` (p95 ≥ 85 % of the allocation), `BELOW_ONE_VCPU`, `MULTI_THREAD_PARTIAL`; `shape` is null unless mean, p95 and the allocation were all read. Memory adds `peak_bytes_upper_bound` (bound × the job's memory). `wait` is `NOT_EXPOSED`: Cloud Run publishes no database or container wait metric.

(I) INTERPRETATION: the `gcloud monitoring time-series list` flags and the Distribution JSON shape were read from the Monitoring API reference, not from a live call; a different shape reads `UNREADABLE` / `QUERY_FAILED` (null), never a guess, and the first real run is the proof. (I) INTERPRETATION: the executor table (`executor_ops.json`) is not edited here; until `metrics` is added to this kind's `allowed_args` by its enablement path, the executor refuses the argument and the leg is reachable only by running the script directly.

## Corpus evidence — precisely what exists

* **Exists:** `Dockerfile.pipeline` downloads the Swiss Ephemeris files and runs `sha256sum -c` on `sepl_18.se1`, `semo_18.se1`, `seas_18.se1`; a mismatch fails the build, so no image is pushed. `sefstars.txt` and `seleapsec.txt` are downloaded but **not** checksummed. Combined with the tag→commit tie above, the evidence is: *the Dockerfile at `provenance.image_commit` pins these digests, and CI built the tag from it.* The record names where to read this (`corpus.build_gate_read_at`); the signer runs `git show <image_commit>:platform/python-sidecar/Dockerfile.pipeline` and compares the three pinned digests with the local pinned corpus (`/Users/Dev/kalayantra/ephe`).
* **Does not exist:** any measurement of the corpus *inside the deployed image*. No image label, registry field or Cloud Run field records it, and reading it means running the image. The op therefore reports an honest null rather than a pass.
* **Smallest reviewed way to close it (proposal — not done here, because it changes a production image build and would move the digest mid-J-2a):** (1) in `deploy.yml`'s re-point step add `--update-labels=commit-sha=${DEPLOY_SHA}` (the services' scheme), which this op already reads and cross-checks; (2) in the same job, after the push, add a CI step that runs the pushed image once with `--entrypoint sha256sum` over `/app/ephe/*` and fails the deploy on a mismatch with the three pinned digests, and record the result as a job label (`ephe-ok=<first 12 hex of the digest list>`). With (1) the commit tie no longer rests on the tag alone; with (2) the corpus is measured in the deployed bytes at deploy time.

## Not proven by this op

The image digest at the moment an execution *started* (the execution record carries the reference as launched, not a resolved digest — `image_reference_equals_job` compares references only); who pushed the tag; the corpus in the running container; the database effects of the run (use `readback_sql`); log lines past Cloud Logging retention, and (when `truncated` is true) entries older than the 60,000 read.

## Shape caveat

(I) INTERPRETATION — no live gcloud response was captured for this build. The parser reads the Cloud Run v1 shapes the repo already reads (`spec.template.spec.template.spec.containers[0].image`, `deploy.yml`; `status.conditions` / `succeededCount` / `taskCount` for an execution, `gochara_seal_execution_check.py`; `image_summary.digest`, `gochara-verification-job-deploy.yml`). A different shape **refuses**, never guesses. Fixtures under `tests/fixtures/cloudrun_readback/` are shaped from those paths, not captured. If the first real run refuses on shape, the receipt's `reason` names the field; fix the parser, do not hand-edit the receipt.
