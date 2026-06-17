---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R0_FOUNDATION
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-29
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R0_FOUNDATION_v1_0.md and execute it."
phase: Portal Redesign R0
phase_name: Foundation — AppShell + theme zones + /build → /cockpit rename
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (DRAFT, v1.0.1)
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
risk_classification: LOW (navigation + theme tokens only; zero schema; zero sidecar; zero auth)
parallelizable_with: []                  # R0 is the gate — runs alone
must_complete_before: [R1, R2, R3, R4, R5, R6, R7]
depends_on: []
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R0_REPORT_v1_0.md (closure report)
---

# EXEC_BRIEF — Portal Redesign R0 — Foundation

## Mission

Land the three foundation pieces every other redesign phase consumes: a single `<AppShell>` (left rail + breadcrumb), a `<ZoneRoot zone="vellum|ink|bridge">` theme-scope component, and the `/build → /cockpit` route rename with a permanent 301. Retire `DashboardHeader`, `BuildHeader`, `ForceDarkMode`, and `ConsumeForceDark` in favor of the new shell + zone components. Zero schema changes, zero migrations, zero sidecar, zero auth model changes.

This is the gate phase. R1, R2, R5, R6 cannot fan out into parallel worktrees until R0 closes.

## Pre-flight gate

Halt with an actionable message if any of the following fail.

1. The active `CLAUDECODE_BRIEF.md` at project root has `status: COMPLETE` (i.e., the trace fix is fully merged) — R0 itself doesn't conflict with the trace fix, but the convention is one CLAUDECODE_BRIEF at a time.
2. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` exists and contains §3 surface specifications.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` exists with R0 row at `status: authored` and `exec_brief: EXEC_BRIEF_PORTAL_REDESIGN_R0_FOUNDATION_v1_0.md`.
4. Working tree clean.
5. Branch named `redesign/r0-foundation` (create if absent).

## Scope declaration

```yaml
may_touch:
  - platform/src/components/shared/AppShell.tsx                        # NEW
  - platform/src/components/shared/AppShellRail.tsx                    # NEW
  - platform/src/components/shared/AppShellBreadcrumb.tsx              # NEW
  - platform/src/components/shared/ZoneRoot.tsx                        # NEW (replaces ForceDarkMode + ConsumeForceDark)
  - platform/src/app/dashboard/layout.tsx                              # wrap in AppShell, drop DashboardHeader
  - platform/src/app/clients/[id]/layout.tsx                           # add AppShell wrapper at the right level
  - platform/src/app/admin/layout.tsx                                  # wrap in AppShell
  - platform/src/app/audit/layout.tsx                                  # wrap in AppShell (if present)
  - platform/src/app/cockpit/**                                        # NEW directory — move from /build
  - platform/src/app/build/**                                          # delete page files; replace with redirects
  - platform/src/components/dashboard/DashboardHeader.tsx              # delete (retired)
  - platform/src/components/build/BuildHeader.tsx                      # update nav links from /build/* → /cockpit/*
  - platform/src/components/auth/ForceDarkMode.tsx                     # delete (retired — superseded by ZoneRoot)
  - platform/src/components/consume/ConsumeForceDark.tsx               # delete (retired — superseded by ZoneRoot)
  - platform/src/app/clients/[id]/consume/layout.tsx                   # remove ForceDarkMode usage; rely on ZoneRoot
  - platform/src/app/login/page.tsx                                    # remove ForceDarkMode usage; replace with ZoneRoot zone="ink"
  - platform/src/app/globals.css                                       # add zone-scoped CSS rules (additive only)
  - platform/src/lib/config/feature_flags.ts                           # add PORTAL_REDESIGN_R0_ENABLED flag (default true at close)
  - tests/e2e/portal/appshell.spec.ts                                  # NEW Playwright smoke
  - tests/e2e/portal/cockpit-redirect.spec.ts                          # NEW: /build/* → /cockpit/* 301 verification
  - tests/components/AppShell.test.tsx                                 # NEW
  - tests/components/ZoneRoot.test.tsx                                 # NEW
must_not_touch:
  - 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/lib/db/                                               # except feature_flags.ts which is in lib/config
  - platform/src/app/api/**                                            # NO API surface change
  - platform/src/lib/firebase/                                         # auth model unchanged
  - platform/src/components/build/CockpitGrid.tsx                      # cockpit internals untouched (R6 scope)
  - platform/src/components/build/ (the rest)                          # except BuildHeader nav links
  - platform/src/components/consume/, platform/src/components/chat/    # R3/R4 scope
  - platform/src/components/dashboard/ClientCard.tsx                   # R1/R2 scope
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md                        # promotion of VISION + TRACKER to CURRENT happens at R0 close
  - 00_ARCHITECTURE/CLAUDE.md                                          # §C item update happens at R0 close, AS PART of close
```

