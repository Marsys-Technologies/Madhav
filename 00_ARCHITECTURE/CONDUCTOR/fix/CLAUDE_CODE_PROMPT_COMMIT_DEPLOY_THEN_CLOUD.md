---
artifact: CLAUDE_CODE_PROMPT_COMMIT_DEPLOY_THEN_CLOUD.md
canonical_id: CLAUDE_CODE_PROMPT_COMMIT_DEPLOY_THEN_CLOUD
version: 1.0
status: READY — review+commit the ~160 uncommitted changes deliberately, merge/push, DEPLOY the image, THEN run the heavy build from cloud.
authored_by: Cowork 2026-06-24
native_decision: "Address all ~160 uncommitted changes; commit/merge/push; deploy; then run from cloud (not local)."
caution: "Push auto-deploys prod. 160 unreviewed changes committed blindly = risk. SORT before committing — do NOT git add -A everything."
---

# Commit → Deploy → Run-from-Cloud (the correct order)

> Before the cloud heavy-build can run the FIXED code, the deployed image must contain it — which means
> the ~160 uncommitted working-tree changes must be committed + pushed + deployed FIRST. But 160 changes
> committed blindly is dangerous (junk, half-work, a prod migration, the not-restart-safe script could all
> get swept in + auto-deployed). SORT them deliberately. Then deploy. Then run from cloud.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav, branch main, HEAD b87bff79). There
are ~160 uncommitted changes. Get them committed + deployed correctly so the cloud heavy-build runs the
FIXED code — but do it DELIBERATELY, not with a blind `git add -A`. **Note: pushing main AUTO-DEPLOYS prod
(migrate + Cloud Run). So a careless bulk commit could deploy junk or half-finished work.**

### STEP 1 — INVENTORY the ~160 changes (do NOT commit yet)
`git status` + `git diff --stat`. SORT every change into:
- **(A) SHIP — the foundation fixes:** the L0 + L1 writer/migration/test fixes (ga_dashas vocab, the 7
  bypass→read-L0 conversions, ga_yoga parser, ga_sensitive IndexError, bg_dignity_reference Rahu/Ketu +
  Mercury, the guard tests, the L0/L1 seal docs + map updates). These are the point — they MUST ship.
- **(B) JUNK — do NOT commit:** scratch/log files (`console-full.txt` is one — confirm + exclude), debug
  output, temp files, anything not meant for the repo. Add to .gitignore if appropriate.
- **(C) NOT-READY / RISKY — flag for a decision:** half-finished work, experimental code, the
  not-restart-safe `run_heavy_writer_standalone.py` (decide: ship as-is, ship with the resumable-cleanup
  hardening folded in, or leave uncommitted), and ANY `platform/migrations/` or `platform/supabase/migrations/`
  change (high-stakes — auto-runs on prod; READ it, confirm it's intended + correct before shipping).
- **(D) UNRELATED — separate concern:** changes from a different workstream that shouldn't ride along with
  the foundation fixes (commit separately or leave for their own PR).
Report the sorted inventory (counts per bucket + the notable files in B/C/D) BEFORE committing.

### STEP 2 — COMMIT deliberately (grouped, not one mega-commit)
Commit bucket A in logical groups with clear messages (e.g. "fix(l0): Rahu/Ketu exaltation + Mercury
atichara + cross-table guard", "fix(l1): ga_dashas ayanamsha vocab + 7 L0-bypass→read + ga_yoga parser").
Bucket B: do NOT commit (gitignore the junk). Bucket C: commit only what you + the native approved; the
migration especially only after confirming it. Bucket D: separate commits or hold.
**Do NOT `git add -A` blindly.** Stage by path/bucket.

### STEP 3 — Verify CI-clean, then push (this auto-deploys)
Run the test suite / lint to confirm the commits don't break the build (the guard tests must pass; no
net-new failures). Then `git push origin main`. This triggers CI → deploy (migrate + Cloud Run web + the
job image). Watch it go green.

### STEP 4 — Confirm the DEPLOYED IMAGE now contains the fixes (the whole reason for this)
The cloud heavy-build runs the JOB IMAGE. After the push+deploy:
`gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1
  --format='value(spec.template.spec.template.spec.containers[0].image)'`
→ confirm its image SHA == the just-pushed merge SHA (the fixed code). If the deploy pipeline doesn't
rebuild the JOB image (only the web image), explicitly build+push+update the job image to the new code
(per the reroute prompt Step 1.5). **Do NOT run the cloud job until its image SHA == the fixed-code commit.**

### STEP 5 — THEN run the heavy build from cloud (per the reroute prompt)
Now run ga_dashas + ga_sensitive as the Cloud Run Job (in-cloud, near DB, raised/heartbeat watchdog,
resumable targeted-cleanup) per CLAUDE_CODE_PROMPT_REROUTE_HEAVY_BUILD_TO_CLOUD.md. Then the L1 in-data
gate (dasha↔fact JOIN all 5 ayanamshas) → seal L1 in data. NO L2 until then.

### REPORT
The sorted inventory (A/B/C/D); what was committed vs excluded vs held; the migration decision (if any);
CI result; the deployed job-image SHA == fixed-code confirmation; then proceed to the cloud run. STOP and
report at Step 4 (image confirmed) before the long cloud run, so the native confirms the right code is
deployed before 10h of compute.

---
*End. SORT the 160 (ship the fixes / drop the junk / flag the risky migration+script / separate unrelated)
→ commit grouped, not bulk → CI-clean → push (auto-deploy) → CONFIRM the job image SHA == fixed code →
THEN run from cloud. Never git add -A 160 changes blindly into an auto-deploying main.*
