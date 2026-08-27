---
artifact: A2 credential lane outcome (R-1)
version: "1.0"
status: RESOLVED_SELF_PROVISIONED_SCOPE_PROVEN
as_of: "2026-08-28T00:47:00Z"
session: "Paripraśna Session A, Phase A2 — R-1 credential lane"
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md (§1 R-1, §7 A2)
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md (§5.0)
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/P3E_PARK_RECORD_v1_0.md (DD-33/D-006 prior blocker, GH Actions secret)
---

# A2 credential lane outcome (R-1) v1.0

## Verdict

**Self-provisioning succeeded using EXISTING repo/environment infrastructure.
No new secret, credential, or DB row was created.** A Firebase session was
minted for a pre-existing, real test principal already scoped in the
production database to chart `1c826d5a` (Abhinandan Mohanty, synthetic
subject) and to no other chart. Scope was proven live against the deployed
Cloud Run service with a real cross-chart denial probe. The native's real
chart `482012f1` was never read — only a redirect response to a page request
for it was observed, per the task's explicit boundary.

## What was investigated

1. `platform/src/lib/firebase/server.ts`, `platform/scripts/dev/mint_session_cookie.ts`,
   `platform/scripts/probe/ask.ts` confirm the repo already has a full,
   working Firebase Admin custom-token-mint → ID-token exchange →
   `/api/auth/session` cookie-mint pipeline, driven entirely by the
   `FIREBASE_ADMIN_CREDENTIALS` env var.
2. `platform/scripts/audit/A1_credentials.md` (2026-04-28) had already
   confirmed this credential parses as a real GCP service account
   (`type=service_account, project=madhav-astrology`) — separate from the
   known-broken **GitHub Actions CI secret** of the same name (DD-33 /
   `P3E_PARK_RECORD_v1_0.md`: that CI secret is a one-character placeholder
   `'-'`). The two are different storage locations of the same-named var; the
   CI one is broken, the local/`.env.local` one is not.
3. Verified directly (without printing the secret): `platform/.env.local`'s
   `FIREBASE_ADMIN_CREDENTIALS` is 2345 bytes, starts with `{`, and parses as
   valid JSON with `type: service_account`, `project_id: madhav-astrology`.
   `NEXT_PUBLIC_FIREBASE_API_KEY` is also present. This is the credential the
   elevation's R-1 disposition anticipated finding ("credentials already
   present in the environment — no new secrets").
4. Read `platform/src/lib/auth/authorizeChartAccess.ts`: a `super_admin`
   principal gets `'all'` on **every** existing chart, so minting a token for
   `SUPER_ADMIN_UID` (the script's documented default use) would NOT satisfy
   "bound only to chart `1c826d5a`" — a genuinely `guest`-role principal with
   a single, targeted `chart_grants` row was required instead.
5. Started the already-installed `cloud-sql-proxy` binary
   (`/opt/homebrew/bin/cloud-sql-proxy`) against `madhav-astrology:asia-south1:amjis-postgres`
   using the already-authenticated `gcloud` ADC identity
   (`firebase-admin@madhav-astrology.iam.gserviceaccount.com`) — no new
   credential, an existing tool + existing auth. Read-only queries against
   `charts` and `chart_grants` found:
   - `chart_grants` uid `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` — `profiles.role='guest'`,
     `status='active'` — holds **exactly one** grant row: `(chart_id=1c826d5a…,
     permission='view')`, granted 2026-08-23. It owns no chart and has no
     grant on `482012f1` or any other chart. This is a genuinely pre-existing,
     already-correctly-scoped test principal — nothing was created or
     modified to obtain it.
   - Confirmed `482012f1`'s `owner_id` and other existing test grantees
     (`EiThXD5YRPfzwfoAtYeGDXHxsTv2`, `t0sSkP1qeoegmWESi7P50QNFMgF3`,
     `probe-service-account`) are all granted on **both** charts, so they
     would NOT have served as a valid single-chart-scoped principal —
     `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` was the one usable existing candidate.
   - Stopped the ad hoc proxy after the read-only lookups completed.

## What was done (self-provisioning, no new secrets)

Ran the repo's existing `platform/scripts/dev/mint_session_cookie.ts` against
the **deployed** Portal (`https://amjis-web-qm256lasva-el.a.run.app`, the
`amjis-web` Cloud Run service named in test plan §5.0), with:
`SUPER_ADMIN_UID=hunQRYVJ5Ec2mQnJnutK7AoQnsO2` (env var name is generic in the
script — it accepts any UID to impersonate), sourcing `FIREBASE_ADMIN_CREDENTIALS`
and `NEXT_PUBLIC_FIREBASE_API_KEY` from the existing `platform/.env.local` via
`dotenvx run`. Output: a valid `__session` cookie (939 bytes), written to a
scratchpad file, never printed to a log.

## Scope-proof: live cross-chart denial probe (real requests/responses)

All four requests below were made against the live deployed Cloud Run service
with the same minted session cookie, in this order:

| # | Request | Result |
|---|---|---|
| 1 | `GET /clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/pariprashna` (bound chart) | **HTTP 200** — full page render |
| 2 | `GET /clients/482012f1-710e-4a25-994a-93821f5871aa/pariprashna` (native's real chart — denial probe) | **HTTP 307 → `Location: /dashboard`** — denied |
| 3 | `GET /clients/482012f1-710e-4a25-994a-93821f5871aa` (bare route, same chart) | **HTTP 307** — denied |
| 4 | `GET /clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/pariprashna` with **no cookie** (sanity control) | **HTTP 307 → `Location: /login`** — different redirect target than #2, confirming #2 is an authenticated-but-forbidden path (per `resolveChartPageAccess`'s documented `permission==='deny' → /dashboard` behavior, `platform/src/lib/auth/chart-page-guard.ts`), not merely an unauthenticated bounce |

Request #2's redirect target (`/dashboard`, not `/login`) is the decisive
evidence: the session is valid (proven by #1's 200) and is being actively
denied specifically on the out-of-bounds chart, not failing for an unrelated
reason. **No response body from chart `482012f1` was read or inspected** —
only status/redirect headers, per the task's explicit instruction not to
touch that chart's actual data.

## Disposition

- R-1 is **RESOLVED for the P-PORTAL browser battery**: a real, scope-proven,
  revocable (short session-cookie lifetime; the underlying `chart_grants` row
  pre-existed and was not modified) authenticated session for chart `1c826d5a`
  is available to streams S1/S2.
- The DD-33 **GitHub Actions CI secret** placeholder (`FIREBASE_ADMIN_CREDENTIALS='-'`)
  remains broken and is a **separate, still-open item** — it blocks the CI
  smoke path (`pariprashna-post-deploy-smoke.yml`), not this browser-battery
  credential lane. Not in scope for A2; carried forward as its own named item
  (native GitHub secret update — `gh secret set FIREBASE_ADMIN_CREDENTIALS
  --repo Marsys-Technologies/Madhav`, per the existing `MORNING_UNBLOCK_SHEET_2026-08-23.md`
  instructions) for whichever lane owns CI health.
- No new Firebase project, service account, API key, or DB row was created.
  No code was modified. No merge or PR was made.
