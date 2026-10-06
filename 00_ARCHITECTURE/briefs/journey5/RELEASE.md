---
artifact: JOURNEY5_RELEASE
version: 1.0
status: PROTECTED_INTEGRATION_PENDING
---
# Journey 5 protected release

Authority CCD-024; exclusive production lease L-PORTAL-JOURNEY5-PRODUCTION-20261006, verified coordination commit03f028413e028b133149b13e1648fd420067f541, expires2026-10-06T06:21:17Z. Existing normal CI-gated deployment, no protection bypass.

## Recovery readiness

CloudSQL amjis-postgres pre-migration on-demand backup **1791256883782**, status **SUCCESSFUL**, finished **2026-10-06T03:22:44.869Z**. Restore mechanism is CloudSQL backup restore for this instance; no restore was executed. Restoration of the whole shared database is an emergency coordinated operation, not an acceptance test. Additive1310 is compatible with the predecessor app; ordinary code rollback leaves the column and receipt in place.

Prior serving web revision **amjis-web-probe-f50a00091db2-37400455184-1**,100%traffic; immutable image **sha256:c9e49589e4c176d77e374c8bad7189059b02d52c7c08415c2de7591961e747df**. Re-read immediately before release. Revert web traffic to the verified healthy predecessor while retaining existing tags if candidate smoke/live checks fail; no unrelated service or foreign release rollback.

Read-only production preflight confirms profiles, personas and migration tracker owned by the existing amjis_app migration login. account_preferences column and1308/1309 receipts absent before release.1310 source is independently reviewed and reserved;1309 belongs to the released local LEL work and is not part of this candidate.

## Candidate and outcome

Protected PR/required CI and merge-queue outcome pending. Actual1310 ledger SHA256, column/default/object constraint and serving exact candidate SHA/revision/traffic must be independently checked after the routine runner. Authenticated read-only nine-page acceptance follows release. No real password, saved preference/persona/model/default/provider grant or chart changed for testing; no paid AI generation.

Private recovery, schema and source logs: delivery-evidence under the Journey5 reconciliation folder. Deployment and owner acceptance are not inferred from local tests or prototype fixtures.

Changelog: v1.0 records recoverable backup, predecessor pin and production preflight; release remains pending.

Final collision sweep covered all136 open PRs. Older Gochara PR3191 already contains1308; LEL reserves1309. Journey5 was renumbered before application to **1310_journey5_account_preferences.sql**. Only the unapplied filename/header changed; the reviewed DDL is unchanged. Earlier Journey5 reservation1308 is explicitly superseded in the coordination log, preserving the foreign1308 and1309 claims.
