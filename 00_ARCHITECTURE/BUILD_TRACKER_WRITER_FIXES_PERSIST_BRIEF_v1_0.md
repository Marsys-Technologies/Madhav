---
artifact: BUILD_TRACKER_WRITER_FIXES_PERSIST_BRIEF_v1_0.md
canonical_id: BUILD_TRACKER_WRITER_FIXES_PERSIST_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
purpose: Persist the ga_sensitive + ga_nakshatra writer fixes (applied via the LOCAL orchestrator) into main AND the Cloud Run job image, so cloud builds stop reverting to the old crashing code.
audience: Claude Code (Antigravity)
---

# Persist the writer fixes — "what ran locally must run in the cloud"

## §0 — Why this is urgent (the trap)
The Gaṇita layer was lit for 1c826d5a by running the **local** orchestrator
(`run_abhinandan_sensitive_nakshatra.py`). But production builds execute on **GCP Cloud Run**
(`brahma-build-pipeline-job`, asia-south1). If the two writer fixes are not committed AND the Cloud
Run job image is not rebuilt from that commit, the next cloud-triggered build silently runs the OLD
code and re-introduces the fatal halts — making the lit layer unreproducible. Web-app deploys do NOT
rebuild the job image; it is a separate build (the `job_image_tag` surfaced in the runs response).

## §1 — The two fixes to persist
1. **ga_sensitive** — AK-divergence fatal `ValueError` halt → `logger.warning` (one divergent value
   no longer aborts the asset). Writer module under
   `platform/python-sidecar/pipeline/orchestrator/writers/` (ga_sensitive).
2. **ga_nakshatra** — two `KeyError: 0` crashes in `_fetch_bg_nakshatra` and the cross-ayanamsha
   step, from psycopg `dict_row` cursors accessed as tuples → explicit dict-row cursor + key-name
   access at BOTH sites.

## §2 — PASTE TO CLAUDE CODE
```
Persist two writer fixes that were applied/validated via the LOCAL orchestrator into main and the
Cloud Run job image. Confirm the working tree holds these changes (git diff) in the ga_sensitive and
ga_nakshatra writer modules under platform/python-sidecar/pipeline/orchestrator/writers/.

1. SCOPE CHECK: git status + git diff. Confirm ONLY the intended writer changes (ga_sensitive halt→
   warning; ga_nakshatra two dict_row fixes) plus, if present, run_abhinandan_sensitive_nakshatra.py.
   If run_abhinandan_sensitive_nakshatra.py is a throwaway one-off, do NOT commit it (or move it under
   scripts/ if it's a reusable per-chart runner). Flag anything unexpected and STOP if unclear.

2. TESTS: run the python-sidecar test suite for these writers (pytest for ga_sensitive + ga_nakshatra,
   plus any orchestrator writer-discovery test). Add a regression test for each fix if none exists:
   - ga_sensitive: an AK-divergence input produces a warning + a completed WriterResult, NOT a raise.
   - ga_nakshatra: a dict_row-backed fetch path returns rows by key without KeyError: 0.
   Run typecheck/lint as configured. All green before committing.

3. COMMIT to main:
   fix(ga-writers): ga_sensitive AK-divergence warns not halts; ga_nakshatra dict_row cursor access
   Report the commit SHA.

4. JOB IMAGE REBUILD (the critical step): rebuild + push the brahma-build-pipeline-job image from the
   new SHA, NOT just the web app. Use the established job-image build path (the brahma-pipeline repo /
   Cloud Build / Artifact Registry tag — image asia-south1-docker.pkg.dev/madhav-astrology/amjis/
   brahma-pipeline:latest per memory reference-brahma-pipeline-orchestrator). Then update the Cloud Run
   Job to the new image if it doesn't auto-pick latest. Report the new image digest/tag.

5. VERIFY parity: trigger a NO-OP or single-asset cloud build for 1c826d5a and confirm the runs
   response job_image_tag matches the image you just pushed (commit SHA / digest). This proves the
   cloud now runs the fixed code. Do NOT do a destructive rebuild here — a single already-lit asset
   with action!='rebuild' will skip cleanly; that's enough to read job_image_tag.

CONSTRAINTS: 1c826d5a only for any build trigger; never native 482012f1. Deliver: git diff summary,
test results, commit SHA, new job image tag/digest, and the runs-response job_image_tag proving parity.
STOP and report.
```

## §3 — Done when
Both fixes are committed to main, the Cloud Run job image is rebuilt from that SHA, and a cloud build's
`job_image_tag` provably matches — so a cloud-triggered Gaṇita build of 1c826d5a reproduces the lit
layer without the old `ValueError` / `KeyError` halts.
