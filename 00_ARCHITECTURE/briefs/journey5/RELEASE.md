---
artifact: JOURNEY5_RELEASE
version: 1.1
status: DEPLOYED_READ_ONLY_VERIFIED
---
# Journey 5 protected release

Authority CCD-024; exclusive production lease L-PORTAL-JOURNEY5-PRODUCTION-20261006, verified coordination commit03f028413e028b133149b13e1648fd420067f541, expires2026-10-06T06:21:17Z. Existing normal CI-gated deployment, no protection bypass.

## Recovery readiness

CloudSQL amjis-postgres pre-migration on-demand backup **1791256883782**, status **SUCCESSFUL**, finished **2026-10-06T03:22:44.869Z**. Restore mechanism is CloudSQL backup restore for this instance; no restore was executed. Restoration of the whole shared database is an emergency coordinated operation, not an acceptance test. Additive1310 is compatible with the predecessor app; ordinary code rollback leaves the column and receipt in place.

Refreshed serving predecessor **amjis-web-probe-b7a26ab358cd-37411387504-1**,100%traffic/Ready=true; immutable image **sha256:105529b3b8d764c58ae554cac55d7b7422bbd49656483a9d601e6a783a9e1774**. Its independent release37411387504 succeeded. This supersedes the earlierf50/75eeda pins and preserves the independently owned engine release. Re-read immediately before Journey5 release. Revert only the Journey5 web candidate to this verified predecessor while retaining existing tags if candidate smoke/live checks fail; no unrelated service rollback. Web release health does not certify all engine/provider smoke jobs.

Read-only production preflight confirms profiles, personas and migration tracker owned by the existing amjis_app migration login. account_preferences column and1308/1309 receipts absent before release.1310 source is independently reviewed and reserved;1309 belongs to the released local LEL work and is not part of this candidate.

## Candidate and outcome

Protected [PR3197](https://github.com/Marsys-Technologies/Madhav/pull/3197) merged2026-10-06T04:23:01Z as **2c117ba1afffa53dfd3d3a726baa7b3983ccf595**. Full PR CI37410005280 and full container build37410005252 passed; required merge-queue checks passed on the accepted exact SHA. All113 owned paths match the reviewed/final source branch byte-for-byte after protected integration; independently owned predecessor changes are preserved. Main exact-SHA CI37413445970 passed in full. Normal automatic deployment37415721436 finished SUCCESS, including routine migration, candidate smoke and earned outcome gate. Web candidate signing/RLS and release smoke passed; MCP, pipeline job image and sidecar mutation jobs were skipped by the path detector.

Read-only preflight across926 runner SQLfiles confirms **only1310 pending**, with preference column/object constraint/receipt absent. Routine runner applied1310 at2026-10-06T05:03:38.144Z; read-only production verification confirms exact source SHA256ce1a1a0c54345b2d3a2590453bd4049a0d2112796c7cbbc566f95167641686f7, jsonbNOTNULLdefault{}, validated object constraint, no pending runner SQL and no foreign1308/1309 receipts. Exact serving revision **amjis-web-probe-2c117ba1afff-37415721436-1**, source **2c117ba1afffa53dfd3d3a726baa7b3983ccf595**, immutable image **asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web@sha256:303b650555ba9cfe7bae34dd99f0c4f28571b17215a93ba730a4280867a7afba**, Ready=true and desired/observed100%traffic independently verified; prior limits-canary/web-iam-a/web-iam-b tags preserved. Authenticated read-only acceptance covers all nine account pages at1440/390/320 (27normal width checks, no page-wide overflow), API-only scope retained across Observatory/Consumption, honest empty persona/unknown cost states and live Escape drawer dismissal. Four unauthenticated account/profile/preferences/personas/usage guard checks return401. No real password, saved preference/persona/model/default/provider grant or chart changed for testing; no manually invoked paid AI generation.

Private recovery, schema and source logs: delivery-evidence under the Journey5 reconciliation folder. Live acceptance is supported by the actual serving/schema/browser receipts; owner DESIGN acceptance remains open. The prototype stays illustrative. Existing saved Claude Code default is shown unavailable pending execution validation; provider/catalog readiness and the separate automatic Paripraśna smoke remain operator follow-ups. Fresh comparison: pre-deploy37413819260 and post-deploy37417213726 both reportHTTP400 with6/11blocking assertions failed, preserving the existing baseline rather than certifying Consultation/provider health. No manually invoked paid/subscription AI generation. Shared credential rotation follow-up remains open after the earlier private diagnostic incident; no secret was committed or exported.

Changelog: v1.0 recorded recovery and preflight. v1.1 records actual protected release, schema/serving identity, authenticated read-only verification and explicit acceptance limits.

[Live account](https://amjis-web-938361928218.asia-south1.run.app/account) · [Deployment](https://github.com/Marsys-Technologies/Madhav/actions/runs/37415721436) · [Sanitized live receipt](LIVE_RELEASE.json) · [Actual migration](MIGRATION_VERIFICATION.json).

Final collision sweep covered all136 open PRs. Older Gochara PR3191 already contains1308; LEL reserves1309. Journey5 was renumbered before application to **1310_journey5_account_preferences.sql**. Only the unapplied filename/header changed; the reviewed DDL is unchanged. Earlier Journey5 reservation1308 is explicitly superseded in the coordination log, preserving the foreign1308 and1309 claims.
