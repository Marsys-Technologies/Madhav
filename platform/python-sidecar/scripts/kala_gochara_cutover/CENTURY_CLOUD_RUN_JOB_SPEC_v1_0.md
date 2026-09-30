# CENTURY CLOUD RUN JOB SPEC v1.0 — Pravāha A2.4

**Status:** SPEC (the build itself is A2.5, gated on D-CLOUD + A2.3). Nothing here
runs a century enumeration; ADK-0028 prohibits local century enumeration and this
document changes no runtime behaviour.
**Scope:** chart `482012f1` ONLY (ADK-0029). Generation label `'4.1'` (chart-1
`'4.0'` is burned — ADK-0027 §1/§4). Horizon `[1984-02-05, 2084-02-05)` (f0p2
evidence step 1; no narrowing ruling exists). Candidate only — never published
without D-FLIP.

## 1. Vehicle

`brahma-build-pipeline-job` (Cloud Run Job, `asia-south1`, project
`madhav-astrology`), the governed build path — the deploy pipeline re-points it at
`brahma-pipeline:$DEPLOY_SHA` with:

- `--memory=16Gi --cpu=4 --task-timeout=86400` (deploy.yml; the 16Gi raise was
  F-185: **`/tmp` is RAM-backed tmpfs on Cloud Run — there is NO disk volume**),
- service account `data-plane-builder-runtime@…`, `DATABASE_URL` from
  `data-plane-builder-db-url:latest`.

The job's stock entrypoint is the pipeline orchestrator (`--build-id --chart-id`),
which has no century-enumeration asset. The century build therefore runs as a job
execution with a **container override** (the Jobs API `Overrides` mechanism
jobInvoker.ts already uses for args): entrypoint `python`, command chain per §3.
A2.5 must use `gcloud run jobs execute … --overrides` (or a first-class
orchestrator asset if one is registered by then — an A5.x concern); either way the
execution is the Cloud Run job, never a local run.

## 2. Streaming payloads — the memory design

Constraint math (risk register §8): pre-T0-G, ~13.5M episodes per century; the
Tier 0-G `global_boundary_table` fix (A2.1, `59a1d625d`) removed the duplicated
boundary SOLVES (1.21M of 1.35M per decade were duplicates), but the per-target
attachment rows still exist pre-dedupe, so the cross-body in-memory list at
century scale stays O(10⁷) rows — 16Gi RAM, no disk. The design that fits:

1. **Per-body chunks.** `step06_enumerate_episodes.py --bodies` (M-3/R7: the
   eight non-Moon grahas `Sun Mercury Venus Mars Jupiter Saturn Rahu Ketu`;
   validation rejects unknowns/dups — RE-VERIFIED 2026-09-30 against
   PERSISTED_BODIES) exists precisely for this: dedupe groups and §3.2 contact
   ids include the body, so per-body payloads concatenate exactly.
2. **One execution, looping bodies, streaming to GCS.** Per body: enumerate →
   sort → append NDJSON to `gs://<build-artifacts>/kala_gochara/482012f1/4.1/
   episodes/<body>.ndjson`, then free the list. Per-body peak ≈ (13.5M/8)
   dicts ≈ 2–4 GiB — fits the 16Gi task with headroom; nothing century-scale
   ever touches `/tmp`.
3. **One candidate build** (`step06_candidate_build.py`) reading the
   concatenated stream, single transaction, `publish_candidate` +
   `write_contacts` + `write_coverage` — the candidate-generation write path
   unchanged.

### Required code/infra changes BEFORE A2.5 (pre-flight checklist, none exist yet)

- [ ] step06: `--episodes-ndjson-out` streaming write (per-body append, no
      century-scale list; per-body sort preserves the canonical ordering the
      content digest depends on). The monolithic `--episodes-out` stays for
      decade-scale rehearsals.
- [ ] step06_candidate_build: accept `--episodes-ndjson` (streamed read).
      DB-direct per-body appends were REJECTED: `publish_candidate`/
      `write_coverage` are once-per-manifest and PK/duplicate semantics make
      8 partial builds dishonest; one build from the complete stream is the
      honest shape.
- [ ] GCS build-artifacts bucket + write grant for
      `data-plane-builder-runtime@…` (precedent: `madhav-marsys-sources` via
      `google-cloud-storage` in the sidecar image). Bucket choice is a native
      infra decision — flagged here, not assumed.
- [ ] Ephemeris `.se1` files present in the job image (the local harness pins
      `/Users/…/.run/se1` with sha256s; the job image must carry the same
      pinned set — verified as part of A2.5 pre-flight).

## 3. Execution chain (per A2.5 run)

```
gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 \
  --overrides=<container: python scripts/kala_gochara_cutover/
               century_run.py --chart-id 482012f1 --generation 4.1 \
               --horizon-start 1984-02-05T00:00:00+00:00 \
               --horizon-end 2084-02-05T00:00:00+00:00>
```

where `century_run.py` (to be written with the checklist items) loops
PERSISTED_BODIES: step06 (`--bodies <b>`, NDJSON stream out) → then the single
candidate build → `step06b_windows_projection.py` → report. Exit codes
propagate per step (§12.9 stale-overlay refusal = 7; publish refusal = 6).

Resume rule: a failed execution leaves a `candidate` manifest at worst
(`_require_not_published` already protects anything published); re-run is a
fresh build of the same generation label — candidate rows are replaced, never
edited in place (N-7).

## 4. Gates this spec does NOT touch

Link-2, flip gates b/c, checks a–k, PRAMĀṆIN verification and the benchmark
metrics report (`pravaha metric`: wall time, physical roots, Swiss calls,
coverage, unresolved spans) are **A2.6**, after the A2.5 run. The flip is J2
under D-FLIP. The ga_strength rebuild remains unauthorised (native ruling
2026-09-29).
