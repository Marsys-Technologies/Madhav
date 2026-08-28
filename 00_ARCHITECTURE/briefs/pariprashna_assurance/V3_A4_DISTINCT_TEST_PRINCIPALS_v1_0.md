---
artifact: V3_A4_DISTINCT_TEST_PRINCIPALS
version: "1.0"
status: PROPOSED — informational record from the V3 autonomous overnight
  closeout campaign, lane A4 (Structural Engineer). Not a tracker event, not
  a stream result packet, not a closure artifact. Written for future streams
  that mint test sessions; adopt at will.
date: 2026-08-29
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/A2_CREDENTIAL_LANE_OUTCOME_v1_0.md (the shared-principal recipe this generalizes)
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/S5_CONVERGENCE_HANDOFF_v1_0.md §2 (the session-revocation drill that surfaced the collision)
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md V3-E-017 (the logout/revocation fix whose UID-scoping is what collided)
  - platform/scripts/dev/mint_stream_test_principal.ts (the capability)
---

# Distinct per-stream test principals (V3 A4)

## Problem

Every Pariprashna assurance stream (S1, S2, S5, ...) minted its `__session`
cookies against the **same** pre-existing Firebase UID
`hunQRYVJ5Ec2mQnJnutK7AoQnsO2` (`A2_CREDENTIAL_LANE_OUTCOME_v1_0.md`). That
was a reasonable simplification when only one stream ran at a time — but
`DELETE /api/auth/session` (logout) calls Firebase Admin's
`revokeRefreshTokens(uid)` (V3-E-017 fix,
`platform/src/app/api/auth/session/route.ts`), which is **UID-scoped**: it
invalidates every session cookie ever issued for that UID, not just the
caller's own cookie (`verifySessionCookie()`'s `checkRevoked: true` flag,
`platform/src/lib/firebase/server.ts`). When stream S5 ran its
session-revocation security drill (`S5_CONVERGENCE_HANDOFF_v1_0.md` §2)
against the shared UID, it silently revoked stream S2's still-active
click-through session mid-run — the two streams were, without either
realizing it, the same underlying principal.

This is **not** an application defect. UID-scoped revocation is correct
production behavior and is exactly what V3-E-017 was fixing. The defect was
entirely in how the test harness reused one identity across concurrent,
independent test streams.

## Fix: distinct principals, not looser revocation

`platform/scripts/dev/mint_stream_test_principal.ts` provisions a **distinct**
guest-role test principal per stream, each scoped only to the synthetic
assurance chart (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`):

1. Derives a per-stream UID (`pariprashna-test-<stream_id>`, e.g.
   `pariprashna-test-s2`), or accepts an explicit override.
2. Idempotently inserts a `chart_grants` row `(chart_id=<synthetic chart>,
   principal_id=<uid>, permission='view')` — the same shape three other
   pre-existing test principals already hold on that chart, so this is
   additive within an already-supported access pattern, not a new one.
3. Mints a Firebase custom token for that UID and exchanges it for a
   `__session` cookie via the app's own `/api/auth/session` endpoint,
   exactly like the existing `mint_session_cookie.ts` recipe (which remains
   unmodified and still works for its documented `SUPER_ADMIN_UID` use case).
4. Refuses unconditionally to run against the native's real chart
   (`482012f1-710e-4a25-994a-93821f5871aa`), even if explicitly passed.

No production auth code was changed. `authorizeChartAccess.ts`,
`revokeRefreshTokens`, and `verifySessionCookie`'s `checkRevoked` semantics
are untouched — this is additive test-data provisioning (a new
`chart_grants` row per stream), not a loosened check.

## Proof

`platform/src/app/api/auth/session/__tests__/route.stream-isolation.test.ts`
extends the existing V3-E-017 Firebase Admin simulator
(`route.revocation.test.ts`) to track revocation per-UID instead of with one
global flag, and proves:

- two distinct stream principals authenticate to their own, independent uids;
- one principal's logout/revocation drill revokes **only** its own uid — the
  other principal's session is provably unaffected;
- a principal can keep operating normally after another stream's drill, and
  can still independently revoke its own session later;
- a CONTROL case reproduces the original defect on purpose (two cookies
  sharing one uid — the pre-fix shared-principal setup) to show the same
  test harness *would* catch the collision if it recurred.

Command output (2026-08-29, this worktree):

```
$ npx vitest run src/app/api/auth/session/__tests__/
 Test Files  2 passed (2)
      Tests  11 passed (11)
```

(5 pre-existing V3-E-017 tests + 6 new isolation-proof tests, all green.)

## Adoption

Streams that mint test sessions going forward can call:

```
STREAM_ID=s2 SERVICE_URL=https://amjis-web-qm256lasva-el.a.run.app \
  DATABASE_URL=<cloud-sql-proxy connection string> \
  COOKIE_OUTPUT_FILE=<scratch path> \
  npx dotenvx run -f platform/.env.local -- \
  npx tsx platform/scripts/dev/mint_stream_test_principal.ts
```

in place of `mint_session_cookie.ts SUPER_ADMIN_UID=hunQRYVJ5Ec2mQnJnutK7AoQnsO2`,
to get a session whose lifecycle (including any drill that revokes it) is
fully isolated from every other stream. `mint_session_cookie.ts` is left
exactly as-is for anything that still legitimately needs the original shared
principal or a genuine `super_admin` impersonation.