A discovery that forces a touch outside `may_touch` halts and emits a `scope_expansion_request` block.

## §1 — `<AppShell>` specification

**Path:** `platform/src/components/shared/AppShell.tsx`

**Props:**
```ts
interface AppShellProps {
  children: React.ReactNode;
  user: { uid: string; email?: string; name?: string };
  profile: { role: 'super_admin' | 'admin' | 'client'; status: 'active' | 'inactive' };
  breadcrumb?: BreadcrumbSegment[];      // top breadcrumb segments — see AppShellBreadcrumb
  zone?: 'vellum' | 'ink' | 'bridge';    // default 'vellum'; ink for Consume; bridge for Chart Profile
}
type BreadcrumbSegment = { label: string; href?: string; current?: boolean };
```

**Layout:**
- Left rail (`<AppShellRail>`): fixed 56 px wide on desktop, collapsed-only on mobile (sheet trigger from breadcrumb). Contents top-to-bottom: `Sigil` (links to `/dashboard` aka Roster), `Roster` icon-link, `Cockpit` icon-link (super_admin only), `Admin` icon-link (super_admin only), spacer, avatar at bottom with dropdown (Sign out, theme toggle if applicable).
- Top breadcrumb (`<AppShellBreadcrumb>`): 40 px tall, vellum-zone styled. Renders the `breadcrumb` segments separated by `·`. Last segment styled as `current` (no link, slightly stronger weight).
- Content column: takes remaining width, scrolls internally, inherits `<ZoneRoot>` from props.
- Sign-out: same Firebase + session-cookie deletion as the current `DashboardHeader`/`BuildHeader` (lift the function into `AppShell` once; both old headers had the same code).

**Visual:** Vellum zone by default. Rail uses `var(--sidebar)` background with `var(--sidebar-border)` separator. Sigil active state: gold glow. Active nav link: `var(--sidebar-accent)` background.

**Acceptance:**
- Rendered on every authenticated route.
- super_admin sees Cockpit + Admin in the rail; admin sees Admin only; client sees neither.
- Sigil click navigates to `/dashboard` regardless of current route.
- Avatar dropdown shows email/name; Sign out works end-to-end.
- a11y: rail has `role="navigation"` and `aria-label="Primary navigation"`; breadcrumb has `role="navigation"` and `aria-label="Breadcrumb"`.

## §2 — `<ZoneRoot>` specification

**Path:** `platform/src/components/shared/ZoneRoot.tsx`

Replaces `ForceDarkMode` + `ConsumeForceDark` with one component that explicitly scopes a theme zone to its subtree.

```ts
interface ZoneRootProps {
  zone: 'vellum' | 'ink' | 'bridge';
  children: React.ReactNode;
  asChild?: boolean;                     // for use with shadcn Slot pattern when needed
}
```

**Behavior:**
- `zone="vellum"`: applies `class="zone-vellum"` to its subtree. Default page chrome — uses `--background`, `--foreground`, `--card`, etc. as already defined.
- `zone="ink"`: applies `class="zone-ink dark"` to its subtree. The `dark` class scopes Tailwind dark variants AND the existing dark mode CSS rules. Used for Consume and the Chart Profile hero band.
- `zone="bridge"`: a vellum container that is allowed to host a nested `zone="ink"` for hero bands. Adds `class="zone-bridge"`. CSS rules in `globals.css` ensure ink-zone children of bridge-zone do NOT bleed their background outside the ink subtree.

**CSS additions to `globals.css`** (additive — do not modify existing rules):

```css
/* Zone scopes — VISION §3.2 */
.zone-vellum { /* default; no overrides needed */ }

.zone-ink {
  background: var(--brand-ink);
  color: var(--brand-gold-cream);
}

.zone-bridge { /* container; allows nested zone-ink */ }
.zone-bridge .zone-ink {
  /* ink hero bands inside bridge zones are CONTAINED — no background bleed */
  isolation: isolate;
}
```

