# Inquiry lifecycle signing-key rotation runbook v1.0

Status: SOURCE-READY; NOT EXECUTED

Owner: platform-security-release

Scope: `amjis-web` raw MCP Inquiry lifecycle tokens only

Authority boundary: this artifact does not authorize Secret Manager, IAM, Cloud Run, staging, or production mutation.

## Contract

The service issues every new token with `INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT` and the public
`INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID`. During a rotation overlap it verifies tokens with both
that pair and the optional `..._PREVIOUS` / `..._PREVIOUS_KID` pair. It never issues with the
previous key. Configuration fails closed when a pair is missing, a KID is not a monotonic
`inquiry-vN` identifier, KIDs collide, or key material is not canonical unpadded base64url encoding
of at least 32 random bytes.

The maximum application token lifetime is 3,600 seconds. Keep the previous key available for at
least 3,900 seconds (maximum lifetime plus a 300-second deployment/clock buffer) after the new
revision receives traffic. Disabling it earlier invalidates legitimate in-flight lifecycles.

## Preflight (read-only)

Run these only in an approved release context. They print metadata, never secret payloads.

```bash
gcloud secrets describe inquiry-lifecycle-signing-key --project madhav-astrology \
  --format='value(name)'
gcloud secrets versions list inquiry-lifecycle-signing-key --project madhav-astrology \
  --filter='state=ENABLED' --format='table(name,state,createTime)'
gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
  --flatten='spec.template.spec.containers[].env[]' \
  --filter='spec.template.spec.containers.env.name~^INQUIRY_LIFECYCLE_SIGNING_KEY_.*_KID$' \
  --format='table(spec.template.spec.containers.env.name,spec.template.spec.containers.env.value)'
gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
  --flatten='spec.template.spec.containers[].env[]' \
  --filter='spec.template.spec.containers.env.name~^INQUIRY_LIFECYCLE_SIGNING_KEY_(CURRENT|PREVIOUS)$' \
  --format='table(spec.template.spec.containers.env.name,spec.template.spec.containers.env.valueFrom.secretKeyRef.name,spec.template.spec.containers.env.valueFrom.secretKeyRef.key)'
```

Stop if the secret is absent, the service identity lacks access, the currently bound version/KID
cannot be established, or the approved change record does not name the exact old and new version.
Do not recover by minting unrelated credentials or by placing a key in a plaintext environment
value.

## Initial provisioning

Under separately approved credentials/change authority:

1. Generate at least 32 random bytes into a permission-restricted temporary file and encode them as
   canonical unpadded base64url. Do not print, log, paste into a PR, or retain the file.
2. Create `inquiry-lifecycle-signing-key` if absent and add the material as version 1.
3. Grant Secret Manager accessor only to
   `amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com`.
4. In the reviewed deployment change, bind the secret version to
   `INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT` and set the non-secret
   `INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID=inquiry-v1`.
5. Deploy without traffic, run the staging lifecycle checks below, then promote under the normal
   release gate.

Do not set a PREVIOUS pair for initial provisioning.

## Rotation with overlap

Assume the active pair is KID `inquiry-vN` and Secret Manager version `OLD_VERSION`.

1. Add independent random material as `NEW_VERSION`; do not overwrite or disable `OLD_VERSION`.
2. Prepare one reviewed deployment change with these four bindings:

   ```text
   INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID=inquiry-v<N+1>
   INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT=inquiry-lifecycle-signing-key:NEW_VERSION
   INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID=inquiry-vN
   INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS=inquiry-lifecycle-signing-key:OLD_VERSION
   ```

3. Deploy the candidate without traffic. Confirm it issues a token whose decoded header contains
   only the new public KID; never print the token or signature.
4. Confirm the candidate accepts a pre-rotation test token and a newly issued token for the same
   staging principal, rejects an unknown KID, and preserves subject/chart/JTI replay checks.
5. Promote through normal release control. Record deployed revision, new/old version numbers,
   non-secret KIDs, test receipt IDs, and timestamps.
6. Wait at least 3,900 seconds from traffic promotion. Query only the privacy-safe
   `[mcp:inquiry] lifecycle token verified` audit signal (it contains the public KID and no token,
   signature, claims, or key material) and verify no old-KID validation remains in the bounded
   logs window.
7. Deploy a second reviewed change that removes both PREVIOUS bindings. Re-run the lifecycle smoke.
8. Disable `OLD_VERSION`. Destroy it only after the repository-wide secret policy's seven-day
   incident-free period.

## Staging acceptance receipts

The change record must retain, without raw tokens or secret material:

- exact source SHA and Cloud Run candidate revision;
- current and previous KIDs plus Secret Manager version numbers;
- one start → execute → finalize receipt using the new KID;
- one pre-rotation-token continuation accepted during overlap;
- unknown-KID, wrong-subject, stale-JTI, and expired-token rejection codes;
- migration 1033/1037 applied-version evidence and `role_web_serve` RLS/grant checks;
- a post-promotion health window and the timestamp at which overlap removal became safe.

## Rollback

Before overlap removal, rollback is configuration-only: route traffic to the prior healthy revision,
which still has the old key as CURRENT. If the new revision must remain deployed, issue another
revision with the old pair restored as CURRENT and the new pair as PREVIOUS; this preserves tokens
minted by both revisions.

After PREVIOUS removal, do not route back to a revision that cannot validate tokens issued by the
current revision. Restore a dual-key revision first. Re-enabling a disabled old Secret Manager
version requires explicit incident/change authority. A destroyed version cannot be recovered.

Migration rollback is separate and destructive. Migration 1033's documented DOWN removes retained
lifecycle/evidence data, and migration 1037 removes reservation data. Export required evidence and
obtain database change approval before any staging/shared DOWN. Source tests prove transactional
rollback and disposable UP/reapply/DOWN only; they do not authorize shared execution.

## Source-local evidence

- `platform/src/lib/vidhi/inquiry/lifecycle_token.test.ts` proves current-only issuance, overlap
  verification, old-key removal, unknown-KID rejection, and fail-closed parsing.
- `platform/src/lib/vidhi/inquiry/migration_1033.db.test.ts` proves forced-failure transaction
  rollback plus disposable UP/reapply/RLS/role/replay/DOWN behavior when its localhost-only database
  gate is supplied.
- `platform/src/app/api/mcp/inquiry/route.ts` loads the key ring per request and returns stable token
  failures without exposing configuration or key material.

Until the external receipts above exist, PA-R06 is only source/local/disposable-ready and its
credential, staging-migration, service-role, and deployed-runtime remainder stays open.
