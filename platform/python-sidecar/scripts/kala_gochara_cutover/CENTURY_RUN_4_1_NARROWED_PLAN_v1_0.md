# CENTURY RUN '4.1' — NARROWED-HORIZON PLAN v1.0 — Pravāha A2.5

**Status:** PLAN, pending steward verification of the exact command, then D-CLOUD-gated
execution. Nothing here runs until the steward confirms; the job executes on Cloud
Run only (ADK-0028 — no local century-scale build), candidate rows only, never flipped.
**Supersedes the horizon scope of `CENTURY_CLOUD_RUN_JOB_SPEC_v1_0.md` §0** per the
native ruling below; the spec's streaming design is retired with #2768 (closed
unmerged — its streaming code is not revived).

## 0. The ruling (steward M20260930T135600-d63b, 2026-09-30, native ruling)

> Native ruling: '4.1' (A2.5) is NARROWED to the scored horizon 1998-01-01→2026-04-17
> — exactly the evaluation protocol's horizon — built with the EXISTING reviewed
> enumeration + candidate-build path (current main, after #2764) as a Cloud Run job
> run, candidate rows only for 482012f1 generation '4.1', never flipped. #2768 is
> closed unmerged (branch kept for reference); do not revive its streaming code.

Plan steps per the ruling: (1) job invocation (this document §2–§4); (2) pre-run
checklist incl. the candidate-only guard and the post-run completeness check (§5);
(3) `pravaha report --ref A2.5` with the exact command; the steward verifies, then
the run executes.

## 1. Horizon derivation

Evaluation protocol scored horizon (`event_registry_v2_3.json`): start
`1998-01-01`, end `2026-04-17` inclusive, H = 10,334 days.
`(2026-04-18 − 1998-01-01) = 10,334` days exactly, so the end-EXCLUSIVE bound the
enumerator takes is **`2026-04-18T00:00:00+00:00`**. Steward to confirm this
boundary reading at verification time; it is the only reading consistent with H.

- `--horizon-start 1998-01-01T00:00:00+00:00`
- `--horizon-end   2026-04-18T00:00:00+00:00`

## 2. Vehicle — why a dedicated job

`brahma-build-pipeline-job`'s image ENTRYPOINT is `python -m pipeline.orchestrator.main`
(--run-id only; F4.b/SM-R-11 forbids no-args dispatch). Job *execution* overrides
carry only `args`/`env` (verified against `gcloud run jobs execute --help` and
`gcloud beta …`: `--args`, `--update-env-vars`, `--tasks`, `--task-timeout` — no
command override; the v2 Jobs API `ContainerOverride` likewise has no `command`
field, and `jobInvoker.ts` uses args only). The A2.4 spec's assumed
"entrypoint python + command chain" override is therefore **not implementable** as
written. The governed vehicle is a dedicated deploy-managed job:

- **`brahma-gochara-century-job`** (asia-south1, project madhav-astrology), created
  and re-pointed by `deploy.yml` alongside the pipeline job, same image
  `brahma-pipeline:$DEPLOY_SHA`, SA `data-plane-builder-runtime@…`, secret
  `DATABASE_URL=data-plane-builder-db-url:latest`, `--memory=16Gi --cpu=4
  --task-timeout=86400 --max-retries=0` (a failed run is inspected, never
  auto-retried; resume = a fresh execution rebuilding the candidate, N-7).
- Container command: `/bin/sh
  /app/platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh`
  (committed, reviewable; parameters pinned in the script — chart, generation,
  horizon are NOT env-overridable).

## 3. Execution chain (what the script runs)

1. Step 0 (fail closed): sha256-verify `/app/ephe` `sepl_18/semo_18/seas_18.se1`
   against the Dockerfile.pipeline pins, presence/size-floor the aux files, and
   assert Sun/Moon/Saturn compute with the SWIEPH backend bit (never Moshier —
   F-14: the returned retflag, not the requested flag). Any failure exits 1
   before any solve or DB touch.
2. `step06_enumerate_episodes.py` — all `PERSISTED_BODIES` (8 non-Moon grahas; Moon
   stays on-demand per M-3/R7), orb 5.0 (M-1), refine on, `--ephe-path /app/ephe`
   (image carries the sha256-pinned .se1 set, `Dockerfile.pipeline`), episodes +
   coverage JSON to `/tmp/century_4_1/`.
3. `step06_candidate_build.py` — one transaction: `register_convention` →
   `publish_candidate` → `write_contacts` → `write_coverage` (delete-then-insert
   scoped to (chart, '4.1'), legal only while candidate).
4. `step06b_windows_projection.py` — generation '4.1', baseline '3.0' (the rollback
   surface is untouched).
5. In-script post-run completeness check (§5).

DSN handling (steward amendment 1): the scripts read `DATABASE_URL` from the
environment (`common.resolve_dsn` — `--dsn` is now optional and deprecated for
this path), so the credential never appears on argv or in argparse/usage/error
echo. Error paths print host/port at most (`refuse_production`); the no-DSN error
names neither value.

## 4. The exact command (after the deploy PR merges and the job exists)

```
gcloud run jobs execute brahma-gochara-century-job \
  --project=madhav-astrology --region=asia-south1 --wait \
  --update-env-vars=PRODUCTION_TRANCHE_2_AUTHORIZED=true
```

`PRODUCTION_TRANCHE_2_AUTHORIZED=true` is required because the job's DATABASE_URL
host is a non-loopback private IP, so `common.refuse_production` (step 6 → tranche
2) applies; the script itself exits 4 if the flag is absent. It is passed at
execution time only — the job's standing environment stays clean.

## 5. Pre-run checklist (all must hold; the chain also self-guards)

- [ ] D-CLOUD granted; steward verified the command above.
- [ ] Deploy of this PR has run: `gcloud run jobs describe brahma-gochara-century-job`
      shows image tag == the merge SHA on main and command ==
      `/bin/sh /app/.../century_run_4_1.sh`.
- [ ] Candidate-only guard (read-only, via the validation reader):
      `SELECT status FROM kala_gochara_publication WHERE chart_id='482012f1-…' AND
      generation='4.1'` → no row, or `candidate`. In-path guards: `publish_candidate`
      / `_require_not_published` refuse a published generation (exit 6);
      generations 'v1'/'3.0'/'4.0' rows are never touched (writes are scoped
      delete-then-insert on ('482012f1…','4.1')).
- [ ] §12.9 overlay freshness: the enumerator checks `ka_vedha_gochara`/`ka_moorti_nirnaya`
      fingerprints BEFORE enumerating and exits 7 on stale — if that fires, STOP and
      report; do not force.
- [ ] Ephemeris: step 0 of the runner sha256-verifies the image's `/app/ephe`
      `.se1` set against the Dockerfile.pipeline pins and asserts the SWIEPH
      backend before enumeration; any mismatch fails the execution closed.
- [ ] Memory: see §6 estimate. If the task OOMs, STOP, report the measurement —
      the per-body fallback (`--bodies` loop + concatenation; the dedupe contact
      ids include the body, so payloads concatenate exactly) is the documented
      next step, not a silent retry.
- [ ] No flip: step07/step08 are not part of this chain; D-FLIP is reserved.

## 6. Memory estimate (16 Gi task, /tmp is RAM-backed — F-185)

- Reviewed evidence basis: pre-T0-G decade run ≈ 1.35M episodes; century-scale RSS
  estimated 20–30 GB ⇒ ~1.5–2.2 KiB per in-memory episode dict
  (`f0p2_horizon_parity_evidence.md`). The T0-G `global_boundary_table` fix removed
  duplicate boundary *solves*; per-target attachment rows remain pre-dedupe, so the
  payload stays O(rows) ∝ horizon length.
- Narrowed horizon = 28.29 y ⇒ worst case ≈ 0.2829 × 13.5M ≈ **3.8M episodes**.
- Enumeration peak ≈ 3.8M × 1.5–2.2 KiB ≈ **5.5–8.2 GiB**, plus the `json.dumps`
  serialization buffer and the ~1.5–2 GB `/tmp` JSON files (RAM) ⇒ worst ≈
  **11 GiB < 16 Gi**. Candidate-build peak ≈ parsed episodes (≈ 5.5–8 GiB) + write
  buffers ⇒ < 10 GiB. Both steps fit with ≥ 5 Gi headroom; the ruling's
  measurement-before-running clause is not triggered by this estimate.

## 7. Post-run completeness check (in-script, fails the execution on mismatch)

- `kala_gochara_contacts` rows for (chart, '4.1') grouped by **body** and by
  **relation** must equal the episodes-JSON counts exactly; totals must match.
- The '4.1' manifest must exist with `status='candidate'` (anything else → exit 1).
- Printed line carries `manifest.row_counts` and the coverage row count for the
  evidence packet (A2.6 collects the benchmark metrics: wall time, physical roots,
  Swiss calls, coverage, unresolved spans — `pravaha metric`).

## 8. Out of scope (unchanged)

ga_strength rebuild (unauthorised), any flip (J2/D-FLIP), chart 1c826d5a, 'v1'/'3.0'
rows, the retired streaming code path, and the A5.x registered-writer substrate.