**Acceptance:**
- Login page renders with `<ZoneRoot zone="ink">` instead of `ForceDarkMode`. Visually unchanged.
- Consume route renders with `<ZoneRoot zone="ink">` instead of `ConsumeForceDark`. Visually unchanged.
- A test page (or unit test) that renders `<ZoneRoot zone="bridge"><div>vellum</div><ZoneRoot zone="ink"><div>ink hero</div></ZoneRoot></ZoneRoot>` shows the ink zone fully contained.
- `next-themes` toggle in the avatar dropdown (if present) flips light/dark on vellum zones only — ink zones remain ink. (This matches the current behavior where Consume is always dark regardless of user preference.)

## §3 — `/build → /cockpit` route rename

**Move all files** under `platform/src/app/build/` (excluding `error.tsx` if shared) to `platform/src/app/cockpit/`. The directory currently contains: `activity/`, `health/`, `interventions/`, `parallel/`, `plan/`, `registry/`, `sessions/`, `error.tsx`, `layout.tsx`, `page.tsx`. Use `git mv` so history follows.

**Replace** the original `platform/src/app/build/` files with redirect-only versions. The simplest pattern: a single `platform/src/app/build/[...slug]/page.tsx`:

```tsx
import { redirect, permanentRedirect } from 'next/navigation';

export default async function BuildLegacyRedirect({
  params,
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  const { slug = [] } = await params;
  permanentRedirect(`/cockpit/${slug.join('/')}`);
}
```

Plus a top-level `platform/src/app/build/page.tsx` that does `permanentRedirect('/cockpit')` for the bare `/build` URL.

**Update** `platform/src/components/build/BuildHeader.tsx` `NAV_LINKS`:
- `/build` → `/cockpit`
- `/build/plan` → `/cockpit/plan`
- ...etc for all 8 entries

**Update** `cockpit/layout.tsx` (newly moved from `build/layout.tsx`) to reflect the rename in its display copy if any (e.g., "BUILD" wordmark next to the Logo becomes "COCKPIT", or stays "BUILD" if you prefer the metaphor — native call; capture in closure report).

**Acceptance:**
- `curl -I https://{host}/build` returns 308 with Location `/cockpit`.
- `curl -I https://{host}/build/sessions` returns 308 with Location `/cockpit/sessions`.
- The Cockpit at `/cockpit` renders identically to the previous `/build`.
- All internal links in `BuildHeader` and any other navigation surface point to `/cockpit/*`.
- A grep for `'/build'` and `"/build"` in `platform/src/` returns zero results outside the redirect file itself and any genuine string literals (e.g., the audit log if it logs route names).

## §4 — Header retirement

Delete `platform/src/components/dashboard/DashboardHeader.tsx`. Its functionality is fully covered by `<AppShell>`.

Update `platform/src/app/dashboard/layout.tsx` to:

```tsx
import { redirect } from 'next/navigation';
import { getServerUserWithProfile } from '@/lib/auth/access-control';
import { AppShell } from '@/components/shared/AppShell';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const ctx = await getServerUserWithProfile();
  if (!ctx) redirect('/login');
  if (ctx.profile.status !== 'active') redirect('/login');

  return (
    <AppShell user={ctx.user} profile={ctx.profile} breadcrumb={[{ label: 'Roster', current: true }]}>
      {children}
    </AppShell>
  );
}
```

Same pattern for `admin/layout.tsx` and the new `cockpit/layout.tsx`.

For `clients/[id]/layout.tsx`, the AppShell wraps with a chart-aware breadcrumb:

```tsx
breadcrumb={[
  { label: 'Roster', href: '/dashboard' },
  { label: chart.name, href: `/clients/${id}`, current: true },
]}
```

The leaf pages (Build, Consume, Profile) extend the breadcrumb with their own segment via a layout-prop pattern — e.g., `clients/[id]/build/layout.tsx` adds `{ label: 'Build', current: true }`.

