---
artifact: CLAUDE_CODE_PROMPT_REROUTE_HEAVY_BUILD_TO_CLOUD.md
canonical_id: CLAUDE_CODE_PROMPT_REROUTE_HEAVY_BUILD_TO_CLOUD
version: 1.0
status: READY — kill the local ga_dashas run, reroute heavy writers to a Cloud Run Job (in the provisioned cloud, raised timeout), re-run + verify. The durable heavy-build fix for L1/L2/L3.
authored_by: Cowork 2026-06-24
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — fixes the heavy-build EXECUTION PATH (was local-standalone-over-proxy; native provisioned cloud for this).
native_decision: "Kill the local run, restart as a cloud job with raised watchdog timeout. We're paying for cloud infra; heavy builds must run THERE, not on the local machine over the proxy."
---

# Reroute Heavy Builds to the Provisioned Cloud (Cloud Run Job, raised timeout)

> The ga_dashas rebuild is grinding ~10h LOCALLY over the Cloud SQL proxy because the standalone script
> bypassed the orchestrator's Cloud Run Job to dodge the 30-min watchdog. WRONG path. Native provisioned a
> cloud server for exactly this. Fix: run heavy writers as a Cloud Run Job (in-cloud, near the DB, no proxy
> hop) with the watchdog timeout RAISED — fast AND survives long runs. This is the durable pattern for
> L1's ga_dashas + ga_sensitive, L2 rebuild, and L3's heavier convergence rebuild.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Reroute the heavy-writer rebuild
from the slow LOCAL standalone path to the provisioned CLOUD (a Cloud Run Job with a raised timeout).
Native decision: stop running heavy writers on the local machine over the Cloud SQL proxy; run them IN the
cloud. Chart = 482012f1-710e-4a25-994a-93821f5871aa. DATA-FIRST verification throughout.

### STEP 0 — Measure CPU-bound vs I/O-bound on the CURRENT local run (settle the "will cloud help?" question)
Before killing it, check PID 48701's CPU usage (top/ps). REPORT: is it CPU-bound (CPU pegged ~100% → the
ephemeris math is the cost → cloud helps modestly) or I/O-bound (low CPU, waiting → the proxy round-trips
are the cost → cloud is DRAMATICALLY faster)? Either way we proceed to cloud (the architecture is wrong),
but report which it is so we know the expected speedup. (If clearly I/O-bound, the reroute is a big win;
if CPU-bound, set expectations that cloud is correct-but-not-magic.)

### STEP 1 — Kill the local run cleanly
Stop PID 48701. Note: the standalone script is NOT restart-safe (pre-cleanup full-DELETEs on startup), and
we're moving to a new path anyway, so the ~3-4h of local progress is sacrificed by design. Confirm the
process is stopped; leave chart_dashas as-is (the cloud re-run will handle cleanup).

### STEP 1.5 — ⚠️ DEPLOY THE FIXED CODE TO THE JOB IMAGE FIRST (BLOCKING — do not skip)
**A Cloud Run Job runs a pre-built CONTAINER IMAGE, not your live source files.** The local standalone
script worked because it ran your SOURCE directly (with the ga_dashas fix). The cloud job runs whatever
image was last deployed — which does NOT contain the fix (the new code was never deployed). If you run the
cloud job on the stale image, it will faithfully rebuild the OLD BROKEN DATA over ~10h and report success —
a 10-hour, plausible-green, totally-wrong run. PREVENT THIS:
1. CONFIRM the gap: `gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1
   --format='value(spec.template.spec.template.spec.containers[0].image)'` → note the image + its build SHA;
   does it predate the ga_dashas fix commit? (Almost certainly YES = stale.)
