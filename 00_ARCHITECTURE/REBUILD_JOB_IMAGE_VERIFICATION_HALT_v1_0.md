---
artifact: REBUILD_JOB_IMAGE_VERIFICATION_HALT_v1_0.md
canonical_id: REBUILD_JOB_IMAGE_VERIFICATION_HALT
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
severity: HIGH — prevents rebuilding on stale orchestrator code
purpose: >
  HALT the in-flight 1c826d5a rebuild and PROVE, before any further asset rebuilds, that the Cloud Run
  job image actually carries the ga_positions + ga_sensitive fix commits, AND that the already-rebuilt
  first asset (ga_positions) came out correct. Localhost only TRIGGERS; the compute + DB writes run in
  the Cloud Run job image — if that image is stale, the rebuild silently re-bakes the OLD logic.
audience: Claude Code (Antigravity)
---

# Halt + verify: is the rebuild actually running the fixed code?

## §0 — The risk (native raised it — it is valid)
The rebuild is triggered from localhost, but ALL compute + DB writes happen in the Cloud Run job
`brahma-build-pipeline-job`, which runs whatever code is baked into its container image. Committing the
fix to `main` and even deploying the WEB app do NOT rebuild the job image — that is a separate build.
So if the job image predates the fix commits, the rebuild is running OLD logic and re-baking the
contamination / AK bug. We must prove the image is current BEFORE rebuilding anything else. Do NOT
rebuild on faith.

AMBIGUITY TO RESOLVE (do not assume): one project note says the `deploy-web` job on push→main ALSO
deploys the pipeline-job image (which would make a merged fix auto-live). But the Phase-3 report showed
the job image rebuilt as a SEPARATE deploy that moved twice (424cb3f9 → c47d6753). So whether push→main
reliably bakes the job image is UNCERTAIN — §2 resolves it empirically by reading the actually-deployed
image and mapping it to a commit. Trust the deployed digest, not the CI theory.

Fixed commits that MUST be in the job image:
- ga_positions contamination fix (adapter passes birth_params; writer refuses NATIVE_BIRTH for
  non-native).
- ga_sensitive KN-Rao AK reckoning fix (Rāhu reverse-degree).

## §1 — STEP A: HALT the in-flight build (do this first, read-state then stop)
1. Identify the active run for 1c826d5a:
   `SELECT id, state, action, plan, started_at FROM build_runs
      WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a'
        AND state IN ('planned','running','paused') ORDER BY started_at DESC LIMIT 1;`
2. PAUSE it (not stop — preserve progress) via the cockpit control or
   `POST /api/cockpit/runs/[id]/pause`. Confirm build_runs.state='paused'. Record which assets already
   completed (`SELECT asset_id, state FROM build_run_assets WHERE run_id=<id> ORDER BY position;`).
   Note: the orchestrator checks pause between assets, so an in-flight asset finishes first — that's
   fine; we just stop NEW assets starting on a possibly-stale image.

## §2 — STEP B: prove the JOB IMAGE carries the fix (image-SHA check)
The job image, project, region, job name (from platform/src/lib/cloud_run/jobs.ts):
project=`madhav-astrology`, region=`asia-south1`, job=`brahma-build-pipeline-job`, and the deployed
image is `job.template.containers[0].image` (tag convention `…:<commit-sha>`).
1. Read the deployed image:
   `gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1 --project=madhav-astrology \
      --format='value(template.template.containers[0].image)'`
   Record the full image ref + its tag/digest.
2. Map image → source commit. The tag is typically the short commit SHA; if it's `:latest` or a digest,
   resolve the digest to the build that produced it (Cloud Build history / Artifact Registry:
   `gcloud artifacts docker images describe <IMAGE_REF> --format='value(image_summary.digest)'` and the
   build provenance / labels). Determine the exact git commit baked into the running image.
3. Assert that commit CONTAINS both fix commits: `git merge-base --is-ancestor <ga_positions_fix_SHA>
   <image_commit>` and same for the ga_sensitive fix SHA (or `git log <image_commit>` shows them).
   - If BOTH fixes are ancestors of the image commit → image is CURRENT (capability proven). Continue.
   - If EITHER is missing → image is STALE. HALT. The rebuild so far ran old code. Do NOT resume.
     Rebuild + push the job image from a SHA containing both fixes (see §5), then restart the rebuild
     from ga_positions (the already-done assets are suspect and must be redone on the correct image).

## §3 — STEP C: prove the OUTPUT is correct (data check on the already-rebuilt asset)
Image capability is necessary but not sufficient — prove the first rebuilt asset actually produced
correct data. ga_positions is the root asset and the contamination canary.
`SELECT fact_subject, fact_key, fact_value FROM chart_facts
   WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a' AND fact_category='graha_position'
     AND fact_subject IN ('SUN','MOON','LAGNA') ORDER BY fact_subject, fact_key;`
ACCEPTANCE (Abhinandan's real chart, NOT the native's):
- SUN  → ~318° Aquarius / Shatabhisha (NOT 291.96° Capricorn = native)
- MOON → ~73° Gemini / Ardra (NOT the native's Purva Bhadrapada)
- LAGNA→ ~23.5° Aries (NOT the native's 12.4°)
Cross-check the build_id on those rows is the CURRENT rebuild's run, not the old 26bbbd7c.
- If correct → the running image HAS the fix and it executed correctly. Safe to resume.
- If still the native's values → either the image is stale (contradicts §2 → re-check) or ga_positions
  didn't actually rebuild. HALT and report which.

## §4 — STEP D: decide (don't waste compute)
- §2 CURRENT **and** §3 CORRECT → RESUME the paused run (`POST /api/cockpit/runs/[id]/resume`); the
  downstream assets will build on proven-good code + proven-good positions. No wasted work.
- §2 STALE (image missing a fix) → STOP. Rebuild the job image (§5). The already-rebuilt assets ran on
  old code and must be redone — but only AFTER the image is correct, so we don't waste another pass.
- §2 CURRENT but §3 WRONG → STOP and report; something other than the image (e.g. ga_positions skipped,
  birth_params not fetched) is wrong — diagnose before any further rebuild.

## §5 — IF the image is stale: rebuild it (only then)
Rebuild + push `brahma-build-pipeline-job` image
(`asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:latest` + a commit-SHA tag) from a
git SHA containing BOTH fix commits. Confirm via §2 that the new deployed image's commit is an ancestor
test PASS. THEN restart the rebuild from ga_positions on 1c826d5a. Verify §3 acceptance before
continuing downstream.

## §6 — Deliverables + guardrails
DELIVER: the paused-run state + completed-asset list; the deployed image ref + its resolved commit +
the ancestor check for both fixes (CURRENT/STALE); the SUN/MOON/LAGNA data check (CORRECT/WRONG) with
the rebuild's build_id; and the decision taken (resume / rebuild-image-then-restart / diagnose).
GUARDRAILS: read-only until the decision; PAUSE not STOP (preserve progress) until we know; destructive
re-rebuild only on 1c826d5a, never native 482012f1; do not resume on an unproven image. STOP and report
at the decision point.

## §7 — Process note (so this can't recur)
Going forward, EVERY rebuild brief must verify job_image_tag → commit BEFORE triggering, not after. The
runs response already surfaces `job_image_tag`; treat a rebuild whose image commit doesn't contain the
intended fix as a no-op-and-halt, not a build. (Fold into the standing rebuild checklist.)
