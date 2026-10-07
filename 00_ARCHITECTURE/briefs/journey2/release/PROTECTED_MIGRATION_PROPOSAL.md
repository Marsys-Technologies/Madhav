---
artifact: JOURNEY2_PROTECTED_MIGRATION_PROPOSAL
version: 1.1
status: DRAFT_REQUIRES_SCOPE_RULING
---

# Exact Journey Two migration window

Deployment37597115725 stopped at migration1312 with `permission denied for schema public`. The routine amjis_app role owns conversation_shares and has public USAGE, deliberately without CREATE. Creating the partial index needs CREATE. Actual readback shows no1312 tracker, column, FK or index: the transaction rolled back. Actual serving e743a8a73fc0 remains Ready at100%; no new web revision was promoted. Correction PR3235 auto-merge is disabled.

Proposed bounded repair, not implemented: retain migration1312 bytes/hash acb13f0f93cbc142a1cde26018e11a189e981396b23275c73dc33d4b253ecc70. Extend the existing manual-only protected public-schema workflow with a boolean `journey2_schema_migration` input, defaultfalse. Journey Two mode must reject every other protected migration/bootstrap input before any grant; require CI-green without emergency override and assert the selected set is exactly `{1312_journey2_exchange_shares.sql}`. Add1312 to migrate.ts's protected pending-file guard with an actionable exact-input refusal. Preserve existing non-Journey selection behavior. Keep CI-green, immutable DEPLOY_SHA, marked/strict data-plane and Nirmana/Purna ownership prerequisites, protected environment approval and serialized production lease. Use the existing jataka-schema-capability.ts grant/run/revoke mechanism without new credentials or role membership. Use always() to revoke CREATE on ordinary success and failure paths; it cannot guarantee execution after runner loss or forced termination. Service deployment must remain blocked unless the close succeeds. For an interrupted own window, halt promotion, read back privileges, close through the existing protected revoke mechanism, verify CREATE=false, then reassess before retry. Never cancel an active production window or assume cleanup executed. Verify public CREATE=false/USAGE=true afterward and exact1312 SHA/column/FK/index before promotion.

Source scope needing amendment: `.github/workflows/deploy.yml`, `platform/scripts/migrate.ts`, and focused existing deployment/migration contract tests, plus owned governance release receipts. Existing schema-capability helper should stay unchanged. Add meaningful least-privilege PostgreSQL regression: the current role cannot create this index, exact authorized window can apply1312, normal success/failure paths revoke CREATE, conflicting inputs are rejected before grant, interrupted-window handling blocks promotion until privileges are verified closed, and routine replay/immutable-hash checks still work. Independent migration/security review, full quality and protected checks are required before protected source merge and manual exact-SHA dispatch. No automatic privilege widening, permanent grants, privileged bootstrap recreation, direct production SQL, unrelated migration or chart/asset rebuild.

Authority gap: CCD-028 excludes IAM/credential/account-permission changes, and this session's declared must_not_touch includes `.github/**`; SESSION_OPEN additionally excludes permission changes. The proposed temporary schema capability and workflow scope need an explicit native ruling before implementation or dispatch. Existing protected inputs select unrelated exact migration sets and cannot legitimately be repurposed for1312.

Alternative assessed: dropping the message_id partial index would avoid schema CREATE, but weakens the reviewed FK deletion/lookup performance contract and changes the already reviewed migration. The exact existing protected window is proposed; no omission or unreviewed workaround has been applied.

## Changelog

- 1.0: actual failed deployment, transaction rollback, unchanged serving revision and concrete smallest protected-route proposal; native scope ruling remains pending.

- 1.1: independent proposal review resolved combined-input ambiguity and qualified always() cleanup with explicit interrupted-window recovery. Native scope ruling is still pending.
