---
artifact: CLAUDECODE_BRIEF_NIRMANA_PAGE_RENAME_v1_0.md
canonical_id: NIRMANA_PAGE_RENAME_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (code-plane blast-radius map) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
execution_mode: CONTINUOUS / AUTONOMOUS — phase-by-phase, no human gate between phases. Tier-3 rails only.
data_plane: code-plane change only (one prod-verify at the end via the running app)
native_decision: "Name + URL, with redirect" (2026-06-16) — name the per-chart build-tracker page **Nirmāṇa** AND rename the route /clients/[id]/build → /clients/[id]/nirmana, updating all references, keeping a /build → /nirmana redirect so old links don't 404.
rationale: >
  This per-chart build-tracker page (Brahmagyan/Gaṇita/Bodha/… layers + asset bars) keeps getting
  confused with the dashboard cockpit. It is reached from the jātaka card's **Nirmāṇa** button, so
  naming the PAGE Nirmāṇa makes the button→page relationship self-consistent and disambiguates it
  from the dashboard cockpit. Nirmāṇa = "creation / building" — the right Sanskrit for a build tracker.
---

# Nirmāṇa Page Rename (build tracker) — Brief v1.0

## §0 — What this does
1. Gives the per-chart build-tracker page a visible name: **Nirmāṇa** (the page currently has NO
   title/H1 — just the chart name + a "Data assets" tab — which is why it's confused with the cockpit).
2. Renames the route `/clients/[id]/build` → `/clients/[id]/nirmana` and updates EVERY reference.
3. Keeps a `/clients/[id]/build` → `/clients/[id]/nirmana` redirect so old bookmarks/links don't 404.

**CRITICAL — do NOT rename `/api/build` or `/api/cockpit/*`.** Those are API routes, unrelated to
this page's URL. This rename touches ONLY the page route `clients/[id]/build` and the links that
point at it. `/api/build`, `/api/cockpit/...` (stats/registry/runs/sse/clear/refresh/plan) stay exactly
as they are — the page keeps calling them.

## §1 — PHASE N1 — Visible name + back-link (cheap, do first; native-approved visual)
**Native reviewed a mockup and approved (2026-06-16): the daṇḍa-flanked `॥ Nirmāṇa ॥` title in the
SAME style as the dashboard "Jātakas" + Nava Jātaka pages, WITH a small "Build Tracker" subtitle,
AND a ChevronLeft back-link to /dashboard matching the Nava Jātaka page. Reuse the design-system
tokens — do NOT hardcode hex; the values below are the token equivalents for reference only.**

### N1.1 — The title (mirror the dashboard "Jātakas" / Nava Jātaka title EXACTLY)
The "pipings" are the Devanagari daṇḍa `॥` (U+0965), NOT pipe chars. Reference markup is
`dashboard/page.tsx:186-190` and `NewClientForm.tsx:665-669`. Use the SAME classes/tokens:
```tsx
<h1 className="bt-display text-brand-gold-cream">
  <span className="opacity-55 text-brand-gold font-serif mr-1" aria-hidden="true">॥</span>
  Nirmāṇa
  <span className="opacity-55 text-brand-gold font-serif ml-1" aria-hidden="true">॥</span>
</h1>
```
(`bt-display` = the brand display type ramp from globals.css; `text-brand-gold-cream` ≈ #fce29a;
`text-brand-gold` ≈ #d4af37. Same as the two reference pages — do not invent new values.)

### N1.2 — The "Build Tracker" subtitle (native: KEEP it)
Directly under the title, a small uppercase gold caption to disambiguate from the dashboard cockpit:
```tsx
<p className="bt-label bt-label-upper text-brand-gold/55" style={{ textAlign: 'center' }}>Build Tracker</p>
```
(Use the existing `bt-label bt-label-upper` utility — same family used for form labels in
NewClientForm — NOT a bespoke style. This is the one element that differs from Nava Jātaka, by
native decision, because this page needs to self-identify vs the cockpit.)

### N1.3 — The back-link (mirror Nava Jātaka EXACTLY — `NewClientForm.tsx:646-670`)
A relative-positioned, centered title row with the back-arrow absolute-left:
```tsx
<div className="relative flex items-center justify-center w-full mb-2">
  <Link href="/dashboard" aria-label="Back to dashboard"
    className="absolute left-0 flex items-center justify-center w-8 h-8 rounded-full transition-colors duration-150"
    style={{ color: 'oklch(0.58 0.025 80)' }}
    onMouseEnter={(e)=>{(e.currentTarget as HTMLElement).style.color='var(--brand-gold)'}}
    onMouseLeave={(e)=>{(e.currentTarget as HTMLElement).style.color='oklch(0.58 0.025 80)'}}>
    <ChevronLeft size={20} strokeWidth={1.5} />
  </Link>
  {/* title from N1.1 here, centered */}
</div>
```
`import { ChevronLeft } from 'lucide-react'` (same icon + size 20 + strokeWidth 1.5 as Nava Jātaka).
Place this header block ABOVE the existing CockpitShell chart-name + WRITERS/QUEUE/BUILD/SIDECAR
strip (which stays unchanged). Do NOT use router.back() — link explicitly to /dashboard so it always
lands on the roster (Nava Jātaka uses an explicit /dashboard href, not back()).

### N1.4 — Browser tab metadata
`export const metadata = { title: 'Nirmāṇa · <chart name> — MARSYS-JIS' }` (or generateMetadata that
pulls the chart name), matching the dashboard's `'Jātakas — MARSYS-JIS'` pattern (dashboard/layout.tsx:8).

### N1.5 — Acceptance
- [ ] The page shows `॥ Nirmāṇa ॥` rendered IDENTICALLY to dashboard "Jātakas" (same font/color/daṇḍas — diff the classes).
- [ ] A small "Build Tracker" subtitle sits under the title.
- [ ] A ChevronLeft back-arrow (gold on hover) sits at the title row's left and links to /dashboard.
- [ ] Browser tab reads "Nirmāṇa · …".
- [ ] No URL change yet (that's N2); only the header + tab.

## §2 — PHASE N2 — Route rename `/build` → `/nirmana`
Move the route folder and ALL its children:
```
app/clients/[id]/build/                  →  app/clients/[id]/nirmana/
  page.tsx                               →  page.tsx
  layout.tsx                             →  layout.tsx
  error.tsx                              →  error.tsx
  [conversationId]/page.tsx              →  [conversationId]/page.tsx
  __tests__/page.test.tsx                →  __tests__/page.test.tsx
```
Use `git mv` so history is preserved. Update any internal relative imports if they reference the
folder name. The `[conversationId]/page.tsx` currently does `redirect(\`/clients/${id}/build\`)` —
repoint it to `…/nirmana`.

## §3 — PHASE N3 — Update ALL references (the blast radius — 11 link sites + 3 API redirect_urls + 2 guards)
**Internal page links (router.push / href / redirect) — change `/build` → `/nirmana`:**
- `app/clients/[id]/build/[conversationId]/page.tsx:14` — `redirect(\`/clients/${id}/build\`)`
- `app/clients/[id]/consult/page.tsx:136` — `const cockpitHref = \`/clients/${id}/build\`` (also consider renaming the var off "cockpit" → "nirmana" to kill the naming confusion at the source)
- `app/clients/[id]/page.tsx:92` — `cta href \`/clients/${id}/build\`` ('Continue building')
- `components/clients/NewClientForm.tsx:619` — `router.push(data.redirect_url ?? \`/clients/${data.chart_id}/build\`)`
- `components/clients/EditClientForm.tsx:160` — `router.push(\`/clients/${chart.id}/build\`)`
- `components/dashboard/ClientCard.tsx:257` — `href \`/clients/${chart.id}/build\`` (the **Nirmāṇa button** — confirm its label is already "Nirmāṇa"; the href is what changes)
- `components/dashboard/RosterTableView.tsx:137` — `href \`/clients/${c.id}/build\``
- `components/dashboard/BuildCompleteToast.tsx:73` — `viewUrl \`/clients/${build.chart_id}/build\``
- `components/brahma/ChartCreatedToast.tsx:76` — `href \`/clients/${chartId}/build\``

**API `redirect_url` strings (server emits these; NewClientForm consumes) — change `/build` → `/nirmana`:**
- `app/api/clients/create/route.ts:305, 326, 408` — all three `redirect_url: \`/clients/${…}/build\``
- (also update the doc comment at line 12 if it names the path)

**Path-guards that check `pathname.includes('/build')` — update to `/nirmana`:**
- `components/shared/AppShellBreadcrumb.tsx:23` — `if (pathname.includes('/build')) return null`
- `components/nav/ConditionalChartSwitcherBar.tsx:14` — `if (pathname?.includes('/build')) return null`
- NOTE: `.includes('/build')` would ALSO match `/api/build` etc.; switch to `.includes('/nirmana')`
  and verify the guard still fires only on this page (test the breadcrumb/switcher hide-behavior).

**Auth guard:** `lib/auth/chart-page-guard.ts` (`resolveChartPageAccess`) is path-agnostic (keyed on
chart access, not the URL string) — confirm it needs NO change. The page's own `if (!access.canBuild)
redirect(\`/clients/${id}\`)` stays (canBuild is the permission name, unrelated to the URL).

## §4 — PHASE N4 — Back-compat redirect (`/build` → `/nirmana`, no 404s)
Add a redirect so any old bookmark/external link to the old path lands on the new one:
- Preferred: a `redirects()` entry in `next.config.js`:
  `{ source: '/clients/:id/build', destination: '/clients/:id/nirmana', permanent: true }`
  AND `{ source: '/clients/:id/build/:conversationId', destination: '/clients/:id/nirmana/:conversationId', permanent: true }`.
- (If next.config redirects don't fit the setup, a tiny `app/clients/[id]/build/page.tsx` stub that
  `redirect()`s to `…/nirmana` is the fallback — but the config redirect is cleaner and covers the
  child route.)
- Acceptance: navigating to the old `/clients/<id>/build` 301s to `/clients/<id>/nirmana`.

## §5 — PHASE N5 — Tests + verify
- Update test references to the new path: `app/clients/__tests__/chart_pages.test.tsx`,
  `app/clients/[id]/nirmana/__tests__/page.test.tsx`, `components/clients/__tests__/NewClientForm.test.tsx`,
  `app/api/clients/create/__tests__/route.test.ts`, `app/api/clients/__tests__/create.integration.test.ts`
  — anything asserting `/build`. (Do NOT touch `app/api/build/__tests__/build.integration.test.ts` —
  that's the /api/build API, not this page.)
- Acceptance [verify-against: prod via running app, proxy up]:
  - [ ] `/clients/<native>/nirmana` renders the build tracker with a **Nirmāṇa** title + tab title.
  - [ ] The jātaka card **Nirmāṇa** button → lands on `/nirmana` (not `/build`).
  - [ ] Old `/clients/<native>/build` 301-redirects to `/nirmana` (no 404).
  - [ ] New-chart create flow + Edit + "Continue building" CTA + roster/card links + the two toasts all land on `/nirmana`.
  - [ ] Breadcrumb + chart-switcher still correctly hide on the Nirmāṇa page.
  - [ ] Full test suite green; no dangling `/build` page-link references (grep `clients/.*/build` returns only the redirect + /api/build).

## §6 — Out of scope
- The dashboard **cockpit** (`/cockpit`) — NOT renamed; this rename is precisely to STOP confusing the two.
- `/api/build` and `/api/cockpit/*` API routes — unchanged.
- No data-plane / migration work. No L2 Bodha.

---
*End of NIRMANA_PAGE_RENAME v1.0. Name the per-chart build-tracker page **Nirmāṇa** (it had no title,
hence the cockpit confusion): N1 adds the daṇḍa-flanked `॥ Nirmāṇa ॥` title in the SAME bt-display
gold tokens as dashboard "Jātakas", a "Build Tracker" subtitle (native-kept), and a ChevronLeft
back-link to /dashboard mirroring Nava Jātaka — native-approved via mockup 2026-06-16. Then rename the
route /clients/[id]/build → /clients/[id]/nirmana: 11 internal link sites + 3 API redirect_urls + 2
path guards, plus a permanent /build→/nirmana redirect so old links don't 404. Do NOT touch /api/build
or /api/cockpit/*. The dashboard cockpit is untouched — this rename exists to disambiguate the two
surfaces. Reuse design-system tokens (bt-display / text-brand-gold-cream / bt-label) — never hardcode hex.*