`BuildHeader` is NOT deleted (it's still used inside the Cockpit), but its `signOut` and avatar dropdown become redundant once Cockpit lives inside `AppShell`. Resolve by removing the avatar from `BuildHeader` and letting the `AppShell` avatar handle it. The Cockpit gets its rich `BuildHeader` nav strip BELOW the AppShell breadcrumb — two-row header pattern.

## §5 — `ForceDarkMode` and `ConsumeForceDark` retirement

Delete both files. Replace usages:
- `platform/src/app/login/page.tsx` line ~91: `<ForceDarkMode />` → wrap the whole page body in `<ZoneRoot zone="ink">`.
- `platform/src/app/clients/[id]/consume/layout.tsx`: remove the manual `<div className="dark">` + `<ForceDarkMode />` pattern; replace with `<ZoneRoot zone="ink">{children}</ZoneRoot>`.
- Any `<RequestAccessModal>`, `<ForgotPasswordModal>` usages on login: unchanged (they live inside the ZoneRoot zone="ink" subtree and inherit dark mode).

## §6 — Feature flag

Add `PORTAL_REDESIGN_R0_ENABLED` to `platform/src/lib/config/feature_flags.ts`. Default value at landing: `true`. The flag exists so a quick `MARSYS_FLAG_PORTAL_REDESIGN_R0_ENABLED=false` env var rollback is possible if a problem surfaces in staging.

The flag gates ONLY the `<AppShell>` swap in the layouts. With the flag off, layouts render their old headers (DashboardHeader, BuildHeader cockpit-mode) as fallback. Implementation: a small adapter in each affected layout that branches on the flag. R7 removes the adapter and the legacy header-rendering branch.

## §7 — Tests and verification

### §7.1 Playwright smoke

- `tests/e2e/portal/appshell.spec.ts`: super_admin login → assert rail has Roster + Cockpit + Admin; admin login → assert Admin only; client login → assert neither (rail collapsed). Avatar dropdown opens; sign out works.
- `tests/e2e/portal/cockpit-redirect.spec.ts`: hit `/build`, `/build/sessions`, `/build/plan`, `/build/health` — assert all 308 to `/cockpit/*` and the destination renders.

### §7.2 Unit tests

- `tests/components/AppShell.test.tsx`: rendering by role; breadcrumb rendering; `current` segment styling.
- `tests/components/ZoneRoot.test.tsx`: zone classes applied; `bridge > ink` containment; default zone is `vellum`.

### §7.3 Visual regression

Capture before/after screenshots on: login, dashboard, clients/[id]/consume, /build (becomes /cockpit), /admin. Login and consume MUST be visually unchanged (ZoneRoot is a behavioral swap only).

### §7.4 Governance scripts

- `mirror_enforcer.py` exit 0.
- `drift_detector.py` exit 0 or 3 (known_residuals only).
- `schema_validator.py` exit 0.

## §8 — Closure report and promotion

Land `00_ARCHITECTURE/PORTAL_REDESIGN_R0_REPORT_v1_0.md` with frontmatter `status: COMPLETE`. The closure report MUST do these promotion steps as part of close:

1. **Promote VISION to CURRENT.** Edit `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` frontmatter `status: DRAFT` → `status: CURRENT`. Add a changelog entry for the promotion.
2. **Promote TRACKER inclusion.** No status change (TRACKER is LIVING by definition); just confirm in the closure report.
3. **Add CANONICAL_ARTIFACTS entries.** Edit `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md §1` — add two rows:
   - `canonical_id: PORTAL_REDESIGN_VISION`, `path: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md`, `version: 1.0.1`, `status: CURRENT`.
   - `canonical_id: PORTAL_REDESIGN_TRACKER`, `path: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md`, `version: 1.0.0`, `status: LIVING`.
4. **Update CLAUDE.md §C** mandatory-reading list: add VISION + TRACKER as item #12 (between item #11 and the closing ND paragraph). Mirror the change to `.geminirules` and `.gemini/project_state.md` per `MP.1` mirror discipline.
5. **Update TRACKER §2 state block.** Set `active_phase: null` (R0 just closed; next phase committed-to is whichever the native picks from {R1, R2, R5, R6}). Set `last_redesign_session_id`, `last_close_at`. Set `vision_status: CURRENT`, `canonical_artifacts_entry: true`, `claude_md_section_C_updated: true`.
6. **Update TRACKER §3 R0 row.** `status: closed`, populate `session_id`, `closed_at`, `follow_ups`.
7. **Run all governance scripts.** Mirror enforcer is the load-bearing one this session because of the CLAUDE.md / .geminirules / .gemini/project_state.md mirror updates.
8. **Append SESSION_LOG entry.**

If any promotion step fails, the close-checklist fails and R0 does NOT claim close.

## §9 — Out of scope

- Do NOT touch `clients/[id]/page.tsx` (R2 scope).
- Do NOT touch the Roster page contents (R1 scope).
- Do NOT touch `BuildChat`, `ConsumeChat`, or any per-client Build/Consume components beyond the layout-level AppShell wrap.
- Do NOT modify the Cockpit's internal grid (R6 scope).
- Do NOT introduce any DB schema change.
- Do NOT touch the trace fix surface (it's in flight or just-merged).

## §10 — One-line summary

Land the foundation that lets every other redesign phase fan out: one shell, one zone primitive, one route rename, one flag, all the deletions of the surfaces they replace.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R0_FOUNDATION_v1_0.md (AUTHORED, 2026-04-29).*
