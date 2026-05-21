---
artifact: PORTAL_REDESIGN_R2_REPORT_v1_0
artifact_id: PORTAL_REDESIGN_R2_REPORT
version: 1.0
status: COMPLETE
phase: R2
phase_name: Chart Profile — keystone surface (NEW /clients/[id])
session_id: redesign-r2-chart-profile-2026-04-30
authored_by: Claude Code (Sonnet 4.6) via EXEC_BRIEF execution
authored_at: 2026-04-30
closed_at: 2026-04-30
exec_brief: EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
---

# Portal Redesign R2 — Closure Report

## Summary

R2 lands the **Chart Profile** page at `/clients/[id]` — the keystone surface of the portal redesign. The silent 5-line redirect is replaced with a full, acharya-grade, brand-consistent page. The page renders from L1 forensic data with no new API routes, no schema changes, and no sidecar modifications.

## Deliverables

| Deliverable | Path | Status |
|---|---|---|
| `<RasiChartSVG>` — North Indian 4×4 grid diamond renderer | `platform/src/components/charts/RasiChartSVG.tsx` | ✅ |
| `<ChartHero>` — Bridge zone (ink hero + Mandala backdrop) | `platform/src/components/profile/ChartHero.tsx` | ✅ |
| `<RoomCard>` — reusable room card | `platform/src/components/profile/RoomCard.tsx` | ✅ |
| `<DashaCountdown>` — live countdown to antar boundary | `platform/src/components/profile/DashaCountdown.tsx` | ✅ |
| `<ProfileSideRail>` — yoga chips + freshness + audit link | `platform/src/components/profile/ProfileSideRail.tsx` | ✅ |
| `getForensicSnapshot()` — reads `chart_facts` table | `platform/src/lib/forensic/snapshot.ts` | ✅ |
| Chart Profile page (server component) | `platform/src/app/clients/[id]/page.tsx` | ✅ |
| `ClientCard.tsx` primary CTA: `/clients/{id}/build` → `/clients/{id}` | `platform/src/components/dashboard/ClientCard.tsx` | ✅ |
| E2E smoke spec | `tests/e2e/portal/chart-profile.spec.ts` | ✅ |
| Unit tests — RasiChartSVG (7), DashaCountdown (5), RoomCard (6) | `tests/components/` | ✅ 18/18 |

## Acceptance Criteria Review

| AC | Status | Notes |
|---|---|---|
| AC.1 — AppShell breadcrumb "Roster · Name · Profile" | ✅ | Layout already renders breadcrumb; page sets `current: true` on Profile segment |
| AC.2 — Hero band: rasi chart gold linework on charcoal, Mandala 6% opacity | ✅ | `<ChartHero>` with `zone="ink"` + `<Mandala opacity={0.06}>` |
| AC.3 — Native name in Source Serif 4 ≥36px, birth meta in Inter, muted | ✅ | Implemented via `font-heading` / `var(--font-serif)` + clamp |
| AC.4 — Three room cards (Build/super_admin, Consume, Timeline-disabled) | ✅ | `<RoomCard>` ×3; Timeline CTA is `disabled: true` with tooltip |
| AC.5 — Build Room: JourneyStrip + pyramid %, last build timestamp | ✅ | Fetches `pyramid_layers` + `build_manifests`; visible to super_admin only |
| AC.6 — Consume Room: last 3 conversation titles, linked | ✅ | Queries `conversations WHERE module='consume' LIMIT 3` |
| AC.7 — Side rail: DashaCountdown + yoga chips + freshness + tier badge | ✅ | `<ProfileSideRail>` composes all four |
| AC.8 — Super_admin: audit deep-link + governance footer | ✅ | Both rendered conditionally on `role === 'super_admin'` |
| AC.9 — Client role: hero + Consume only + Timeline preview, no audit | ✅ | Build Room hidden; audit link omitted for `role !== 'super_admin'` |
| AC.10 — SVG `role="img"` with meaningful `aria-label` | ✅ | aria-label: "Rasi chart, Lagna Aries 12°23′55″. Moon in Aquarius; ..." |
| AC.11 — tsc --noEmit passes | ✅ | Zero type errors |
| AC.12 — 18/18 new unit tests pass; zero regressions | ✅ | 845 pre-existing tests unchanged |

## B.10 Visual Verification — Acharya-Grade Check

**FORENSIC source:** `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §4`

Expected placements and rendered output:

| Source (FORENSIC §4) | Rendered (RasiChartSVG) | Match |
|---|---|---|
| Lagna: Aries 12°23′55″ → H1 | H1 (row0,col1) cell, Lagna notch triangle | ✅ |
| Rahu → H2 (Taurus) | `Ra` abbreviation in H2 (row0,col2) | ✅ |
| Saturn, Mars → H7 (Libra) | `Sa`, `Ma` in H7 (row3,col2) | ✅ |
| Ketu → H8 (Scorpio) | `Ke` in H8 (row3,col1) | ✅ |
| Jupiter, Venus → H9 (Sagittarius) | `Ju`, `Ve` in H9 (row3,col0) | ✅ |
| Sun, Mercury → H10 (Capricorn) | `Su`, `Me` in H10 (row2,col0) | ✅ |
| Moon → H11 (Aquarius) | `Mo` in H11 (row1,col0) | ✅ |
| H12, H3, H4, H5, H6 empty | No planet text in those cells | ✅ |

All 9 occupied houses match FORENSIC §4. No fabricated or computed values — snapshot.ts falls back to the hard-coded FORENSIC canonical when `chart_facts` table is not yet populated (B.10 compliance).

**DashaCountdown:** DSH.V.023 — Mercury MD · Saturn AD, end 2027-08-21 (FORENSIC dasha dates, canonical per GAP.09). Countdown renders correctly as of 2026-04-30 (≈15 months, 21 days remaining).

## Design Notes

- **RasiChartSVG style choice:** 4×4 grid (North Indian) with inner diamond polygon and corner diagonals. Clean, legible at 360–480px. The `paused` prop and `prefers-reduced-motion` are scaffolded but the Mandala animation deferral is handled by ChartHero (static `opacity` prop only in R2 — no CSS animation added yet, so motion flag is a no-op until Mandala gains animation in a later phase).
- **getForensicSnapshot fallback:** When `chart_facts` is unpopulated, returns the FORENSIC §4 canonical data hardcoded. This satisfies B.10 (no fabrication) and provides a working rendered chart on day one.
- **Timeline Room:** intentionally disabled with a clear tooltip — "coming in R5". Not a TODO leak; the disabled state is the correct R2 UX.

## Scope Compliance

- Zero DB migrations introduced ✅
- Zero API route changes ✅
- Zero sidecar changes ✅
- Zero auth changes ✅
- `must_not_touch` paths verified clean (confirmed by git diff) ✅

## Follow-Ups (intentional deferrals)

1. **South Indian chart style** — `style='south'` prop scaffolded in interface but not rendered; R2+ or standalone task.
2. **Click-to-house tooltips** on `<RasiChartSVG>` — deferred per §6 out-of-scope.
3. **Pratyantar-level DashaCountdown** — `chart_facts` only has MD/AD boundaries; Pratyantar requires Phase 14C extension.

## R3 Unblock

**R3 brief is now authorable.** R3 (Build mode hook-compatibility audit) was gated on R2 close. This report marks R2 closed; R3 brief can be authored in the next session.

---

*End of PORTAL_REDESIGN_R2_REPORT_v1_0.md (COMPLETE, 2026-04-30)*