2. BUILD + PUSH a new image from current main (the fixed code) to the registry
   (asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:latest or the job's image path) —
   the same build the deploy pipeline does. Confirm the build includes the ga_dashas + ga_sensitive fixes.
3. UPDATE the job to the new image: `gcloud run jobs update brahma-build-pipeline-job --region=asia-south1
   --image=<new-image>`.
4. VERIFY: re-describe the job; its image SHA now == the fixed-code commit. Only then proceed.
**Do NOT run the job until its image contains the fix.** (The Step-4 JOIN gate would catch stale code — it'd
fail for 3/5 ayanamshas — but don't burn 10h to discover that; deploy-first makes it right the first time.)

### STEP 2 — Wire the heavy writer to run as a CLOUD RUN JOB with raised timeout
The orchestrator's normal path is the Cloud Run Job `brahma-build-pipeline-job` (asia-south1) — it runs
IN the cloud next to the DB (no proxy hop). The reason we bypassed it was the 30-min watchdog. Fix that,
don't bypass it:
- Confirm/raise the Cloud Run Job task timeout to handle a ~10h+ run (precedent: it was raised to 86400s
  /24h for the earlier convergence work — verify it's still set, or re-raise:
  `gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1
   --format='value(spec.template.spec.template.spec.timeoutSeconds)'`; raise via
  `gcloud run jobs update ... --task-timeout=86400` if needed).
- Identify the in-job watchdog that killed the writer at 30 min (the `state='building'` → TS watchdog).
  Raise/disable it FOR HEAVY WRITERS specifically (a per-writer or per-run timeout override) so a legit
  10h run isn't killed — WITHOUT removing the watchdog's protection against genuinely-stuck builds (e.g.
  a heartbeat-based watchdog that resets on each committed substep, rather than a flat 30-min wall).
- Ensure the cloud job runs the SAME fixed writer code (the canonical-ayanamsha-vocab fix must be deployed
  to the job's image — confirm the job image == current main, or deploy it first).
- **Make the cleanup RESUMABLE (the L3-hardening, do it now):** replace the standalone script's blanket
  `DELETE FROM chart_dashas WHERE chart_id=%s` with a TARGETED stale-purge
  `DELETE WHERE ayanamsha_id IN ('lahiri','kp','surya_siddhanta')` + rely on the per-substep
  `replace_prior_chart_dashas()` idempotency. Now a restart resumes instead of re-running from zero. (This
  is required before L3's heavier rebuild anyway — do it here.)

### STEP 3 — Run ga_dashas as the cloud job; verify it's faster + commits correctly
Launch the cloud job for ga_dashas. Confirm: it runs in-cloud (not local), commits per-substep (rows appear
in chart_dashas), ends `state='lit'` with real rows in asset_throughput (NOT a silent direct-runner bypass —
it must report build state correctly). Report the cloud run's wall-clock vs the local ~16min/substep — the
speedup confirms (or refutes) the proxy-latency diagnosis.

### STEP 4 — Then the original L1 in-data verification (unchanged — the gate is the same)
Once ga_dashas completes in-cloud:
  -- canonical labels: SELECT DISTINCT ayanamsha_id FROM chart_dashas WHERE chart_id='482012f1-...';
  -- THE gate: dasha↔chart_facts JOIN returns rows for ALL 5 ayanamshas (confirm the fact_subject
  --   ayanamsha-suffix convention first, adjust the JOIN key; expect 5 ayanamshas, comparable non-zero counts):
  SELECT d.ayanamsha_id, count(*) FROM chart_dashas d JOIN chart_facts f
    ON f.chart_id=d.chart_id AND f.fact_subject LIKE '%_'||d.ayanamsha_id
    WHERE d.chart_id='482012f1-...' GROUP BY 1 ORDER BY 1;
  -- 7 systems present, non-collapsed counts.
Then ga_sensitive via the same cloud-job path; verify ~5,166 rows + distribution census.
Then re-confirm L1 headline gates (Rahu/Ketu exalted/1.0 ×5, ga_yoga 36/36, FORENSIC 7/7).
Seal L1 IN DATA (update L1_SEAL + map §3) only when all gates verify.

### STEP 5 — Document the cloud heavy-build pattern (the durable outcome)
Record the cloud-job heavy-build path (raised/heartbeat timeout + resumable targeted-cleanup) as THE way to
run heavy writers — retire / deprecate the local standalone-over-proxy script for heavy builds. L2 rebuild
+ L3 convergence rebuild use this path. This removes BOTH the watchdog-kill problem AND the proxy-latency
problem in one fix.

STOP after L1 seals in-data — do NOT start L2. Report: the CPU-bound/IO-bound finding, the cloud run's
speed vs local, the JOIN gate (all 5 ayanamshas), and the documented cloud pattern.

---
*End. Kill the slow local run; run heavy writers as a Cloud Run Job in the provisioned cloud (near the DB,
no proxy) with a raised/heartbeat watchdog + resumable targeted-cleanup — fast, long-run-safe, restart-safe.
Fixes the execution path for L1/L2/L3. Then the same L1 in-data gate. Measure CPU vs I/O first to confirm
the speedup. NO L2 until L1 seals in-data.*
