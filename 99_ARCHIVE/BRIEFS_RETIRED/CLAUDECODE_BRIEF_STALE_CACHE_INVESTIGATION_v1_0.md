---
canonical_id: CLAUDECODE_BRIEF_STALE_CACHE_INVESTIGATION
version: 1.0
status: COMPLETE
authored: 2026-06-07
author: Cowork (planning)
executor: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: Fix — prod serves STALE cached HTML on plain routes after deploy
---

# CLAUDECODE_BRIEF — Stale-cache-after-deploy investigation + fix

## §0 — Symptom (Cowork-confirmed live, 2026-06-07)

The new-client form is correctly DEPLOYED to prod, but users see the OLD form. Proven:
- `https://madhav.marsys.in/clients/new` (plain) → OLD form: manual-coords accordion,
  node microcopy, timezone/UTC fields, NO `gmp-place-autocomplete`.
- `https://madhav.marsys.in/clients/new?cb=anything` (query param) → NEW form: Manual
  override checkbox, `gmp-place-autocomplete` present, no tz fields, centered card.
- Same server, same revision (`amjis-web-00534-qb5`+). Only difference = query string.

Conclusion: NOT a deploy failure. The bare path is served from a STALE edge/CDN/Next
static cache; a query param busts that cache and reveals the fresh build. This has recurred
3× this session (form deploy, cockpit deploy, this) — it needs a root-cause fix so users
never see stale pages after a deploy.

## §1 — Likely cause (Cowork's read; VERIFY before fixing)

- `platform/src/app/clients/new/page.tsx` has NO `export const dynamic` /
  `export const revalidate` directive. So Next.js (App Router) likely treats it as a
  **statically prerendered** route — the HTML is generated at build and cached at the edge.
- `platform/next.config.ts` has no `headers()` / `Cache-Control` config; deploy.yml shows
  no obvious Cloud CDN invalidation step. So a stale static document can persist at the
  CDN / browser / Cloud Run layer across deploys until TTL expiry.

But DO NOT assume — Step 1 is to confirm WHERE the cache actually lives.

## §2 — Step 1: Diagnose (report before fixing)

- **Response headers:** `curl -sI https://madhav.marsys.in/clients/new` and inspect
  `Cache-Control`, `Age`, `X-Vercel-Cache`/`CDN-Cache`/`Via`, `ETag`, `x-nextjs-cache`.
  Compare with the `?cb=` variant. The header diff tells you which layer is caching.
  (Use curl for header inspection only — this is allowed; it is not a content-fetch
  workaround.)
- **Is there a CDN in front?** Check whether `madhav.marsys.in` points at Cloud CDN / a
  load balancer with caching, or straight at Cloud Run. `gcloud` describe the backend /
  URL map if a LB exists. If Cloud CDN is enabled, that's the cache layer.
- **Is the route static?** Check the Next build output (`.next` / build log) for whether
  `/clients/new` is marked `○ (Static)` vs `λ (Dynamic)`. If static, that's the root.
- **Cloud Run:** confirm whether responses carry a long `Cache-Control` from Next or a
  proxy. Report which layer holds the stale copy.

## §3 — Step 2: Fix (choose based on the diagnosis)

Pick the fix that matches where the cache actually lives — don't apply all blindly:

- **If the route is statically cached by Next and should always be fresh:** add to
  `platform/src/app/clients/new/page.tsx`:
  `export const dynamic = 'force-dynamic'` (and/or `export const revalidate = 0`) so the
  page is rendered per-request and not served from a stale static document. (Cheap; the
  page is a light form. Confirm it doesn't break the auth/redirect behaviour.)
- **If a CDN / Cloud Run sends a long Cache-Control on the HTML document:** set the HTML
  document `Cache-Control` to `no-store` (or `no-cache, must-revalidate`) for app routes
  like `/clients/new` (and ideally `/clients/[id]/build`), while leaving Next's
  hashed/immutable `/_next/static/*` assets long-cached (those are content-hashed and safe
  to cache forever). The goal: HTML revalidates, static chunks stay immutable.
- **If Cloud CDN is in front:** ensure the deploy pipeline issues a CDN cache
  **invalidation** for the changed paths after each deploy (e.g. `gcloud compute
  url-maps invalidate-cdn-cache ... --path "/*"` or scoped paths) so a new revision
  doesn't keep serving the prior cached document.

**Preferred minimal fix** (if diagnosis confirms static-route caching, the most likely
case): `force-dynamic` on the form route (and the cockpit build route if it shows the same
symptom), since these are authenticated, per-user, low-traffic pages that should never be
statically cached. Verify the cockpit `/clients/[id]/build` route too — it had the same
stale symptom earlier this session.

## §4 — Acceptance
- After the fix + a fresh deploy: `https://madhav.marsys.in/clients/new` (PLAIN, no query
  param, in a fresh browser / incognito) serves the NEW form on first load — Manual
  override present, `gmp-place-autocomplete` present, no tz fields. No cache-bust needed.
  `[verify-against: prod] [via: curl headers + browser incognito]`
- `/_next/static/*` assets remain long-cached (don't disable caching wholesale — only the
  HTML document should revalidate).
- Cowork re-verifies the plain prod URL in Chrome (incognito + normal) after deploy.

## §5 — Branch + ship
```
git checkout main && git pull --ff-only
git checkout -b fix/stale-route-cache
# Step 1 diagnose → report headers/CDN/static findings in the PR description
# Step 2 apply the matching fix
git add -A && git commit -m "fix: stop serving stale cached HTML on /clients/new (+ build route) after deploy"
git push origin fix/stale-route-cache
# merge to main, deploy, then Cowork verifies the PLAIN prod URL is fresh
```
Do NOT disable caching on static assets. Report the Step-1 diagnosis before the Step-2 fix
so the native can confirm the cause.

## §6 — Note
This is the same stale-serve that masked the form deploy and the cockpit deploy earlier
this session (each needed a `?cb=` to reveal the new build). Fixing it at the source means
future deploys are visible immediately on the plain URL — and removes the need to cache-bust
during prod verification.
