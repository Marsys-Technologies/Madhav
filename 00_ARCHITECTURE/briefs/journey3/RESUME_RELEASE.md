---
version: 2.0
session_id: MADHAV_JOURNEY3_RELEASE_RESUME_20261006
status: DEPLOYED_SCREEN_VERIFIED_WITH_PRE_EXISTING_ENGINE_RESIDUALS
source_pr: https://github.com/Marsys-Technologies/Madhav/pull/3190
source_sha: 64c0a182febe8c48d38c83510e40da7ce8c14bf0
serving_revision: amjis-web-probe-64c0a182febe-37395346947-1
---

# Journey 3 — Chart Preparation release

Journey 3/page14 Nirmāṇa is implemented, protected-merged and deployed. The live screen presents six expandable preparation layers, actual asset counts/statuses, dependencies and truthful readiness, guarded scope previews, and shared chart navigation. Authenticated desktop, measured390×844 mobile, keyboard expansion/collapse and read-only status checks passed. Four pre-existing asset failures remain visible; this release does not qualify or repair those engines.

## Source and protected checks

Owner instruction to implement and deploy persists under CCD-023. Original candidate1b4801932 and earlier blocked release/close are historical. Candidatec0a35f6574868dbb2337cc10534d0fc34a9de374 was reconciled onto accepted Consultation source916d74290a2a, retaining both routes and CCD-022/023. PR3190 merged through the protected queue at2026-10-06T00:18:19Z as64c0a182febe8c48d38c83510e40da7ce8c14bf0. All22 reviewed platform file blobs match the integrated source (RESUME_QUEUE_SOURCE.json).

- Local rebased suite:1,418files,15,695passed,3expectedfail,1,060skipped,2todo, zero unexpected failures;19 focused shared-route/preparation checks also pass. Types:0errors. Lint:0errors,627 inherited warnings.
- Exact-candidate PR quality37385412114, build37385412113, TAP37385412187 and EKV37385412118 succeeded.
- Full protected integrated CI37391352054 and separate exact-source post-merge main CI37393295355 succeeded; all33 active stages passed, census intentionally skipped.
- Scoped manifest fingerprint/root validation passed:131entries, rootb3a4d133bdf628cb. Closing drift has only two LOW local database-connectivity findings, explicitly booked in RESUME_SESSION_CLOSE.yaml. Local schema inspection remains unperformed; no credentials changed.

## Deployment and final runtime

Normal workflow_dispatch37393421080 used existing ci_gate=require-ci-green with already-successful FULL integrated CI for the exact same source64. The workflow's normal exact-SHA CI lookup allows that completed run; no emergency, force, schema override, release-gate edit or cancellation of a production/foreign run occurred. Separate main CI was still running at dispatch and subsequently succeeded. The standard migration runner completed, but newly applied migration count is not separately claimed; Journey3 authored no migration.

Manual deployment37393421080 succeeded and initially served revisionamjis-web-probe-64c0a182febe-37393421080-1. Automatic main-CI follow-up37395346947 then successfully redeployed the same actual pinned source64; its workflow listing head e718a9b15a1d is default-branch metadata, not the pinned DEPLOY_SHA. The final revision isamjis-web-probe-64c0a182febe-37395346947-1, Ready=True and100% desired/observed traffic. Existing limits-canary/web-iam-a/web-iam-b service tags are preserved.

Both serving revisions resolve to the identical linux/amd64 image sha256:8246e7eec1d256b035f9005c834511277ddb9b6a690850c2482958c195886bd2. Final source tag OCI index sha256:e89b09aa1ee0337b50ab0a41ca7fbf4b0eec4238c360e3701c79aac28ed0892e contains that platform manifest (RESUME_FINAL_IMAGE_MANIFEST.txt). Index and platform digests are distinct types and are not compared as equal. Final runtime/source/image/traffic receipts are RESUME_FINAL_SERVICE.json and RESUME_FINAL_REVISION.json; original deployment receipts remain unchanged.

## Live acceptance and limits

Authenticated review used an existing authorized chart. All six layers display real counts; Kāla shows3 existing errors and Mīmāṃsā1. Downstream preparation remains incomplete where dependencies/status require it; an all-assets-lit layer is not presented as unconditional question readiness. Final desktop reload on the last serving revision settled from initial unavailable/loading placeholders into the real loaded status/counts; final screenshot was saved after settling.

All six layers expand and collapse by Enter. Actual measured390×844 mobile layout has no document horizontal overflow with layers collapsed or expanded; asset rows and action labels remain readable. Mobile/keyboard acceptance was performed on the first revision and applies to the final revision's verified identical immutable serving image. Temporary viewport overrides were reset and only the final live page is retained. Action/confirmation behavior also has the earlier fictional-fixture evidence; no Build/Rebuild/Refresh/Pause/Stop/Clear or paid provider/record/permission action was executed live.

Initial runtime observation recorded50 completed preparation/status GETs, all200 and zero5xx; this is a bounded observation rather than an exhaustive traffic audit (RESUME_LIVE_HTTP.json). The final desktop refresh and subsequent revision-specific read-only HTTP receipt are recorded separately. Private real-chart screenshots and identifiers stay outside this Git packet; published UI screenshots in the original source packet are fictional fixtures.

## Closure and independent campaigns

The historical runner-blocked RELEASE.md/SESSION_CLOSE.yaml/log entry are retained verbatim except a forward pointer; they do not describe current production. RESUME_SESSION_OPEN.yaml, RESUME_SESSION_CLOSE.yaml and its scoped validation record describe this resumed release. The own coordination lease is released with the verified live outcome; its remote receipt is RESUME_LEASE_RELEASE.json. Closing state/log/evidence is published separately as a docs-only PR; that publication does not redeploy or qualify engine source.

Shared main now includes independently owned engine PR3176/e718a9b15a1d. Its engine qualification/deployment and Consultation's separate presentation residuals are outside this release. No foreign worktree, engine/writer/orchestrator, real chart data, credentials or permissions were modified. The four existing asset errors and actual build/clear/provider execution retain their separate owner authority.
